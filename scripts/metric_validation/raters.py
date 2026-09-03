"""Who graded what, and in what capacity.

The report used to infer a rater's kind from its id: anything not prefixed
"llm-" was a human. That held until one person labelled twice, at which point
two label files read as two evaluators and the report cleared its own PENDING
marker — the exact false claim the marker exists to prevent.

Kind, person and status are declared here instead of guessed. Two ids by one
person are one evaluator, and a pass withdrawn for cause stays in the repo as
evidence while staying out of every number.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

AUXILIARY_PREFIX = "llm-"


@dataclass(frozen=True)
class RaterProfile:
    rater_id: str
    kind: str
    person: str | None
    status: str
    note: str

    @property
    def is_human(self) -> bool:
        return self.kind == "human"

    @property
    def is_withdrawn(self) -> bool:
        return self.status == "withdrawn"


def profile_for(rater_id: str, roster: dict[str, RaterProfile]) -> RaterProfile:
    """The declared profile, or the prefix rule for an undeclared rater.

    The fallback keeps a study without a roster working, and keeps a newly
    added judge auxiliary by default — the failure that matters is a model
    counted as a human, never the reverse.
    """
    if rater_id in roster:
        return roster[rater_id]
    auxiliary = rater_id.startswith(AUXILIARY_PREFIX)
    return RaterProfile(
        rater_id=rater_id,
        kind="auxiliary" if auxiliary else "human",
        person=None if auxiliary else rater_id,
        status="active",
        note="",
    )


def load_roster(path: Path) -> dict[str, RaterProfile]:
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {
        rater_id: RaterProfile(
            rater_id=rater_id,
            kind=entry["kind"],
            person=entry.get("person"),
            status=entry.get("status", "active"),
            note=entry.get("note", ""),
        )
        for rater_id, entry in raw.items()
    }


def write_roster(roster: dict[str, RaterProfile], path: Path) -> None:
    payload = {
        rater_id: {k: v for k, v in asdict(profile).items() if k != "rater_id"}
        for rater_id, profile in roster.items()
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
