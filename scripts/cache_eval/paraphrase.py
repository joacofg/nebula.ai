"""Paraphrases for set (c) of the cache measurement: one local rewrite of 200 corpus prompts.

Set (c) of ``benchmarks/cache/v1/preregistration.md``: 200 of the 1000 Spanish corpus prompts
(40 per task, seed 20261022), each rewritten once by the local ``qwen2.5:7b`` at temperature 0,
with the instruction as the system message and the prompt as the user message.

    python -m scripts.cache_eval.paraphrase

generates the rewrites (raw replies are cached under ``artifacts/cache-eval/paraphrases/``, so a
re-run never regenerates), keeps the valid ones, embeds every original and paraphrase with both
models, and writes ``benchmarks/cache/v1/paraphrases/paraphrases.jsonl`` (valid rewrites),
``dropped.jsonl`` (the rest, with the reason and the length ratio) and the 40-pair blind sample
``sample.jsonl`` that ``scripts.cache_eval.label`` presents. A paraphrase is valid when its
length is 0.5 to 2.0 times the original's (the pre-registration's paraphrase-validity amendment).
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import httpx

from scripts.cache_eval import embed
from scripts.cache_eval.pawsx import PRODUCTION_MODEL, SENSITIVITY_MODEL
from scripts.ground_truth.records import PromptRow, read_rows

PER_TASK = 40
SAMPLE_SIZE = 40
SEED = 20261022
RETRY_SEED = SEED + 1
MODEL = "qwen2.5:7b"
MIN_RATIO = 0.5  # a valid paraphrase is 0.5 to 2.0 times the original's length, both included
MAX_RATIO = 2.0
MIN_VALID = 150  # fewer valid paraphrases than this has to be said in the report
GENERATIONS_PATH = Path("artifacts/cache-eval/paraphrases/generations.jsonl")
CORPUS_PATH = Path("benchmarks/ground-truth/v1/prompts.es.jsonl")
OUT_DIR = Path("benchmarks/cache/v1/paraphrases")
INSTRUCTION = (
    "Reescribe la siguiente consulta con otras palabras, sin cambiar lo que pide ni agregar "
    "información. Devuelve solo la consulta reescrita."
)

# (original prompt, seed) -> the model's raw reply
Generate = Callable[[str, int], str]
# (texts, model=...) -> one unit vector per text; ``embed.embed_texts`` fits
EmbedTexts = Callable[..., list[list[float]]]

# What a chat model wraps around a rewrite it was told to return bare: a lead-in sentence
# ("Aquí tienes la consulta reescrita:") or a label ("Reescritura:"), optionally in bold.
_ANNOUNCEMENT = re.compile(
    r"^\**\s*(?:aqu[ií] (?:tienes|est[aá]|te dejo)[^:\n]{0,80}|consulta reescrita"
    r"|consulta parafraseada|versi[oó]n reescrita|reescritura|reescrito|par[aá]frasis)"
    r"\s*\**\s*:\s*\**\s*",
    re.IGNORECASE,
)
_QUOTE_PAIRS = (('"', '"'), ("'", "'"), ("«", "»"), ("“", "”"), ("‘", "’"))


def _unquote(text: str) -> str:
    for opening, closing in _QUOTE_PAIRS:
        inner = text[1:-1]
        if (
            len(text) >= 2
            and text[0] == opening
            and text[-1] == closing
            and opening not in inner
            and closing not in inner
        ):
            return inner.strip()
    return text


def clean(reply: str) -> str:
    """The rewritten query alone: no surrounding whitespace, announcement or wrapping quotes.

    Quotes and colons that belong to the text are kept: a pair of quotes is only removed when
    it wraps the whole reply and appears nowhere inside it.
    """
    text = reply.strip()
    while True:
        stripped = _unquote(_ANNOUNCEMENT.sub("", text, count=1).strip())
        if stripped == text:
            return text
        text = stripped


def select_prompts(
    rows: list[PromptRow], *, per_task: int = PER_TASK, seed: int = SEED
) -> list[PromptRow]:
    """``per_task`` prompts of every task type, drawn with ``seed``, listed in id order.

    The draw does not depend on the order of ``rows``: each task's prompts are sorted by id
    before sampling, and each task has its own generator keyed by the seed and the task name.
    """
    by_task: dict[str, list[PromptRow]] = defaultdict(list)
    for row in sorted(rows, key=lambda r: r.prompt_id):
        by_task[row.task_type].append(row)
    picked: list[PromptRow] = []
    for task in sorted(by_task):
        pool = by_task[task]
        if len(pool) < per_task:
            raise ValueError(f"Task {task!r} has {len(pool)} prompts; {per_task} needed.")
        picked.extend(random.Random(f"{seed}:{task}").sample(pool, per_task))
    return sorted(picked, key=lambda r: r.prompt_id)


def chat_request(prompt: str, *, seed: int) -> dict:
    """The Ollama ``/api/chat`` body of one rewrite: the registered instruction as the system
    message and the prompt, alone, as the user message."""
    return {
        "model": MODEL,
        "stream": False,
        "options": {"temperature": 0, "seed": seed},
        "messages": [
            {"role": "system", "content": INSTRUCTION},
            {"role": "user", "content": prompt},
        ],
    }


def ollama_generate(prompt: str, seed: int) -> str:
    base_url = os.environ.get("NEBULA_OLLAMA_BASE_URL", "http://localhost:11434")
    response = httpx.post(
        f"{base_url}/api/chat",
        json=chat_request(prompt, seed=seed),
        timeout=httpx.Timeout(600.0, connect=5.0),
    )
    response.raise_for_status()
    return response.json()["message"]["content"]


def _messages_sha256(prompt: str) -> str:
    """Hash of the messages a rewrite of ``prompt`` sends: instruction, layout and prompt."""
    messages = chat_request(prompt, seed=SEED)["messages"]
    canonical = json.dumps(messages, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def cached_generate(generate: Generate, path: Path = GENERATIONS_PATH) -> Generate:
    """``generate`` with its raw replies kept in a JSONL file.

    One row per (model, seed, messages): a reply that is already in the file is returned
    without asking the model, so a re-run (or a run that stopped half way) never regenerates.
    The messages are hashed whole, so a reply made with another instruction or another message
    layout is never reused. A new reply is appended as soon as it exists.
    """
    replies: dict[tuple[str, int, str], str] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                replies[(row["model"], row["seed"], row["messages_sha256"])] = row["reply"]

    def cached(prompt: str, seed: int) -> str:
        key = (MODEL, seed, _messages_sha256(prompt))
        if key not in replies:
            replies[key] = generate(prompt, seed)
            row = {
                "model": MODEL,
                "seed": seed,
                "messages_sha256": key[2],
                "reply": replies[key],
            }
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        return replies[key]

    return cached


@dataclass(frozen=True)
class Rewritten:
    text: str
    seed: int


@dataclass(frozen=True)
class Dropped:
    reason: str
    length_ratio: float  # of the last reply, 0.0 when it was empty


def _same_text(a: str, b: str) -> bool:
    return " ".join(a.split()).casefold() == " ".join(b.split()).casefold()


def length_problem(original: str, paraphrase: str) -> str | None:
    """``"too_short"`` or ``"too_long"`` when the paraphrase's length is outside 0.5 to 2.0 times
    the original's in characters (both bounds are valid), else ``None``."""
    if len(paraphrase) < MIN_RATIO * len(original):
        return "too_short"
    if len(paraphrase) > MAX_RATIO * len(original):
        return "too_long"
    return None


