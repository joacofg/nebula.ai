"""Train the learned router, trace its frontier, and write the artifact and report.

    python -m scripts.router.train

Scores are out of fold (5 folds grouped by prompt). The frontier traced on
them picks its thresholds on those same scores, so it is an in-sample choice
of two parameters; the headline numbers are the nested estimate, where each
fold is routed with thresholds and weights chosen without it. The shipped
weights are refit on all data and carry the out-of-fold operating points.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from scripts.ground_truth import report as gt_report
from scripts.router import cv, data, embed, frontier, knn, logreg

PREFIX_MARGIN = 0.02
TARGETS = ("local", "economy")
MAIN_LABELS = "tiers.R3_ordinal_mean.jsonl"
SENSITIVITY_LABELS = ("tiers.R1_unanimous.jsonl", "tiers.R2_majority.jsonl")
QUALITY_LEVELS = (0.85, 0.90, 0.95)
DEFAULT_TARGET = 0.95
ARTIFACT = Path("src/nebula/data/learned_router_v1.json")
REPLAY = Path("src/nebula/data/router_replay_v1.json")
REPLAY_TEXT_CHARS = 160
OUT = Path("benchmarks/router/v1")
THESIS = Path("docs/tfc/tesis/06-evaluacion.md")


def choose_prefix(aucs: dict[str, float]) -> str:
    return "classification" if aucs["classification"] - aucs["none"] > PREFIX_MARGIN else "none"


def operating_points(front: list[dict]) -> list[dict]:
    return [
        {"tau_local": p["tau_local"], "tau_economy": p["tau_economy"],
         "quality": p["quality"], "cost_per_prompt": p["cost"]}
        for p in front
    ]


def artifact(*, weights: dict, lambdas: dict, prefix: str, points: list[dict], labels: dict) -> dict:
    return {
        "version": 1,
        "label": "v1",
        "embedding_model": embed.EMBEDDING_MODEL,
        "prefix": prefix,
        "lambda": lambdas,
        "labels": labels,
        "models": {
            name: {"weights": [float(v) for v in w], "bias": float(b)} for name, (w, b) in weights.items()
        },
        "operating_points": points,
    }


def _cheapest_meeting(front: list[dict], q: float) -> tuple[float, float]:
    feasible = [p for p in front if p["quality"] >= q]
    if not feasible:
        return float("inf"), float("inf")
    best = min(feasible, key=lambda p: p["cost"])
    return best["tau_local"], best["tau_economy"]


def nested_tiers(examples, X, fold_of, lambdas, *, quality_target: float) -> list[str]:
    """Per outer fold: pick thresholds on the other folds' out-of-fold scores,
    fit on those folds, route the held-out fold. No test prompt touches either
    the weights or the thresholds that route it."""
    fold_of = np.asarray(fold_of)
    tiers: list[str] = [""] * len(examples)
    for f in sorted(set(fold_of.tolist())):
        train_idx = np.flatnonzero(fold_of != f)
        test_idx = np.flatnonzero(fold_of == f)
        train_ex = [examples[i] for i in train_idx]
        inner, test_p = {}, {}
        for target in TARGETS:
            y = _labels(train_ex, target)
            inner[target] = cv.out_of_fold(X[train_idx], y, fold_of[train_idx], lambdas[target])
            w, b = logreg.fit(X[train_idx], y, lambdas[target])
            test_p[target] = logreg.predict(w, b, X[test_idx])
        front = frontier.pareto(frontier.sweep(inner["local"], inner["economy"], train_ex))
        tau_l, tau_e = _cheapest_meeting(front, quality_target)
        for i, tier in zip(test_idx, frontier.route(test_p["local"], test_p["economy"], tau_l, tau_e)):
            tiers[i] = tier
    return tiers


def bootstrap_savings(examples, tiers, *, resamples: int = 1000, seed: int = 20260930) -> dict:
    """Point estimate and a prompt-grouped percentile interval for the savings
    of a routing against all-frontier and against the random mix at the same quality."""
    cost, quality = frontier.evaluate(tiers, examples)
    all_frontier = frontier.corner_points(examples)["all_frontier"][0]
    random_cost = frontier.random_cost_at_quality(examples, quality)
    groups: dict[str, list[int]] = {}
    for i, e in enumerate(examples):
        groups.setdefault(e.prompt_id, []).append(i)
    ids = sorted(groups)
    rng = np.random.default_rng(seed)
    vs_frontier, vs_random = [], []
    for _ in range(resamples):
        idx = [i for g in rng.choice(len(ids), size=len(ids)) for i in groups[ids[g]]]
        sub = [examples[i] for i in idx]
        c, q = frontier.evaluate([tiers[i] for i in idx], sub)
        af = frontier.corner_points(sub)["all_frontier"][0]
        rc = frontier.random_cost_at_quality(sub, q)
        vs_frontier.append(1 - c / af)
        if rc:
            vs_random.append(1 - c / rc)
    pct = lambda xs: [float(np.percentile(xs, 2.5)), float(np.percentile(xs, 97.5))]  # noqa: E731
    return {
        "cost": cost, "quality": quality, "all_frontier_cost": all_frontier, "random_cost": random_cost,
        "vs_all_frontier": 1 - cost / all_frontier, "vs_all_frontier_ci95": pct(vs_frontier),
        "vs_random": (1 - cost / random_cost) if random_cost else None,
        "vs_random_ci95": pct(vs_random) if vs_random else None,
        "resamples": resamples,
    }


def replay_payload(examples, probs, *, points, baselines, nested, latency) -> dict:
    """What the console's Evaluación page replays: out-of-fold scores, labels and costs."""
    def trim(text: str) -> str:
        text = " ".join(text.split())
        return text if len(text) <= REPLAY_TEXT_CHARS else text[:REPLAY_TEXT_CHARS] + "…"

    return {
        "version": 1,
        "router_label": "v1",
        "rows": [
            {"key": e.key, "lang": e.lang, "task": e.task_type, "text": trim(e.text),
             "p_local": float(probs["local"][i]), "p_economy": float(probs["economy"][i]),
             "local_ok": bool(e.local_ok), "economy_ok": bool(e.economy_ok),
             "cost_economy": float(e.cost_economy), "cost_frontier": float(e.cost_frontier)}
            for i, e in enumerate(examples)
        ],
        "operating_points": points,
        "baselines": baselines,
        "nested": nested,
        "latency": latency,
    }


