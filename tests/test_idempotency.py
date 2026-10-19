"""Повторная доставка событий (идемпотентность)."""

from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import EVENTS_DIR, assert_deal, load, send

NORMAL = load(EVENTS_DIR / "scenarios" / "01_normal_flow.json")
DUPLICATES = load(EVENTS_DIR / "scenarios" / "02_duplicate_delivery.json")


def test_same_event_twice_is_duplicate(client):
    event = NORMAL["events"][0]
    assert send(client, event).json()["result"] == "applied"
    second = send(client, event)
    assert second.status_code == 200
    assert second.json()["result"] == "duplicate"


def test_duplicate_does_not_change_state(client):
    first, second = NORMAL["events"][0], NORMAL["events"][1]
    send(client, first)
    send(client, second)
    assert send(client, first).json()["result"] == "duplicate"
    assert_deal(client, second["deal_id"], second["status"], second["version"])


def test_many_redeliveries(client):
    event = NORMAL["events"][0]
    results = [send(client, event).json()["result"] for _ in range(5)]
    assert results == ["applied"] + ["duplicate"] * 4


def test_duplicate_detected_after_restart(db_path):
    """Сведения об обработанных событиях должны храниться в БД, а не в памяти процесса."""
    event = NORMAL["events"][0]
    with TestClient(app) as c:
        assert send(c, event).json()["result"] == "applied"
    with TestClient(app) as c:
        assert send(c, event).json()["result"] == "duplicate"
        assert_deal(c, event["deal_id"], event["status"], event["version"])


def test_duplicate_delivery_scenario(client):
    results = [send(client, e).json()["result"] for e in DUPLICATES["events"]]
    assert results == DUPLICATES["expected_results"]
    final = DUPLICATES["expected_final_state"][0]
    assert_deal(client, final["deal_id"], final["status"], final["version"])
