from typing import AsyncGenerator, Optional
import httpx
from .config import get_settings


class OllamaClient:
    """Cliente ligero para llamar a Ollama en modo streaming."""

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        settings = get_settings()
        self.base_url = base_url or settings.ollama_host
        self.model = model or settings.ollama_model
        self.temperature = settings.ollama_temperature
        self.top_p = settings.ollama_top_p
        self.max_tokens = settings.ollama_max_tokens

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        stream: bool = True,
    ) -> AsyncGenerator[str, None]:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": self.temperature,
                "top_p": self.top_p,
                "num_predict": self.max_tokens,
            },
        }
        if system:
            payload["system"] = system

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", f"{self.base_url}/api/generate", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    yield line
