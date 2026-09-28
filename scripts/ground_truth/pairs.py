"""Each cheaper candidate against the frontier reference, on the same prompt."""

from __future__ import annotations

from scripts.ground_truth import records
from scripts.metric_validation.corpus import Pair, ResponseSide

CANDIDATES: tuple[str, ...] = ("qwen7b", "llama3b", "haiku")
LOCAL_ROLES: tuple[str, ...] = ("qwen7b", "llama3b")
REFERENCE = "gpt41"


def split_pair_id(pair_id: str) -> tuple[str, str, str]:
    lang, candidate, prompt_id = pair_id.split(":", 2)
    return lang, candidate, prompt_id


def build_pairs(
    lang: str,
    prompts: list[records.PromptRow],
    responses: dict[str, dict[str, records.ResponseRow]],
) -> tuple[list[Pair], dict[str, int]]:
    """Pairs in a stable order. A prompt whose reference is missing or empty
    yields no pairs: grading a candidate against nothing measures nothing."""
    skipped = {"reference_unusable": 0, "candidate_failed": 0}
    out: list[Pair] = []
    for prompt in sorted(prompts, key=lambda p: p.prompt_id):
        ref = responses.get(REFERENCE, {}).get(prompt.prompt_id)
        if ref is None or ref.status != "ok" or not ref.text.strip():
            skipped["reference_unusable"] += 1
            continue
        for candidate in sorted(CANDIDATES):
            row = responses.get(candidate, {}).get(prompt.prompt_id)
            if row is None or row.status != "ok":
                skipped["candidate_failed"] += 1
                continue
            out.append(Pair(
                pair_id=f"{lang}:{candidate}:{prompt.prompt_id}",
                kind="local_vs_premium" if candidate in LOCAL_ROLES else "premium_vs_premium",
                task_type=prompt.task_type,
                prompt=prompt.prompt,
                left=ResponseSide(candidate, row.model, row.text),
                right=ResponseSide("reference", ref.model, ref.text),
                cosine={},
                band="unbanded",
            ))
    return out, skipped
