from datetime import datetime
from typing import Optional
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


class AdminUser(UserBase):
    last_activity: Optional[datetime] = None


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
    prompt_id: Optional[int] = None


class ChatResponseChunk(BaseModel):
    content: str


class GenerateTitle(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=1000, description="Prompt para generar el titulo")


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class ConfigInfo(BaseModel):
    ollama_host: str
    ollama_model: str
    ollama_temperature: float
    ollama_top_p: float
    ollama_max_tokens: int


class ReassignConversationRequest(BaseModel):
    target_user_id: Optional[int] = None
    target_email: Optional[EmailStr] = None


class LoginResponse(BaseModel):
    """Respuesta de login - puede requerir 2FA"""
    needs_2fa: bool
    session_token: Optional[str] = None  # Token temporal para verificar 2FA
    access_token: Optional[str] = None   # Si no requiere 2FA
    refresh_token: Optional[str] = None


class Verify2FARequest(BaseModel):
    """Verificación de código TOTP"""
    session_token: str
    totp_code: str = Field(..., min_length=6, max_length=6, pattern="^[0-9]{6}$")


class Setup2FARequest(BaseModel):
    """Setup inicial de 2FA (admin)"""
    user_email: EmailStr


class Setup2FAResponse(BaseModel):
    """Respuesta con QR para configurar 2FA"""
    secret: str
    qr_code: str  # URL de imagen QR en data:image/png;base64


class DemoQRCode(BaseModel):
    """QR code para un usuario demo"""
    email: str
    role: str
    qr_code: str
    secret: str


class DemoQRCodesResponse(BaseModel):
    """Respuesta con QR codes de usuarios demo"""
    demo_qrs: list[DemoQRCode]


class RegisterRequest(BaseModel):
    """Solicitud de registro de nuevo usuario"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class SystemPromptCreate(BaseModel):
    """Crear un nuevo system prompt"""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    content: str = Field(..., min_length=10)
    is_default: bool = False


class SystemPromptUpdate(BaseModel):
    """Actualizar un system prompt"""
    name: str | None = None
    description: str | None = None
    content: str | None = None
    is_default: bool | None = None
    is_active: bool | None = None


class SystemPromptResponse(BaseModel):
    """Respuesta con datos de system prompt"""
    id: int
    name: str
    description: str | None
    content: str
    is_default: bool
    is_active: bool
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
