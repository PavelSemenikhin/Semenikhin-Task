from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.events import EventBatch
from app.db.base import get_db
from app.db.models import Event

router = APIRouter(prefix="/events", tags=["Events"])


@router.post(
    "/ingest/",
    status_code=status.HTTP_201_CREATED,
    description="Ingest events",
)
async def events_ingestion(
        payload: EventBatch,
        db: AsyncSession = Depends(get_db),
):
    event_ids = [e.event_id for e in payload.events]

    stmt = select(Event.event_id).where(Event.event_id.in_(event_ids))
    result = await db.execute(stmt)
    existing_ids = {row[0] for row in result.all()}

    new_events = []
    for event in payload.events:
        if event.event_id in existing_ids:
            continue

        new_events.append(Event(
            event_id=event.event_id,
            occurred_at=event.occurred_at,
            user_id=event.user_id,
            event_type=event.event_type,
            properties=event.properties,
        ))

    db.add_all(new_events)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database integrity error during ingestion",
        )

    return {
        "inserted": len(new_events),
        "skipped": len(existing_ids),
        "total": len(payload.events),
    }
