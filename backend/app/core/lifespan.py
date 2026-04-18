import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.clients import init_postgres, init_redis
from app.core.config import envs
from app.core.utils import download_file_from_gdrive
from app.services import KnowledgeBaseService
from .logging import AppLoggerAdapter, LogCategory, LogLayer, extra_
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
            
        if envs.ENVIRONMENT != "local":
            logger.info((
                f"Non-local environment detected ({envs.ENVIRONMENT}),"
                " setting up knowledge base"
            ))
            
            os.makedirs(envs.KNOWLEDGE_BASE_UPLOAD_DIR, exist_ok=True)
            logger.debug(
                f"Upload directory created/verified: {envs.KNOWLEDGE_BASE_UPLOAD_DIR}"
            )
            kb_path = f"{envs.KNOWLEDGE_BASE_UPLOAD_DIR}/knowledge_base.md"
            download_file_from_gdrive(
                fileid=envs.KNOWLEDGE_BASE_GDRIVE_FILE_ID,
                filepath=kb_path
            )
            logger.info("Knowledge base fetched from GDrive!")
            logger.debug(
                f"Initializing KnowledgeBaseService with {envs.WHICH_KNOWLEDGE_BASE}"
            )
            kb_service = KnowledgeBaseService(which=envs.WHICH_KNOWLEDGE_BASE)
            await kb_service.create_and_upload_chunks(
                filepath=kb_path,
                chunk_size=envs.CHUNK_SIZE,
                overlapping=envs.CHUNK_OVERLAP
            )
            await kb_service.close()
            logger.info("Knowledge base setup completed")
        else:
            logger.info("Local environment detected, skipping knowledge base setup")

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
                coalesce=True
            )
            logger.info("Agent autorun scheduled", extra=extra_(
                seconds=envs.AGENT_POLL_SECONDS
            ))

        else:
            logger.warning("Scheduler already running")
            
    except Exception:
        logger.exception("Application startup failed")
        raise

    yield
