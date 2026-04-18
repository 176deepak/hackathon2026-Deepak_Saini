import gdown
import hashlib
import hmac
import time
import jwt
from passlib.context import CryptContext
import logging

from app.core.config import envs
from app.core.logging import AppLoggerAdapter, LogCategory, LogLayer, extra_

JWT_SECRET = envs.APP_JWT_SECRET_KEY
JWT_ALGORITHM = envs.APP_JWT_ALGORITHM

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

logger = AppLoggerAdapter(
    logging.getLogger(__name__),
    {
        "layer": LogLayer.SERVICE,
        "category": LogCategory.SECURITY if hasattr(LogCategory, "SECURITY") else LogCategory.API,
        "component": __name__,
    },
)


def hash_token(value: str) -> str:
    """Hash verification tokens / OTPs using HMAC-SHA256."""
    
    return hmac.new(
        key=envs.APP_SECRET_KEY.encode(),
        msg=value.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()


def hash_password(password: str) -> str:
    """Hash password/secret keys etc."""
    
    sha256_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return pwd_context.hash(sha256_hash)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify the password/secret keys against the pre hashed password or keys etc."""
    
    sha256_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return pwd_context.verify(sha256_hash, hashed_password)


def sign_jwt(user_id: str, **kwargs) -> dict[str, str]:
    """Sign Bearer token for user"""

    now = int(time.time())

    payload = {
        "iss": envs.APP_NAME,
        "sub": user_id,
        "iat": now,
        "exp": now + envs.APP_JWT_EXP_TIME,
        **kwargs
    }

    try:
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        logger.debug(
            "JWT signed",
            extra=extra_(
                operation="sign_jwt",
                status="success",
                sub=user_id,
                exp=payload.get("exp"),
            ),
        )
        return {"access_token": token}
    except Exception as e:
        logger.exception(
            "JWT signing failed",
            extra=extra_(
                operation="sign_jwt",
                status="failure",
                sub=user_id,
                error_type=type(e).__name__,
            ),
        )
        raise


def decode_jwt(token: str) -> dict:
    """Decode tge hashed token"""
    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if decoded_token.get("exp", 0) < time.time():
            logger.warning(
                "JWT expired",
                extra=extra_(operation="decode_jwt", status="failure", reason="expired"),
            )
            return None
        return decoded_token
    except jwt.ExpiredSignatureError:
        logger.warning(
            "JWT expired (signature)",
            extra=extra_(
                operation="decode_jwt", status="failure", reason="expired_signature"
            ),
        )
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(
            "JWT invalid",
            extra=extra_(
                operation="decode_jwt",
                status="failure",
                reason="invalid_token",
                error_type=type(e).__name__,
            ),
        )
        return None
    except Exception as e:
        logger.exception(
            "JWT decode failed",
            extra=extra_(
                operation="decode_jwt",
                status="failure",
                error_type=type(e).__name__,
            ),
        )
        return None


def download_file_from_gdrive(fileid:str, filepath) -> str:
    logger.info((
        f"Downloading file from Google Drive - file_id:"
        f" {fileid}, destination: {filepath}"
    ))
    try:
        url = f"https://drive.google.com/file/d/{fileid}/view?usp=sharing"
        logger.debug(f"Google Drive URL: {url}")
        gdown.download(url, filepath, quiet=False)
        logger.info(f"File downloaded successfully from Google Drive to {filepath}")
        return filepath
    except Exception as e:
        logger.exception(
            f"Error downloading file from Google Drive (file_id: {fileid}): {e}", 
            exc_info=True
        )
        raise