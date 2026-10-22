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


def test_frontier_figure_plots_the_curve_and_the_baselines(tmp_path):
    from scripts.thesis import figures

    report = json.loads(Path("benchmarks/router/v1/report.json").read_text())
    fig = figures.frontier_figure(report)
    ax = fig.axes[0]
    assert len(ax.lines) == 1
    assert len(ax.lines[0].get_xdata()) == len(report["learned"]["pareto"])
    labels = " ".join(t.get_text() for t in ax.texts)
    for label in ("todo local", "todo económico", "todo frontier", "heurística", "objetivo 0.95"):
        assert label in labels
    written = figures.write_frontier(report, tmp_path / "frontera")
    assert [p.suffix for p in written] == [".png", ".svg"]
    assert all(p.stat().st_size > 0 for p in written)


def test_tier_distribution_table_totals_each_rule_and_language():
    report = json.loads(Path("benchmarks/ground-truth/v1/report.json").read_text())
    text = tables.tier_distribution(report)
    assert "| R3 media ordinal (elegida) | español | 742 | 174 | 84 |" in text
    assert "| R3 con llama3.2:3b como local | español | 615 | 281 | 104 |" in text
    assert "| código |" in text


def test_cost_at_quality_compares_the_classifiers():
    report = json.loads(Path("benchmarks/router/v1/report.json").read_text())
    text = tables.router_cost_at_quality(report)
    assert "| regresión logística (elegida) | 0.56 | 1.01 | 1.70 |" in text
    assert "| kNN (k = 20) | 0.64 | 1.06 | 1.76 |" in text
    assert "| mezcla aleatoria de niveles | 0.96 | 1.47 | 1.97 |" in text


def test_a_report_missing_a_key_names_the_block_and_the_file(monkeypatch, capsys):
    report = json.loads(Path("benchmarks/router/v1/report.json").read_text())
    del report["knn"]
    real = tables._json
    monkeypatch.setattr(tables, "_json", lambda p: report if p == tables.ROUTER / "report.json" else real(p))
    assert tables.main(["--check"]) == 2
    err = capsys.readouterr().err
    assert "router-cost-at-quality" in err and "benchmarks/router/v1/report.json" in err


def test_metric_validation_block_reports_the_pilot_judges_kappa():
    text = tables.metric_validation(Path("benchmarks/metric-validation"))
    assert "κ binario" in text and "0.09" in text and "-0.05" in text


# Expected figures below are copied from benchmarks/cache/v1/report.md, the human-readable report.
def _cache_report() -> dict:
    return json.loads(Path("benchmarks/cache/v1/report.json").read_text(encoding="utf-8"))


def test_cache_verdict_block_states_no_safe_threshold_and_the_new_default():
    text = tables.cache_verdict(_cache_report())
    assert "ningún umbral de la grilla" in text
    assert "0.453 en PAWS-X y 0.803 en el replay" in text
    assert "0.620 en PAWS-X y 0.920 en el replay" in text
    assert "pasa a 0.99" in text
    assert "`nomic-embed-text-v2-moe`" in text and "0.98" in text


def test_cache_verdict_block_keeps_the_default_on_a_pass():
    report = _cache_report()
    report["preregistration"] |= {"verdict": "pass", "recommended_t": None, "product_default_t": 0.9,
                                  "at_recommended": None}
    text = tables.cache_verdict(report)
    assert "es seguro en el umbral pre-registrado, 0.90" in text and "sigue en 0.90" in text


def test_cache_grid_marks_the_registered_and_the_recommended_threshold():
    text = tables.cache_grid(_cache_report())
    assert text.startswith("| Umbral |")
    assert "| 0.90 (pre-registrado) | 1805 | 0.453 | 0.901 | 173 | 0.803 | 0.803 |" in text
    assert "| 0.99 (recomendado) | 245 | 0.620 | 0.168 | 25 | 0.920 | 0.133 |" in text
    assert "| 0.80 | 1978 | 0.451 | 0.985 | 439 | 0.380 | 0.965 |" in text


