"""Оценка 9: проверка подписи webhook (HMAC-SHA256)."""

import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import EVENTS_DIR, load

pytestmark = pytest.mark.advanced

SECRET = "test-secret"
EVENT = load(EVENTS_DIR / "scenarios" / "01_normal_flow.json")["events"][0]


def sign(body: bytes, secret: str = SECRET) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


@pytest.fixture
def signed_client(db_path, monkeypatch):
    monkeypatch.setenv("WEBHOOK_SECRET", SECRET)
    with TestClient(app) as c:
        yield c


def post_raw(client, body: bytes, signature: str | None):
    headers = {"Content-Type": "application/json"}
    if signature is not None:
        headers["X-CRM-Signature"] = signature
    return client.post("/webhooks/crm", content=body, headers=headers)


def test_valid_signature_accepted(signed_client):
    body = json.dumps(EVENT).encode()
    response = post_raw(signed_client, body, sign(body))
    assert response.status_code == 200
    assert response.json()["result"] == "applied"


def test_missing_signature_rejected(signed_client):
    body = json.dumps(EVENT).encode()
    assert post_raw(signed_client, body, None).status_code == 401
    assert signed_client.get(f"/deals/{EVENT['deal_id']}").status_code == 404


def test_wrong_secret_rejected(signed_client):
    body = json.dumps(EVENT).encode()
    assert post_raw(signed_client, body, sign(body, "other")).status_code == 401


def test_tampered_body_rejected(signed_client):
    body = json.dumps(EVENT).encode()
    signature = sign(body)
    tampered = json.dumps(dict(EVENT, status="won")).encode()
    assert post_raw(signed_client, tampered, signature).status_code == 401


def test_signature_checked_before_validation(signed_client):
    """Неподписанный запрос отклоняется с 401, даже если тело некорректно."""
    assert post_raw(signed_client, b"{}", None).status_code == 401


def test_no_secret_means_no_check(client):
    response = client.post("/webhooks/crm", json=EVENT)
    assert response.status_code == 200
