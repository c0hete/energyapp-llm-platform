from typing import AsyncGenerator, Optional, List, Dict, Any
import httpx
from .config import get_settings


class OllamaClient:
    """Cliente para Ollama con soporte de Tool Calling."""

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
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Genera respuesta con soporte opcional de Tool Calling.

        Args:
            prompt: Mensaje del usuario
            system: System prompt
            stream: Si se debe hacer streaming
            tools: Lista de herramientas disponibles (Tool Calling)
        """
        # Si hay tools, usar /api/chat (requerido para tool calling)
        # Si no hay tools, usar /api/generate (backward compatibility)
        if tools:
            # Formato para /api/chat (messages array)
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": self.model,
                "messages": messages,
                "stream": stream,
                "tools": tools,
                "options": {
                    "temperature": self.temperature,
                    "top_p": self.top_p,
                    "num_predict": self.max_tokens,
                },
            }
            endpoint = "/api/chat"
        else:
            # Formato para /api/generate (original)
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
            endpoint = "/api/generate"

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", f"{self.base_url}{endpoint}", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    yield line
