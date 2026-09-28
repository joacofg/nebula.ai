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
