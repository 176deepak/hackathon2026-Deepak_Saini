import logging
from redis.asyncio import Redis

from app.core.config import envs
from app.core.logging import LogCategory, LogLayer, AppLoggerAdapter

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
    _redis = Redis.from_url(envs.redis_uri, decode_responses=False)


def get_redis() -> Redis:
    
    if _redis is None:
        logger.exception("Redis client not initialized")
        raise RuntimeError("Redis client not initialized")

    logger.info("Redis client returned")
    return _redis


async def close_redis():
    if _redis:
        await _redis.close()