def _labels(examples: list[data.Example], target: str) -> np.ndarray:
    return np.array([e.local_ok if target == "local" else e.economy_ok for e in examples], dtype=float)


def _matrix(examples: list[data.Example], prefix: str) -> np.ndarray:
    vectors = embed.load_embeddings(prefix)
    return np.array([vectors[e.key] for e in examples])


def _oof(examples, X, fold_of, lambdas=None):
    out, lam_used, losses = {}, {}, {}
    for target in TARGETS:
        y = _labels(examples, target)
        if lambdas is None:
            lam, losses[target] = cv.choose_lambda(X, y, fold_of)
        else:
            lam = lambdas[target]
        lam_used[target] = lam
        out[target] = cv.out_of_fold(X, y, fold_of, lam)
    return out, lam_used, losses


def _aucs(examples, probs) -> dict:
    result = {}
    for target in TARGETS:
        y = _labels(examples, target)
        result[target] = {"all": cv.auc(y, probs[target])}
        for lang in ("es", "en"):
            mask = np.array([e.lang == lang for e in examples])
            result[target][lang] = cv.auc(y[mask], probs[target][mask])
    return result


def _summary_at(front, q):
    feasible = [p for p in front if p["quality"] >= q]
    return min(feasible, key=lambda p: p["cost"]) if feasible else None


def _frontier_block(examples, probs) -> dict:
    points = frontier.sweep(probs["local"], probs["economy"], examples)
    front = frontier.pareto(points)
    return {"pareto": front, "cost_at": {str(q): frontier.cost_at_quality(front, q) for q in QUALITY_LEVELS}}