def rewrite(original: str, generate: Generate) -> Rewritten | Dropped:
    """One cleaned rewrite of ``original``.

    An empty reply, or one that says the same as the original once cleaned (ignoring case and
    spacing), is retried once with the next seed; if that fails too the prompt is dropped, with
    the reason of each attempt. Length validity is checked afterwards, by ``build``.
    """
    failures: list[str] = []
    text = ""
    for seed in (SEED, RETRY_SEED):
        text = clean(generate(original, seed))
        if not text:
            failures.append(f"seed {seed}: empty reply")
        elif _same_text(text, original):
            failures.append(f"seed {seed}: identical to the original")
        else:
            return Rewritten(text=text, seed=seed)
    return Dropped("; ".join(failures), len(text) / len(original))


@dataclass(frozen=True)
class DroppedPrompt:
    prompt_id: str
    reason: str
    kind: str  # "empty_or_identical", "too_short" or "too_long"
    length_ratio: float


@dataclass(frozen=True)
class BuildResult:
    records: list[dict]
    dropped: list[DroppedPrompt]


def dropped_record(dropped: DroppedPrompt) -> dict:
    """A row of ``dropped.jsonl``."""
    return {
        "prompt_id": dropped.prompt_id,
        "reason": dropped.reason,
        "length_ratio": dropped.length_ratio,
    }


