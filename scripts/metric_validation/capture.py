"""Build the pilot corpus: run the prompts, embed the answers, assemble pairs.

The study needs both classes populated. Local-vs-premium pairs are the case the
metric will actually be used on, but nothing guarantees they span the range: if
the local model happens to answer well everywhere, every pair is substitutable
and the separation is unmeasurable. Two planted kinds fix the range —
premium-vs-premium anchors the ceiling (the noise floor of the metric itself)
and cross-prompt anchors the floor.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from scripts.metric_validation.corpus import (
    PREFIX_VARIANTS,
    PROVISIONAL_PREFIX,
    Pair,
    ResponseSide,
    band_for,
)

MOCK_MARKERS = ("mock", "stub", "fake")

Similarity = Callable[[str, str, str], float]


@dataclass(frozen=True)
class PromptRecord:
    prompt_id: str
    task_type: str
    prompt: str


def cosine(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError("Cosine needs two vectors of the same dimensionality.")

    left_norm = sum(value * value for value in left) ** 0.5
    right_norm = sum(value * value for value in right) ** 0.5
    if left_norm == 0.0 or right_norm == 0.0:
        raise ValueError("Cosine is undefined for a zero-norm vector.")

    dot = sum(a * b for a, b in zip(left, right, strict=True))
    return dot / (left_norm * right_norm)


def apply_prefix(text: str, variant: str) -> str:
    """Prepend a nomic-embed-text task prefix.

    ``none`` is a real variant, not a missing value: comparing two answers is
    not a search, so running the model bare is a candidate the sweep has to
    consider alongside the three documented prefixes.
    """
    if variant not in PREFIX_VARIANTS:
        raise ValueError(f"Unknown prefix variant {variant!r}.")
    if variant == "none":
        return text
    return f"{variant}: {text}"


def ensure_real_premium(*, provider: str, base_url: str, model: str) -> None:
    """Refuse to capture references from a stand-in provider.

    Nebula's mock premium provider echoes the prompt back. References captured
    from it would sit close to the prompt rather than to a real answer, and
    every downstream similarity would look reassuring for the wrong reason.
    """
    fingerprint = f"{provider} {model}".lower()
    if any(marker in fingerprint for marker in MOCK_MARKERS):
        raise RuntimeError(
            f"Refusing to capture pilot responses from a mock premium provider "
            f"(provider={provider!r}, model={model!r}). Set NEBULA_PREMIUM_PROVIDER, "
            f"NEBULA_PREMIUM_BASE_URL and NEBULA_PREMIUM_API_KEY to a real provider."
        )
    if not base_url.strip():
        raise RuntimeError("Refusing to capture: the premium provider has no base URL.")


def _stable_pick(candidates: Sequence[str], *, salt: str) -> str:
    digest = int.from_bytes(hashlib.sha256(salt.encode("utf-8")).digest(), "big")
    return candidates[digest % len(candidates)]


def _cosines(left: str, right: str, similarity: Similarity) -> dict[str, float]:
    return {prefix: similarity(left, right, prefix) for prefix in PREFIX_VARIANTS}


def _pair(
    pair_id: str,
    kind: str,
    record: PromptRecord,
    left: ResponseSide,
    right: ResponseSide,
    similarity: Similarity,
) -> Pair:
    scores = _cosines(left.text, right.text, similarity)
    return Pair(
        pair_id=pair_id,
        kind=kind,
        task_type=record.task_type,
        prompt=record.prompt,
        left=left,
        right=right,
        cosine=scores,
        band=band_for(scores[PROVISIONAL_PREFIX]),
    )


def build_pairs(
    records: Sequence[PromptRecord],
    *,
    local: dict[str, str],
    premium_a: dict[str, str],
    premium_b: dict[str, str],
    similarity: Similarity,
    noise_floor_count: int,
    cross_prompt_count: int,
    local_model: str = "local",
    premium_a_model: str = "premium-a",
    premium_b_model: str = "premium-b",
) -> list[Pair]:
    """Assemble every pair the study labels, deterministically."""
    ordered = sorted(records, key=lambda record: record.prompt_id)
    if noise_floor_count > len(ordered) or cross_prompt_count > len(ordered):
        raise ValueError("Cannot plant more pairs than there are prompts.")

    pairs: list[Pair] = []

    for record in ordered:
        pairs.append(
            _pair(
                f"lvp:{record.prompt_id}",
                "local_vs_premium",
                record,
                ResponseSide("local", local_model, local[record.prompt_id]),
                ResponseSide("premium_a", premium_a_model, premium_a[record.prompt_id]),
                similarity,
            )
        )

    for record in ordered[:noise_floor_count]:
        pairs.append(
            _pair(
                f"pvp:{record.prompt_id}",
                "premium_vs_premium",
                record,
                ResponseSide("premium_a", premium_a_model, premium_a[record.prompt_id]),
                ResponseSide("premium_b", premium_b_model, premium_b[record.prompt_id]),
                similarity,
            )
        )

    by_task: dict[str, list[str]] = {}
    for record in ordered:
        by_task.setdefault(record.task_type, []).append(record.prompt_id)

    for record in ordered[:cross_prompt_count]:
        siblings = [
            prompt_id
            for prompt_id in by_task[record.task_type]
            if prompt_id != record.prompt_id
        ]
        if not siblings:
            raise ValueError(
                f"Task type {record.task_type!r} has a single prompt, so no "
                f"cross-prompt negative can be planted for it."
            )
        borrowed = _stable_pick(siblings, salt=f"cross:{record.prompt_id}")
        pairs.append(
            _pair(
                f"xpr:{record.prompt_id}",
                "cross_prompt",
                record,
                ResponseSide("premium_a", premium_a_model, premium_a[record.prompt_id]),
                ResponseSide("premium_offtarget", premium_a_model, premium_a[borrowed]),
                similarity,
            )
        )

    return pairs
