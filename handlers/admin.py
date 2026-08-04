"""Admin panel handlerlari — PIN himoyali kengaytirilgan boshqaruv."""
from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
)
from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from config import config
from database.models import (
    AdminSettings,
    AuditLog,
    Feedback,
    Message as DbMessage,
    MessageDirection,
    User,
    UserStatus,
    UserTag,
)
from keyboards import inline as ikb
from utils import analytics as A
from utils.helpers import escape, fmt_dt, media_label
from utils.states import AdminStates

router = Router(name="admin")


# ============== /admin (PIN) ==============
@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext, session) -> None:
    if not message.from_user or message.from_user.id != config.ADMIN_ID:
        await message.answer("⛔ Bu buyruq faqat admin uchun.")
        return
    await state.set_state(AdminStates.pin)
    await message.answer("🔐 Admin panel uchun PIN kodni kiriting:")


@router.message(AdminStates.pin, F.text)
async def check_pin(message: Message, state: FSMContext, session) -> None:
    if (message.text or "").strip() == config.ADMIN_PIN:
        await state.set_state(AdminStates.menu)
        await log_audit(session, config.ADMIN_ID, "admin_login", config.ADMIN_ID, "PIN ok")
        await message.answer(
            "✅ Xush kelibsiz, admin!\n\n👑 Admin panel:",
            reply_markup=ikb.main_admin_kb(),
        )
    else:
        await log_audit(session, config.ADMIN_ID, "admin_login_fail", config.ADMIN_ID, "Wrong PIN")
        await message.answer("❌ Noto'g'ri PIN. Qaytadan urinib ko'ring:")
        await state.clear()


# ============== Admin home ==============
@router.callback_query(F.data == "adm:home")
async def cb_home(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminStates.menu)
    await call.message.edit_text(
        "👑 <b>Admin Panel</b>\n\nBo'limni tanlang:",
        reply_markup=ikb.main_admin_kb(),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data == "adm:exit")
async def cb_exit(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await call.message.edit_text("🚪 Admin panelidan chiqildi.")
    await call.answer()


# ============== Statistics ==============
@router.callback_query(F.data == "adm:stats")
async def cb_stats(call: CallbackQuery, session) -> None:
    s = await A.full_stats(session)
    text = (
        "📊 <b>Statistika</b>\n\n"
        f"👥 Foydalanuvchilar: <b>{s['users_total']}</b>\n"
        f"🆕 Faol (24h): <b>{s['users_24h']}</b>\n"
        f"🟢 Onlayn hozir: <b>{s['online_now']}</b>\n"
        f"⭐ VIP: <b>{s['vip']}</b>\n"
        f"🚫 Bloklangan: <b>{s['blocked']}</b>\n\n"
        f"💬 Xabarlar (jami): <b>{s['messages_total']}</b>\n"
        f"📨 Bugun: <b>{s['messages_today']}</b>\n"
        f"🔔 O'qilmagan: <b>{s['unread']}</b>\n"
    )
    # 7 kunlik mini grafik
    if s['messages_7d']:
        text += "\n📈 <b>Oxirgi 7 kun:</b>\n"
        for d, c in s['messages_7d']:
            bar = "█" * min(c, 20)
            text += f"<code>{d}</code> {bar} {c}\n"
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=ikb.stats_kb())
    await call.answer()


# ============== Users list ==============
@router.callback_query(F.data.startswith("adm:users"))
async def cb_users(call: CallbackQuery, session) -> None:
    parts = (call.data or "").split(":")
    page = 0
    if len(parts) >= 3 and parts[2].isdigit():
        page = int(parts[2])
    res = await session.execute(select(User).order_by(User.created_at.desc()).limit(500))
    users = res.scalars().all()
    if not users:
        await call.answer("Hozircha foydalanuvchilar yo'q.", show_alert=True)
        return
    per_page = 8
    total_pages = (len(users) + per_page - 1) // per_page
    text = f"👥 <b>Foydalanuvchilar</b> ({len(users)} ta, sahifa {page+1}/{total_pages})"
    await call.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=ikb.users_list_kb(list(users), page, per_page),
    )
    await call.answer()


