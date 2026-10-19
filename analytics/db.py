"""SQLite log of published posts and their latest engagement metrics."""

import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "analytics.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS posts_log (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    platform          TEXT      NOT NULL,
    platform_post_id  TEXT      NOT NULL UNIQUE,
    topic             TEXT      NOT NULL DEFAULT '',
    domain            TEXT      NOT NULL DEFAULT 'general',
    tone              TEXT      NOT NULL DEFAULT 'Unknown',
    reactions         INTEGER   NOT NULL DEFAULT 0,
    comments          INTEGER   NOT NULL DEFAULT 0,
    shares            INTEGER   NOT NULL DEFAULT 0,
    created_at        TIMESTAMP NOT NULL,
    metrics_synced_at TIMESTAMP
)
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class PostsDatabase:
    """Thread-safe access to the ``posts_log`` table.

    One connection is shared behind a lock, so ``":memory:"`` works too (tests).
    The default file is data/analytics.db, or ANALYTICS_DB_PATH when set.
    """

    def __init__(self, path: Optional[str] = None):
        self.path = str(path or os.getenv("ANALYTICS_DB_PATH") or DEFAULT_DB_PATH)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()

    def init_db(self) -> None:
        """Creates the table if it does not exist yet. Safe to call any number of times."""
        with self._lock, self._conn:
            self._conn.execute(SCHEMA)

    def insert_post(self, platform: str, platform_post_id: str, topic: str = "", domain: str = "general",
                    tone: str = "Unknown", created_at: Optional[str] = None) -> int:
        """Logs a published post and returns its row id. A post already logged is not duplicated."""
        with self._lock, self._conn:
            cursor = self._conn.execute(
                "INSERT OR IGNORE INTO posts_log (platform, platform_post_id, topic, domain, tone, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (platform, platform_post_id, topic, domain, tone, created_at or utc_now()),
            )
            if cursor.rowcount:
                return cursor.lastrowid
            row = self._conn.execute("SELECT id FROM posts_log WHERE platform_post_id = ?",
                                     (platform_post_id,)).fetchone()
            return row["id"]

    def update_metrics(self, platform_post_id: str, reactions: int, comments: int, shares: int,
                       synced_at: Optional[str] = None) -> bool:
        """Stores the latest counts for a post. Returns False if the post is not in the log."""
        with self._lock, self._conn:
            cursor = self._conn.execute(
                "UPDATE posts_log SET reactions = ?, comments = ?, shares = ?, metrics_synced_at = ? "
                "WHERE platform_post_id = ?",
                (int(reactions), int(comments), int(shares), synced_at or utc_now(), platform_post_id),
            )
            return cursor.rowcount > 0

    def get_all_posts(self, platform: Optional[str] = None) -> list[dict]:
        """All logged posts, newest first, optionally for one platform."""
        query = "SELECT * FROM posts_log"
        params: tuple = ()
        if platform:
            query += " WHERE platform = ?"
            params = (platform,)
        query += " ORDER BY created_at DESC, id DESC"
        with self._lock:
            return [dict(row) for row in self._conn.execute(query, params).fetchall()]

    def close(self) -> None:
        with self._lock:
            self._conn.close()
