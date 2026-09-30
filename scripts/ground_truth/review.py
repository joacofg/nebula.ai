"""Human spot check of the translations.

    python -m scripts.ground_truth.review

Shows 40 English/Spanish pairs drawn with a fixed seed. For each: y = faithful,
n = wrong (meaning changed, something lost or added), s = skip. Resumable.
"""

from __future__ import annotations

import argparse
import json
import random
import textwrap
from datetime import UTC, datetime
from pathlib import Path

from scripts.ground_truth import cli, records

REVIEW_SIZE = 40
SEED = 20260927


def review_sample(rows_es: list[records.PromptRow], *, size: int, seed: int) -> list[records.PromptRow]:
    ordered = sorted(rows_es, key=lambda r: r.prompt_id)
    return sorted(random.Random(seed).sample(ordered, min(size, len(ordered))), key=lambda r: r.prompt_id)


def error_rate(path: Path) -> dict[str, float | int]:
    if not path.exists():
        return {"reviewed": 0, "wrong": 0, "rate": 0.0}
    verdicts: dict[str, bool] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            raw = json.loads(line)
            verdicts[raw["prompt_id"]] = raw["faithful"]
    wrong = sum(1 for ok in verdicts.values() if not ok)
    return {"reviewed": len(verdicts), "wrong": wrong, "rate": wrong / len(verdicts) if verdicts else 0.0}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=cli.DEFAULT_ROOT)
    root = parser.parse_args().root
    en = {r.prompt_id: r for r in records.read_rows(root / "prompts.en.jsonl", records.PromptRow)}
    es = records.read_rows(root / "prompts.es.jsonl", records.PromptRow)
    out = root / "translation_review.jsonl"
    done = set()
    if out.exists():
        done = {json.loads(line)["prompt_id"] for line in out.read_text(encoding="utf-8").splitlines() if line.strip()}
    queue = [r for r in review_sample(es, size=REVIEW_SIZE, seed=SEED) if r.prompt_id not in done]
    for position, row in enumerate(queue, start=1):
        print("─" * 78, f"\n{position}/{len(queue)}  {row.prompt_id}\nEN:\n{textwrap.fill(en[row.prompt_id].prompt, 78)}")
        print(f"\nES:\n{textwrap.fill(row.prompt, 78)}\n")
        while (answer := input("faithful? [y/n/s] ").strip().lower()) not in {"y", "n", "s"}:
            pass
        if answer == "s":
            continue
        note = input("note (optional): ").strip() if answer == "n" else ""
        with out.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({
                "prompt_id": row.prompt_id, "faithful": answer == "y", "note": note,
                "recorded_at": datetime.now(UTC).isoformat(timespec="seconds"),
            }, ensure_ascii=False) + "\n")
    print(error_rate(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
