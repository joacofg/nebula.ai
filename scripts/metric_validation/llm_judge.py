"""An auxiliary LLM rater following the human rubric on the same blinded pairs.

This is a stand-in for the second human evaluator the plan asks for, and it is
labelled as one everywhere it surfaces. It earns its place by answering a
question the single-rater study cannot: whether the rubric is specific enough
that two independent readers apply it the same way.
"""

from __future__ import annotations

import json
import re

from scripts.metric_validation import rubric

# The id the first judge's grades are already stored under. Kept so those
# 130 labels are not orphaned by a rename.
RATER_ID = "llm-judge"


def rater_id_for(model: str) -> str:
    """Derive a rater id from a judge's model.

    The "llm-" prefix is what the report keys off to mark a rater auxiliary.
    However many judges run, none of them is the human evaluator rigour point 3
    asks for, and the id has to keep saying so.
    """
    slug = model.rsplit("/", maxsplit=1)[-1]
    return f"llm-{slug}"


def validate_rater_id(rater_id: str) -> str:
    """Refuse a judge id the report would read as a human rater.

    The report decides who is auxiliary by this prefix and nothing else, so an
    id without it turns a model's agreement with a model into the inter-rater
    agreement the thesis reports, and silently clears the PENDING marker.
    """
    if not rater_id.startswith("llm-"):
        raise ValueError(
            f"Judge rater id {rater_id!r} must start with 'llm-'; the report uses "
            f"that prefix to mark a rater auxiliary."
        )
    return rater_id

_INSTRUCTIONS = """\
You are grading how interchangeable two candidate responses to the same prompt \
are. You are not judging which one is better, and you are not being asked which \
model wrote them.

{question}

Grade on this scale, and reply with JSON only, in the form {{"grade": "<grade>"}}:

{scale}

PROMPT
------
{prompt}

RESPONSE A
----------
{response_a}

RESPONSE B
----------
{response_b}
"""


def judge_prompt(payload: dict[str, str]) -> str:
    """Build the judge's prompt from a blinded payload.

    Takes the blinded payload rather than the pair so it is structurally
    impossible for provenance to reach the judge that the human rater cannot
    see; a judge with the answer key would agree for the wrong reason.
    """
    scale = "\n".join(
        f"- {grade}: {rubric.DESCRIPTIONS[grade]}" for grade in rubric.SCALE
    )
    return _INSTRUCTIONS.format(
        question=rubric.QUESTION,
        scale=scale,
        prompt=payload["prompt"],
        response_a=payload["response_a"],
        response_b=payload["response_b"],
    )


def parse_grade(reply: str) -> str:
    """Read a rubric grade out of the judge's reply, or refuse.

    There is no default. A judge that hedged, refused, or invented a grade has
    not rated the pair, and recording a stand-in grade would inflate agreement
    precisely on the pairs that were hardest to call.
    """
    for candidate in re.findall(r"\{.*?\}", reply, flags=re.DOTALL):
        try:
            grade = json.loads(candidate).get("grade")
        except (json.JSONDecodeError, AttributeError):
            continue
        if isinstance(grade, str) and grade.strip().lower() in rubric.SCALE:
            return grade.strip().lower()

    raise ValueError(
        f"The judge did not return a rubric grade. Reply was: {reply[:200]!r}"
    )
