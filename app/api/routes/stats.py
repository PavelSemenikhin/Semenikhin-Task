from fastapi import APIRouter, Depends, HTTPException, status, Query
from datetime import date

from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.stats import DAUItem, TopEventItem, RetentionEventItem
from app.db.base import get_db
from app.db.models import Event

router = APIRouter(prefix="/stats", tags=["Stats"])


@router.get(
    "/dau/",
    response_model=list[DAUItem],
    status_code=status.HTTP_200_OK,
    summary="Daily Active Users (DAU)",
    description="Get DAU stats",
)
async def get_dau(
    from_date: date = Query(example="2025-01-01"),
    to_date: date = Query(example="2025-12-31"),
    segment: str | None = Query(None, example="purchase"),
    db: AsyncSession = Depends(get_db),
):
    if from_date > to_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{from_date} cannot be after {to_date}",
        )

    stmt = select(
        func.date(Event.occurred_at).label("date"),
        func.count(distinct(Event.user_id)).label("dau"),
    ).where(func.date(Event.occurred_at).between(from_date, to_date))

    if segment:
        stmt = stmt.where(Event.event_type == segment)

    stmt = stmt.group_by(func.date(Event.occurred_at)).order_by(
        func.date(Event.occurred_at)
    )

    result = await db.execute(stmt)
    rows = result.mappings().all()

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
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
            detail=f"{from_date} cannot be after {to_date}",
        )

    stmt = (
        select(Event.event_type, func.count().label("count"))
        .where(Event.occurred_at.between(from_date, to_date))
        .group_by(Event.event_type)
        .order_by(func.count().desc())
        .limit(limit)
    )

    result = await db.execute(stmt)
    rows = result.mappings().all()

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )

    return [TopEventItem(**row) for row in rows]


@router.get(
    "/retention/",
    response_model=list[RetentionEventItem],
    status_code=status.HTTP_200_OK,
    description="Get retention events",
)
async def get_retention(
    start_date: date,
    windows: int = 3,
    db: AsyncSession = Depends(get_db),
):
    first_seen_subquery = (
        select(
            Event.user_id,
            func.min(func.date(Event.occurred_at)).label(
                "first_seen",
            ),
        )
        .group_by(Event.user_id)
        .subquery()
    )

    stmt = (
        select(
            first_seen_subquery.c.first_seen.label("cohort_date"),
            func.date_part(
                "day", Event.occurred_at - first_seen_subquery.c.first_seen
            ).label("day_number"),
            func.count(func.distinct(Event.user_id)).label("users"),
        )
        .join(
            first_seen_subquery,
            Event.user_id == first_seen_subquery.c.user_id,
        )
        .where(first_seen_subquery.c.first_seen >= start_date)
        .group_by(first_seen_subquery.c.first_seen, "day_number")
        .order_by(first_seen_subquery.c.first_seen, "day_number")
    )

    result = await db.execute(stmt)
    rows = result.mappings().all()
    if not rows:
        raise HTTPException(status_code=404, detail="Not found")

    cohorts: dict[date, dict[int, int]] = {}
    for row in rows:
        cohort = row["cohort_date"]
        day = int(row["day_number"])
        users = row["users"]
        cohorts.setdefault(cohort, {})[day] = users

    response = []
    for cohort_date, days in cohorts.items():
        total_users = days.get(0, 0)
        if not total_users:
            continue

        retention_rate = []
        for day in range(1, windows + 1):
            if day in days:
                retention_rate.append(round(days[day] / total_users, 2))
            else:
                retention_rate.append(None)

        response.append(
            RetentionEventItem(
                cohort_date=cohort_date,
                total_users=total_users,
                retention_rate=retention_rate,
            )
        )

    return response


@router.get("/count/")
async def get_events(db: AsyncSession = Depends(get_db)):
    stmt = select(Event).order_by(Event.event_id)
    result = await db.execute(stmt)
    count = result.scalars().all()
    count_of_events = len(count)
    return {
        "count": count_of_events,
    }
