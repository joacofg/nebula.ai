from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

DeploymentEnvironment = Literal["production", "staging", "development"]
EnrollmentState = Literal["pending", "active", "revoked", "unlinked"]


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
