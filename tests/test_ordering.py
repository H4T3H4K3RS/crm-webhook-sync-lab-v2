"""Нарушение порядка доставки (версионирование)."""

from tests.conftest import EVENTS_DIR, assert_deal, load, send

OUT_OF_ORDER = load(EVENTS_DIR / "scenarios" / "03_out_of_order.json")
SAME_VERSION = load(EVENTS_DIR / "scenarios" / "05_same_version_conflict.json")


def test_older_event_after_newer_is_stale(client):
    v1, v3, v2 = OUT_OF_ORDER["events"]
    send(client, v1)
    send(client, v3)
    response = send(client, v2)
    assert response.status_code == 200
    assert response.json()["result"] == "stale"
    assert_deal(client, v3["deal_id"], v3["status"], v3["version"])


def test_first_event_can_have_any_version(client):
    """Первое пришедшее событие сделки применяется, даже если его version > 1."""
    _, v3, v2 = OUT_OF_ORDER["events"]
    assert send(client, v3).json()["result"] == "applied"
    assert send(client, v2).json()["result"] == "stale"
    assert_deal(client, v3["deal_id"], v3["status"], v3["version"])


def test_version_gaps_are_allowed(client):
    v1, v3, _ = OUT_OF_ORDER["events"]
    assert send(client, v1).json()["result"] == "applied"
    assert send(client, v3).json()["result"] == "applied"


def test_same_version_different_event_is_stale(client):
    results = [send(client, e).json()["result"] for e in SAME_VERSION["events"]]
    assert results == SAME_VERSION["expected_results"]
    final = SAME_VERSION["expected_final_state"][0]
    assert_deal(client, final["deal_id"], final["status"], final["version"])


def test_stale_event_redelivered_is_duplicate(client):
    """Устаревшее событие тоже считается обработанным: его повторная доставка — duplicate."""
    v1, v3, v2 = OUT_OF_ORDER["events"]
    send(client, v1)
    send(client, v3)
    assert send(client, v2).json()["result"] == "stale"
    assert send(client, v2).json()["result"] == "duplicate"
