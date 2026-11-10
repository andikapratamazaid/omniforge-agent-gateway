"""Penyimpanan SQLite: identitas lintas platform, sesi, pesan, cron, eksekusi."""

from __future__ import annotations

import secrets
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

from . import config

SCHEMA = Path(__file__).resolve().parent.parent / "schema.sql"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Store:
    def __init__(self, path: Path | None = None):
        self.path = path or config.db_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # check_same_thread=False + kunci: koneksi dipakai bersama oleh
        # thread server webhook dan thread cron.
        self._lock = threading.RLock()
        self.db = sqlite3.connect(self.path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA.read_text(encoding="utf-8"))
        self.db.commit()

    def execute(self, sql, params=()):
        with self._lock:
            return self.db.execute(sql, params)

    def commit(self):
        with self._lock:
            self.db.commit()

    # ---------- identitas lintas platform ----------
    def resolve_identity(self, platform: str, platform_user_id: str) -> int:
        row = self.execute(
            "SELECT identity_id FROM platform_links WHERE platform=? AND platform_user_id=?",
            (platform, platform_user_id),
        ).fetchone()
        if row:
            return int(row["identity_id"])
        cur = self.execute("INSERT INTO identities DEFAULT VALUES")
        identity_id = int(cur.lastrowid)
        self.execute(
            "INSERT INTO platform_links VALUES (?,?,?)",
            (identity_id, platform, platform_user_id),
        )
        self.commit()
        return identity_id

    def create_link_code(self, identity_id: int) -> str:
        code = secrets.token_hex(3).upper()
        self.execute(
            "INSERT OR REPLACE INTO link_codes VALUES (?,?,?)",
            (code, identity_id, now_iso()),
        )
        self.commit()
        return code

    def apply_link_code(self, code: str, platform: str, platform_user_id: str) -> int | None:
        """Tautkan akun platform ini ke identitas pemilik kode. Mengembalikan
        identity_id tujuan, atau None bila kode tidak dikenal."""
        row = self.execute(
            "SELECT identity_id FROM link_codes WHERE code=?", (code.strip().upper(),)
        ).fetchone()
        if not row:
            return None
        target = int(row["identity_id"])
        current = self.resolve_identity(platform, platform_user_id)
        if current != target:
            # Pindahkan seluruh riwayat identitas sementara ke identitas target.
            self.execute(
                "DELETE FROM sessions WHERE identity_id=? AND session_key IN "
                "(SELECT session_key FROM sessions WHERE identity_id=?)", (current, target))
            self.execute("UPDATE messages SET identity_id=? WHERE identity_id=?", (target, current))
            self.execute("UPDATE sessions SET identity_id=? WHERE identity_id=?", (target, current))
            self.execute("UPDATE cron_jobs SET identity_id=? WHERE identity_id=?", (target, current))
            self.execute("DELETE FROM platform_links WHERE identity_id=?", (current,))
            self.execute("DELETE FROM identities WHERE id=?", (current,))
        self.execute(
            "INSERT OR REPLACE INTO platform_links VALUES (?,?,?)",
            (target, platform, platform_user_id),
        )
        self.execute("DELETE FROM link_codes WHERE code=?", (code.strip().upper(),))
        self.commit()
        return target

    def platforms_of(self, identity_id: int) -> list[str]:
        rows = self.execute(
            "SELECT DISTINCT platform FROM platform_links WHERE identity_id=?", (identity_id,)
        ).fetchall()
        return [r["platform"] for r in rows]

    # ---------- sesi dan pesan ----------
    def ensure_session(self, identity_id: int, session_key: str) -> None:
        self.execute(
            "INSERT OR IGNORE INTO sessions VALUES (?,?,?)",
            (identity_id, session_key, now_iso()),
        )
        self.commit()

    def add_message(self, identity_id: int, session_key: str, platform: str, role: str, text: str) -> None:
        self.ensure_session(identity_id, session_key)
        self.execute(
            "INSERT INTO messages (identity_id, session_key, platform, role, text, ts) VALUES (?,?,?,?,?,?)",
            (identity_id, session_key, platform, role, text, now_iso()),
        )
        self.commit()

    def history(self, identity_id: int, session_key: str, limit: int = 20) -> list[dict]:
        rows = self.execute(
            "SELECT platform, role, text, ts FROM messages WHERE identity_id=? AND session_key=? ORDER BY id DESC LIMIT ?",
            (identity_id, session_key, limit),
        ).fetchall()
        return [dict(r) for r in reversed(rows)]

    def last_platform(self, identity_id: int, session_key: str) -> str:
        row = self.execute(
            "SELECT platform FROM messages WHERE identity_id=? AND session_key=? AND role='user' ORDER BY id DESC LIMIT 1",
            (identity_id, session_key),
        ).fetchone()
        return row["platform"] if row else ""

    # ---------- cron ----------
    def add_cron(self, identity_id: int, platform: str, chat_id: str, schedule: str, prompt: str) -> int:
        cur = self.execute(
            "INSERT INTO cron_jobs (identity_id, platform, chat_id, schedule, prompt) VALUES (?,?,?,?,?)",
            (identity_id, platform, chat_id, schedule, prompt),
        )
        self.commit()
        return int(cur.lastrowid)

    def list_cron(self, identity_id: int | None = None) -> list[dict]:
        if identity_id is None:
            rows = self.execute("SELECT * FROM cron_jobs ORDER BY id").fetchall()
        else:
            rows = self.execute(
                "SELECT * FROM cron_jobs WHERE identity_id=? ORDER BY id", (identity_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    def mark_cron_run(self, job_id: int) -> None:
        self.execute("UPDATE cron_jobs SET last_run=? WHERE id=?", (now_iso(), job_id))
        self.commit()

    # ---------- eksekusi ----------
    def log_execution(self, backend: str, command: str, allowed: bool, output: str) -> None:
        self.execute(
            "INSERT INTO executions (backend, command, allowed, output, ts) VALUES (?,?,?,?,?)",
            (backend, command, int(allowed), output[:2000], now_iso()),
        )
        self.commit()

    def stats(self) -> dict:
        def count(sql: str) -> int:
            return int(self.execute(sql).fetchone()[0])

        return {
            "identities": count("SELECT COUNT(*) FROM identities"),
            "links": count("SELECT COUNT(*) FROM platform_links"),
            "messages": count("SELECT COUNT(*) FROM messages"),
            "cron_jobs": count("SELECT COUNT(*) FROM cron_jobs"),
            "executions": count("SELECT COUNT(*) FROM executions"),
        }
