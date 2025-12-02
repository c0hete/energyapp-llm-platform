# EnergyApp LLM Platform

Plataforma de IA autohospedada con FastAPI + Ollama (Qwen 2.5:3B). Pensada para operar en VPS propio con seguridad basica y despliegue simple.

## Caracteristicas principales
- Inferencia local (Ollama en `127.0.0.1:11434`), sin envio de datos a terceros.
- Autenticacion dual:
  - JWT para la API (access/refresh tokens).
  - Sesiones por cookies persistidas en BD con auditoria de IP/User-Agent.
  - Soporte 2FA TOTP opcional.
- Historico de conversaciones persistido (users, conversations, messages, sessions).
- Dos interfaces UI:
  - SPA original en `/static/index.html` (chat, config, admin via JWT).
  - SSR recomendada en `/login`, `/dashboard`, `/config`, `/admin`, `/register` (Jinja2 + sesiones).
- Panel Admin SSR interactivo: 3 columnas (usuarios | conversaciones | mensajes) con reasignacion de conversaciones y visor de mensajes.
- Configuracion de modelo desde la UI (host/model/temperature/top_p/max_tokens) y ping a Ollama.
- Logging: auth.log, audit.log, app.log con rotacion.
- CORS restringido a `https://energyapp.alvaradomazzei.cl`.
- Servicio uvicorn bajo systemd; reverse proxy Caddy con TLS.

## Roles y visibilidad
- Admin: ve todo y puede reasignar cualquier conversacion.
- Supervisor: ve trabajadores y a si mismo; puede reasignar dentro de ese scope.
- Trabajador: solo sus propias conversaciones.
- Cambio de contrasena: solo para correos `@inacapmail.cl`.
- 2FA: si `totp_enabled` esta activo, el login pide TOTP; auto-setup disponible para `@inacapmail.cl`.
- Endpoints admin aceptan sesion o JWT (hibrido) para compatibilidad SSR/SPA.

## Cuentas demo (pruebas rapidas)
- administrador@alvaradomazzei.cl / **admin123** (rol: admin)
- trabajador@alvaradomazzei.cl / **worker123** (rol: trabajador)
- supervisor@alvaradomazzei.cl / **supervisor123** (rol: supervisor)

Nota: Estas cuentas no pueden cambiar contrasena. Los accesos rapidos en el login rellenan estas credenciales.

## Modelo actual
- Modelo: Qwen 2.5:3B Instruct (GGUF Q4)
- Consumo esperado: ~2-3 GB RAM durante inferencia

## Estructura de proyecto
- `src/`: API FastAPI (auth, conversations, admin, config, ssr), modelos SQLAlchemy y cliente Ollama.
- `templates/`: vistas SSR (login, dashboard, config, admin, register).
- `static/`: SPA original (HTML/JS/CSS), se mantiene por compatibilidad.
- `config/`: `settings.yaml` base.
- `scripts/`: utilidades (dev_api.sh, seed_admin.py, deploy.sh).
- `docs/`: documentacion de arquitectura y operacion.
- `data/`, `logs/`: carpetas locales creadas en runtime.

## Requisitos
- Python 3.10+ (local usamos 3.13.8).
- PostgreSQL (prod) o SQLite (dev por defecto).
- Ollama sirviendo en `localhost:11434` con Qwen 2.5:3B.

## Configuracion (.env recomendado)
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
.\.venv\Scripts\activate           # Windows (en Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## Rutas principales
- SSR (recomendado): `/login`, `/dashboard`, `/config`, `/admin`, `/register`
- SPA (legado): `/static/index.html`
- Health: `/health`

## Despliegue en VPS (resumen)
```
cd /root/energyapp-llm-platform
source .venv/bin/activate
git pull
pip install -r requirements.txt   # si hay nuevas dependencias
systemctl restart energyapp
```
Logs: `journalctl -u energyapp -f`  
Estado: `systemctl status energyapp`
