import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.clients import init_postgres, init_redis
from app.core.config import envs
from .logging import AppLoggerAdapter, LogCategory, LogLayer
from .scheduler import scheduler

logger = AppLoggerAdapter(
    logging.getLogger(__name__),
    {
        "layer": LogLayer.LIFESPAN,
        "category": LogCategory.LIFESPAN,
        "component": __name__,
    },
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        
        logger.debug("Initializing PostgreSQL")

        await init_postgres()

        logger.info("PostgreSQL initialized")
        
        logger.debug("Initializing Redis")

        await init_redis()

        logger.info("Redis initialized")

        if not scheduler.running:
            logger.debug("Starting scheduler")

            scheduler.start()

            logger.info("Scheduler started")

        if envs.AGENT_AUTORUN:
            from app.services.agent import AgentRunner

            runner = AgentRunner()

            scheduler.add_job(
                runner.run_tick,
                "interval",
                seconds=envs.AGENT_POLL_SECONDS,
                id="agent_poll",
                replace_existing=True,
                max_instances=1,
                coalesce=True,
            )
            logger.info("Agent autorun scheduled", extra={
                "seconds": envs.AGENT_POLL_SECONDS
            })

        else:
            logger.warning("Scheduler already running")
            
    except Exception:
        logger.exception("Application startup failed")
        raise

    yield
