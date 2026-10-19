"""Некорректные входные данные."""

import pytest

from tests.conftest import INVALID, load, send


@pytest.mark.parametrize("path", INVALID, ids=[p.stem for p in INVALID])
def test_invalid_payload_rejected(client, path):
    case = load(path)
    response = send(client, case["payload"])
    assert response.status_code == 422, case["description"]
    assert client.get("/deals/D-9001").status_code == 404, "некорректное событие не должно менять данные"


def test_malformed_json_rejected(client):
    response = client.post(
        "/webhooks/crm", content=b"{not json", headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422


def test_invalid_event_is_not_marked_processed(client):
    """После исправления данных CRM может повторить событие с тем же event_id — оно должно примениться."""
    bad = load(INVALID[4])["payload"]  # unknown_status
    assert send(client, bad).status_code == 422
    fixed = dict(bad, status="new")
    assert send(client, fixed).json()["result"] == "applied"
