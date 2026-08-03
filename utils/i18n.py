"""i18n — ko'p tilli tarjimalar (lightweight, RAM-based)."""
from __future__ import annotations

import json
import os
from typing import Any

_LOCALES: dict[str, dict[str, Any]] = {}
_LANGS = ("uz", "ru", "en")
_DEFAULT = "uz"


def _load_locale(code: str) -> dict:
    if code in _LOCALES:
        return _LOCALES[code]
    path = os.path.join(os.path.dirname(__file__), "..", "locales", f"{code}.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    _LOCALES[code] = data
    return data


def t(key: str, lang: str = _DEFAULT, **kwargs) -> str:
    """Tarjima olish: t('welcome', 'uz', name='Firdavs')."""
    if lang not in _LANGS:
        lang = _DEFAULT
    data = _load_locale(lang) or _load_locale(_DEFAULT)
    text = data.get(key) or _load_locale(_DEFAULT).get(key, key)
    try:
        return text.format(**kwargs)
    except (KeyError, IndexError):
        return text


def available_languages() -> list[str]:
    return list(_LANGS)


__all__ = ["t", "available_languages"]
