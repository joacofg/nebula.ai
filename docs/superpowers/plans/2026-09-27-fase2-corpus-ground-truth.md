# Fase 2 — Corpus bilingüe y ground truth — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Label every prompt of a 1000-ES + 250-EN public corpus with the cheapest tier (`local` / `economy` / `frontier`) whose answer can replace gpt-4.1's, using a judge ensemble whose agreement with a human reader is measured in both languages.

**Architecture:** A new offline package `scripts/ground_truth/` with one resumable stage per module (`sample → translate → capture → holdout → judge → validate → tiers → report`), each writing JSONL under `benchmarks/ground-truth/v1/`. Pure logic (sampling, validators, rules, tiers) is separated from I/O so it is unit-tested without network. Blinding, rubric, grade parsing, the labelling session and statistics are imported from `scripts/metric_validation/`, never modified.

**Tech Stack:** Python 3.12 stdlib + `httpx` (already a dependency), OpenRouter (OpenAI-compatible), Ollama, pytest (auto asyncio).

**Spec:** `docs/superpowers/specs/2026-09-27-fase2-corpus-ground-truth.md`

## Global Constraints

- Branch `fase2-ground-truth`; one commit per task; PR at the end, merge after `make lint`, `make test`, `make console-test` are green (push/merge pre-authorised).
- Never modify `scripts/metric_validation/`, `benchmarks/metric-validation/`, `docs/evaluation.md`, `tests/test_metric_validation.py`. Import from them only.
- Heavy runs go through `darwin-throttle` (e.g. `darwin-throttle .venv/bin/pytest -p no:cacheprovider`); never raise worker counts.
- Tests: no network, no Ollama, no Qdrant.
- Code, comments, commits in English; thesis text in Spanish.
- Models (exact ids): translator `mistralai/mistral-large-2512`; candidates `qwen2.5:7b`, `llama3.2:3b` (Ollama), `anthropic/claude-haiku-4.5`, `openai/gpt-4.1`; judges `google/gemini-2.5-flash`, `deepseek/deepseek-chat-v3-0324`. Temperature 0 everywhere; candidate `max_tokens=1024`.
- Premium calls only through OpenRouter (`NEBULA_PREMIUM_BASE_URL` must contain `openrouter.ai`; key `NEBULA_PREMIUM_API_KEY`).
- Hard spend cap USD 35 for the phase (`spend.jsonl` accumulates across stages).
- Data root `benchmarks/ground-truth/v1/` (tracked); raw dataset downloads in `artifacts/ground-truth-sources/` (gitignored).
- Rubric: `scripts/metric_validation/rubric.py` unchanged.
- Commit trailer: `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`.

## Review Focus

1. Re-running a stage after `BudgetExceeded` or a crash must neither re-pay for an `ok` row nor duplicate it in the results (latest row per key wins) — pinned in Task 4 and Task 6.
2. An empty or failed gpt-4.1 reference makes every pair on that prompt meaningless: such prompts produce no pairs and are counted, never judged against "" — pinned in Task 5.
3. A judge reply truncated or without a grade is `missing`, never a default grade, and a pair missing any of its 4 grades is excluded from rules, kappa and tiers — pinned in Task 6 and Task 7.
4. A "translation" that answers the request instead of translating it (much longer than the source), or wraps it in tags/quotes, must be caught or cleaned — pinned in Task 3.
5. Judging the corpus before the pre-registration and hold-out exist would let the rules be chosen after seeing judge output — the judge stage refuses — pinned in Task 6.

---

### Task 0: Package skeleton, rows and provenance

**Files:**
- Create: `scripts/ground_truth/__init__.py`, `scripts/ground_truth/records.py`, `scripts/ground_truth/cli.py`
- Test: `tests/test_ground_truth.py`

**Interfaces:**
- Produces:
  - `records.PromptRow(prompt_id: str, task_type: str, source: str, prompt: str, role: str, en_subset: bool = False)` — `role` ∈ {"corpus","reserve"}
  - `records.ResponseRow(prompt_id, lang, model, status, text, finish_reason, prompt_tokens: int, completion_tokens: int, cost_usd: float, resolved_model, error="")` — `status` ∈ {"ok","failed"}
  - `records.Judgement(pair_id, judge, orientation, status, grade: str | None, reply: str)` — `orientation` ∈ {"ab","ba"}, `status` ∈ {"ok","missing"}
  - `records.append_row(row, path)`, `records.write_rows(rows, path)`, `records.read_rows(path, cls) -> list`, `records.latest(rows, key: Callable) -> dict`
  - `cli.DEFAULT_ROOT = Path("benchmarks/ground-truth/v1")`, `cli.update_provenance(root, **fields)`, `cli.sha256_of(path)`, `cli.openrouter_client() -> httpx.AsyncClient`, `cli.ollama_client() -> httpx.AsyncClient`

- [ ] **Step 1: Failing tests**

```python
from scripts.ground_truth import records, cli

def test_rows_round_trip_and_latest_wins(tmp_path):
    path = tmp_path / "r.jsonl"
    first = records.ResponseRow("p1", "es", "m", "failed", "", "", 0, 0, 0.0, "m", "boom")
    second = records.ResponseRow("p1", "es", "m", "ok", "hola", "stop", 3, 4, 0.01, "m")
    records.append_row(first, path)
    records.append_row(second, path)
    rows = records.read_rows(path, records.ResponseRow)
    assert rows == [first, second]
    assert records.latest(rows, key=lambda r: r.prompt_id) == {"p1": second}

def test_read_rows_on_missing_file_is_empty(tmp_path):
    assert records.read_rows(tmp_path / "nope.jsonl", records.PromptRow) == []

def test_update_provenance_merges(tmp_path):
    cli.update_provenance(tmp_path, a=1)
    cli.update_provenance(tmp_path, b={"x": 2})
    import json
    assert json.loads((tmp_path / "provenance.json").read_text()) == {"a": 1, "b": {"x": 2}}
```

- [ ] **Step 2:** `.venv/bin/pytest tests/test_ground_truth.py -q` → FAIL (module missing).

- [ ] **Step 3: Implement**

`records.py`:
```python
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
```

`cli.py`:
```python
"""Shared plumbing for the stage commands: paths, provenance, HTTP clients."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import httpx

from scripts.metric_validation.build_pilot_corpus import load_dotenv

DEFAULT_ROOT = Path("benchmarks/ground-truth/v1")
SOURCES_DIR = Path("artifacts/ground-truth-sources")


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def update_provenance(root: Path, **fields: Any) -> None:
    path = root / "provenance.json"
    current = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    current.update(fields)
    root.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def openrouter_client() -> httpx.AsyncClient:
    load_dotenv()
    base_url = os.environ.get("NEBULA_PREMIUM_BASE_URL", "")
    api_key = os.environ.get("NEBULA_PREMIUM_API_KEY", "")
    if "openrouter.ai" not in base_url:
        raise RuntimeError(f"Premium calls go through OpenRouter only; base URL is {base_url!r}.")
    if not api_key:
        raise RuntimeError("NEBULA_PREMIUM_API_KEY is unset.")
    return httpx.AsyncClient(
        base_url=base_url,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=httpx.Timeout(180.0, connect=10.0),
    )


def ollama_client() -> httpx.AsyncClient:
    load_dotenv()
    return httpx.AsyncClient(
        base_url=os.environ.get("NEBULA_OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=httpx.Timeout(600.0, connect=5.0),
    )
```

- [ ] **Step 4:** tests PASS. **Step 5:** commit `feat(ground-truth): stage rows, provenance and clients`.

---

### Task 1: Sources and stratified sample

**Files:** Create `scripts/ground_truth/sources.py`, `scripts/ground_truth/sample.py`; test in `tests/test_ground_truth.py`.

**Interfaces:**
- Consumes: `records.PromptRow`, `records.write_rows`, `cli.*`, `metric_validation.corpus.TASK_TYPES`.
- Produces: `sources.SOURCES: dict[str, Source]`, `sources.Candidate(source_id, task_type, prompt)`, `sources.dolly_candidates(raw: Iterable[dict])`, `sources.gsm8k_candidates(raw)`, `sources.mbpp_candidates(raw)`, `sources.fetch(source, cache_dir) -> Path`; `sample.stratified_sample(candidates, *, per_task, reserve_per_task, seed) -> list[PromptRow]`; constants `sample.PER_TASK=200`, `sample.RESERVE_PER_TASK=20`, `sample.EN_PER_TASK=50`, `sample.SEED=20260927`, `sample.MAX_PROMPT_CHARS=6000`.

- [ ] **Step 1: Failing tests**

```python
from scripts.ground_truth import sample, sources

def _cands(n_per_task):
    from scripts.metric_validation.corpus import TASK_TYPES
    return [sources.Candidate(f"{t}:{i}", t, f"prompt {t} {i}") for t in TASK_TYPES for i in range(n_per_task)]

def test_sample_is_deterministic_and_balanced():
    a = sample.stratified_sample(_cands(40), per_task=10, reserve_per_task=3, seed=7)
    b = sample.stratified_sample(list(reversed(_cands(40))), per_task=10, reserve_per_task=3, seed=7)
    assert a == b
    from collections import Counter
    assert Counter((r.task_type, r.role) for r in a) == Counter(
        {(t, role): n for t in {r.task_type for r in a} for role, n in (("corpus", 10), ("reserve", 3))}
    )
    assert len({r.prompt_id for r in a}) == len(a)

def test_sample_refuses_a_short_stratum():
    import pytest
    with pytest.raises(ValueError, match="code"):
        sample.stratified_sample(
            [c for c in _cands(40) if c.task_type != "code"] + _cands(2)[:2], per_task=10, reserve_per_task=3, seed=7
        )

def test_sample_drops_duplicates_and_overlong():
    cands = _cands(40) + [sources.Candidate("dup", "code", "prompt code 0"), sources.Candidate("long", "code", "x" * 7000)]
    rows = sample.stratified_sample(cands, per_task=39, reserve_per_task=1, seed=1)
    assert not any(r.source in {"dup", "long"} for r in rows)

def test_dolly_maps_categories_and_folds_context():
    raw = [
        {"instruction": "Q?", "context": "", "category": "open_qa"},
        {"instruction": "Summarise", "context": "Long text.", "category": "summarization"},
        {"instruction": "Summarise", "context": "", "category": "summarization"},
        {"instruction": "Sort these", "context": "", "category": "classification"},
        {"instruction": "Poem", "context": "", "category": "creative_writing"},
    ]
    got = sources.dolly_candidates(raw)
    assert [(c.source_id, c.task_type, c.prompt) for c in got] == [
        ("dolly:0", "factual_qa", "Q?"),
        ("dolly:1", "summarisation", "Summarise\n\nLong text."),
        ("dolly:4", "open_writing", "Poem"),
    ]

def test_mbpp_prompt_carries_the_first_test_verbatim():
    got = sources.mbpp_candidates([{"task_id": 11, "text": "Write f.", "test_list": ["assert f(1) == 2", "x"]}])
    assert got[0].prompt == "Write f.\nYour code should satisfy this test:\n```python\nassert f(1) == 2\n```"
    assert got[0].source_id == "mbpp:11" and got[0].task_type == "code"

def test_fetch_refuses_a_hash_mismatch(tmp_path):
    import pytest
    src = sources.Source("x", "http://unused", "0" * 64, "MIT", "cite")
    (tmp_path / "x.jsonl").write_text("{}\n")
    with pytest.raises(ValueError, match="sha256"):
        sources.fetch(src, tmp_path)
```

- [ ] **Step 2:** run → FAIL.

- [ ] **Step 3: Implement**

`sources.py`:
```python
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
```

