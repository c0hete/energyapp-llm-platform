# Arquitectura y despliegue

## Visión general
- Plataforma LLM privada con inferencia local vía Ollama (Qwen 2.5:3B).
- Backend FastAPI (auth, chat, conversaciones, admin) + UI estática.
- Reverse proxy Caddy con TLS; servicio uvicorn gestionado por systemd.
- Entorno prod: Ubuntu 24.04, 6 vCPU, ~12 GB RAM, 100 GB SSD.

## Componentes
- Ollama: `127.0.0.1:11434` con `qwen2.5:3b-instruct` (GGUF Q4).
- App LLM: `/root/energyapp-llm-platform` (FastAPI + UI).
- DB: PostgreSQL 16 (`energyapp`), tablas users/conversations/messages.
- Proxy: Caddy expone `https://energyapp.alvaradomazzei.cl` → `127.0.0.1:8001`.
- Seguridad base: UFW (80/443), CORS restringido, HTTPS, Fail2Ban.
- UX actual: favicon, mensaje de bienvenida en chat, estado “generando…” durante streaming, auto-títulos de conversación, botón demo admin y accesos rápidos (admin/trabajador/supervisor).

## Estructura de repo
- `src/`: API (auth, conversations, admin), cliente Ollama.
- `config/`: `settings.yaml`; `.env` para secretos.
- `static/`: UI HTML/JS/CSS.
- `scripts/`: dev/deploy/seed.
- `docs/`: esta documentación.
- `data/`, `logs/`: se crean en runtime.

## Despliegue actual (prod)
- Ruta app: `/root/energyapp-llm-platform`
- venv: `.venv`
- systemd: `energyapp.service` (uvicorn 0.0.0.0:8001)
- Caddyfile bloque activo:
  ```
  energyapp.alvaradomazzei.cl {
      encode gzip
      reverse_proxy 127.0.0.1:8001
  }
  ```
- CORS permitido: `https://energyapp.alvaradomazzei.cl`
- Health: `/health`
- UI: `/static/index.html`

## Configuración (ENV)
```
ENERGYAPP_DB_URL=postgresql+psycopg2://energyapp:energyapp_db_demo@localhost:5432/energyapp
ENERGYAPP_SECRET_KEY=cambia_esto_tambien
ENERGYAPP_ALLOWED_ORIGINS=["https://energyapp.alvaradomazzei.cl"]
ENERGYAPP_LOG_TO_FILE=true
ENERGYAPP_LOG_FILE=./logs/app.log
```

## Flujo de actualización
```
cd /root/energyapp-llm-platform
git pull
source .venv/bin/activate
pip install -r requirements.txt   # si hay nuevas deps
sudo systemctl restart energyapp
```
Logs: `sudo journalctl -u energyapp -f`  
Estado: `sudo systemctl status energyapp`

## Integración con Ollama
- Endpoint: `http://127.0.0.1:11434`
- Modelo: `qwen2.5:3b-instruct`
- No exponer Ollama a internet; solo localhost/proxy.

## Seguridad / operación (estado)
- CORS restringido a dominio público.
- UFW abierto 80/443; 8001 solo interno.
- TLS Let’s Encrypt vía Caddy.
- systemd con restart automático.
- Pendiente: rate-limit en Caddy; backup DB (pg_dump diario); rotación de logs.

## API y funciones
- Auth: `/auth/login`, `/auth/refresh`, `/auth/me` (JWT access/refresh, roles admin/user).
- Chat: `/chat` (stream a Ollama, guarda mensajes, crea conversación si falta).
- Conversaciones: listar/crear/obtener/actualizar, borrar; mensajes por conversación.
- Admin: listar usuarios, activar/desactivar, cambiar rol; listar conversaciones/mensajes (solo lectura).
- UI: login + chat, lista de conversaciones, pestañas Chat/Config/Admin (demo), botones perfil/logout.

## Plan siguiente fase
- Seguridad extra: rate-limit en Caddy, backup pg_dump, rotación de logs.
- UX: bienvenida, indicador de streaming, renombrar conversaciones y refresco auto.
- Perfil/Config: email/rol/cambio password; selector de modelo y parámetros; ping a Ollama.
- Admin: activar/desactivar usuarios, cambiar rol; listados con filtros/paginación.
- Datos/escala: paginar mensajes/conversaciones; límites de tamaño; refresh tokens en front.
- Pruebas: auth básica y mock de chat; smoke-test para despliegues.
