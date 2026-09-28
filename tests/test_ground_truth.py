from __future__ import annotations

import json
from collections import Counter

import httpx
import pytest

from scripts.ground_truth import (
    capture,
    cli,
    ensemble,
    holdout,
    judge,
    llm,
    records,
    review,
    sample,
    sources,
    spend,
    tiers,
    translate,
    validate,
)
from scripts.ground_truth import pairs as gt_pairs
from scripts.metric_validation.corpus import TASK_TYPES, Pair, ResponseSide


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


def test_items_for_uses_spanish_corpus_and_english_subset():
    en = [records.PromptRow("a", "code", "s", "EN a", "corpus"),
          records.PromptRow("b", "code", "s", "EN b", "corpus"),
          records.PromptRow("c", "code", "s", "EN c", "reserve")]
    es = [records.PromptRow("a", "code", "s", "ES a", "corpus", en_subset=True),
          records.PromptRow("c", "code", "s", "ES c", "corpus", en_subset=False)]
    assert capture.items_for("es", en, es) == [("a", "ES a"), ("c", "ES c")]
    assert capture.items_for("en", en, es) == [("a", "EN a")]


async def test_capture_resumes_without_repaying_and_retries_failures(tmp_path, monkeypatch):
    async def no_sleep(_):
        return None

    monkeypatch.setattr(llm.asyncio, "sleep", no_sleep)
    calls = []
    fail = {"b"}

    async def chat(prompt):
        calls.append(prompt)
        if prompt in fail:
            raise llm.CallFailed("down")
        return llm.Completion(f"r:{prompt}", "stop", 1, 2, 0.001, "m")

    ledger = spend.SpendLedger(tmp_path / "spend.jsonl", cap_usd=1)
    out = tmp_path / "gpt41.es.jsonl"
    items = [("a", "a"), ("b", "b")]
    got = await capture.capture_role(items, lang="es", model="openai/gpt-4.1", chat=chat,
                                     out_path=out, ledger=ledger, concurrency=1)
    assert got["a"].status == "ok" and got["b"].status == "failed"
    fail.clear()
    got = await capture.capture_role(items, lang="es", model="openai/gpt-4.1", chat=chat,
                                     out_path=out, ledger=ledger, concurrency=1)
    assert calls.count("a") == 1 and got["b"].status == "ok"
    assert ledger.total == pytest.approx(0.002)


async def test_capture_stops_at_the_cap_and_keeps_what_was_paid(tmp_path):
    async def chat(prompt):
        return llm.Completion("x", "stop", 1, 1, 0.6, "m")

    ledger = spend.SpendLedger(tmp_path / "spend.jsonl", cap_usd=1.0)
    out = tmp_path / "haiku.es.jsonl"
    with pytest.raises(spend.BudgetExceeded):
        await capture.capture_role([("a", "a"), ("b", "b"), ("c", "c")], lang="es",
                                   model="anthropic/claude-haiku-4.5", chat=chat,
                                   out_path=out, ledger=ledger, concurrency=1)
    assert [r.prompt_id for r in records.read_rows(out, records.ResponseRow)] == ["a", "b"]


def _resp(pid, role, text="t", status="ok"):
    return records.ResponseRow(pid, "es", role, status, text, "stop", 1, 1, 0.0, role)


def test_build_pairs_skips_unusable_reference_and_failed_candidates():
    prompts = [records.PromptRow("p1", "code", "s", "P1", "corpus"),
               records.PromptRow("p2", "code", "s", "P2", "corpus")]
    responses = {
        "gpt41": {"p1": _resp("p1", "gpt41", "ref"), "p2": _resp("p2", "gpt41", "   ")},
        "qwen7b": {"p1": _resp("p1", "qwen7b"), "p2": _resp("p2", "qwen7b")},
        "llama3b": {"p1": _resp("p1", "llama3b", status="failed")},
        "haiku": {"p1": _resp("p1", "haiku")},
    }
    got, skipped = gt_pairs.build_pairs("es", prompts, responses)
    assert [p.pair_id for p in got] == ["es:haiku:p1", "es:qwen7b:p1"]
    assert skipped == {"reference_unusable": 1, "candidate_failed": 1}
    qwen = got[1]
    assert qwen.kind == "local_vs_premium"
    assert qwen.right.origin == "reference" and qwen.right.text == "ref"
    assert got[0].kind == "premium_vs_premium"
    assert gt_pairs.split_pair_id("es:qwen7b:code-0001") == ("es", "qwen7b", "code-0001")


def _corpus_pairs():
    prompts = [records.PromptRow(f"{t}-{i:04d}", t, "s", f"P {t} {i}", "corpus")
               for t in TASK_TYPES for i in range(30)]
    responses = {
        role: {p.prompt_id: _resp(p.prompt_id, role, f"{role} {p.prompt_id}") for p in prompts}
        for role in ("gpt41", "qwen7b", "llama3b", "haiku")
    }
    return gt_pairs.build_pairs("es", prompts, responses)[0]


