from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

import logging
from app.core.config import envs
from app.core.logging import AppLoggerAdapter, LogCategory, LogLayer, extra_
from app.services.base import BaseService

logger = AppLoggerAdapter(
    logging.getLogger(__name__),
    {
        "layer": LogLayer.SERVICE,
        "category": LogCategory.API,
        "component": __name__,
    },
)


class SystemService(BaseService):
    def check_health(self, db: Session) -> dict:
        try:
            db.execute(text("SELECT 1"))
            payload = {
                "status": "ok",
                "database": "up",
                "version": envs.APP_VERSION,
                "timestamp": datetime.now(timezone.utc),
            }
            logger.debug("Health check succeeded")
            return payload
        except Exception:
            logger.exception("Health check failed")
            return {
                "status": "degraded",
                "database": "down",
                "version": envs.APP_VERSION,
                "timestamp": datetime.now(timezone.utc),
            }

    def ping(self) -> dict:
        logger.debug("Ping")
        return {"message": "pong"}
