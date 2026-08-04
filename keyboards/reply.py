"""Foydalanuvchi reply keyboardlari."""
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_reply_kb(lang: str = "uz") -> ReplyKeyboardMarkup:
    if lang == "en":
        return ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="💬 Chat"), KeyboardButton(text="👤 Profile")],
            [KeyboardButton(text="📊 Status"), KeyboardButton(text="⭐ Feedback")],
            [KeyboardButton(text="🌐 Language"), KeyboardButton(text="ℹ️ Help")],
        ], resize_keyboard=True)
    if lang == "ru":
        return ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="💬 Чат"), KeyboardButton(text="👤 Профиль")],
            [KeyboardButton(text="📊 Статус"), KeyboardButton(text="⭐ Оценка")],
            [KeyboardButton(text="🌐 Язык"), KeyboardButton(text="ℹ️ Помощь")],
        ], resize_keyboard=True)
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="💬 Chat"), KeyboardButton(text="👤 Profil")],
        [KeyboardButton(text="📊 Status"), KeyboardButton(text="⭐ Baho")],
        [KeyboardButton(text="🌐 Til"), KeyboardButton(text="ℹ️ Yordam")],
    ], resize_keyboard=True)


def language_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🇺🇿 O'zbek"), KeyboardButton(text="🇷🇺 Русский")],
        [KeyboardButton(text="🇬🇧 English")],
        [KeyboardButton(text="◀️ Bekor")],
    ], resize_keyboard=True)


def feedback_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="⭐"), KeyboardButton(text="⭐⭐")],
        [KeyboardButton(text="⭐⭐⭐"), KeyboardButton(text="⭐⭐⭐⭐")],
        [KeyboardButton(text="⭐⭐⭐⭐⭐"), KeyboardButton(text="⏭ O'tkazib yuborish")],
    ], resize_keyboard=True, one_time_keyboard=True)


def cancel_kb(lang: str = "uz") -> ReplyKeyboardMarkup:
    label = "◀️ Bekor" if lang == "uz" else ("◀️ Отмена" if lang == "ru" else "◀️ Cancel")
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=label)]], resize_keyboard=True, one_time_keyboard=True)
