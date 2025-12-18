import uuid
import pytest
import asyncio


@pytest.mark.asyncio
async def test_idempotent_insert(client):
    event = {
        "event_id": str(uuid.uuid4()),
        "occurred_at": "2025-10-28T10:00:00Z",
        "user_id": 1,
        "event_type": "login",
        "properties": {"country": "UA"},
    }

    payload = {"events": [event]}

    r1 = await client.post("/events/ingest/", json=payload)
    assert r1.status_code == 202
    assert r1.json() == {"published": 1, "status": "queued"}

    await asyncio.sleep(2)

    r2 = await client.post("/events/ingest/", json=payload)
    assert r2.status_code == 202
    assert r2.json() == {"published": 1, "status": "queued"}
