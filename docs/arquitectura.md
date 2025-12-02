# Arquitectura y despliegue

## Visión general
- Plataforma LLM privada con inferencia local vía Ollama (Qwen 2.5:3B).
- Backend FastAPI (auth, chat, conversaciones, admin) + UI estática.
- Reverse proxy Caddy con TLS; servicio uvicorn gestionado por systemd.
- Entorno prod: Ubuntu 24.04, 6 vCPU, ~12 GB RAM, 100 GB SSD.

## Componentes
- Ollama: `127.0.0.1:11434` con `qwen2.5:3b-instruct` (GGUF Q4).
- App LLM: `/root/energyapp-llm-platform` (FastAPI + UI).
- DB: PostgreSQL 16 (`energyapp`), tablas `users`, `conversations`, `messages`.
- Proxy: Caddy expone `https://energyapp.alvaradomazzei.cl` → `127.0.0.1:8001`.
- Seguridad base: UFW (80/443), CORS restringido, HTTPS, Fail2ban.
- UX: favicon, bienvenida, streaming con estado “generando”, auto-títulos de conversación, accesos rápidos (admin/trabajador/supervisor), logo en header, panel Admin con reasignación de conversaciones. Soporta 2FA TOTP en login (si el usuario tiene `totp_enabled`); 2FA self-service para emails `@inacapmail.cl`.

## Cuentas demo
- **admin@example.com / admin123** (rol: admin)
- **trabajador@example.com / worker123** (rol: trabajador)
- **supervisor@example.com / supervisor123** (rol: supervisor)

Los accesos rápidos en el login rellenan estas credenciales.

## Estructura de repo
- `src/`: API (auth, conversations, admin), cliente Ollama.
- `config/`: `settings.yaml`; `.env` para secretos.
- `static/`: UI HTML/JS/CSS.
- `scripts/`: dev/deploy/seed.
- `docs/`: esta documentación.
- `data/`, `logs/`: se crean en runtime.
- Registro: `/auth/register` restringido a dominios `@alvaradomazzei.cl` y `@inacapmail.cl`.
- Cambio de contraseña: solo permitido para cuentas `@inacapmail.cl`.
- Roles (backend y UI):
  - Admin: ve todos los usuarios/conversaciones/mensajes; reasignar cualquiera; pestaña Admin visible.
  - Supervisor: pestaña Admin visible; solo ve trabajadores y a sí mismo; conversaciones/mensajes solo de trabajadores y propias; reasigna solo dentro de ese scope.
  - Trabajador: sin pestaña Admin; solo sus conversaciones.

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
- Rate-limit vía Fail2ban (/chat y /auth; lee `/var/log/caddy/energyapp-access.log`).
- Backups diarios (pg_dump) en `/srv/backups/energyapp/` (retiene 14 días).
- Logrotate para Caddy y para la app (si `ENERGYAPP_LOG_TO_FILE=true`).

## API y funciones
- Auth: `/auth/login`, `/auth/verify-2fa` (TOTP), `/auth/refresh`, `/auth/me`, `/auth/register` (dominios permitidos).
- 2FA self-service: `/auth/setup-2fa` (solo emails `@inacapmail.cl`); cambio de contraseña solo para `@inacapmail.cl`.
- Chat: `/chat` (stream a Ollama, guarda mensajes, crea conversación si falta).
- Conversaciones: listar/crear/obtener/actualizar, borrar; mensajes por conversación.
- Admin: listar usuarios (con última actividad), ver conversaciones/mensajes, reasignar conversación a otro usuario.
- UI: login + chat, pestañas Chat/Config/Admin, perfil/logout, accesos rápidos demo.

## Próximos pasos sugeridos
- Paginación en listas largas (usuarios, conversaciones, mensajes).
- Límite de tamaño de mensaje y refresh tokens en front.
- Pruebas: auth básica, mock de chat, smoke-test de despliegue.
