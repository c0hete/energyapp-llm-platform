# Arquitectura y despliegue

## Vision general
- Objetivo: Plataforma LLM privada para EnergyApp, con inferencia local via Ollama (Qwen 2.5:3B).
- Modo operativo: API/servicio interno que consumen apps (Laravel, Node.js, etc.).
- Entorno de produccion: Ubuntu 24.04, 6 vCPU, ~12 GB RAM, 100 GB SSD.

## Componentes
- Ollama: Sirve el modelo en `127.0.0.1:11434`.
- Aplicacion LLM (este repo): clientes, pipelines, endpoints y orquestacion.
- Servicios existentes: Caddy/Apache como reverse proxy, PostgreSQL 16, Docker (Nextcloud).
- Seguridad base: Fail2Ban + UFW; WireGuard (cuando funcione) para VPN.

## Estructura de carpetas (repo)
- `src/`: codigo fuente de la app (API, clientes, pipelines).
- `config/`: `settings.yaml` y variables sensibles (usar `.env`).
- `data/`: artefactos locales (embeddings, caches). Evitar commitear datos pesados.
- `tests/`: pruebas unitarias/integracion.
- `docs/`: documentacion.
- `scripts/`: utilidades de desarrollo/despliegue.

## Flujo de despliegue recomendado
1) Trabajo local: commits y push a GitHub.  
2) En el VPS: `git pull` en `/srv/ai/ia-empresas`.  
3) Crear/actualizar entorno virtual y dependencias.  
4) Ejecutar tests rapidos (pytest).  
5) Arrancar servicio/API (uvicorn/gunicorn) detras de Caddy/Apache.  

## Integracion con Ollama
- Endpoint: `http://127.0.0.1:11434`.
- Modelo inicial: `qwen2.5:3b-instruct`.
- No exponer Ollama a internet; solo localhost/reverse proxy interno.

## Configuracion (settings.yaml) ejemplo
```yaml
app:
  name: energyapp-llm
  env: dev

ollama:
  host: http://127.0.0.1:11434
  model: qwen2.5:3b-instruct
  temperature: 0.6
  top_p: 0.9

logging:
  level: INFO
  file: ./logs/app.log
```

## Plan funcional (API + UI con roles)
- Auth y roles: JWT (access + refresh) con roles `admin`, `user`; usuarios activos/inactivos.
- Conversaciones: historial por usuario; listar, crear, renombrar, cerrar; mensajes almacenados en DB.
- Chat: endpoint `/chat` que llama a Ollama con streaming y guarda user/assistant en DB.
- Admin: vistas de solo lectura para usuarios y conversaciones; activar/desactivar usuarios; no editar mensajes.
- Front: SPA ligera (React/Vite) con login, chat con lista de conversaciones, panel admin de lectura.
- Seguridad: CORS restringido, rate limiting en Caddy, HTTPS obligatorio, logs de acceso.

## Implementacion inicial (scaffold)
- Backend: FastAPI; endpoints `/health` y `/chat` (streaming a Ollama).
- Config: `pydantic-settings` (ENV prefix `ENERGYAPP_`), defaults seguros y SQLite local por defecto.
- DB/ORM: SQLAlchemy + modelos base (users, conversations, messages).
- Auth utils: hashing bcrypt y generacion de JWT (access + refresh).
- Cliente Ollama: httpx async streaming hacia `api/generate`.
- Scripts: `scripts/dev_api.sh` levanta uvicorn en modo desarrollo.
- Rutas cargadas en `src/main.py`:
  - `/health` (meta)
  - `/chat` (stream, guarda mensajes; crea conversacion si no hay conversation_id)
  - `/auth/*` (login/refresh/me con JWT)
  - `/conversations/*` (CRUD basico + mensajes)
  - `/admin/*` (lectura/supervision)
- UI demo: `static/index.html` (login + chat contra `/auth/login` y `/chat`).

## Rutas/API propuestas (borrador)
- Auth:
  - `POST /auth/login` -> access/refresh JWT.
  - `POST /auth/refresh` -> renueva access.
- Usuario (self):
  - `GET /me` -> perfil.
- Chat y conversaciones:
  - `POST /chat` -> stream con Ollama, requiere auth, guarda mensaje user/assistant en DB.
  - `GET /conversations` -> lista propias.
  - `POST /conversations` -> crear (opcional: titulo).
  - `GET /conversations/{id}` -> detalle + mensajes (paginados).
  - `PATCH /conversations/{id}` -> renombrar/cerrar.
  - `POST /conversations/{id}/messages` -> anadir mensaje user y disparar respuesta LLM.
- Admin (solo lectura/supervision):
  - `GET /admin/users` -> listar usuarios, filtrar por activo/rol.
  - `PATCH /admin/users/{id}` -> activar/desactivar, cambiar rol.
  - `GET /admin/conversations` -> listar conversaciones (agregar filtros).
  - `GET /admin/conversations/{id}/messages` -> ver mensajes (solo lectura).

Roles/seguridad:
- Roles: `admin`, `user`; flag `active`.
- Auth via JWT (access corto + refresh); password hash con bcrypt.
- Rate limit (proxy) y CORS restringido.

Modelo de datos (DB):
- users(id, email, password_hash, role, active, created_at).
- conversations(id, user_id, title, status, created_at, updated_at).
- messages(id, conversation_id, role, content, meta, created_at).

Notas de UI (front SPA):
- Login -> set tokens.
- Chat view -> lista conversaciones, mensajes, input; estado de streaming.
- Admin view -> tablas de usuarios (activar/desactivar), conversaciones y mensajes (solo lectura).

## Estado actual (enero 2025)
- `src/main.py`: routers auth, conversations, admin; `/chat` stream a Ollama, guarda mensajes y crea conversacion si falta `conversation_id`; streaming de texto limpio.
- `src/schemas.py`: Pydantic para login/tokens, conversaciones, mensajes, chat.
- `src/deps.py`: `get_db`; `get_current_user` y `require_admin` con validacion JWT (Bearer) y usuario activo.
- `src/routes/auth.py`: `/auth/login`, `/auth/refresh`, `/auth/me` con JWT.
- `src/routes/conversations.py`: listar/crear/obtener/actualizar conversaciones, listar mensajes (filtra por usuario).
- `src/routes/admin.py`: listar usuarios, activar/desactivar/cambiar rol; listar conversaciones y mensajes (solo lectura).
- `src/models.py`: ORM users, conversations, messages.
- `src/ollama_client.py`: cliente httpx async streaming.
- `scripts/dev_api.sh`: arranque uvicorn con venv.
- `static/index.html`: UI demo (login + chat) usando streaming de texto.

### Pendientes inmediatos
- Paginacion de mensajes y conversaciones.
- Manejo de errores/timeouts en streaming Ollama y validaciones de estados.
- Endpoints admin/usuario: añadir filtros/paginado y validaciones extra.
