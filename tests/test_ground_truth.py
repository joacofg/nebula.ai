from __future__ import annotations

import json


from collections import Counter

import httpx
import pytest

from scripts.ground_truth import cli, llm, records, review, sample, sources, spend, translate
from scripts.metric_validation.corpus import TASK_TYPES


def test_rows_round_trip_and_latest_wins(tmp_path):
    path = tmp_path / "r.jsonl"
    first = records.ResponseRow("p1", "es", "m", "failed", "", "", 0, 0, 0.0, "m", "boom")
    second = records.ResponseRow("p1", "es", "m", "ok", "hola", "stop", 3, 4, 0.01, "m")
    records.append_row(first, path)
    records.append_row(second, path)
    rows = records.read_rows(path, records.ResponseRow)
    assert rows == [first, second]
    assert records.latest(rows, key=lambda r: r.prompt_id) == {"p1": second}


def test_read_rows_on_missing_file_is_empty(tmp_path):
    assert records.read_rows(tmp_path / "nope.jsonl", records.PromptRow) == []


def test_update_provenance_merges(tmp_path):
    cli.update_provenance(tmp_path, a=1)
    cli.update_provenance(tmp_path, b={"x": 2})
    assert json.loads((tmp_path / "provenance.json").read_text()) == {"a": 1, "b": {"x": 2}}


def _cands(n_per_task):
    return [
        sources.Candidate(f"{t}:{i}", t, f"prompt {t} {i}")
        for t in TASK_TYPES
        for i in range(n_per_task)
    ]


def test_sample_is_deterministic_and_balanced():
    a = sample.stratified_sample(_cands(40), per_task=10, reserve_per_task=3, seed=7)
    b = sample.stratified_sample(list(reversed(_cands(40))), per_task=10, reserve_per_task=3, seed=7)
    assert a == b
    assert Counter((r.task_type, r.role) for r in a) == Counter(
        {(t, role): n for t in TASK_TYPES for role, n in (("corpus", 10), ("reserve", 3))}
    )
    assert len({r.prompt_id for r in a}) == len(a)


def test_sample_refuses_a_short_stratum():
    short = [c for c in _cands(40) if c.task_type != "code"] + [
        c for c in _cands(2) if c.task_type == "code"
    ]
    with pytest.raises(ValueError, match="code"):
        sample.stratified_sample(short, per_task=10, reserve_per_task=3, seed=7)


def test_sample_drops_duplicates_and_overlong():
    cands = _cands(40) + [
        sources.Candidate("dup", "code", "prompt code 0"),
        sources.Candidate("long", "code", "x" * 7000),
    ]
    rows = sample.stratified_sample(cands, per_task=39, reserve_per_task=1, seed=1)
    assert not any(r.source in {"dup", "long"} for r in rows)


def test_dolly_maps_categories_and_folds_context():
    raw = [
        {"instruction": "Q?", "context": "", "category": "open_qa"},
        {"instruction": "Summarise", "context": "Long text.", "category": "summarization"},
        {"instruction": "Summarise", "context": "", "category": "summarization"},
        {"instruction": "Sort these", "context": "", "category": "classification"},
        {"instruction": "Poem", "context": "", "category": "creative_writing"},
    ]
    got = sources.dolly_candidates(raw)
    assert [(c.source_id, c.task_type, c.prompt) for c in got] == [
        ("dolly:0", "factual_qa", "Q?"),
        ("dolly:1", "summarisation", "Summarise\n\nLong text."),
        ("dolly:4", "open_writing", "Poem"),
    ]


def test_mbpp_prompt_carries_the_first_test_verbatim():
    got = sources.mbpp_candidates(
        [{"task_id": 11, "text": "Write f.", "test_list": ["assert f(1) == 2", "x"]}]
    )
    assert got[0].prompt == (
        "Write f.\nYour code should satisfy this test:\n```python\nassert f(1) == 2\n```"
    )
    assert got[0].source_id == "mbpp:11" and got[0].task_type == "code"


