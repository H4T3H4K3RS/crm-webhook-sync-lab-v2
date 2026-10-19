"""Оценка 10: конкурентная доставка и конфликт event_id."""

import random
from concurrent.futures import ThreadPoolExecutor

import pytest

from app.db import init_db
from app.schemas import DealStatusChangedEvent
from app.service import get_deal, process_event
from tests.conftest import EVENTS_DIR, load, send

pytestmark = pytest.mark.advanced

STATUSES = ["new", "qualification", "proposal", "negotiation", "won", "lost"]


def make_event(version: int, deal_id: str = "D-7001") -> DealStatusChangedEvent:
    return DealStatusChangedEvent(
        event_id=f"evt_{deal_id}_v{version}",
        event_type="deal.status_changed",
        deal_id=deal_id,
        status=STATUSES[version % len(STATUSES)],
        version=version,
        occurred_at=f"2026-10-01T09:{version:02d}:00Z",
    )


def test_parallel_redelivery_applied_once(db_path):
    init_db()
    event = make_event(1)
    with ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(lambda _: process_event(event), range(40)))
    assert results.count("applied") == 1
    assert results.count("duplicate") == 39


def test_parallel_out_of_order_keeps_latest(db_path):
    init_db()
    events = [make_event(v) for v in range(1, 41)]
    random.Random(42).shuffle(events)
    with ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(process_event, events))
    assert "duplicate" not in results
    deal = get_deal("D-7001")
    assert deal.version == 40
    assert deal.status.value == STATUSES[40 % len(STATUSES)]


def test_reused_event_id_with_different_payload_is_conflict(client):
    event = load(EVENTS_DIR / "scenarios" / "01_normal_flow.json")["events"][0]
    assert send(client, event).json()["result"] == "applied"
    tampered = dict(event, status="won")
    assert send(client, tampered).status_code == 409
    assert send(client, event).json()["result"] == "duplicate"
