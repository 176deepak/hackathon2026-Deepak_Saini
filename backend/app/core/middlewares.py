import logging
import time
import uuid
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_maintenance import MaintenanceModeMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.schemas.api import RESTResponse
from .config import envs
from .logging import LogCategory, LogLayer, AppLoggerAdapter, extra_
from .request_context import reset_request_id, set_request_id

logger = AppLoggerAdapter(
    logging.getLogger(__name__),
    {
        "layer": LogLayer.MIDDLEWARE,
        "category": LogCategory.MIDDLEWARE,
        "component": __name__,
    },
)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        request_id_token = set_request_id(request_id)

        start_time = time.perf_counter()
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        logger.info(
            "Incoming request",
            extra=extra_(
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                client_ip=client_ip,
                user_agent=user_agent,
            ),
        )

        try:
            response: Response = await call_next(request)
            latency_ms = round((time.perf_counter() - start_time) * 1000)
            logger.info(
                "Request completed",
                extra=extra_(
                    request_id=request_id,
                    method=request.method,
                    path=request.url.path,
                    client_ip=client_ip,
                    user_agent=user_agent,
                    status_code=response.status_code,
                    latency_ms=latency_ms,
                ),
            )
            return response
        except Exception as exc:
            latency_ms = round((time.perf_counter() - start_time) * 1000)
            logger.exception(
                "Request failed",
                extra=extra_(
                    request_id=request_id,
                    method=request.method,
                    path=request.url.path,
                    client_ip=client_ip,
                    user_agent=user_agent,
                    latency_ms=latency_ms,
                    error_type=exc.__class__.__name__,
                ),
                exc_info=False,
            )
            raise
        finally:
            reset_request_id(request_id_token)


async def custom_maintenance_response(request: Request) -> JSONResponse:
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    request_id = getattr(request.state, "request_id", None) or str(uuid.uuid4())

    logger.warning(
        "Request blocked due to maintenance mode",
        extra=extra_(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=client_ip,
            user_agent=user_agent,
            http_status=status.HTTP_503_SERVICE_UNAVAILABLE,
        ),
    )

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=RESTResponse(
            code=status.HTTP_503_SERVICE_UNAVAILABLE,
            success=False,
            data={},
            msg="Service under maintenance! Please check back later.",
        ).model_dump(),
    )


def setup_middleware(app: FastAPI) -> None:
    app.add_middleware(RequestLoggingMiddleware)

    logger.info("RequestLoggingMiddleware registered")

    app.add_middleware(
        MaintenanceModeMiddleware,
        response_handler=custom_maintenance_response,
    )

    logger.info("MaintenanceModeMiddleware registered")

    allowed_origins = envs.cors_allowed_origins

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[allowed_origins]
        if isinstance(allowed_origins, str)
        else allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    logger.info("CORSMiddleware registered")
