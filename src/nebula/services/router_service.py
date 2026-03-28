from dataclasses import dataclass, field
from math import ceil
from typing import Any, Literal

from pydantic import BaseModel

from nebula.core.config import Settings
from nebula.models.governance import RoutingMode, TenantPolicy
from nebula.models.openai import ChatCompletionRequest

RouteTarget = Literal["local", "premium"]


@dataclass(slots=True, frozen=True)
class RouteDecision:
    target: RouteTarget
    reason: str
    signals: dict[str, Any] = field(default_factory=dict)
    score: float = 0.0


def _estimate_token_count(text: str) -> int:
    """Chars/4 heuristic — same formula as PolicyService._estimate_text_tokens()."""
    return max(1, ceil(len(text) / 4))


class ReplayRouteContext(BaseModel):
    token_count: int | None = None
    keyword_match: bool | None = None
    complexity_tier: Literal["low", "medium", "high"] | None = None


class RouterService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def choose_target(self, prompt: str, request: ChatCompletionRequest) -> RouteTarget:
        return (await self.choose_target_with_reason(prompt, request)).target

    async def choose_target_for_replay(
        self,
        request: ChatCompletionRequest,
        replay_context: ReplayRouteContext,
        routing_mode: RoutingMode = "auto",
        policy: TenantPolicy | None = None,
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

        token_count = replay_context.token_count or _estimate_token_count(self._serialize_request_messages(request))
        if replay_context.complexity_tier is not None:
            complexity_tier = replay_context.complexity_tier
        elif token_count < 500:
            complexity_tier = "low"
        elif token_count <= 2000:
            complexity_tier = "medium"
        else:
            complexity_tier = "high"

        budget_proximity: float | None = None
        model_constraint = bool(policy is not None and policy.allowed_premium_models)
        keyword_match = bool(replay_context.keyword_match)

        signals: dict[str, Any] = {
            "token_count": token_count,
            "complexity_tier": complexity_tier,
            "budget_proximity": budget_proximity,
            "model_constraint": model_constraint,
            "keyword_match": keyword_match,
            "replay": True,
        }

        token_score = min(token_count / 500, 1.0)
        policy_bonus = 0.1 if model_constraint else 0.0
        score = round(min(token_score + policy_bonus, 1.0), 4)

        if complexity_tier == "low" and not keyword_match:
            return RouteDecision(
                target="local",
                reason="token_complexity",
                signals=signals,
                score=score,
            )
        return RouteDecision(
            target="premium",
            reason="token_complexity",
            signals=signals,
            score=score,
        )

    async def choose_target_with_reason(
        self,
        prompt: str,
        request: ChatCompletionRequest,
        routing_mode: RoutingMode = "auto",
        policy: TenantPolicy | None = None,
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

        token_count = _estimate_token_count(prompt)
        if token_count < 500:
            complexity_tier = "low"
        elif token_count <= 2000:
            complexity_tier = "medium"
        else:
            complexity_tier = "high"

        budget_proximity: float | None = None
        if policy is not None and policy.soft_budget_usd and policy.soft_budget_usd > 0:
            pass

        model_constraint = bool(policy is not None and policy.allowed_premium_models)

        signals: dict[str, Any] = {
            "token_count": token_count,
            "complexity_tier": complexity_tier,
            "budget_proximity": budget_proximity,
            "model_constraint": model_constraint,
        }

        token_score = min(token_count / 500, 1.0)
        policy_bonus = 0.1 if model_constraint else 0.0
        score = round(min(token_score + policy_bonus, 1.0), 4)

        complexity_hints = ("analyze", "reason", "contract", "debug", "architecture", "design")
        keyword_match = any(hint in prompt.lower() for hint in complexity_hints)
        signals["keyword_match"] = keyword_match

        if complexity_tier == "low" and not keyword_match:
            return RouteDecision(
                target="local",
                reason="token_complexity",
                signals=signals,
                score=score,
            )
        return RouteDecision(
            target="premium",
            reason="token_complexity",
            signals=signals,
            score=score,
        )

    def resolve_model(self, target: RouteTarget) -> str:
        if target == "local":
            return self.settings.local_model
        return self.settings.premium_model

    def _serialize_request_messages(self, request: ChatCompletionRequest) -> str:
        parts: list[str] = []
        for message in request.messages:
            if isinstance(message.content, str):
                parts.append(message.content)
            else:
                parts.append(str(message.content))
        return "\n".join(parts)
