"""Blind labeling CLI for the cache measurement.

    python -m scripts.cache_eval.label neighbors     # (b) corpus neighbors: 265 pairs
    python -m scripts.cache_eval.label paraphrases   # (c) the 40-pair paraphrase sample

(``make cache-label SET=neighbors``). One pair at a time, A and B only, with the registered
question; the answer is ``s`` (sí), ``n`` (no) or ``?`` (no sé), ``q`` quits and the next run
resumes. One JSONL row per answer is appended to ``<set>/labels/human-es-1.jsonl``.

The labeling is blind. Pairs are shown in one fixed shuffled order (seed 20261022) regardless of
how the file is sorted, with A and B swapped at random for about half of them, and nothing but
the two texts is printed: no cosine, id, tier or position in the file, and nothing that says
which pairs the author had already seen. This script is deliberately separate from the frozen
``scripts/metric_validation/`` labeler.
"""

from __future__ import annotations

import argparse
import json
import random
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

SEED = 20261022
RATER_ID = "human-es-1"
ROOT = Path("benchmarks/cache/v1")
ANSWERS = {"s": "sí", "n": "no", "?": "?"}
QUIT = "q"
PROMPT = "[s] sí  [n] no  [?] no sé  [q] salir > "


@dataclass(frozen=True)
class LabelSet:
    pairs: str  # path of the pairs file under the root
    labels: str  # path of the labels file under the root
    question: str
    missing_hint: str  # what to run when the pairs file does not exist


SETS = {
    "neighbors": LabelSet(
        pairs="neighbors/pairs.jsonl",
        labels=f"neighbors/labels/{RATER_ID}.jsonl",
        question="¿Una respuesta a A sirve para B?",
        missing_hint="make cache-data",
    ),
    "paraphrases": LabelSet(
        pairs="paraphrases/sample.jsonl",
        labels=f"paraphrases/labels/{RATER_ID}.jsonl",
        question="¿B pide lo mismo que A?",
        missing_hint="make cache-paraphrases",
    ),
}


@dataclass(frozen=True)
class Shown:
    """A pair as the labeler sees it: A and B already swapped when the draw says so."""

    pair_id: str
    a: str
    b: str


def presentation(pairs: list[dict], *, seed: int = SEED) -> list[Shown]:
    """The fixed shuffled order and A/B orientation of ``pairs``.

    Depends only on the set of pairs and the seed, not on the order of the file, so a file
    sorted by cosine leaks nothing about which pair comes first and a resumed session shows
    every pair in the same orientation as before.
    """
    ordered = sorted(pairs, key=lambda p: p["pair_id"])
    rng = random.Random(seed)
    rng.shuffle(ordered)
    swaps = [rng.random() < 0.5 for _ in ordered]
    return [
        Shown(p["pair_id"], p["b"], p["a"]) if swap else Shown(p["pair_id"], p["a"], p["b"])
        for p, swap in zip(ordered, swaps, strict=True)
    ]


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _append_label(path: Path, pair_id: str, label: str) -> None:
    row = {
        "pair_id": pair_id,
        "label": label,
        "rater_id": RATER_ID,
        "recorded_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main(
    argv: list[str] | None = None,
    *,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("set", choices=sorted(SETS))
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    spec = SETS[args.set]
    pairs_path = args.root / spec.pairs
    labels_path = args.root / spec.labels

    if not pairs_path.exists():
        output_fn(f"No existe {pairs_path}. Genéralo con `{spec.missing_hint}`.")
        return 1

    shown = presentation(_read_jsonl(pairs_path))
    done = {row["pair_id"] for row in _read_jsonl(labels_path)} if labels_path.exists() else set()
    pending = [(number, pair) for number, pair in enumerate(shown, start=1) if pair.pair_id not in done]
    if not pending:
        output_fn("No quedan pares por etiquetar.")
        return 0

    answered = 0
    for number, pair in pending:
        output_fn("─" * 78)
        output_fn(f"Par {number} de {len(shown)}\n\nA:\n{pair.a}\n\nB:\n{pair.b}\n\n{spec.question}")
        while True:
            try:
                answer = input_fn(PROMPT).strip().lower()
            except EOFError:
                answer = QUIT
            if answer == QUIT or answer in ANSWERS:
                break
            output_fn("Respuesta no válida: usa s, n, ? o q.")
        if answer == QUIT:
            output_fn(f"Guardado. Quedan {len(pending) - answered} pares; vuelve a ejecutar para seguir.")
            return 0
        _append_label(labels_path, pair.pair_id, ANSWERS[answer])
        answered += 1
    output_fn(f"Listo: los {len(shown)} pares están etiquetados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
