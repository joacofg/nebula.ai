from __future__ import annotations

import json


from collections import Counter

import pytest

from scripts.ground_truth import cli, records, sample, sources
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
