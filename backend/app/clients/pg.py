import logging
from collections.abc import AsyncGenerator
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import envs
from app.core.logging import LogCategory, LogLayer, AppLoggerAdapter, extra_

logger = AppLoggerAdapter(
    logging.getLogger(__name__),
    {
        "layer": LogLayer.DB,
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
    logger.info(
        "PostgreSQL engine initialized",
        extra=extra_(
            operation="init_postgres",
            status="success",
            host=envs.PG_DB_HOST,
            port=envs.PG_DB_PORT,
            db=envs.PG_DB_NAME,
            pool_size=envs.PG_MIN_CONNECTION,
            max_overflow=envs.PG_MAX_CONNECTION,
        ),
    )


async def get_pgdb() -> AsyncGenerator[AsyncSession | Any, Any]:
    async with AsyncSessionLocal() as session:
        logger.debug(
            "PostgreSQL session acquired",
            extra=extra_(operation="get_pgdb", status="start"),
        )
        
        try:
            yield session
        
        finally:
            logger.debug(
                "PostgreSQL session released",
                extra=extra_(operation="get_pgdb", status="success"),
            )


async def close_postgres() -> None:
    try:
        await engine.dispose()
        logger.info(
            "PostgreSQL engine disposed",
            extra=extra_(operation="close_postgres", status="success"),
        )
    except Exception:
        logger.exception(
            "Failed to dispose PostgreSQL engine",
            extra=extra_(operation="close_postgres", status="failure"),
        )
