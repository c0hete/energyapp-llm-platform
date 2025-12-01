from typing import AsyncGenerator
from pathlib import Path
import json
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import StreamingResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import httpx

from .config import get_settings, Settings
from .db import SessionLocal, engine
from .models import Base, Conversation, Message
from .ollama_client import OllamaClient
from .deps import get_current_user, get_db
from . import schemas
from .routes import auth as auth_routes
from .routes import conversations as conv_routes
from .routes import admin as admin_routes

# Crear tablas si no existen (para entornos de desarrollo)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="EnergyApp LLM Platform", version="0.2.0")


def get_settings_dep() -> Settings:
    return get_settings()


@app.get("/health", tags=["meta"])
async def health(settings: Settings = Depends(get_settings_dep)):
    return {"status": "ok", "env": settings.env, "model": settings.ollama_model}


@app.post("/chat", tags=["chat"])
async def chat(
    body: schemas.ChatRequest,
    settings: Settings = Depends(get_settings_dep),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
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

    client = OllamaClient(base_url=settings.ollama_host, model=settings.ollama_model)

    async def streamer():
        assistant_content = ""
        try:
            async for token in client.generate(prompt=body.prompt, system=body.system, stream=True):
                try:
                    data = json.loads(token)
                    chunk = data.get("response", "")
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
        # Guardar respuesta del asistente
        assistant_msg = Message(  # type: ignore[attr-defined]
            conversation_id=conv_id, role="assistant", content=assistant_content
        )
        db.add(assistant_msg)
        db.commit()

    return StreamingResponse(streamer(), media_type="text/plain")


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/static/index.html", status_code=status.HTTP_307_TEMPORARY_REDIRECT)


# Servir UI estatica simple (ruta absoluta para evitar problemas de cwd)
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


app.include_router(auth_routes.router)
app.include_router(conv_routes.router)
app.include_router(admin_routes.router)
