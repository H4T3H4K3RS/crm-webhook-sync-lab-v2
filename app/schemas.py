"""Модели входящих webhook-событий и ответов API."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class DealStatus(str, Enum):
    """Допустимые статусы сделки в CRM."""

    NEW = "new"
    QUALIFICATION = "qualification"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"


class DealStatusChangedEvent(BaseModel):
    """Событие CRM `deal.status_changed`.

    TODO (этап 4): добавьте валидацию входных данных:
      - event_type допускает только значение "deal.status_changed";
      - event_id и deal_id — непустые строки;
      - status — только значения из DealStatus;
      - version — целое число >= 1;
      - лишние поля в теле запроса запрещены.
    Подсказка: Literal, Field(min_length=..., ge=...), model_config.
    """

    event_id: str
    event_type: str
    deal_id: str
    status: str
    version: int
    occurred_at: datetime


class WebhookResult(BaseModel):
    """Ответ на приём webhook.

    result:
      - "applied"   — событие применено, статус сделки обновлён;
      - "duplicate" — событие с таким event_id уже обрабатывалось;
      - "stale"     — событие устарело (version не больше текущей), данные не изменены.
    """

    result: str
    event_id: str
    deal_id: str


class Deal(BaseModel):
    """Актуальное состояние сделки."""

    deal_id: str
    status: DealStatus
    version: int
    updated_at: datetime
