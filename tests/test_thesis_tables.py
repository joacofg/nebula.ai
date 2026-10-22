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


def test_apply_rows_reports_a_stale_row_and_check_does_not_write(tmp_path):
    path = _write(tmp_path, "a.md", "| ID | X |\n|---|---|\n| CP-01 | old |\n| CP-02 | keep |\n")
    rows = {"a.md": {"CP-01": "| CP-01 | new |"}}
    assert blocks.apply_rows(rows, tmp_path, write=False) == ["a.md:CP-01"]
    assert "| CP-01 | old |" in path.read_text(encoding="utf-8")
    assert blocks.apply_rows(rows, tmp_path, write=True) == ["a.md:CP-01"]
    assert path.read_text(encoding="utf-8") == "| ID | X |\n|---|---|\n| CP-01 | new |\n| CP-02 | keep |\n"
    assert blocks.apply_rows(rows, tmp_path, write=False) == []


def test_apply_rows_needs_exactly_one_row_with_the_id(tmp_path):
    _write(tmp_path, "a.md", "| CP-01 | x |\n| CP-01 | y |\n")
    _write(tmp_path, "b.md", "sin filas\n")
    with pytest.raises(blocks.BlockError, match="CP-01"):
        blocks.apply_rows({"a.md": {"CP-01": "| CP-01 | z |"}}, tmp_path, write=False)
    with pytest.raises(blocks.BlockError, match="CP-02"):
        blocks.apply_rows({"b.md": {"CP-02": "| CP-02 | z |"}}, tmp_path, write=False)


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
    report = _cache_report()
    report["savings"]["cited_rates"]["unchecked_source"] = 0.05
    with pytest.raises(KeyError, match="unchecked_source"):
        tables.cache_savings(report)


def test_cache_savings_note_explains_the_two_baselines_and_the_trace_composition():
    text = tables.cache_savings(_cache_report())
    assert "este trabajo cita la estimación anidada, USD 1.70" in text
    assert "en r = 40 %, 600 pedidos son prompts nuevos y los otros 400 repiten" in text


def test_the_cache_test_case_follows_the_registered_verdict():
    rows = tables.cache_test_case_rows(_cache_report())
    obtained = "ningún umbral la alcanza; en 0.90, 0.453 y 0.803; en el mejor, 0.99, 0.620 y 0.920"
    assert f"| {obtained} | F |" in rows["11-implantacion.md"]["CP-18"]
    annex = rows["14-anexos.md"]["CP-18"]
    assert f"| {obtained} | F |" in annex
    assert "| 1999 pares de PAWS-X en español; replay con 173 paráfrasis válidas y los 1000 originales; " \
           "umbrales de 0.80 a 0.99 |" in annex
    for name, by_id in rows.items():
        lines = (tables.THESIS_DIR / name).read_text(encoding="utf-8").splitlines()
        assert by_id["CP-18"] in lines


def test_check_fails_when_a_cp18_row_disagrees_with_the_report(monkeypatch, capsys):
    report = _cache_report()
    report["preregistration"]["valid_paraphrases"] = 172
    real = tables._json
    monkeypatch.setattr(tables, "_json", lambda p: report if p == tables.CACHE / "report.json" else real(p))
    assert tables.main(["--check"]) == 1
    assert "14-anexos.md:CP-18" in capsys.readouterr().err


def _verdict(report: dict, verdict: str, recommended: float | None, *, product: float) -> dict:
    pre = report["preregistration"]
    at = next((p for p in pre["grid"] if p["t"] == recommended), None)
    pre |= {"verdict": verdict, "recommended_t": recommended, "product_default_t": product,
            "at_recommended": at}
    return report


def test_cache_blocks_for_a_fail_with_a_safe_threshold():
    report = _verdict(_cache_report(), "fail", 0.95, product=0.95)
    text = tables.cache_verdict(report)
    assert "el umbral pre-registrado, 0.90, no es seguro: la precisión fue 0.453 en PAWS-X" in text
    assert "El menor umbral seguro de la grilla es 0.95, con precisión 0.464 en PAWS-X y 0.913" in text
    assert "pasa a 0.95" in text
    assert tables.cache_test_case(report) == ("en 0.90, 0.453 y 0.803; la alcanza desde 0.95, 0.464 y 0.913", "F")


def test_cache_blocks_for_a_pass_and_for_not_measurable():
    passed = _verdict(_cache_report(), "pass", None, product=0.9)
    assert tables.cache_test_case(passed) == ("en 0.90, 0.453 y 0.803", "P")
    unmeasured = _verdict(_cache_report(), "not_measurable", None, product=0.9)
    text = tables.cache_verdict(unmeasured)
    assert "«no medible con estos datos»" in text and "sigue en 0.90" in text
    assert tables.cache_test_case(unmeasured) == ("no medible: ningún umbral tiene aciertos suficientes", "F")
    with pytest.raises(ValueError, match="unknown cache verdict"):
        tables.cache_test_case(_verdict(_cache_report(), "maybe", None, product=0.9))


@pytest.mark.parametrize(("verdict", "recommended", "expected"), [
    ("pass", None, "la misma regla daría un umbral seguro en 0.90"),
    ("fail", 0.95, "la misma regla daría un umbral seguro desde 0.95"),
    ("not_measurable", None, "la misma regla no podría medirse con estos datos"),
])
def test_cache_verdict_sentence_for_each_sensitivity_outcome(verdict, recommended, expected):
    report = _cache_report()
    model = report["models"]["sensitivity"][0]
    model["verdict"] |= {"verdict": verdict, "recommended_t": recommended}
    model["at_recommended"] = next((p for p in model["grid"] if p["t"] == recommended), None)
    assert expected in tables.cache_verdict(report)


def test_cache_replay_block_with_mixed_false_hits_and_nothing_dropped():
    report = _cache_report()
    paraphrases = report["paraphrases"]
    paraphrases["dropped_by_kind"] = {}
    point = next(p for p in paraphrases["nomic_v1"]["curve"] if p["t"] == 0.9)
    point["loo_hits"] = 30
    text = tables.cache_replay(report)
    assert "descartadas: ninguna" in text
    assert "De los falsos aciertos, 30 en 0.90 y 2 en 0.99 vienen de originales" in text


def test_a_cache_report_missing_a_key_names_the_block_and_the_file(monkeypatch, capsys):
    report = _cache_report()
    del report["savings"]
    real = tables._json
    monkeypatch.setattr(tables, "_json", lambda p: report if p == tables.CACHE / "report.json" else real(p))
    assert tables.main(["--check"]) == 2
    err = capsys.readouterr().err
    assert "cache-savings" in err and "benchmarks/cache/v1/report.json" in err
