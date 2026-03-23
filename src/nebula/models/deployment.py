from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

DeploymentEnvironment = Literal["production", "staging", "development"]
EnrollmentState = Literal["pending", "active", "revoked", "unlinked"]
RemoteActionType = Literal["rotate_deployment_credential"]
RemoteActionStatus = Literal["queued", "in_progress", "applied", "failed"]
RemoteActionFailureReason = Literal[
    "unauthorized_local_policy",
    "expired",
    "unsupported_capability",
    "invalid_state",
    "apply_error",
]


class DeploymentCreateRequest(BaseModel):
    display_name: str
    environment: DeploymentEnvironment


class DeploymentRecord(BaseModel):
    id: str
    display_name: str
    environment: str
    enrollment_state: EnrollmentState
    nebula_version: str | None
    capability_flags: list[str]
    enrolled_at: str | None
    revoked_at: str | None
    unlinked_at: str | None
    created_at: str
    updated_at: str
    last_seen_at: str | None = None
    freshness_status: str | None = None  # FreshnessStatus or None for pending (per D-14)
    freshness_reason: str | None = None
    dependency_summary: dict[str, list[str]] | None = None
    remote_action_summary: RemoteActionSummary | None = None


class RemoteActionSummary(BaseModel):
    queued: int = 0
    applied: int = 0
    failed: int = 0
    last_action_at: str | None = None


class RemoteActionQueueRequest(BaseModel):
    note: str = Field(min_length=1, max_length=280)


class RemoteActionRecord(BaseModel):
    id: str
    deployment_id: str
    action_type: RemoteActionType
    status: RemoteActionStatus
    note: str
    requested_at: str
    expires_at: str
    started_at: str | None = None
    finished_at: str | None = None
    failure_reason: RemoteActionFailureReason | None = None
    failure_detail: str | None = None
    result_credential_prefix: str | None = None


class EnrollmentTokenResponse(BaseModel):
    token: str
    expires_at: str
    deployment_id: str


class EnrollmentExchangeRequest(BaseModel):
    enrollment_token: str
    nebula_version: str
    capability_flags: list[str]


class EnrollmentExchangeResponse(BaseModel):
    deployment_id: str
    deployment_credential: str
    display_name: str
    environment: str