`sample.py`:
```python
"""Stage 1: draw the stratified English corpus.

    python -m scripts.ground_truth.sample

200 prompts per task type plus a reserve of 20 that replaces prompts the
translation stage rejects, so every stratum stays at 200 in Spanish.
"""

from __future__ import annotations

import argparse
import random
from collections.abc import Sequence
from pathlib import Path

from scripts.ground_truth import cli, records, sources
from scripts.metric_validation.corpus import TASK_TYPES

PER_TASK = 200
RESERVE_PER_TASK = 20
EN_PER_TASK = 50
SEED = 20260927
MAX_PROMPT_CHARS = 6000  # ~1500 tokens
MIN_PROMPT_CHARS = 12


def _eligible(candidates: Sequence[sources.Candidate]) -> list[sources.Candidate]:
    seen: set[str] = set()
    out: list[sources.Candidate] = []
    for candidate in sorted(candidates, key=lambda c: c.source_id):
        text = candidate.prompt.strip()
        if not MIN_PROMPT_CHARS <= len(text) <= MAX_PROMPT_CHARS or text in seen:
            continue
        seen.add(text)
        out.append(candidate)
    return out


def stratified_sample(
    candidates: Sequence[sources.Candidate], *, per_task: int, reserve_per_task: int, seed: int
) -> list[records.PromptRow]:
    by_task: dict[str, list[sources.Candidate]] = {}
    for candidate in _eligible(candidates):
        by_task.setdefault(candidate.task_type, []).append(candidate)

    rows: list[records.PromptRow] = []
    for task in TASK_TYPES:
        pool = by_task.get(task, [])
        wanted = per_task + reserve_per_task
        if len(pool) < wanted:
            raise ValueError(f"Task {task!r} has {len(pool)} eligible prompts; {wanted} needed.")
        picked = random.Random(f"{seed}:{task}").sample(pool, wanted)
        for index, candidate in enumerate(picked):
            rows.append(
                records.PromptRow(
                    prompt_id=f"{task}-{index:04d}",
                    task_type=task,
                    source=candidate.source_id,
                    prompt=candidate.prompt.strip(),
                    role="corpus" if index < per_task else "reserve",
                )
            )
    return rows


def notice() -> str:
    lines = ["Prompts in this directory are derived from the following datasets.", ""]
    for source in sources.SOURCES.values():
        lines.append(f"- {source.name}: {source.citation}. License: {source.license}. {source.url}")
    lines += ["", "Spanish prompts are machine translations of the originals (same licenses)."]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=cli.DEFAULT_ROOT)
    args = parser.parse_args()

    loaders = {
        "dolly": sources.dolly_candidates,
        "gsm8k": sources.gsm8k_candidates,
        "mbpp": sources.mbpp_candidates,
    }
    candidates: list[sources.Candidate] = []
    for name, loader in loaders.items():
        path = sources.fetch(sources.SOURCES[name], cli.SOURCES_DIR)
        candidates += loader(sources.read_jsonl(path))

    rows = stratified_sample(
        candidates, per_task=PER_TASK, reserve_per_task=RESERVE_PER_TASK, seed=SEED
    )
    records.write_rows(rows, args.root / "prompts.en.jsonl")
    (args.root / "NOTICE").write_text(notice(), encoding="utf-8")
    cli.update_provenance(
        args.root,
        sample_seed=SEED,
        sources={n: {"url": s.url, "sha256": s.sha256, "license": s.license} for n, s in sources.SOURCES.items()},
        prompts_en_sha256=cli.sha256_of(args.root / "prompts.en.jsonl"),
    )
    print(f"{len(rows)} prompts → {args.root / 'prompts.en.jsonl'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4:** PASS. **Step 5:** commit `feat(ground-truth): stratified sample from Dolly, GSM8K and MBPP`.

---

### Task 2: LLM calls and the spend ledger

**Files:** Create `scripts/ground_truth/llm.py`, `scripts/ground_truth/spend.py`; tests.

**Interfaces:**
- Produces: `llm.Completion(text, finish_reason, prompt_tokens, completion_tokens, cost_usd: float | None, resolved_model)`; `llm.Chat = Callable[[str], Awaitable[Completion]]`; `llm.CallFailed`; `llm.openrouter_chat(client, model, *, max_tokens, extra=None) -> Chat`; `llm.ollama_chat(client, model, *, max_tokens) -> Chat`; `async llm.with_retries(chat, prompt, *, attempts=4, backoff=2.0, sleep=asyncio.sleep) -> Completion`.
- `spend.PRICES: dict[str, tuple[float, float]]` (USD per 1M in/out); `spend.estimate(model, prompt_tokens, completion_tokens) -> float`; `spend.BudgetExceeded`; `spend.SpendLedger(path, cap_usd)` with `.total`, `.check()`, `.record(*, stage, model, completion) -> float`.

- [ ] **Step 1: Failing tests**

```python
import httpx, pytest
from scripts.ground_truth import llm, spend

async def test_openrouter_chat_reads_usage_cost_and_finish_reason():
    def handler(request):
        import json
        body = json.loads(request.content)
        assert body["temperature"] == 0.0 and body["max_tokens"] == 9 and body["usage"] == {"include": True}
        assert body["reasoning"] == {"max_tokens": 0}
        return httpx.Response(200, json={
            "model": "openai/gpt-4.1-2025-04-14",
            "choices": [{"message": {"content": "hi"}, "finish_reason": "length"}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 9, "cost": 0.002},
        })
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://x") as client:
        chat = llm.openrouter_chat(client, "openai/gpt-4.1", max_tokens=9, extra={"reasoning": {"max_tokens": 0}})
        got = await chat("q")
    assert got == llm.Completion("hi", "length", 5, 9, 0.002, "openai/gpt-4.1-2025-04-14")

async def test_openrouter_error_body_is_a_failure():
    transport = httpx.MockTransport(lambda r: httpx.Response(200, json={"error": {"message": "nope"}}))
    async with httpx.AsyncClient(transport=transport, base_url="http://x") as client:
        with pytest.raises(llm.CallFailed):
            await llm.openrouter_chat(client, "m", max_tokens=5)("q")

async def test_ollama_chat_maps_done_reason_and_counts():
    transport = httpx.MockTransport(lambda r: httpx.Response(200, json={
        "message": {"content": "hola"}, "done_reason": "length", "prompt_eval_count": 3, "eval_count": 7}))
    async with httpx.AsyncClient(transport=transport, base_url="http://x") as client:
        got = await llm.ollama_chat(client, "qwen2.5:7b", max_tokens=7)("q")
    assert got == llm.Completion("hola", "length", 3, 7, 0.0, "qwen2.5:7b")

async def test_with_retries_gives_up_with_call_failed():
    calls = []
    async def flaky(prompt):
        calls.append(prompt)
        raise httpx.ConnectError("down")
    async def no_sleep(_):
        return None
    with pytest.raises(llm.CallFailed):
        await llm.with_retries(flaky, "q", attempts=4, sleep=no_sleep)
    assert len(calls) == 4

def test_ledger_accumulates_across_instances_and_enforces_cap(tmp_path):
    path = tmp_path / "spend.jsonl"
    ledger = spend.SpendLedger(path, cap_usd=0.01)
    ledger.record(stage="t", model="openai/gpt-4.1", completion=llm.Completion("", "stop", 1, 1, 0.006, "m"))
    again = spend.SpendLedger(path, cap_usd=0.01)
    assert again.total == pytest.approx(0.006)
    again.check()
    again.record(stage="t", model="openai/gpt-4.1", completion=llm.Completion("", "stop", 1, 1, None, "m"))
    assert again.total == pytest.approx(0.006 + spend.estimate("openai/gpt-4.1", 1, 1))
    again.record(stage="t", model="openai/gpt-4.1", completion=llm.Completion("", "stop", 1, 1, 0.01, "m"))
    with pytest.raises(spend.BudgetExceeded):
        again.check()

def test_estimate_refuses_unknown_models():
    with pytest.raises(ValueError):
        spend.estimate("who/knows", 1, 1)
```

- [ ] **Step 2:** FAIL.

- [ ] **Step 3: Implement**

`llm.py`:
```python
"""One prompt in, one completion out, with the accounting the study reports."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class Completion:
    text: str
    finish_reason: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float | None
    resolved_model: str


Chat = Callable[[str], Awaitable[Completion]]


class CallFailed(RuntimeError):
    """A call that did not produce a completion after every retry."""


def openrouter_chat(
    client: httpx.AsyncClient, model: str, *, max_tokens: int, extra: dict[str, Any] | None = None
) -> Chat:
    async def chat(prompt: str) -> Completion:
        body: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "max_tokens": max_tokens,
            "usage": {"include": True},
            **(extra or {}),
        }
        response = await client.post("/chat/completions", json=body)
        response.raise_for_status()
        data = response.json()
        if "error" in data or not data.get("choices"):
            raise CallFailed(f"{model}: {data.get('error', data)!r}"[:300])
        choice = data["choices"][0]
        usage = data.get("usage") or {}
        cost = usage.get("cost")
        return Completion(
            text=(choice.get("message") or {}).get("content") or "",
            finish_reason=choice.get("finish_reason") or "",
            prompt_tokens=int(usage.get("prompt_tokens", 0)),
            completion_tokens=int(usage.get("completion_tokens", 0)),
            cost_usd=float(cost) if cost is not None else None,
            resolved_model=data.get("model", model),
        )

    return chat


def ollama_chat(client: httpx.AsyncClient, model: str, *, max_tokens: int) -> Chat:
    async def chat(prompt: str) -> Completion:
        response = await client.post(
            "/api/chat",
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"temperature": 0.0, "num_predict": max_tokens},
            },
        )
        response.raise_for_status()
        data = response.json()
        return Completion(
            text=(data.get("message") or {}).get("content", ""),
            finish_reason=data.get("done_reason", ""),
            prompt_tokens=int(data.get("prompt_eval_count", 0)),
            completion_tokens=int(data.get("eval_count", 0)),
            cost_usd=0.0,
            resolved_model=model,
        )

    return chat


async def with_retries(
    chat: Chat,
    prompt: str,
    *,
    attempts: int = 4,
    backoff: float = 2.0,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> Completion:
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            return await chat(prompt)
        except (httpx.HTTPError, CallFailed, KeyError, ValueError) as error:
            last = error
            if attempt + 1 < attempts:
                await sleep(backoff * (2**attempt))
    raise CallFailed(str(last)[:300]) from last
```

`spend.py`:
```python
"""What the study has spent, and the cap that stops it.

OpenRouter reports the billed cost per call; the price table is only the
fallback when it does not, and the source of the dry-run estimate.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from scripts.ground_truth.llm import Completion

# USD per 1M tokens (input, output), OpenRouter list prices on 2026-09-27.
PRICES: dict[str, tuple[float, float]] = {
    "mistralai/mistral-large-2512": (0.5, 1.5),
    "anthropic/claude-haiku-4.5": (1.0, 5.0),
    "openai/gpt-4.1": (2.0, 8.0),
    "google/gemini-2.5-flash": (0.3, 2.5),
    "deepseek/deepseek-chat-v3-0324": (0.29, 1.14),
}
DEFAULT_CAP_USD = 35.0


class BudgetExceeded(RuntimeError):
    pass


def estimate(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    if model not in PRICES:
        raise ValueError(f"No price for {model!r}; add it to spend.PRICES.")
    price_in, price_out = PRICES[model]
    return (prompt_tokens * price_in + completion_tokens * price_out) / 1_000_000


class SpendLedger:
    def __init__(self, path: Path, cap_usd: float) -> None:
        self.path = path
        self.cap_usd = cap_usd
        self.total = 0.0
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    self.total += json.loads(line)["cost_usd"]

    def check(self) -> None:
        if self.total >= self.cap_usd:
            raise BudgetExceeded(
                f"Spent USD {self.total:.4f} of a USD {self.cap_usd:.2f} cap. "
                f"Everything paid for is cached; raise --cap to continue."
            )

    def record(self, *, stage: str, model: str, completion: Completion) -> float:
        cost = completion.cost_usd
        if cost is None:
            cost = estimate(model, completion.prompt_tokens, completion.completion_tokens)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({
                "at": datetime.now(UTC).isoformat(timespec="seconds"),
                "stage": stage,
                "model": model,
                "prompt_tokens": completion.prompt_tokens,
                "completion_tokens": completion.completion_tokens,
                "cost_usd": cost,
                "estimated": completion.cost_usd is None,
            }, sort_keys=True) + "\n")
        self.total += cost
        return cost
```

- [ ] **Step 4:** PASS. **Step 5:** commit `feat(ground-truth): OpenRouter/Ollama calls with a persistent spend cap`.

---

### Task 3: Translation stage and review session

**Files:** Create `scripts/ground_truth/translate.py`, `scripts/ground_truth/review.py`; tests.

**Interfaces:**
- Consumes: `records.*`, `llm.*`, `spend.SpendLedger`, `sample.EN_PER_TASK`, `sample.PER_TASK`.
- Produces: `translate.TRANSLATOR`, `translate.translation_prompt(text) -> str`, `translate.clean(reply) -> str`, `translate.translation_problems(source, translated) -> list[str]`, `translate.TranslationRow(prompt_id, status, text, problems: list[str], attempts: int)`, `async translate.translate_all(rows, *, chat, cache_path, ledger, concurrency=8) -> dict[str, TranslationRow]`, `translate.assemble_spanish(rows_en, translations, *, per_task, en_per_task) -> list[PromptRow]`; `review.REVIEW_SIZE=40`, `review.review_sample(rows_es, *, size, seed) -> list[PromptRow]`, `review.error_rate(path) -> dict`.

- [ ] **Step 1: Failing tests**

```python
from scripts.ground_truth import translate, records, review

def test_problems_catch_lost_numbers_and_code():
    src = "Janet has 16 eggs and eats 3.\n```python\nassert f(1) == 2\n```"
    assert translate.translation_problems(src, "Janet tiene 16 huevos y come 3.\n```python\nassert f(1) == 2\n```") == []
    assert any("numbers" in p for p in translate.translation_problems(src, "Janet tiene huevos.\n```python\nassert f(1) == 2\n```"))
    assert any("code" in p for p in translate.translation_problems(src, "Janet tiene 16 huevos y come 3.\n```python\nassert g(1) == 2\n```"))

