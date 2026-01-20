from datetime import datetime
import uuid
from typing import Any

from pydantic import BaseModel, model_validator


class EventItem(BaseModel):
    event_id: uuid.UUID
    occurred_at: datetime
    user_id: int
    event_type: str
    properties: dict[str, Any] | None = None


class EventBatch(BaseModel):
    events: list[EventItem]

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, data):
        if isinstance(data, list):
            return {"events": data}
        return data
