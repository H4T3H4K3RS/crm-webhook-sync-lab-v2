"""Работа с SQLite."""

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from app.config import get_database_path


def connect() -> sqlite3.Connection:
    path = get_database_path()
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    conn = sqlite3.connect(path, timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    """Создаёт таблицы, если их ещё нет.

    TODO (этап 2): добавьте таблицу для учёта уже обработанных событий
    (идемпотентность). Подумайте, какое ограничение гарантирует, что
    одно и то же event_id не будет записано дважды.
    """
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS deals (
                deal_id    TEXT PRIMARY KEY,
                status     TEXT NOT NULL,
                version    INTEGER NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
