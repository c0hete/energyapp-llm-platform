from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
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
