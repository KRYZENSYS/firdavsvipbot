"""Admin paneli inline keyboardlari."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_admin_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Statistika", callback_data="adm:stats"),
         InlineKeyboardButton(text="👥 Foydalanuvchilar", callback_data="adm:users")],
        [InlineKeyboardButton(text="💬 Inbox", callback_data="adm:inbox"),
         InlineKeyboardButton(text="🔍 Qidiruv", callback_data="adm:search")],
        [InlineKeyboardButton(text="📢 Broadcast", callback_data="adm:broadcast"),
         InlineKeyboardButton(text="⚠️ Warnings", callback_data="adm:warnings")],
        [InlineKeyboardButton(text="🏷 Teglar", callback_data="adm:tags"),
         InlineKeyboardButton(text="📈 Analytics", callback_data="adm:analytics")],
        [InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data="adm:settings"),
         InlineKeyboardButton(text="💾 Export", callback_data="adm:export")],
        [InlineKeyboardButton(text="🚪 Chiqish", callback_data="adm:exit")],
    ])


def stats_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Yangilash", callback_data="adm:stats")],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm:home")],
    ])


def users_list_kb(users: list, page: int = 0, per_page: int = 8) -> InlineKeyboardMarkup:
    rows = []
    start = page * per_page
    end = start + per_page
    page_users = users[start:end]
    for u in page_users:
        rows.append([InlineKeyboardButton(
            text=f"👤 {u.anonymous_id} • {u.full_name[:20]} • #{u.telegram_id}",
            callback_data=f"adm:user:{u.id}",
        )])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"adm:users:{page-1}"))
    nav.append(InlineKeyboardButton(text=f"📄 {page+1}/{(len(users)+per_page-1)//per_page}", callback_data="noop"))
    if end < len(users):
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"adm:users:{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(text="◀️ Bosh sahifa", callback_data="adm:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def user_actions_kb(user_db_id: int, telegram_id: int, status: str, tag: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="💬 Inbox (suhbatlar)", callback_data=f"adm:user:msg:{user_db_id}")],
        [InlineKeyboardButton(text="✉️ Javob berish", callback_data=f"adm:reply:{telegram_id}")],
    ]
    if status == "blocked":
        rows.append([InlineKeyboardButton(text="✅ Blokdan chiqarish", callback_data=f"adm:unblock:{user_db_id}")])
    else:
        rows.append([InlineKeyboardButton(text="🚫 Bloklash", callback_data=f"adm:block:{user_db_id}")])
    rows.append([InlineKeyboardButton(text="⚠️ Warn", callback_data=f"adm:warn:{user_db_id}")])
    # tag switcher
    next_tag = "vip" if tag != "vip" else "regular"
    rows.append([InlineKeyboardButton(text=f"🏷 Tegni o'zgartirish: → {next_tag}", callback_data=f"adm:tag:{user_db_id}:{next_tag}")])
    rows.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm:users")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def inbox_kb(threads: list, page: int = 0, per_page: int = 8) -> InlineKeyboardMarkup:
    rows = []
    start = page * per_page
    end = start + per_page
    page_threads = threads[start:end]
    for t in page_threads:
        rows.append([InlineKeyboardButton(
            text=f"💬 {t['anon_id']} • {t['unread']} ta yangi • oxirgi: {t['last_time']}",
            callback_data=f"adm:user:{t['id']}",
        )])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"adm:inbox:{page-1}"))
    if end < len(threads):
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"adm:inbox:{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(text="◀️ Bosh sahifa", callback_data="adm:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def user_messages_kb(user_db_id: int, telegram_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✉️ Javob berish", callback_data=f"adm:reply:{telegram_id}")],
        [InlineKeyboardButton(text="🚫 Bloklash", callback_data=f"adm:block:{user_db_id}")],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm:users")],
    ])


def broadcast_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Hammaga", callback_data="adm:bcast:all")],
        [InlineKeyboardButton(text="⭐ VIP", callback_data="adm:bcast:vip")],
        [InlineKeyboardButton(text="🆕 Yangi", callback_data="adm:bcast:new")],
        [InlineKeyboardButton(text="🟢 Faol (24h)", callback_data="adm:bcast:active")],
        [InlineKeyboardButton(text="◀️ Bekor", callback_data="adm:home")],
    ])


def confirm_kb(action: str, target: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Ha, davom etish", callback_data=f"adm:{action}:yes:{target}")],
        [InlineKeyboardButton(text="❌ Yo'q, bekor", callback_data="adm:home")],
    ])


def back_home_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Bosh sahifa", callback_data="adm:home")],
    ])


def settings_kb(autoreply: bool, autoreply_text: str) -> InlineKeyboardMarkup:
    status = "✅ Yoniq" if autoreply else "❌ O'chiq"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🤖 Auto-reply: {status}", callback_data="adm:toggle:autoreply")],
        [InlineKeyboardButton(text="✏️ Auto-reply matnini o'zgartirish", callback_data="adm:set:autoreply")],
        [InlineKeyboardButton(text="◀️ Bosh sahifa", callback_data="adm:home")],
    ])


def export_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 JSON yuklash", callback_data="adm:export:json")],
        [InlineKeyboardButton(text="📊 CSV yuklash", callback_data="adm:export:csv")],
        [InlineKeyboardButton(text="◀️ Bosh sahifa", callback_data="adm:home")],
    ])


def tags_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ VIP foydalanuvchilar", callback_data="adm:tag:list:vip")],
        [InlineKeyboardButton(text="👥 Oddiy", callback_data="adm:tag:list:regular")],
        [InlineKeyboardButton(text="🆕 Yangi", callback_data="adm:tag:list:new")],
        [InlineKeyboardButton(text="🚫 Blocked", callback_data="adm:tag:list:blocked")],
        [InlineKeyboardButton(text="◀️ Bosh sahifa", callback_data="adm:home")],
    ])


def pagination_kb(prefix: str, page: int, total_pages: int) -> InlineKeyboardMarkup:
    rows = []
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"adm:{prefix}:{page-1}"))
    nav.append(InlineKeyboardButton(text=f"📄 {page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"adm:{prefix}:{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(text="◀️ Bosh sahifa", callback_data="adm:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
