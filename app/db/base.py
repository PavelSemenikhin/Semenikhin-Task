from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.config import settings


DATABASE_ASYNC_URL = (
    f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@"
    f"{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)


postgresql_engine = create_async_engine(DATABASE_ASYNC_URL, echo=False)

ENGINE = postgresql_engine

AsyncPostgresqlSessionLocal = async_sessionmaker(
    bind=ENGINE,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncPostgresqlSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()