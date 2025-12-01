from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status

from .config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def _create_token(subject: str, expires_minutes: int, token_type: str) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode: Dict[str, Any] = {"sub": subject, "exp": expire, "type": token_type}
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(subject: str) -> str:
    settings = get_settings()
    return _create_token(subject, settings.access_token_expire_minutes, "access")


def create_refresh_token(subject: str) -> str:
    settings = get_settings()
    return _create_token(subject, settings.refresh_token_expire_minutes, "refresh")


def decode_token(token: str, expected_type: str = "access") -> Dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        if payload.get("type") != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
