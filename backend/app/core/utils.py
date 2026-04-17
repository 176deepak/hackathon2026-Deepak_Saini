import hashlib
import hmac
import time
import jwt
from passlib.context import CryptContext

from app.core.config import envs

JWT_SECRET = envs.APP_JWT_SECRET_KEY
JWT_ALGORITHM = envs.APP_JWT_ALGORITHM

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return {"access_token": token}


def decode_jwt(token: str) -> dict:
    """Decode tge hashed token"""
    
    decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    return decoded_token if decoded_token["exp"] >= time.time() else None
