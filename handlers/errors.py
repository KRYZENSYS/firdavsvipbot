"""Xatolarni ushlash."""
import logging
from aiogram import Router
from aiogram.types import ErrorEvent

router = Router(name="errors")
logger = logging.getLogger(__name__)


@router.error()
async def on_error(event: ErrorEvent) -> None:
    logger.exception(
        "Unhandled exception in update %s: %s",
        getattr(event.update, "update_id", "?"),
        event.exception,
    )
