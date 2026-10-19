"""Обычная обработка событий."""

from tests.conftest import EVENTS_DIR, assert_deal, load, send

NORMAL = load(EVENTS_DIR / "scenarios" / "01_normal_flow.json")


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_unknown_deal_returns_404(client):
    assert client.get("/deals/D-NOPE").status_code == 404


def test_first_event_creates_deal(client):
    event = NORMAL["events"][0]
    response = send(client, event)
    assert response.status_code == 200
    assert response.json() == {
        "result": "applied",
        "event_id": event["event_id"],
        "deal_id": event["deal_id"],
    }
    assert_deal(client, event["deal_id"], event["status"], event["version"])


def test_events_in_order_update_status(client):
    for event in NORMAL["events"]:
        assert send(client, event).json()["result"] == "applied"
    final = NORMAL["expected_final_state"][0]
    assert_deal(client, final["deal_id"], final["status"], final["version"])


def test_deal_updated_at_matches_last_applied_event(client):
    for event in NORMAL["events"]:
        send(client, event)
    body = client.get("/deals/D-1001").json()
    assert body["updated_at"].startswith(NORMAL["events"][-1]["occurred_at"].rstrip("Z"))
