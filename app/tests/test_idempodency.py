import uuid
import pytest


@pytest.mark.asyncio
async def test_idempotent_insert(client):
    event = {
        "event_id": str(uuid.uuid4()),
        "occurred_at": "2025-10-28T10:00:00Z",
        "user_id": 1,
        "event_type": "login",
        "properties": {"country": "UA"}
    }

    payload = {"events": [event]}

    r1 = await client.post("/events/ingest/", json=payload)
    assert r1.status_code == 201
    assert r1.json()["inserted"] == 1
    assert r1.json()["skipped"] == 0

    r2 = await client.post("/events/ingest/", json=payload)
    assert r2.status_code == 201
    assert r2.json()["inserted"] == 0
    assert r2.json()["skipped"] == 1
