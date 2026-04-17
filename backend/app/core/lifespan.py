import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter

from app.clients import get_redis, init_postgres, init_redis
from app.kafka import kafka_producer
from app.utils import current_operation
from .logging import (
    AppLoggerAdapter, LogCategory, LogEvent, LogLayer, LogStatus, extra_,
)
from .scheduler import scheduler

logger = AppLoggerAdapter(
    logging.getLogger(__name__),
    {
        "layer": LogLayer.CORE,
        "category": LogCategory.LIFESPAN,
        "component": __name__,
    },
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    operation = current_operation()

    try:
        
        logger.debug(
            "Initializing PostgreSQL",
            extra=extra_(
                operation=operation, status=LogStatus.START, event=LogEvent.DB_INIT
            ),
        )

        await init_postgres()

        logger.info(
            "PostgreSQL initialized",
            extra=extra_(
                operation=operation, status=LogStatus.SUCCESS, event=LogEvent.DB_INIT
            ),
        )

        logger.debug(
            "Initializing Redis",
            extra=extra_(
                operation=operation, status=LogStatus.START, event=LogEvent.CACHE_INIT
            ),
        )

        await init_redis()

        logger.info(
            "Redis initialized",
            extra=extra_(
                operation=operation, status=LogStatus.SUCCESS, event=LogEvent.CACHE_INIT
            ),
        )

        logger.debug(
            "Initializing FastAPI limiter",
            extra=extra_(
                operation=operation,
                status=LogStatus.START,
                event=LogEvent.RATELIMITER_INIT,
            ),
        )

        redis = get_redis()
        await FastAPILimiter.init(redis)

        logger.info(
            "FastAPI limiter initialized",
            extra=extra_(
                operation=operation,
                status=LogStatus.SUCCESS,
                event=LogEvent.RATELIMITER_INIT,
            ),
        )

        if not scheduler.running:
            logger.debug(
                "Starting scheduler",
                extra=extra_(
                    operation=operation,
                    status=LogStatus.START,
                    event=LogEvent.SCHEDULER_START,
                ),
            )

            scheduler.start()

            logger.info(
                "Scheduler started",
                extra=extra_(
                    operation=operation,
                    status=LogStatus.SUCCESS,
                    event=LogEvent.SCHEDULER_START,
                ),
            )

        else:
            logger.warning(
                "Scheduler already running",
                extra=extra_(
                    operation=operation,
                    status=LogStatus.SKIPPED,
                    event=LogEvent.SCHEDULER_START,
                ),
            )
            
        logger.debug(
            "Starting kafka producer",
            extra=extra_(
                operation=operation, 
                status=LogStatus.START, 
                event=LogEvent.KAFKA_PRODUCER_START
            ),
        )
        
        await kafka_producer.start()
        
        logger.info(
            "Kafka producer started",
            extra=extra_(
                operation=operation, 
                status=LogStatus.SUCCESS, 
                event=LogEvent.KAFKA_PRODUCER_START
            ),
        )
    
    except Exception as exc:
        logger.exception(
            "Application startup failed",
            extra=extra_(
                operation=operation,
                status=LogStatus.FAILURE,
                event=LogEvent.LIFESPAN_STARTUP,
                error_type=exc.__class__.__name__,
            ),
        )
        raise

    yield
    
    await kafka_producer.stop()
