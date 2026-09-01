"""Blinding for the metric-validation labelling protocol.

Raters must not be able to see which response came from the local model, what
the cosine says, or which similarity band the pair was drawn from. Any of the
three would turn the study into a check that the rater can read the metric.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from scripts.metric_validation.corpus import Pair


@dataclass(frozen=True)
class BlindedPair:
    pair_id: str
    prompt: str
    side_a: str
    side_b: str
    swapped: bool


def _stable_digest(*parts: str) -> int:
    """A hash that survives a new process.

    ``hash()`` is salted per interpreter run, so a blinding built on it would
    hand a resumed labelling session a different orientation than the sitting
    it is resuming.
    """
    joined = "\x1f".join(parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(joined).digest(), "big")


def blind(pair: Pair, *, rater_id: str) -> BlindedPair:
    swapped = _stable_digest("side", rater_id, pair.pair_id) % 2 == 1
    first, second = (pair.right, pair.left) if swapped else (pair.left, pair.right)
    return BlindedPair(
        pair_id=pair.pair_id,
        prompt=pair.prompt,
        side_a=first.text,
        side_b=second.text,
        swapped=swapped,
    )


def presentation_order(pair_ids: list[str], *, rater_id: str) -> list[str]:
    """Order the pairs for one rater, so position cannot correlate with band."""
    return sorted(pair_ids, key=lambda pair_id: _stable_digest("order", rater_id, pair_id))


def blinded_payload(pair: Pair, *, rater_id: str) -> dict[str, str]:
    """Exactly what a rater is allowed to see."""
    view = blind(pair, rater_id=rater_id)
    return {
        "pair_id": view.pair_id,
        "prompt": view.prompt,
        "response_a": view.side_a,
        "response_b": view.side_b,
    }
