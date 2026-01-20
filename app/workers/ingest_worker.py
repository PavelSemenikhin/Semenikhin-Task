import asyncio
import json
import logging
from datetime import datetime
from sqlalchemy.dialects.postgresql import insert

from app.core.nats_client import connect_nats, subscribe, close_nats
from app.db.base import AsyncPostgresqlSessionLocal, init_db
from app.db.models import Event

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


async def handle_event(payload):
    if isinstance(payload, str):
        payload = json.loads(payload)

    events = payload.get("events", [payload])

    inserted = 0
    async with AsyncPostgresqlSessionLocal() as session:
        for e in events:
            try:
                occurred_at = (
                    datetime.fromisoformat(
                        e["occurred_at"].replace("Z", "+00:00")
                    )
                    if isinstance(e["occurred_at"], str)
                    else e["occurred_at"]
                )

                stmt = (
                    insert(Event)
                    .values(
                        event_id=e["event_id"],
                        occurred_at=occurred_at,
                        user_id=e["user_id"],
                        event_type=e["event_type"],
                        properties=e.get("properties", {}),
                    )
                    .on_conflict_do_nothing(index_elements=["event_id"])
                )
                result = await session.execute(stmt)
                if result.rowcount:
                    inserted += result.rowcount
            except Exception as exc:
                logger.exception(
                    f"Failed to insert event: {e} | Error: {exc}"
                )  # noqa

        await session.commit()
        logger.info(f"Inserted {inserted} events from NATS")


async def main():
    logger.info("Starting ingest worker...")
    await init_db()
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
