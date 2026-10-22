"""Regenerate every generated block of the thesis from the committed reports.

    python -m scripts.thesis.tables [--check]

Reads only what is versioned under ``benchmarks/``: no network, no training.
``--check`` writes nothing and exits 1 when a block is stale.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from scripts.metric_validation import rubric
from scripts.thesis import blocks

THESIS_DIR = Path("docs/tfc/tesis")
GT_ROOT = Path("benchmarks/ground-truth/v1")
ROUTER = Path("benchmarks/router/v1")
RESULTS = Path("benchmarks/results")
METRIC = Path("benchmarks/metric-validation")
BASELINE_RUNS = ("20260819T225557Z", "20260819T225703Z", "20260819T225713Z")
POLICY_NAMES = {
    "all_local": "todo local (qwen2.5:7b)",
    "all_economy": "todo económico (claude-haiku-4.5)",
    "all_frontier": "todo frontier (gpt-4.1)",
    "oracle": "oráculo",
    "heuristic_premium_frontier": "heurística de dos reglas → frontier",
    "heuristic_premium_economy": "heurística de dos reglas → económico",
}
LABEL_RULES = {"tiers.R1_unanimous.jsonl": "R1 unanimidad", "tiers.R2_majority.jsonl": "R2 mayoría"}
FRONTIER_LEVELS = (0.80, 0.85, 0.90, 0.95, 0.98)
TIER_FILES = {
    "tiers.R1_unanimous.jsonl": "R1 unanimidad",
    "tiers.R2_majority.jsonl": "R2 mayoría",
    "tiers.R3_ordinal_mean.jsonl": "R3 media ordinal (elegida)",
    "tiers.llama3b.jsonl": "R3 con llama3.2:3b como local",
}
LANGS = {"es": "español", "en": "inglés"}
TASKS = {"code": "código", "factual_qa": "preguntas factuales", "multistep_reasoning": "razonamiento",
         "open_writing": "escritura abierta", "summarisation": "resumen"}
CACHE = Path("benchmarks/cache/v1")
# Thresholds of the cache grid table (the recommended one is always added); the full grid is in
# benchmarks/cache/v1/report.md.
CACHE_GRID_SHOWN = (0.80, 0.85, 0.90, 0.95, 0.96, 0.97, 0.98, 0.99)
# Cited repetition rates of the savings trace that get a labeled row. Only a rate found in its
# primary source is printed: the 3.7 % the trace attributes to WildChat is not a repetition rate in
# the WildChat paper (there it is the share of conversations longer than ten turns), so its row is
# left out of the thesis.
CITED_RATES = {"lmsys_exact_duplicates": "duplicados de LMSYS-Chat-1M", "meancache": "MeanCache"}
DROP_REASONS = {"too_short": "por cortas", "too_long": "por largas",
                "empty_or_identical": "por vacías o idénticas al original"}
PENDING = "pendiente"


def _json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"missing report {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _pct(x: float, digits: int = 1) -> str:
    return f"{x * 100:.{digits}f} %"


def _usd(cost_per_prompt: float) -> str:
    return f"{cost_per_prompt * 1000:.2f}"


def baseline_savings(runs_dir: Path) -> str:
    parts, served = [], set()
    for run_id in BASELINE_RUNS:
        s = _json(runs_dir / run_id / "report.json")["summary"]
        avoided, spent = s["estimated_premium_cost_avoided"], s["estimated_premium_cost"]
        parts.append(f"{_pct(avoided / (spent + avoided))} (corrida {run_id})")
        routes = s["route_distribution"]
        served.add((s["passed"], s["total_requests"], routes.get("local", 0) + routes.get("cache", 0)))
    if len(served) != 1:
        raise ValueError(f"baseline runs disagree on scenarios or routes: {sorted(served)}")
    passed, total, cheap = served.pop()
    return (f"Línea de base (heurística de dos reglas, {total} escenarios, 2026-08-19): "
            f"{', '.join(parts)} de gasto premium evitado. En cada corrida pasaron "
            f"{passed}/{total} escenarios y {cheap} de {total} pedidos se sirvieron por el modelo "
            f"local o por el caché. Estas corridas no miden la calidad de lo que se sirvió.")


def _labels(root: Path, rater: str) -> dict[str, str]:
    path = root / "labels" / f"{rater}.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"missing labels {path}")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {row["pair_id"]: row["grade"] for row in rows}


def metric_validation(root: Path) -> str:
    r = _json(root / "report.json")
    raters = _json(root / "raters.json")
    chosen = r["chosen_prefix"]
    natural = next(p for p in r["prefix_sweep_natural"] if p["prefix"] == chosen)
    ci = natural["auc_ci"]
    scale = {s["kind"]: s for s in r["scale_by_kind"]}
    labels = {rater: _labels(root, rater) for rater in r["raters"]}
    shared = sorted(labels[r["reference_rater"]])
    rates = []
    for rater in r["raters"]:
        info = raters[rater]
        who = "el lector humano" if info["kind"] == "human" else info["note"].split(",")[0]
        subs = sum(rubric.is_substitutable(labels[rater][p]) for p in shared)
        rates.append(f"{who} {_pct(subs / len(shared), 0)}")
    kappas = []
    for a in r["agreements"]:
        if a["left_rater"] == r["reference_rater"]:
            who = raters[a["right_rater"]]["note"].split(",")[0]
            kappas.append(f"{a['cohens_kappa_binary']:.2f} para {who}")
    return (f"Sobre {natural['pairs']} pares en inglés con nota humana, la similitud coseno del "
            f"embedding (prefijo `{chosen}`) separó las respuestas sustituibles de las que no lo eran "
            f"con AUC {natural['auc']:.2f} (IC 95 % {ci['low']:.2f}–{ci['high']:.2f}), por debajo "
            f"del azar. La mediana del coseno entre una respuesta local y una premium fue "
            f"{scale['local_vs_premium']['median']:.3f}, prácticamente la misma que entre dos modelos "
            f"premium ({scale['premium_vs_premium']['median']:.3f}): en ese rango la métrica está "
            f"saturada y no distingue calidad. En esos mismos pares, la proporción juzgada sustituible "
            f"fue {', '.join(rates)}. El acuerdo de esos dos jueces con el lector, medido con el κ "
            f"binario de Cohen, fue {' y '.join(kappas)}.")


def router_fixed_policies(report: dict) -> str:
    rows = ["| Política | Costo (USD cada 1000 prompts) | Calidad |", "|---|---|---|"]
    for key, label in POLICY_NAMES.items():
        p = report["baselines"][key]
        rows.append(f"| {label} | {_usd(p['cost'])} | {p['quality']:.3f} |")
    n = report["nested"]["0.95"]
    rows.append(f"| router aprendido, objetivo 0.95 (estimación anidada) | {_usd(n['cost'])} | "
                f"{n['quality']:.3f} |")
    return "\n".join(rows)


def router_sensitivity(report: dict) -> str:
    levels = sorted(report["learned"]["cost_at"], key=float)
    rows = ["| Regla de etiquetado | " + " | ".join(f"calidad ≥ {float(q):.2f}" for q in levels)
            + " | todo frontier |", "|---|" + "---|" * (len(levels) + 1)]
    for key, v in report["sensitivity"].items():
        rows.append(f"| {LABEL_RULES.get(key, key)} | "
                    + " | ".join(_usd(v["cost_at"][q]) for q in levels)
                    + f" | {_usd(v['all_frontier_cost'])} |")
    main = report["learned"]["cost_at"]
    rows.append("| R3 media ordinal (elegida) | " + " | ".join(_usd(main[q]) for q in levels)
                + f" | {_usd(report['baselines']['all_frontier']['cost'])} |")
    return "\n".join(rows)


def router_cost_at_quality(report: dict) -> str:
    levels = sorted(report["learned"]["cost_at"], key=float)
    rows = ["| Política | " + " | ".join(f"calidad ≥ {float(q):.2f}" for q in levels) + " |",
            "|---|" + "---|" * len(levels)]
    for label, costs in (("regresión logística (elegida)", report["learned"]["cost_at"]),
                         ("kNN (k = 20)", report["knn"]["cost_at"]),
                         ("mezcla aleatoria de niveles", report["random_cost_at"])):
        rows.append(f"| {label} | " + " | ".join(_usd(costs[q]) for q in levels) + " |")
    return "\n".join(rows)


def router_latency(latency: dict) -> str:
    rows = ["| Modelo | Mediana (s) | p90 (s) | Respuestas |", "|---|---|---|---|"]
    for v in sorted(latency.values(), key=lambda v: v["median_s"]):
        rows.append(f"| {v['model']} | {v['median_s']:.1f} | {v['p90_s']:.1f} | {v['n']} |")
    return "\n".join(rows)


def router_frontier_points(report: dict) -> str:
    pareto = report["learned"]["pareto"]
    rows = ["| Calidad mínima | τ local | τ económico | Costo (USD cada 1000) | Local | Económico | "
            "Frontier |", "|---|---|---|---|---|---|---|"]
    for q in FRONTIER_LEVELS:
        p = min((p for p in pareto if p["quality"] >= q), key=lambda p: p["cost"])
        s = p["share"]
        rows.append(f"| {q:.2f} | {p['tau_local']:.2f} | {p['tau_economy']:.2f} | {_usd(p['cost'])} | "
                    f"{_pct(s['local'], 0)} | {_pct(s['economy'], 0)} | {_pct(s['frontier'], 0)} |")
    return "\n".join(rows)


def tier_distribution(gt_report: dict) -> str:
    tiers = ("local", "economy", "frontier")
    rows = ["| Regla | Idioma | Local | Económico | Frontier |", "|---|---|---|---|---|"]
    for name, label in TIER_FILES.items():
        for lang, by_task in gt_report["tiers"][name]["distribution"].items():
            totals = [sum(c[t] for c in by_task.values()) for t in tiers]
            rows.append(f"| {label} | {LANGS[lang]} | " + " | ".join(map(str, totals)) + " |")
    chosen = gt_report["tiers"]["tiers.R3_ordinal_mean.jsonl"]["distribution"]["es"]
    rows += ["", "| Tarea (español, R3) | Local | Económico | Frontier |", "|---|---|---|---|"]
    for task, label in TASKS.items():
        c = chosen[task]
        rows.append(f"| {label} | " + " | ".join(str(c[t]) for t in tiers) + " |")
    return "\n".join(rows)


def _t(t: float) -> str:
    return f"{t:.2f}"


def _n3(x: float | None) -> str:
    return "—" if x is None else f"{x:.3f}"


def _rate(r: float) -> str:
    return f"{r * 100:.1f}".removesuffix(".0") + " %"


def _join(items: list[str]) -> str:
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " y " + items[-1]


def _cache_models(report: dict) -> list[dict]:
    """The production embedding first, then the sensitivity ones."""
    return [report["models"]["production"], *report["models"]["sensitivity"]]


def _cache_verdict_sentence(pre: dict) -> str:
    d, r = pre["at_default"], pre["at_recommended"]
    default, product, verdict = _t(pre["default_t"]), _t(pre["product_default_t"]), pre["verdict"]
    if verdict == "not_measurable":
        return (f"ningún umbral de la grilla tiene al menos {pre['min_hits']} aciertos en los dos conjuntos, "
                f"así que el resultado es «no medible con estos datos». El valor por defecto del producto "
                f"sigue en {product}.")
    at_default = f"{_n3(d['precision_a'])} en PAWS-X y {_n3(d['precision_c'])} en el replay"
    if verdict == "pass":
        return (f"el caché es seguro en el umbral pre-registrado, {default}: la precisión fue {at_default}, "
                f"con cobertura {_n3(d['recall_a'])} y {_n3(d['recall_c'])}. El valor por defecto del "
                f"producto sigue en {product}.")
    at_rec = f"{_n3(r['precision_a'])} en PAWS-X y {_n3(r['precision_c'])} en el replay"
    recall = f"su cobertura es {_n3(r['recall_a'])} en PAWS-X y {_n3(r['recall_c'])} en el replay"
    if verdict == "fail":
        return (f"el umbral pre-registrado, {default}, no es seguro: la precisión fue {at_default}. El menor "
                f"umbral seguro de la grilla es {_t(r['t'])}, con precisión {at_rec}; {recall}. El valor por "
                f"defecto para los tenants nuevos pasa a {product}.")
    if verdict == "no_safe_threshold":
        return (f"ningún umbral de la grilla es seguro. En el umbral pre-registrado, {default}, la precisión "
                f"fue {at_default}. El umbral recomendado es {_t(r['t'])}, el de mayor precisión mínima entre "
                f"los dos conjuntos ({at_rec}), que no llega a {_t(pre['criterion'])}; {recall}. El valor por "
                f"defecto para los tenants nuevos pasa a {product}.")
    raise ValueError(f"unknown cache verdict {verdict!r}")


def _cache_sensitivity_sentence(model: dict) -> str:
    v, d, r = model["verdict"], model["at_default"], model["at_recommended"]
    if v["verdict"] == "pass":
        outcome = f"daría un umbral seguro en {_t(v['default_t'])}"
    elif v["verdict"] == "fail":
        outcome = f"daría un umbral seguro desde {_t(r['t'])}"
    elif v["verdict"] == "no_safe_threshold":
        outcome = (f"no daría ningún umbral seguro (recomendaría {_t(r['t'])}, con precisión "
                   f"{_n3(r['precision_a'])} en PAWS-X y {_n3(r['precision_c'])} en el replay)")
    elif v["verdict"] == "not_measurable":
        outcome = "no podría medirse con estos datos"
    else:
        raise ValueError(f"unknown cache verdict {v['verdict']!r}")
    return (f"Con `{model['name']}`, medido solo como sensibilidad, la precisión en "
            f"{_t(v['default_t'])} es {_n3(d['precision_a'])} en PAWS-X y {_n3(d['precision_c'])} en "
            f"el replay, y la misma regla {outcome}; no cambia nada en el producto.")


def cache_verdict(report: dict) -> str:
    """The pre-registered verdict of the cache measurement and what it does to the product default."""
    pre = report["preregistration"]
    grid = [p["t"] for p in pre["grid"]]
    text = (f"Con el embedding de producción (`{pre['model']}`), la grilla de umbrales va de {_t(min(grid))} "
            f"a {_t(max(grid))}, y un umbral cuenta solo si tiene al menos {pre['min_hits']} aciertos en cada "
            f"conjunto. Resultado: {_cache_verdict_sentence(pre)}")
    return " ".join([text, *(_cache_sensitivity_sentence(m) for m in report["models"]["sensitivity"])])


def cache_test_case(report: dict) -> tuple[str, str]:
    """The obtained result and the P/F status of test case CP-18 (the pre-registered criterion)."""
    pre = report["preregistration"]
    d, r, verdict = pre["at_default"], pre["at_recommended"], pre["verdict"]
    status = "P" if verdict == "pass" else "F"
    if verdict == "not_measurable":
        return "no medible: ningún umbral tiene aciertos suficientes", status
    at_default = f"en {_t(pre['default_t'])}, {_n3(d['precision_a'])} y {_n3(d['precision_c'])}"
    if verdict == "pass":
        return at_default, status
    at_rec = f"{_t(r['t'])}, {_n3(r['precision_a'])} y {_n3(r['precision_c'])}"
    if verdict == "fail":
        return f"{at_default}; la alcanza desde {at_rec}", status
    if verdict == "no_safe_threshold":
        return f"ningún umbral la alcanza; {at_default}; en el mejor, {at_rec}", status
    raise ValueError(f"unknown cache verdict {verdict!r}")


def cache_grid(report: dict) -> str:
    """Precision and recall of both sets at some grid thresholds, production embedding."""
    pre = report["preregistration"]
    marks = {_t(pre["default_t"]): " (pre-registrado)"}
    shown = {_t(t) for t in CACHE_GRID_SHOWN}
    if pre["recommended_t"] is not None:
        marks[_t(pre["recommended_t"])] = " (recomendado)"
        shown.add(_t(pre["recommended_t"]))
    points = {_t(p["t"]): p for p in pre["grid"]}
    rows = ["| Umbral | PAWS-X: aciertos | PAWS-X: precisión | PAWS-X: cobertura | Replay: aciertos | "
            "Replay: precisión | Replay: cobertura |", "|---|---|---|---|---|---|---|"]
    for t in sorted(shown, key=float):
        p = points[t]
        rows.append(f"| {t}{marks.get(t, '')} | {p['hits_a']} | {_n3(p['precision_a'])} | "
                    f"{_n3(p['recall_a'])} | {p['hits_c']} | {_n3(p['precision_c'])} | {_n3(p['recall_c'])} |")
    return "\n".join(rows)


def cache_pawsx(report: dict) -> str:
    """Set (a): how many PAWS-X pairs are paraphrases, and the precision range of each embedding."""
    models = _cache_models(report)
    first = report["pawsx"][models[0]["key"]]
    ranges = []
    for i, model in enumerate(models):
        curve = [c for c in report["pawsx"][model["key"]]["curve"] if c["precision"] is not None]
        low = min(c["precision"] for c in curve)
        best = max(curve, key=lambda c: c["precision"])
        where = f" (el máximo, en {_t(best['t'])})" if i == 0 else ""
        ranges.append(f"de {_n3(low)} a {_n3(best['precision'])} con `{model['name']}`{where}")
    return (f"El conjunto tiene {first['pairs']} pares de prueba en español, {first['paraphrases']} de ellos "
            f"paráfrasis según su etiqueta ({first['paraphrases'] / first['pairs']:.3f} del total). Sobre la "
            f"grilla, la precisión va {_join(ranges)}.")


def _blocked(n: int) -> str:
    if n == 0:
        return "ningún acierto bloqueado por nivel"
    return "1 acierto bloqueado por nivel" if n == 1 else f"{n} aciertos bloqueados por nivel"


def cache_replay(report: dict) -> str:
    """Set (c): the valid paraphrases, their hits and false hits, the tier rule and the human check."""
    pp, pre = report["paraphrases"], report["preregistration"]
    model = report["models"]["production"]
    data = pp[model["key"]]
    by_kind = sorted(pp["dropped_by_kind"].items(), key=lambda kv: (-kv[1], kv[0]))
    dropped = (_join([f"{n} {DROP_REASONS[kind]}" for kind, n in by_kind]) if by_kind
               else "ninguna")
    cos = data["own_original_cosine"]
    curve = {_t(p["t"]): p for p in data["curve"]}
    ts = list(dict.fromkeys(_t(t) for t in (pre["default_t"], pre["product_default_t"])))
    points = [curve[t] for t in ts]
    hits = (f"En {ts[0]} el replay tuvo {points[0]['correct_hits']} aciertos correctos y "
            f"{points[0]['false_hits']} falsos")
    hits += "".join(f", y en {t}, {p['correct_hits']} correctos y {p['false_hits']} falsos"
                    for t, p in zip(ts[1:], points[1:], strict=True))
    if all(p["loo_hits"] == p["false_hits"] for p in points):
        origin = "Todos los falsos aciertos vienen de originales que encontraron a otro prompt del corpus."
    else:
        origin = ("De los falsos aciertos, " + _join([f"{p['loo_hits']} en {t}" for t, p in zip(ts, points)])
                  + " vienen de originales que encontraron a otro prompt del corpus.")
    tier = pp["tier_vs_original"]
    ordered = sorted(data["tier_rule_on"].items(), key=lambda kv: float(kv[0]))
    rule = _join([f"{_n3(p['precision'])} en {t} ({_blocked(p['tier_blocked'])})" for t, p in ordered])
    text = (f"Cumplen la regla de validez {pp['valid']} de las {pp['registered']} paráfrasis; "
            f"descartadas: {dropped}. El coseno de cada paráfrasis con su original (`{model['name']}`) "
            f"tiene mediana {_n3(cos['median'])}, cuartil inferior {_n3(cos['p25'])} y mínimo "
            f"{_n3(cos['min'])}. {hits}. {origin} Cada paráfrasis se rutea con su propio vector: su nivel "
            f"coincide con el de su original en {tier['same']}, es más alto en {tier['higher']} y más bajo "
            f"en {tier['lower']}. Con la regla de nivel activa, la precisión es {rule}.")
    check = report["paraphrase_validation"]
    if check == PENDING:
        return text + " Estado de la revisión humana de la muestra de paráfrasis: pendiente."
    return text + (f" Revisión humana de la muestra de paráfrasis: {check['labeled']} de {check['sample']} pares "
                   f"revisados; en {check['si']} la paráfrasis pide lo mismo que su original, en {check['no']} no, "
                   f"y {check['unsure']} quedaron en duda (proporción fiel, sin las dudas: "
                   f"{_n3(check['faithful_rate'])}).")


def _band(band: dict) -> str:
    if band["to"] is None:
        return f"desde {_t(band['from'])}"
    return f"entre {_t(band['from'])} y {_t(band['to'])}"


def _band_counts(bands: list[dict]) -> str:
    return _join([f"{band['pairs']} {_band(band)}" for band in bands])


def cache_neighbors(report: dict) -> str:
    """Set (b), descriptive: distinct corpus prompts close to each other, and the human check."""
    n = report["neighbors"]
    models = _cache_models(report)
    lowest = min(b["from"] for b in n["bands"])
    text = (f"Entre los prompts en español del corpus hay {n['pairs']} pares de prompts distintos con "
            f"coseno de {_t(lowest)} o más con `{models[0]['name']}`: {_band_counts(n['bands'])}.")
    for model in models[1:]:
        text += (f" Con `{model['name']}`, entre los mismos prompts: "
                 f"{_band_counts(n[model['key'] + '_bands'])}.")
    human = n["human_labels"]
    if human == PENDING:
        return text + " Estado de la revisión humana de esos pares: pendiente."
    shares = _join([f"{_n3(b['acceptable_share'])} {_band(b)}" for b in n["bands"]])
    ordered = sorted(human["agreement"].items(), key=lambda kv: float(kv[0]))
    agreement = _join([f"{_n3(a)} en {t}" for t, a in ordered])
    return text + (f" Revisión humana de esos pares: {human['labeled']} de {human['pairs']} revisados, "
                   f"{human['decided']} con respuesta sí o no. La proporción en que la respuesta a uno le "
                   f"sirve al otro es {shares}. El acuerdo de la decisión del caché (servir si el coseno "
                   f"llega al umbral) con la del revisor es {agreement}.")


def cache_savings(report: dict) -> str:
    """Cost and quality of the Spanish trace by repetition rate, the cache against the router alone."""
    s, pre = report["savings"], report["preregistration"]
    curves = s[report["models"]["production"]["key"]]
    thresholds = list(dict.fromkeys(_t(t) for t in (pre["product_default_t"], pre["default_t"])))
    by_rate = [{round(p["r"], 3): p for p in curves[t]["curve"]} for t in thresholds]
    labels = {round(s["cited_rates"][key], 3): label for key, label in CITED_RATES.items()}
    unchecked = {round(r, 3) for key, r in s["cited_rates"].items() if key not in CITED_RATES}
    first = thresholds[0]
    header = (f"| Repetición | Router solo: costo | Router solo: calidad | Caché en {first}: costo | "
              f"Caché en {first}: ahorro adicional | Caché en {first}: calidad |")
    for t in thresholds[1:]:
        header += f" Caché en {t}: ahorro adicional | Caché en {t}: calidad |"
    rows = [header, "|---|" + "---|" * (5 + 2 * (len(thresholds) - 1))]
    for r in sorted(set(by_rate[0]) - unchecked):
        points = [curve[r] for curve in by_rate]
        if len({round(p["router_only_cost_per_1000"], 9) for p in points}) != 1:
            raise ValueError(f"the router-only cost of rate {r} differs between thresholds")
        p = points[0]
        label = _rate(r) + (f" ({labels[r]})" if r in labels else "")
        row = (f"| {label} | {p['router_only_cost_per_1000']:.3f} | {p['router_only_quality']:.3f} | "
               f"{p['cost_per_1000']:.3f} | {_pct(p['extra_saving_vs_router'])} | {p['quality']:.3f} |")
        for q in points[1:]:
            row += f" {_pct(q['extra_saving_vs_router'])} | {q['quality']:.3f} |"
        rows.append(row)
    c = s["consistency"]
    if abs(c["r0_router_only_cost_per_1000"] - c["spanish_cost_per_1000"]) > 1e-9:
        raise ValueError("the trace's router-only cost at r = 0 is not the router's cost on the Spanish prompts")
    false_hits = _join([f"{c['r0_false_hits'][t]} en {t}" for t in thresholds])
    note = (f"La traza usa solo los {c['spanish_prompts']} prompts en español. Sobre el corpus completo "
            f"({c['corpus_prompts']} prompts), el router del gateway cuesta USD {c['corpus_cost_per_1000']:.3f} "
            f"cada mil (la tesis cita la estimación anidada, USD {c['cited_cost_per_1000']:.2f}); sobre los "
            f"prompts en español, que son más caros de rutear, cuesta USD {c['spanish_cost_per_1000']:.3f}, que "
            f"es el costo del router solo en la traza sin repetición. Sin repetición, el caché igual sirve "
            f"algunos pedidos: prompts distintos lo bastante parecidos a uno anterior, que cuentan como falsos "
            f"aciertos ({false_hits}).")
    return "\n".join(rows) + "\n\n" + note


class GeneratorError(ValueError):
    pass


def _render(name: str, source: Path, build) -> str:
    try:
        return build()
    except FileNotFoundError:
        raise
    except (KeyError, ValueError, StopIteration, TypeError, IndexError) as exc:
        raise GeneratorError(f"{name}: {source}: {exc!r}") from exc


def render_all() -> dict[str, str]:
    from scripts.ground_truth import report as gt_report
    from scripts.router import train

    summary = _render("corpus-fase2", GT_ROOT, lambda: gt_report.summarise(GT_ROOT))
    router_path, latency_path, gt_path = ROUTER / "report.json", ROUTER / "latency.json", GT_ROOT / "report.json"
    router, latency = _json(router_path), _json(latency_path)
    cache_path = CACHE / "report.json"
    cache = _json(cache_path)
    blocks_spec = (
        ("corpus-fase2", GT_ROOT, lambda: gt_report.thesis_corpus(summary)),
        ("judges-fase2", GT_ROOT, lambda: gt_report.thesis_judges(summary)),
        ("router-fase3", router_path, lambda: train.thesis_block(router)),
        ("tier-distribution", gt_path, lambda: tier_distribution(_json(gt_path))),
        ("baseline-savings", RESULTS, lambda: baseline_savings(RESULTS)),
        ("metric-validation", METRIC, lambda: metric_validation(METRIC)),
        ("router-fixed-policies", router_path, lambda: router_fixed_policies(router)),
        ("router-sensitivity", router_path, lambda: router_sensitivity(router)),
        ("router-cost-at-quality", router_path, lambda: router_cost_at_quality(router)),
        ("router-latency", latency_path, lambda: router_latency(latency)),
        ("router-frontier-points", router_path, lambda: router_frontier_points(router)),
        ("cache-verdict", cache_path, lambda: cache_verdict(cache)),
        ("cache-grid", cache_path, lambda: cache_grid(cache)),
        ("cache-pawsx", cache_path, lambda: cache_pawsx(cache)),
        ("cache-replay", cache_path, lambda: cache_replay(cache)),
        ("cache-neighbors", cache_path, lambda: cache_neighbors(cache)),
        ("cache-savings", cache_path, lambda: cache_savings(cache)),
    )
    return {name: _render(name, source, build) for name, source, build in blocks_spec}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="write nothing; exit 1 if stale")
    args = parser.parse_args(argv)
    try:
        stale = blocks.apply(render_all(), THESIS_DIR, write=not args.check)
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"thesis-tables: {exc}", file=sys.stderr)
        return 2
    if args.check and stale:
        print("stale GEN blocks: " + ", ".join(stale), file=sys.stderr)
        return 1
    print(("updated: " + ", ".join(stale)) if stale else "thesis tables up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
