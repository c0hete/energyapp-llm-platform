from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import relationship, Mapped
from .db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    email: Mapped[str] = Column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = Column(String(255), nullable=False)
    role: Mapped[str] = Column(String(50), default="user")  # admin | user | trabajador | supervisor
    active: Mapped[bool] = Column(Boolean, default=True)
    totp_secret: Mapped[str | None] = Column(String(32), nullable=True)  # TOTP secret base32
    totp_enabled: Mapped[bool] = Column(Boolean, default=False)  # Si 2FA está activado
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    conversations = relationship("Conversation", back_populates="user")


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = Column(Integer, ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = Column(String(255), default="Nueva conversacion")
    status: Mapped[str] = Column(String(50), default="open")  # open | closed
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    conversation_id: Mapped[int] = Column(
        Integer, ForeignKey("conversations.id"), nullable=False
    )
    role: Mapped[str] = Column(String(50), nullable=False)  # user | assistant
    content: Mapped[str] = Column(Text, nullable=False)
    meta: Mapped[str | None] = Column(Text, nullable=True)  # json serializado
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


class Session(Base):
    """Sesiones de usuario para autenticación basada en cookies"""
    __tablename__ = "sessions"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token: Mapped[str] = Column(String(255), unique=True, index=True, nullable=False)
    ip_address: Mapped[str | None] = Column(String(45), nullable=True)  # IPv4 o IPv6
    user_agent: Mapped[str | None] = Column(String(500), nullable=True)
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at: Mapped[datetime] = Column(DateTime, nullable=False, index=True)
    last_used_at: Mapped[datetime | None] = Column(DateTime, nullable=True)
    is_active: Mapped[bool] = Column(Boolean, default=True, index=True)

    user = relationship("User", backref="sessions")


class SystemPrompt(Base):
    """Prompts del sistema que los admins pueden crear e inyectar en conversaciones"""
    __tablename__ = "system_prompts"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    name: Mapped[str] = Column(String(255), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = Column(Text, nullable=True)
    content: Mapped[str] = Column(Text, nullable=False)  # El prompt real
    is_default: Mapped[bool] = Column(Boolean, default=False, index=True)
    is_active: Mapped[bool] = Column(Boolean, default=True, index=True)
    created_by: Mapped[int] = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    creator = relationship("User", backref="system_prompts")


class UserCreationLog(Base):
    """Registro de creación de usuarios (para auditoría)"""
    __tablename__ = "user_creation_logs"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_by_admin_id: Mapped[int | None] = Column(Integer, ForeignKey("users.id"), nullable=True)  # None si fue auto-registro
    reason: Mapped[str | None] = Column(Text, nullable=True)  # Motivo de la solicitud/creación
    ip_address: Mapped[str | None] = Column(String(45), nullable=True)
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", foreign_keys=[user_id], backref="creation_logs")
    created_by = relationship("User", foreign_keys=[created_by_admin_id])


class AuditLog(Base):
    """Sistema de auditoría centralizado para tracking de actividad"""
    __tablename__ = "audit_logs"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)

    # Quién
    user_id: Mapped[int | None] = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    user_email: Mapped[str | None] = Column(String(255), nullable=True)  # Denormalizado para queries rápidas
    user_role: Mapped[str | None] = Column(String(50), nullable=True)

    # Qué
    action: Mapped[str] = Column(String(100), nullable=False, index=True)  # login_success, create_user, etc.
    resource_type: Mapped[str | None] = Column(String(50), nullable=True, index=True)  # user, conversation, prompt, message
    resource_id: Mapped[int | None] = Column(Integer, nullable=True)

    # Contexto (JSONB para flexibilidad)
    meta_data: Mapped[str | None] = Column(Text, nullable=True)  # JSON string

    # Resultado
    status: Mapped[str] = Column(String(20), nullable=False, default="success", index=True)  # success, failed, blocked
    error_message: Mapped[str | None] = Column(Text, nullable=True)

    # Cuándo y dónde
    ip_address: Mapped[str | None] = Column(String(45), nullable=True)
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow, index=True)

    # Relación opcional con usuario
    user = relationship("User", foreign_keys=[user_id], backref="audit_logs")

    __table_args__ = (
        Index('idx_audit_user_time', 'user_id', 'created_at'),
        Index('idx_audit_action_time', 'action', 'created_at'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_status_time', 'status', 'created_at'),
    )


class CIE10Code(Base):
    """Códigos CIE-10 (Clasificación Internacional de Enfermedades)"""
    __tablename__ = "cie10_codes"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    code: Mapped[str] = Column(String(10), unique=True, index=True, nullable=False)
    description: Mapped[str] = Column(Text, nullable=False)
    level: Mapped[int] = Column(Integer, nullable=False, index=True)  # 0=capítulo, 1=categoría, 2=subcategoría
    parent_code: Mapped[str | None] = Column(String(10), nullable=True, index=True)
    is_range: Mapped[bool] = Column(Boolean, default=False, index=True)  # True si es rango (ej: A00-B99)
    search_vector: Mapped[str | None] = Column(TSVECTOR, nullable=True)  # Full-text search en español
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_cie10_search', 'search_vector', postgresql_using='gin'),
    )