def test_problems_tolerate_spanish_number_formatting():
    assert translate.translation_problems("It costs 1,000.50 dollars", "Cuesta 1.000,50 dólares") == []

def test_problems_catch_an_answer_instead_of_a_translation():
    src = "What causes the seasons?"
    assert any("answer" in p for p in translate.translation_problems(src, "¿Qué causa las estaciones? " + "Las estaciones se deben a la inclinación del eje. " * 5))
    assert translate.translation_problems(src, "") == ["empty"]

def test_clean_strips_wrappers():
    assert translate.clean("<request>\n¿Hola?\n</request>") == "¿Hola?"
    assert translate.clean('"¿Hola?"') == "¿Hola?"
    assert translate.clean("¿Hola?") == "¿Hola?"

def _row(pid, task, role="corpus"):
    return records.PromptRow(pid, task, "s", f"p {pid}", role)

def test_assemble_spanish_replaces_rejects_from_reserve_and_flags_en_subset():
    rows = [_row("t-0", "code"), _row("t-1", "code"), _row("t-2", "code", "reserve"), _row("t-3", "code", "reserve")]
    tr = {
        "t-0": translate.TranslationRow("t-0", "ok", "es0", [], 1),
        "t-1": translate.TranslationRow("t-1", "rejected", "", ["numbers"], 2),
        "t-2": translate.TranslationRow("t-2", "ok", "es2", [], 1),
    }
    got = translate.assemble_spanish(rows, tr, per_task=2, en_per_task=1)
    assert [(r.prompt_id, r.prompt, r.role, r.en_subset) for r in got] == [
        ("t-0", "es0", "corpus", True), ("t-2", "es2", "corpus", False)]

def test_assemble_spanish_refuses_an_exhausted_reserve():
    import pytest
    rows = [_row("t-0", "code"), _row("t-1", "code", "reserve")]
    tr = {"t-0": translate.TranslationRow("t-0", "rejected", "", ["x"], 2)}
    with pytest.raises(ValueError, match="code"):
        translate.assemble_spanish(rows, tr, per_task=1, en_per_task=1)

async def test_translate_all_retries_once_then_rejects_and_resumes(tmp_path):
    from scripts.ground_truth import llm, spend
    replies = iter(["sin numero", "sin numero", "tiene 2"])
    calls = []
    async def chat(prompt):
        calls.append(prompt)
        return llm.Completion(next(replies), "stop", 1, 1, 0.0, "m")
    ledger = spend.SpendLedger(tmp_path / "spend.jsonl", cap_usd=1)
    rows = [records.PromptRow("a", "code", "s", "has 2", "corpus"), records.PromptRow("b", "code", "s", "has 2", "corpus")]
    got = await translate.translate_all(rows, chat=chat, cache_path=tmp_path / "t.jsonl", ledger=ledger, concurrency=1)
    assert got["a"].status == "rejected" and got["a"].attempts == 2
    assert got["b"].status == "ok" and got["b"].text == "tiene 2"
    again = await translate.translate_all(rows, chat=chat, cache_path=tmp_path / "t.jsonl", ledger=ledger, concurrency=1)
    assert len(calls) == 3 and again == got

def test_review_sample_is_deterministic_and_bounded():
    rows = [records.PromptRow(f"p{i}", "code", "s", "x", "corpus") for i in range(100)]
    assert review.review_sample(rows, size=40, seed=1) == review.review_sample(list(reversed(rows)), size=40, seed=1)
    assert len(review.review_sample(rows, size=40, seed=1)) == 40
```

Note: rejected rows are cached and **not** retried on re-run (a deterministic translator at temperature 0 would reject again; re-paying buys nothing).

- [ ] **Step 2:** FAIL.

- [ ] **Step 3: Implement**

`translate.py`:
```python
"""Stage 2: translate the corpus into Spanish.

    python -m scripts.ground_truth.translate [--cap 35]

The translator comes from a model family that neither answers nor grades, so
no candidate is favoured by its own phrasing. A mechanical check guards what a
translation must never change — numbers and code — and a rejected prompt is
replaced from its stratum's reserve rather than kept broken.
"""

from __future__ import annotations

import argparse
import asyncio
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from scripts.ground_truth import cli, llm, records, sample, spend

TRANSLATOR = "mistralai/mistral-large-2512"
MAX_TOKENS = 2048
ATTEMPTS = 2
ANSWER_RATIO = 2.5  # a translation this much longer than its source is an answer

_INSTRUCTIONS = """\
Translate the request between the tags from English into neutral Latin American Spanish.
Rules:
- Translate it; do not answer it, do not add anything.
- Keep every number, every code block, everything inside backticks, function and \
variable names, URLs and proper names exactly as they are.
- Keep the line breaks.
- Reply with the translation only, without the tags.

<request>
{prompt}
</request>"""

_CODE = re.compile(r"```.*?```|`[^`\n]+`", re.DOTALL)
_DIGITS = re.compile(r"\d+")


@dataclass(frozen=True)
class TranslationRow:
    prompt_id: str
    status: str
    text: str
    problems: list[str] = field(default_factory=list)
    attempts: int = 1


def translation_prompt(text: str) -> str:
    return _INSTRUCTIONS.format(prompt=text)


def clean(reply: str) -> str:
    text = reply.strip()
    text = re.sub(r"^<request>\s*|\s*</request>$", "", text).strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        text = text[1:-1].strip()
    return text


def translation_problems(source: str, translated: str) -> list[str]:
    if not translated.strip():
        return ["empty"]
    problems: list[str] = []
    # Digit runs, not numbers: "1,000.50" and "1.000,50" are the same runs.
    if Counter(_DIGITS.findall(_CODE.sub("", source))) != Counter(_DIGITS.findall(_CODE.sub("", translated))):
        problems.append("numbers differ")
    if _CODE.findall(source) != _CODE.findall(translated):
        problems.append("code spans changed")
    if len(translated) > ANSWER_RATIO * len(source) + 40:
        problems.append("looks like an answer, not a translation")
    return problems


async def translate_all(
    rows: list[records.PromptRow],
    *,
    chat: llm.Chat,
    cache_path: Path,
    ledger: spend.SpendLedger,
    concurrency: int = 8,
) -> dict[str, TranslationRow]:
    done = records.latest(records.read_rows(cache_path, TranslationRow), key=lambda r: r.prompt_id)
    gate = asyncio.Semaphore(concurrency)

    async def one(row: records.PromptRow) -> None:
        async with gate:
            problems: list[str] = []
            text = ""
            for attempt in range(1, ATTEMPTS + 1):
                ledger.check()
                completion = await llm.with_retries(chat, translation_prompt(row.prompt))
                ledger.record(stage="translate", model=TRANSLATOR, completion=completion)
                text = clean(completion.text)
                problems = translation_problems(row.prompt, text)
                if not problems:
                    break
            result = TranslationRow(
                row.prompt_id, "rejected" if problems else "ok", "" if problems else text, problems, attempt
            )
            records.append_row(result, cache_path)
            done[row.prompt_id] = result

    await asyncio.gather(*(one(row) for row in rows if row.prompt_id not in done))
    return {row.prompt_id: done[row.prompt_id] for row in rows if row.prompt_id in done}


def assemble_spanish(
    rows_en: list[records.PromptRow],
    translations: dict[str, TranslationRow],
    *,
    per_task: int,
    en_per_task: int,
) -> list[records.PromptRow]:
    """Corpus prompts that translated cleanly, topped up from the reserve in order."""
    by_task: dict[str, list[records.PromptRow]] = {}
    for row in rows_en:
        by_task.setdefault(row.task_type, []).append(row)

    out: list[records.PromptRow] = []
    for task, rows in by_task.items():
        ordered = [r for r in rows if r.role == "corpus"] + [r for r in rows if r.role == "reserve"]
        kept = [r for r in ordered if (t := translations.get(r.prompt_id)) is not None and t.status == "ok"]
        if len(kept) < per_task:
            raise ValueError(f"Task {task!r}: only {len(kept)} clean translations for {per_task} slots.")
        for index, row in enumerate(kept[:per_task]):
            out.append(records.PromptRow(
                row.prompt_id, task, row.source, translations[row.prompt_id].text,
                "corpus", en_subset=index < en_per_task,
            ))
    return out


def _needed(rows_en: list[records.PromptRow], translations: dict[str, TranslationRow]) -> list[records.PromptRow]:
    """Corpus rows, plus as many reserve rows per task as there are rejects."""
    wanted: list[records.PromptRow] = []
    for task in sorted({r.task_type for r in rows_en}):
        rows = [r for r in rows_en if r.task_type == task]
        corpus = [r for r in rows if r.role == "corpus"]
        rejects = sum(1 for r in corpus if (t := translations.get(r.prompt_id)) and t.status != "ok")
        reserve = [r for r in rows if r.role == "reserve"]
        reserve_rejects = sum(1 for r in reserve if (t := translations.get(r.prompt_id)) and t.status != "ok")
        wanted += corpus + reserve[: rejects + reserve_rejects]
    return wanted


