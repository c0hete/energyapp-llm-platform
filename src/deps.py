from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional

from .db import SessionLocal
from .models import User
from .auth import decode_token
from . import sessions as session_mgmt
from .logging_config import log_error


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _get_token_from_header(request: Request) -> Optional[str]:
    auth = request.headers.get("Authorization")
    if not auth:
        return None
    parts = auth.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


def _get_session_token_from_cookie(request: Request) -> Optional[str]:
    """Extrae el token de sesión de la cookie"""
    return request.cookies.get("session_token")


def get_client_ip(request: Request) -> Optional[str]:
    """Obtiene la dirección IP del cliente"""
    if x_forwarded_for := request.headers.get("X-Forwarded-For"):
        return x_forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else None


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """
    Obtiene el usuario actual usando JWT (método antiguo).
    Se mantiene para transición gradual.
    """
    token = _get_token_from_header(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Auth required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(token, expected_type="access")
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.id == int(user_id)).first()  # type: ignore[attr-defined]
    if not user or not user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_user_from_session(request: Request, db: Session = Depends(get_db)) -> User:
    """
    Obtiene el usuario actual usando sesión basada en cookies (método nuevo).
    Valida el token de sesión y retorna el usuario.
    """
    import logging
    logger = logging.getLogger("energyapp.auth")

    session_token = _get_session_token_from_cookie(request)
    logger.info(f"SESSION_VALIDATE_ATTEMPT | token_present={session_token is not None} | cookies={list(request.cookies.keys())}")

    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session required",
        )

    ip_address = get_client_ip(request)
    logger.info(f"SESSION_VALIDATE_TRY | token={session_token[:20]}... | ip={ip_address}")
    user = session_mgmt.validate_session(db, session_token, ip_address=ip_address)

    if not user:
        logger.info(f"SESSION_VALIDATE_FAILED | token={session_token[:20]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    logger.info(f"SESSION_VALIDATE_SUCCESS | user_id={user.id} | email={user.email}")
    return user


def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """
    Intenta obtener el usuario usando sesión o JWT.
    Retorna None si no está autenticado (opcional).
    """
    # Intentar con sesión primero
    session_token = _get_session_token_from_cookie(request)
    if session_token:
        ip_address = get_client_ip(request)
        user = session_mgmt.validate_session(db, session_token, ip_address=ip_address)
        if user:
            return user

    # Si no hay sesión, intentar con JWT
    token = _get_token_from_header(request)
    if token:
        try:
            payload = decode_token(token, expected_type="access")
            user_id = payload.get("sub")
            if user_id:
                user = db.query(User).filter(User.id == int(user_id)).first()  # type: ignore[attr-defined]
                if user and user.active:  # type: ignore[attr-defined]
                    return user
        except HTTPException:
            pass

    return None


def require_admin(user: User = Depends(get_current_user)) -> User:
    if getattr(user, "role", "") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin only",
        )
    return user


def require_admin_or_supervisor(user: User = Depends(get_current_user)) -> User:
    role = getattr(user, "role", "")
    if role not in ("admin", "supervisor"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or supervisor only",
        )
    return user


def require_admin_session(user: User = Depends(get_current_user_from_session)) -> User:
    """Requiere admin, usando sesión"""
    if getattr(user, "role", "") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin only",
        )
    return user


def require_admin_or_supervisor_session(user: User = Depends(get_current_user_from_session)) -> User:
    """Requiere admin o supervisor, usando sesión"""
    role = getattr(user, "role", "")
    if role not in ("admin", "supervisor"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or supervisor only",
        )
    return user


def get_current_user_hybrid(request: Request, db: Session = Depends(get_db)) -> User:
    """
    Obtiene el usuario actual usando sesión o JWT (híbrido).
    Intenta sesión primero, luego JWT. Levanta excepción si ninguno funciona.
    """
    # Intentar con sesión primero
    session_token = _get_session_token_from_cookie(request)
    if session_token:
        ip_address = get_client_ip(request)
        user = session_mgmt.validate_session(db, session_token, ip_address=ip_address)
        if user and user.active:  # type: ignore[attr-defined]
            return user

    # Si no hay sesión, intentar con JWT
    token = _get_token_from_header(request)
    if token:
        try:
            payload = decode_token(token, expected_type="access")
            user_id = payload.get("sub")
            if user_id:
                user = db.query(User).filter(User.id == int(user_id)).first()  # type: ignore[attr-defined]
                if user and user.active:  # type: ignore[attr-defined]
                    return user
        except Exception:
            pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Auth required",
    )


def require_admin_or_supervisor_hybrid(user: User = Depends(get_current_user_hybrid)) -> User:
    """Requiere admin o supervisor, usando sesión o JWT"""
    role = getattr(user, "role", "")
    if role not in ("admin", "supervisor"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or supervisor only",
        )
    return user
