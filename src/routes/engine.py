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
    # Get CPU and memory metrics with highest precision for real-time monitoring
    cpu_percent = psutil.cpu_percent(interval=0.05)
    memory = psutil.virtual_memory()

    # Convert bytes to GB
    memory_used_gb = memory.used / (1024 ** 3)
    memory_total_gb = memory.total / (1024 ** 3)
    memory_free_gb = memory.available / (1024 ** 3)

    # Check Ollama health
    ollama_healthy = await check_ollama_health(settings.ollama_host)
    ollama_status = "healthy" if ollama_healthy else "unhealthy"

    # Determine overall engine status based on metrics
    # Critical: CPU sustained at 99%+ or available memory < 1GB or Ollama offline
    # Warning: CPU at 95-99% (near saturation)
    # OK: CPU < 95% and sufficient memory (normal LLM inference)

    if not ollama_healthy:
        status = "offline"
    elif cpu_percent >= 99 or memory_free_gb < 1.0:
        status = "critical"
    elif cpu_percent >= 95:
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
