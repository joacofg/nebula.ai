from __future__ import annotations

import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from nebula.db.models import Base


def _upgrade(database_url: str, revision: str = "head") -> None:
    # Save original environment variables
    original_db_url = os.environ.get("NEBULA_DATABASE_URL")
    original_data_store_path = os.environ.get("NEBULA_DATA_STORE_PATH")

    try:
        # Set environment variables to use the test database
        os.environ["NEBULA_DATABASE_URL"] = database_url
        # Ensure NEBULA_DATA_STORE_PATH doesn't interfere
        if "NEBULA_DATA_STORE_PATH" in os.environ:
            del os.environ["NEBULA_DATA_STORE_PATH"]

        root = Path(__file__).resolve().parents[1]
        config = Config(str(root / "alembic.ini"))
        config.set_main_option("script_location", str(root / "migrations"))
        command.upgrade(config, revision)
    finally:
        # Restore original environment variables
        if original_db_url is not None:
            os.environ["NEBULA_DATABASE_URL"] = original_db_url
        elif "NEBULA_DATABASE_URL" in os.environ:
            del os.environ["NEBULA_DATABASE_URL"]

        if original_data_store_path is not None:
            os.environ["NEBULA_DATA_STORE_PATH"] = original_data_store_path


def test_migrations_create_exactly_the_orm_schema(tmp_path: Path) -> None:
    versions = sorted(p.name for p in (Path(__file__).resolve().parents[1] / "migrations" / "versions").glob("*.py"))
    assert versions == [
        "20260916_0001_initial_schema.py",
        "20260930_0002_routing_quality_target.py",
        "20260930_0003_rate_limit.py",
    ]

    database_url = f"sqlite+pysqlite:///{tmp_path / 'fresh.db'}"
    _upgrade(database_url)

    engine = create_engine(database_url)
    try:
        inspector = inspect(engine)
        created = set(inspector.get_table_names()) - {"alembic_version"}
        expected = set(Base.metadata.tables)
        assert created == expected == {"tenants", "tenant_policies", "api_keys", "usage_ledger"}
        for table_name in expected:
            actual_columns = {column["name"] for column in inspector.get_columns(table_name)}
            model_columns = {column.name for column in Base.metadata.tables[table_name].columns}
            assert actual_columns == model_columns, table_name

        # Verify the ledger index exists
        usage_ledger_indexes = {index["name"] for index in inspector.get_indexes("usage_ledger")}
        assert "idx_usage_ledger_tenant_timestamp" in usage_ledger_indexes
    finally:
        engine.dispose()


def test_quality_target_migration_adds_the_column_to_a_pre_phase3_database(tmp_path: Path) -> None:
    # A database created before phase 3: tenant_policies without the column, stamped at 0001.
    database_url = f"sqlite+pysqlite:///{tmp_path / 'old.db'}"
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            policies = Base.metadata.tables["tenant_policies"]
            columns = [
                column for column in policies.columns if column.name != "routing_quality_target"
            ]
            ddl = ", ".join(
                f"{column.name} {column.type.compile(engine.dialect)}" for column in columns
            )
            connection.execute(text(f"CREATE TABLE tenant_policies ({ddl})"))
            connection.execute(
                text(
                    "INSERT INTO tenant_policies (tenant_id, routing_mode_default, "
                    "calibrated_routing_enabled, allowed_premium_models_json, "
                    "semantic_cache_enabled, semantic_cache_similarity_threshold, "
                    "semantic_cache_max_entry_age_hours, fallback_enabled, "
                    "prompt_capture_enabled, response_capture_enabled, "
                    "evidence_retention_window, metadata_minimization_level, updated_at) "
                    "VALUES ('old', 'auto', 1, '[]', 1, 0.9, 168, 1, 0, 0, '30d', 'standard', "
                    "'2026-09-01 00:00:00')"
                )
            )
            connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) PRIMARY KEY)"))
            connection.execute(text("INSERT INTO alembic_version VALUES ('20260916_0001')"))
    finally:
        engine.dispose()

    _upgrade(database_url)

    engine = create_engine(database_url)
    try:
        columns = {column["name"] for column in inspect(engine).get_columns("tenant_policies")}
        with engine.connect() as connection:
            value = connection.execute(
                text("SELECT routing_quality_target FROM tenant_policies WHERE tenant_id = 'old'")
            ).scalar_one()
    finally:
        engine.dispose()

    assert "routing_quality_target" in columns
    assert value == 0.95


def test_rate_limit_migration_adds_a_nullable_column_to_a_phase4_database(tmp_path: Path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'phase4.db'}"
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            policies = Base.metadata.tables["tenant_policies"]
            columns = [c for c in policies.columns if c.name != "rate_limit_requests_per_minute"]
            ddl = ", ".join(f"{c.name} {c.type.compile(engine.dialect)}" for c in columns)
            connection.execute(text(f"CREATE TABLE tenant_policies ({ddl})"))
            connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) PRIMARY KEY)"))
            connection.execute(text("INSERT INTO alembic_version VALUES ('20260930_0002')"))
    finally:
        engine.dispose()

    _upgrade(database_url)

    engine = create_engine(database_url)
    try:
        cols = {c["name"]: c for c in inspect(engine).get_columns("tenant_policies")}
    finally:
        engine.dispose()
    assert cols["rate_limit_requests_per_minute"]["nullable"] is True