async def run(args: argparse.Namespace) -> int:
    root: Path = args.root
    rows_en = records.read_rows(root / "prompts.en.jsonl", records.PromptRow)
    ledger = spend.SpendLedger(root / "spend.jsonl", cap_usd=args.cap)
    cache = root / "translations.jsonl"
    async with cli.openrouter_client() as client:
        chat = llm.openrouter_chat(client, TRANSLATOR, max_tokens=MAX_TOKENS)
        translations: dict[str, TranslationRow] = {}
        while True:  # each pass pulls in reserve rows for the rejects of the last
            batch = _needed(rows_en, translations)
            translations = await translate_all(batch, chat=chat, cache_path=cache, ledger=ledger)
            if all(r.prompt_id in translations for r in _needed(rows_en, translations)):
                break
    rows_es = assemble_spanish(rows_en, translations, per_task=sample.PER_TASK, en_per_task=sample.EN_PER_TASK)
    records.write_rows(rows_es, root / "prompts.es.jsonl")
    rejected = sum(1 for t in translations.values() if t.status != "ok")
    cli.update_provenance(
        root,
        translator=TRANSLATOR,
        translations_rejected=rejected,
        prompts_es_sha256=cli.sha256_of(root / "prompts.es.jsonl"),
    )
    print(f"{len(rows_es)} Spanish prompts; {rejected} translations rejected; spent USD {ledger.total:.4f}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=cli.DEFAULT_ROOT)
    parser.add_argument("--cap", type=float, default=spend.DEFAULT_CAP_USD)
    return asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
```

`review.py`:
```python
"""Human spot check of the translations.

    python -m scripts.ground_truth.review

Shows 40 English/Spanish pairs drawn with a fixed seed. For each: y = faithful,
n = wrong (meaning changed, something lost or added), s = skip. Resumable.
"""

from __future__ import annotations

import argparse
import json
import random
import textwrap
from datetime import UTC, datetime
from pathlib import Path

from scripts.ground_truth import cli, records

REVIEW_SIZE = 40
SEED = 20260927


def review_sample(rows_es: list[records.PromptRow], *, size: int, seed: int) -> list[records.PromptRow]:
    ordered = sorted(rows_es, key=lambda r: r.prompt_id)
    return sorted(random.Random(seed).sample(ordered, min(size, len(ordered))), key=lambda r: r.prompt_id)


def error_rate(path: Path) -> dict[str, float | int]:
    if not path.exists():
        return {"reviewed": 0, "wrong": 0, "rate": 0.0}
    verdicts: dict[str, bool] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            raw = json.loads(line)
            verdicts[raw["prompt_id"]] = raw["faithful"]
    wrong = sum(1 for ok in verdicts.values() if not ok)
    return {"reviewed": len(verdicts), "wrong": wrong, "rate": wrong / len(verdicts) if verdicts else 0.0}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=cli.DEFAULT_ROOT)
    root = parser.parse_args().root
    en = {r.prompt_id: r for r in records.read_rows(root / "prompts.en.jsonl", records.PromptRow)}
    es = records.read_rows(root / "prompts.es.jsonl", records.PromptRow)
    out = root / "translation_review.jsonl"
    done = set()
    if out.exists():
        done = {json.loads(l)["prompt_id"] for l in out.read_text(encoding="utf-8").splitlines() if l.strip()}
    queue = [r for r in review_sample(es, size=REVIEW_SIZE, seed=SEED) if r.prompt_id not in done]
    for position, row in enumerate(queue, start=1):
        print("─" * 78, f"\n{position}/{len(queue)}  {row.prompt_id}\nEN:\n{textwrap.fill(en[row.prompt_id].prompt, 78)}")
        print(f"\nES:\n{textwrap.fill(row.prompt, 78)}\n")
        while (answer := input("faithful? [y/n/s] ").strip().lower()) not in {"y", "n", "s"}:
            pass
        if answer == "s":
            continue
        note = input("note (optional): ").strip() if answer == "n" else ""
        with out.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({
                "prompt_id": row.prompt_id, "faithful": answer == "y", "note": note,
                "recorded_at": datetime.now(UTC).isoformat(timespec="seconds"),
            }, ensure_ascii=False) + "\n")
    print(error_rate(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4:** PASS. **Step 5:** commit `feat(ground-truth): guarded translation with reserve replacement and a review session`.

---

### Task 4: Capture stage

**Files:** Create `scripts/ground_truth/capture.py`; tests.

**Interfaces:**
- Consumes: `records.*`, `llm.*`, `spend.*`, `cli.*`.
- Produces: `capture.ROLES: dict[str, tuple[str, str]]` = `{"qwen7b": ("ollama","qwen2.5:7b"), "llama3b": ("ollama","llama3.2:3b"), "haiku": ("openrouter","anthropic/claude-haiku-4.5"), "gpt41": ("openrouter","openai/gpt-4.1")}`; `capture.LANGS=("es","en")`; `capture.MAX_TOKENS=1024`; `capture.items_for(lang, rows_en, rows_es) -> list[tuple[str, str]]`; `async capture.capture_role(items, *, lang, model, chat, out_path, ledger: SpendLedger | None, concurrency) -> dict[str, ResponseRow]`; `capture.responses_path(root, role, lang) -> Path`; `capture.load_responses(root, lang) -> dict[str, dict[str, ResponseRow]]` (role → prompt_id → latest row).

- [ ] **Step 1: Failing tests**

```python
from scripts.ground_truth import capture, llm, records, spend

def test_items_for_uses_spanish_corpus_and_english_subset():
    en = [records.PromptRow("a", "code", "s", "EN a", "corpus"), records.PromptRow("b", "code", "s", "EN b", "corpus"),
          records.PromptRow("c", "code", "s", "EN c", "reserve")]
    es = [records.PromptRow("a", "code", "s", "ES a", "corpus", en_subset=True),
          records.PromptRow("c", "code", "s", "ES c", "corpus", en_subset=False)]
    assert capture.items_for("es", en, es) == [("a", "ES a"), ("c", "ES c")]
    assert capture.items_for("en", en, es) == [("a", "EN a")]

async def test_capture_resumes_without_repaying_and_retries_failures(tmp_path):
    calls = []
    fail = {"b"}
    async def chat(prompt):
        calls.append(prompt)
        if prompt in fail:
            raise llm.CallFailed("down")
        return llm.Completion(f"r:{prompt}", "stop", 1, 2, 0.001, "m")
    ledger = spend.SpendLedger(tmp_path / "spend.jsonl", cap_usd=1)
    out = tmp_path / "gpt41.es.jsonl"
    items = [("a", "a"), ("b", "b")]
    got = await capture.capture_role(items, lang="es", model="openai/gpt-4.1", chat=chat, out_path=out, ledger=ledger, concurrency=1)
    assert got["a"].status == "ok" and got["b"].status == "failed"
    fail.clear()
    got = await capture.capture_role(items, lang="es", model="openai/gpt-4.1", chat=chat, out_path=out, ledger=ledger, concurrency=1)
    assert calls == ["a", "b", "b"] and got["b"].status == "ok"
    assert ledger.total == pytest.approx(0.002)

async def test_capture_stops_at_the_cap_and_keeps_what_was_paid(tmp_path):
    import pytest
    async def chat(prompt):
        return llm.Completion("x", "stop", 1, 1, 0.6, "m")
    ledger = spend.SpendLedger(tmp_path / "spend.jsonl", cap_usd=1.0)
    out = tmp_path / "haiku.es.jsonl"
    with pytest.raises(spend.BudgetExceeded):
        await capture.capture_role([("a", "a"), ("b", "b"), ("c", "c")], lang="es", model="anthropic/claude-haiku-4.5",
                                   chat=chat, out_path=out, ledger=ledger, concurrency=1)
    assert [r.prompt_id for r in records.read_rows(out, records.ResponseRow)] == ["a", "b"]
```

(add `import pytest` at module top of the test file once.)

- [ ] **Step 2:** FAIL.

- [ ] **Step 3: Implement** `capture.py`:
```python
"""Stage 3: every candidate answers every prompt.

    python -m scripts.ground_truth.capture --roles qwen7b,llama3b,haiku,gpt41 --langs es,en [--dry-run]

Rows are written as they arrive. A failed call is recorded as failed and
retried by the next run; an ok row is never paid for twice.
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from scripts.ground_truth import cli, llm, records, spend

ROLES: dict[str, tuple[str, str]] = {
    "qwen7b": ("ollama", "qwen2.5:7b"),
    "llama3b": ("ollama", "llama3.2:3b"),
    "haiku": ("openrouter", "anthropic/claude-haiku-4.5"),
    "gpt41": ("openrouter", "openai/gpt-4.1"),
}
LANGS = ("es", "en")
MAX_TOKENS = 1024
OPENROUTER_CONCURRENCY = 8
ASSUMED_OUTPUT_TOKENS = 450  # dry-run only


def responses_path(root: Path, role: str, lang: str) -> Path:
    return root / "responses" / f"{role}.{lang}.jsonl"


def items_for(lang: str, rows_en: list[records.PromptRow], rows_es: list[records.PromptRow]) -> list[tuple[str, str]]:
    if lang == "es":
        return [(r.prompt_id, r.prompt) for r in rows_es]
    english = {r.prompt_id: r.prompt for r in rows_en}
    return [(r.prompt_id, english[r.prompt_id]) for r in rows_es if r.en_subset]


def load_responses(root: Path, lang: str) -> dict[str, dict[str, records.ResponseRow]]:
    return {
        role: records.latest(records.read_rows(responses_path(root, role, lang), records.ResponseRow), key=lambda r: r.prompt_id)
        for role in ROLES
    }


async def capture_role(
    items: list[tuple[str, str]],
    *,
    lang: str,
    model: str,
    chat: llm.Chat,
    out_path: Path,
    ledger: spend.SpendLedger | None,
    concurrency: int,
) -> dict[str, records.ResponseRow]:
    done = records.latest(records.read_rows(out_path, records.ResponseRow), key=lambda r: r.prompt_id)
    gate = asyncio.Semaphore(concurrency)

    async def one(prompt_id: str, prompt: str) -> None:
        async with gate:
            if ledger is not None:
                ledger.check()
            try:
                c = await llm.with_retries(chat, prompt)
            except llm.CallFailed as error:
                row = records.ResponseRow(prompt_id, lang, model, "failed", "", "", 0, 0, 0.0, model, str(error))
            else:
                cost = ledger.record(stage="capture", model=model, completion=c) if ledger else 0.0
                row = records.ResponseRow(prompt_id, lang, model, "ok", c.text, c.finish_reason,
                                          c.prompt_tokens, c.completion_tokens, cost, c.resolved_model)
            records.append_row(row, out_path)
            done[prompt_id] = row

    pending = [(pid, p) for pid, p in items if pid not in done or done[pid].status != "ok"]
    await asyncio.gather(*(one(pid, p) for pid, p in pending))
    return {pid: done[pid] for pid, _ in items if pid in done}


def dry_run(items_by_lang: dict[str, list[tuple[str, str]]], roles: list[str]) -> float:
    total = 0.0
    for role in roles:
        kind, model = ROLES[role]
        if kind != "openrouter":
            continue
        for lang, items in items_by_lang.items():
            cost = sum(spend.estimate(model, len(p) // 4 + 10, ASSUMED_OUTPUT_TOKENS) for _, p in items)
            print(f"  {role:8} {lang}: {len(items):5} prompts ≈ USD {cost:.2f}")
            total += cost
    print(f"  total ≈ USD {total:.2f}")
    return total


async def run(args: argparse.Namespace) -> int:
    root: Path = args.root
    rows_en = records.read_rows(root / "prompts.en.jsonl", records.PromptRow)
    rows_es = records.read_rows(root / "prompts.es.jsonl", records.PromptRow)
    roles = args.roles.split(",")
    items_by_lang = {lang: items_for(lang, rows_en, rows_es) for lang in args.langs.split(",")}
    if args.dry_run:
        dry_run(items_by_lang, roles)
        return 0

    ledger = spend.SpendLedger(root / "spend.jsonl", cap_usd=args.cap)
    async with cli.openrouter_client() as premium, cli.ollama_client() as ollama:
        tags = (await ollama.get("/api/tags")).json().get("models", [])
        digests = {m["model"]: m.get("digest", "") for m in tags}
        for role in roles:
            kind, model = ROLES[role]
            if kind == "ollama" and model not in digests:
                raise RuntimeError(f"{model} is not pulled; run `ollama pull {model}`.")
            chat = (llm.ollama_chat(ollama, model, max_tokens=MAX_TOKENS) if kind == "ollama"
                    else llm.openrouter_chat(premium, model, max_tokens=MAX_TOKENS))
            for lang, items in items_by_lang.items():
                print(f"{role} ({model}) {lang}: {len(items)} prompts …", flush=True)
                got = await capture_role(
                    items, lang=lang, model=model, chat=chat, out_path=responses_path(root, role, lang),
                    ledger=ledger if kind == "openrouter" else None,
                    concurrency=OPENROUTER_CONCURRENCY if kind == "openrouter" else 1,
                )
                failed = sum(1 for r in got.values() if r.status != "ok")
                print(f"  {failed} failed; spent so far USD {ledger.total:.4f}", flush=True)
        version = (await ollama.get("/api/version")).json().get("version", "unknown")
    cli.update_provenance(
        root,
        candidates={role: model for role, (_, model) in ROLES.items()},
        ollama_version=version,
        ollama_digests={m: d for m, d in digests.items() if m in {model for _, model in ROLES.values()}},
        max_tokens=MAX_TOKENS,
        temperature=0.0,
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=cli.DEFAULT_ROOT)
    parser.add_argument("--roles", default=",".join(ROLES))
    parser.add_argument("--langs", default=",".join(LANGS))
    parser.add_argument("--cap", type=float, default=spend.DEFAULT_CAP_USD)
    parser.add_argument("--dry-run", action="store_true")
    return asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
```

Concurrency note: with 8 in flight, the cap can be overshot by at most 8 calls (≪ USD 0.1).

- [ ] **Step 4:** PASS. **Step 5:** commit `feat(ground-truth): resumable capture with a spend cap`.

---

### Task 5: Pairs and the Spanish hold-out

**Files:** Create `scripts/ground_truth/pairs.py`, `scripts/ground_truth/holdout.py`; tests.

**Interfaces:**
- Consumes: `records.*`, `capture.ROLES`, `capture.load_responses`, `metric_validation.corpus.{Pair, ResponseSide, TASK_TYPES, write_pairs, read_pairs}`.
- Produces: `pairs.CANDIDATES=("qwen7b","llama3b","haiku")`, `pairs.REFERENCE="gpt41"`, `pairs.LOCAL_ROLES=("qwen7b","llama3b")`, `pairs.build_pairs(lang, prompts: list[PromptRow], responses: dict[str, dict[str, ResponseRow]]) -> tuple[list[Pair], dict[str, int]]` (pairs, skip counts `{"reference_unusable": n, "candidate_failed": m}`), `pairs.split_pair_id(pair_id) -> tuple[str, str, str]`; `holdout.HOLDOUT_PER_TASK=10`, `holdout.RATER="human-es-1"`, `holdout.select_holdout(pairs_es, *, per_task, seed) -> list[Pair]`, `holdout.calibration_negatives(pairs_es, *, seed, count=2) -> list[Pair]`, `holdout.holdout_dir(root) -> Path`.

- [ ] **Step 1: Failing tests**

```python
from scripts.ground_truth import pairs as gt_pairs, holdout
from scripts.metric_validation.corpus import TASK_TYPES

def _resp(pid, role, text="t", status="ok"):
    return records.ResponseRow(pid, "es", role, status, text, "stop", 1, 1, 0.0, role)

def test_build_pairs_skips_unusable_reference_and_failed_candidates():
    prompts = [records.PromptRow("p1", "code", "s", "P1", "corpus"), records.PromptRow("p2", "code", "s", "P2", "corpus")]
    responses = {
        "gpt41": {"p1": _resp("p1", "gpt41", "ref"), "p2": _resp("p2", "gpt41", "   ")},
        "qwen7b": {"p1": _resp("p1", "qwen7b"), "p2": _resp("p2", "qwen7b")},
        "llama3b": {"p1": _resp("p1", "llama3b", status="failed")},
        "haiku": {"p1": _resp("p1", "haiku")},
    }
    got, skipped = gt_pairs.build_pairs("es", prompts, responses)
    assert [p.pair_id for p in got] == ["es:haiku:p1", "es:qwen7b:p1"]
    assert skipped == {"reference_unusable": 1, "candidate_failed": 1}
    qwen = got[1]
    assert qwen.kind == "local_vs_premium" and qwen.right.origin == "reference" and qwen.right.text == "ref"
    assert got[0].kind == "premium_vs_premium"
    assert gt_pairs.split_pair_id("es:qwen7b:code-0001") == ("es", "qwen7b", "code-0001")

def _corpus_pairs():
    prompts = [records.PromptRow(f"{t}-{i:04d}", t, "s", f"P {t} {i}", "corpus") for t in TASK_TYPES for i in range(30)]
    responses = {role: {p.prompt_id: _resp(p.prompt_id, role, f"{role} {p.prompt_id}") for p in prompts}
                 for role in ("gpt41", "qwen7b", "llama3b", "haiku")}
    return gt_pairs.build_pairs("es", prompts, responses)[0]

def test_holdout_is_stratified_deterministic_and_prompt_distinct():
    from collections import Counter
    ps = _corpus_pairs()
    got = holdout.select_holdout(ps, per_task=10, seed=3)
    assert got == holdout.select_holdout(list(reversed(ps)), per_task=10, seed=3)
    assert Counter(p.task_type for p in got) == {t: 10 for t in TASK_TYPES}
    by_cand = Counter(gt_pairs.split_pair_id(p.pair_id)[1] for p in got)
    assert set(by_cand) == {"qwen7b", "llama3b", "haiku"} and max(by_cand.values()) - min(by_cand.values()) <= 1
    for task in TASK_TYPES:
        pids = [gt_pairs.split_pair_id(p.pair_id)[2] for p in got if p.task_type == task]
        assert len(pids) == len(set(pids))

def test_calibration_negatives_are_off_prompt_references():
    ps = _corpus_pairs()
    neg = holdout.calibration_negatives(ps, seed=3, count=2)
    assert len(neg) == 2 and all(p.kind == "cross_prompt" for p in neg)
    for p in neg:
        assert p.left.text != p.right.text and p.pair_id.startswith("xpr:")
```

- [ ] **Step 2:** FAIL.

- [ ] **Step 3: Implement**

`pairs.py`:
```python
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
```

`holdout.py`:
```python
"""Stage 4: draw the Spanish pairs a human grades, before any judge runs.

    python -m scripts.ground_truth.holdout

The draw depends on the seed and the corpus only, so it cannot lean toward
the pairs the judges find easy or hard. The two cross-prompt pairs exist for
the calibration round of the labelling session and are never scored.

Then:  python -m scripts.metric_validation.label --rater human-es-1 \\
         --pairs benchmarks/ground-truth/v1/holdout/pairs.jsonl \\
         --labels benchmarks/ground-truth/v1/holdout/labels
"""

from __future__ import annotations

import argparse
import random
from dataclasses import replace
from pathlib import Path

from scripts.ground_truth import capture, cli, pairs, records
from scripts.metric_validation import raters
from scripts.metric_validation.corpus import Pair, TASK_TYPES, write_pairs

HOLDOUT_PER_TASK = 10
SEED = 20260927
RATER = "human-es-1"


def holdout_dir(root: Path) -> Path:
    return root / "holdout"


def select_holdout(pairs_es: list[Pair], *, per_task: int, seed: int) -> list[Pair]:
    ordered = sorted(pairs_es, key=lambda p: p.pair_id)
    out: list[Pair] = []
    for task_index, task in enumerate(TASK_TYPES):
        rng = random.Random(f"{seed}:{task}")
        # Rotate who gets the extra slot so the totals differ by at most one.
        shares = [per_task // 3] * 3
        for extra in range(per_task % 3):
            shares[(task_index + extra) % 3] += 1
        used: set[str] = set()
        for candidate, share in zip(pairs.CANDIDATES, shares, strict=True):
            pool = [p for p in ordered if p.task_type == task
                    and pairs.split_pair_id(p.pair_id)[1] == candidate
                    and pairs.split_pair_id(p.pair_id)[2] not in used]
            if len(pool) < share:
                raise ValueError(f"{task}/{candidate}: {len(pool)} pairs for {share} slots.")
            for picked in rng.sample(pool, share):
                used.add(pairs.split_pair_id(picked.pair_id)[2])
                out.append(picked)
    return sorted(out, key=lambda p: p.pair_id)


def calibration_negatives(pairs_es: list[Pair], *, seed: int, count: int = 2) -> list[Pair]:
    """A reference answer shown against the reference answer to another prompt."""
    refs: dict[str, Pair] = {}
    for p in sorted(pairs_es, key=lambda p: p.pair_id):
        refs.setdefault(pairs.split_pair_id(p.pair_id)[2], p)
    prompt_ids = sorted(refs)
    rng = random.Random(f"{seed}:calibration")
    out: list[Pair] = []
    for prompt_id in rng.sample(prompt_ids, count):
        base = refs[prompt_id]
        siblings = [i for i in prompt_ids if i != prompt_id and refs[i].task_type == base.task_type]
        other = refs[rng.choice(siblings)]
        out.append(replace(
            base,
            pair_id=f"xpr:{prompt_id}",
            kind="cross_prompt",
            left=base.right,
            right=replace(other.right, origin="reference_offtarget"),
        ))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=cli.DEFAULT_ROOT)
    root = parser.parse_args().root
    prompts = records.read_rows(root / "prompts.es.jsonl", records.PromptRow)
    corpus_pairs, _ = pairs.build_pairs("es", prompts, capture.load_responses(root, "es"))
    chosen = select_holdout(corpus_pairs, per_task=HOLDOUT_PER_TASK, seed=SEED)
    target = holdout_dir(root) / "pairs.jsonl"
    if target.exists():
        raise RuntimeError(f"{target} exists; the hold-out is drawn once.")
    target.parent.mkdir(parents=True, exist_ok=True)
    write_pairs(chosen + calibration_negatives(corpus_pairs, seed=SEED), target)
    raters.write_roster(
        {RATER: raters.RaterProfile(RATER, "human", "rater-a", "active",
                                    "Spanish hold-out, 50 pairs drawn before any judge ran")},
        holdout_dir(root) / "raters.json",
    )
    cli.update_provenance(root, holdout_seed=SEED, holdout_sha256=cli.sha256_of(target))
    print(f"{len(chosen)} hold-out pairs → {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

(`rater-a` is the same person id the pilot uses for Joaquín, so the report can tell it is one evaluator.)

- [ ] **Step 4:** PASS. **Step 5:** commit `feat(ground-truth): candidate-vs-reference pairs and a pre-drawn Spanish hold-out`.

---

### Task 6: Pre-registration and the judge stage

**Files:** Create `benchmarks/ground-truth/v1/preregistration.md`, `scripts/ground_truth/judge.py`; tests.

**Interfaces:**
- Consumes: `records.Judgement`, `llm.*`, `spend.*`, `pairs.*`, `holdout.holdout_dir`, `metric_validation.llm_judge.{judge_prompt, parse_grade, rater_id_for}`, `metric_validation.corpus.read_pairs`.
- Produces: `judge.JUDGES=("google/gemini-2.5-flash","deepseek/deepseek-chat-v3-0324")`, `judge.ORIENTATIONS=("ab","ba")`, `judge.JUDGE_EXTRA`, `judge.payload(pair, orientation) -> dict[str,str]`, `async judge.judge_pairs(pairs, *, judge_model, chat, out_path, ledger, concurrency, parse_attempts=3) -> None`, `judge.judgements_path(root, judge_model, set_name) -> Path` (`judgements/<set>.<rater-id>.jsonl`, set ∈ {"corpus","pilot"}), `judge.ensure_preregistered(root, run_git=...)`.

- [ ] **Step 1: Write `preregistration.md`** (Spanish is fine; it is thesis material):

```markdown
# Pre-registro — ensamble de jueces (fase 2)

Fijado antes de correr cualquier juez sobre el corpus. El commit de este archivo es anterior a `judgements/corpus.*`.

- Rúbrica: `scripts/metric_validation/rubric.py` (4 grados; sustituible = `equivalent` o `minor_loss`).
- Jueces: `google/gemini-2.5-flash`, `deepseek/deepseek-chat-v3-0324`, temperatura 0, razonamiento apagado.
- Cada par candidato–referencia se juzga en las dos posiciones (`ab`, `ba`) por los dos jueces: 4 notas.
- Un par con menos de 4 notas válidas queda fuera de reglas, kappa y niveles.
- Reglas (índices 0–3 de la escala):
  - R1 unánime: las 4 notas ≤ `minor_loss`.
  - R2 mayoría: ≥ 3 de 4 notas ≤ `minor_loss`.
  - R3 ordinal: media de índices ≤ 1.5.
- Selección: mayor kappa de Cohen binario contra `human-3` sobre los 22 pares EN del piloto; empate → R1 > R2 > R3.
- Hold-out: 50 pares ES sorteados (semilla 20260927) antes de los jueces, etiquetados por `human-es-1`. Se reporta el kappa de la regla elegida con IC bootstrap 95 % (2000 remuestras, semilla 20260927). No se usa para elegir.
- Umbral: kappa ES < 0.4 → la tesis declara el ground truth "limitado por los jueces".
- Nivel por prompt: `local` si qwen2.5:7b es sustituible por gpt-4.1; si no, `economy` si claude-haiku-4.5 lo es; si no, `frontier`. Sensibilidad: lo mismo con llama3.2:3b como local.
```

- [ ] **Step 2: Failing tests**

```python
from scripts.ground_truth import judge
from scripts.metric_validation.corpus import Pair, ResponseSide

def _pair(pid="es:qwen7b:p1"):
    return Pair(pid, "local_vs_premium", "code", "PROMPT", ResponseSide("qwen7b", "q", "CAND"),
                ResponseSide("reference", "g", "REF"), {}, "unbanded")

def test_payload_orientations_and_no_provenance():
    ab, ba = judge.payload(_pair(), "ab"), judge.payload(_pair(), "ba")
    assert (ab["response_a"], ab["response_b"]) == ("CAND", "REF")
    assert (ba["response_a"], ba["response_b"]) == ("REF", "CAND")
    prompt = judge.judge_prompt_for(_pair(), "ab")
    for leak in ("qwen", "reference", "gpt", "local", "premium"):
        assert leak not in prompt.lower().replace("response", "")

async def test_judge_records_missing_after_parse_retries_and_never_defaults(tmp_path):
    replies = iter(["no idea", "still no", "{\"grade\": \"maybe\"}", '{"grade": "partial"}'])
    async def chat(prompt):
        return llm.Completion(next(replies), "stop", 1, 1, 0.0, "m")
    out = tmp_path / "j.jsonl"
    ledger = spend.SpendLedger(tmp_path / "spend.jsonl", cap_usd=1)
    await judge.judge_pairs([_pair()], judge_model="google/gemini-2.5-flash", chat=chat, out_path=out,
                            ledger=ledger, concurrency=1, orientations=("ab",))
    rows = records.read_rows(out, records.Judgement)
    assert [(r.status, r.grade) for r in rows] == [("missing", None)]
    await judge.judge_pairs([_pair()], judge_model="google/gemini-2.5-flash", chat=chat, out_path=out,
                            ledger=ledger, concurrency=1, orientations=("ab",))
    latest = records.latest(records.read_rows(out, records.Judgement), key=lambda r: (r.pair_id, r.orientation))
    assert latest[("es:qwen7b:p1", "ab")].grade == "partial"

async def test_judge_does_not_repay_ok_rows(tmp_path):
    calls = []
    async def chat(prompt):
        calls.append(prompt)
        return llm.Completion('{"grade": "equivalent"}', "stop", 1, 1, 0.0, "m")
    out = tmp_path / "j.jsonl"
    ledger = spend.SpendLedger(tmp_path / "spend.jsonl", cap_usd=1)
    for _ in range(2):
        await judge.judge_pairs([_pair()], judge_model="google/gemini-2.5-flash", chat=chat, out_path=out,
                                ledger=ledger, concurrency=1)
    assert len(calls) == 2  # ab + ba, once

def test_ensure_preregistered_refuses_uncommitted_or_missing_holdout(tmp_path):
    import pytest
    (tmp_path / "preregistration.md").write_text("x")
    with pytest.raises(RuntimeError, match="committed"):
        judge.ensure_preregistered(tmp_path, run_git=lambda *a: "")
    with pytest.raises(RuntimeError, match="hold-out"):
        judge.ensure_preregistered(tmp_path, run_git=lambda *a: "abc123")
    (tmp_path / "holdout").mkdir()
    (tmp_path / "holdout" / "pairs.jsonl").write_text("")
    judge.ensure_preregistered(tmp_path, run_git=lambda *a: "abc123")
```

`run_git(*args) -> str` returns stdout; the real one checks `git log -1 --format=%H -- <file>` is non-empty **and** `git status --porcelain -- <file>` is empty (the test stub returns the same string for both calls, so "abc123" means committed-but-dirty would pass; the real function calls them separately — implement by calling `run_git("log", ...)` then `run_git("status", ...)` and treat non-empty status as dirty; in the test, pass a stub that returns "" for `status`). Use this stub in the test instead:

```python
def _git(log, status=""):
    return lambda *args: log if args[0] == "log" else status
```
and call `run_git=_git("")`, `_git("abc123")`, plus one assertion that `_git("abc123", " M preregistration.md")` raises "committed".

- [ ] **Step 3:** FAIL.

- [ ] **Step 4: Implement** `judge.py`:
```python
"""Stage 5: both judges grade every candidate-vs-reference pair, both ways round.

    python -m scripts.ground_truth.judge --set pilot
    python -m scripts.ground_truth.judge --set corpus --langs es,en

The corpus set refuses to run until the pre-registration is committed and the
hold-out is drawn: the rules must be fixed before anyone sees a judge's grade.
"""

from __future__ import annotations

import argparse
import asyncio
import subprocess
from collections.abc import Callable
from pathlib import Path

from scripts.ground_truth import capture, cli, holdout, llm, pairs, records, spend
from scripts.metric_validation import labels as mv_labels
from scripts.metric_validation import llm_judge
from scripts.metric_validation.corpus import Pair, read_pairs

JUDGES: tuple[str, ...] = ("google/gemini-2.5-flash", "deepseek/deepseek-chat-v3-0324")
ORIENTATIONS: tuple[str, ...] = ("ab", "ba")
JUDGE_MAX_TOKENS = 200
# Thinking tokens are billed and a grade needs none.
JUDGE_EXTRA: dict[str, dict] = {"google/gemini-2.5-flash": {"reasoning": {"max_tokens": 0}}}
CONCURRENCY = 8
PILOT_ROOT = Path("benchmarks/metric-validation")
PILOT_RATER = "human-3"


def judgements_path(root: Path, judge_model: str, set_name: str) -> Path:
    return root / "judgements" / f"{set_name}.{llm_judge.rater_id_for(judge_model)}.jsonl"


def payload(pair: Pair, orientation: str) -> dict[str, str]:
    first, second = (pair.left, pair.right) if orientation == "ab" else (pair.right, pair.left)
    return {"pair_id": pair.pair_id, "prompt": pair.prompt, "response_a": first.text, "response_b": second.text}


def judge_prompt_for(pair: Pair, orientation: str) -> str:
    return llm_judge.judge_prompt(payload(pair, orientation))


async def judge_pairs(
    pair_list: list[Pair],
    *,
    judge_model: str,
    chat: llm.Chat,
    out_path: Path,
    ledger: spend.SpendLedger,
    concurrency: int,
    parse_attempts: int = 3,
    orientations: tuple[str, ...] = ORIENTATIONS,
) -> None:
    done = records.latest(records.read_rows(out_path, records.Judgement), key=lambda r: (r.pair_id, r.orientation))
    gate = asyncio.Semaphore(concurrency)

    async def one(pair: Pair, orientation: str) -> None:
        async with gate:
            reply = ""
            grade: str | None = None
            for _ in range(parse_attempts):
                ledger.check()
                try:
                    c = await llm.with_retries(chat, judge_prompt_for(pair, orientation))
                except llm.CallFailed as error:
                    reply = f"call failed: {error}"
                    break
                ledger.record(stage="judge", model=judge_model, completion=c)
                reply = c.text
                try:
                    grade = llm_judge.parse_grade(reply)
                    break
                except ValueError:
                    continue
            row = records.Judgement(pair.pair_id, judge_model, orientation,
                                    "ok" if grade else "missing", grade, reply[:500])
            records.append_row(row, out_path)

    todo = [(p, o) for p in pair_list for o in orientations
            if (p.pair_id, o) not in done or done[(p.pair_id, o)].status != "ok"]
    await asyncio.gather(*(one(p, o) for p, o in todo))


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=False).stdout.strip()


def ensure_preregistered(root: Path, run_git: Callable[..., str] = _git) -> None:
    prereg = root / "preregistration.md"
    if not prereg.exists() or not run_git("log", "-1", "--format=%H", "--", str(prereg)) \
            or run_git("status", "--porcelain", "--", str(prereg)):
        raise RuntimeError(f"{prereg} must be committed, unmodified, before judging the corpus.")
    if not (holdout.holdout_dir(root) / "pairs.jsonl").exists():
        raise RuntimeError("Draw the hold-out (python -m scripts.ground_truth.holdout) before judging.")


def pilot_pairs() -> list[Pair]:
    graded = {label.pair_id for label in mv_labels.read(PILOT_ROOT / "labels" / f"{PILOT_RATER}.jsonl")}
    return [p for p in read_pairs(PILOT_ROOT / "pairs.jsonl") if p.pair_id in graded]


def corpus_pairs(root: Path, langs: list[str]) -> list[Pair]:
    out: list[Pair] = []
    for lang in langs:
        prompts = records.read_rows(root / "prompts.es.jsonl", records.PromptRow)
        if lang == "en":
            english = {r.prompt_id: r for r in records.read_rows(root / "prompts.en.jsonl", records.PromptRow)}
            prompts = [english[r.prompt_id] for r in prompts if r.en_subset]
        built, skipped = pairs.build_pairs(lang, prompts, capture.load_responses(root, lang))
        print(f"{lang}: {len(built)} pairs; skipped {skipped}")
        out += built
    return out


async def run(args: argparse.Namespace) -> int:
    root: Path = args.root
    if args.set == "corpus":
        ensure_preregistered(root)
        pair_list = corpus_pairs(root, args.langs.split(","))
    else:
        pair_list = pilot_pairs()
    ledger = spend.SpendLedger(root / "spend.jsonl", cap_usd=args.cap)
    async with cli.openrouter_client() as client:
        for judge_model in JUDGES:
            chat = llm.openrouter_chat(client, judge_model, max_tokens=JUDGE_MAX_TOKENS,
                                       extra=JUDGE_EXTRA.get(judge_model))
            out = judgements_path(root, judge_model, args.set)
            print(f"{judge_model}: {len(pair_list)} pairs × {len(ORIENTATIONS)} …", flush=True)
            await judge_pairs(pair_list, judge_model=judge_model, chat=chat, out_path=out,
                              ledger=ledger, concurrency=CONCURRENCY)
            rows = records.latest(records.read_rows(out, records.Judgement), key=lambda r: (r.pair_id, r.orientation))
            missing = sum(1 for r in rows.values() if r.status != "ok")
            print(f"  {missing} missing; spent so far USD {ledger.total:.4f}", flush=True)
    cli.update_provenance(root, judges=list(JUDGES), judge_extra=JUDGE_EXTRA, judge_max_tokens=JUDGE_MAX_TOKENS)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=cli.DEFAULT_ROOT)
    parser.add_argument("--set", choices=("pilot", "corpus"), required=True)
    parser.add_argument("--langs", default="es,en")
    parser.add_argument("--cap", type=float, default=spend.DEFAULT_CAP_USD)
    return asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5:** PASS. **Step 6:** commit `feat(ground-truth): pre-registered judge ensemble, both orientations` (commit `preregistration.md` in this commit).

