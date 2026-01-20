import uuid
import pytest


@pytest.mark.asyncio
async def test_idempotent_insert(client):
    event = {
        "event_id": str(uuid.uuid4()),
        "occurred_at": "2025-10-28T10:00:00Z",
        "user_id": 1,
        "event_type": "login",
        "properties": {"country": "UA"},
    }

    payload = [event]

    r1 = await client.post("/events", json=payload)
    assert r1.status_code == 202
    assert r1.json() == {"published": 1, "status": "queued"}

    r2 = await client.post("/events", json=payload)
    assert r2.status_code == 202
    assert r2.json() == {"published": 1, "status": "queued"}
