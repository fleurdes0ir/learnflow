"""Async engine SQLAlchemy (lazy). Schema & migration menyusul di Milestone 1."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import get_settings

_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            get_settings().database_url,
            pool_pre_ping=True,
            connect_args={"timeout": 3},  # asyncpg: gagal cepat kalau DB mati
        )
    return _engine


async def check_db() -> bool:
    """SELECT 1. Dipakai /readyz — tidak pernah melempar exception."""
    try:
        async with get_engine().connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        return False
    return True


async def dispose_engine() -> None:
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