---

### Task 7: Ensemble rules and validation

**Files:** Create `scripts/ground_truth/ensemble.py`, `scripts/ground_truth/validate.py`; tests.

**Interfaces:**
- Consumes: `records.Judgement`, `judge.*`, `holdout.*`, `metric_validation.{rubric, stats, labels}`.
- Produces: `ensemble.RULES=("R1_unanimous","R2_majority","R3_ordinal_mean")`, `ensemble.substitutable(rule, grades) -> bool`, `ensemble.grades_by_pair(judgements, *, judges, orientations) -> dict[str, list[str]]`, `ensemble.choose_rule(kappas: dict[str, float | None]) -> str`; `validate.rule_kappas(pair_grades, human) -> dict[str, float | None]`, `validate.position_flip_rate(judgements, judge_model) -> float`, `validate.inter_judge_kappa(judgements) -> float`, `validate.holdout_agreement(pair_grades, human, rule, *, seed) -> dict`, `validate.validate(root) -> dict` (written to `validation.json`).

- [ ] **Step 1: Failing tests**

```python
from scripts.ground_truth import ensemble, validate

def test_rules_on_hand_worked_grades():
    g = ["equivalent", "minor_loss", "minor_loss", "partial"]  # idx 0,1,1,2 → mean 1.0
    assert not ensemble.substitutable("R1_unanimous", g)
    assert ensemble.substitutable("R2_majority", g)
    assert ensemble.substitutable("R3_ordinal_mean", g)
    h = ["minor_loss", "minor_loss", "partial", "divergent"]  # idx 1,1,2,3 → mean 1.75
    assert not ensemble.substitutable("R2_majority", h) and not ensemble.substitutable("R3_ordinal_mean", h)
    k = ["equivalent", "equivalent", "partial", "partial"]  # mean 1.0, 2 of 4
    assert not ensemble.substitutable("R2_majority", k) and ensemble.substitutable("R3_ordinal_mean", k)
    import pytest
    with pytest.raises(ValueError):
        ensemble.substitutable("R1_unanimous", g[:3])

def _j(pid, judge_, o, grade, status="ok"):
    return records.Judgement(pid, judge_, o, status, grade, "")

def test_grades_by_pair_requires_all_four_and_latest_wins():
    rows = [_j("p", "A", "ab", "partial"), _j("p", "A", "ab", "equivalent"), _j("p", "A", "ba", "equivalent"),
            _j("p", "B", "ab", "equivalent"), _j("p", "B", "ba", "equivalent"),
            _j("q", "A", "ab", "equivalent"), _j("q", "A", "ba", "equivalent"),
            _j("q", "B", "ab", "equivalent"), _j("q", "B", "ba", None, "missing")]
    got = ensemble.grades_by_pair(rows, judges=("A", "B"), orientations=("ab", "ba"))
    assert got == {"p": ["equivalent"] * 4}

def test_choose_rule_prefers_conservative_on_ties_and_skips_undefined():
    assert ensemble.choose_rule({"R1_unanimous": 0.5, "R2_majority": 0.5, "R3_ordinal_mean": 0.4}) == "R1_unanimous"
    assert ensemble.choose_rule({"R1_unanimous": None, "R2_majority": 0.2, "R3_ordinal_mean": 0.3}) == "R3_ordinal_mean"
    import pytest
    with pytest.raises(ValueError):
        ensemble.choose_rule({r: None for r in ensemble.RULES})

def test_rule_kappas_against_human():
    grades = {"a": ["equivalent"] * 4, "b": ["divergent"] * 4, "c": ["equivalent", "equivalent", "equivalent", "partial"]}
    human = {"a": "equivalent", "b": "partial", "c": "minor_loss", "z": "equivalent"}
    got = validate.rule_kappas(grades, human)
    assert got["R2_majority"] == pytest.approx(1.0) and got["R3_ordinal_mean"] == pytest.approx(1.0)
    assert got["R1_unanimous"] < 1.0

def test_position_flip_rate_counts_binary_changes_only():
    rows = [_j("p", "A", "ab", "equivalent"), _j("p", "A", "ba", "minor_loss"),
            _j("q", "A", "ab", "equivalent"), _j("q", "A", "ba", "divergent"),
            _j("r", "A", "ab", "equivalent")]
    assert validate.position_flip_rate(rows, "A") == pytest.approx(0.5)

def test_holdout_agreement_pending_without_labels():
    got = validate.holdout_agreement({"p": ["equivalent"] * 4}, {}, "R1_unanimous", seed=1)
    assert got["status"] == "pending" and got["labelled"] == 0
```

