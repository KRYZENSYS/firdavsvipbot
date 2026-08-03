"""Statistika va analitika."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Message, MessageDirection, User, UserStatus, UserTag


async def total_users(session: AsyncSession) -> int:
    res = await session.execute(select(func.count(User.id)))
    return int(res.scalar() or 0)


async def active_users_24h(session: AsyncSession) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    res = await session.execute(
        select(func.count(User.id)).where(User.last_seen >= cutoff)
    )
    return int(res.scalar() or 0)


async def online_now(session: AsyncSession) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
    res = await session.execute(
        select(func.count(User.id)).where(User.last_seen >= cutoff)
    )
    return int(res.scalar() or 0)


async def blocked_users(session: AsyncSession) -> int:
    res = await session.execute(
        select(func.count(User.id)).where(User.status == UserStatus.BLOCKED)
    )
    return int(res.scalar() or 0)


async def vip_users(session: AsyncSession) -> int:
    res = await session.execute(
        select(func.count(User.id)).where(User.tag == UserTag.VIP)
    )
    return int(res.scalar() or 0)


async def total_messages(session: AsyncSession) -> int:
    res = await session.execute(select(func.count(Message.id)))
    return int(res.scalar() or 0)


async def unread_messages(session: AsyncSession) -> int:
    res = await session.execute(
        select(func.count(Message.id))
        .where(Message.direction == MessageDirection.INCOMING)
        .where(Message.is_read.is_(False))
    )
    return int(res.scalar() or 0)


async def messages_today(session: AsyncSession) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    res = await session.execute(
        select(func.count(Message.id)).where(Message.created_at >= cutoff)
    )
    return int(res.scalar() or 0)


async def messages_last_n_days(session: AsyncSession, days: int = 7) -> list[tuple[str, int]]:
    """Har kunlik xabarlar soni (oxirgi N kun)."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    rows = await session.execute(
        select(
            func.date(Message.created_at).label("d"),
            func.count(Message.id).label("c"),
        )
        .where(Message.created_at >= cutoff)
        .group_by("d")
        .order_by("d")
    )
    return [(str(r.d), int(r.c)) for r in rows]


async def top_users_by_messages(session: AsyncSession, limit: int = 10) -> list[tuple[User, int]]:
    rows = await session.execute(
        select(User, func.count(Message.id).label("c"))
        .join(Message, Message.user_id == User.id)
        .group_by(User.id)
        .order_by(func.count(Message.id).desc())
        .limit(limit)
    )
    return [(u, int(c)) for u, c in rows.all()]


async def spam_messages_count(session: AsyncSession) -> int:
    res = await session.execute(
        select(func.count(Message.id)).where(Message.is_read.is_(False))
    )
    return int(res.scalar() or 0)


async def full_stats(session: AsyncSession) -> dict:
    return {
        "users_total": await total_users(session),
        "users_24h": await active_users_24h(session),
        "online_now": await online_now(session),
        "blocked": await blocked_users(session),
        "vip": await vip_users(session),
        "messages_total": await total_messages(session),
        "unread": await unread_messages(session),
        "messages_today": await messages_today(session),
        "messages_7d": await messages_last_n_days(session, 7),
    }
