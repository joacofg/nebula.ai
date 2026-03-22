from __future__ import annotations

from pydantic import BaseModel


class HeartbeatRequest(BaseModel):
    nebula_version: str
    capability_flags: list[str]
    dependency_summary: dict[str, list[str]]
    # dependency_summary shape: {"healthy": ["governance_store"], "degraded": [], "unavailable": ["semantic_cache"]}


class HeartbeatResponse(BaseModel):
    acknowledged: bool
