"""SQLite: foydalanuvchi tanlagan agent, suhbat tarixi va xarajat statistikasi."""

from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS user_state (
    user_id    INTEGER PRIMARY KEY,
    agent_key  TEXT NOT NULL,
    updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS turns (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    agent_key  TEXT NOT NULL,
    user_text  TEXT NOT NULL,
    reply_text TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_turns_user_agent ON turns(user_id, agent_key, id);
CREATE TABLE IF NOT EXISTS usage_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL,
    agent_key     TEXT NOT NULL,
    input_tokens  INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    cache_read    INTEGER NOT NULL,
    created_at    REAL NOT NULL
);
"""


class Storage:
    def __init__(self, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.executescript(SCHEMA)
        self._lock = threading.Lock()

    # ------------------------------------------------------------ agent choice
    def get_agent(self, user_id: int) -> str | None:
        row = self._conn.execute(
            "SELECT agent_key FROM user_state WHERE user_id = ?", (user_id,)
        ).fetchone()
        return row[0] if row else None

    def set_agent(self, user_id: int, agent_key: str) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO user_state(user_id, agent_key, updated_at) VALUES (?, ?, ?) "
                "ON CONFLICT(user_id) DO UPDATE SET agent_key = excluded.agent_key, "
                "updated_at = excluded.updated_at",
                (user_id, agent_key, time.time()),
            )

    # ----------------------------------------------------------------- history
    def history(self, user_id: int, agent_key: str, max_turns: int) -> list[dict[str, str]]:
        """Oxirgi `max_turns` ta savol-javob, Claude messages formatida (eski → yangi)."""
        rows = self._conn.execute(
            "SELECT user_text, reply_text FROM turns WHERE user_id = ? AND agent_key = ? "
            "ORDER BY id DESC LIMIT ?",
            (user_id, agent_key, max_turns),
        ).fetchall()
        messages: list[dict[str, str]] = []
        for user_text, reply_text in reversed(rows):
            messages.append({"role": "user", "content": user_text})
            messages.append({"role": "assistant", "content": reply_text})
        return messages

    def add_turn(self, user_id: int, agent_key: str, user_text: str, reply_text: str) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO turns(user_id, agent_key, user_text, reply_text, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, agent_key, user_text, reply_text, time.time()),
            )

    def reset(self, user_id: int, agent_key: str | None = None) -> int:
        with self._lock, self._conn:
            if agent_key is None:
                cur = self._conn.execute("DELETE FROM turns WHERE user_id = ?", (user_id,))
            else:
                cur = self._conn.execute(
                    "DELETE FROM turns WHERE user_id = ? AND agent_key = ?", (user_id, agent_key)
                )
            return cur.rowcount

    # ------------------------------------------------------------------- usage
    def log_usage(
        self, user_id: int, agent_key: str, input_tokens: int, output_tokens: int, cache_read: int
    ) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO usage_log(user_id, agent_key, input_tokens, output_tokens, "
                "cache_read, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, agent_key, input_tokens, output_tokens, cache_read, time.time()),
            )

    def usage_since(self, since_ts: float) -> list[tuple[str, int, int, int, int]]:
        """(agent_key, so'rovlar soni, input, output, cache_read) ro'yxati."""
        return self._conn.execute(
            "SELECT agent_key, COUNT(*), SUM(input_tokens), SUM(output_tokens), SUM(cache_read) "
            "FROM usage_log WHERE created_at >= ? GROUP BY agent_key ORDER BY COUNT(*) DESC",
            (since_ts,),
        ).fetchall()

    def close(self) -> None:
        self._conn.close()
