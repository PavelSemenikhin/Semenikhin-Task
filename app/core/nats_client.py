import json
import logging
from nats.aio.client import Client as NATS
from nats.aio.errors import ErrConnectionClosed, ErrTimeout, ErrNoServers

from app.core.config import settings

logger = logging.getLogger(__name__)

nc: NATS | None = None


async def connect_nats() -> NATS:
    global nc
    if nc and nc.is_connected:
        return nc

    try:
        nc = NATS()
        await nc.connect(servers=[settings.NATS_URL])
        logger.info(f"Connected to NATS at {settings.NATS_URL}")
        return nc
    except ErrNoServers:
        logger.error("NATS: no available servers")
        raise
    except Exception as e:
        logger.exception(f"Failed to connect to NATS: {e}")
        raise


async def publish(subject: str, data: dict) -> None:
    if not nc or not nc.is_connected:
        await connect_nats()

    try:
        payload = json.dumps(data).encode()
        await nc.publish(subject, payload)
        logger.debug(f"Published to {subject}: {data}")
    except (ErrConnectionClosed, ErrTimeout) as e:
        logger.warning(f"Publish failed ({e}), reconnecting...")
        await connect_nats()
        await nc.publish(subject, json.dumps(data).encode())
    except Exception as e:
        logger.exception(f"Error publishing to {subject}: {e}")


async def subscribe(subject: str, handler) -> None:
    if not nc or not nc.is_connected:
        await connect_nats()

    async def internal_handler(msg):
        try:
            payload = json.loads(msg.data.decode())
            await handler(payload)
        except Exception as e:
            logger.exception(f"Handler error for {subject}: {e}")

    await nc.subscribe(subject, cb=internal_handler)
    logger.info(f"Subscribed to {subject}")


async def close_nats():
    global nc # noqa
    if nc and nc.is_connected:
        await nc.drain()
        logger.info("NATS connection closed")
