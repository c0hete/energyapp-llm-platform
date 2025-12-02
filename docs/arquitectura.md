# Arquitectura y despliegue

## Vision general
- Plataforma LLM privada con inferencia local via Ollama (Qwen 2.5:3B).
- Backend FastAPI modular (auth, chat, conversaciones, admin, config, ssr) + UI SSR y SPA legado.
- Reverse proxy Caddy con TLS; servicio uvicorn gestionado por systemd.
- Entorno prod: Ubuntu 24.04, 6 vCPU, ~12 GB RAM, 100 GB SSD.

## Componentes
- Ollama: `127.0.0.1:11434` con `qwen2.5:3b-instruct` (GGUF Q4).
- App LLM: `/root/energyapp-llm-platform` (FastAPI + UI).
- DB: PostgreSQL 16 (`energyapp`), tablas `users`, `conversations`, `messages`, `sessions`.
- Proxy: Caddy expone `https://energyapp.alvaradomazzei.cl` -> `127.0.0.1:8001`.
- Seguridad base: UFW (80/443), CORS restringido, HTTPS, Fail2ban.
- UX: favicon, bienvenida, streaming con estado "generando", auto-titulos de conversacion, accesos rapidos (admin/trabajador/supervisor), logo en header.
- 2FA TOTP en login si el usuario tiene `totp_enabled`; self-service 2FA para correos `@inacapmail.cl`.

## Cuentas demo
- administrador@alvaradomazzei.cl / admin123 (rol: admin)
- trabajador@alvaradomazzei.cl / worker123 (rol: trabajador)
- supervisor@alvaradomazzei.cl / supervisor123 (rol: supervisor)

Accesos rapidos en el login rellenan estas credenciales.

## Estructura de repo
- `src/`: API (auth, conversations, admin, config, ssr), cliente Ollama y modelos.
- `config/`: `settings.yaml`; `.env` para secretos.
- `templates/`: vistas SSR (login, dashboard, config, admin, register).
- `static/`: UI HTML/JS/CSS (SPA original).
- `scripts/`: dev/deploy/seed.
- `docs/`: esta documentacion.
- `data/`, `logs/`: se crean en runtime.
- Registro: `/auth/register` restringido a dominios `@alvaradomazzei.cl` y `@inacapmail.cl`.
- Cambio de contrasena: solo permitido para cuentas `@inacapmail.cl`.

## Roles (backend y UI)
- Admin: ve todos los usuarios/conversaciones/mensajes; reasigna cualquiera; pestaña Admin visible.
- Supervisor: pestaña Admin visible; solo ve trabajadores y a si mismo; conversaciones/mensajes solo de trabajadores y propias; reasigna dentro de ese scope.
- Trabajador: sin pestaña Admin; solo sus conversaciones.

## Admin SSR interactivo (nuevo)
- Layout de 3 columnas: usuarios | conversaciones | mensajes.
- Seleccion de usuario -> carga sus conversaciones (AJAX con sesion).
- Seleccion de conversacion -> visor de mensajes.
- Reasignacion de conversaciones a otro usuario (select dinamico).
- Endpoints admin aceptan sesion o JWT (hibrido) para compatibilidad SSR/SPA.

## Despliegue actual (prod)
- Ruta app: `/root/energyapp-llm-platform`
- venv: `.venv`
- systemd: `energyapp.service` (uvicorn 0.0.0.0:8001)
- Caddyfile bloque activo:
  ```
  energyapp.alvaradomazzei.cl {
      encode gzip
      reverse_proxy 127.0.0.1:8001
      log {
          output file /var/log/caddy/energyapp-access.log {
              roll_size 5mb
              roll_keep 14
              roll_keep_for 336h
          }
      }
  }
  ```
- CORS permitido: `https://energyapp.alvaradomazzei.cl`
- Health: `/health`
- UI SSR: `/login` -> `/dashboard`
- SPA (legado): `/static/index.html`

## Configuracion (ENV)
```
ENERGYAPP_DB_URL=postgresql+psycopg2://energyapp:energyapp_db_demo@localhost:5432/energyapp
ENERGYAPP_SECRET_KEY=cambia_esto_tambien
ENERGYAPP_ALLOWED_ORIGINS=["https://energyapp.alvaradomazzei.cl"]
ENERGYAPP_LOG_TO_FILE=true
ENERGYAPP_LOG_FILE=./logs/app.log
```

## Flujo de actualizacion
```
cd /root/energyapp-llm-platform
git pull
source .venv/bin/activate
pip install -r requirements.txt   # si hay nuevas deps
sudo systemctl restart energyapp
```
Logs: `sudo journalctl -u energyapp -f`  
Estado: `sudo systemctl status energyapp`

## Integracion con Ollama
- Cliente en `src/ollama_client.py`.
- Configurable en `config/settings.yaml` o variables de entorno.
- Ping desde UI de config (boton "Probar conexion").
