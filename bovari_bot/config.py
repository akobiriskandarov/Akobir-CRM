"""Sozlamalar: barcha qiymatlar .env faylidan yoki muhit o'zgaruvchilaridan olinadi."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _int_set(raw: str) -> frozenset[int]:
    out: set[int] = set()
    for part in raw.replace(";", ",").split(","):
        part = part.strip()
        if part:
            out.add(int(part))
    return frozenset(out)


def _bool(raw: str | None, default: bool) -> bool:
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "ha", "on"}


@dataclass(frozen=True)
class Settings:
    telegram_token: str
    # Bo'sh bo'lsa — botdan hamma foydalana oladi (tavsiya etilmaydi: API xarajati).
    allowed_user_ids: frozenset[int] = field(default_factory=frozenset)
    admin_user_ids: frozenset[int] = field(default_factory=frozenset)
    model: str = "claude-opus-5-5"
    effort: str = "medium"
    max_tokens: int = 16000
    history_turns: int = 12
    web_search: bool = True
    db_path: str = "data/bovari.db"
    bot_name: str = "Bovari Agency"


def load_settings() -> Settings:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN topilmadi. .env.example faylidan nusxa olib, .env yarating."
        )
    if not (os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")):
        raise RuntimeError("ANTHROPIC_API_KEY topilmadi. .env faylga qo'shing.")

    admins = _int_set(os.getenv("ADMIN_USER_IDS", ""))
    allowed = _int_set(os.getenv("ALLOWED_USER_IDS", "")) | admins

    return Settings(
        telegram_token=token,
        allowed_user_ids=allowed,
        admin_user_ids=admins,
        model=os.getenv("CLAUDE_MODEL", "claude-opus-5-5").strip(),
        effort=os.getenv("CLAUDE_EFFORT", "medium").strip(),
        max_tokens=int(os.getenv("CLAUDE_MAX_TOKENS", "16000")),
        history_turns=int(os.getenv("HISTORY_TURNS", "12")),
        web_search=_bool(os.getenv("WEB_SEARCH"), True),
        db_path=os.getenv("DB_PATH", "data/bovari.db").strip(),
        bot_name=os.getenv("BOT_NAME", "Bovari Agency").strip(),
    )