# ============== Single user view ==============
@router.callback_query(F.data.startswith("adm:user:"))
async def cb_user(call: CallbackQuery, session) -> None:
    parts = (call.data or "").split(":")
    if len(parts) < 3:
        return
    sub = parts[2]
    user_db_id = int(parts[3]) if len(parts) > 3 else None
    if not user_db_id:
        await call.answer("Xato", show_alert=True)
        return

    user = await session.get(User, user_db_id)
    if not user:
        await call.answer("Foydalanuvchi topilmadi.", show_alert=True)
        return

    if sub == "msg":
        # user xabarlarini ko'rsatish
        res = await session.execute(
            select(DbMessage)
            .where(DbMessage.user_id == user_db_id)
            .order_by(DbMessage.created_at.desc())
            .limit(20)
        )
        msgs = res.scalars().all()
        if not msgs:
            await call.answer("Xabarlar yo'q.", show_alert=True)
            return
        text = f"💬 <b>{escape(user.anonymous_id)} — suhbat tarixi</b>\n\n"
        for m in reversed(msgs):
            icon = "🟢" if m.direction == MessageDirection.INCOMING else "🔵"
            text += f"{icon} <i>{fmt_dt(m.created_at)}</i>\n{escape(m.text[:200])}\n\n"
        await call.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=ikb.user_messages_kb(user_db_id, user.telegram_id),
        )
        await call.answer()
        return

    text = (
        f"👤 <b>{escape(user.anonymous_id)}</b>\n\n"
        f"📛 Ism: {escape(user.full_name)}\n"
        f"📛 Username: @{escape(user.username or '—')}\n"
        f"🆔 Telegram ID: <code>{user.telegram_id}</code>\n"
        f"🌐 Til: {user.language}\n"
        f"🏷 Teg: <b>{user.tag.value}</b>\n"
        f"📊 Status: {user.status.value}\n"
        f"⚠️ Warnings: {user.warnings}\n"
        f"💬 Xabarlar: {user.message_count}\n"
        f"🕐 Ro'yxatdan: {fmt_dt(user.created_at)}\n"
        f"👁 Oxirgi: {fmt_dt(user.last_seen)}\n"
    )
    await call.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=ikb.user_actions_kb(user_db_id, user.telegram_id, user.status.value, user.tag.value),
    )
    await call.answer()


# ============== Inbox ==============
@router.callback_query(F.data.startswith("adm:inbox"))
async def cb_inbox(call: CallbackQuery, session) -> None:
    parts = (call.data or "").split(":")
    page = 0
    if len(parts) >= 3 and parts[2].isdigit():
        page = int(parts[2])
    # Oxirgi xabari bo'lgan userlar
    sub = (
        select(
            User.id,
            User.anonymous_id,
            User.username,
            User.telegram_id,
            User.last_seen,
            func.max(DbMessage.created_at).label("last_msg"),
            func.sum(
                func.iif(
                    (DbMessage.direction == MessageDirection.INCOMING) & (DbMessage.is_read.is_(False)),
                    1, 0
                )
            ).label("unread"),
        )
        .join(DbMessage, DbMessage.user_id == User.id, isouter=True)
        .group_by(User.id)
        .order_by(func.max(DbMessage.created_at).desc().nullslast())
        .limit(500)
    )
    res = await session.execute(sub)
    rows = res.all()
    threads = [
        {
            "id": r.id,
            "anon_id": r.anonymous_id,
            "telegram_id": r.telegram_id,
            "last_time": fmt_dt(r.last_msg),
            "unread": int(r.unread or 0),
        }
        for r in rows
    ]
    if not threads:
        await call.answer("Inbox bo'sh.", show_alert=True)
        return
    per_page = 8
    total_pages = (len(threads) + per_page - 1) // per_page
    text = f"💬 <b>Inbox</b> — {len(threads)} ta foydalanuvchi, sahifa {page+1}/{total_pages}"
    await call.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=ikb.inbox_kb(threads, page, per_page),
    )
    await call.answer()


