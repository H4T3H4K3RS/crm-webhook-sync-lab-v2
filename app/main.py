"""REST API сервиса синхронизации статусов сделок."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from app.db import init_db
from app.schemas import Deal, DealStatusChangedEvent, WebhookResult
from app.service import get_deal, process_event


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="CRM Webhook Sync", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/webhooks/crm", response_model=WebhookResult)
def receive_webhook(event: DealStatusChangedEvent) -> WebhookResult:
    # TODO (дополнительно, оценка 9): проверка подписи X-CRM-Signature.
    result = process_event(event)
    return WebhookResult(result=result, event_id=event.event_id, deal_id=event.deal_id)


@app.get("/deals/{deal_id}", response_model=Deal)
def read_deal(deal_id: str) -> Deal:
    deal = get_deal(deal_id)
    if deal is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal
