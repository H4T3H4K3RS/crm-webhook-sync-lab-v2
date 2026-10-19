"""Настройки сервиса (читаются из переменных окружения)."""

import os


def get_database_path() -> str:
    """Путь к файлу SQLite. Тесты подменяют его через DATABASE_PATH."""
    return os.environ.get("DATABASE_PATH", "data/deals.db")


def get_webhook_secret() -> str | None:
    """Секрет для проверки подписи webhook (дополнительное задание, уровень П)."""
    return os.environ.get("WEBHOOK_SECRET") or None
