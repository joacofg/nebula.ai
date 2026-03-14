from dataclasses import dataclass
from typing import Literal

from nebula.core.config import Settings
from nebula.models.governance import RoutingMode
from nebula.models.openai import ChatCompletionRequest

RouteTarget = Literal["local", "premium"]


@dataclass(slots=True, frozen=True)
class RouteDecision:
    target: RouteTarget
    reason: str


class RouterService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def choose_target(self, prompt: str, request: ChatCompletionRequest) -> RouteTarget:
        return (await self.choose_target_with_reason(prompt, request)).target

    async def choose_target_with_reason(
        self,
        prompt: str,
        request: ChatCompletionRequest,
        routing_mode: RoutingMode = "auto",
    ) -> RouteDecision:
        requested_model = request.model != self.settings.default_model
        if requested_model and request.model == self.settings.local_model:
            return RouteDecision(target="local", reason="explicit_local_model")
        if requested_model:
            return RouteDecision(target="premium", reason="explicit_premium_model")
        if routing_mode == "local_only":
            return RouteDecision(target="local", reason="policy_local_only")
        if routing_mode == "premium_only":
            return RouteDecision(target="premium", reason="policy_premium_only")

        complexity_hints = ("analyze", "reason", "contract", "debug", "architecture", "design")
        contains_complexity_hint = any(hint in prompt.lower() for hint in complexity_hints)
        if len(prompt) < self.settings.router_complexity_chars and not contains_complexity_hint:
            return RouteDecision(target="local", reason="simple_prompt")
        if contains_complexity_hint:
            return RouteDecision(target="premium", reason="complexity_hint")
        return RouteDecision(target="premium", reason="prompt_length")

    def resolve_model(self, target: RouteTarget) -> str:
        if target == "local":
            return self.settings.local_model
        return self.settings.premium_model
