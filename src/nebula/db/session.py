from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from nebula.core.config import Settings


def resolve_database_url(settings: Settings) -> str:
    if settings.database_url:
        return settings.database_url
    if settings.data_store_path == ":memory:":
        return "sqlite+pysqlite:///:memory:"
    return f"sqlite+pysqlite:///{Path(settings.data_store_path).resolve()}"


def create_engine_from_settings(settings: Settings) -> Engine:
    database_url = resolve_database_url(settings)
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    if database_url.startswith("sqlite") and settings.data_store_path != ":memory:":
        Path(settings.data_store_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
    return create_engine(database_url, future=True, pool_pre_ping=True, connect_args=connect_args)


def create_session_factory(settings: Settings) -> sessionmaker[Session]:
    engine = create_engine_from_settings(settings)
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)
