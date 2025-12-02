"""
Gestión de sesiones basadas en cookies para autenticación
Almacena sesiones en DB para persistencia y auditoría
"""
import secrets
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session as DBSession
from .models import User, Session as SessionModel
from .logging_config import log_session_create, log_session_validate
from .config import get_settings


def generate_session_token() -> str:
    """Genera un token seguro para la sesión"""
    return secrets.token_urlsafe(32)


def create_session(
    db: DBSession,
    user_id: int,
    ip_address: str | None = None,
    user_agent: str | None = None,
    hours: int = 24
) -> str:
    """
    Crea una nueva sesión de usuario

    Args:
        db: Database session
        user_id: ID del usuario
        ip_address: Dirección IP del cliente (para auditoría)
        user_agent: User-Agent del cliente
        hours: Duración de la sesión en horas (default: 24)

    Returns:
        Token de sesión (para guardar en cookie)
    """
    token = generate_session_token()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=hours)

    session = SessionModel(
        user_id=user_id,
        token=token,
        ip_address=ip_address,
        user_agent=user_agent,
        created_at=now,
        expires_at=expires_at,
        last_used_at=now,
        is_active=True
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    # Log
    user = db.query(User).filter(User.id == user_id).first()  # type: ignore[attr-defined]
    if user:
        log_session_create(user_id, user.email, ip_address)  # type: ignore[attr-defined]

    return token


def validate_session(
    db: DBSession,
    token: str,
    ip_address: str | None = None,
    update_last_used: bool = True
) -> User | None:
    """
    Valida un token de sesión y retorna el usuario si es válido

    Args:
        db: Database session
        token: Token de sesión a validar
        ip_address: Dirección IP para auditoría
        update_last_used: Si actualizar el campo last_used_at

    Returns:
        User si la sesión es válida, None si no es válida/expirada
    """
    now = datetime.now(timezone.utc)

    session = (
        db.query(SessionModel)  # type: ignore[attr-defined]
        .filter(
            SessionModel.token == token,  # type: ignore[attr-defined]
            SessionModel.is_active == True,  # type: ignore[attr-defined]
            SessionModel.expires_at > now  # type: ignore[attr-defined]
        )
        .first()
    )

    if not session:
        log_session_validate(user_id=-1, ip_address=ip_address, success=False)
        return None

    # Obtener el usuario
    user = db.query(User).filter(User.id == session.user_id).first()  # type: ignore[attr-defined]
    if not user or not user.active:  # type: ignore[attr-defined]
        log_session_validate(user_id=session.user_id, ip_address=ip_address, success=False)
        return None

    # Actualizar last_used_at
    if update_last_used:
        session.last_used_at = now  # type: ignore[attr-defined]
        db.commit()

    log_session_validate(user_id=user.id, ip_address=ip_address, success=True)
    return user


def revoke_session(db: DBSession, token: str) -> bool:
    """
    Revoca una sesión (logout)

    Args:
        db: Database session
        token: Token de sesión a revocar

    Returns:
        True si se revocó exitosamente, False si no encontró la sesión
    """
    session = (
        db.query(SessionModel)  # type: ignore[attr-defined]
        .filter(SessionModel.token == token)  # type: ignore[attr-defined]
        .first()
    )

    if not session:
        return False

    session.is_active = False  # type: ignore[attr-defined]
    db.commit()
    return True


def revoke_all_user_sessions(db: DBSession, user_id: int) -> int:
    """
    Revoca todas las sesiones de un usuario (logout everywhere)

    Args:
        db: Database session
        user_id: ID del usuario

    Returns:
        Número de sesiones revocadas
    """
    result = (
        db.query(SessionModel)  # type: ignore[attr-defined]
        .filter(
            SessionModel.user_id == user_id,  # type: ignore[attr-defined]
            SessionModel.is_active == True  # type: ignore[attr-defined]
        )
        .update({"is_active": False})  # type: ignore[attr-defined]
    )
    db.commit()
    return result


def cleanup_expired_sessions(db: DBSession) -> int:
    """
    Limpia sesiones expiradas de la base de datos
    Útil ejecutar periódicamente (cronjob)

    Args:
        db: Database session

    Returns:
        Número de sesiones eliminadas
    """
    now = datetime.now(timezone.utc)
    result = (
        db.query(SessionModel)  # type: ignore[attr-defined]
        .filter(SessionModel.expires_at < now)  # type: ignore[attr-defined]
        .delete()
    )
    db.commit()
    return result


def get_active_sessions_count(db: DBSession, user_id: int) -> int:
    """
    Obtiene el número de sesiones activas de un usuario

    Args:
        db: Database session
        user_id: ID del usuario

    Returns:
        Número de sesiones activas
    """
    now = datetime.now(timezone.utc)
    count = (
        db.query(SessionModel)  # type: ignore[attr-defined]
        .filter(
            SessionModel.user_id == user_id,  # type: ignore[attr-defined]
            SessionModel.is_active == True,  # type: ignore[attr-defined]
            SessionModel.expires_at > now  # type: ignore[attr-defined]
        )
        .count()
    )
    return count
