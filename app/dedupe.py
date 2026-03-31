from __future__ import annotations

import sqlite3
from pathlib import Path
from threading import Lock


class EventDedupeStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _initialize(self) -> None:
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS processed_events (
                        event_key TEXT PRIMARY KEY,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                conn.commit()

    def seen_or_record(self, event_key: str) -> bool:
        with self._lock:
            with self._connect() as conn:
                existing = conn.execute(
                    "SELECT 1 FROM processed_events WHERE event_key = ?",
                    (event_key,),
                ).fetchone()
                if existing:
                    return True

                conn.execute(
                    "INSERT INTO processed_events (event_key) VALUES (?)",
                    (event_key,),
                )
                conn.commit()
                return False
