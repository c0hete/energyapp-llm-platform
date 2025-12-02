from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import httpx

from .. import schemas
from ..config import get_settings, Settings
from ..deps import get_current_user, get_db
from ..models import User

router = APIRouter(prefix="/config", tags=["config"])


def _validate_params(data: schemas.ConfigInfo) -> None:
    if not (0 <= data.ollama_temperature <= 1):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="temperature fuera de rango (0-1)")
    if not (0 <= data.ollama_top_p <= 1):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="top_p fuera de rango (0-1)")
    if data.ollama_max_tokens <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="max_tokens debe ser mayor a 0")


@router.get("/info", response_model=schemas.ConfigInfo)
def get_info(
    settings: Settings = Depends(get_settings),
    user: User = Depends(get_current_user),  # noqa: B008
):
    return schemas.ConfigInfo(
        ollama_host=settings.ollama_host,
        ollama_model=settings.ollama_model,
        ollama_temperature=settings.ollama_temperature,
        ollama_top_p=settings.ollama_top_p,
        ollama_max_tokens=settings.ollama_max_tokens,
    )


@router.post("/set", response_model=schemas.ConfigInfo)
def set_config(
    body: schemas.ConfigInfo,
    db: Session = Depends(get_db),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
    user: User = Depends(get_current_user),  # noqa: B008
):
    _validate_params(body)
    # Persistencia en memoria (se pierde al reiniciar); para algo permanente usar tabla settings.
    settings.ollama_host = body.ollama_host
    settings.ollama_model = body.ollama_model
    settings.ollama_temperature = body.ollama_temperature
    settings.ollama_top_p = body.ollama_top_p
    settings.ollama_max_tokens = body.ollama_max_tokens
    return body


@router.post("/test-ollama")
async def test_ollama(
    settings: Settings = Depends(get_settings),  # noqa: B008
    user: User = Depends(get_current_user),  # noqa: B008
):
    url = settings.ollama_host.rstrip("/") + "/api/tags"
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(url)
            resp.raise_for_status()
        return {"ok": True}
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ollama no disponible: {exc}",
        )
