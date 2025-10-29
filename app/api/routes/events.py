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
    inserted = 0
    skipped = 0

    for event in payload.events:
        stmt = select(Event).where(Event.event_id == event.event_id)
        result = await db.execute(stmt)
        existing_event = result.scalar_one_or_none()

        if existing_event:
            skipped += 1
            continue

        new_event = Event(
            event_id=event.event_id,
            occurred_at=event.occurred_at,
            user_id=event.user_id,
            event_type=event.event_type,
            properties=event.properties,
        )

        db.add(new_event)
        inserted += 1

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database integrity error during ingestion",
        )

    return {
        "inserted": inserted,
        "skipped": skipped,
        "total": inserted + skipped,
    }
