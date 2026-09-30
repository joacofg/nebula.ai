"""Stage 8: the report, and the thesis paragraphs that cite it.

    python -m scripts.ground_truth.report
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from scripts.ground_truth import capture, cli, pairs, records, review, sources, tiers, translate

THESIS = Path("docs/tfc/tesis/06-evaluacion.md")


def replace_block(text: str, name: str, content: str) -> str:
    pattern = re.compile(rf"(<!-- GEN:{re.escape(name)} -->\n)(.*?)(\n<!-- /GEN:{re.escape(name)} -->)", re.DOTALL)
    if not pattern.search(text):
        raise ValueError(f"No GEN block {name!r} in the thesis source.")
    return pattern.sub(lambda m: m.group(1) + content + m.group(3), text, count=1)


def tier_distribution(rows: list[dict]) -> dict:
    out: dict = defaultdict(lambda: defaultdict(lambda: {t: 0 for t in (*tiers.TIERS, "unlabelled")}))
    for row in rows:
        out[row["lang"]][row["task_type"]][row["tier"] or "unlabelled"] += 1
    return json.loads(json.dumps(out))


def _jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def summarise(root: Path) -> dict:
    prompts = tiers.prompts_by_lang(root)
    translations = records.latest(records.read_rows(root / "translations.jsonl", translate.TranslationRow),
                                  key=lambda r: r.prompt_id)
    capture_stats: dict = {}
    skipped: dict = {}
    for lang, rows in prompts.items():
        responses = capture.load_responses(root, lang)
        capture_stats[lang] = {
            role: {"ok": sum(1 for r in by.values() if r.status == "ok"),
                   "failed": sum(1 for r in by.values() if r.status != "ok"),
                   "truncated": sum(1 for r in by.values() if r.finish_reason == "length")}
            for role, by in responses.items()
        }
        skipped[lang] = pairs.build_pairs(lang, rows, responses)[1]
    spend_by_stage: dict[str, float] = defaultdict(float)
    for row in _jsonl(root / "spend.jsonl"):
        spend_by_stage[row["stage"]] += row["cost_usd"]
    validation = json.loads((root / "validation.json").read_text()) if (root / "validation.json").exists() else None
    names = ([name for _, _, name in tiers.tier_files(validation["rule_selection"]["chosen"])]
             if validation else ["tiers.jsonl", "tiers.llama3b.jsonl"])
    tier_rows = {name: _jsonl(root / name) for name in names}
    return {
        "prompts": {lang: {t: sum(1 for r in rows if r.task_type == t) for t in sorted({r.task_type for r in rows})}
                    for lang, rows in prompts.items()},
        "translation": {"translator": translate.TRANSLATOR,
                        "rejected": sum(1 for t in translations.values() if t.status != "ok"),
                        "numbers_restyled": sum(1 for t in translations.values() if t.warnings),
                        "review": review.error_rate(root / "translation_review.jsonl")},
        "capture": capture_stats,
        "pairs_skipped": skipped,
        "validation": validation,
        "tiers": {name: {"distribution": tier_distribution(rows),
                         "coverage": sum(1 for r in rows if r["tier"]) / len(rows) if rows else 0.0}
                  for name, rows in tier_rows.items()},
        "spend_usd": {"by_stage": dict(spend_by_stage), "total": sum(spend_by_stage.values())},
    }


def _fmt(value: float | None) -> str:
    return "—" if value is None else f"{value:.3f}"


def render_markdown(s: dict) -> str:
    out = ["# Ground truth — fase 2", "", "## Corpus", "", "| lang | " + " | ".join(sorted(s["prompts"]["es"])) + " |",
           "|---|" + "---|" * len(s["prompts"]["es"])]
    for lang, counts in s["prompts"].items():
        out.append(f"| {lang} | " + " | ".join(str(counts.get(t, 0)) for t in sorted(s["prompts"]["es"])) + " |")
    t = s["translation"]
    out += ["", f"Translator `{t['translator']}`: {t['rejected']} rejected by the number/code check; "
                f"human review {t['review']['wrong']}/{t['review']['reviewed']} wrong.", "",
            "## Capture", "", "| lang | role | ok | failed | truncated |", "|---|---|---|---|---|"]
    for lang, roles in s["capture"].items():
        for role, c in roles.items():
            out.append(f"| {lang} | {role} | {c['ok']} | {c['failed']} | {c['truncated']} |")
    out += ["", f"Pairs skipped: {s['pairs_skipped']}", "", "## Judges", ""]
    v = s["validation"]
    if v:
        sel = v["rule_selection"]
        out += [f"Rule selection on {sel['compared']} EN pilot pairs graded by `{sel['rater']}` "
                f"({sel['human_substitutable']} substitutable / {sel['human_not_substitutable']} not; "
                f"{sel['selection']}):", "",
                "| rule | kappa |", "|---|---|"]
        out += [f"| {r} | {_fmt(k)} |" for r, k in sel["kappas"].items()]
        out += ["", f"**Chosen: `{sel['chosen']}`.**", ""]
        h = v["holdout_es"]
        if h["status"] == "pending":
            out.append("**Spanish hold-out: PENDING** (no human labels yet).")
        elif h["kappa"] is None:
            out.append(f"Spanish hold-out ({h['compared']} pairs, {h['status']}): kappa undefined (one class).")
        else:
            out.append(f"Spanish hold-out ({h['compared']} pairs, {h['status']}): kappa {h['kappa']:.3f} "
                       f"[{h['ci95'][0]:.3f}, {h['ci95'][1]:.3f}]" + (" — **judge-limited**" if h["judge_limited"] else ""))
        nc = v.get("holdout_es_excluding_code")
        if nc and nc.get("kappa") is not None:
            out.append(f"Excluding code pairs (post hoc, rater low-confidence): {nc['compared']} pairs, "
                       f"kappa {nc['kappa']:.3f} [{nc['ci95'][0]:.3f}, {nc['ci95'][1]:.3f}]")
        out += ["", "Position flip rate: " + ", ".join(f"`{m}` {r:.1%}" for m, r in v["position_flip_rate"].items()),
                f"Inter-judge kappa: {_fmt(v['inter_judge_kappa'])}", ""]
    out += ["## Tiers", ""]
    for name, tier in s["tiers"].items():
        out += [f"### {name} (coverage {tier['coverage']:.1%})", "", "| lang | task | local | economy | frontier | unlabelled |",
                "|---|---|---|---|---|---|"]
        for lang, tasks in tier["distribution"].items():
            for task, c in sorted(tasks.items()):
                out.append(f"| {lang} | {task} | {c['local']} | {c['economy']} | {c['frontier']} | {c['unlabelled']} |")
        out.append("")
    out += ["## Spend", "", f"Total USD {s['spend_usd']['total']:.2f}: " +
            ", ".join(f"{k} {v:.2f}" for k, v in s["spend_usd"]["by_stage"].items()), ""]
    return "\n".join(out)


def thesis_corpus(s: dict) -> str:
    srcs = "; ".join(f"{src.name} ({src.license})" for src in sources.SOURCES.values())
    es = s["prompts"]["es"]
    en_total = sum(s["prompts"]["en"].values())
    tr = s["translation"]
    rv = tr["review"]
    text = (
        f"El corpus combina tres conjuntos públicos: {srcs}. Se muestrearon {sum(es.values())} prompts "
        f"estratificados por tarea ({', '.join(f'{t} {n}' for t, n in es.items())}) con semilla fija, "
        f"y un subconjunto pareado de {en_total} en inglés. La traducción al español la hizo "
        f"`{tr['translator']}`, de una familia ajena a candidatos y jueces. Un control mecánico rechazó "
        f"{tr['rejected']} traducciones que alteraban bloques de código, o números en razonamiento y "
        f"código (donde los números son la tarea), y se reemplazaron desde la reserva del mismo estrato; en las tareas "
        f"de Dolly, {tr.get('numbers_restyled', 0)} traducciones reescribieron números por estilo "
        f"(p. ej. «siglo XV») y quedaron marcadas para la revisión humana. "
    )
    if rv["reviewed"] == 0:
        return text + "La revisión humana de una muestra de traducciones está pendiente."
    return text + (f"Una revisión humana de {rv['reviewed']} traducciones encontró {rv['wrong']} "
                   f"infieles ({rv['rate']:.0%}).")


def thesis_judges(s: dict) -> str:
    v = s["validation"]
    if not v:
        return "> PENDIENTE: validación de jueces."
    sel, h = v["rule_selection"], v["holdout_es"]
    kappas = ", ".join(f"{r.split('_')[0]} {_fmt(k)}" for r, k in sel["kappas"].items())
    text = (
        f"Cada par candidato–referencia recibe cuatro notas (dos jueces, dos posiciones). La regla se "
        f"eligió sobre {sel['compared']} pares en inglés etiquetados por un lector humano; esos pares se "
        f"eligieron en el piloto por desacuerdo entre dos jueces previos y quedaron "
        f"{sel['human_substitutable']} sustituibles y {sel['human_not_substitutable']} no, así que el kappa "
        f"de selección descansa en muy pocos negativos. Kappa binario por regla: {kappas}; se eligió "
        f"{sel['chosen'].split('_')[0]}. Como análisis de sensibilidad pre-registrado, los niveles se "
        f"reportan bajo las tres reglas. "
    )
    if h["status"] == "pending":
        text += "La validación sobre el hold-out en español está pendiente."
    elif h["kappa"] is None:
        text += (f"Sobre el hold-out en español ({h['compared']} pares) el kappa es indefinido: "
                 f"una de las dos partes asignó una sola clase.")
    else:
        partial = "" if h["status"] == "complete" else ", resultado parcial"
        text += (f"Sobre el hold-out en español ({h['compared']} pares sorteados antes de correr los "
                 f"jueces{partial}) la regla elegida obtuvo kappa {h['kappa']:.2f} "
                 f"(IC 95 % {h['ci95'][0]:.2f}–{h['ci95'][1]:.2f}). El acuerdo bruto fue "
                 f"{h['raw_agreement']:.0%}; el lector juzgó sustituibles {h['human_substitutable']} de "
                 f"{h['compared']}, y en los desacuerdos el ensamble fue más estricto que el lector "
                 f"{h['judges_stricter']} veces y más laxo {h['judges_laxer']}.")
        if h["judge_limited"]:
            text += " Al quedar por debajo de 0.4, el ground truth se declara limitado por los jueces."
    nc = v.get("holdout_es_excluding_code")
    if h["status"] != "pending" and nc and nc.get("kappa") is not None:
        text += (f" Análisis post hoc, no pre-registrado: el evaluador marcó como de baja confianza sus "
                 f"notas sobre pares de código, porque la terminal de etiquetado reenvuelve los bloques de "
                 f"código; sin esos pares ({nc['compared']}) el kappa es {nc['kappa']:.2f} "
                 f"(IC 95 % {nc['ci95'][0]:.2f}–{nc['ci95'][1]:.2f}).")
    flips = ", ".join(f"{m.split('/')[-1]} {r:.0%}" for m, r in v["position_flip_rate"].items())
    return text + f" Tasa de cambio de veredicto al invertir posiciones: {flips}."


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=cli.DEFAULT_ROOT)
    root = parser.parse_args().root
    summary = summarise(root)
    (root / "report.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (root / "report.md").write_text(render_markdown(summary), encoding="utf-8")
    text = THESIS.read_text(encoding="utf-8")
    text = replace_block(text, "corpus-fase2", thesis_corpus(summary))
    text = replace_block(text, "judges-fase2", thesis_judges(summary))
    THESIS.write_text(text, encoding="utf-8")
    print(f"report → {root / 'report.md'}; thesis blocks updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
