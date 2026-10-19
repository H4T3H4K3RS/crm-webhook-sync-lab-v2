"""Бизнес-логика обработки webhook-событий."""

from app.db import get_connection
from app.schemas import Deal, DealStatusChangedEvent


def process_event(event: DealStatusChangedEvent) -> str:
    """Применяет событие к состоянию сделки и возвращает результат обработки.

    Возвращаемые значения: "applied", "duplicate", "stale".

    Текущая реализация наивная: она безусловно перезаписывает статус сделки.
    Из-за этого:
      - повторная доставка события обрабатывается повторно (нет идемпотентности);
      - устаревшее событие, пришедшее позже нового, затирает актуальный статус.

    TODO (этап 2): идемпотентность по event_id -> "duplicate".
    TODO (этап 3): версионирование — не перезаписывать данные событием
                   с version <= текущей -> "stale".
    TODO: проверка и запись должны выполняться атомарно (в одной транзакции).
    """
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO deals (deal_id, status, version, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(deal_id) DO UPDATE SET
                status = excluded.status,
                version = excluded.version,
                updated_at = excluded.updated_at
            """,
            (event.deal_id, event.status, event.version, event.occurred_at.isoformat()),
        )
    return "applied"


def get_deal(deal_id: str) -> Deal | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT deal_id, status, version, updated_at FROM deals WHERE deal_id = ?",
            (deal_id,),
        ).fetchone()
    if row is None:
        return None
    return Deal(**dict(row))