def run(root: Path = data.GROUND_TRUTH) -> dict:
    examples = data.load_examples(root, MAIN_LABELS)
    fold_of = cv.folds(examples)

    prefix_results = {}
    for prefix in embed.PREFIXES:
        X = _matrix(examples, prefix)
        probs, lambdas, losses = _oof(examples, X, fold_of)
        aucs = _aucs(examples, probs)
        prefix_results[prefix] = {"lambdas": lambdas, "log_loss": losses, "auc": aucs,
                                  "mean_auc": float(np.mean([aucs[t]["all"] for t in TARGETS]))}
    prefix = choose_prefix({p: r["mean_auc"] for p, r in prefix_results.items()})
    lambdas = prefix_results[prefix]["lambdas"]
    X = _matrix(examples, prefix)
    probs, _, _ = _oof(examples, X, fold_of, lambdas)
    main = _frontier_block(examples, probs)

    knn_probs = {t: knn.oof_probabilities(X, _labels(examples, t), fold_of) for t in TARGETS}
    knn_block = _frontier_block(examples, knn_probs)
    knn_block["auc"] = _aucs(examples, knn_probs)

    corners = frontier.corner_points(examples)
    baselines = {name: {"cost": c, "quality": q} for name, (c, q) in corners.items()}
    for tier in ("frontier", "economy"):
        c, q = frontier.evaluate(frontier.heuristic_tiers(examples, premium_tier=tier), examples)
        baselines[f"heuristic_premium_{tier}"] = {"cost": c, "quality": q}
    random_at = {str(q): frontier.random_cost_at_quality(examples, q) for q in QUALITY_LEVELS}
    for name in ("heuristic_premium_frontier", "heuristic_premium_economy"):
        q = baselines[name]["quality"]
        baselines[name]["learned_cost_at_same_quality"] = frontier.cost_at_quality(main["pareto"], q)
        baselines[name]["random_cost_at_same_quality"] = frontier.random_cost_at_quality(examples, q)

    by_lang = {}
    point = _summary_at(main["pareto"], DEFAULT_TARGET)
    if point is not None:
        tiers = frontier.route(probs["local"], probs["economy"], point["tau_local"], point["tau_economy"])
        for lang in ("es", "en"):
            idx = [i for i, e in enumerate(examples) if e.lang == lang]
            sub = [examples[i] for i in idx]
            c, q = frontier.evaluate([tiers[i] for i in idx], sub)
            share = {t: sum(1 for i in idx if tiers[i] == t) / len(idx) for t in ("local", "economy", "frontier")}
            by_lang[lang] = {"cost": c, "quality": q, "share": share}

    sensitivity = {}
    for labels_file in SENSITIVITY_LABELS:
        ex_s = data.load_examples(root, labels_file)
        probs_s, _, _ = _oof(ex_s, X, fold_of, lambdas)
        block = _frontier_block(ex_s, probs_s)
        sensitivity[labels_file] = {
            "cost_at": block["cost_at"],
            "all_frontier_cost": frontier.corner_points(ex_s)["all_frontier"][0],
            "random_at": {str(q): frontier.random_cost_at_quality(ex_s, q) for q in QUALITY_LEVELS},
        }

    weights = {}
    for target in TARGETS:
        weights[target] = logreg.fit(X, _labels(examples, target), lambdas[target])
    labels_path = root / MAIN_LABELS
    raw = artifact(
        weights=weights, lambdas=lambdas, prefix=prefix, points=operating_points(main["pareto"]),
        labels={"file": MAIN_LABELS, "sha256": hashlib.sha256(labels_path.read_bytes()).hexdigest()},
    )

    nested = {}
    for q in (0.90, 0.95):
        tiers = nested_tiers(examples, X, fold_of, lambdas, quality_target=q)
        block = bootstrap_savings(examples, tiers)
        block["by_lang"] = {}
        for lang in ("es", "en"):
            idx = [i for i, e in enumerate(examples) if e.lang == lang]
            c, qq = frontier.evaluate([tiers[i] for i in idx], [examples[i] for i in idx])
            block["by_lang"][lang] = {"cost": c, "quality": qq}
        block["share"] = {t: tiers.count(t) / len(tiers) for t in ("local", "economy", "frontier")}
        nested[str(q)] = block

    latency_path = OUT / "latency.json"
    replay = replay_payload(
        examples, probs, points=raw["operating_points"],
        baselines={k: {"cost": v["cost"], "quality": v["quality"]} for k, v in baselines.items()},
        nested={q: {k: n[k] for k in ("quality", "cost", "vs_all_frontier", "vs_all_frontier_ci95",
                                      "vs_random", "vs_random_ci95", "share", "by_lang")}
                for q, n in nested.items()},
        latency=json.loads(latency_path.read_text()) if latency_path.exists() else {},
    )

    return {
        "replay": replay,
        "nested": nested,
        "examples": len(examples),
        "folds": 5,
        "prefix": {"chosen": prefix, "margin": PREFIX_MARGIN, "results": prefix_results},
        "learned": {"auc": _aucs(examples, probs), **main, "default_target": DEFAULT_TARGET,
                    "default_point": point, "by_lang_at_default": by_lang},
        "knn": knn_block,
        "baselines": baselines,
        "random_cost_at": random_at,
        "sensitivity": sensitivity,
        "artifact": raw,
    }


