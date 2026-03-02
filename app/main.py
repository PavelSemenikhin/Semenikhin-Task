import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from prometheus_client import Counter, Histogram, CONTENT_TYPE_LATEST, generate_latest

from app.api.routes.events import router as events_router
from app.api.routes.stats import router as stats_router
from app.core.config import settings
from app.core.nats_client import connect_nats, close_nats
from app.db.base import init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    if settings.NATS_URL:
        await connect_nats()
    yield
    if settings.NATS_URL:
        await close_nats()


app = FastAPI(lifespan=lifespan)

REQUEST_COUNT = Counter(
    "backend_requests_total",
    "HTTP-запити до сервісу",
    ["method", "endpoint", "http_status"],
)

REQUEST_DURATION = Histogram(
    "backend_request_duration_seconds",
    "Тривалість обробки HTTP-запитів",
    ["method", "endpoint"],
)


@app.middleware("http")
async def prometheus_metrics(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    REQUEST_COUNT.labels(
        request.method,
        request.url.path,
        str(response.status_code),
    ).inc()
    REQUEST_DURATION.labels(request.method, request.url.path).observe(time.time() - start)
    return response


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


app.include_router(stats_router)
app.include_router(events_router)
