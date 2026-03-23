"""Canonical hosted default-export contract.

This module is the single backend source of truth for what metadata a
self-hosted Nebula deployment shares with the optional hosted control plane
by default.  It defines the allowlist (the Pydantic models) and the exclusion
list (HOSTED_EXCLUDED_DATA_CLASSES) so that downstream phases can reference
one authoritative contract instead of re-inventing field lists.

Trust-boundary rule: the hosted plane is metadata-only.  Raw prompts,
responses, provider credentials, usage-ledger rows, tenant secrets, and
authoritative runtime policy state NEVER leave the customer environment
via this default contract.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Freshness vocabulary
# ---------------------------------------------------------------------------

FreshnessStatus = Literal["connected", "degraded", "stale", "offline"]
"""Hosted control-plane freshness describes what the plane last heard from
a deployment, not whether the deployment is currently healthy."""

# ---------------------------------------------------------------------------
# Exclusion list — data classes that MUST NOT appear in the default export
# ---------------------------------------------------------------------------

HOSTED_EXCLUDED_DATA_CLASSES: tuple[str, ...] = (
    "raw_prompts",
    "raw_responses",
    "provider_credentials",
    "raw_usage_ledger_rows",
    "tenant_secrets",
    "authoritative_runtime_policy_state",
)

# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class HostedDependencySummary(BaseModel):
    """Coarse dependency health as last reported by the deployment."""

    healthy: list[str] = Field(default_factory=list)
    degraded: list[str] = Field(default_factory=list)
    unavailable: list[str] = Field(default_factory=list)


class HostedRemoteActionSummary(BaseModel):
    """Aggregate counts for remote actions processed by this deployment."""

    queued: int = 0
    applied: int = 0
    failed: int = 0
    last_action_at: datetime | None = None


# ---------------------------------------------------------------------------
# Top-level contract
# ---------------------------------------------------------------------------


class HostedDeploymentMetadata(BaseModel):
    """Default metadata a self-hosted Nebula deployment exports to the
    hosted control plane.

    This is the canonical allowlist.  Any field not present here is
    excluded by default.  Richer diagnostic exports (if added later)
    must be operator-initiated and clearly separate from this contract.
    """

    deployment_id: str
    display_name: str
    environment: str
    labels: dict[str, str] = Field(default_factory=dict)
    nebula_version: str
    capability_flags: list[str] = Field(default_factory=list)
    registered_at: datetime
    last_seen_at: datetime | None = None
    freshness_status: FreshnessStatus
    freshness_reason: str | None = None
    dependency_summary: HostedDependencySummary
    remote_action_summary: HostedRemoteActionSummary
