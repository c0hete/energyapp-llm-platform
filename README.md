# EnergyApp LLM Platform

Plataforma de IA autohospedada para EnergyApp con FastAPI + Ollama (Qwen 2.5:3B). Pensada para operar en VPS propio con seguridad básica y despliegue automatizado.

## Características
- Inferencia local (Ollama en `127.0.0.1:11434`), sin envío de datos externos.
- Autenticación JWT (access/refresh), roles `admin` y `user`; soporte 2FA TOTP opcional.
- Historias de conversación persistidas (users, conversations, messages).
- UI ligera servida desde `/static/index.html`: login con accesos rápidos, chat con streaming y limpiado, pestañas Chat/Config/Admin, lista de conversaciones.
- Panel Admin (solo rol admin): listado de usuarios con última actividad, explorador de conversaciones/mensajes y reasignación de conversaciones mediante selector de usuario.
- Config de modelo desde la UI (host/model/temperature/top_p/max_tokens) y ping a Ollama.
- CORS restringido a dominio público (`https://energyapp.alvaradomazzei.cl`).
- Servicio uvicorn bajo systemd; reverse proxy Caddy con TLS.

## Cuentas demo (para pruebas rápidas)
- admin@example.com / **admin123** (rol: admin)
- trabajador@example.com / **worker123** (rol: trabajador)
- supervisor@example.com / **supervisor123** (rol: supervisor)

Los accesos rápidos en el login rellenan estas credenciales.

## Modelo actual
- **Modelo**: Qwen 2.5:3B Instruct (GGUF Q4)
- **Consumo esperado**: ~2–3 GB RAM durante inferencia

## Estructura
- `src/`: API FastAPI (auth, conversations, admin), cliente Ollama.
- `config/`: settings base (`settings.yaml`).
- `static/`: UI HTML/JS/CSS.
- `scripts/`: utilidades (dev_api.sh, seed_admin.py, deploy.sh).
- `docs/`: documentación de arquitectura y operación.
- `data/`, `logs/`: carpetas locales (se crean al iniciar).

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
- Servicio systemd `energyapp.service` (uvicorn 0.0.0.0:8001)
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

## 2FA (TOTP)
- Si el usuario tiene 2FA habilitado (`totp_enabled=True` y `totp_secret`), el login responde `needs_2fa=True` y entrega `session_token`; el código TOTP se valida en `/auth/verify-2fa` y recién ahí se devuelven tokens.
- Endpoint de soporte/demo para QR de cuentas demo: `/auth/demo-qr-codes`.
- En la UI, al requerir 2FA se muestra el QR y el campo de código de 6 dígitos.

## Registro con dominio permitido
- `/auth/register` admite nuevos usuarios solo con correos `@alvaradomazzei.cl` o `@inacapmail.cl`.

## Licencia
MIT. Autor: Jose Alvarado Mazzei, 2025.