# ============== Search ==============
@router.callback_query(F.data == "adm:search")
async def cb_search(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminStates.search_user)
    await call.message.edit_text(
        "🔍 <b>Qidiruv</b>\n\nIsm, username yoki anonim ID bo'yicha yozing:",
        parse_mode="HTML",
        reply_markup=ikb.back_home_kb(),
    )
    await call.answer()


@router.message(AdminStates.search_user, F.text)
async def search_user(message: Message, state: FSMContext, session) -> None:
    q = (message.text or "").strip().lstrip("@")
    if not q:
        return
    res = await session.execute(
        select(User).where(
            or_(
                User.username.ilike(f"%{q}%"),
                User.full_name.ilike(f"%{q}%"),
                User.anonymous_id.ilike(f"%{q}%"),
            )
        ).limit(20)
    )
    users = res.scalars().all()
    if not users:
        await message.answer("🔍 Hech narsa topilmadi.", reply_markup=ikb.back_home_kb())
        return
    rows = []
    for u in users:
        rows.append([InlineKeyboardButton(
            text=f"{u.anonymous_id} • {u.full_name} • @{u.username or '—'}",
            callback_data=f"adm:user:{u.id}",
        )])
    rows.append([InlineKeyboardButton(text="◀️ Bosh sahifa", callback_data="adm:home")])
    await message.answer(
        f"🔍 <b>{len(users)} ta natija topildi:</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )
    await state.set_state(AdminStates.menu)


# ============== Reply to user ==============
@router.callback_query(F.data.startswith("adm:reply:"))
async def cb_reply(call: CallbackQuery, state: FSMContext) -> None:
    telegram_id = int(call.data.split(":")[2])
    await state.set_state(AdminStates.reply_to)
    await state.update_data(reply_to_id=telegram_id)
    await call.message.edit_text(
        f"✉️ <b>Javob yozish</b>\n\nFoydalanuvchi: <code>{telegram_id}</code>\n\nXabaringizni yozing:",
        parse_mode="HTML",
        reply_markup=ikb.back_home_kb(),
    )
    await call.answer()


@router.message(AdminStates.reply_to, F.text)
async def send_reply(message: Message, state: FSMContext, session) -> None:
    data = await state.get_data()
    tid = data.get("reply_to_id")
    if not tid:
        await message.answer("⚠️ Xatolik.")
        return
    text = message.text or ""
    if not text.strip():
        return
    # DB ga saqlash
    res = await session.execute(select(User).where(User.telegram_id == tid))
    user = res.scalar_one_or_none()
    if not user:
        await message.answer("⚠️ Foydalanuvchi topilmadi.")
        await state.set_state(AdminStates.menu)
        return
    db_msg = DbMessage(
        user_id=user.id,
        direction=MessageDirection.OUTGOING,
        text=text,
    )
    session.add(db_msg)
    # user'ga yuborish
    try:
        await message.bot.send_message(
            chat_id=tid,
            text=f"💌 <b>Admin javobi:</b>\n\n{escape(text)}",
            parse_mode="HTML",
        )
        await log_audit(session, config.ADMIN_ID, "reply", tid, text[:120])
        await message.answer("✅ Yuborildi.")
    except Exception as e:
        await message.answer(f"❌ Yuborilmadi: {e}")
    await state.set_state(AdminStates.menu)


# ============== Block / Unblock ==============
@router.callback_query(F.data.startswith("adm:block:"))
async def cb_block(call: CallbackQuery, session) -> None:
    user_db_id = int(call.data.split(":")[2])
    user = await session.get(User, user_db_id)
    if not user:
        await call.answer("Topilmadi.", show_alert=True)
        return
    user.status = UserStatus.BLOCKED
    user.tag = UserTag.BLOCKED
    await log_audit(session, config.ADMIN_ID, "block", user.telegram_id, "")
    await call.answer("🚫 Bloklandi", show_alert=True)
    text = (
        f"👤 <b>{escape(user.anonymous_id)}</b>\n\n"
        f"📛 Ism: {escape(user.full_name)}\n"
        f"📛 Username: @{escape(user.username or '—')}\n"
        f"🆔 Telegram ID: <code>{user.telegram_id}</code>\n"
        f"🌐 Til: {user.language}\n"
        f"🏷 Teg: <b>{user.tag.value}</b>\n"
        f"📊 Status: {user.status.value}\n"
        f"⚠️ Warnings: {user.warnings}\n"
        f"💬 Xabarlar: {user.message_count}\n"
        f"🕐 Ro'yxatdan: {fmt_dt(user.created_at)}\n"
        f"👁 Oxirgi: {fmt_dt(user.last_seen)}\n"
    )
    await call.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=ikb.user_actions_kb(user_db_id, user.telegram_id, user.status.value, user.tag.value),
    )


