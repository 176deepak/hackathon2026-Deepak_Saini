import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.core.config import envs
from app.core.logging import AppLoggerAdapter, LogCategory, LogLayer, extra_
from app.core.utils import sign_jwt
from app.schemas.api import AuthTokenData, RESTResponse
import logging


router = APIRouter(prefix="/auth", tags=["Auth"])
security = HTTPBasic(auto_error=True)

logger = AppLoggerAdapter(
    logging.getLogger(__name__),
    {
        "layer": LogLayer.API,
        "category": LogCategory.API,
        "component": __name__,
    },
)


def _auth_expected() -> tuple[str, str]:
    username = envs.APP_AUTH_USERNAME or envs.APP_DOCS_USERNAME
    password = envs.APP_AUTH_PASSWORD or envs.APP_DOCS_PASSWORD
    return username, password


@router.post(
    "/login",
    response_model=RESTResponse[AuthTokenData],
    summary="Login (Basic Auth) and receive JWT",
)
async def login(credentials: HTTPBasicCredentials = Depends(security)):
    expected_username, expected_password = _auth_expected()

    if not (
        secrets.compare_digest(credentials.username, expected_username)
        and secrets.compare_digest(credentials.password, expected_password)
    ):
        logger.warning(
            "Dashboard login failed",
            extra=extra_(username=credentials.username),
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": 'Basic realm="Dashboard"'},
        )

    try:
        token = sign_jwt(
            user_id=credentials.username,
            role="dashboard",
        )["access_token"]
    except Exception:
        logger.exception(
            "Failed to sign JWT",
            extra=extra_(username=credentials.username),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create token",
        )

    logger.info(
        "Dashboard login successful",
        extra=extra_(
            username=credentials.username,
            expires_in=int(envs.APP_JWT_EXP_TIME),
        ),
    )

    return RESTResponse(
        code=status.HTTP_200_OK,
        success=True,
        data=AuthTokenData(
            access_token=token,
            token_type="bearer",
            expires_in=int(envs.APP_JWT_EXP_TIME),
        ),
        msg="Login successful",
    )
