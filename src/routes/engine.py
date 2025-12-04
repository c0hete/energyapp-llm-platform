"""
Engine monitoring endpoints for system health and Ollama status
"""
from fastapi import APIRouter, Depends
import psutil
import httpx
from ..config import Settings, get_settings

router = APIRouter(prefix="/engine", tags=["engine"])


async def check_ollama_health(ollama_host: str) -> bool:
    """Check if Ollama is responding to health checks"""
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{ollama_host}/api/tags")
            return response.status_code == 200
    except Exception:
        return False


@router.get("/status")
async def get_engine_status(settings: Settings = Depends(get_settings)):
    """
    Get current engine status including:
    - CPU usage percentage
    - Memory usage (used, total, free in GB)
    - Ollama health status
    - Overall engine status (ok, warning, critical, offline)
    """
    # Get CPU and memory metrics
    cpu_percent = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory()

    # Convert bytes to GB
    memory_used_gb = memory.used / (1024 ** 3)
    memory_total_gb = memory.total / (1024 ** 3)
    memory_free_gb = memory.available / (1024 ** 3)

    # Check Ollama health
    ollama_healthy = await check_ollama_health(settings.ollama_host)
    ollama_status = "healthy" if ollama_healthy else "unhealthy"

    # Determine overall engine status based on metrics
    # Critical: CPU > 85% or available memory < 2GB or Ollama offline
    # Warning: CPU between 60-85%
    # OK: CPU < 60% and sufficient memory and Ollama healthy

    if not ollama_healthy:
        status = "offline"
    elif cpu_percent > 85 or memory_free_gb < 2.0:
        status = "critical"
    elif cpu_percent > 60:
        status = "warning"
    else:
        status = "ok"

    return {
        "status": status,
        "cpu_percent": round(cpu_percent, 1),
        "memory_used_gb": round(memory_used_gb, 2),
        "memory_total_gb": round(memory_total_gb, 2),
        "memory_free_gb": round(memory_free_gb, 2),
        "ollama": ollama_status,
        "engine_enabled": True
    }
