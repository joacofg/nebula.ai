"""On-disk rows for the ground-truth study: one JSONL file per stage output.

Files are append-only and the latest row per key wins, so a stage that is
re-run after a crash or a spend cap retries what failed without rewriting what
was already paid for.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PromptRow:
    prompt_id: str
    task_type: str
    source: str
    prompt: str
    role: str
    en_subset: bool = False


@dataclass(frozen=True)
class ResponseRow:
    prompt_id: str
    lang: str
    model: str
    status: str
    text: str
    finish_reason: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    resolved_model: str
    error: str = ""


@dataclass(frozen=True)
class Judgement:
    pair_id: str
    judge: str
    orientation: str
    status: str
    grade: str | None
    reply: str


def _line(row: Any) -> str:
    return json.dumps(asdict(row), ensure_ascii=False, sort_keys=True) + "\n"


def append_row(row: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(_line(row))


def write_rows(rows: Iterable[Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(_line(row))


def read_rows[T](path: Path, cls: type[T]) -> list[T]:
    if not path.exists():
        return []
    rows: list[T] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(cls(**json.loads(line)))
    return rows


def latest[T, K](rows: Iterable[T], *, key: Callable[[T], K]) -> dict[K, T]:
    """The last row for each key, which is the one that counts."""
    out: dict[K, T] = {}
    for row in rows:
        out[key(row)] = row
    return out
