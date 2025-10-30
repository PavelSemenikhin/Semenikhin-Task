from fastapi import APIRouter, status, Depends

from app.api.schemas.events import EventBatch
from app.core.nats_client import publish
from app.core.rate_limiter import rate_limiter

router = APIRouter(prefix="/events", tags=["Events"])


@router.post(
    "/ingest/",
    status_code=status.HTTP_202_ACCEPTED,
    description="Publish events to NATS for async ingestion",
    dependencies=[Depends(rate_limiter)]
)
async def events_ingestion(
        payload: EventBatch,
):
    published = 0

    for event in payload.events:
        await publish("events.ingest", event.model_dump_json())
        published += 1

    return {
        "published": published,
        "status": "queued"
    }
