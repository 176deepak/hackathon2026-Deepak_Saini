from fastapi import FastAPI

from app.core.logging import setup_logging
setup_logging()

from app.core.metadata import (
    APP_TITLE, APP_VERSION, APP_SUMMARY, APP_DESCRIPTION, APP_CONTACT, APP_LICENSE_INFO, 
    OPENAPI_SERVERS, OPENAPI_TAGS
)
from app.core.lifespan import lifespan
from app.core.middlewares import setup_middleware
from app.core.exception import setup_exception_handlers
from app.core.docs import setup_protected_docs
from app.core.routes import setup_routes

app = FastAPI(
    title=APP_TITLE,
    summary=APP_SUMMARY,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    contact=APP_CONTACT,
    license_info=APP_LICENSE_INFO,
    openapi_tags=OPENAPI_TAGS,
    servers=OPENAPI_SERVERS,
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

setup_middleware(app)
setup_exception_handlers(app)
setup_protected_docs(app)
setup_routes(app)