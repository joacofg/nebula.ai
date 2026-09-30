"""Stage 7: the cheapest tier that serves each prompt as well as the frontier.

    python -m scripts.ground_truth.tiers
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.ground_truth import cli, ensemble, judge, records

TIERS: tuple[str, ...] = ("local", "economy", "frontier")
ECONOMY_ROLE = "haiku"


def tier_for(local_ok: bool | None, economy_ok: bool | None) -> str | None:
    """None when a missing verdict leaves the answer open."""
    if local_ok is None:
        return None
    if local_ok:
        return "local"
    if economy_ok is None:
        return None
    return "economy" if economy_ok else "frontier"


def build_tiers(
    prompts_by_lang: dict[str, list[records.PromptRow]],
    pair_grades: dict[str, list[str]],
    rule: str,
    *,
    local_role: str,
) -> list[dict]:
    def verdict(lang: str, role: str, prompt_id: str) -> bool | None:
        grades = pair_grades.get(f"{lang}:{role}:{prompt_id}")
        return None if grades is None else ensemble.substitutable(rule, grades)

    out: list[dict] = []
    for lang in sorted(prompts_by_lang):
        for prompt in sorted(prompts_by_lang[lang], key=lambda p: p.prompt_id):
            local_ok = verdict(lang, local_role, prompt.prompt_id)
            economy_ok = verdict(lang, ECONOMY_ROLE, prompt.prompt_id)
            out.append({
                "lang": lang, "prompt_id": prompt.prompt_id, "task_type": prompt.task_type,
                "tier": tier_for(local_ok, economy_ok),
                "local_substitutable": local_ok, "economy_substitutable": economy_ok,
            })
    return out


def tier_files(chosen: str) -> list[tuple[str, str, str]]:
    """(local role, rule, file): the chosen rule for both local models, and
    every rule for qwen as the pre-registered sensitivity analysis."""
    return [
        ("qwen7b", chosen, "tiers.jsonl"),
        ("llama3b", chosen, "tiers.llama3b.jsonl"),
        *(("qwen7b", rule, f"tiers.{rule}.jsonl") for rule in ensemble.RULES),
    ]


def prompts_by_lang(root: Path) -> dict[str, list[records.PromptRow]]:
    es = records.read_rows(root / "prompts.es.jsonl", records.PromptRow)
    en_all = {r.prompt_id: r for r in records.read_rows(root / "prompts.en.jsonl", records.PromptRow)}
    return {"es": es, "en": [en_all[r.prompt_id] for r in es if r.en_subset]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=cli.DEFAULT_ROOT)
    root = parser.parse_args().root
    rule = json.loads((root / "validation.json").read_text())["rule_selection"]["chosen"]
    judgements: list[records.Judgement] = []
    for model in judge.JUDGES:
        judgements += records.read_rows(judge.judgements_path(root, model, "corpus"), records.Judgement)
    grades = ensemble.grades_by_pair(judgements, judges=judge.JUDGES, orientations=judge.ORIENTATIONS)
    prompts = prompts_by_lang(root)
    for local_role, file_rule, name in tier_files(rule):
        rows = build_tiers(prompts, grades, file_rule, local_role=local_role)
        (root / name).write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
        labelled = sum(1 for r in rows if r["tier"] is not None)
        print(f"{name}: {labelled}/{len(rows)} labelled ({labelled / len(rows):.1%}) with {file_rule}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