@router.callback_query(F.data.startswith("adm:unblock:"))
async def cb_unblock(call: CallbackQuery, session) -> None:
    user_db_id = int(call.data.split(":")[2])
    user = await session.get(User, user_db_id)
    if not user:
        await call.answer("Topilmadi.", show_alert=True)
        return
    user.status = UserStatus.ACTIVE
    user.tag = UserTag.REGULAR
    user.warnings = 0
    await log_audit(session, config.ADMIN_ID, "unblock", user.telegram_id, "")
    await call.answer("✅ Blokdan chiqarildi", show_alert=True)
    text = (
        f"👤 <b>{escape(user.anonymous_id)}</b>\n\n"
        f"📛 Ism: {escape(user.full_name)}\n"
        f"📛 Username: @{escape(user.username or '—')}\n"
        f"🆔 Telegram ID: <code>{user.telegram_id}</code>\n"
        f"🌐 Til: {user.language}\n"
        f"🏷 Teg: <b>{user.tag.value}</b>\n"
        f"📊 Status: {user.status.value}\n"
        f"⚠️ Warnings: {user.warnings}\n"
        f"💬 Xabarlar: {user.message_count}\n"
        f"🕐 Ro'yxatdan: {fmt_dt(user.created_at)}\n"
        f"👁 Oxirgi: {fmt_dt(user.last_seen)}\n"
    )
    await call.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=ikb.user_actions_kb(user_db_id, user.telegram_id, user.status.value, user.tag.value),
    )


# ============== Warning ==============
@router.callback_query(F.data.startswith("adm:warn:"))
async def cb_warn(call: CallbackQuery, state: FSMContext) -> None:
    user_db_id = int(call.data.split(":")[2])
    user = await session.get(User, user_db_id)
    if not user:
        await call.answer("Topilmadi.", show_alert=True)
        return
    user.warnings += 1
    if user.warnings >= 3:
        user.status = UserStatus.BLOCKED
    # user'ga xabar berish
    try:
        await call.bot.send_message(
            chat_id=user.telegram_id,
            text=f"⚠️ Sizga ogohlantirish berildi ({user.warnings}/3). Qoidalarga rioya qiling.",
        )
    except Exception:
        pass
    await log_audit(session, config.ADMIN_ID, "warn", user.telegram_id, f"warning #{user.warnings}")
    await call.answer(f"⚠️ Warning #{user.warnings} berildi", show_alert=True)
    text = (
        f"👤 <b>{escape(user.anonymous_id)}</b>\n\n"
        f"📛 Ism: {escape(user.full_name)}\n"
        f"📛 Username: @{escape(user.username or '—')}\n"
        f"🆔 Telegram ID: <code>{user.telegram_id}</code>\n"
        f"🌐 Til: {user.language}\n"
        f"🏷 Teg: <b>{user.tag.value}</b>\n"
        f"📊 Status: {user.status.value}\n"
        f"⚠️ Warnings: {user.warnings}\n"
        f"💬 Xabarlar: {user.message_count}\n"
        f"🕐 Ro'yxatdan: {fmt_dt(user.created_at)}\n"
        f"👁 Oxirgi: {fmt_dt(user.last_seen)}\n"
    )
    await call.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=ikb.user_actions_kb(user_db_id, user.telegram_id, user.status.value, user.tag.value),
    )


