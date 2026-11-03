"""Claude markdown javobini Telegram HTML formatiga o'tkazish va bo'laklash."""

from __future__ import annotations

import html
import re

TELEGRAM_LIMIT = 4096
CHUNK_SIZE = 3800  # HTML teglar uchun zaxira

_FENCE = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)
_INLINE_CODE = re.compile(r"`([^`\n]+)`")
_BOLD = re.compile(r"\*\*(.+?)\*\*|__(.+?)__", re.DOTALL)
_ITALIC = re.compile(r"(?<![\w*])\*(?!\s)([^*\n]+?)(?<!\s)\*(?![\w*])")
_STRIKE = re.compile(r"~~(.+?)~~")
_LINK = re.compile(r"\[([^\]\n]+)\]\((https?://[^\s)]+)\)")
_HEADER = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", re.MULTILINE)
_BULLET = re.compile(r"^(\s*)[-*+]\s+", re.MULTILINE)
_HR = re.compile(r"^\s*([-*_])(\s*\1){2,}\s*$", re.MULTILINE)


def md_to_tg_html(text: str) -> str:
    """Oddiy markdown → Telegram qo'llab-quvvatlaydigan HTML (b, i, s, code, pre, a)."""
    placeholders: list[str] = []

    def stash(fragment: str) -> str:
        placeholders.append(fragment)
        return f"\x00{len(placeholders) - 1}\x00"

    # 1) Kod bloklari va inline kod — ichini formatlamaymiz.
    text = _FENCE.sub(lambda m: stash(f"<pre>{html.escape(m.group(1).rstrip())}</pre>"), text)
    text = _INLINE_CODE.sub(lambda m: stash(f"<code>{html.escape(m.group(1))}</code>"), text)
    # 2) Havolalar.
    text = _LINK.sub(
        lambda m: stash(
            f'<a href="{html.escape(m.group(2), quote=True)}">{html.escape(m.group(1))}</a>'
        ),
        text,
    )
    # 3) Qolgan matnni xavfsiz qilish.
    text = html.escape(text, quote=False)
    # 4) Blok elementlari.
    text = _HR.sub("", text)
    text = _HEADER.sub(lambda m: f"<b>{m.group(1)}</b>", text)
    text = _BULLET.sub(lambda m: f"{m.group(1)}• ", text)
    # 5) Inline formatlash.
    text = _BOLD.sub(lambda m: f"<b>{m.group(1) or m.group(2)}</b>", text)
    text = _STRIKE.sub(lambda m: f"<s>{m.group(1)}</s>", text)
    text = _ITALIC.sub(lambda m: f"<i>{m.group(1)}</i>", text)
    # 6) Joy egallovchilarni qaytarish.
    text = re.sub(r"\x00(\d+)\x00", lambda m: placeholders[int(m.group(1))], text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_markdown(text: str, limit: int = CHUNK_SIZE) -> list[str]:
    """Matnni paragraf/qator chegarasida bo'laklaydi; kod bloklarini buzmaydi."""
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    current = ""
    in_fence = False

    def flush() -> None:
        nonlocal current
        if current.strip():
            piece = current.rstrip()
            if in_fence:
                piece += "\n```"
            chunks.append(piece)
        current = "```\n" if in_fence else ""

    for line in text.split("\n"):
        # Juda uzun bitta qator — qattiq bo'lamiz.
        while len(line) > limit:
            if current.strip():
                flush()
            chunks.append(line[:limit])
            line = line[limit:]
        if len(current) + len(line) + 1 > limit:
            flush()
        current += line + "\n"
        if line.strip().startswith("```"):
            in_fence = not in_fence
    if current.strip():
        chunks.append(current.rstrip())
    return chunks
