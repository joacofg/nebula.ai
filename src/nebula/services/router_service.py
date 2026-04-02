from dataclasses import dataclass, field
from math import ceil
from typing import Any, Literal

from pydantic import BaseModel

from nebula.core.config import Settings
from nebula.models.governance import RoutingMode, TenantPolicy
from nebula.models.openai import ChatCompletionRequest

RouteTarget = Literal["local", "premium"]
ComplexityTier = Literal["low", "medium", "high"]
RouteMode = Literal["calibrated", "heuristic_override", "degraded"]


@dataclass(slots=True, frozen=True)
class RouteDecision:
    target: RouteTarget
    reason: str
    signals: dict[str, Any] = field(default_factory=dict)
    score: float = 0.0


@dataclass(slots=True, frozen=True)
class CalibratedScoreBreakdown:
    token_count: int
    complexity_tier: ComplexityTier
    keyword_match: bool
    budget_proximity: float | None
    model_constraint: bool
    route_mode: RouteMode
    replay: bool
    token_score: float
    keyword_bonus: float
    policy_bonus: float
    budget_penalty: float
    total_score: float


def _estimate_token_count(text: str) -> int:
    """Chars/4 heuristic — same formula as PolicyService._estimate_text_tokens()."""
    return max(1, ceil(len(text) / 4))


class ReplayRouteContext(BaseModel):
    token_count: int | None = None
    keyword_match: bool | None = None
    complexity_tier: Literal["low", "medium", "high"] | None = None