def _usd(v: float | None, per: int = 1000) -> str:
    return "—" if v is None else f"{v * per:.3f}"


def render_markdown(r: dict) -> str:
    b, learned = r["baselines"], r["learned"]
    out = [
        "# Learned router — v1", "",
        f"{r['examples']} prompts, {r['folds']}-fold CV grouped by prompt. Costs in USD per 1000 prompts.", "",
        "## Classifiers (out-of-fold AUC)", "", "| prefix | target | all | es | en | λ |", "|---|---|---|---|---|---|",
    ]
    for prefix, res in r["prefix"]["results"].items():
        for t in TARGETS:
            a = res["auc"][t]
            out.append(f"| {prefix} | {t} | {a['all']:.3f} | {a['es']:.3f} | {a['en']:.3f} | {res['lambdas'][t]} |")
    out += ["", f"Chosen prefix: `{r['prefix']['chosen']}` (needs > {PREFIX_MARGIN} mean AUC to switch).", "",
            "## Cost at a quality level", "", "| policy | " + " | ".join(f"q ≥ {q}" for q in QUALITY_LEVELS) + " |",
            "|---|" + "---|" * len(QUALITY_LEVELS)]
    out.append("| learned (logistic) | " + " | ".join(_usd(learned["cost_at"][str(q)]) for q in QUALITY_LEVELS) + " |")
    out.append("| kNN (k=20) | " + " | ".join(_usd(r["knn"]["cost_at"][str(q)]) for q in QUALITY_LEVELS) + " |")
    out.append("| random mixture | " + " | ".join(_usd(r["random_cost_at"][str(q)]) for q in QUALITY_LEVELS) + " |")
    out += ["", "## Nested estimate (thresholds and weights chosen without the routed fold)", "",
            "| target | achieved quality | cost | vs all-frontier [95% CI] | vs random at same quality [95% CI] | es quality | en quality |",
            "|---|---|---|---|---|---|---|"]
    for q, n in r["nested"].items():
        vr = "—" if n["vs_random"] is None else (f"{n['vs_random']:.0%} [{n['vs_random_ci95'][0]:.0%}, "
                                                  f"{n['vs_random_ci95'][1]:.0%}]")
        out.append(f"| {q} | {n['quality']:.3f} | {_usd(n['cost'])} | {n['vs_all_frontier']:.0%} "
                   f"[{n['vs_all_frontier_ci95'][0]:.0%}, {n['vs_all_frontier_ci95'][1]:.0%}] | {vr} | "
                   f"{n['by_lang']['es']['quality']:.3f} | {n['by_lang']['en']['quality']:.3f} |")
    latency_path = OUT / "latency.json"
    if latency_path.exists():
        lat = json.loads(latency_path.read_text())
        out += ["", "## Latency (30 Spanish prompts, sequential, this machine)", "",
                "| role | model | median s | p90 s |", "|---|---|---|---|"]
        for role, v in lat.items():
            out.append(f"| {role} | {v['model']} | {v['median_s']:.1f} | {v['p90_s']:.1f} |")
    out += ["", "## Fixed policies", "", "| policy | cost | quality | learned at same quality | random at same quality |",
            "|---|---|---|---|---|"]
    for name, v in b.items():
        out.append(f"| {name} | {_usd(v['cost'])} | {v['quality']:.3f} | {_usd(v.get('learned_cost_at_same_quality'))} "
                   f"| {_usd(v.get('random_cost_at_same_quality'))} |")
    p = learned["default_point"]
    if p:
        out += ["", f"## Default target q ≥ {learned['default_target']}", "",
                f"τ_local {p['tau_local']:.2f}, τ_economy {p['tau_economy']:.2f}: cost {_usd(p['cost'])}, "
                f"quality {p['quality']:.3f}, share " + ", ".join(f"{k} {v:.0%}" for k, v in p["share"].items()), ""]
        for lang, v in learned["by_lang_at_default"].items():
            out.append(f"- {lang}: cost {_usd(v['cost'])}, quality {v['quality']:.3f}, share "
                       + ", ".join(f"{k} {s:.0%}" for k, s in v["share"].items()))
    out += ["", "## Label-rule sensitivity", "", "| labels | " + " | ".join(f"learned q≥{q}" for q in QUALITY_LEVELS)
            + " | all-frontier |", "|---|" + "---|" * (len(QUALITY_LEVELS) + 1)]
    for name, v in r["sensitivity"].items():
        out.append(f"| {name} | " + " | ".join(_usd(v["cost_at"][str(q)]) for q in QUALITY_LEVELS)
                   + f" | {_usd(v['all_frontier_cost'])} |")
    out += ["", "## Pareto frontier (learned)", "", "| τ_local | τ_economy | cost | quality | local | economy | frontier |",
            "|---|---|---|---|---|---|---|"]
    for p in learned["pareto"]:
        out.append(f"| {p['tau_local']:.2f} | {p['tau_economy']:.2f} | {_usd(p['cost'])} | {p['quality']:.3f} | "
                   f"{p['share']['local']:.0%} | {p['share']['economy']:.0%} | {p['share']['frontier']:.0%} |")
    return "\n".join(out) + "\n"


