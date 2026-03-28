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
from nebula.services.router_service import RouteDecision, RouterService


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
        policy = tenant_context.policy
        route_decision = await router_service.choose_target_with_reason(
            prompt,
            request,
            routing_mode=policy.routing_mode_default,
            policy=policy,
        )
        self._enforce_explicit_model_constraints(
            request,
            route_decision,
            policy.routing_mode_default,
            tenant_context.tenant.id,
        )

        soft_budget_exceeded = False
        if policy.soft_budget_usd is not None:
            soft_budget_exceeded = self.store.tenant_spend_total(tenant_context.tenant.id) >= policy.soft_budget_usd

        projected_premium_cost: float | None = None
        if route_decision.target == "premium":
            premium_model = self._resolve_premium_model(request)
            if policy.allowed_premium_models and premium_model not in policy.allowed_premium_models:
                self._policy_denied(
                    tenant_id=tenant_context.tenant.id,
                    route_target=route_decision.target,
                    route_reason=route_decision.reason,
                    policy_mode=policy.routing_mode_default,
                    detail=f"Premium model '{premium_model}' is not allowed for this tenant.",
                )
            projected_premium_cost = self._estimate_request_cost(request, premium_model)
            if (
                policy.max_premium_cost_per_request is not None
                and projected_premium_cost is not None
                and projected_premium_cost > policy.max_premium_cost_per_request
            ):
                self._policy_denied(
                    tenant_id=tenant_context.tenant.id,
                    route_target=route_decision.target,
                    route_reason=route_decision.reason,
                    policy_mode=policy.routing_mode_default,
                    detail="Request exceeds the tenant premium spend guardrail.",
                )

        outcome_parts: list[str] = []
        if policy.routing_mode_default != "auto":
            outcome_parts.append(f"routing_mode={policy.routing_mode_default}")
        if not policy.semantic_cache_enabled:
            outcome_parts.append("cache=disabled")
        if not policy.fallback_enabled:
            outcome_parts.append("fallback=disabled")
        if soft_budget_exceeded:
            outcome_parts.append("soft_budget=exceeded")
        if not outcome_parts:
            outcome_parts.append("default")

        return PolicyResolution(
            route_decision=route_decision,
            policy_mode=policy.routing_mode_default,
            cache_enabled=policy.semantic_cache_enabled,
            fallback_enabled=policy.fallback_enabled,
            policy_outcome=";".join(outcome_parts),
            soft_budget_exceeded=soft_budget_exceeded,
            projected_premium_cost=projected_premium_cost,
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

    def _enforce_explicit_model_constraints(
        self,
        request: ChatCompletionRequest,
        route_decision: RouteDecision,
        routing_mode: RoutingMode,
        tenant_id: str | None = None,
    ) -> None:
        if request.model == self.settings.local_model and routing_mode == "premium_only":
            self._policy_denied(
                tenant_id=tenant_id,
                route_target="local",
                route_reason="explicit_local_model",
                policy_mode=routing_mode,
                detail="Tenant policy requires premium-only routing.",
            )
        if request.model not in {self.settings.default_model, self.settings.local_model} and routing_mode == "local_only":
            self._policy_denied(
                tenant_id=tenant_id,
                route_target="premium",
                route_reason="explicit_premium_model",
                policy_mode=routing_mode,
                detail="Tenant policy does not allow explicit premium routing.",
            )
        if routing_mode == "local_only" and route_decision.target == "premium":
            self._policy_denied(
                tenant_id=tenant_id,
                route_target=route_decision.target,
                route_reason=route_decision.reason,
                policy_mode=routing_mode,
                detail="Tenant policy restricts this request to local routing only.",
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
