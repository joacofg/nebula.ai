"""Tests for the hosted default-export contract.

These tests lock the exact hosted metadata allowlist, freshness vocabulary,
and excluded data classes so that downstream phases cannot accidentally
drift the trust boundary.
"""

from __future__ import annotations

import json
from pathlib import Path


from nebula.models.hosted_contract import (
    HOSTED_EXCLUDED_DATA_CLASSES,
    FreshnessStatus,
    HostedDependencySummary,
    HostedDeploymentMetadata,
    HostedRemoteActionSummary,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# -- Schema allowlist guard --------------------------------------------------


def test_hosted_contract_schema_contains_only_allowed_default_export_fields():
    """The hosted metadata schema exposes exactly the allowed default fields."""
    schema = HostedDeploymentMetadata.model_json_schema()

    expected_properties = {
        "deployment_id",
        "display_name",
        "environment",
        "labels",
        "nebula_version",
        "capability_flags",
        "registered_at",
        "last_seen_at",
        "freshness_status",
        "freshness_reason",
        "dependency_summary",
        "remote_action_summary",
    }

    actual_properties = set(schema["properties"].keys())
    assert actual_properties == expected_properties, (
        f"Schema drift detected. "
        f"Missing: {expected_properties - actual_properties}, "
        f"Extra: {actual_properties - expected_properties}"
    )


# -- Freshness vocabulary guard -----------------------------------------------


def test_freshness_status_has_exactly_four_values():
    """Hosted freshness uses only connected, degraded, stale, and offline."""
    # FreshnessStatus is Literal — extract args from __args__
    allowed = set(FreshnessStatus.__args__)  # type: ignore[attr-defined]
    assert allowed == {"connected", "degraded", "stale", "offline"}


# -- Exclusion guard ----------------------------------------------------------


def test_hosted_contract_excludes_sensitive_runtime_data():
    """The exclusion list is exact and regression-safe."""
    assert HOSTED_EXCLUDED_DATA_CLASSES == (
        "raw_prompts",
        "raw_responses",
        "provider_credentials",
        "raw_usage_ledger_rows",
        "tenant_secrets",
        "authoritative_runtime_policy_state",
    )


def test_schema_properties_do_not_contain_excluded_names():
    """No excluded data class name appears as a top-level schema property."""
    schema = HostedDeploymentMetadata.model_json_schema()
    all_property_names = set(schema["properties"].keys())
    for excluded in HOSTED_EXCLUDED_DATA_CLASSES:
        assert excluded not in all_property_names, (
            f"Excluded data class '{excluded}' found in schema properties"
        )


# -- Schema artifact guard ----------------------------------------------------


def test_schema_title_is_hosted_deployment_metadata():
    """The generated schema title matches the canonical model name."""
    schema = HostedDeploymentMetadata.model_json_schema()
    assert schema["title"] == "HostedDeploymentMetadata"


def test_schema_includes_remote_action_summary():
    """The schema includes the remote action summary sub-model."""
    schema = HostedDeploymentMetadata.model_json_schema()
    # The property must exist at top level
    assert "remote_action_summary" in schema["properties"]


def test_schema_includes_freshness_status_enum_values():
    """The committed schema carries the four freshness enum values."""
    schema = HostedDeploymentMetadata.model_json_schema()
    freshness_prop = schema["properties"]["freshness_status"]
    # Pydantic v2 emits enum values in the property directly
    assert set(freshness_prop["enum"]) == {
        "connected",
        "degraded",
        "stale",
        "offline",
    }


# -- Committed JSON schema artifact guard -------------------------------------


def test_committed_schema_artifact_matches_model():
    """The committed JSON schema file matches the live Pydantic model output."""
    artifact_path = PROJECT_ROOT / "docs" / "hosted-default-export.schema.json"
    assert artifact_path.exists(), (
        f"Schema artifact not found at {artifact_path}"
    )

    with artifact_path.open() as f:
        committed = json.load(f)

    generated = HostedDeploymentMetadata.model_json_schema()
    assert committed == generated, (
        "Committed schema artifact has drifted from the Pydantic model. "
        "Regenerate with HostedDeploymentMetadata.model_json_schema()."
    )


# -- Sub-model structure guards -----------------------------------------------


def test_dependency_summary_has_expected_fields():
    """HostedDependencySummary has healthy, degraded, unavailable lists."""
    schema = HostedDependencySummary.model_json_schema()
    assert set(schema["properties"].keys()) == {
        "healthy",
        "degraded",
        "unavailable",
    }


def test_remote_action_summary_has_expected_fields():
    """HostedRemoteActionSummary has queued, applied, failed, last_action_at."""
    schema = HostedRemoteActionSummary.model_json_schema()
    assert set(schema["properties"].keys()) == {
        "queued",
        "applied",
        "failed",
        "last_action_at",
    }
