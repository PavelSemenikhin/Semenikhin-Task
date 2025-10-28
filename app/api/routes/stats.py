from fastapi import APIRouter, Depends, HTTPException, status
from datetime import date

from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.stats import DAUItem, TopEventItem
from app.db.base import get_db
from app.db.models import Event

router = APIRouter(prefix="/stats", tags=["Stats"])


@router.get(
    "/dau/",
    response_model=list[DAUItem],
    status_code=status.HTTP_200_OK,
    description="Get DAU stats",

)
async def get_dau(
        from_date: date,
        to_date: date,
        db: AsyncSession = Depends(get_db)
):
    if from_date > to_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{from_date} cannot be after {to_date}"
        )

    stmt = (
        select(
            func.date(Event.occurred_at).label("date"),
            func.count(distinct(Event.user_id)).label("dau")
        )
        .where(Event.occurred_at.between(from_date, to_date))
        .group_by(func.date(Event.occurred_at))
        .order_by(func.date(Event.occurred_at))
    )

    result = await db.execute(stmt)
    rows = result.mappings().all()
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found"
        )

    return [DAUItem(**row) for row in rows]


@router.get(
    "/top_event/",
    response_model=list[TopEventItem],
    status_code=status.HTTP_200_OK,
    description="Get top event types",
)
async def get_top_event_type(
        from_date: date,
        to_date: date,
        limit: int = 10,
        db: AsyncSession = Depends(get_db),
):
    if from_date > to_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{from_date} cannot be after {to_date}"
        )

    stmt = (
        select(
            Event.event_type,
            func.count().label("count")
        )
        .where(Event.occurred_at.between(from_date, to_date))
        .group_by(Event.event_type)
        .order_by(func.count().desc())
        .limit(limit))

    result = await db.execute(stmt)
    rows = result.mappings().all()

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found"
        )

    return [TopEventItem(**row) for row in rows]
