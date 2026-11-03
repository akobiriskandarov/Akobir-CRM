"""Claude API bilan ishlash qatlami."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

import anthropic

from .agents import COORDINATOR_PROMPT, PLAN_SCHEMA, Agent
from .config import Settings

log = logging.getLogger(__name__)

# Xavfsizlik klassifikatori so'rovni rad etsa, API uni avtomatik ravishda
# Anthropic tavsiya qilgan zaxira modelda qayta bajaradi.
FALLBACK_BETA = "server-side-fallback-2026-07-01"
MAX_PAUSE_CONTINUATIONS = 3


class LLMError(Exception):
    """Foydalanuvchiga ko'rsatiladigan xato (o'zbek tilida)."""


@dataclass
class Reply:
    text: str
    sources: list[tuple[str, str]] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    truncated: bool = False


class ClaudeClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = anthropic.AsyncAnthropic(max_retries=3)

    # ---------------------------------------------------------------- helpers
    def _tools(self, agent: Agent) -> list[dict[str, Any]]:
        if agent.web_search and self.settings.web_search:
            return [{"type": "web_search_20260209", "name": "web_search", "max_uses": 5}]
        return []

    async def _run(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        effort: str,
        tools: list[dict[str, Any]] | None = None,
        output_format: dict[str, Any] | None = None,
        max_tokens: int | None = None,
    ) -> Reply:
        output_config: dict[str, Any] = {"effort": effort}
        if output_format is not None:
            output_config["format"] = output_format

        messages = list(messages)
        reply = Reply(text="")
        texts: list[str] = []
        seen_urls: set[str] = set()

        try:
            for _ in range(MAX_PAUSE_CONTINUATIONS + 1):
                kwargs: dict[str, Any] = dict(
                    model=self.settings.model,
                    max_tokens=max_tokens or self.settings.max_tokens,
                    system=system,
                    messages=messages,
                    thinking={"type": "adaptive"},
                    output_config=output_config,
                    cache_control={"type": "ephemeral"},
                    betas=[FALLBACK_BETA],
                    fallbacks="default",
                )
                if tools:
                    kwargs["tools"] = tools

                async with self.client.beta.messages.stream(**kwargs) as stream:
                    response = await stream.get_final_message()

                usage = response.usage
                reply.input_tokens += usage.input_tokens or 0
                reply.output_tokens += usage.output_tokens or 0
                reply.cache_read_tokens += getattr(usage, "cache_read_input_tokens", 0) or 0

                if response.stop_reason == "refusal":
                    raise LLMError(
                        "Bu so'rovga javob berib bo'lmadi (xavfsizlik filtri). "
                        "Savolni boshqacha shakllantirib ko'ring."
                    )

                for block in response.content:
                    if block.type != "text":
                        continue
                    texts.append(block.text)
                    for c in getattr(block, "citations", None) or []:
                        url = getattr(c, "url", None)
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            reply.sources.append((getattr(c, "title", None) or url, url))

                if response.stop_reason == "pause_turn":
                    # Server tomonidagi web qidiruv uzoq davom etdi — davom ettiramiz.
                    messages.append({"role": "assistant", "content": response.content})
                    continue
                if response.stop_reason == "max_tokens":
                    reply.truncated = True
                break
        except LLMError:
            raise
        except anthropic.AuthenticationError as e:
            raise LLMError("Claude API kaliti noto'g'ri. Administratorga murojaat qiling.") from e
        except anthropic.RateLimitError as e:
            raise LLMError("Hozir so'rovlar juda ko'p. 1 daqiqadan keyin qayta urinib ko'ring.") from e
        except anthropic.BadRequestError as e:
            log.exception("Claude bad request")
            raise LLMError(f"So'rovda xato: {e.message}") from e
        except anthropic.APIStatusError as e:
            log.exception("Claude API status error")
            raise LLMError(f"Claude xizmatida xato ({e.status_code}). Birozdan keyin urinib ko'ring.") from e
        except anthropic.APIConnectionError as e:
            raise LLMError("Claude bilan aloqa yo'q. Internetni tekshiring.") from e

        reply.text = "".join(texts).strip()
        if not reply.text:
            raise LLMError("Agent bo'sh javob qaytardi. Qayta urinib ko'ring.")
        return reply

    # ---------------------------------------------------------------- public
    async def ask_agent(
        self, agent: Agent, history: list[dict[str, Any]], user_content: Any
    ) -> Reply:
        """`history` — oldingi suhbat (faqat matn), `user_content` — yangi xabar."""
        messages = [*history, {"role": "user", "content": user_content}]
        return await self._run(
            system=agent.system_prompt,
            messages=messages,
            effort=agent.effort or self.settings.effort,
            tools=self._tools(agent),
        )

    async def plan_team_task(self, task: str) -> dict[str, Any]:
        """Koordinator: vazifani agentlar o'rtasida taqsimlaydi (JSON reja)."""
        reply = await self._run(
            system=COORDINATOR_PROMPT,
            messages=[{"role": "user", "content": task}],
            effort="low",
            output_format={"type": "json_schema", "schema": PLAN_SCHEMA},
            max_tokens=8000,
        )
        try:
            plan = json.loads(reply.text)
        except json.JSONDecodeError as e:
            raise LLMError("Koordinator rejasini o'qib bo'lmadi. Qayta urinib ko'ring.") from e
        plan["steps"] = plan.get("steps", [])[:5]
        return plan

    async def synthesize(self, task: str, results: list[tuple[Agent, str]], instruction: str) -> Reply:
        body = "\n\n".join(f"### {a.title} natijasi\n{text}" for a, text in results)
        return await self._run(
            system=COORDINATOR_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Vazifa: {task}\n\n{body}\n\n{instruction}",
                }
            ],
            effort=self.settings.effort,
        )
