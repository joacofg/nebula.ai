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