- [ ] **Step 2:** FAIL.

- [ ] **Step 3: Implement**

`ensemble.py`:
```python
"""The pre-registered rules that turn four judge grades into one verdict.

See benchmarks/ground-truth/v1/preregistration.md. Changing a rule here after
the corpus was judged invalidates the pre-registration.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from scripts.ground_truth import records
from scripts.metric_validation import rubric

RULES: tuple[str, ...] = ("R1_unanimous", "R2_majority", "R3_ordinal_mean")  # most conservative first
GRADES_PER_PAIR = 4
_CUT = rubric.SCALE.index(rubric.SUBSTITUTABLE_THROUGH)


def substitutable(rule: str, grades: Sequence[str]) -> bool:
    if len(grades) != GRADES_PER_PAIR:
        raise ValueError(f"A verdict needs {GRADES_PER_PAIR} grades, got {len(grades)}.")
    positions = [rubric.SCALE.index(grade) for grade in grades]
    passing = sum(1 for p in positions if p <= _CUT)
    if rule == "R1_unanimous":
        return passing == GRADES_PER_PAIR
    if rule == "R2_majority":
        return passing >= 3
    if rule == "R3_ordinal_mean":
        return sum(positions) / len(positions) <= 1.5
    raise ValueError(f"Unknown rule {rule!r}.")


def grades_by_pair(
    judgements: Iterable[records.Judgement], *, judges: Sequence[str], orientations: Sequence[str]
) -> dict[str, list[str]]:
    """Pairs with every (judge, orientation) graded, grades in a fixed order."""
    latest = records.latest(judgements, key=lambda r: (r.pair_id, r.judge, r.orientation))
    out: dict[str, list[str]] = {}
    for pair_id in sorted({key[0] for key in latest}):
        grades = []
        for judge in judges:
            for orientation in orientations:
                row = latest.get((pair_id, judge, orientation))
                if row is None or row.status != "ok" or row.grade is None:
                    break
                grades.append(row.grade)
        if len(grades) == len(judges) * len(orientations):
            out[pair_id] = grades
    return out


def choose_rule(kappas: dict[str, float | None]) -> str:
    defined = {rule: k for rule, k in kappas.items() if k is not None}
    if not defined:
        raise ValueError("Kappa is undefined for every rule; no rule can be chosen.")
    best = max(defined.values())
    return next(rule for rule in RULES if rule in defined and abs(defined[rule] - best) < 1e-12)
```

