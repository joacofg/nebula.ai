"""The product's default cache threshold is the one the pre-registered measurement chose.

benchmarks/cache/v1/report.json carries `preregistration.product_default_t`, the value the
pre-registered rule gives the product default. Both places a default lives (the policy model
a new tenant starts from and the stored column) must equal it, so re-measuring with a verdict
that moves the value fails here until the defaults follow.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nebula.db.models import Base, TenantPolicyModel
from nebula.models.governance import TenantPolicy

REPORT = Path(__file__).resolve().parents[1] / "benchmarks" / "cache" / "v1" / "report.json"


def _registered_default() -> float:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    return report["preregistration"]["product_default_t"]


def test_a_policy_built_without_the_field_uses_the_registered_default():
    assert TenantPolicy().semantic_cache_similarity_threshold == _registered_default()


def test_a_stored_policy_inserted_without_the_field_gets_the_registered_default():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    try:
        Base.metadata.create_all(engine)
        with Session(engine) as session:
            session.add(
                TenantPolicyModel(
                    tenant_id="fresh",
                    routing_mode_default="auto",
                    updated_at=datetime.now(UTC),
                )
            )
            session.commit()
            stored = session.get(TenantPolicyModel, "fresh")
            assert stored is not None
            assert stored.semantic_cache_similarity_threshold == _registered_default()
    finally:
        engine.dispose()
