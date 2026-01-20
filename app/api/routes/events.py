from fastapi import APIRouter, status, Depends, HTTPException

from app.api.schemas.events import EventBatch
from app.core.nats_client import publish
from app.core.rate_limiter import rate_limiter

router = APIRouter(tags=["Events"])


@router.post(
    "/events",
    status_code=status.HTTP_202_ACCEPTED,
    description="Publish events to NATS for async ingestion",
    dependencies=[Depends(rate_limiter)],
)
@router.post(
    "/events/ingest/",
    status_code=status.HTTP_202_ACCEPTED,
    description="Publish events to NATS for async ingestion",
    dependencies=[Depends(rate_limiter)],
)
async def events_ingestion(payload: EventBatch):
    published = 0

    try:
        for event in payload.events:
            await publish("events.ingest", event.model_dump(mode="json"))
            published += 1
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to publish events: {exc}",
        ) from exc

    return {"published": published, "status": "queued"}
