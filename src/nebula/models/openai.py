from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str | list[dict[str, Any]]
    name: str | None = None


class ChatCompletionRequest(BaseModel):
    model: str = Field(default="nebula-auto")
    messages: list[ChatMessage] = Field(min_length=1)
    temperature: float | None = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float | None = Field(default=1.0, ge=0.0, le=1.0)
    n: int | None = Field(default=1, ge=1, le=8)
    stream: bool = False
    stop: str | list[str] | None = None
    max_tokens: int | None = Field(default=None, ge=1)
    presence_penalty: float | None = Field(default=0.0, ge=-2.0, le=2.0)
    frequency_penalty: float | None = Field(default=0.0, ge=-2.0, le=2.0)
    user: str | None = None
    metadata: dict[str, Any] | None = None


class ChatCompletionResponseMessage(BaseModel):
    role: Literal["assistant"] = "assistant"
    content: str


class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatCompletionResponseMessage
    finish_reason: Literal["stop", "length", "content_filter", "tool_calls"] = "stop"


class ChatCompletionUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionResponse(BaseModel):
    id: str
    object: Literal["chat.completion"] = "chat.completion"
    created: int
    model: str
    choices: list[ChatCompletionChoice]
    usage: ChatCompletionUsage
    system_fingerprint: str | None = None


class ChatCompletionStreamDelta(BaseModel):
    role: Literal["assistant"] | None = None
    content: str | None = None


class ChatCompletionChunkChoice(BaseModel):
    index: int
    delta: ChatCompletionStreamDelta
    finish_reason: Literal["stop", "length", "content_filter", "tool_calls"] | None = None


class ChatCompletionChunk(BaseModel):
    id: str
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int
    model: str
    choices: list[ChatCompletionChunkChoice]
    system_fingerprint: str | None = None


class EmbeddingsRequest(BaseModel):
    model: str = Field(min_length=1)
    input: str | list[str]

    @field_validator("model")
    @classmethod
    def validate_model(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("model must not be blank")
        return value

    @field_validator("input")
    @classmethod
    def validate_input(cls, value: str | list[str]) -> str | list[str]:
        if isinstance(value, str):
            if not value.strip():
                raise ValueError("input must not be blank")
            return value

        if not value:
            raise ValueError("input list must not be empty")

        normalized: list[str] = []
        for item in value:
            if isinstance(item, list):
                raise ValueError("input must be a flat list of strings")
            if not isinstance(item, str):
                raise ValueError("input list must contain only strings")
            if not item.strip():
                raise ValueError("input list entries must not be blank")
            normalized.append(item)
        return normalized


class EmbeddingData(BaseModel):
    object: Literal["embedding"] = "embedding"
    index: int
    embedding: list[float]


class EmbeddingsUsage(BaseModel):
    prompt_tokens: int = 0
    total_tokens: int = 0


class EmbeddingsResponse(BaseModel):
    object: Literal["list"] = "list"
    data: list[EmbeddingData]
    model: str
    usage: EmbeddingsUsage = Field(default_factory=EmbeddingsUsage)
