from typing import AsyncGenerator
from pathlib import Path
import json
import logging
from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.responses import StreamingResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import httpx
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .config import get_settings, Settings
from .db import SessionLocal, engine
from .models import Base, Conversation, Message, SystemPrompt
from .ollama_client import OllamaClient
from .deps import get_current_user_hybrid, get_db
from . import schemas
from .routes import auth as auth_routes
from .routes import conversations as conv_routes
from .routes import admin as admin_routes
from .routes import config as config_routes
from .routes import prompts as prompts_routes
from .routes import engine as engine_routes
from .routes import cie10 as cie10_routes
from .csrf import generate_csrf_token, validate_csrf_token
from .tools import execute_cie10_tool, get_tool_definitions

# Crear tablas si no existen (para entornos de desarrollo)
Base.metadata.create_all(bind=engine)

# Configuracion inicial de logging y settings compartidos
_settings = get_settings()
logging.basicConfig(
    level=getattr(logging, _settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(_settings.log_file) if _settings.log_to_file else logging.NullHandler(),
    ],
)
app = FastAPI(title="EnergyApp LLM Platform", version="0.2.0")

# Rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["100 per minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda request, exc: JSONResponse(
    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
    content={"detail": "Rate limit exceeded"}
))


def get_settings_dep() -> Settings:
    return get_settings()


# CSRF protection middleware
@app.middleware("http")
async def csrf_middleware(request: Request, call_next):
    # Generate CSRF token for GET requests
    if request.method == "GET":
        response = await call_next(request)
        csrf_token = generate_csrf_token()
        response.set_cookie(
            "csrf_token",
            csrf_token,
            max_age=3600,  # 1 hour
            httponly=False,  # Allow JavaScript to read it
            secure=True,
            samesite="lax"
        )
        response.headers["X-CSRF-Token"] = csrf_token
        return response

    # Validate CSRF token for state-changing requests
    if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
        csrf_token_from_header = request.headers.get("X-CSRF-Token")
        csrf_token_from_cookie = request.cookies.get("csrf_token")

        if csrf_token_from_header and csrf_token_from_cookie and csrf_token_from_header == csrf_token_from_cookie:
            response = await call_next(request)
            return response
        # Skip CSRF validation for auth endpoints (not protected by session)
        elif request.url.path in ["/auth/login", "/auth/register", "/auth/verify-2fa"]:
            response = await call_next(request)
            return response
        # Skip CSRF validation for endpoints protected by session token (session is CSRF protection)
        elif request.url.path.startswith("/chat") or request.url.path.startswith("/conversations") or request.url.path.startswith("/prompts"):
            # These endpoints validate session token, which is CSRF-proof because cookies can't be read by cross-origin JS
            response = await call_next(request)
            return response
        else:
            # CSRF token mismatch or missing
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token invalid or missing"
            )

    response = await call_next(request)
    return response


# CORS restricto a dominios permitidos
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["meta"])
async def health(settings: Settings = Depends(get_settings_dep)):
    return {"status": "ok", "env": settings.env, "model": settings.ollama_model}


