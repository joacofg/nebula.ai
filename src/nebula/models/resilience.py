from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

DependencyClass = Literal["serving_critical", "serving_optional", "metadata_only"]
DependencyLifecycleState = Literal["ready", "degraded", "not_ready", "recovering"]
ServingEffect = Literal["fail_closed", "continuity_limited", "unaffected"]


class DependencyHealthReason:
    GOVERNANCE_QUERY_FAILED = "governance_query_failed"
    GOVERNANCE_SCHEMA_INCOMPLETE = "governance_schema_incomplete"
    GOVERNANCE_READY = "governance_ready"
    SEMANTIC_CACHE_READY = "semantic_cache_ready"
    SEMANTIC_CACHE_UNAVAILABLE = "semantic_cache_unavailable"
    SEMANTIC_CACHE_COLLECTION_MISSING = "semantic_cache_collection_missing"
    PREMIUM_PROVIDER_MOCK = "premium_provider_mock"
    PREMIUM_PROVIDER_READY = "premium_provider_ready"
    PREMIUM_PROVIDER_UNAVAILABLE = "premium_provider_unavailable"
    LOCAL_OLLAMA_READY = "local_ollama_ready"
    LOCAL_OLLAMA_UNAVAILABLE = "local_ollama_unavailable"
    RETENTION_DISABLED = "retention_disabled"
    RETENTION_IDLE = "retention_idle"
    RETENTION_RUNNING = "retention_running"
    RETENTION_FAILED = "retention_failed"
    RETENTION_OK = "retention_ok"


def iso_or_none(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat()


def build_dependency_health(
    *,
    dependency_class: DependencyClass,
    lifecycle_state: DependencyLifecycleState,
    serving_effect: ServingEffect,
    reason_code: str,
    detail: str,
    required: bool,
    recovering: bool | None = None,
    last_failure_at: datetime | None = None,
    last_recovery_at: datetime | None = None,
    compatibility: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status": lifecycle_state,
        "required": required,
        "detail": detail,
        "dependency_class": dependency_class,
        "lifecycle_state": lifecycle_state,
        "serving_effect": serving_effect,
        "reason_code": reason_code,
        "recovering": recovering if recovering is not None else lifecycle_state == "recovering",
        "last_failure_at": iso_or_none(last_failure_at),
        "last_recovery_at": iso_or_none(last_recovery_at),
    }
    if compatibility:
        payload.update(compatibility)
    if extra:
        payload.update(extra)
    return payload
