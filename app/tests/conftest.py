import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.db import base
from app.db.models import Base
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


@pytest.fixture(scope="function")
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as cl:
        yield cl
