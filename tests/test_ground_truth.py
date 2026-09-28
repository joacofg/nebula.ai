from __future__ import annotations

import json


from scripts.ground_truth import cli, records


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
