"""ClaudeClient mantiqini haqiqiy API ga murojaat qilmasdan tekshiradi."""

import asyncio
import os
from types import SimpleNamespace

os.environ.setdefault("ANTHROPIC_API_KEY", "test")

from bovari_bot.agents import AGENTS
from bovari_bot.config import Settings
from bovari_bot.llm import ClaudeClient, LLMError


def _resp(blocks, stop="end_turn"):
    return SimpleNamespace(
        content=blocks,
        stop_reason=stop,
        usage=SimpleNamespace(input_tokens=10, output_tokens=5, cache_read_input_tokens=3),
    )


class _Stream:
    def __init__(self, resp):
        self.resp = resp

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def get_final_message(self):
        return self.resp


def _client(responses, calls):
    c = ClaudeClient(Settings(telegram_token="x"))

    def stream(**kw):
        calls.append(kw)
        return _Stream(responses.pop(0))

    c.client = SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(stream=stream)))
    return c


def test_ask_agent_with_search_and_pause():
    cite = SimpleNamespace(url="https://x.uz", title="X")
    calls = []
    c = _client(
        [
            _resp([SimpleNamespace(type="thinking"), SimpleNamespace(type="text", text="Bir ", citations=[cite])], "pause_turn"),
            _resp([SimpleNamespace(type="text", text="ikki", citations=None)]),
        ],
        calls,
    )
    reply = asyncio.run(c.ask_agent(AGENTS["marketolog"], [], "salom"))
    assert reply.text == "Bir ikki"
    assert reply.sources == [("X", "https://x.uz")]
    assert reply.input_tokens == 20
    assert len(calls) == 2
    kw = calls[0]
    assert kw["model"] == "claude-opus-5-5"
    assert kw["thinking"] == {"type": "adaptive"}
    assert kw["fallbacks"] == "default"
    assert kw["output_config"]["effort"] == "high"
    assert kw["tools"][0]["type"] == "web_search_20260209"
    assert calls[1]["messages"][-1]["role"] == "assistant"


def test_no_tools_for_copywriter_and_refusal():
    calls = []
    c = _client([_resp([], "refusal")], calls)
    try:
        asyncio.run(c.ask_agent(AGENTS["kopirayter"], [], "salom"))
    except LLMError:
        pass
    else:
        raise AssertionError("refusal should raise")
    assert "tools" not in calls[0]
    assert calls[0]["output_config"]["effort"] == "medium"


def test_plan_parsing():
    calls = []
    c = _client([_resp([SimpleNamespace(type="text", text='{"summary":"s","steps":[{"agent":"smm","task":"t"}]}', citations=None)])], calls)
    plan = asyncio.run(c.plan_team_task("vazifa"))
    assert plan["steps"][0]["agent"] == "smm"
    assert calls[0]["output_config"]["format"]["type"] == "json_schema"