`validate.py`:
```python
"""Stage 6: how well the ensemble agrees with a human reader.

    python -m scripts.ground_truth.validate

English picks the rule; Spanish, drawn before the judges ran, tests it.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.ground_truth import cli, ensemble, holdout, judge, records
from scripts.metric_validation import labels as mv_labels
from scripts.metric_validation import rubric, stats

SEED = 20260927
JUDGE_LIMITED_BELOW = 0.4


def rule_kappas(pair_grades: dict[str, list[str]], human: dict[str, str]) -> dict[str, float | None]:
    common = sorted(set(pair_grades) & set(human))
    if not common:
        raise ValueError("No pair has both a full set of judge grades and a human grade.")
    out: dict[str, float | None] = {}
    truth = [rubric.is_substitutable(human[p]) for p in common]
    for rule in ensemble.RULES:
        predicted = [ensemble.substitutable(rule, pair_grades[p]) for p in common]
        try:
            out[rule] = stats.cohens_kappa(predicted, truth)
        except ValueError:
            out[rule] = None
    return out


def position_flip_rate(judgements: list[records.Judgement], judge_model: str) -> float:
    latest = records.latest(
        (r for r in judgements if r.judge == judge_model and r.status == "ok"),
        key=lambda r: (r.pair_id, r.orientation),
    )
    both = [p for p in {k[0] for k in latest} if (p, "ab") in latest and (p, "ba") in latest]
    if not both:
        raise ValueError(f"No pair graded both ways by {judge_model}.")
    flips = sum(
        1 for p in both
        if rubric.is_substitutable(latest[(p, "ab")].grade) != rubric.is_substitutable(latest[(p, "ba")].grade)
    )
    return flips / len(both)


def inter_judge_kappa(judgements: list[records.Judgement]) -> float:
    latest = records.latest((r for r in judgements if r.status == "ok"),
                            key=lambda r: (r.pair_id, r.orientation, r.judge))
    first, second = judge.JUDGES
    keys = sorted({(k[0], k[1]) for k in latest if (k[0], k[1], first) in latest and (k[0], k[1], second) in latest})
    return stats.cohens_kappa(
        [rubric.is_substitutable(latest[(*k, first)].grade) for k in keys],
        [rubric.is_substitutable(latest[(*k, second)].grade) for k in keys],
    )


def holdout_agreement(pair_grades: dict[str, list[str]], human: dict[str, str], rule: str, *, seed: int) -> dict:
    common = sorted(set(pair_grades) & set(human))
    if not common:
        return {"status": "pending", "labelled": len(human), "compared": 0}
    sample = [(ensemble.substitutable(rule, pair_grades[p]), rubric.is_substitutable(human[p])) for p in common]
    interval = stats.bootstrap_ci(
        sample, lambda draw: stats.cohens_kappa([a for a, _ in draw], [b for _, b in draw]), seed=seed
    )
    per_rule = rule_kappas(pair_grades, human)
    return {
        "status": "complete" if len(common) >= holdout.HOLDOUT_PER_TASK * 5 else "partial",
        "labelled": len(human),
        "compared": len(common),
        "excluded_without_full_grades": len(set(human) - set(pair_grades)),
        "kappa": interval.point,
        "ci95": [interval.low, interval.high],
        "resamples_used": interval.resamples_used,
        "judge_limited": interval.point < JUDGE_LIMITED_BELOW,
        "all_rules_for_reference": per_rule,
    }


def _judgements(root: Path, set_name: str) -> list[records.Judgement]:
    rows: list[records.Judgement] = []
    for model in judge.JUDGES:
        rows += records.read_rows(judge.judgements_path(root, model, set_name), records.Judgement)
    return rows


def validate(root: Path) -> dict:
    pilot = _judgements(root, "pilot")
    pilot_grades = ensemble.grades_by_pair(pilot, judges=judge.JUDGES, orientations=judge.ORIENTATIONS)
    human3 = {l.pair_id: l.grade for l in mv_labels.read(judge.PILOT_ROOT / "labels" / f"{judge.PILOT_RATER}.jsonl")}
    en = rule_kappas(pilot_grades, human3)
    chosen = ensemble.choose_rule(en)

    corpus = _judgements(root, "corpus")
    corpus_grades = ensemble.grades_by_pair(corpus, judges=judge.JUDGES, orientations=judge.ORIENTATIONS)
    label_path = holdout.holdout_dir(root) / "labels" / f"{holdout.RATER}.jsonl"
    human_es = {l.pair_id: l.grade for l in mv_labels.read(label_path) if not l.pair_id.startswith("xpr:")}

    return {
        "rule_selection": {"set": "pilot-en", "rater": judge.PILOT_RATER,
                           "compared": len(set(pilot_grades) & set(human3)), "kappas": en, "chosen": chosen},
        "holdout_es": holdout_agreement(corpus_grades, human_es, chosen, seed=SEED),
        "position_flip_rate": {m: position_flip_rate(corpus, m) for m in judge.JUDGES},
        "inter_judge_kappa": inter_judge_kappa(corpus),
        "corpus_pairs_with_full_grades": len(corpus_grades),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=cli.DEFAULT_ROOT)
    root = parser.parse_args().root
    result = validate(root)
    (root / "validation.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4:** PASS. **Step 5:** commit `feat(ground-truth): pre-registered ensemble rules, validated against human readers`.

---

### Task 8: Tier labels

**Files:** Create `scripts/ground_truth/tiers.py`; tests.

**Interfaces:**
- Consumes: `ensemble.*`, `judge.*`, `pairs.*`, `records.PromptRow`, `validate.validate` output (`validation.json["rule_selection"]["chosen"]`).
- Produces: `tiers.TIERS=("local","economy","frontier")`, `tiers.tier_for(local_ok: bool | None, economy_ok: bool | None) -> str | None`, `tiers.build_tiers(prompts_by_lang: dict[str, list[PromptRow]], pair_grades, rule, local_role) -> list[dict]`; files `tiers.jsonl`, `tiers.llama3b.jsonl` with rows `{"lang","prompt_id","task_type","tier","local_substitutable","economy_substitutable"}`.

- [ ] **Step 1: Failing tests**

```python
from scripts.ground_truth import tiers

@pytest.mark.parametrize("local_ok, economy_ok, want", [
    (True, None, "local"), (True, False, "local"), (False, True, "economy"),
    (False, False, "frontier"), (None, True, None), (False, None, None),
])
def test_tier_for(local_ok, economy_ok, want):
    assert tiers.tier_for(local_ok, economy_ok) == want

def test_build_tiers_uses_the_named_local_role():
    prompts = {"es": [records.PromptRow("p", "code", "s", "x", "corpus")]}
    grades = {"es:qwen7b:p": ["divergent"] * 4, "es:llama3b:p": ["equivalent"] * 4, "es:haiku:p": ["equivalent"] * 4}
    q = tiers.build_tiers(prompts, grades, "R1_unanimous", local_role="qwen7b")
    l = tiers.build_tiers(prompts, grades, "R1_unanimous", local_role="llama3b")
    assert q[0]["tier"] == "economy" and l[0]["tier"] == "local"
```

- [ ] **Step 2:** FAIL.

- [ ] **Step 3: Implement** `tiers.py`:
```python
"""Stage 7: the cheapest tier that serves each prompt as well as the frontier.

    python -m scripts.ground_truth.tiers
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.ground_truth import cli, ensemble, judge, records

TIERS: tuple[str, ...] = ("local", "economy", "frontier")
ECONOMY_ROLE = "haiku"


def tier_for(local_ok: bool | None, economy_ok: bool | None) -> str | None:
    """None when a missing verdict leaves the answer open."""
    if local_ok is None:
        return None
    if local_ok:
        return "local"
    if economy_ok is None:
        return None
    return "economy" if economy_ok else "frontier"


def build_tiers(
    prompts_by_lang: dict[str, list[records.PromptRow]],
    pair_grades: dict[str, list[str]],
    rule: str,
    *,
    local_role: str,
) -> list[dict]:
    def verdict(lang: str, role: str, prompt_id: str) -> bool | None:
        grades = pair_grades.get(f"{lang}:{role}:{prompt_id}")
        return None if grades is None else ensemble.substitutable(rule, grades)

    out: list[dict] = []
    for lang in sorted(prompts_by_lang):
        for prompt in sorted(prompts_by_lang[lang], key=lambda p: p.prompt_id):
            local_ok = verdict(lang, local_role, prompt.prompt_id)
            economy_ok = verdict(lang, ECONOMY_ROLE, prompt.prompt_id)
            out.append({
                "lang": lang, "prompt_id": prompt.prompt_id, "task_type": prompt.task_type,
                "tier": tier_for(local_ok, economy_ok),
                "local_substitutable": local_ok, "economy_substitutable": economy_ok,
            })
    return out


def prompts_by_lang(root: Path) -> dict[str, list[records.PromptRow]]:
    es = records.read_rows(root / "prompts.es.jsonl", records.PromptRow)
    en_all = {r.prompt_id: r for r in records.read_rows(root / "prompts.en.jsonl", records.PromptRow)}
    return {"es": es, "en": [en_all[r.prompt_id] for r in es if r.en_subset]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=cli.DEFAULT_ROOT)
    root = parser.parse_args().root
    rule = json.loads((root / "validation.json").read_text())["rule_selection"]["chosen"]
    judgements: list[records.Judgement] = []
    for model in judge.JUDGES:
        judgements += records.read_rows(judge.judgements_path(root, model, "corpus"), records.Judgement)
    grades = ensemble.grades_by_pair(judgements, judges=judge.JUDGES, orientations=judge.ORIENTATIONS)
    prompts = prompts_by_lang(root)
    for local_role, name in (("qwen7b", "tiers.jsonl"), ("llama3b", "tiers.llama3b.jsonl")):
        rows = build_tiers(prompts, grades, rule, local_role=local_role)
        (root / name).write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
        labelled = sum(1 for r in rows if r["tier"] is not None)
        print(f"{name}: {labelled}/{len(rows)} labelled ({labelled / len(rows):.1%}) with {rule}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4:** PASS. **Step 5:** commit `feat(ground-truth): cheapest sufficient tier per prompt`.

---

### Task 9: Report and thesis blocks

**Files:** Create `scripts/ground_truth/report.py`; Modify `docs/tfc/tesis/06-evaluacion.md` (§6.2 and §6.3 PENDIENTE lines → GEN markers); tests.

**Interfaces:**
- Consumes: everything above; `review.error_rate`.
- Produces: `report.replace_block(text, name, content) -> str`; `report.summarise(root) -> dict`; `report.render_markdown(summary) -> str`; `report.thesis_corpus(summary) -> str`; `report.thesis_judges(summary) -> str`. Output `report.json`, `report.md`, updated thesis blocks `corpus-fase2` and `judges-fase2`.

- [ ] **Step 1: Failing tests**

```python
from scripts.ground_truth import report

def test_replace_block_replaces_only_between_markers():
    text = "a\n<!-- GEN:x -->\nold\n<!-- /GEN:x -->\nb\n"
    assert report.replace_block(text, "x", "new") == "a\n<!-- GEN:x -->\nnew\n<!-- /GEN:x -->\nb\n"
    import pytest
    with pytest.raises(ValueError, match="y"):
        report.replace_block(text, "y", "new")

def test_tier_distribution_table_counts_unlabelled():
    rows = [{"lang": "es", "task_type": "code", "tier": "local"}, {"lang": "es", "task_type": "code", "tier": None},
            {"lang": "es", "task_type": "code", "tier": "frontier"}]
    got = report.tier_distribution(rows)
    assert got == {"es": {"code": {"local": 1, "economy": 0, "frontier": 1, "unlabelled": 1}}}
```

- [ ] **Step 2:** FAIL.

- [ ] **Step 3: Implement** `report.py` with:
  - `replace_block` (regex on `<!-- GEN:{name} -->\n(.*?)\n<!-- /GEN:{name} -->`, DOTALL; raise `ValueError(f"No GEN block {name!r}")` when absent).
  - `tier_distribution(rows) -> {lang: {task: {tier...: n, "unlabelled": n}}}`.
  - `summarise(root)`: prompt counts per task/lang, translation rejects (from `translations.jsonl`), review `error_rate`, per role/lang `failed` and `finish_reason == "length"` counts (from `capture.load_responses`), pair skip counts (`pairs.build_pairs` per lang), `validation.json`, tier distributions for `tiers.jsonl` and `tiers.llama3b.jsonl`, coverage, `spend.jsonl` total by stage.
  - `render_markdown(summary)`: sections Corpus, Translation, Capture (failures/truncations table), Judges (rule kappas table, chosen rule, ES hold-out kappa + CI or **PENDING**, position flip rate, inter-judge kappa), Tiers (distribution table per language, both local roles), Spend.
  - `thesis_corpus(summary)` in Spanish: origin (3 datasets with licenses), per-task counts, translator and rejection count, reviewed error rate.
  - `thesis_judges(summary)` in Spanish: ensemble, rules, EN kappas and chosen rule, ES kappa with CI (or "pendiente"), flip rates, "limitado por los jueces" sentence when `judge_limited`.
  - `main()`: writes `report.json`, `report.md`, and replaces the two blocks in `docs/tfc/tesis/06-evaluacion.md`.

  Code:
```python
"""Stage 8: the report, and the thesis paragraphs that cite it.

    python -m scripts.ground_truth.report
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from scripts.ground_truth import capture, cli, pairs, records, review, sources, tiers, translate

