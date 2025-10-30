import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.api.routes.stats import router as stats_router
from app.api.routes.events import router as events_router
from app.core.nats_client import connect_nats, close_nats

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_nats()
    yield
    await close_nats()


app = FastAPI(lifespan=lifespan)

app.include_router(stats_router)
app.include_router(events_router)
