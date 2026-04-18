import logging
from redis.asyncio import Redis

from app.core.config import envs
from app.core.logging import LogCategory, LogLayer, AppLoggerAdapter, extra_

logger = AppLoggerAdapter(
    logging.getLogger(__name__),
    {
        "layer": LogLayer.CACHE,
        "category": LogCategory.CACHE,
        "component": __name__,
    },
)

_redis: Redis | None = None


async def init_redis():
    global _redis
    try:
        _redis = Redis.from_url(envs.redis_uri, decode_responses=False)
        # Ping early so failures happen at startup, not first request.
        await _redis.ping()
        logger.info(
            "Redis initialized",
            extra=extra_(
                operation="init_redis",
                status="success",
                redis_db=envs.REDIS_DB,
                redis_host=envs.REDIS_HOST,
                redis_port=envs.REDIS_PORT,
            ),
        )
    except Exception:
        logger.exception(
            "Redis initialization failed",
            extra=extra_(
                operation="init_redis",
                status="failure",
                redis_db=envs.REDIS_DB,
                redis_host=envs.REDIS_HOST,
                redis_port=envs.REDIS_PORT,
            ),
        )
        raise


def get_redis() -> Redis:
    
    if _redis is None:
        logger.error(
            "Redis client not initialized",
            extra=extra_(operation="get_redis", status="failure"),
        )
        raise RuntimeError("Redis client not initialized")

    logger.debug(
        "Redis client returned",
        extra=extra_(operation="get_redis", status="success"),
    )
    return _redis


async def close_redis():
    global _redis
    if not _redis:
        return

    try:
        await _redis.close()
        logger.info(
            "Redis connection closed",
            extra=extra_(operation="close_redis", status="success"),
        )
    except Exception:
        logger.exception(
            "Failed to close Redis connection",
            extra=extra_(operation="close_redis", status="failure"),
        )
    finally:
        _redis = None