def build(
    prompts: list[PromptRow], *, generate: Generate, embed_texts: EmbedTexts
) -> BuildResult:
    """A row of ``paraphrases.jsonl`` for every prompt with a valid paraphrase.

    A prompt is dropped, and listed with its reason and length ratio, when no usable rewrite
    came out (see ``rewrite``) or the rewrite's length is outside ``MIN_RATIO`` to ``MAX_RATIO``
    times the original's. Each kept row carries the cosine between the original and its
    paraphrase under both embedding models (no prefix, unit-normalized), the model and the seed
    that produced the rewrite.
    """
    rewritten: list[tuple[PromptRow, Rewritten]] = []
    dropped: list[DroppedPrompt] = []
    for prompt in prompts:
        outcome = rewrite(prompt.prompt, generate)
        if isinstance(outcome, Dropped):
            dropped.append(
                DroppedPrompt(prompt.prompt_id, outcome.reason, "empty_or_identical", outcome.length_ratio)
            )
            continue
        problem = length_problem(prompt.prompt, outcome.text)
        if problem is None:
            rewritten.append((prompt, outcome))
        else:
            ratio = len(outcome.text) / len(prompt.prompt)
            bound = f"below {MIN_RATIO}" if problem == "too_short" else f"above {MAX_RATIO}"
            dropped.append(
                DroppedPrompt(prompt.prompt_id, f"length ratio {ratio:.2f} is {bound}", problem, ratio)
            )

    originals = [prompt.prompt for prompt, _ in rewritten]
    paraphrases = [outcome.text for _, outcome in rewritten]
    cosines: dict[str, list[float]] = {}
    for model in (PRODUCTION_MODEL, SENSITIVITY_MODEL):
        vectors = embed_texts(originals + paraphrases, model=model)
        half = len(originals)
        cosines[model] = [embed.cosine(a, b) for a, b in zip(vectors[:half], vectors[half:])]

    records = [
        {
            "prompt_id": prompt.prompt_id,
            "task_type": prompt.task_type,
            "original": prompt.prompt,
            "paraphrase": outcome.text,
            "model": MODEL,
            "seed": outcome.seed,
            "cos_nomic_v1": cosines[PRODUCTION_MODEL][i],
            "cos_nomic_v2": cosines[SENSITIVITY_MODEL][i],
        }
        for i, (prompt, outcome) in enumerate(rewritten)
    ]
    return BuildResult(records, dropped)


def select_sample(records: list[dict], *, size: int = SAMPLE_SIZE, seed: int = SEED) -> list[dict]:
    """The blind sample for the human check: ``size`` pairs as ``pair_id, a, b`` only.

    A is the original and B its paraphrase (the labeler swaps them at random when it shows
    them); nothing else about the pair, such as its task or cosine, is written to the file.
    """
    ordered = sorted(records, key=lambda r: r["prompt_id"])
    drawn = random.Random(seed).sample(ordered, min(size, len(ordered)))
    return [
        {"pair_id": r["prompt_id"], "a": r["original"], "b": r["paraphrase"]}
        for r in sorted(drawn, key=lambda r: r["prompt_id"])
    ]


def _write_jsonl(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def summary(selected: int, result: BuildResult) -> list[str]:
    """What a run reports: the valid count, the retries, the drop reasons by kind, and a
    warning when fewer than ``MIN_VALID`` paraphrases are valid (the report has to say so)."""
    valid = len(result.records)
    retried = sum(1 for r in result.records if r["seed"] != SEED)
    lines = [
        f"{selected} prompts selected: {valid} valid paraphrases, {len(result.dropped)} dropped",
        f"  {retried} valid paraphrases come from the retry seed",
    ]
    kinds = Counter(d.kind for d in result.dropped)
    lines += [f"  dropped, {kind}: {count}" for kind, count in sorted(kinds.items())]
    if valid < MIN_VALID:
        lines.append(f"WARNING: only {valid} valid paraphrases, fewer than {MIN_VALID}; "
                     "the report has to say so.")
    return lines


def main() -> int:
    corpus = read_rows(CORPUS_PATH, PromptRow)
    prompts = select_prompts(corpus)

    calls = 0

    def generate(prompt: str, seed: int) -> str:
        nonlocal calls
        calls += 1
        print(f"generating with {MODEL}, seed {seed}: call {calls}", flush=True)
        return ollama_generate(prompt, seed)

    result = build(prompts, generate=cached_generate(generate), embed_texts=embed.embed_texts)
    _write_jsonl(result.records, OUT_DIR / "paraphrases.jsonl")
    _write_jsonl([dropped_record(d) for d in result.dropped], OUT_DIR / "dropped.jsonl")
    _write_jsonl(select_sample(result.records), OUT_DIR / "sample.jsonl")

    print("\n".join(summary(len(prompts), result)))
    print(f"{calls} model calls -> {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
