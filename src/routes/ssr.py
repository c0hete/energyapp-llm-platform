"""
Rutas de Server-Side Rendering (SSR) usando Jinja2 templates
Complementan las rutas API existentes con HTML renderizado del lado del servidor
"""

from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..deps import get_db, get_current_user_from_session, get_current_user_optional
from ..models import User, Conversation, Message
from ..config import get_settings

# Configurar templates directory
TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(tags=["ssr"])


def is_authenticated(request: Request, db: Session) -> bool:
    """Verifica si el usuario tiene sesión activa"""
    try:
        user = get_current_user_optional(request, db)
        return user is not None
    except:
        return False


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, db: Session = Depends(get_db)):
    """Página de login SSR"""
    # Si ya está autenticado, redirigir al dashboard
    if is_authenticated(request, db):
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_from_session)
):
    """Página de dashboard/chat (protegida)"""
    # Obtener conversaciones del usuario
    convs = db.query(Conversation).filter(Conversation.user_id == user.id).order_by(Conversation.created_at.desc()).limit(50).all()  # type: ignore[attr-defined]

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "conversations": convs
        }
    )


@router.get("/config", response_class=HTMLResponse)
async def config_page(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_from_session)
):
    """Página de configuración (protegida)"""
    settings = get_settings()
    return templates.TemplateResponse(
        "config.html",
        {
            "request": request,
            "user": user,
            "settings": {
                "ollama_host": settings.ollama_host,
                "ollama_model": settings.ollama_model,
                "ollama_temperature": settings.ollama_temperature,
                "ollama_top_p": settings.ollama_top_p,
                "ollama_max_tokens": settings.ollama_max_tokens,
            }
        }
    )


@router.get("/admin", response_class=HTMLResponse)
async def admin_page(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_from_session)
):
    """Panel admin (protegido, solo admins)"""
    if user.role != "admin":  # type: ignore[attr-defined]
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado"
        )

    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "user": user
        }
    )


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, db: Session = Depends(get_db)):
    """Página de registro"""
    # Si ya está autenticado, redirigir al dashboard
    if is_authenticated(request, db):
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    email = request.query_params.get("email", "")
    return templates.TemplateResponse(
        "register.html",
        {
            "request": request,
            "prefill_email": email
        }
    )


@router.get("/conversations", response_class=HTMLResponse)
async def conversations_list_page(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_from_session)
):
    """Página de lista de conversaciones (protegida)"""
    # Obtener conversaciones del usuario con datos adicionales
    convs = db.query(Conversation).filter(Conversation.user_id == user.id).order_by(Conversation.created_at.desc()).all()  # type: ignore[attr-defined]

    # Enriquecer con mensaje count y última actividad
    conversations_data = []
    for conv in convs:
        msg_count = db.query(func.count(Message.id)).filter(Message.conversation_id == conv.id).scalar() or 0  # type: ignore[attr-defined]
        last_msg = db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.created_at.desc()).first()  # type: ignore[attr-defined]

        conversations_data.append({
            "id": conv.id,  # type: ignore[attr-defined]
            "title": conv.title,  # type: ignore[attr-defined]
            "status": conv.status,  # type: ignore[attr-defined]
            "created_at": conv.created_at,  # type: ignore[attr-defined]
            "last_message_at": last_msg.created_at if last_msg else None,  # type: ignore[attr-defined]
            "message_count": msg_count,
        })

    return templates.TemplateResponse(
        "conversations-list.html",
        {
            "request": request,
            "user": user,
            "conversations": conversations_data,
        }
    )


@router.get("/conversations/{conversation_id}", response_class=HTMLResponse)
async def conversation_detail_page(
    conversation_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_from_session)
):
    """Página de detalle de conversación (protegida)"""
    # Verificar que el usuario tiene acceso a esta conversación
    conv = db.query(Conversation).filter(  # type: ignore[attr-defined]
        Conversation.id == conversation_id,  # type: ignore[attr-defined]
        Conversation.user_id == user.id  # type: ignore[attr-defined]
    ).first()

    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversación no encontrada"
        )

    # Obtener todos los mensajes de la conversación
    messages = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at.asc()).all()  # type: ignore[attr-defined]

    return templates.TemplateResponse(
        "conversation-detail.html",
        {
            "request": request,
            "user": user,
            "conversation": conv,
            "messages": messages,
        }
    )


@router.get("/", response_class=HTMLResponse)
async def root(request: Request, db: Session = Depends(get_db)):
    """Ruta raíz: redirigir a dashboard si autenticado, a login si no"""
    if is_authenticated(request, db):
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    else:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