@app.post("/chat", tags=["chat"])
async def chat(
    body: schemas.ChatRequest,
    settings: Settings = Depends(get_settings_dep),
    db: Session = Depends(get_db),
    user=Depends(get_current_user_hybrid),
):
    # Verificar acceso a la conversacion (si se provee conversation_id)
    if body.conversation_id:
        conv = (
            db.query(Conversation)  # type: ignore[attr-defined]
            .filter(Conversation.id == body.conversation_id, Conversation.user_id == user.id)  # type: ignore[attr-defined]
            .first()
        )
        if not conv:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    else:
        conv = Conversation(user_id=user.id, title="Nueva conversacion", status="open")  # type: ignore[attr-defined]
        db.add(conv)
        db.commit()
        db.refresh(conv)
    conv_id = conv.id  # type: ignore[attr-defined]

    # Guardar mensaje del usuario
    user_msg = Message(  # type: ignore[attr-defined]
        conversation_id=conv.id, role="user", content=body.prompt
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # Resolver el system prompt (desde prompt_id si se proporciona, sino usar el parámetro system)
    system_prompt = body.system or "Eres un asistente útil."
    if body.prompt_id:
        prompt_obj = db.query(SystemPrompt).filter(SystemPrompt.id == body.prompt_id).first()  # type: ignore[attr-defined]
        if prompt_obj:
            system_prompt = prompt_obj.content  # type: ignore[attr-defined]

    client = OllamaClient(base_url=settings.ollama_host, model=settings.ollama_model)

    # Obtener definiciones de tools para Tool Calling
    tools = get_tool_definitions()

    async def streamer():
        assistant_content = ""
        try:
            # Primera generación con tools disponibles
            async for token in client.generate(
                prompt=body.prompt,
                system=system_prompt,
                stream=True,
                tools=tools
            ):
                try:
                    data = json.loads(token)

                    # Verificar si hay tool call
                    # En /api/chat, tool_calls viene dentro de message
                    tool_calls = None
                    if "message" in data and "tool_calls" in data["message"]:
                        tool_calls = data["message"]["tool_calls"]
                    elif "tool_calls" in data:
                        tool_calls = data["tool_calls"]

                    if tool_calls:
                        for tool_call in tool_calls:
                            tool_name = tool_call.get("function", {}).get("name")
                            tool_args = tool_call.get("function", {}).get("arguments", {})

                            if isinstance(tool_args, str):
                                tool_args = json.loads(tool_args)

                            # Ejecutar la herramienta
                            if tool_name in ["search_cie10", "get_cie10_code"]:
                                result = await execute_cie10_tool(tool_name, tool_args)

                                # Formatear resultado para el usuario
                                if result.get("success"):
                                    formatted = format_cie10_result(result)
                                    assistant_content += formatted
                                    yield formatted
                                else:
                                    error_msg = f"Error en búsqueda: {result.get('error')}\n"
                                    assistant_content += error_msg
                                    yield error_msg

                    # Respuesta normal (texto)
                    # /api/chat usa message.content, /api/generate usa response
                    chunk = ""
                    if "message" in data:
                        chunk = data["message"].get("content", "")
                    else:
                        chunk = data.get("response", "")

                    if chunk:
                        assistant_content += chunk
                        yield chunk

                    if data.get("done"):
                        break

                except json.JSONDecodeError:
                    # Si llega basura, se omite
                    continue
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Ollama no disponible: {exc}",
            )
        finally:
            # Guardar respuesta del asistente (se ejecuta siempre, incluso si hay errores)
            if assistant_content:
                assistant_msg = Message(  # type: ignore[attr-defined]
                    conversation_id=conv_id, role="assistant", content=assistant_content
                )
                db.add(assistant_msg)
                db.commit()

    return StreamingResponse(streamer(), media_type="text/plain")


def format_cie10_result(result: dict) -> str:
    """Formatea los resultados de CIE-10 para presentación al usuario"""
    if not result.get("success"):
        return f"\nError: {result.get('error')}\n"

    data = result.get("data", [])
    if isinstance(data, dict):
        # Código individual
        formatted = f"\nCódigo CIE-10: {data.get('code')}\n"
        formatted += f"Descripción: {data.get('description')}\n"
        formatted += f"Nivel: {data.get('level')} | Rango: {'Sí' if data.get('is_range') else 'No'}\n"
        if data.get('parent_code'):
            formatted += f"Código padre: {data.get('parent_code')}\n"
        formatted += "\n"
        return formatted
    elif isinstance(data, list):
        # Lista de códigos
        formatted = f"\nResultados para '{result.get('query')}':\n\n"
        for idx, item in enumerate(data[:10], 1):
            formatted += f"{idx}. {item.get('code')} - {item.get('description')}\n"
        formatted += "\n"
        return formatted

    return "\n"


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/static/index.html", status_code=status.HTTP_307_TEMPORARY_REDIRECT)


# Servir UI estatica simple (ruta absoluta para evitar problemas de cwd)
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


app.include_router(auth_routes.router)
app.include_router(conv_routes.router)
app.include_router(admin_routes.router)
app.include_router(config_routes.router)
app.include_router(prompts_routes.router)
app.include_router(engine_routes.router)
app.include_router(cie10_routes.router)
