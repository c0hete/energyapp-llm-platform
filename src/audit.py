"""Sistema de auditoría centralizado para EnergyApp"""

import json
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from .models import User, AuditLog


class AuditLogger:
    """Logger centralizado para eventos de auditoría"""

    @staticmethod
    def log(
        db: Session,
        action: str,
        user: Optional[User] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """
        Guardar log de auditoría en la base de datos

        Args:
            db: Sesión de base de datos
            action: Acción realizada (ej: "login_success", "create_user")
            user: Usuario que realizó la acción (opcional)
            resource_type: Tipo de recurso afectado (ej: "user", "conversation")
            resource_id: ID del recurso afectado
            status: Estado del resultado ("success", "failed", "blocked")
            error_message: Mensaje de error si falló
            metadata: Datos adicionales en formato dict
            ip_address: IP desde donde se realizó la acción

        Returns:
            AuditLog: Registro de auditoría creado
        """
        log_entry = AuditLog(  # type: ignore[call-arg]
            user_id=user.id if user else None,  # type: ignore[attr-defined]
            user_email=user.email if user else None,  # type: ignore[attr-defined]
            user_role=user.role if user else None,  # type: ignore[attr-defined]
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            error_message=error_message,
            metadata=json.dumps(metadata) if metadata else None,
            ip_address=ip_address
        )

        db.add(log_entry)

        # Commit inmediato para asegurar persistencia
        try:
            db.commit()
            db.refresh(log_entry)
        except Exception as e:
            db.rollback()
            # Si falla el log, no queremos romper la operación principal
            print(f"[AUDIT ERROR] Failed to save audit log: {e}")

        return log_entry

    @staticmethod
    def log_auth(
        db: Session,
        action: str,
        email: str,
        success: bool,
        ip_address: Optional[str] = None,
        error_message: Optional[str] = None,
        user: Optional[User] = None
    ):
        """Helper para logs de autenticación"""
        return AuditLogger.log(
            db=db,
            action=action,
            user=user,
            status="success" if success else "failed",
            error_message=error_message,
            metadata={"email": email},
            ip_address=ip_address
        )

    @staticmethod
    def log_user_action(
        db: Session,
        action: str,
        admin: User,
        target_user_id: int,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Helper para logs de gestión de usuarios"""
        return AuditLogger.log(
            db=db,
            action=action,
            user=admin,
            resource_type="user",
            resource_id=target_user_id,
            metadata=metadata,
            ip_address=ip_address
        )

    @staticmethod
    def log_conversation_action(
        db: Session,
        action: str,
        user: User,
        conversation_id: int,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Helper para logs de conversaciones"""
        return AuditLogger.log(
            db=db,
            action=action,
            user=user,
            resource_type="conversation",
            resource_id=conversation_id,
            metadata=metadata,
            ip_address=ip_address
        )

    @staticmethod
    def log_prompt_action(
        db: Session,
        action: str,
        admin: User,
        prompt_id: int,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Helper para logs de system prompts"""
        return AuditLogger.log(
            db=db,
            action=action,
            user=admin,
            resource_type="system_prompt",
            resource_id=prompt_id,
            metadata=metadata,
            ip_address=ip_address
        )


# Constantes de acciones para consistencia
class AuditAction:
    """Constantes de acciones de auditoría"""

    # Autenticación
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    SESSION_EXPIRED = "session_expired"
    PASSWORD_CHANGED = "password_changed"

    # Usuarios
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    ROLE_CHANGED = "role_changed"
    USER_ACTIVATED = "user_activated"
    USER_DEACTIVATED = "user_deactivated"

    # Conversaciones
    CONVERSATION_STARTED = "conversation_started"
    CONVERSATION_VIEWED = "conversation_viewed"
    CONVERSATION_DELETED = "conversation_deleted"
    CONVERSATION_REASSIGNED = "conversation_reassigned"
    MESSAGE_SENT = "message_sent"

    # System Prompts
    PROMPT_CREATED = "prompt_created"
    PROMPT_UPDATED = "prompt_updated"
    PROMPT_DELETED = "prompt_deleted"
    PROMPT_ACTIVATED = "prompt_activated"
    PROMPT_DEACTIVATED = "prompt_deactivated"

    # Tool Calling
    TOOL_CALLED = "tool_called"
    TOOL_FAILED = "tool_failed"
