# Firdavs VIP Bot — Database layer
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from database.models import Base


def _ensure_data_dir(url: str) -> None:
    """SQLite uchun data/ papkasini yaratish."""
    if url.startswith("sqlite"):
        path = url.split("///", 1)[-1]
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)


DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///data/bot.db")
_ensure_data_dir(DATABASE_URL)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def init_db() -> None:
    """Barcha jadvallarni yaratish."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """Context manager orqali session olish."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_session_dep() -> AsyncIterator[AsyncSession]:
    """aiogram dependency sifatida."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


__all__ = [
    "engine",
    "async_session_factory",
    "init_db",
    "get_session",
    "get_session_dep",
]
