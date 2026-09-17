from __future__ import annotations

import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from nebula.db.models import Base


def _upgrade(database_url: str) -> None:
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
        command.upgrade(config, "head")
    finally:
        # Restore original environment variables
        if original_db_url is not None:
            os.environ["NEBULA_DATABASE_URL"] = original_db_url
        elif "NEBULA_DATABASE_URL" in os.environ:
            del os.environ["NEBULA_DATABASE_URL"]

        if original_data_store_path is not None:
            os.environ["NEBULA_DATA_STORE_PATH"] = original_data_store_path


def test_single_migration_creates_exactly_the_orm_schema(tmp_path: Path) -> None:
    versions = sorted(p.name for p in (Path(__file__).resolve().parents[1] / "migrations" / "versions").glob("*.py"))
    assert versions == ["20260916_0001_initial_schema.py"]

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
