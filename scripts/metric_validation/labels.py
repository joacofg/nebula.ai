"""Append-only label storage, one file per rater.

Append-only because labelling runs over several sittings and a crash must not
cost the sitting, and because a corrected grade should supersede the earlier
one without erasing it: the superseded line is part of the study's audit trail.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from scripts.metric_validation import blinding, rubric


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


@dataclass(frozen=True)
class Label:
    pair_id: str
    rater_id: str
    grade: str
    notes: str = ""
    recorded_at: str = field(default_factory=_now, compare=False)


def append(label: Label, path: Path) -> None:
    if label.grade not in rubric.SCALE:
        raise ValueError(f"Grade {label.grade!r} is not on the rubric.")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "pair_id": label.pair_id,
                    "rater_id": label.rater_id,
                    "grade": label.grade,
                    "notes": label.notes,
                    "recorded_at": label.recorded_at,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n"
        )


def read(path: Path) -> list[Label]:
    """Every pair's final grade, in the order the pairs were first labelled."""
    if not path.exists():
        return []
    latest: dict[str, Label] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            latest[raw["pair_id"]] = Label(
                pair_id=raw["pair_id"],
                rater_id=raw["rater_id"],
                grade=raw["grade"],
                notes=raw.get("notes", ""),
                recorded_at=raw["recorded_at"],
            )
    return list(latest.values())


def remaining(pair_ids: list[str], path: Path, *, rater_id: str) -> list[str]:
    """Pairs this rater has not graded yet, in their presentation order."""
    done = {label.pair_id for label in read(path)}
    return [
        pair_id
        for pair_id in blinding.presentation_order(pair_ids, rater_id=rater_id)
        if pair_id not in done
    ]
