"""Yordamchi funksiyalar."""
from __future__ import annotations

import html
import random
import string
from datetime import datetime
from typing import Optional

import pytz
from aiogram.types import Message, User as TgUser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import config
from database.models import User, UserTag


# ============== Anonim ID generator ==============
ADJECTIVES = [
    "Neon", "Cyber", "Shadow", "Phantom", "Midnight", "Pixel", "Quantum",
    "Ninja", "Ghost", "Stellar", "Lunar", "Solar", "Void", "Astral",
    "Vortex", "Echo", "Nova", "Pulse", "Glitch", "Onyx", "Rogue", "Zen",
    "Frozen", "Toxic", "Crimson", "Blazing", "Silent", "Electric", "Mystic",
]

ANIMALS = [
    "Wolf", "Fox", "Cat", "Hawk", "Tiger", "Panther", "Eagle", "Dragon",
    "Raven", "Shark", "Falcon", "Lynx", "Phoenix", "Viper", "Otter", "Owl",
    "Bear", "Cobra", "Jaguar", "Mantis", "Spider", "Bison", "Crane", "Whale",
]


def make_anonymous_id() -> str:
    """Masalan: NeonFox_42"""
    return f"{random.choice(ADJECTIVES)}{random.choice(ANIMALS)}_{random.randint(10, 999)}"


def tz_now() -> datetime:
    """Asia/Tashkent timezone hozirgi vaqt."""
    return datetime.now(pytz.timezone(config.TIMEZONE))


def fmt_dt(dt: Optional[datetime]) -> str:
    if not dt:
        return "—"
    if dt.tzinfo is None:
        dt = pytz.timezone(config.TIMEZONE).localize(dt)
    return dt.strftime("%d.%m.%Y %H:%M")


def escape(text: str) -> str:
    """HTML escape — xavfsiz ko'rsatish uchun."""
    if text is None:
        return ""
    return html.escape(str(text))


def is_spam_text(text: str) -> bool:
    """Spam kalit so'zlarini tekshirish."""
    if not text:
        return False
    low = text.lower()
    return any(kw in low for kw in config.SPAM_KEYWORDS)


def truncate(text: str, limit: int = 200) -> str:
    if not text:
        return ""
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def is_admin(telegram_id: int) -> bool:
    return config.ADMIN_ID and telegram_id == config.ADMIN_ID


def is_valid_message(text: str) -> bool:
    if not text:
        return False
    if len(text) > config.MAX_MESSAGE_LENGTH:
        return False
    return True


async def get_or_create_user(
    session: AsyncSession, tg_user: TgUser, language: str | None = None
) -> User:
    """Foydalanuvchini bazadan olish yoki yaratish."""
    result = await session.execute(
        select(User).where(User.telegram_id == tg_user.id)
    )
    user = result.scalar_one_or_none()
    if user:
        # yangilash
        user.username = tg_user.username
        user.full_name = tg_user.full_name or "Anonymous"
        user.is_online = True
        user.last_seen = tz_now().replace(tzinfo=None)
        if user.tag == UserTag.NEW and user.message_count > 0:
            user.tag = UserTag.REGULAR
        return user

    # yangi user
    user = User(
        telegram_id=tg_user.id,
        username=tg_user.username,
        full_name=tg_user.full_name or "Anonymous",
        anonymous_id=make_anonymous_id(),
        language=(language or config.DEFAULT_LANGUAGE),
        tag=UserTag.NEW,
        last_seen=tz_now().replace(tzinfo=None),
        created_at=tz_now().replace(tzinfo=None),
    )
    session.add(user)
    await session.flush()
    return user


def get_lang(user: User) -> str:
    return user.language or config.DEFAULT_LANGUAGE


def media_label(message: Message) -> str:
    """Xabar turi matn sifatida."""
    if message.text:
        return message.text
    if message.photo:
        return f"[📷 Photo: {message.caption or 'no caption'}]"
    if message.video:
        return f"[🎬 Video: {message.caption or 'no caption'}]"
    if message.voice:
        return "[🎤 Voice message]"
    if message.audio:
        return f"[🎵 Audio: {message.audio.title or ''}]"
    if message.document:
        return f"[📎 File: {message.document.file_name or 'document'}]"
    if message.sticker:
        return f"[🎭 Sticker: {message.sticker.emoji or ''}]"
    if message.animation:
        return "[🎞 GIF]"
    if message.location:
        return "[📍 Location]"
    if message.contact:
        return "[👤 Contact]"
    if message.poll:
        return "[📊 Poll]"
    return "[Unsupported message]"


def short_id(uid: int) -> str:
    """Qisqa ID (UI uchun)."""
    return f"#{uid}"


__all__ = [
    "make_anonymous_id",
    "tz_now",
    "fmt_dt",
    "escape",
    "is_spam_text",
    "truncate",
    "is_admin",
    "is_valid_message",
    "get_or_create_user",
    "get_lang",
    "media_label",
    "short_id",
]
