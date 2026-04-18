"""SQLite implementation of the Repository protocol."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Iterable, Optional

from ..logging_setup import get_logger
from .models import Group, Message, Signal, Summary, User

log = get_logger(__name__)


def _iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat()


def _parse(dt: str | None) -> datetime:
    return datetime.fromisoformat(dt) if dt else datetime.utcnow()


class SqliteRepository:
    """Thread-safe SQLite repo. `initialize()` runs DDL idempotently."""

    def __init__(self, db_path: Path, schema_path: Optional[Path] = None) -> None:
        self._path = Path(db_path)
        self._schema = schema_path or Path(__file__).with_name("schema.sql")
        self._lock = RLock()
        self._conn: Optional[sqlite3.Connection] = None

    # ------------------------------------------------------------------ lifecycle
    def initialize(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            self._conn = sqlite3.connect(self._path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.executescript(self._schema.read_text())
            self._conn.commit()
        log.info("sqlite initialized", extra={"path": str(self._path)})

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None

    def _cx(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("Repository not initialized. Call .initialize() first.")
        return self._conn

    # ------------------------------------------------------------------ groups
    def upsert_group(self, group: Group) -> int:
        with self._lock:
            cx = self._cx()
            cx.execute(
                """
                INSERT INTO groups (telegram_id, title, username, last_message_id)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(telegram_id) DO UPDATE SET
                  title = excluded.title,
                  username = excluded.username
                """,
                (group.telegram_id, group.title, group.username, group.last_message_id),
            )
            cx.commit()
            row = cx.execute(
                "SELECT id FROM groups WHERE telegram_id = ?", (group.telegram_id,)
            ).fetchone()
            return int(row["id"])

    def get_group(self, telegram_id: int) -> Optional[Group]:
        with self._lock:
            row = self._cx().execute(
                "SELECT telegram_id, title, username, last_message_id FROM groups WHERE telegram_id=?",
                (telegram_id,),
            ).fetchone()
            if not row:
                return None
            return Group(
                telegram_id=int(row["telegram_id"]),
                title=row["title"],
                username=row["username"],
                last_message_id=int(row["last_message_id"]),
            )

    def set_last_message_id(self, group_telegram_id: int, message_id: int) -> None:
        with self._lock:
            cx = self._cx()
            cx.execute(
                """
                UPDATE groups
                SET last_message_id = MAX(last_message_id, ?)
                WHERE telegram_id = ?
                """,
                (message_id, group_telegram_id),
            )
            cx.commit()

    # ------------------------------------------------------------------ users
    def upsert_user(self, user: User) -> int:
        with self._lock:
            cx = self._cx()
            cx.execute(
                """
                INSERT INTO users (telegram_id, username, display_name)
                VALUES (?, ?, ?)
                ON CONFLICT(telegram_id) DO UPDATE SET
                  username = excluded.username,
                  display_name = excluded.display_name
                """,
                (user.telegram_id, user.username, user.display_name),
            )
            cx.commit()
            row = cx.execute(
                "SELECT id FROM users WHERE telegram_id = ?", (user.telegram_id,)
            ).fetchone()
            return int(row["id"])

    # ------------------------------------------------------------------ messages
    def insert_messages(self, messages: Iterable[Message]) -> list[int]:
        """Bulk insert. Returns internal ids (new or pre-existing)."""
        ids: list[int] = []
        with self._lock:
            cx = self._cx()
            for m in messages:
                cx.execute(
                    """
                    INSERT OR IGNORE INTO messages
                      (telegram_id, group_telegram_id, sender_telegram_id,
                       text, message_type, sent_at, reply_to, raw_meta)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        m.telegram_id,
                        m.group_telegram_id,
                        m.sender_telegram_id,
                        m.text,
                        m.message_type,
                        _iso(m.sent_at),
                        m.reply_to,
                        json.dumps(m.raw_meta) if m.raw_meta else None,
                    ),
                )
                row = cx.execute(
                    "SELECT id FROM messages WHERE group_telegram_id=? AND telegram_id=?",
                    (m.group_telegram_id, m.telegram_id),
                ).fetchone()
                if row:
                    ids.append(int(row["id"]))
            cx.commit()
        return ids

    def list_messages(
        self,
        group_telegram_id: Optional[int] = None,
        since: Optional[datetime] = None,
        limit: int = 500,
    ) -> list[tuple[int, Message]]:
        sql = (
            "SELECT id, telegram_id, group_telegram_id, sender_telegram_id, text, "
            "message_type, sent_at, reply_to, raw_meta FROM messages"
        )
        clauses: list[str] = []
        params: list[object] = []
        if group_telegram_id is not None:
            clauses.append("group_telegram_id = ?")
            params.append(group_telegram_id)
        if since is not None:
            clauses.append("sent_at >= ?")
            params.append(_iso(since))
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY sent_at ASC LIMIT ?"
        params.append(limit)

        with self._lock:
            rows = self._cx().execute(sql, params).fetchall()

        out: list[tuple[int, Message]] = []
        for r in rows:
            out.append(
                (
                    int(r["id"]),
                    Message(
                        telegram_id=int(r["telegram_id"]),
                        group_telegram_id=int(r["group_telegram_id"]),
                        sender_telegram_id=(
                            int(r["sender_telegram_id"])
                            if r["sender_telegram_id"] is not None
                            else None
                        ),
                        text=r["text"],
                        message_type=r["message_type"],
                        sent_at=_parse(r["sent_at"]),
                        reply_to=int(r["reply_to"]) if r["reply_to"] is not None else None,
                        raw_meta=json.loads(r["raw_meta"]) if r["raw_meta"] else {},
                    ),
                )
            )
        return out

    # ------------------------------------------------------------------ signals
    def insert_signal(self, message_internal_id: int, signal: Signal) -> Optional[int]:
        with self._lock:
            cx = self._cx()
            cx.execute(
                """
                INSERT OR IGNORE INTO signals
                  (rule_name, message_id, group_telegram_id, matched_conditions,
                   confidence, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    signal.rule_name,
                    message_internal_id,
                    signal.group_telegram_id,
                    json.dumps(signal.matched_conditions),
                    float(signal.confidence),
                    _iso(signal.created_at),
                ),
            )
            cx.commit()
            row = cx.execute(
                "SELECT id FROM signals WHERE rule_name=? AND message_id=?",
                (signal.rule_name, message_internal_id),
            ).fetchone()
            return int(row["id"]) if row else None

    def list_signals(self, limit: int = 200) -> list[Signal]:
        with self._lock:
            rows = self._cx().execute(
                """
                SELECT rule_name, message_id, group_telegram_id, matched_conditions,
                       confidence, created_at
                FROM signals
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            Signal(
                rule_name=r["rule_name"],
                message_id=int(r["message_id"]),
                group_telegram_id=int(r["group_telegram_id"]),
                matched_conditions=json.loads(r["matched_conditions"]),
                confidence=float(r["confidence"]),
                created_at=_parse(r["created_at"]),
            )
            for r in rows
        ]

    # ------------------------------------------------------------------ summaries
    def insert_summary(self, summary: Summary) -> int:
        with self._lock:
            cx = self._cx()
            cur = cx.execute(
                """
                INSERT INTO summaries
                  (group_telegram_id, covers_from, covers_to, message_count, text,
                   model, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    summary.group_telegram_id,
                    _iso(summary.covers_from),
                    _iso(summary.covers_to),
                    int(summary.message_count),
                    summary.text,
                    summary.model,
                    _iso(summary.created_at),
                ),
            )
            cx.commit()
            return int(cur.lastrowid or 0)

    def list_summaries(
        self, group_telegram_id: Optional[int] = None, limit: int = 50
    ) -> list[Summary]:
        sql = (
            "SELECT group_telegram_id, covers_from, covers_to, message_count, text, "
            "model, created_at FROM summaries"
        )
        params: list[object] = []
        if group_telegram_id is not None:
            sql += " WHERE group_telegram_id = ?"
            params.append(group_telegram_id)
        sql += " ORDER BY covers_to DESC LIMIT ?"
        params.append(limit)
        with self._lock:
            rows = self._cx().execute(sql, params).fetchall()
        return [
            Summary(
                group_telegram_id=int(r["group_telegram_id"]),
                covers_from=_parse(r["covers_from"]),
                covers_to=_parse(r["covers_to"]),
                message_count=int(r["message_count"]),
                text=r["text"],
                model=r["model"],
                created_at=_parse(r["created_at"]),
            )
            for r in rows
        ]
