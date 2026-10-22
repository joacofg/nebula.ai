"""The product's default cache threshold is the one the pre-registered measurement chose.

benchmarks/cache/v1/report.json carries `preregistration.product_default_t`, the value the
pre-registered rule gives the product default. Both places a default lives (the policy model
a new tenant starts from and the stored column) must equal it, so re-measuring with a verdict
that moves the value fails here until the defaults follow.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from nebula.db.models import Base, TenantPolicyModel
from nebula.models.governance import TenantPolicy
from tests.support import registered_cache_threshold


def test_a_policy_built_without_the_field_uses_the_registered_default():
    assert TenantPolicy().semantic_cache_similarity_threshold == registered_cache_threshold()


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
            assert stored.semantic_cache_similarity_threshold == registered_cache_threshold()
    finally:
        engine.dispose()
