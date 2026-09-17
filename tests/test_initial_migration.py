from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from nebula.db.models import Base


def _upgrade(database_url: str) -> None:
    root = Path(__file__).resolve().parents[1]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")


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
    finally:
        engine.dispose()
