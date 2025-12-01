from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    app_name: str = "energyapp-llm"
    env: str = "dev"

    # Security
    secret_key: str = "change-me"  # cambia en produccion
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 60 * 24 * 14  # 14 dias
    allowed_origins: list[str] = Field(
        default_factory=lambda: ["https://energyapp.alvaradomazzei.cl"]
    )

    # Ollama
    ollama_host: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:3b-instruct"
    ollama_temperature: float = 0.6
    ollama_top_p: float = 0.9
    ollama_max_tokens: int = 512

    # Database
    db_url: str = Field(
        default="sqlite:///./data/app.db",
        description="Cadena de conexion SQLAlchemy. Usa postgres en prod.",
    )

    # Logging
    log_level: str = "INFO"
    log_to_file: bool = False
    log_file: str = "./logs/app.log"

    class Config:
        env_prefix = "ENERGYAPP_"
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()  # type: ignore[arg-type]
    # Crear carpetas basicas para data/logs si no existen
    Path("./data").mkdir(parents=True, exist_ok=True)
    Path("./logs").mkdir(parents=True, exist_ok=True)
    return settings
