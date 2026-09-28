"""The three public datasets the corpus is drawn from, pinned by content hash.

The URLs point at moving branches; the hash is what pins the revision. A
download that no longer matches refuses to proceed instead of silently
sampling from a different dataset than the one the thesis cites.
"""

from __future__ import annotations

import hashlib
import json
import urllib.request
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Source:
    name: str
    url: str
    sha256: str
    license: str
    citation: str


@dataclass(frozen=True)
class Candidate:
    source_id: str
    task_type: str
    prompt: str


SOURCES: dict[str, Source] = {
    "dolly": Source(
        "dolly",
        "https://huggingface.co/datasets/databricks/databricks-dolly-15k/resolve/main/databricks-dolly-15k.jsonl",
        "2df9083338b4abd6bceb5635764dab5d833b393b55759dffb0959b6fcbf794ec",
        "CC BY-SA 3.0",
        "Conover et al. (2023), Free Dolly: Introducing the World's First Truly Open Instruction-Tuned LLM",
    ),
    "gsm8k": Source(
        "gsm8k",
        "https://raw.githubusercontent.com/openai/grade-school-math/master/grade_school_math/data/test.jsonl",
        "3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14",
        "MIT",
        "Cobbe et al. (2021), Training Verifiers to Solve Math Word Problems",
    ),
    "mbpp": Source(
        "mbpp",
        "https://raw.githubusercontent.com/google-research/google-research/master/mbpp/mbpp.jsonl",
        "ccf64ceae9c5403bf50a044cb6d505bfd2a2963ee58338ba268fd65beab92a9f",
        "CC BY 4.0",
        "Austin et al. (2021), Program Synthesis with Large Language Models",
    ),
}

# Classification and information extraction are left out: they are closer to
# structured extraction than to the traffic a chat gateway routes.
DOLLY_TASKS: dict[str, str] = {
    "open_qa": "factual_qa",
    "general_qa": "factual_qa",
    "closed_qa": "factual_qa",
    "summarization": "summarisation",
    "creative_writing": "open_writing",
    "brainstorming": "open_writing",
}


def fetch(source: Source, cache_dir: Path) -> Path:
    path = cache_dir / f"{source.name}.jsonl"
    if not path.exists():
        cache_dir.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(source.url, timeout=120) as response:  # noqa: S310 - pinned URL
            path.write_bytes(response.read())
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != source.sha256:
        raise ValueError(
            f"{source.name}: sha256 {digest} does not match the pinned {source.sha256}. "
            f"The upstream file changed; delete {path} only if the thesis is updated to cite it."
        )
    return path


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def dolly_candidates(raw: Iterable[dict]) -> list[Candidate]:
    out: list[Candidate] = []
    for index, item in enumerate(raw):
        task = DOLLY_TASKS.get(item["category"])
        instruction = item["instruction"].strip()
        context = item.get("context", "").strip()
        if task is None or not instruction:
            continue
        if task == "summarisation" and not context:
            continue  # nothing to summarise
        prompt = f"{instruction}\n\n{context}" if context else instruction
        out.append(Candidate(f"dolly:{index}", task, prompt))
    return out


def gsm8k_candidates(raw: Iterable[dict]) -> list[Candidate]:
    return [
        Candidate(f"gsm8k:{index}", "multistep_reasoning", item["question"].strip())
        for index, item in enumerate(raw)
    ]


def mbpp_candidates(raw: Iterable[dict]) -> list[Candidate]:
    # The standard MBPP prompt: description plus one test, so the function
    # name and signature are part of the request.
    return [
        Candidate(
            f"mbpp:{item['task_id']}",
            "code",
            f"{item['text'].strip()}\nYour code should satisfy this test:\n```python\n{item['test_list'][0]}\n```",
        )
        for item in raw
    ]
