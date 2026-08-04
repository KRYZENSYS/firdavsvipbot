"""Foydalanuvchi handlerlari."""
from __future__ import annotations

from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from config import config
from database.models import Feedback, Message as DbMessage, MessageDirection, UserStatus, UserTag
from keyboards.reply import (
    cancel_kb,
    feedback_kb,
    language_kb,
    main_reply_kb,
)
from utils.helpers import (
    escape,
    fmt_dt,
    get_lang,
    get_or_create_user,
    is_spam_text,
    is_valid_message,
    media_label,
    tz_now,
)
from utils.i18n import t
from utils.states import UserStates

router = Router(name="user")


async def _user_lang(message: Message, session) -> str:
    user = await get_or_create_user(session, message.from_user)
    return get_lang(user)


# ============== /start ==============
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, session) -> None:
    await state.clear()
    user = await get_or_create_user(session, message.from_user)
    lang = get_lang(user)
    text = t("welcome", lang, name=user.full_name, brand=config.BRAND_NAME)
    await message.answer(text, reply_markup=main_reply_kb(lang), parse_mode="HTML")


# ============== /help ==============
@router.message(Command("help"))
async def cmd_help(message: Message, session) -> None:
    lang = await _user_lang(message, session)
    await message.answer(t("help", lang), parse_mode="HTML", reply_markup=main_reply_kb(lang))


# ============== /profile ==============
@router.message(Command("profile"))
async def cmd_profile(message: Message, session) -> None:
    user = await get_or_create_user(session, message.from_user)
    lang = get_lang(user)
    text = t(
        "profile", lang,
        anon_id=user.anonymous_id,
        full_name=escape(user.full_name),
        username=user.username or "—",
        language=lang.upper(),
        tag=user.tag.value,
        messages=user.message_count,
        created=fmt_dt(user.created_at),
    )
    await message.answer(text, parse_mode="HTML", reply_markup=main_reply_kb(lang))


# ============== /status ==============
@router.message(Command("status"))
async def cmd_status(message: Message, session) -> None:
    # Admin onlayn/oflaynligi haqida taxminiy ma'lumot
    # Production uchun admin sessionini kuzatish kerak (hozircha shunday)
    user = await get_or_create_user(session, message.from_user)
    lang = get_lang(user)
    if config.AUTO_REPLY_ENABLED:
        text = t("status", lang)
    else:
        text = t("status", lang).split("— yoki —")[0]
    await message.answer(text, parse_mode="HTML", reply_markup=main_reply_kb(lang))


# ============== /clear ==============
@router.message(Command("clear"))
async def cmd_clear(message: Message, session) -> None:
    user = await get_or_create_user(session, message.from_user)
    lang = get_lang(user)
    # eski xabarlarni o'chirish (faqat shu user uchun)
    from sqlalchemy import delete
    await session.execute(
        delete(DbMessage).where(DbMessage.user_id == user.id)
    )
    await message.answer(t("clear", lang), reply_markup=main_reply_kb(lang))


# ============== /stop ==============
@router.message(Command("stop"))
async def cmd_stop(message: Message, state: FSMContext, session) -> None:
    await state.set_state(UserStates.chatting)
    user = await get_or_create_user(session, message.from_user)
    lang = get_lang(user)
    await message.answer(
        t("stop", lang),
        reply_markup=ReplyKeyboardRemove(),
    )


# ============== /lang ==============
@router.message(Command("lang"))
async def cmd_lang(message: Message, session) -> None:
    user = await get_or_create_user(session, message.from_user)
    await message.answer(
        t("lang_select", get_lang(user)),
        reply_markup=language_kb(),
    )


# Language selection (custom)
@router.message(F.text.in_(["🇺🇿 O'zbek", "🇷🇺 Русский", "🇬🇧 English", "◀️ Bekor"]))
async def choose_language(message: Message, session) -> None:
    user = await get_or_create_user(session, message.from_user)
    text = message.text or ""
    if text == "🇺🇿 O'zbek" or text == "O'zbek":
        user.language = "uz"
    elif text == "🇷🇺 Русский" or text == "Русский":
        user.language = "ru"
    elif text == "🇬🇧 English":
        user.language = "en"
    else:
        await message.answer("Bekor qilindi.", reply_markup=main_reply_kb(get_lang(user)))
        return
    lang_label = {"uz": "O'zbek", "ru": "Русский", "en": "English"}[user.language]
    await message.answer(
        t("lang_changed", get_lang(user), language=lang_label),
        reply_markup=main_reply_kb(user.language),
    )


# ============== Reply keyboard button handlers ==============
@router.message(F.text.in_(["👤 Profil", "👤 Profile", "👤 Профиль"]))
async def btn_profile(message: Message, session) -> None:
    await cmd_profile(message, session)


@router.message(F.text.in_(["📊 Status", "📊 Статус"]))
async def btn_status(message: Message, session) -> None:
    await cmd_status(message, session)


@router.message(F.text.in_(["🌐 Til", "🌐 Язык", "🌐 Language"]))
async def btn_lang(message: Message, session) -> None:
    await cmd_lang(message, session)


@router.message(F.text.in_(["ℹ️ Yordam", "ℹ️ Помощь", "ℹ️ Help"]))
async def btn_help(message: Message, session) -> None:
    await cmd_help(message, session)


@router.message(F.text.in_(["💬 Chat", "💬 Чат"]))
async def btn_chat(message: Message, state: FSMContext, session) -> None:
    user = await get_or_create_user(session, message.from_user)
    await state.set_state(UserStates.chatting)
    await message.answer(
        "✍️ Xabaringizni yozing. Admin ko'radi va javob beradi.\n\n/stop — suhbatni to'xtatish",
        reply_markup=main_reply_kb(get_lang(user)),
    )


