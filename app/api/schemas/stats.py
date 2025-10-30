from pydantic import BaseModel
from datetime import date


class DAUItem(BaseModel):
    date: date
    dau: int


class TopEventItem(BaseModel):
    event_type: str
    count: int


class RetentionEventItem(BaseModel):
    cohort_date: date
    total_users: int
    retention_rate: list[float | None]