def test_fetch_refuses_a_hash_mismatch(tmp_path):
    src = sources.Source("x", "http://unused", "0" * 64, "MIT", "cite")
    (tmp_path / "x.jsonl").write_text("{}\n")
    with pytest.raises(ValueError, match="sha256"):
        sources.fetch(src, tmp_path)


async def test_openrouter_chat_reads_usage_cost_and_finish_reason():
    def handler(request):
        body = json.loads(request.content)
        assert body["temperature"] == 0.0 and body["max_tokens"] == 9
        assert body["usage"] == {"include": True}
        assert body["reasoning"] == {"max_tokens": 0}
        return httpx.Response(200, json={
            "model": "openai/gpt-4.1-2025-04-14",
            "choices": [{"message": {"content": "hi"}, "finish_reason": "length"}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 9, "cost": 0.002},
        })

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://x") as client:
        chat = llm.openrouter_chat(
            client, "openai/gpt-4.1", max_tokens=9, extra={"reasoning": {"max_tokens": 0}}
        )
        got = await chat("q")
    assert got == llm.Completion("hi", "length", 5, 9, 0.002, "openai/gpt-4.1-2025-04-14")


async def test_openrouter_error_body_is_a_failure():
    transport = httpx.MockTransport(
        lambda r: httpx.Response(200, json={"error": {"message": "nope"}})
    )
    async with httpx.AsyncClient(transport=transport, base_url="http://x") as client:
        with pytest.raises(llm.CallFailed):
            await llm.openrouter_chat(client, "m", max_tokens=5)("q")


async def test_ollama_chat_maps_done_reason_and_counts():
    transport = httpx.MockTransport(lambda r: httpx.Response(200, json={
        "message": {"content": "hola"}, "done_reason": "length",
        "prompt_eval_count": 3, "eval_count": 7,
    }))
    async with httpx.AsyncClient(transport=transport, base_url="http://x") as client:
        got = await llm.ollama_chat(client, "qwen2.5:7b", max_tokens=7)("q")
    assert got == llm.Completion("hola", "length", 3, 7, 0.0, "qwen2.5:7b")


async def test_with_retries_gives_up_with_call_failed():
    calls = []

    async def flaky(prompt):
        calls.append(prompt)
        raise httpx.ConnectError("down")

    async def no_sleep(_):
        return None

    with pytest.raises(llm.CallFailed):
        await llm.with_retries(flaky, "q", attempts=4, sleep=no_sleep)
    assert len(calls) == 4


def test_ledger_accumulates_across_instances_and_enforces_cap(tmp_path):
    path = tmp_path / "spend.jsonl"
    ledger = spend.SpendLedger(path, cap_usd=0.01)
    ledger.record(stage="t", model="openai/gpt-4.1",
                  completion=llm.Completion("", "stop", 1, 1, 0.006, "m"))
    again = spend.SpendLedger(path, cap_usd=0.01)
    assert again.total == pytest.approx(0.006)
    again.check()
    again.record(stage="t", model="openai/gpt-4.1",
                 completion=llm.Completion("", "stop", 1, 1, None, "m"))
    assert again.total == pytest.approx(0.006 + spend.estimate("openai/gpt-4.1", 1, 1))
    again.record(stage="t", model="openai/gpt-4.1",
                 completion=llm.Completion("", "stop", 1, 1, 0.01, "m"))
    with pytest.raises(spend.BudgetExceeded):
        again.check()


def test_estimate_refuses_unknown_models():
    with pytest.raises(ValueError):
        spend.estimate("who/knows", 1, 1)


