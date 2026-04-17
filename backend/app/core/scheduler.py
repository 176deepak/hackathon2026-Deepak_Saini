from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import envs

DATABASE_URL = (
    f"postgresql+psycopg2://{envs.PG_DB_USER}:"
    f"{envs.PG_DB_PASSWORD}@"
    f"{envs.PG_DB_HOST}:"
    f"{envs.PG_DB_PORT}/"
    f"{envs.PG_DB_NAME}"
)

jobstores = {"default": SQLAlchemyJobStore(url=DATABASE_URL)}
executors = {"default": AsyncIOExecutor()}

job_defaults = {
    "coalesce": False,
    "max_instances": envs.APP_SCHEDULER_MAX_INSTANCE,
}

scheduler = AsyncIOScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone="UTC",
)