def test_holdout_is_stratified_deterministic_and_prompt_distinct():
    ps = _corpus_pairs()
    got = holdout.select_holdout(ps, per_task=10, seed=3)
    assert got == holdout.select_holdout(list(reversed(ps)), per_task=10, seed=3)
    assert Counter(p.task_type for p in got) == {t: 10 for t in TASK_TYPES}
    by_cand = Counter(gt_pairs.split_pair_id(p.pair_id)[1] for p in got)
    assert set(by_cand) == {"qwen7b", "llama3b", "haiku"}
    assert max(by_cand.values()) - min(by_cand.values()) <= 1
    for task in TASK_TYPES:
        pids = [gt_pairs.split_pair_id(p.pair_id)[2] for p in got if p.task_type == task]
        assert len(pids) == len(set(pids))


def test_calibration_negatives_are_off_prompt_references():
    neg = holdout.calibration_negatives(_corpus_pairs(), seed=3, count=2)
    assert len(neg) == 2 and all(p.kind == "cross_prompt" for p in neg)
    for p in neg:
        assert p.left.text != p.right.text and p.pair_id.startswith("xpr:")


async def test_translate_all_leaves_a_failed_call_for_the_next_run(tmp_path, monkeypatch):
    async def no_sleep(_):
        return None

    monkeypatch.setattr(llm.asyncio, "sleep", no_sleep)

    async def chat(prompt):
        if "down" in prompt:
            raise httpx.ConnectError("429")
        return llm.Completion("tiene 2", "stop", 1, 1, 0.0, "m")

    ledger = spend.SpendLedger(tmp_path / "spend.jsonl", cap_usd=1)
    rows = [records.PromptRow("a", "code", "s", "down 2", "corpus"),
            records.PromptRow("b", "code", "s", "has 2", "corpus")]
    cache = tmp_path / "t.jsonl"
    got = await translate.translate_all(rows, chat=chat, cache_path=cache, ledger=ledger,
                                        concurrency=2)
    assert set(got) == {"b"}
    assert [r.prompt_id for r in records.read_rows(cache, translate.TranslationRow)] == ["b"]


def _pair(pid="es:qwen7b:p1"):
    return Pair(pid, "local_vs_premium", "code", "PROMPT", ResponseSide("qwen7b", "q", "CAND"),
                ResponseSide("reference", "g", "REF"), {}, "unbanded")


def test_payload_orientations_and_no_provenance():
    ab, ba = judge.payload(_pair(), "ab"), judge.payload(_pair(), "ba")
    assert (ab["response_a"], ab["response_b"]) == ("CAND", "REF")
    assert (ba["response_a"], ba["response_b"]) == ("REF", "CAND")
    prompt = judge.judge_prompt_for(_pair(), "ab").lower()
    for leak in ("qwen", "reference", "gpt", "local", "premium"):
        assert leak not in prompt


async def test_judge_records_missing_after_parse_retries_and_never_defaults(tmp_path):
    replies = iter(["no idea", "still no", '{"grade": "maybe"}', '{"grade": "partial"}'])

    async def chat(prompt):
        return llm.Completion(next(replies), "stop", 1, 1, 0.0, "m")

    out = tmp_path / "j.jsonl"
    ledger = spend.SpendLedger(tmp_path / "spend.jsonl", cap_usd=1)
    kwargs = dict(judge_model="google/gemini-2.5-flash", chat=chat, out_path=out,
                  ledger=ledger, concurrency=1, orientations=("ab",))
    await judge.judge_pairs([_pair()], **kwargs)
    rows = records.read_rows(out, records.Judgement)
    assert [(r.status, r.grade) for r in rows] == [("missing", None)]
    await judge.judge_pairs([_pair()], **kwargs)
    latest = records.latest(records.read_rows(out, records.Judgement),
                            key=lambda r: (r.pair_id, r.orientation))
    assert latest[("es:qwen7b:p1", "ab")].grade == "partial"


async def test_judge_does_not_repay_ok_rows(tmp_path):
    calls = []

    async def chat(prompt):
        calls.append(prompt)
        return llm.Completion('{"grade": "equivalent"}', "stop", 1, 1, 0.0, "m")

    out = tmp_path / "j.jsonl"
    ledger = spend.SpendLedger(tmp_path / "spend.jsonl", cap_usd=1)
    for _ in range(2):
        await judge.judge_pairs([_pair()], judge_model="google/gemini-2.5-flash", chat=chat,
                                out_path=out, ledger=ledger, concurrency=1)
    assert len(calls) == 2  # ab + ba, once


def _git(log, status=""):
    return lambda *args: log if args[0] == "log" else status