def test_problems_catch_lost_numbers_and_code():
    src = "Janet has 16 eggs and eats 3.\n```python\nassert f(1) == 2\n```"
    good = "Janet tiene 16 huevos y come 3.\n```python\nassert f(1) == 2\n```"
    assert translate.translation_problems(src, good) == []
    lost = "Janet tiene huevos.\n```python\nassert f(1) == 2\n```"
    assert any("numbers" in p for p in translate.translation_problems(src, lost))
    changed = "Janet tiene 16 huevos y come 3.\n```python\nassert g(1) == 2\n```"
    assert any("code" in p for p in translate.translation_problems(src, changed))


def test_problems_tolerate_spanish_number_formatting():
    assert translate.translation_problems("It costs 1,000.50 dollars", "Cuesta 1.000,50 dólares") == []


def test_problems_catch_an_answer_instead_of_a_translation():
    src = "What causes the seasons?"
    answer = "¿Qué causa las estaciones? " + "Se deben a la inclinación del eje terrestre. " * 5
    assert any("answer" in p for p in translate.translation_problems(src, answer))
    assert translate.translation_problems(src, "") == ["empty"]


def test_clean_strips_wrappers():
    assert translate.clean("<request>\n¿Hola?\n</request>") == "¿Hola?"
    assert translate.clean('"¿Hola?"') == "¿Hola?"
    assert translate.clean("¿Hola?") == "¿Hola?"


def _row(pid, task, role="corpus"):
    return records.PromptRow(pid, task, "s", f"p {pid}", role)


def test_assemble_spanish_replaces_rejects_from_reserve_and_flags_en_subset():
    rows = [_row("t-0", "code"), _row("t-1", "code"),
            _row("t-2", "code", "reserve"), _row("t-3", "code", "reserve")]
    tr = {
        "t-0": translate.TranslationRow("t-0", "ok", "es0", [], 1),
        "t-1": translate.TranslationRow("t-1", "rejected", "", ["numbers"], 2),
        "t-2": translate.TranslationRow("t-2", "ok", "es2", [], 1),
    }
    got = translate.assemble_spanish(rows, tr, per_task=2, en_per_task=1)
    assert [(r.prompt_id, r.prompt, r.role, r.en_subset) for r in got] == [
        ("t-0", "es0", "corpus", True), ("t-2", "es2", "corpus", False)]


def test_assemble_spanish_refuses_an_exhausted_reserve():
    rows = [_row("t-0", "code"), _row("t-1", "code", "reserve")]
    tr = {"t-0": translate.TranslationRow("t-0", "rejected", "", ["x"], 2)}
    with pytest.raises(ValueError, match="code"):
        translate.assemble_spanish(rows, tr, per_task=1, en_per_task=1)


async def test_translate_all_retries_once_then_rejects_and_resumes(tmp_path):
    replies = iter(["sin numero", "sin numero", "tiene 2"])
    calls = []

    async def chat(prompt):
        calls.append(prompt)
        return llm.Completion(next(replies), "stop", 1, 1, 0.0, "m")

    ledger = spend.SpendLedger(tmp_path / "spend.jsonl", cap_usd=1)
    rows = [records.PromptRow("a", "code", "s", "has 2", "corpus"),
            records.PromptRow("b", "code", "s", "has 2", "corpus")]
    cache = tmp_path / "t.jsonl"
    got = await translate.translate_all(rows, chat=chat, cache_path=cache, ledger=ledger,
                                        concurrency=1)
    assert got["a"].status == "rejected" and got["a"].attempts == 2
    assert got["b"].status == "ok" and got["b"].text == "tiene 2"
    again = await translate.translate_all(rows, chat=chat, cache_path=cache, ledger=ledger,
                                          concurrency=1)
    assert len(calls) == 3 and again == got


def test_review_sample_is_deterministic_and_bounded():
    rows = [records.PromptRow(f"p{i}", "code", "s", "x", "corpus") for i in range(100)]
    assert review.review_sample(rows, size=40, seed=1) == review.review_sample(
        list(reversed(rows)), size=40, seed=1)
    assert len(review.review_sample(rows, size=40, seed=1)) == 40
