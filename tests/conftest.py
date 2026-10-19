import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

EVENTS_DIR = Path(__file__).resolve().parent.parent / "events"
SCENARIOS = sorted((EVENTS_DIR / "scenarios").glob("*.json"))
INVALID = sorted((EVENTS_DIR / "invalid").glob("*.json"))


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_PATH", str(path))
    monkeypatch.delenv("WEBHOOK_SECRET", raising=False)
    return path


@pytest.fixture
def client(db_path):
    with TestClient(app) as c:
        yield c


def send(client: TestClient, event: dict):
    return client.post("/webhooks/crm", json=event)


def assert_deal(client: TestClient, deal_id: str, status: str, version: int):
    response = client.get(f"/deals/{deal_id}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == status
    assert body["version"] == version