# ============== Tag change ==============
@router.callback_query(F.data.startswith("adm:tag:"))
async def cb_tag(call: CallbackQuery, session) -> None:
    parts = (call.data or "").split(":")
    # adm:tag:{user_db_id}:{next_tag}  yoki  adm:tag:list:{tag}
    if len(parts) >= 4 and parts[2] == "list":
        # tag bo'yicha filter
        tag = parts[3]
        try:
            tag_enum = UserTag(tag)
        except ValueError:
            await call.answer("Xato tag", show_alert=True)
            return
        res = await session.execute(select(User).where(User.tag == tag_enum).limit(50))
        users = res.scalars().all()
        if not users:
            await call.answer("Bu tegda foydalanuvchilar yo'q.", show_alert=True)
            return
        rows = [[InlineKeyboardButton(
            text=f"{u.anonymous_id} • {u.full_name[:20]}",
            callback_data=f"adm:user:{u.id}",
        )] for u in users]
        rows.append([InlineKeyboardButton(text="◀️ Bosh sahifa", callback_data="adm:home")])
        await call.message.edit_text(
            f"🏷 <b>{tag}</b> — {len(users)} ta foydalanuvchi",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
        )
        await call.answer()
        return

    if len(parts) < 4:
        return
    user_db_id = int(parts[2])
    new_tag = parts[3]
    user = await session.get(User, user_db_id)
    if not user:
        await call.answer("Topilmadi.", show_alert=True)
        return
    try:
        user.tag = UserTag(new_tag)
    except ValueError:
        await call.answer("Xato tag", show_alert=True)
        return
    await log_audit(session, config.ADMIN_ID, "tag_change", user.telegram_id, new_tag)
    await call.answer(f"🏷 Teg o'zgartirildi: {new_tag}", show_alert=True)
    text = (
        f"👤 <b>{escape(user.anonymous_id)}</b>\n\n"
        f"📛 Ism: {escape(user.full_name)}\n"
        f"📛 Username: @{escape(user.username or '—')}\n"
        f"🆔 Telegram ID: <code>{user.telegram_id}</code>\n"
        f"🌐 Til: {user.language}\n"
        f"🏷 Teg: <b>{user.tag.value}</b>\n"
        f"📊 Status: {user.status.value}\n"
        f"⚠️ Warnings: {user.warnings}\n"
        f"💬 Xabarlar: {user.message_count}\n"
        f"🕐 Ro'yxatdan: {fmt_dt(user.created_at)}\n"
        f"👁 Oxirgi: {fmt_dt(user.last_seen)}\n"
    )
    await call.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=ikb.user_actions_kb(user_db_id, user.telegram_id, user.status.value, user.tag.value),
    )


@router.callback_query(F.data == "adm:tags")
async def cb_tags(call: CallbackQuery) -> None:
    await call.message.edit_text(
        "🏷 <b>Teglar bo'yicha</b>",
        parse_mode="HTML",
        reply_markup=ikb.tags_kb(),
    )
    await call.answer()


# ============== Broadcast ==============
@router.callback_query(F.data == "adm:broadcast")
async def cb_broadcast(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminStates.broadcast)
    await call.message.edit_text(
        "📢 <b>Broadcast</b>\n\nKimga yuborishni tanlang:",
        parse_mode="HTML",
        reply_markup=ikb.broadcast_kb(),
    )
    await call.answer()


@router.callback_query(F.data.startswith("adm:bcast:"))
async def cb_bcast_target(call: CallbackQuery, state: FSMContext) -> None:
    target = (call.data or "").split(":")[2]
    await state.update_data(bcast_target=target)
    await call.message.edit_text(
        f"📢 <b>Broadcast</b>\n\nAuditoriya: <b>{target}</b>\n\nYuboriladigan xabarni yozing (HTML qo'llab-quvvatlanadi):",
        parse_mode="HTML",
        reply_markup=ikb.back_home_kb(),
    )
    await call.answer()


