import uuid
import pytest


@pytest.mark.asyncio
async def test_ingest_to_dau_stats(client):
    events = [
        {
            "event_id": str(uuid.uuid4()),
            "occurred_at": "2025-10-28T10:00:00Z",
            "user_id": 1,
            "event_type": "login",
            "properties": {"country": "UA"},
        },
        {
            "event_id": str(uuid.uuid4()),
            "occurred_at": "2025-10-28T12:00:00Z",
            "user_id": 2,
            "event_type": "login",
            "properties": {"country": "UA"},
        },
        {
            "event_id": str(uuid.uuid4()),
            "occurred_at": "2025-10-29T09:00:00Z",
            "user_id": 1,
            "event_type": "purchase",
            "properties": {"amount": 10},
        },
    ]

    ingest = await client.post("/events", json=events)
    assert ingest.status_code == 202
    assert ingest.json() == {"published": 3, "status": "queued"}

    dau = await client.get(
        "/stats/dau/",
        params={"from": "2025-10-28", "to": "2025-10-29"},
    )
    assert dau.status_code == 200
    assert dau.json() == [
        {"date": "2025-10-28", "dau": 2},
        {"date": "2025-10-29", "dau": 1},
    ]
