# Firdavs VIP Bot Configuration
import os
from dataclasses import dataclass, field
from typing import List


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def _env_int(key: str, default: int = 0) -> int:
    try:
        return int(os.environ.get(key, default))
    except (TypeError, ValueError):
        return default


def _env_bool(key: str, default: bool = False) -> bool:
    v = os.environ.get(key)
    if v is None:
        return default
    return v.lower() in ("1", "true", "yes", "on")


@dataclass
class Config:
    # Telegram
    BOT_TOKEN: str = _env("BOT_TOKEN", "PUT_YOUR_BOT_TOKEN_HERE")
    ADMIN_ID: int = _env_int("ADMIN_ID", 0)          # Sizning Telegram ID
    ADMIN_USERNAME: str = _env("ADMIN_USERNAME", "firdavs")  # Sizning @username (ixtiyoriy)

    # Database
    DATABASE_URL: str = _env("DATABASE_URL", "sqlite+aiosqlite:///data/bot.db")

    # Security
    ADMIN_PIN: str = _env("ADMIN_PIN", "2026")        # 4-6 raqamli admin panel paroli
    ANTIFLOOD_RATE: int = _env_int("ANTIFLOOD_RATE", 2)  # sekundlar orasida minimal interval
    ANTIFLOOD_BURST: int = _env_int("ANTIFLOOD_BURST", 5)
    SPAM_KEYWORDS: List[str] = field(default_factory=lambda: [
        w.strip().lower() for w in
        _env("SPAM_KEYWORDS", "viagra,casino,crypto giveaway,free money,click here,xxx,sex")
        .split(",") if w.strip()
    ])

    # Bot behavior
    DEFAULT_LANGUAGE: str = _env("DEFAULT_LANGUAGE", "uz")  # uz | ru | en
    AUTO_REPLY_ENABLED: bool = _env_bool("AUTO_REPLY_ENABLED", True)
    AUTO_REPLY_TEXT: str = _env(
        "AUTO_REPLY_TEXT",
        "✅ Xabaringiz qabul qilindi! Admin tez orada javob beradi. 🤍",
    )

    # Limits
    MAX_MESSAGE_LENGTH: int = _env_int("MAX_MESSAGE_LENGTH", 4000)
    MAX_HISTORY_PER_USER: int = _env_int("MAX_HISTORY_PER_USER", 50)

    # Branding
    BRAND_NAME: str = _env("BRAND_NAME", "Firdavs VIP")
    BRAND_TAGLINE: str = _env("BRAND_TAGLINE", "Premium anonymous chat — siz bilan, faqat siz uchun 🤍")
    BRAND_URL: str = _env("BRAND_URL", "https://t.me/FirdavsVipBot")

    # Misc
    LOG_LEVEL: str = _env("LOG_LEVEL", "INFO")
    TIMEZONE: str = _env("TIMEZONE", "Asia/Tashkent")


config = Config()
