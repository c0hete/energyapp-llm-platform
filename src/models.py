from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship, Mapped
from .db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    email: Mapped[str] = Column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = Column(String(255), nullable=False)
    role: Mapped[str] = Column(String(50), default="user")  # admin | user
    active: Mapped[bool] = Column(Boolean, default=True)
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
