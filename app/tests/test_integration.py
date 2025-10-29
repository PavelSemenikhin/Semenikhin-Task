import uuid
import pytest
from datetime import datetime, UTC


@pytest.mark.asyncio
async def test_ingest_and_dau_stats(client):
    today = datetime.now(UTC).date()
    events = [
        {
            "event_id": str(uuid.uuid4()),
            "occurred_at": f"{today}T10:00:00Z",
            "user_id": 1,
            "event_type": "login",
            "properties": {"country": "UA"},
        },
        {
            "event_id": str(uuid.uuid4()),
            "occurred_at": f"{today}T11:00:00Z",
            "user_id": 2,
            "event_type": "click",
            "properties": {"country": "PL"},
        },
    ]

    r = await client.post("/events/ingest/", json={"events": events})
    assert r.status_code == 201
    assert r.json()["inserted"] == 2

    resp = await client.get(f"/stats/dau/?from_date={today}&to_date={today}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["dau"] == 2
