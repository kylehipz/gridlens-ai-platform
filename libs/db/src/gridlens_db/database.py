from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

DEFAULT_DATABASE_URL = "postgresql+psycopg://gridlens_app:gridlens_app_local@127.0.0.1:5432/gridlens_dev"


def database_url() -> str:
    return _normalize_driver(os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL))


def create_database_engine(url: str | None = None) -> Engine:
    return create_engine(_normalize_driver(url or database_url()), future=True)


def _normalize_driver(url: str) -> str:
    if url.startswith("postgresql://"):
        return f"postgresql+psycopg://{url.removeprefix('postgresql://')}"
    return url
