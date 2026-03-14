from typing import Literal

from nebula.core.config import Settings
from nebula.models.openai import ChatCompletionRequest

RouteTarget = Literal["local", "premium"]


class RouterService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def choose_target(self, prompt: str, request: ChatCompletionRequest) -> RouteTarget:
        requested_model = request.model != self.settings.default_model
        if requested_model and request.model == self.settings.premium_model:
            return "premium"

        complexity_hints = ("analyze", "reason", "contract", "debug", "architecture", "design")
        contains_complexity_hint = any(hint in prompt.lower() for hint in complexity_hints)
        if len(prompt) < self.settings.router_complexity_chars and not contains_complexity_hint:
            return "local"
        return "premium"

    def resolve_model(self, target: RouteTarget) -> str:
        if target == "local":
            return self.settings.local_model
        return self.settings.premium_model
