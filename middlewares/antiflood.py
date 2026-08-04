"""Anti-flood middleware."""
from __future__ import annotations

import time
from collections import defaultdict
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from config import config


class AntiFloodMiddleware(BaseMiddleware):
    """Foydalanuvchi xabarlarini rate-limit qilish.

    Konfiguratsiya:
      - ANTIFLOOD_RATE: sekundlar orasida minimal interval (default 2)
      - ANTIFLOOD_BURST: ruxsat etilgan burst hajmi (default 5)
    """

    def __init__(self, rate: float | None = None, burst: int | None = None) -> None:
        self.rate = rate or config.ANTIFLOOD_RATE
        self.burst = burst or config.ANTIFLOOD_BURST
        self._last: dict[int, float] = defaultdict(float)
        self._tokens: dict[int, float] = defaultdict(lambda: float(self.burst))
        self._warned: dict[int, float] = defaultdict(float)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Faqat Message va CallbackQuery uchun
        user = None
        if isinstance(event, Message):
            user = event.from_user
        else:
            user = getattr(event, "from_user", None)

        if user is None or user.is_bot:
            return await handler(event, data)

        uid = user.id
        now = time.monotonic()

        # Token bucket
        elapsed = now - self._last[uid]
        self._last[uid] = now
        # refill
        self._tokens[uid] = min(self.burst, self._tokens[uid] + elapsed / self.rate)
        if self._tokens[uid] < 1.0:
            # Spam — rate limited
            # 5 sekundda bir marta ogohlantirish
            if now - self._warned[uid] > 5:
                self._warned[uid] = now
                if isinstance(event, Message):
                    try:
                        await event.answer("⏳ Iltimos, sekinroq yozing. Juda ko'p xabar yubordingiz.")
                    except Exception:
                        pass
            return  # blok
        self._tokens[uid] -= 1.0
        return await handler(event, data)
