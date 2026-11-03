"""Bovari Agency Telegram boti: 7 ta AI agent bitta botda."""

from __future__ import annotations

import asyncio
import base64
import logging
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from functools import wraps
from typing import Any, Awaitable, Callable

from telegram import (
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.constants import ChatAction, ChatType, ParseMode
from telegram.error import BadRequest, TelegramError
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .agents import AGENTS, DEFAULT_AGENT_KEY, SYNTHESIS_INSTRUCTION, Agent
from .config import Settings
from .formatting import md_to_tg_html, split_markdown
from .llm import ClaudeClient, LLMError, Reply
from .storage import Storage

log = logging.getLogger(__name__)

TEAM_BUTTON = "👥 Jamoa (bir nechta agent)"
NEW_CHAT_BUTTON = "🔄 Yangi suhbat"
TEXT_FILE_EXT = (".txt", ".csv", ".tsv", ".md", ".json", ".srt", ".vtt")
MAX_TEXT_FILE_CHARS = 300_000
MAX_STORED_FILE_CHARS = 30_000
IMAGE_MIME = {"image/jpeg", "image/png", "image/gif", "image/webp"}

# Claude Opus 5.5 narxlari (USD / 1M token) — /statistika uchun taxminiy hisob.
PRICE_INPUT, PRICE_OUTPUT, PRICE_CACHE_READ = 4.0, 20.0, 0.20

Handler = Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[Any]]


