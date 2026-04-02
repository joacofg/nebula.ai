from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from nebula.models.governance import (
    CacheControlSummary,
    CacheInsight,
    RecommendationBundle,
    RecommendationCard,
    RecommendationEvidence,
    TenantPolicy,
    UsageLedgerRecord,
)
from nebula.services.auth_service import AuthenticatedTenantContext
from nebula.services.governance_store import GovernanceStore
from nebula.services.policy_simulation_service import PolicySimulationService
from nebula.services.semantic_cache_service import SemanticCacheService

_MAX_RECOMMENDATIONS = 3
_LEDGER_WINDOW_LIMIT = 200
_CACHE_HIT_RECOMMENDATION_THRESHOLD = 0.20
_PREMIUM_COST_RECOMMENDATION_THRESHOLD_USD = 0.01
_PREMIUM_SHARE_RECOMMENDATION_THRESHOLD = 0.50


@dataclass(slots=True, frozen=True)
class RecommendationMetrics:
    total_requests: int
    premium_requests: int
    cache_hits: int
    policy_denials: int
    premium_cost_usd: float
    avoided_premium_cost_usd: float
    avg_latency_ms: float | None
    last_request_at: datetime | None

    @property
    def premium_share(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.premium_requests / self.total_requests

    @property
    def cache_hit_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.cache_hits / self.total_requests


class RecommendationService:
    """Derive bounded operator guidance from persisted governance and cache signals.

    Recommendations are deterministic, tenant-scoped, and read-only. The service never writes
    policies, usage rows, or cache entries. Guidance is grounded exclusively in policy state,
    ledger history, and coarse semantic-cache runtime health.
    """

    def __init__(
        self,
        *,
        governance_store: GovernanceStore,
        policy_simulation_service: PolicySimulationService,
        semantic_cache_service: SemanticCacheService,
    ) -> None:
        self.governance_store = governance_store
        self.policy_simulation_service = policy_simulation_service
        self.semantic_cache_service = semantic_cache_service

    async def build_summary(
        self,
        *,
        tenant_context: AuthenticatedTenantContext,
    ) -> RecommendationBundle:
        policy = tenant_context.policy
        ledger = self.governance_store.list_usage_records(
            tenant_id=tenant_context.tenant.id,
            limit=_LEDGER_WINDOW_LIMIT,
        )
        metrics = self._compute_metrics(ledger)
        cache_summary = await self._build_cache_summary(policy=policy, metrics=metrics)
        calibration_summary = self.governance_store.summarize_calibration_evidence(
            tenant_id=tenant_context.tenant.id,
        )
        recommendations = self._build_recommendations(policy=policy, metrics=metrics, cache_summary=cache_summary)
        return RecommendationBundle(
            tenant_id=tenant_context.tenant.id,
            generated_at=datetime.now(UTC),
            window_requests_evaluated=metrics.total_requests,
            calibration_summary=calibration_summary,
            recommendations=recommendations[:_MAX_RECOMMENDATIONS],
            cache_summary=cache_summary,
        )

    def _compute_metrics(self, ledger: list[UsageLedgerRecord]) -> RecommendationMetrics:
        total_requests = len(ledger)
        premium_requests = sum(1 for row in ledger if row.final_route_target == "premium")
        cache_hits = sum(1 for row in ledger if row.cache_hit)
        policy_denials = sum(1 for row in ledger if row.terminal_status == "policy_denied")
        premium_cost_usd = round(
            sum((row.estimated_cost or 0.0) for row in ledger if row.final_route_target == "premium"),
            6,
        )
        avoided_premium_cost_usd = round(
            sum(
                (row.estimated_cost or 0.0)
                for row in ledger
                if row.cache_hit and (row.estimated_cost or 0.0) > 0
            ),
            6,
        )
        latency_values = [row.latency_ms for row in ledger if row.latency_ms is not None]
        avg_latency_ms = round(sum(latency_values) / len(latency_values), 2) if latency_values else None
        last_request_at = max((row.timestamp for row in ledger), default=None)
        return RecommendationMetrics(
            total_requests=total_requests,
            premium_requests=premium_requests,
            cache_hits=cache_hits,
            policy_denials=policy_denials,
            premium_cost_usd=premium_cost_usd,
            avoided_premium_cost_usd=avoided_premium_cost_usd,
            avg_latency_ms=avg_latency_ms,
            last_request_at=last_request_at,
        )

    async def _build_cache_summary(
        self,
        *,
        policy: TenantPolicy,
        metrics: RecommendationMetrics,
    ) -> CacheControlSummary:
        runtime_health = await self.semantic_cache_service.health_status()
        runtime_status = str(runtime_health.get("status", "unknown"))
        runtime_detail = str(runtime_health.get("detail", "Unavailable"))
        enabled = bool(policy.semantic_cache_enabled)
        insight_level = "info"
        if runtime_status == "degraded":
            insight_level = "warning"
        if not enabled:
            insight_level = "notice"

        cache_insights: list[CacheInsight] = [
            CacheInsight(
                code=(
                    "cache_runtime_degraded"
                    if runtime_status == "degraded"
                    else "cache_policy_disabled"
                    if not enabled
                    else "cache_runtime_ready"
                ),
                title=(
                    "Semantic cache degraded"
                    if runtime_status == "degraded"
                    else "Semantic cache disabled"
                    if not enabled
                    else "Semantic cache healthy"
                ),
                level=insight_level,
                summary=runtime_detail,
                evidence=[
                    RecommendationEvidence(
                        label="runtime_status",
                        value=runtime_status,
                    ),
                    RecommendationEvidence(
                        label="cache_enabled",
                        value=str(enabled).lower(),
                    ),
                ],
            )
        ]

        if metrics.total_requests > 0:
            cache_insights.append(
                CacheInsight(
                    code="cache_effectiveness_window",
                    title="Recent cache effectiveness",
                    level="info",
                    summary=(
                        f"Recent cache hit rate is {metrics.cache_hit_rate:.0%} across "
                        f"{metrics.total_requests} ledger-backed requests."
                    ),
                    evidence=[
                        RecommendationEvidence(label="cache_hits", value=str(metrics.cache_hits)),
                        RecommendationEvidence(label="window_requests", value=str(metrics.total_requests)),
                        RecommendationEvidence(
                            label="avoided_premium_cost_usd",
                            value=f"{metrics.avoided_premium_cost_usd:.6f}",
                        ),
                    ],
                )
            )

        return CacheControlSummary(
            enabled=enabled,
            similarity_threshold=policy.semantic_cache_similarity_threshold,
            max_entry_age_hours=policy.semantic_cache_max_entry_age_hours,
            runtime_status=runtime_status,
            runtime_detail=runtime_detail,
            estimated_hit_rate=round(metrics.cache_hit_rate, 4),
            avoided_premium_cost_usd=metrics.avoided_premium_cost_usd,
            insights=cache_insights[:2],
        )

    def _build_recommendations(
        self,
        *,
        policy: TenantPolicy,
        metrics: RecommendationMetrics,
        cache_summary: CacheControlSummary,
    ) -> list[RecommendationCard]:
        recommendations: list[RecommendationCard] = []

        if cache_summary.runtime_status == "degraded":
            recommendations.append(
                RecommendationCard(
                    code="restore_semantic_cache_runtime",
                    title="Restore semantic cache availability",
                    priority=1,
                    category="cache",
                    summary="Cache-backed guidance is limited until the semantic cache dependency returns healthy.",
                    recommended_action="Investigate the semantic cache dependency and restore readiness before tuning thresholds.",
                    evidence=[
                        RecommendationEvidence(label="cache_runtime_status", value=cache_summary.runtime_status),
                        RecommendationEvidence(label="cache_runtime_detail", value=cache_summary.runtime_detail),
                    ],
                )
            )

        if (
            policy.semantic_cache_enabled
            and metrics.total_requests >= 5
            and metrics.cache_hit_rate < _CACHE_HIT_RECOMMENDATION_THRESHOLD
        ):
            recommendations.append(
                RecommendationCard(
                    code="tune_semantic_cache_threshold",
                    title="Review semantic cache tuning",
                    priority=2,
                    category="cache",
                    summary="The cache is enabled but recent hit rate is low for the observed request window.",
                    recommended_action=(
                        "Review similarity threshold and entry age to improve reuse without widening scope beyond operator controls."
                    ),
                    evidence=[
                        RecommendationEvidence(label="cache_hit_rate", value=f"{metrics.cache_hit_rate:.0%}"),
                        RecommendationEvidence(
                            label="similarity_threshold",
                            value=f"{policy.semantic_cache_similarity_threshold:.2f}",
                        ),
                        RecommendationEvidence(
                            label="max_entry_age_hours",
                            value=str(policy.semantic_cache_max_entry_age_hours),
                        ),
                    ],
                )
            )

        if (
            metrics.premium_share >= _PREMIUM_SHARE_RECOMMENDATION_THRESHOLD
            and metrics.premium_cost_usd >= _PREMIUM_COST_RECOMMENDATION_THRESHOLD_USD
        ):
            recommendations.append(
                RecommendationCard(
                    code="review_premium_routing_pressure",
                    title="Review premium routing pressure",
                    priority=3,
                    category="policy",
                    summary="A large share of recent traffic resolved to premium with measurable ledger cost.",
                    recommended_action="Inspect routing defaults and budget guardrails before premium spend grows further.",
                    evidence=[
                        RecommendationEvidence(label="premium_share", value=f"{metrics.premium_share:.0%}"),
                        RecommendationEvidence(
                            label="premium_cost_usd",
                            value=f"{metrics.premium_cost_usd:.6f}",
                        ),
                        RecommendationEvidence(
                            label="routing_mode_default",
                            value=policy.routing_mode_default,
                        ),
                    ],
                )
            )

        if metrics.policy_denials > 0:
            recommendations.append(
                RecommendationCard(
                    code="inspect_policy_denials",
                    title="Inspect recent policy denials",
                    priority=4,
                    category="policy",
                    summary="Recent ledger rows include denied requests, which may indicate tight premium or budget constraints.",
                    recommended_action="Review allowed premium models and per-request budget guardrails against operator intent.",
                    evidence=[
                        RecommendationEvidence(label="policy_denials", value=str(metrics.policy_denials)),
                        RecommendationEvidence(
                            label="max_premium_cost_per_request",
                            value=(
                                f"{policy.max_premium_cost_per_request:.6f}"
                                if policy.max_premium_cost_per_request is not None
                                else "unset"
                            ),
                        ),
                    ],
                )
            )

        if not recommendations:
            recommendations.append(
                RecommendationCard(
                    code="no_action_needed",
                    title="No immediate recommendation",
                    priority=5,
                    category="info",
                    summary="Recent ledger and cache signals do not show an immediate operator action.",
                    recommended_action="Continue monitoring current policy and cache settings.",
                    evidence=[
                        RecommendationEvidence(label="window_requests", value=str(metrics.total_requests)),
                        RecommendationEvidence(
                            label="last_request_at",
                            value=metrics.last_request_at.isoformat() if metrics.last_request_at else "none",
                        ),
                    ],
                )
            )

        recommendations.sort(key=lambda item: (item.priority, item.code))
        return recommendations
