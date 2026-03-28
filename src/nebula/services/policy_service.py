from __future__ import annotations

from dataclasses import dataclass
from math import ceil

from fastapi import HTTPException, status

from nebula.benchmarking.pricing import PricingCatalog
from nebula.core.config import Settings
from nebula.models.governance import RoutingMode
from nebula.models.openai import ChatCompletionRequest
from nebula.providers.base import CompletionUsage
from nebula.services.auth_service import AuthenticatedTenantContext
from nebula.services.governance_store import GovernanceStore
from nebula.services.router_service import ReplayRouteContext, RouteDecision, RouterService


@dataclass(slots=True, frozen=True)
class PolicyEvaluation:
    route_decision: RouteDecision
    policy_mode: RoutingMode
    cache_enabled: bool
    fallback_enabled: bool
    policy_outcome: str
    soft_budget_exceeded: bool
    projected_premium_cost: float | None
    denied: bool = False
    denial_detail: str | None = None


@dataclass(slots=True, frozen=True)
class PolicyResolution:
    route_decision: RouteDecision
    policy_mode: RoutingMode
    cache_enabled: bool
    fallback_enabled: bool
    policy_outcome: str
    soft_budget_exceeded: bool
    projected_premium_cost: float | None


class PolicyService:
    def __init__(
        self,
        settings: Settings,
        store: GovernanceStore,
        pricing: PricingCatalog,
    ) -> None:
        self.settings = settings
        self.store = store
        self.pricing = pricing

    async def resolve(
        self,
        *,
        prompt: str,
        request: ChatCompletionRequest,
        tenant_context: AuthenticatedTenantContext,
        router_service: RouterService,
    ) -> PolicyResolution:
        evaluation = await self.evaluate(
            request=request,
            tenant_context=tenant_context,
            router_service=router_service,
            prompt=prompt,
        )
        if evaluation.denied:
            assert evaluation.denial_detail is not None
            self._policy_denied(
                tenant_id=tenant_context.tenant.id,
                route_target=evaluation.route_decision.target,
                route_reason=evaluation.route_decision.reason,
                policy_mode=evaluation.policy_mode,
                detail=evaluation.denial_detail,
            )

        return PolicyResolution(
            route_decision=evaluation.route_decision,
            policy_mode=evaluation.policy_mode,
            cache_enabled=evaluation.cache_enabled,
            fallback_enabled=evaluation.fallback_enabled,
            policy_outcome=evaluation.policy_outcome,
            soft_budget_exceeded=evaluation.soft_budget_exceeded,
            projected_premium_cost=evaluation.projected_premium_cost,
        )

    async def evaluate(
        self,
        *,
        request: ChatCompletionRequest,
        tenant_context: AuthenticatedTenantContext,
        router_service: RouterService,
        prompt: str | None = None,
        replay_context: ReplayRouteContext | None = None,
    ) -> PolicyEvaluation:
        policy = tenant_context.policy
        if replay_context is not None:
            route_decision = await router_service.choose_target_for_replay(
                request,
                replay_context,
                routing_mode=policy.routing_mode_default,
                policy=policy,
            )
        else:
            route_decision = await router_service.choose_target_with_reason(
                prompt or self._serialize_request_messages(request),
                request,
                routing_mode=policy.routing_mode_default,
                policy=policy,
            )

        denial_detail = self._explicit_model_conflict_detail(
            request=request,
            route_decision=route_decision,
            routing_mode=policy.routing_mode_default,
        )

        soft_budget_exceeded = False
        if policy.soft_budget_usd is not None:
            soft_budget_exceeded = self.store.tenant_spend_total(tenant_context.tenant.id) >= policy.soft_budget_usd

        projected_premium_cost: float | None = None
        if denial_detail is None and route_decision.target == "premium":
            premium_model = self._resolve_premium_model(request)
            if policy.allowed_premium_models and premium_model not in policy.allowed_premium_models:
                denial_detail = f"Premium model '{premium_model}' is not allowed for this tenant."
            else:
                projected_premium_cost = self._estimate_request_cost(request, premium_model)
                if (
                    policy.max_premium_cost_per_request is not None
                    and projected_premium_cost is not None
                    and projected_premium_cost > policy.max_premium_cost_per_request
                ):
                    denial_detail = "Request exceeds the tenant premium spend guardrail."

        outcome_parts: list[str] = []
        if policy.routing_mode_default != "auto":
            outcome_parts.append(f"routing_mode={policy.routing_mode_default}")
        if not policy.semantic_cache_enabled:
            outcome_parts.append("cache=disabled")
        if not policy.fallback_enabled:
            outcome_parts.append("fallback=disabled")
        if soft_budget_exceeded:
            outcome_parts.append("soft_budget=exceeded")
        if denial_detail is not None:
            outcome_parts.append(f"denied={denial_detail}")
        if not outcome_parts:
            outcome_parts.append("default")

        return PolicyEvaluation(
            route_decision=route_decision,
            policy_mode=policy.routing_mode_default,
            cache_enabled=policy.semantic_cache_enabled,
            fallback_enabled=policy.fallback_enabled,
            policy_outcome=";".join(outcome_parts),
            soft_budget_exceeded=soft_budget_exceeded,
            projected_premium_cost=projected_premium_cost,
            denied=denial_detail is not None,
            denial_detail=denial_detail,
        )

    def estimate_usage(self, request: ChatCompletionRequest, response_content: str) -> CompletionUsage:
        prompt_tokens = self._estimate_text_tokens(self._serialize_request_messages(request))
        completion_tokens = self._estimate_text_tokens(response_content)
        return CompletionUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        )

    def estimate_cost(self, model: str, usage: CompletionUsage | None) -> float | None:
        return self.pricing.estimate_cost(model, usage)

    def _resolve_premium_model(self, request: ChatCompletionRequest) -> str:
        if request.model in {self.settings.default_model, self.settings.local_model}:
            return self.settings.premium_model
        return request.model

    def _estimate_request_cost(self, request: ChatCompletionRequest, model: str) -> float | None:
        prompt_tokens = self._estimate_text_tokens(self._serialize_request_messages(request))
        completion_tokens = request.max_tokens if request.max_tokens is not None else max(128, prompt_tokens)
        return self.pricing.estimate_cost(
            model,
            CompletionUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
        )

    def _explicit_model_conflict_detail(
        self,
        *,
        request: ChatCompletionRequest,
        route_decision: RouteDecision,
        routing_mode: RoutingMode,
    ) -> str | None:
        if request.model == self.settings.local_model and routing_mode == "premium_only":
            return "Tenant policy requires premium-only routing."
        if request.model not in {self.settings.default_model, self.settings.local_model} and routing_mode == "local_only":
            return "Tenant policy does not allow explicit premium routing."
        if routing_mode == "local_only" and route_decision.target == "premium":
            return "Tenant policy restricts this request to local routing only."
        return None

    def _enforce_explicit_model_constraints(
        self,
        request: ChatCompletionRequest,
        route_decision: RouteDecision,
        routing_mode: RoutingMode,
        tenant_id: str | None = None,
    ) -> None:
        detail = self._explicit_model_conflict_detail(
            request=request,
            route_decision=route_decision,
            routing_mode=routing_mode,
        )
        if detail is None:
            return
        self._policy_denied(
            tenant_id=tenant_id,
            route_target=("local" if request.model == self.settings.local_model else route_decision.target),
            route_reason=(
                "explicit_local_model"
                if request.model == self.settings.local_model and routing_mode == "premium_only"
                else "explicit_premium_model"
                if request.model not in {self.settings.default_model, self.settings.local_model}
                and routing_mode == "local_only"
                else route_decision.reason
            ),
            policy_mode=routing_mode,
            detail=detail,
        )

    def _policy_denied(
        self,
        *,
        tenant_id: str | None,
        route_target: str,
        route_reason: str,
        policy_mode: RoutingMode,
        detail: str,
    ) -> None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            headers={
                "X-Nebula-Tenant-ID": tenant_id or "",
                "X-Nebula-Route-Target": route_target,
                "X-Nebula-Route-Reason": route_reason,
                "X-Nebula-Provider": "policy",
                "X-Nebula-Cache-Hit": "false",
                "X-Nebula-Fallback-Used": "false",
                "X-Nebula-Policy-Mode": policy_mode,
                "X-Nebula-Policy-Outcome": detail,
            },
        )

    def _serialize_request_messages(self, request: ChatCompletionRequest) -> str:
        parts: list[str] = []
        for message in request.messages:
            if isinstance(message.content, str):
                parts.append(message.content)
            else:
                parts.append(str(message.content))
        return "\n".join(parts)

    def _estimate_text_tokens(self, content: str) -> int:
        return max(1, ceil(len(content) / 4))
