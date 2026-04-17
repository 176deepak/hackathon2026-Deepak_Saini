import logging
from collections.abc import AsyncGenerator
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import envs
from app.core.logging import (
    LogCategory, LogEvent, LogLayer, LogStatus, AppLoggerAdapter, extra_,
)

logger = AppLoggerAdapter(
    logging.getLogger(__name__),
    {
        "layer": LogLayer.CLIENT,
        "category": LogCategory.DATABASE,
        "component": __name__,
    },
)


DATABASE_URL = (
    f"postgresql+asyncpg://{envs.PG_DB_USER}:"
    f"{envs.PG_DB_PASSWORD}@"
    f"{envs.PG_DB_HOST}:"
    f"{envs.PG_DB_PORT}/"
    f"{envs.PG_DB_NAME}"
)

engine = create_async_engine(
    DATABASE_URL,
    pool_size=envs.PG_MIN_CONNECTION,
    max_overflow=envs.PG_MAX_CONNECTION,
    pool_pre_ping=True,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_postgres() -> None:
    pass


async def get_pgdb() -> AsyncGenerator[AsyncSession | Any, Any]:
    async with AsyncSessionLocal() as session:
        logger.debug(
            "PostgreSQL session acquired",
            extra=extra_(
                operation="get_pgdb",
                status=LogStatus.ACQUIRED,
                event=LogEvent.DB_QUERY,
            ),
        )
        
        try:
            yield session
        
        finally:
            logger.info(
                "PostgreSQL session released",
                extra=extra_(
                    operation="get_pgdb",
                    status=LogStatus.RELEASED,
                    event=LogEvent.DB_QUERY,
                ),
            )


async def close_postgres() -> None:
    await engine.dispose()
