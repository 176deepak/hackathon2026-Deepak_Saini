from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import envs
from app.services.base import BaseService


class SystemService(BaseService):
    def check_health(self, db: Session) -> dict:
        db.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "database": "up",
            "version": envs.APP_VERSION,
            "timestamp": datetime.now(timezone.utc),
        }

    def ping(self) -> dict:
        return {"message": "pong"}