@router.message(AdminStates.broadcast, F.text)
async def send_broadcast(message: Message, state: FSMContext, session) -> None:
    data = await state.get_data()
    target = data.get("bcast_target", "all")
    text = message.text or ""
    if not text.strip():
        return

    q = select(User).where(User.status == UserStatus.ACTIVE)
    if target == "vip":
        q = q.where(User.tag == UserTag.VIP)
    elif target == "new":
        q = q.where(User.tag == UserTag.NEW)
    elif target == "active":
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        q = q.where(User.last_seen >= cutoff)
    res = await session.execute(q)
    users = res.scalars().all()

    sent = 0
    failed = 0
    for u in users:
        try:
            await message.bot.send_message(
                chat_id=u.telegram_id,
                text=f"📢 <b>{config.BRAND_NAME}</b>\n\n{escape(text)}",
                parse_mode="HTML",
            )
            sent += 1
        except Exception:
            failed += 1
    await log_audit(session, config.ADMIN_ID, "broadcast", None, f"target={target} sent={sent} failed={failed}")
    await message.answer(
        f"✅ Broadcast yakunlandi.\n\n📤 Yuborildi: <b>{sent}</b>\n❌ Xatolik: <b>{failed}</b>",
        parse_mode="HTML",
        reply_markup=ikb.back_home_kb(),
    )
    await state.set_state(AdminStates.menu)


# ============== Settings ==============
@router.callback_query(F.data == "adm:settings")
async def cb_settings(call: CallbackQuery, session) -> None:
    val = await get_setting(session, "auto_reply", str(config.AUTO_REPLY_ENABLED))
    autoreply = val.lower() == "true"
    text = (
        "⚙️ <b>Sozlamalar</b>\n\n"
        f"🤖 Auto-reply: {'✅ Yoniq' if autoreply else '❌ Oʻchiq'}\n"
    )
    await call.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=ikb.settings_kb(autoreply, config.AUTO_REPLY_TEXT),
    )
    await call.answer()


@router.callback_query(F.data == "adm:toggle:autoreply")
async def cb_toggle_autoreply(call: CallbackQuery, session) -> None:
    cur = await get_setting(session, "auto_reply", str(config.AUTO_REPLY_ENABLED))
    new_val = "false" if cur.lower() == "true" else "true"
    await set_setting(session, "auto_reply", new_val)
    await log_audit(session, config.ADMIN_ID, "toggle_autoreply", None, new_val)
    await cb_settings(call, session)


@router.callback_query(F.data == "adm:set:autoreply")
async def cb_set_autoreply(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminStates.set_autoreply)
    await call.message.edit_text(
        "✏️ Yangi auto-reply matnini yozing:",
        reply_markup=ikb.back_home_kb(),
    )
    await call.answer()


@router.message(AdminStates.set_autoreply, F.text)
async def save_autoreply(message: Message, state: FSMContext, session) -> None:
    txt = message.text or ""
    await set_setting(session, "auto_reply_text", txt)
    await log_audit(session, config.ADMIN_ID, "set_autoreply", None, txt[:100])
    await message.answer("✅ Saqlandi.", reply_markup=ikb.back_home_kb())
    await state.set_state(AdminStates.menu)


# ============== Analytics ==============
@router.callback_query(F.data == "adm:analytics")
async def cb_analytics(call: CallbackQuery, session) -> None:
    s = await A.full_stats(session)
    top = await A.top_users_by_messages(session, 5)
    text = (
        "📈 <b>Analytics</b>\n\n"
        f"👥 Jami userlar: <b>{s['users_total']}</b>\n"
        f"🆕 Faol 24h: <b>{s['users_24h']}</b>\n"
        f"🟢 Onlayn: <b>{s['online_now']}</b>\n"
        f"💬 Bugun xabarlar: <b>{s['messages_today']}</b>\n"
        f"🔔 O'qilmagan: <b>{s['unread']}</b>\n"
    )
    if top:
        text += "\n🏆 <b>Top 5 foydalanuvchi:</b>\n"
        for i, (u, c) in enumerate(top, 1):
            text += f"{i}. <b>{escape(u.anonymous_id)}</b> — {c} xabar\n"
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=ikb.back_home_kb())
    await call.answer()


