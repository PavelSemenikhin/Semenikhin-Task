import asyncio
import json
import logging
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from app.core.nats_client import connect_nats, subscribe, close_nats
from app.db.base import AsyncPostgresqlSessionLocal
from app.db.models import Event

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


async def handle_event(payload):
    try:
        if isinstance(payload, str):
            payload = json.loads(payload)

        events = payload.get("events", [payload])

        async with AsyncPostgresqlSessionLocal() as session:
            for e in events:
                occurred_at = (
                    datetime.fromisoformat(e["occurred_at"].replace("Z", "+00:00"))
                    if isinstance(e["occurred_at"], str)
                    else e["occurred_at"]
                )

                event = Event(
                    event_id=e["event_id"],
                    occurred_at=occurred_at,
                    user_id=e["user_id"],
                    event_type=e["event_type"],
                    properties=e.get("properties", {}),
                )
                session.add(event)

            await session.commit()
            logger.info(f"Inserted {len(events)} events from NATS")

    except IntegrityError:
        await session.rollback()
        logger.warning("Skipped duplicate or invalid events batch")
    except Exception as e:
        logger.exception(f"Failed to insert events batch: {payload} | Error: {e}")


async def main():
    logger.info("Starting ingest worker...")
    await connect_nats()
    await subscribe("events.ingest", handle_event)

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Worker interrupted, shutting down...")
    finally:
        await close_nats()


if __name__ == "__main__":
    asyncio.run(main())