def test_cache_pawsx_block_gives_the_paraphrase_share_and_the_precision_range():
    text = tables.cache_pawsx(_cache_report())
    assert "1999 pares" in text and "907" in text and "0.454 del total" in text
    assert "de 0.451 a 0.620" in text and "de 0.454 a 0.679" in text


def test_cache_replay_block_counts_valid_paraphrases_and_leaves_the_human_check_pending():
    text = tables.cache_replay(_cache_report())
    assert "173 de las 200" in text and "22 por cortas" in text
    assert "mediana 0.957" in text
    assert "139 aciertos correctos y 34 falsos" in text
    assert "revisión humana de la muestra de paráfrasis: pendiente" in text


def test_cache_replay_block_reports_the_human_check_once_labeled():
    report = _cache_report()
    report["paraphrase_validation"] = {"sample": 40, "labeled": 40, "si": 33, "no": 5, "unsure": 2,
                                       "faithful_rate": 33 / 38}
    text = tables.cache_replay(report)
    assert "pendiente" not in text
    assert "40 de 40" in text and "0.868" in text


def test_cache_neighbors_block_gives_the_bands_and_leaves_the_labels_pending():
    text = tables.cache_neighbors(_cache_report())
    assert "265 pares" in text
    assert "6 desde 0.95, 14 entre 0.90 y 0.95 y 245 entre 0.85 y 0.90" in text
    assert "revisión humana de esos pares: pendiente" in text


def test_cache_neighbors_block_reports_the_agreement_once_labeled():
    report = _cache_report()
    neighbors = report["neighbors"]
    for band in neighbors["bands"]:
        band |= {"si": 1, "no": 3, "unsure": 0, "unlabeled": band["pairs"] - 4, "acceptable_share": 0.25}
    neighbors["human_labels"] = {"pairs": 265, "labeled": 200, "decided": 190,
                                 "agreement": {"0.90": 0.8, "0.99": 0.75}}
    text = tables.cache_neighbors(report)
    assert "pendiente" not in text
    assert "200 de 265" in text and "0.800 en 0.90" in text and "0.250" in text


def test_cache_savings_compare_the_cache_with_the_router_on_the_same_trace():
    text = tables.cache_savings(_cache_report())
    assert "| 0 % | 1.848 | 0.988 | 1.846 | 0.1 % | 0.987 | 1.5 % | 0.971 |" in text
    assert ("| 12.1 % (duplicados de LMSYS-Chat-1M) | 1.843 | 0.991 | 1.698 | 7.9 % | 0.990 | 11.4 % "
            "| 0.980 |") in text
    assert "| 31 % (MeanCache) | 1.899 | 0.991 | 1.405 | 26.0 % | 0.990 | 30.5 % | 0.985 |" in text
    assert "USD 1.706" in text and "USD 1.70)" in text and "USD 1.848" in text


def test_cache_savings_label_only_the_repetition_rates_checked_in_their_source():
    text = tables.cache_savings(_cache_report())
    assert "WildChat" not in text and "| 3.7 %" not in text


def test_the_cache_test_case_follows_the_registered_verdict():
    obtained, status = tables.cache_test_case(_cache_report())
    assert status == "F"
    assert "0.453" in obtained and "0.620" in obtained and "0.920" in obtained
    for name in ("11-implantacion.md", "14-anexos.md"):
        lines = (tables.THESIS_DIR / name).read_text(encoding="utf-8").splitlines()
        row = next(line for line in lines if line.startswith("| CP-18 |"))
        assert f"| {obtained} | {status} |" in row


def test_a_cache_report_missing_a_key_names_the_block_and_the_file(monkeypatch, capsys):
    report = _cache_report()
    del report["savings"]
    real = tables._json
    monkeypatch.setattr(tables, "_json", lambda p: report if p == tables.CACHE / "report.json" else real(p))
    assert tables.main(["--check"]) == 2
    err = capsys.readouterr().err
    assert "cache-savings" in err and "benchmarks/cache/v1/report.json" in err
