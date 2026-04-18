import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

from app.core.logging import LogCategory, LogLayer, AppLoggerAdapter, extra_
from app.schemas.api import RESTResponse

logger = AppLoggerAdapter(
    logging.getLogger(__name__),
    {
        "layer": LogLayer.HANDLER,
        "category": LogCategory.EXCEPTION,
        "component": __name__,
    },
)


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> Response:
    client_ip = request.client.host if request.client else "unknown"
    request_id = getattr(request.state, "request_id", None)
    is_docs_endpoint = request.url.path in ["/docs", "/redoc", "/openapi.json"]

    if exc.status_code == status.HTTP_401_UNAUTHORIZED and is_docs_endpoint:
        logger.warning(
            "Unauthorized documentation access",
            extra=extra_(
                http_status=exc.status_code,
                method=request.method,
                path=request.url.path,
                client_ip=client_ip,
                request_id=request_id,
                reason="Docs Auth Required",
            )
        )

        headers = {}
        try:
            if exc.headers:
                headers = dict(exc.headers)
        except Exception:
            logger.warning(
                "Failed to normalize exception headers",
                extra=extra_(
                    http_status=exc.status_code,
                    method=request.method,
                    path=request.url.path,
                    client_ip=client_ip,
                    request_id=request_id,
                )
            )

        if "WWW-Authenticate" not in headers and "www-authenticate" not in headers:
            headers["WWW-Authenticate"] = 'Basic realm="API Documentation"'
        elif "www-authenticate" in headers and "WWW-Authenticate" not in headers:
            headers["WWW-Authenticate"] = headers.pop("www-authenticate")

        # Return PlainTextResponse with proper headers 
        # to trigger browser Basic Auth popup
        return PlainTextResponse(
            content=exc.detail or "Unauthorized",
            status_code=exc.status_code,
            headers=headers,
        )

    log_level = logging.ERROR if exc.status_code >= 500 else logging.WARNING
    logger.log(
        log_level,
        "HTTP exception handled",
        extra=extra_(
            http_status=exc.status_code,
            method=request.method,
            path=request.url.path,
            client_ip=client_ip,
            request_id=request_id,
        )
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=RESTResponse(
            code=exc.status_code,
            success=False,
            data={},
            msg=str(exc.detail),
        ).model_dump()
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    client_ip = request.client.host if request.client else "unknown"

    logger.exception(
        "Unhandled exception during request processing",
        extra=extra_(
            method=request.method,
            path=request.url.path,
            client_ip=client_ip,
            request_id=request_id,
            error_type=exc.__class__.__name__,
        )
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=RESTResponse(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            data={},
            msg="Internal Server Error",
        ).model_dump()
    )
