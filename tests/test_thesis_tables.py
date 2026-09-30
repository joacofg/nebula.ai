import json
from pathlib import Path

import pytest

from scripts.thesis import blocks, tables


def _write(root: Path, name: str, body: str) -> Path:
    path = root / name
    path.write_text(body, encoding="utf-8")
    return path


def test_find_blocks_across_files(tmp_path):
    _write(tmp_path, "a.md", "x\n<!-- GEN:one -->\nold\n<!-- /GEN:one -->\n")
    _write(tmp_path, "b.md", "<!-- GEN:two -->\n\n<!-- /GEN:two -->\n")
    assert blocks.find_blocks(tmp_path) == {"one": tmp_path / "a.md", "two": tmp_path / "b.md"}


def test_marker_quoted_inline_is_not_a_block(tmp_path):
    _write(tmp_path, "README.md", "Los bloques `<!-- GEN:nombre -->` no se editan a mano.\n")
    assert blocks.find_blocks(tmp_path) == {}


def test_duplicate_block_name_is_an_error(tmp_path):
    _write(tmp_path, "a.md", "<!-- GEN:one -->\nx\n<!-- /GEN:one -->\n")
    _write(tmp_path, "b.md", "<!-- GEN:one -->\ny\n<!-- /GEN:one -->\n")
    with pytest.raises(blocks.BlockError, match="one"):
        blocks.find_blocks(tmp_path)


def test_replace_is_literal():
    text = "<!-- GEN:one -->\nold\n<!-- /GEN:one -->"
    out = blocks.replace_block(text, "one", r"ruta C:\1 y \g<0>")
    assert out == "<!-- GEN:one -->\nruta C:\\1 y \\g<0>\n<!-- /GEN:one -->"


def test_missing_block_is_an_error():
    with pytest.raises(blocks.BlockError, match="nope"):
        blocks.replace_block("sin bloques", "nope", "x")


def test_apply_reports_stale_and_check_does_not_write(tmp_path):
    path = _write(tmp_path, "a.md", "<!-- GEN:one -->\nold\n<!-- /GEN:one -->\n")
    assert blocks.apply({"one": "new"}, tmp_path, write=False) == ["one"]
    assert "old" in path.read_text(encoding="utf-8")
    assert blocks.apply({"one": "new"}, tmp_path, write=True) == ["one"]
    assert blocks.apply({"one": "new"}, tmp_path, write=False) == []


def test_apply_rejects_unknown_and_missing_names(tmp_path):
    _write(tmp_path, "a.md", "<!-- GEN:one -->\nold\n<!-- /GEN:one -->\n")
    with pytest.raises(blocks.BlockError, match="two"):
        blocks.apply({"one": "x", "two": "y"}, tmp_path, write=False)
    with pytest.raises(blocks.BlockError, match="one"):
        blocks.apply({}, tmp_path, write=False)


def test_update_block_finds_the_file(tmp_path):
    path = _write(tmp_path, "b.md", "a\n<!-- GEN:two -->\nold\n<!-- /GEN:two -->\nz\n")
    blocks.update_block("two", "new", tmp_path)
    assert path.read_text(encoding="utf-8") == "a\n<!-- GEN:two -->\nnew\n<!-- /GEN:two -->\nz\n"


def _run(tmp: Path, run_id: str, cost: float, avoided: float, routes: dict) -> None:
    folder = tmp / run_id
    folder.mkdir()
    summary = {"total_requests": 14, "passed": 14, "estimated_premium_cost": cost,
               "estimated_premium_cost_avoided": avoided, "route_distribution": routes}
    (folder / "report.json").write_text(json.dumps({"run_id": run_id, "summary": summary}))


def test_baseline_savings_uses_avoided_over_total(tmp_path):
    routes = {"premium": 6, "local": 5, "cache": 3}
    _run(tmp_path, "20260819T225557Z", 0.0002196, 0.0001536, routes)
    _run(tmp_path, "20260819T225703Z", 0.0002196, 0.0001356, routes)
    _run(tmp_path, "20260819T225713Z", 0.0002196, 0.0001464, routes)
    text = tables.baseline_savings(tmp_path)
    assert "41.2 % (corrida 20260819T225557Z)" in text
    assert "38.2 % (corrida 20260819T225703Z)" in text
    assert "40.0 % (corrida 20260819T225713Z)" in text
    assert "14/14" in text and "8 de 14" in text


def test_missing_report_names_the_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="20260819"):
        tables.baseline_savings(tmp_path)


def test_router_tables_are_markdown():
    report = json.loads(Path("benchmarks/router/v1/report.json").read_text())
    fixed = tables.router_fixed_policies(report)
    assert fixed.startswith("| Política |") and "todo frontier" in fixed and "2.47" in fixed
    assert "| R1" in tables.router_sensitivity(report)
    latency = json.loads(Path("benchmarks/router/v1/latency.json").read_text())
    assert "qwen2.5:7b | 21.3" in tables.router_latency(latency)


def test_metric_validation_block_cites_the_cosine_auc():
    text = tables.metric_validation(Path("benchmarks/metric-validation"))
    assert "AUC 0.25" in text and "22 pares" in text


def test_repo_thesis_is_up_to_date():
    assert tables.main(["--check"]) == 0