class RouterService:
    COMPLEXITY_HINTS = ("analyze", "reason", "contract", "debug", "architecture", "design")

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
        explicit_override = self._explicit_override_decision(request=request, routing_mode=routing_mode)
        if explicit_override is not None:
            return explicit_override

        breakdown = self._build_replay_breakdown(request=request, replay_context=replay_context, policy=policy)
        return self._decision_from_breakdown(breakdown)

    async def choose_target_with_reason(
        self,
        prompt: str,
        request: ChatCompletionRequest,
        routing_mode: RoutingMode = "auto",
        policy: TenantPolicy | None = None,
    ) -> RouteDecision:
        explicit_override = self._explicit_override_decision(request=request, routing_mode=routing_mode)
        if explicit_override is not None:
            return explicit_override

        breakdown = self._build_live_breakdown(prompt=prompt, policy=policy)
        return self._decision_from_breakdown(breakdown)

    def resolve_model(self, target: RouteTarget) -> str:
        if target == "local":
            return self.settings.local_model
        return self.settings.premium_model

    def _explicit_override_decision(
        self,
        *,
        request: ChatCompletionRequest,
        routing_mode: RoutingMode,
    ) -> RouteDecision | None:
        requested_model = request.model != self.settings.default_model
        if requested_model and request.model == self.settings.local_model:
            return RouteDecision(target="local", reason="explicit_local_model")
        if requested_model:
            return RouteDecision(target="premium", reason="explicit_premium_model")
        if routing_mode == "local_only":
            return RouteDecision(target="local", reason="policy_local_only")
        if routing_mode == "premium_only":
            return RouteDecision(target="premium", reason="policy_premium_only")
        return None

    def _build_live_breakdown(
        self,
        *,
        prompt: str,
        policy: TenantPolicy | None,
    ) -> CalibratedScoreBreakdown:
        token_count = _estimate_token_count(prompt)
        complexity_tier = self._complexity_tier_from_token_count(token_count)
        keyword_match = self._keyword_match(prompt)
        return self._build_breakdown(
            token_count=token_count,
            complexity_tier=complexity_tier,
            keyword_match=keyword_match,
            policy=policy,
            replay=False,
            route_mode="calibrated",
        )

    def _build_replay_breakdown(
        self,
        *,
        request: ChatCompletionRequest,
        replay_context: ReplayRouteContext,
        policy: TenantPolicy | None,
    ) -> CalibratedScoreBreakdown:
        prompt = self._serialize_request_messages(request)
        token_count = replay_context.token_count or _estimate_token_count(prompt)

        degraded = False
        if replay_context.complexity_tier is not None:
            complexity_tier = replay_context.complexity_tier
        else:
            complexity_tier = self._complexity_tier_from_token_count(token_count)
            degraded = True

        if replay_context.keyword_match is not None:
            keyword_match = replay_context.keyword_match
        else:
            keyword_match = self._keyword_match(prompt)
            degraded = True

        return self._build_breakdown(
            token_count=token_count,
            complexity_tier=complexity_tier,
            keyword_match=keyword_match,
            policy=policy,
            replay=True,
            route_mode="degraded" if degraded else "calibrated",
        )

    def _build_breakdown(
        self,
        *,
        token_count: int,
        complexity_tier: ComplexityTier,
        keyword_match: bool,
        policy: TenantPolicy | None,
        replay: bool,
        route_mode: RouteMode,
    ) -> CalibratedScoreBreakdown:
        budget_proximity: float | None = None
        model_constraint = bool(policy is not None and policy.allowed_premium_models)

        token_score = min(token_count / 500, 1.0)
        keyword_bonus = 0.2 if keyword_match else 0.0
        policy_bonus = 0.1 if model_constraint else 0.0
        budget_penalty = 0.0
        total_score = round(min(max(token_score + keyword_bonus + policy_bonus - budget_penalty, 0.0), 1.0), 4)

        return CalibratedScoreBreakdown(
            token_count=token_count,
            complexity_tier=complexity_tier,
            keyword_match=keyword_match,
            budget_proximity=budget_proximity,
            model_constraint=model_constraint,
            route_mode=route_mode,
            replay=replay,
            token_score=round(token_score, 4),
            keyword_bonus=round(keyword_bonus, 4),
            policy_bonus=round(policy_bonus, 4),
            budget_penalty=round(budget_penalty, 4),
            total_score=total_score,
        )

    def _decision_from_breakdown(self, breakdown: CalibratedScoreBreakdown) -> RouteDecision:
        signals = self._signals_from_breakdown(breakdown)
        if breakdown.complexity_tier == "low" and not breakdown.keyword_match:
            return RouteDecision(
                target="local",
                reason="token_complexity",
                signals=signals,
                score=breakdown.total_score,
            )
        return RouteDecision(
            target="premium",
            reason="token_complexity",
            signals=signals,
            score=breakdown.total_score,
        )

    def _signals_from_breakdown(self, breakdown: CalibratedScoreBreakdown) -> dict[str, Any]:
        return {
            "token_count": breakdown.token_count,
            "complexity_tier": breakdown.complexity_tier,
            "budget_proximity": breakdown.budget_proximity,
            "model_constraint": breakdown.model_constraint,
            "keyword_match": breakdown.keyword_match,
            "route_mode": breakdown.route_mode,
            "calibrated_routing": breakdown.route_mode == "calibrated",
            "degraded_routing": breakdown.route_mode == "degraded",
            "score_components": {
                "token_score": breakdown.token_score,
                "keyword_bonus": breakdown.keyword_bonus,
                "policy_bonus": breakdown.policy_bonus,
                "budget_penalty": breakdown.budget_penalty,
                "total_score": breakdown.total_score,
            },
            "replay": breakdown.replay,
        }

    def _complexity_tier_from_token_count(self, token_count: int) -> ComplexityTier:
        if token_count < 500:
            return "low"
        if token_count <= 2000:
            return "medium"
        return "high"

    def _keyword_match(self, prompt: str) -> bool:
        lowered = prompt.lower()
        return any(hint in lowered for hint in self.COMPLEXITY_HINTS)

    def _serialize_request_messages(self, request: ChatCompletionRequest) -> str:
        parts: list[str] = []
        for message in request.messages:
            if isinstance(message.content, str):
                parts.append(message.content)
            else:
                parts.append(str(message.content))
        return "\n".join(parts)
