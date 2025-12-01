from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserBase(BaseModel):
    id: int
    email: EmailStr
    role: str
    active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ConversationBase(BaseModel):
    id: int
    title: str
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MessageBase(BaseModel):
    id: int
    role: str
    content: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CreateConversation(BaseModel):
    title: Optional[str] = Field(default="Nueva conversacion", max_length=255)


class UpdateConversation(BaseModel):
    title: Optional[str] = Field(default=None, max_length=255)
    status: Optional[str] = Field(default=None, pattern="^(open|closed)$")


class ChatRequest(BaseModel):
    prompt: str
    system: Optional[str] = None
    conversation_id: Optional[int] = None


class ChatResponseChunk(BaseModel):
    content: str