def thesis_block(r: dict) -> str:
    b, learned = r["baselines"], r["learned"]
    af = b["all_frontier"]["cost"]
    n95, n90 = r["nested"]["0.95"], r["nested"]["0.9"]
    h, al = b["heuristic_premium_frontier"], b["all_local"]
    text = (
        f"El router aprendido son dos regresiones logísticas sobre el embedding del prompt "
        f"(prefijo `{r['prefix']['chosen']}`), evaluadas con validación cruzada de 5 folds agrupada por prompt "
        f"sobre {r['examples']} prompts; AUC fuera de fold: local {learned['auc']['local']['all']:.2f}, "
        f"economy {learned['auc']['economy']['all']:.2f}, una señal modesta. En la estimación anidada —umbrales y "
        f"pesos elegidos sin el fold que se rutea— con objetivo de calidad 0.95 el router logra calidad "
        f"{n95['quality']:.3f} a USD {n95['cost'] * 1000:.2f} cada mil prompts, {n95['vs_all_frontier']:.0%} menos "
        f"que enviar todo al modelo frontier (USD {af * 1000:.2f}; IC 95 % {n95['vs_all_frontier_ci95'][0]:.0%}–"
        f"{n95['vs_all_frontier_ci95'][1]:.0%})"
    )
    if n95["vs_random"] is not None:
        text += (f" y {n95['vs_random']:.0%} menos que la mejor mezcla aleatoria de niveles a igual calidad "
                 f"(IC 95 % {n95['vs_random_ci95'][0]:.0%}–{n95['vs_random_ci95'][1]:.0%})")
    text += (f". Con objetivo 0.90 logra {n90['quality']:.3f} a USD {n90['cost'] * 1000:.2f}. El objetivo se "
             f"cumple sobre el conjunto; por idioma la calidad fue {n95['by_lang']['es']['quality']:.3f} en español "
             f"y {n95['by_lang']['en']['quality']:.3f} en inglés. La heurística de dos reglas no mejora a enviar todo "
             f"al modelo local: calidad {h['quality']:.3f} contra {al['quality']:.3f}, a USD {h['cost'] * 1000:.2f} "
             f"cada mil prompts. El oráculo, que conoce la etiqueta, costaría USD {b['oracle']['cost'] * 1000:.2f}: "
             f"queda margen. El costo local se cuenta en cero; su precio es el tiempo")
    latency_path = OUT / "latency.json"
    if latency_path.exists():
        lat = json.loads(latency_path.read_text())
        text += (": en esta máquina la mediana por respuesta fue " + ", ".join(
            f"{v['model']} {v['median_s']:.1f} s" for v in lat.values()) + " (30 prompts, secuencial)")
    text += ". Las reglas de etiquetado R1 y R2 se reportan como sensibilidad."
    return text


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    r = run()
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(r["artifact"]) + "\n", encoding="utf-8")
    REPLAY.write_text(json.dumps(r["replay"]) + "\n", encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "report.json").write_text(
        json.dumps({k: v for k, v in r.items() if k not in ("artifact", "replay")}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    (OUT / "report.md").write_text(render_markdown(r), encoding="utf-8")
    THESIS.write_text(gt_report.replace_block(THESIS.read_text(encoding="utf-8"), "router-fase3", thesis_block(r)),
                      encoding="utf-8")
    print(render_markdown(r))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
