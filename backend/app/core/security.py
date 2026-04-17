import secrets

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import (
    HTTPAuthorizationCredentials, HTTPBasic, HTTPBasicCredentials, HTTPBearer
)

from .utils import decode_jwt
from .config import envs


security = HTTPBasic(auto_error=True)


def docs_basic_auth(
    credentials: HTTPBasicCredentials = Depends(security),
):
    correct_username = secrets.compare_digest(
        credentials.username,
        envs.APP_DOCS_USERNAME,
    )
    correct_password = secrets.compare_digest(
        credentials.password,
        envs.APP_DOCS_PASSWORD,
    )

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": 'Basic realm="API Documentation"'},
        )


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)

        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization required to access this resource.",
            )

        if credentials.scheme != "Bearer":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Authentication scheme must be 'Bearer'.",
            )

        payload = self.verify_and_decode_jwt(credentials.credentials)
        request.state.jwt_payload = payload
        return credentials.credentials

    def verify_and_decode_jwt(self, jwtoken: str) -> dict:
        try:
            payload = decode_jwt(jwtoken)
            return payload
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or expired access token.",
            )