# ============== /feedback ==============
@router.message(Command("feedback"))
async def cmd_feedback(message: Message, state: FSMContext, session) -> None:
    user = await get_or_create_user(session, message.from_user)
    await state.set_state(UserStates.feedback_rating)
    await message.answer(
        t("feedback_prompt", get_lang(user)),
        reply_markup=feedback_kb(),
    )


@router.message(UserStates.feedback_rating, F.text.regexp(r"^⭐+$"))
async def feedback_rating(message: Message, state: FSMContext, session) -> None:
    user = await get_or_create_user(session, message.from_user)
    stars = (message.text or "").count("⭐")
    stars = max(1, min(5, stars))
    await state.update_data(rating=stars)
    await state.set_state(UserStates.feedback_comment)
    await message.answer(
        t("feedback_comment_prompt", get_lang(user)),
        reply_markup=cancel_kb(get_lang(user)),
    )


@router.message(UserStates.feedback_comment, F.text.in_(["⏭ O'tkazib yuborish", "/skip"]))
async def feedback_skip(message: Message, state: FSMContext, session) -> None:
    data = await state.get_data()
    user = await get_or_create_user(session, message.from_user)
    fb = Feedback(user_id=user.id, rating=data.get("rating", 5), comment="—")
    session.add(fb)
    await state.clear()
    await message.answer(
        t("feedback_thanks", get_lang(user)),
        reply_markup=main_reply_kb(get_lang(user)),
    )


@router.message(UserStates.feedback_comment, F.text)
async def feedback_comment(message: Message, state: FSMContext, session) -> None:
    data = await state.get_data()
    user = await get_or_create_user(session, message.from_user)
    fb = Feedback(
        user_id=user.id,
        rating=data.get("rating", 5),
        comment=message.text or "",
    )
    session.add(fb)
    await state.clear()
    await message.answer(
        t("feedback_thanks", get_lang(user)),
        reply_markup=main_reply_kb(get_lang(user)),
    )


# ============== Asosiy chat handler ==============
@router.message(UserStates.chatting, F.text)
async def chat_text(message: Message, state: FSMContext, session) -> None:
    await _forward_message(message, state, session)


@router.message(UserStates.chatting)
async def chat_any(message: Message, state: FSMContext, session) -> None:
    await _forward_message(message, state, session)


async def _forward_message(message: Message, state: FSMContext, session) -> None:
    """Foydalanuvchi xabarini admin'ga yuborish."""
    user = await get_or_create_user(session, message.from_user)
    lang = get_lang(user)

    if user.status == UserStatus.BLOCKED:
        await message.answer(t("blocked", lang))
        return

    text = media_label(message)
    if not is_valid_message(text):
        await message.answer(t("msg_too_long", lang, max=config.MAX_MESSAGE_LENGTH))
        return

    spam = is_spam_text(text)
    if spam:
        user.warnings += 1
        if user.warnings >= 3:
            user.status = UserStatus.BLOCKED
            user.tag = UserTag.SPAMMER
        await message.answer(t("spam_warning", lang))
        return

    # DB ga saqlash
    db_msg = DbMessage(
        user_id=user.id,
        direction=MessageDirection.INCOMING,
        text=text,
        is_spam=False,
        telegram_message_id=message.message_id,
    )
    session.add(db_msg)
    user.message_count += 1
    user.last_seen = tz_now().replace(tzinfo=None)
    if user.tag == UserTag.NEW and user.message_count > 0:
        user.tag = UserTag.REGULAR

    # Admin'ga yuborish
    try:
        admin_text = (
            f"💌 <b>Yangi xabar</b>\n\n"
            f"🎭 <b>{escape(user.anonymous_id)}</b>\n"
            f"👤 Ism: {escape(user.full_name)}\n"
            f"📛 Username: @{escape(user.username or '—')}\n"
            f"🆔 ID: <code>{user.telegram_id}</code>\n"
            f"🏷 Teg: {user.tag.value}\n"
            f"⚠️ Warnings: {user.warnings}\n"
            f"🕐 {fmt_dt(tz_now())}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{escape(text)}\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        await message.bot.send_message(
            chat_id=config.ADMIN_ID,
            text=admin_text,
            parse_mode="HTML",
            reply_markup=None,
        )
    except Exception as e:
        # admin'ga yuborilmasa ham, xabar saqlanadi
        pass

    # Foydalanuvchiga tasdiq
    if config.AUTO_REPLY_ENABLED:
        await message.answer(t("auto_reply", lang), reply_markup=main_reply_kb(lang))
    else:
        await message.answer(t("message_sent", lang), reply_markup=main_reply_kb(lang))


# ============== Default (no state) handler — bu /start ni ushlamagan xabarlar uchun ==============
@router.message(F.text)
async def default_text(message: Message, session) -> None:
    """Agar user FSM holatida bo'lmasa, suhbatni boshlashga yo'naltiramiz."""
    user = await get_or_create_user(session, message.from_user)
    lang = get_lang(user)
    if user.status == UserStatus.BLOCKED:
        await message.answer(t("blocked", lang))
        return
    # Default: har qanday xabarni chat sifatida qabul qilamiz
    from aiogram.fsm.context import FSMContext
    state = FSMContext(
        storage=message.bot.fsm_storage,
        chat=message.chat,
        user=message.from_user.id,
    )
    await state.set_state(UserStates.chatting)
    await _forward_message(message, state, session)
