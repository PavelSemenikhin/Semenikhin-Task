from fastapi import APIRouter, status

from app.api.schemas.events import EventBatch
from app.core.nats_client import publish

router = APIRouter(prefix="/events", tags=["Events"])


@router.post(
    "/ingest/",
    status_code=status.HTTP_202_ACCEPTED,
    description="Publish events to NATS for async ingestion",
)
async def events_ingestion(payload: EventBatch):
    published = 0

    for event in payload.events:
        await publish("events.ingest", event.model_dump_json())
        published += 1

    return {
        "published": published,
        "status": "queued"
    }
