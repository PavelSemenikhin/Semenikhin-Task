from datetime import datetime
import uuid
from typing import List

from pydantic import BaseModel


class EventItem(BaseModel):
    event_id: uuid.UUID
    occurred_at: datetime
    user_id: int
    event_type: str
    properties: dict[str, str] | None = None


class EventBatch(BaseModel):
    events: List[EventItem]