THESIS = Path("docs/tfc/tesis/06-evaluacion.md")


def replace_block(text: str, name: str, content: str) -> str:
    pattern = re.compile(rf"(<!-- GEN:{re.escape(name)} -->\n)(.*?)(\n<!-- /GEN:{re.escape(name)} -->)", re.DOTALL)
    if not pattern.search(text):
        raise ValueError(f"No GEN block {name!r} in the thesis source.")
    return pattern.sub(lambda m: m.group(1) + content + m.group(3), text, count=1)


def tier_distribution(rows: list[dict]) -> dict:
    out: dict = defaultdict(lambda: defaultdict(lambda: {t: 0 for t in (*tiers.TIERS, "unlabelled")}))
    for row in rows:
        out[row["lang"]][row["task_type"]][row["tier"] or "unlabelled"] += 1
    return json.loads(json.dumps(out))


def _jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def summarise(root: Path) -> dict:
    prompts = tiers.prompts_by_lang(root)
    translations = records.latest(records.read_rows(root / "translations.jsonl", translate.TranslationRow),
                                  key=lambda r: r.prompt_id)
    capture_stats: dict = {}
    skipped: dict = {}
    for lang, rows in prompts.items():
        responses = capture.load_responses(root, lang)
        capture_stats[lang] = {
            role: {"ok": sum(1 for r in by.values() if r.status == "ok"),
                   "failed": sum(1 for r in by.values() if r.status != "ok"),
                   "truncated": sum(1 for r in by.values() if r.finish_reason == "length")}
            for role, by in responses.items()
        }
        skipped[lang] = pairs.build_pairs(lang, rows, responses)[1]
    spend_by_stage: dict[str, float] = defaultdict(float)
    for row in _jsonl(root / "spend.jsonl"):
        spend_by_stage[row["stage"]] += row["cost_usd"]
    tier_rows = {name: _jsonl(root / name) for name in ("tiers.jsonl", "tiers.llama3b.jsonl")}
    return {
        "prompts": {lang: {t: sum(1 for r in rows if r.task_type == t) for t in sorted({r.task_type for r in rows})}
                    for lang, rows in prompts.items()},
        "translation": {"translator": translate.TRANSLATOR,
                        "rejected": sum(1 for t in translations.values() if t.status != "ok"),
                        "review": review.error_rate(root / "translation_review.jsonl")},
        "capture": capture_stats,
        "pairs_skipped": skipped,
        "validation": json.loads((root / "validation.json").read_text()) if (root / "validation.json").exists() else None,
        "tiers": {name: {"distribution": tier_distribution(rows),
                         "coverage": sum(1 for r in rows if r["tier"]) / len(rows) if rows else 0.0}
                  for name, rows in tier_rows.items()},
        "spend_usd": {"by_stage": dict(spend_by_stage), "total": sum(spend_by_stage.values())},
    }


def _fmt(value: float | None) -> str:
    return "—" if value is None else f"{value:.3f}"


def render_markdown(s: dict) -> str:
    out = ["# Ground truth — fase 2", "", "## Corpus", "", "| lang | " + " | ".join(sorted(s["prompts"]["es"])) + " |",
           "|---|" + "---|" * len(s["prompts"]["es"])]
    for lang, counts in s["prompts"].items():
        out.append(f"| {lang} | " + " | ".join(str(counts.get(t, 0)) for t in sorted(s["prompts"]["es"])) + " |")
    t = s["translation"]
    out += ["", f"Translator `{t['translator']}`: {t['rejected']} rejected by the number/code check; "
                f"human review {t['review']['wrong']}/{t['review']['reviewed']} wrong.", "",
            "## Capture", "", "| lang | role | ok | failed | truncated |", "|---|---|---|---|---|"]
    for lang, roles in s["capture"].items():
        for role, c in roles.items():
            out.append(f"| {lang} | {role} | {c['ok']} | {c['failed']} | {c['truncated']} |")
    out += ["", f"Pairs skipped: {s['pairs_skipped']}", "", "## Judges", ""]
    v = s["validation"]
    if v:
        sel = v["rule_selection"]
        out += [f"Rule selection on {sel['compared']} EN pilot pairs graded by `{sel['rater']}`:", "",
                "| rule | kappa |", "|---|---|"]
        out += [f"| {r} | {_fmt(k)} |" for r, k in sel["kappas"].items()]
        out += ["", f"**Chosen: `{sel['chosen']}`.**", ""]
        h = v["holdout_es"]
        if h["status"] == "pending":
            out.append("**Spanish hold-out: PENDING** (no human labels yet).")
        else:
            out.append(f"Spanish hold-out ({h['compared']} pairs, {h['status']}): kappa {h['kappa']:.3f} "
                       f"[{h['ci95'][0]:.3f}, {h['ci95'][1]:.3f}]" + (" — **judge-limited**" if h["judge_limited"] else ""))
        out += ["", "Position flip rate: " + ", ".join(f"`{m}` {r:.1%}" for m, r in v["position_flip_rate"].items()),
                f"Inter-judge kappa: {v['inter_judge_kappa']:.3f}", ""]
    out += ["## Tiers", ""]
    for name, tier in s["tiers"].items():
        out += [f"### {name} (coverage {tier['coverage']:.1%})", "", "| lang | task | local | economy | frontier | unlabelled |",
                "|---|---|---|---|---|---|"]
        for lang, tasks in tier["distribution"].items():
            for task, c in sorted(tasks.items()):
                out.append(f"| {lang} | {task} | {c['local']} | {c['economy']} | {c['frontier']} | {c['unlabelled']} |")
        out.append("")
    out += ["## Spend", "", f"Total USD {s['spend_usd']['total']:.2f}: " +
            ", ".join(f"{k} {v:.2f}" for k, v in s["spend_usd"]["by_stage"].items()), ""]
    return "\n".join(out)


def thesis_corpus(s: dict) -> str:
    srcs = "; ".join(f"{src.name} ({src.license})" for src in sources.SOURCES.values())
    es = s["prompts"]["es"]
    en_total = sum(s["prompts"]["en"].values())
    rv = s["translation"]["review"]
    return (
        f"El corpus combina tres conjuntos públicos: {srcs}. Se muestrearon {sum(es.values())} prompts "
        f"estratificados por tarea ({', '.join(f'{t} {n}' for t, n in es.items())}) con semilla fija, "
        f"y un subconjunto pareado de {en_total} en inglés. La traducción al español la hizo "
        f"`{s['translation']['translator']}`, de una familia ajena a candidatos y jueces; "
        f"{s['translation']['rejected']} traducciones fueron rechazadas por el control mecánico de números y código "
        f"y reemplazadas desde la reserva del mismo estrato. Una revisión humana de {rv['reviewed']} traducciones "
        f"encontró {rv['wrong']} infieles ({rv['rate']:.0%})."
    )


def thesis_judges(s: dict) -> str:
    v = s["validation"]
    if not v:
        return "> PENDIENTE: validación de jueces."
    sel, h = v["rule_selection"], v["holdout_es"]
    kappas = ", ".join(f"{r.split('_')[0]} {_fmt(k)}" for r, k in sel["kappas"].items())
    text = (
        f"Cada par candidato–referencia recibe cuatro notas (dos jueces, dos posiciones). Sobre los "
        f"{sel['compared']} pares en inglés etiquetados por un lector humano, el kappa binario de las reglas "
        f"pre-registradas fue {kappas}; se eligió {sel['chosen'].split('_')[0]}. "
    )
    if h["status"] == "pending":
        text += "La validación sobre el hold-out en español está pendiente."
    else:
        text += (f"Sobre el hold-out en español ({h['compared']} pares, sorteados antes de correr los jueces) "
                 f"la regla elegida obtuvo kappa {h['kappa']:.2f} (IC 95 % {h['ci95'][0]:.2f}–{h['ci95'][1]:.2f}).")
        if h["judge_limited"]:
            text += " Al quedar por debajo de 0.4, el ground truth se declara limitado por los jueces."
    flips = ", ".join(f"{m.split('/')[-1]} {r:.0%}" for m, r in v["position_flip_rate"].items())
    return text + f" Tasa de cambio de veredicto al invertir posiciones: {flips}."


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=cli.DEFAULT_ROOT)
    root = parser.parse_args().root
    summary = summarise(root)
    (root / "report.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (root / "report.md").write_text(render_markdown(summary), encoding="utf-8")
    text = THESIS.read_text(encoding="utf-8")
    text = replace_block(text, "corpus-fase2", thesis_corpus(summary))
    text = replace_block(text, "judges-fase2", thesis_judges(summary))
    THESIS.write_text(text, encoding="utf-8")
    print(f"report → {root / 'report.md'}; thesis blocks updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4:** In `06-evaluacion.md` replace `> PENDIENTE (fase 2): origen público, estratificación por tarea, traducción, tamaño.` with
```
<!-- GEN:corpus-fase2 -->
> PENDIENTE (fase 2): origen público, estratificación por tarea, traducción, tamaño.
<!-- /GEN:corpus-fase2 -->
```
and `> PENDIENTE (fase 2): ensamble, rúbrica "lector satisfecho", 50 pares en español.` with the same wrapping under `judges-fase2`.

- [ ] **Step 5:** PASS, `make lint` green. **Step 6:** commit `feat(ground-truth): report and generated thesis paragraphs`.

---

### Task 10: Run the pipeline

Prereq: `ollama pull qwen2.5:7b`. Run long stages in the background with `caffeinate -i`.

- [ ] `python -m scripts.ground_truth.sample` → 1100 rows; commit `prompts.en.jsonl`, `NOTICE`, `provenance.json`.
- [ ] Smoke: one real call per paid model (translator, haiku, gpt-4.1, both judges) through a throwaway script in the scratchpad; confirm `usage.cost` is present and gemini's `completion_tokens` stays small with `reasoning.max_tokens=0`. If gemini still thinks, switch `JUDGE_EXTRA` to `{"reasoning": {"enabled": False}}` and re-check.
- [ ] `python -m scripts.ground_truth.translate` → 1000 ES; commit.
- [ ] `python -m scripts.ground_truth.capture --dry-run`; confirm estimate < USD 15. Then `capture --roles haiku,gpt41`, then `capture --roles qwen7b,llama3b` (hours; background). Commit responses.
- [ ] `python -m scripts.ground_truth.holdout`; commit `holdout/` (pairs + raters.json). The pre-registration is already committed (Task 6).
- [ ] `python -m scripts.ground_truth.judge --set pilot`, then `--set corpus`; commit judgements.
- [ ] `validate`, `tiers`, `report`; commit. Check `tiers.jsonl` coverage ≥ 95 % and spend ≤ USD 35.
- [ ] Human steps for Joaquín (hand off, not blocking the PR): `python -m scripts.ground_truth.review` (~15 min) and `python -m scripts.metric_validation.label --rater human-es-1 --pairs benchmarks/ground-truth/v1/holdout/pairs.jsonl --labels benchmarks/ground-truth/v1/holdout/labels` (~1 h); afterwards re-run `validate` + `report`.

### Task 11: Ship

- [ ] `make lint`, `darwin-throttle make test`, `darwin-throttle make console-test` green.
- [ ] Push branch, open PR "Fase 2: bilingual corpus and judged ground truth", merge (squash) after CI green.
- [ ] Update memory `tesis-fase1-completada` sibling: new memory for fase 2 status and pending human steps.
