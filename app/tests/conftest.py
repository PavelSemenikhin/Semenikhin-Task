import pytest
from datetime import datetime
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy.exc import IntegrityError
from app.db import base
from app.db.models import Base, Event
from app.core.config import settings
from app.main import app


@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(test_engine):
    async_session = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    async with async_session() as session:
        yield session


@pytest.fixture(scope="function", autouse=True)
async def override_base_dependencies(db_session, test_engine):

    base.ENGINE = test_engine

    base.AsyncPostgresqlSessionLocal = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    async def override_get_db():
        async with db_session as session:
            yield session

    base.get_db = override_get_db


@pytest.fixture(scope="function", autouse=True)
async def override_nats_and_publish(db_session, monkeypatch):
    from app.api.routes import events as events_routes

    settings.NATS_URL = None

    async def fake_publish(subject, data):
        event_data = dict(data)
        event_id = event_data.get("event_id")
        if isinstance(event_id, str):
            event_data["event_id"] = uuid.UUID(event_id)
        occurred_at = event_data.get("occurred_at")
        if isinstance(occurred_at, str):
            event_data["occurred_at"] = datetime.fromisoformat(
                occurred_at.replace("Z", "+00:00")
            )
        event = Event(**event_data)
        db_session.add(event)
        try:
            await db_session.commit()
        except IntegrityError:
            await db_session.rollback()
        except Exception:
            await db_session.rollback()
            raise

    monkeypatch.setattr(events_routes, "publish", fake_publish)


@pytest.fixture(scope="function")
async def client(override_nats_and_publish):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as cl:
        yield cl
