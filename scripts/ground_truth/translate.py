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
CONCURRENCY = 4
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
                try:
                    completion = await llm.with_retries(chat, translation_prompt(row.prompt))
                except llm.CallFailed:
                    return  # nothing recorded: the next run retries it
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
            translations = await translate_all(
                batch, chat=chat, cache_path=cache, ledger=ledger, concurrency=CONCURRENCY
            )
            if all(r.prompt_id in translations for r in _needed(rows_en, translations)):
                break
            failed = sum(1 for r in batch if r.prompt_id not in translations)
            if failed:
                raise RuntimeError(f"{failed} translation calls failed; re-run to resume.")
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