def test_ensure_preregistered_refuses_uncommitted_or_missing_holdout(tmp_path):
    (tmp_path / "preregistration.md").write_text("x")
    with pytest.raises(RuntimeError, match="committed"):
        judge.ensure_preregistered(tmp_path, run_git=_git(""))
    with pytest.raises(RuntimeError, match="committed"):
        judge.ensure_preregistered(tmp_path, run_git=_git("abc123", " M preregistration.md"))
    with pytest.raises(RuntimeError, match="hold-out"):
        judge.ensure_preregistered(tmp_path, run_git=_git("abc123"))
    (tmp_path / "holdout").mkdir()
    (tmp_path / "holdout" / "pairs.jsonl").write_text("")
    judge.ensure_preregistered(tmp_path, run_git=_git("abc123"))


def test_rules_on_hand_worked_grades():
    g = ["equivalent", "minor_loss", "minor_loss", "partial"]  # idx 0,1,1,2 -> mean 1.0
    assert not ensemble.substitutable("R1_unanimous", g)
    assert ensemble.substitutable("R2_majority", g)
    assert ensemble.substitutable("R3_ordinal_mean", g)
    h = ["minor_loss", "minor_loss", "partial", "divergent"]  # idx 1,1,2,3 -> mean 1.75
    assert not ensemble.substitutable("R2_majority", h)
    assert not ensemble.substitutable("R3_ordinal_mean", h)
    k = ["equivalent", "equivalent", "partial", "partial"]  # mean 1.0, 2 of 4
    assert not ensemble.substitutable("R2_majority", k)
    assert ensemble.substitutable("R3_ordinal_mean", k)
    with pytest.raises(ValueError):
        ensemble.substitutable("R1_unanimous", g[:3])


def _j(pid, judge_, o, grade, status="ok"):
    return records.Judgement(pid, judge_, o, status, grade, "")


def test_grades_by_pair_requires_all_four_and_latest_wins():
    rows = [_j("p", "A", "ab", "partial"), _j("p", "A", "ab", "equivalent"),
            _j("p", "A", "ba", "equivalent"), _j("p", "B", "ab", "equivalent"),
            _j("p", "B", "ba", "equivalent"),
            _j("q", "A", "ab", "equivalent"), _j("q", "A", "ba", "equivalent"),
            _j("q", "B", "ab", "equivalent"), _j("q", "B", "ba", None, "missing")]
    got = ensemble.grades_by_pair(rows, judges=("A", "B"), orientations=("ab", "ba"))
    assert got == {"p": ["equivalent"] * 4}


def test_choose_rule_prefers_conservative_on_ties_and_skips_undefined():
    tie = {"R1_unanimous": 0.5, "R2_majority": 0.5, "R3_ordinal_mean": 0.4}
    assert ensemble.choose_rule(tie) == "R1_unanimous"
    partial = {"R1_unanimous": None, "R2_majority": 0.2, "R3_ordinal_mean": 0.3}
    assert ensemble.choose_rule(partial) == "R3_ordinal_mean"
    with pytest.raises(ValueError):
        ensemble.choose_rule({r: None for r in ensemble.RULES})


def test_rule_kappas_against_human():
    grades = {"a": ["equivalent"] * 4, "b": ["divergent"] * 4,
              "c": ["equivalent", "equivalent", "equivalent", "partial"]}
    human = {"a": "equivalent", "b": "partial", "c": "minor_loss", "z": "equivalent"}
    got = validate.rule_kappas(grades, human)
    assert got["R2_majority"] == pytest.approx(1.0)
    assert got["R3_ordinal_mean"] == pytest.approx(1.0)
    assert got["R1_unanimous"] < 1.0


def test_position_flip_rate_counts_binary_changes_only():
    rows = [_j("p", "A", "ab", "equivalent"), _j("p", "A", "ba", "minor_loss"),
            _j("q", "A", "ab", "equivalent"), _j("q", "A", "ba", "divergent"),
            _j("r", "A", "ab", "equivalent")]
    assert validate.position_flip_rate(rows, "A") == pytest.approx(0.5)


def test_holdout_agreement_pending_without_labels():
    got = validate.holdout_agreement({"p": ["equivalent"] * 4}, {}, "R1_unanimous", seed=1)
    assert got["status"] == "pending" and got["labelled"] == 0


@pytest.mark.parametrize("local_ok, economy_ok, want", [
    (True, None, "local"), (True, False, "local"), (False, True, "economy"),
    (False, False, "frontier"), (None, True, None), (False, None, None),
])
def test_tier_for(local_ok, economy_ok, want):
    assert tiers.tier_for(local_ok, economy_ok) == want


def test_build_tiers_uses_the_named_local_role():
    prompts = {"es": [records.PromptRow("p", "code", "s", "x", "corpus")]}
    grades = {"es:qwen7b:p": ["divergent"] * 4, "es:llama3b:p": ["equivalent"] * 4,
              "es:haiku:p": ["equivalent"] * 4}
    q = tiers.build_tiers(prompts, grades, "R1_unanimous", local_role="qwen7b")
    lo = tiers.build_tiers(prompts, grades, "R1_unanimous", local_role="llama3b")
    assert q[0]["tier"] == "economy" and lo[0]["tier"] == "local"
