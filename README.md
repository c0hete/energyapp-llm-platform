# EnergyApp LLM Platform

Plataforma de IA autohospedada para EnergyApp con FastAPI + Ollama (Qwen 2.5:3B). Pensada para operar en VPS propio con seguridad básica y despliegue automatizado.

## Características
- Inferencia local (Ollama en `127.0.0.1:11434`), sin datos externos.
- Autenticación JWT (access/refresh), roles `admin` y `user`.
- Historias de conversación en base de datos (users, conversations, messages).
- UI ligera servida desde `/static/index.html` (login + chat), con favicon, mensaje de bienvenida, estado “generando…” en streaming y botón de “Login demo (admin)”.
- CORS restringido a dominio público (`https://energyapp.alvaradomazzei.cl`).
- Servicio uvicorn manejado por systemd; reverse proxy Caddy con TLS.

## Modelo actual
- **Modelo**: Qwen 2.5:3B Instruct (GGUF Q4)
- **Consumo esperado**: ~2–3 GB RAM durante inferencia

## Estructura
- `src/` – API FastAPI, rutas auth/conversations/admin, cliente Ollama.
- `config/` – settings base (`settings.yaml`).
- `static/` – UI HTML/JS/CSS.
- `scripts/` – utilidades (dev_api.sh, seed_admin.py, deploy.sh).
- `docs/` – documentación de arquitectura y operación.
- `data/`, `logs/` – carpetas locales (creadas al iniciar).

## Requisitos
- Python 3.10+ (local usamos 3.13.8)
- PostgreSQL (prod) o SQLite (dev por defecto)
- Ollama sirviendo en localhost:11434 con el modelo Qwen 2.5:3B

## Configuración (.env recomendado)
```
ENERGYAPP_DB_URL=postgresql+psycopg2://energyapp:energyapp_db_demo@localhost:5432/energyapp
ENERGYAPP_SECRET_KEY=cambia_esto_tambien
# Opcional: CORS, logging
# ENERGYAPP_ALLOWED_ORIGINS=["https://energyapp.alvaradomazzei.cl"]
# ENERGYAPP_LOG_TO_FILE=true
# ENERGYAPP_LOG_FILE=./logs/app.log
```

## Uso en local
```
python -m venv .venv
source .venv/bin/activate        # en Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```
UI: http://localhost:8000/static/index.html  
Health: http://localhost:8000/health

## Despliegue en VPS (resumen)
- Código en `/root/energyapp-llm-platform`
- venv: `/root/energyapp-llm-platform/.venv`
- Servicio systemd `energyapp.service` ejecuta uvicorn en `0.0.0.0:8001`
- Caddy expone `https://energyapp.alvaradomazzei.cl` → reverse_proxy a 127.0.0.1:8001
- DB: PostgreSQL en localhost:5432 (`energyapp`)

Actualizar en el VPS:
```
cd /root/energyapp-llm-platform
git pull
source .venv/bin/activate
pip install -r requirements.txt   # solo si hay nuevas deps
sudo systemctl restart energyapp
```

Comandos útiles (systemd):
- Estado: `sudo systemctl status energyapp`
- Logs en vivo: `sudo journalctl -u energyapp -f`
- Restart: `sudo systemctl restart energyapp`

## Licencia
MIT. Autor: Jose Alvarado Mazzei, 2025.
