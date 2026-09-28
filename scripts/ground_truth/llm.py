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
