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
                redis_db=envs.REDIS_DB,
                redis_host=envs.REDIS_HOST,
                redis_port=envs.REDIS_PORT,
            ),
        )
    except Exception:
        logger.exception(
            "Redis initialization failed",
            extra=extra_(
                redis_db=envs.REDIS_DB,
                redis_host=envs.REDIS_HOST,
                redis_port=envs.REDIS_PORT,
            ),
        )
        raise


def get_redis() -> Redis:
    
    if _redis is None:
        logger.error("Redis client not initialized")
        raise RuntimeError("Redis client not initialized")

    logger.debug("Redis client returned")
    return _redis


async def close_redis():
    global _redis
    if not _redis:
        return

    try:
        await _redis.close()
        logger.info("Redis connection closed")
    except Exception:
        logger.exception("Failed to close Redis connection")
    finally:
        _redis = None