class BovariBot:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.storage = Storage(settings.db_path)
        self.llm = ClaudeClient(settings)
        self._user_locks: dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)

    # ================================================================ utils
    def _allowed(self, user_id: int) -> bool:
        return not self.settings.allowed_user_ids or user_id in self.settings.allowed_user_ids

    def _current_agent(self, user_id: int) -> Agent:
        key = self.storage.get_agent(user_id) or DEFAULT_AGENT_KEY
        return AGENTS.get(key, AGENTS[DEFAULT_AGENT_KEY])

    @staticmethod
    def _main_keyboard() -> ReplyKeyboardMarkup:
        labels = [a.label for a in AGENTS.values()]
        rows = [[KeyboardButton(x) for x in labels[i : i + 2]] for i in range(0, len(labels), 2)]
        rows.append([KeyboardButton(TEAM_BUTTON), KeyboardButton(NEW_CHAT_BUTTON)])
        return ReplyKeyboardMarkup(rows, resize_keyboard=True, is_persistent=True)

    @staticmethod
    def _agents_inline() -> InlineKeyboardMarkup:
        buttons = [InlineKeyboardButton(a.label, callback_data=f"agent:{a.key}") for a in AGENTS.values()]
        rows = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
        return InlineKeyboardMarkup(rows)

    @asynccontextmanager
    async def _typing(self, chat_id: int, bot):
        """Javob tayyorlanayotganda 'yozmoqda…' holatini ushlab turadi."""

        async def loop() -> None:
            while True:
                try:
                    await bot.send_chat_action(chat_id, ChatAction.TYPING)
                except TelegramError:
                    pass
                await asyncio.sleep(4.5)

        task = asyncio.create_task(loop())
        try:
            yield
        finally:
            task.cancel()

    async def _send_long(self, message: Message, text: str, header: str | None = None) -> None:
        if header:
            text = f"{header}\n\n{text}"
        for chunk in split_markdown(text):
            try:
                await message.reply_text(
                    md_to_tg_html(chunk),
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                )
            except BadRequest:
                # HTML parsingda muammo bo'lsa — oddiy matn sifatida yuboramiz.
                await message.reply_text(chunk, disable_web_page_preview=True)

    @staticmethod
    def _format_reply(reply: Reply) -> str:
        text = reply.text
        if reply.sources:
            links = "\n".join(f"• [{title}]({url})" for title, url in reply.sources[:6])
            text += f"\n\n**Manbalar:**\n{links}"
        if reply.truncated:
            text += "\n\n_(Javob uzunlik chegarasiga yetdi. Davomi uchun «davom et» deb yozing.)_"
        return text

    def _log_usage(self, user_id: int, agent_key: str, reply: Reply) -> None:
        self.storage.log_usage(
            user_id, agent_key, reply.input_tokens, reply.output_tokens, reply.cache_read_tokens
        )

    def _should_respond(self, update: Update, bot_username: str | None) -> bool:
        """Guruhlarda faqat botga murojaat qilinganda (mention yoki reply) javob beradi."""
        msg = update.effective_message
        chat = update.effective_chat
        if chat is None or chat.type == ChatType.PRIVATE:
            return True
        if msg is None:
            return False
        if msg.reply_to_message and msg.reply_to_message.from_user and msg.reply_to_message.from_user.is_bot:
            return msg.reply_to_message.from_user.username == bot_username
        text = (msg.text or msg.caption or "")
        return bool(bot_username) and f"@{bot_username}".lower() in text.lower()

    def guarded(self, fn: Handler) -> Handler:
        @wraps(fn)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Any:
            user = update.effective_user
            if user is None:
                return None
            if not self._allowed(user.id):
                if update.effective_message:
                    await update.effective_message.reply_text(
                        "⛔ Bu bot faqat Bovari Agency jamoasi uchun.\n"
                        f"Sizning Telegram ID: {user.id} — administratorga yuboring."
                    )
                return None
            return await fn(update, context)

        return wrapper

    # ============================================================= commands
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        agent = self._current_agent(user.id)
        lines = [
            f"Assalomu alaykum, {user.first_name}! 👋",
            "",
            f"<b>{self.settings.bot_name}</b> — marketing jamoasining AI agentlari bitta botda.",
            "",
        ]
        lines += [f"{a.emoji} <b>{a.title}</b> — {a.short}" for a in AGENTS.values()]
        lines += [
            "",
            "👥 <b>Jamoa rejimi</b> — katta vazifani bir nechta agent birgalikda bajaradi: "
            "/jamoa &lt;vazifa&gt;",
            "",
            f"Hozirgi agent: <b>{agent.label}</b>. Pastdagi tugmalar orqali almashtiring "
            "yoki shunchaki savolingizni yozing. Rasm, PDF va CSV fayllarni ham yuborish mumkin.",
        ]
        await update.effective_message.reply_text(
            "\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=self._main_keyboard()
        )

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        agent_cmds = "\n".join(f"/{a.key} — {a.label}" for a in AGENTS.values())
        text = (
            "<b>Buyruqlar</b>\n\n"
            "/agentlar — agent tanlash\n"
            f"{agent_cmds}\n"
            "/jamoa &lt;vazifa&gt; — bir nechta agent birgalikda ishlaydi\n"
            "/qaysi — hozirgi agent\n"
            "/yangi — joriy agent bilan suhbatni yangidan boshlash\n"
            "/tozalash — barcha agentlar tarixini o'chirish\n"
            "/statistika — xarajat statistikasi (admin)\n\n"
            "<b>Maslahatlar</b>\n"
            "• Agent buyrug'idan keyin darhol vazifa yozish mumkin: "
            "<code>/kopirayter to'yxona uchun 3 ta reklama matni</code>\n"
            "• Dizaynerga rasm yuborib, tahlil so'rang.\n"
            "• Analitikka CSV/PDF hisobot yuboring.\n"
            "• Har bir agent sizning suhbat tarixingizni alohida eslab qoladi."
        )
        await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)

    async def cmd_agents(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        agent = self._current_agent(update.effective_user.id)
        await update.effective_message.reply_text(
            f"Hozirgi agent: {agent.label}\nQaysi agent bilan ishlaymiz?",
            reply_markup=self._agents_inline(),
        )

    async def cmd_which(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        agent = self._current_agent(update.effective_user.id)
        await update.effective_message.reply_text(f"Hozirgi agent: {agent.label}\n{agent.short}")

    async def cmd_new(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        agent = self._current_agent(update.effective_user.id)
        self.storage.reset(update.effective_user.id, agent.key)
        context.user_data.pop("awaiting_team", None)
        await update.effective_message.reply_text(
            f"🔄 {agent.label} bilan yangi suhbat boshlandi. Oldingi kontekst o'chirildi."
        )

    async def cmd_clear(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        n = self.storage.reset(update.effective_user.id)
        await update.effective_message.reply_text(f"🧹 Barcha agentlar tarixi tozalandi ({n} ta yozuv).")

    async def cmd_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_user.id not in self.settings.admin_user_ids:
            await update.effective_message.reply_text("Bu buyruq faqat administratorlar uchun.")
            return
        rows = self.storage.usage_since(time.time() - 30 * 86400)
        if not rows:
            await update.effective_message.reply_text("Oxirgi 30 kunda so'rovlar yo'q.")
            return
        total = 0.0
        lines = ["<b>Oxirgi 30 kun statistikasi</b>\n"]
        for key, count, inp, out, cache in rows:
            cost = (inp or 0) / 1e6 * PRICE_INPUT + (out or 0) / 1e6 * PRICE_OUTPUT
            cost += (cache or 0) / 1e6 * PRICE_CACHE_READ
            total += cost
            title = AGENTS[key].label if key in AGENTS else key
            lines.append(f"{title}: {count} ta so'rov ≈ ${cost:.2f}")
        lines.append(f"\n<b>Jami ≈ ${total:.2f}</b>")
        lines.append("<i>Taxminiy hisob; web qidiruv va kesh yozish alohida hisoblanadi.</i>")
        await update.effective_message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)

    def make_agent_command(self, agent: Agent) -> Handler:
        async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            user_id = update.effective_user.id
            self.storage.set_agent(user_id, agent.key)
            context.user_data.pop("awaiting_team", None)
            task = " ".join(context.args or []).strip()
            if task:
                await self._handle_prompt(update, context, task, task)
            else:
                await update.effective_message.reply_text(
                    f"{agent.label} tayyor.\n{agent.short}\n\nVazifangizni yozing."
                )

        return handler

    async def on_agent_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        key = (query.data or "").split(":", 1)[-1]
        agent = AGENTS.get(key)
        if agent is None:
            await query.answer("Noma'lum agent")
            return
        self.storage.set_agent(update.effective_user.id, key)
        context.user_data.pop("awaiting_team", None)
        await query.answer(f"{agent.title} tanlandi")
        await query.edit_message_text(f"✅ {agent.label} tanlandi.\n{agent.short}\n\nVazifangizni yozing.")

    # ============================================================ messages
    async def on_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._should_respond(update, context.bot.username):
            return
        msg = update.effective_message
        text = (msg.text or "").strip()
        if context.bot.username:
            text = text.replace(f"@{context.bot.username}", "").strip()
        if not text:
            return

        # Pastki klaviatura tugmalari.
        for agent in AGENTS.values():
            if text == agent.label:
                self.storage.set_agent(update.effective_user.id, agent.key)
                context.user_data.pop("awaiting_team", None)
                await msg.reply_text(f"✅ {agent.label} tanlandi.\n{agent.short}\n\nVazifangizni yozing.")
                return
        if text == NEW_CHAT_BUTTON:
            await self.cmd_new(update, context)
            return
        if text == TEAM_BUTTON:
            context.user_data["awaiting_team"] = True
            await msg.reply_text(
                "👥 Jamoa rejimi. Katta vazifani batafsil yozing — koordinator uni agentlarga "
                "taqsimlaydi.\n\nMasalan: «Toshkentdagi yangi to'yxona uchun 1 oylik marketing "
                "kampaniyasi: strategiya, kontent-reja, 3 ta Reels ssenariy va vizual konsepsiya»"
            )
            return
        if context.user_data.pop("awaiting_team", False):
            await self._run_team(update, context, text)
            return

        await self._handle_prompt(update, context, text, text)

    async def on_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._should_respond(update, context.bot.username):
            return
        msg = update.effective_message
        photo = msg.photo[-1]
        file = await photo.get_file()
        data = bytes(await file.download_as_bytearray())
        caption = (msg.caption or "").strip() or "Ushbu rasmni o'z rolingdan kelib chiqib tahlil qil."
        content = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": base64.standard_b64encode(data).decode(),
                },
            },
            {"type": "text", "text": caption},
        ]
        await self._handle_prompt(update, context, content, f"[Rasm yuborildi] {caption}")

    async def on_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._should_respond(update, context.bot.username):
            return
        msg = update.effective_message
        doc = msg.document
        name = doc.file_name or "fayl"
        mime = (doc.mime_type or "").lower()
        caption = (msg.caption or "").strip() or "Ushbu faylni o'z rolingdan kelib chiqib tahlil qil."

        if doc.file_size and doc.file_size > 20 * 1024 * 1024:
            await msg.reply_text("Fayl juda katta (Telegram bot limiti — 20 MB).")
            return

        file = await doc.get_file()
        data = bytes(await file.download_as_bytearray())
        b64 = lambda: base64.standard_b64encode(data).decode()  # noqa: E731

        if mime == "application/pdf" or name.lower().endswith(".pdf"):
            content = [
                {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": b64()}},
                {"type": "text", "text": caption},
            ]
            stored = f"[PDF fayl: {name}] {caption}"
        elif mime in IMAGE_MIME:
            content = [
                {"type": "image", "source": {"type": "base64", "media_type": mime, "data": b64()}},
                {"type": "text", "text": caption},
            ]
            stored = f"[Rasm fayl: {name}] {caption}"
        elif name.lower().endswith(TEXT_FILE_EXT) or mime.startswith("text/"):
            body = data.decode("utf-8", errors="replace")
            if len(body) > MAX_TEXT_FILE_CHARS:
                await msg.reply_text(
                    "Fayl juda katta. Iltimos, uni qismlarga bo'lib yoki qisqartirib yuboring."
                )
                return
            content = f"Fayl: {name}\n<file>\n{body}\n</file>\n\n{caption}"
            stored = content if len(body) <= MAX_STORED_FILE_CHARS else f"[Matnli fayl: {name}] {caption}"
        else:
            await msg.reply_text(
                "Bu fayl turini o'qiy olmayman. Qo'llab-quvvatlanadi: PDF, rasm (JPG/PNG/WEBP), "
                "TXT, CSV, MD, JSON, SRT. Excel faylni CSV qilib yuboring."
            )
            return
        await self._handle_prompt(update, context, content, stored)

    # ============================================================== core
    async def _handle_prompt(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        content: Any,
        stored_text: str,
    ) -> None:
        user_id = update.effective_user.id
        msg = update.effective_message
        lock = self._user_locks[user_id]
        if lock.locked():
            await msg.reply_text("⏳ Oldingi so'rovingiz hali bajarilmoqda, biroz kuting…")
        async with lock:
            agent = self._current_agent(user_id)
            history = self.storage.history(user_id, agent.key, self.settings.history_turns)
            async with self._typing(msg.chat_id, context.bot):
                try:
                    reply = await self.llm.ask_agent(agent, history, content)
                except LLMError as e:
                    await msg.reply_text(f"⚠️ {e}")
                    return
            self.storage.add_turn(user_id, agent.key, stored_text, reply.text)
            self._log_usage(user_id, agent.key, reply)
            await self._send_long(msg, self._format_reply(reply), header=f"**{agent.label}**")

    async def cmd_team(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        task = " ".join(context.args or []).strip()
        if not task:
            context.user_data["awaiting_team"] = True
            await update.effective_message.reply_text(
                "👥 Vazifani yozing — koordinator uni agentlarga taqsimlaydi."
            )
            return
        await self._run_team(update, context, task)

    async def _run_team(self, update: Update, context: ContextTypes.DEFAULT_TYPE, task: str) -> None:
        user_id = update.effective_user.id
        msg = update.effective_message
        lock = self._user_locks[user_id]
        if lock.locked():
            await msg.reply_text("⏳ Oldingi so'rovingiz hali bajarilmoqda, biroz kuting…")
        async with lock:
            async with self._typing(msg.chat_id, context.bot):
                try:
                    plan = await self.llm.plan_team_task(task)
                except LLMError as e:
                    await msg.reply_text(f"⚠️ {e}")
                    return

                steps = [s for s in plan["steps"] if s.get("agent") in AGENTS]
                if not steps:
                    await msg.reply_text("Koordinator vazifani taqsimlay olmadi. Batafsilroq yozing.")
                    return
                plan_lines = [f"**👥 Jamoa rejasi:** {plan.get('summary', '')}", ""]
                plan_lines += [
                    f"{i}. {AGENTS[s['agent']].label} — {s['task']}" for i, s in enumerate(steps, 1)
                ]
                await self._send_long(msg, "\n".join(plan_lines))

                results: list[tuple[Agent, str]] = []
                for i, step in enumerate(steps, 1):
                    agent = AGENTS[step["agent"]]
                    previous = "\n\n".join(f"### {a.title} natijasi\n{t}" for a, t in results)
                    prompt = f"Umumiy vazifa: {task}\n\nSening topshirig'ing: {step['task']}"
                    if previous:
                        prompt += f"\n\nJamoadoshlaringning natijalari (ularga tayan):\n\n{previous}"
                    try:
                        reply = await self.llm.ask_agent(agent, [], prompt)
                    except LLMError as e:
                        await msg.reply_text(f"⚠️ {agent.label}: {e}")
                        continue
                    self._log_usage(user_id, agent.key, reply)
                    results.append((agent, reply.text))
                    await self._send_long(
                        msg, self._format_reply(reply), header=f"**{i}/{len(steps)} · {agent.label}**"
                    )

                if len(results) >= 2:
                    try:
                        summary = await self.llm.synthesize(task, results, SYNTHESIS_INSTRUCTION)
                    except LLMError as e:
                        await msg.reply_text(f"⚠️ Yakuniy xulosa: {e}")
                        return
                    self._log_usage(user_id, "jamoa", summary)
                    await self._send_long(msg, summary.text, header="**🧭 Koordinator xulosasi**")

    async def on_error(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        log.exception("Handler xatosi", exc_info=context.error)
        if isinstance(update, Update) and update.effective_message:
            try:
                await update.effective_message.reply_text("⚠️ Kutilmagan xato yuz berdi. Qayta urinib ko'ring.")
            except TelegramError:
                pass

    # ============================================================ wiring
    async def post_init(self, app: Application) -> None:
        bot = app.bot
        commands = [
            BotCommand("start", "Boshlash"),
            BotCommand("agentlar", "Agent tanlash"),
            *[BotCommand(a.key, a.title) for a in AGENTS.values()],
            BotCommand("jamoa", "Bir nechta agent birgalikda"),
            BotCommand("yangi", "Yangi suhbat"),
            BotCommand("qaysi", "Hozirgi agent"),
            BotCommand("tozalash", "Tarixni tozalash"),
            BotCommand("yordam", "Yordam"),
        ]
        for coro in (
            bot.set_my_commands(commands),
            bot.set_my_name(self.settings.bot_name),
            bot.set_my_short_description(
                "Bovari Agency marketing jamoasining AI agentlari: marketolog, SMM, PM, "
                "dizayner, kopirayter, analitik, montajyor."
            ),
            bot.set_my_description(
                "Bovari Agency — marketing, SMM va video production agentligi.\n\n"
                "Bu bot jamoaning 7 ta AI agentini birlashtiradi: Marketolog, SMM menejer, "
                "Proyekt menejer, Dizayner, Kopirayter, Analitik va Video montajyor."
            ),
        ):
            try:
                await coro
            except TelegramError as e:  # masalan, nomni tez-tez o'zgartirish limiti
                log.warning("Bot profilini sozlab bo'lmadi: %s", e)

    def build_application(self) -> Application:
        app = (
            Application.builder()
            .token(self.settings.telegram_token)
            .concurrent_updates(True)
            .post_init(self.post_init)
            .build()
        )
        g = self.guarded
        app.add_handler(CommandHandler("start", g(self.cmd_start)))
        app.add_handler(CommandHandler(["yordam", "help"], g(self.cmd_help)))
        app.add_handler(CommandHandler("agentlar", g(self.cmd_agents)))
        app.add_handler(CommandHandler("qaysi", g(self.cmd_which)))
        app.add_handler(CommandHandler("yangi", g(self.cmd_new)))
        app.add_handler(CommandHandler("tozalash", g(self.cmd_clear)))
        app.add_handler(CommandHandler("statistika", g(self.cmd_stats)))
        app.add_handler(CommandHandler("jamoa", g(self.cmd_team)))
        for agent in AGENTS.values():
            app.add_handler(CommandHandler(agent.key, g(self.make_agent_command(agent))))
        app.add_handler(CallbackQueryHandler(g(self.on_agent_button), pattern=r"^agent:"))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, g(self.on_text)))
        app.add_handler(MessageHandler(filters.PHOTO, g(self.on_photo)))
        app.add_handler(MessageHandler(filters.Document.ALL, g(self.on_document)))
        app.add_error_handler(self.on_error)
        return app
