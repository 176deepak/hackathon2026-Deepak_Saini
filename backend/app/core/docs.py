import logging
from fastapi import Depends, FastAPI, Request
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html

from .logging import LogCategory, LogLayer, AppLoggerAdapter, extra_
from .security import docs_basic_auth

logger = AppLoggerAdapter(
    logging.getLogger(__name__),
    {
        "layer": LogLayer.API,
        "category": LogCategory.API,
        "component": __name__,
    },
)


def setup_protected_docs(app: FastAPI) -> None:
    logger.debug("Registering protected documentation routes")

    @app.get("/docs", include_in_schema=False)
    async def swagger_docs(
        request: Request,
        _=Depends(docs_basic_auth),
    ):
        client_ip = request.client.host if request.client else "unknown"
        request_id = getattr(request.state, "request_id", None)

        logger.info(
            "Serving Swagger UI",
            extra=extra_(
                method=request.method,
                path=request.url.path,
                client_ip=client_ip,
                request_id=request_id,
            ),
        )

        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title=f"{app.title} - Docs"
        )

    @app.get("/redoc", include_in_schema=False)
    async def redoc_docs(
        request: Request,
        _=Depends(docs_basic_auth),
    ):
        client_ip = request.client.host if request.client else "unknown"
        request_id = getattr(request.state, "request_id", None)

        logger.info(
            "Serving ReDoc UI",
            extra=extra_(
                method=request.method,
                path=request.url.path,
                client_ip=client_ip,
                request_id=request_id,
            ),
        )

        return get_redoc_html(
            openapi_url="/openapi.json",
            title=f"{app.title} - ReDoc"
        )

    @app.get("/openapi.json", include_in_schema=False)
    async def openapi(
        request: Request,
        _=Depends(docs_basic_auth),
    ):
        client_ip = request.client.host if request.client else "unknown"
        request_id = getattr(request.state, "request_id", None)

        logger.info(
            "Serving OpenAPI schema",
            extra=extra_(
                method=request.method,
                path=request.url.path,
                client_ip=client_ip,
                request_id=request_id,
            ),
        )

        return app.openapi()

    logger.info("Protected documentation routes registered")