# ============== Export ==============
@router.callback_query(F.data == "adm:export")
async def cb_export(call: CallbackQuery) -> None:
    await call.message.edit_text(
        "💾 <b>Export</b>\n\nFormatni tanlang:",
        parse_mode="HTML",
        reply_markup=ikb.export_kb(),
    )
    await call.answer()


@router.callback_query(F.data == "adm:export:json")
async def export_json(call: CallbackQuery, session) -> None:
    res = await session.execute(select(User))
    users = res.scalars().all()
    data = [
        {
            "id": u.id,
            "telegram_id": u.telegram_id,
            "username": u.username,
            "full_name": u.full_name,
            "anonymous_id": u.anonymous_id,
            "language": u.language,
            "status": u.status.value,
            "tag": u.tag.value,
            "warnings": u.warnings,
            "message_count": u.message_count,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]
    bio = io.BytesIO(json.dumps(data, ensure_ascii=False, indent=2).encode())
    bio.name = "users.json"
    await call.message.answer_document(
        document=("users.json", bio),
        caption="📥 Foydalanuvchilar (JSON)",
    )
    await call.answer()


@router.callback_query(F.data == "adm:export:csv")
async def export_csv(call: CallbackQuery, session) -> None:
    res = await session.execute(select(User))
    users = res.scalars().all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "telegram_id", "username", "full_name", "anonymous_id", "language", "status", "tag", "messages", "warnings", "created_at"])
    for u in users:
        writer.writerow([u.id, u.telegram_id, u.username, u.full_name, u.anonymous_id, u.language, u.status.value, u.tag.value, u.message_count, u.warnings, u.created_at])
    bio = io.BytesIO(buf.getvalue().encode())
    bio.name = "users.csv"
    await call.message.answer_document(
        document=("users.csv", bio),
        caption="📥 Foydalanuvchilar (CSV)",
    )
    await call.answer()


# ============== Warnings panel ==============
@router.callback_query(F.data == "adm:warnings")
async def cb_warnings(call: CallbackQuery, session) -> None:
    res = await session.execute(
        select(User).where(User.warnings > 0).order_by(User.warnings.desc()).limit(20)
    )
    users = res.scalars().all()
    if not users:
        await call.answer("Ogohlantirish olganlar yo'q.", show_alert=True)
        return
    rows = []
    for u in users:
        icon = "🚫" if u.status == UserStatus.BLOCKED else "⚠️"
        rows.append([InlineKeyboardButton(
            text=f"{icon} {u.anonymous_id} — {u.warnings}/3 • {u.full_name[:20]}",
            callback_data=f"adm:user:{u.id}",
        )])
    rows.append([InlineKeyboardButton(text="◀️ Bosh sahifa", callback_data="adm:home")])
    await call.message.edit_text(
        f"⚠️ <b>Ogohlantirishlar</b> — {len(users)} ta",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )
    await call.answer()


# ============== Helpers ==============
async def log_audit(session: AsyncSession, actor_id: int, action: str, target_id: int | None, details: str) -> None:
    session.add(AuditLog(actor_id=actor_id, action=action, target_id=target_id, details=details[:500]))


async def get_setting(session: AsyncSession, key: str, default: str = "") -> str:
    res = await session.execute(select(AdminSettings).where(AdminSettings.key == key))
    row = res.scalar_one_or_none()
    return row.value if row else default


async def set_setting(session: AsyncSession, key: str, value: str) -> None:
    res = await session.execute(select(AdminSettings).where(AdminSettings.key == key))
    row = res.scalar_one_or_none()
    if row:
        row.value = value
    else:
        session.add(AdminSettings(key=key, value=value))


# No-op callback (pagination uchun)
@router.callback_query(F.data == "noop")
async def cb_noop(call: CallbackQuery) -> None:
    await call.answer()
