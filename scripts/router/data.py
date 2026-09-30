"""The router's training set: one row per (language, prompt) with its labels and costs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from scripts.ground_truth import records

GROUND_TRUTH = Path("benchmarks/ground-truth/v1")


@dataclass(frozen=True)
class Example:
    key: str
    lang: str
    prompt_id: str
    task_type: str
    text: str
    local_ok: bool
    economy_ok: bool
    cost_economy: float
    cost_frontier: float


def _costs(root: Path, role: str, lang: str) -> dict[str, float]:
    rows = records.read_rows(root / "responses" / f"{role}.{lang}.jsonl", records.ResponseRow)
    return {r.prompt_id: r.cost_usd for r in records.latest(rows, key=lambda r: r.prompt_id).values()
            if r.status == "ok"}


def load_examples(root: Path, tiers_file: str) -> list[Example]:
    es = records.read_rows(root / "prompts.es.jsonl", records.PromptRow)
    en_all = {r.prompt_id: r for r in records.read_rows(root / "prompts.en.jsonl", records.PromptRow)}
    prompts = {("es", r.prompt_id): r for r in es}
    prompts |= {("en", r.prompt_id): en_all[r.prompt_id] for r in es if r.en_subset}
    labels = {(row["lang"], row["prompt_id"]): row
              for row in map(json.loads, (root / tiers_file).read_text().splitlines()) if row}
    costs = {(lang, role): _costs(root, role, lang) for lang in ("es", "en") for role in ("haiku", "gpt41")}

    out: list[Example] = []
    for (lang, prompt_id), prompt in sorted(prompts.items()):
        label = labels.get((lang, prompt_id))
        if label is None or label["local_substitutable"] is None or label["economy_substitutable"] is None:
            raise ValueError(f"{lang}:{prompt_id} has no complete label in {tiers_file}.")
        try:
            economy = costs[(lang, "haiku")][prompt_id]
            frontier = costs[(lang, "gpt41")][prompt_id]
        except KeyError as error:
            raise ValueError(f"{lang}:{prompt_id} has no captured cost.") from error
        out.append(Example(
            key=f"{lang}:{prompt_id}", lang=lang, prompt_id=prompt_id, task_type=prompt.task_type,
            text=prompt.prompt, local_ok=bool(label["local_substitutable"]),
            economy_ok=bool(label["economy_substitutable"]),
            cost_economy=economy, cost_frontier=frontier,
        ))
    return out
