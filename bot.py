"""Firdavs VIP Bot — main entrypoint.

Bu fayl botni ishga tushiradi:
  - Logger sozlash
  - Database yaratish
  - Bot va Dispatcher yaratish
  - Middleware va handlerlarni ulash
  - Polling orqali ishlash
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import config
from database.db import init_db
from handlers import admin as admin_handlers
from handlers import errors as error_handlers
from handlers import user as user_handlers
from middlewares.antiflood import AntiFloodMiddleware
from middlewares.db_session import DbSessionMiddleware


async def on_startup(bot: Bot) -> None:
    me = await bot.get_me()
    logging.info("=" * 60)
    logging.info("🤖 %s (@%s) ishga tushdi", me.full_name, me.username)
    logging.info("👑 Admin ID: %s", config.ADMIN_ID)
    logging.info("💾 Database: %s", config.DATABASE_URL)
    logging.info("🌍 Timezone: %s", config.TIMEZONE)
    logging.info("=" * 60)
    try:
        await bot.send_message(
            chat_id=config.ADMIN_ID,
            text=(
                "🚀 <b>Firdavs VIP Bot ishga tushdi</b>\n\n"
                f"🤖 @{me.username}\n"
                f"📅 {me.created_at}\n\n"
                "✅ Barcha tizimlar tayyor. Admin panel: /admin"
            ),
            parse_mode="HTML",
        )
    except Exception as e:
        logging.warning("Admin'ga xabar yuborilmadi: %s", e)


async def on_shutdown(bot: Bot) -> None:
    logging.info("🛑 Bot to'xtatilmoqda...")
    try:
        await bot.send_message(
            chat_id=config.ADMIN_ID,
            text="🛑 Bot to'xtatildi.",
        )
    except Exception:
        pass
    await bot.session.close()


async def main() -> None:
    # Logging
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger(__name__)

    # Token tekshirish
    if not config.BOT_TOKEN or config.BOT_TOKEN == "PUT_YOUR_BOT_TOKEN_HERE":
        logger.error("❌ BOT_TOKEN .env faylida o'rnatilmagan!")
        sys.exit(1)
    if not config.ADMIN_ID:
        logger.error("❌ ADMIN_ID .env faylida o'rnatilmagan!")
        sys.exit(1)

    # Database
    await init_db()
    logger.info("✅ Database tayyor")

    # Bot
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Dispatcher
    dp = Dispatcher(storage=MemoryStorage())

    # Middlewares
    dp.message.middleware(DbSessionMiddleware())
    dp.callback_query.middleware(DbSessionMiddleware())
    dp.message.middleware(AntiFloodMiddleware())
    dp.callback_query.middleware(AntiFloodMiddleware())

    # Routers
    dp.include_router(admin_handlers.router)
    dp.include_router(user_handlers.router)
    dp.include_router(error_handlers.router)

    # Hooks
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    logger.info("🚀 Bot polling boshlanmoqda...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("👋 Bot to'xtatildi (Ctrl+C)")
    except Exception as e:
        logging.exception("Kutilmagan xato: %s", e)
        sys.exit(1)
