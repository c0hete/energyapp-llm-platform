# Arquitectura y despliegue

## Vision general
- Plataforma LLM privada con inferencia local via Ollama (Qwen 2.5:3B).
- **Backend:** FastAPI modular (auth, chat, conversaciones, admin, config).
- **Frontend:** Next.js 14 (React 18 + TypeScript + Tailwind + React Query + Zustand).
- **Auth:** Dual (JWT + Sesiones con cookies + 2FA TOTP).
- **Proxy:** Caddy con TLS; uvicorn + Node.js bajo systemd.
- **Entorno prod:** Ubuntu 24.04, 6 vCPU, ~12 GB RAM, 100 GB SSD.

## Master Context Documents (Documentación Detallada)

Esta documentación ha sido reorganizada en 5 documentos especializados para mejor referencia:

### 1. [CONTEXT_DATABASE.md](./CONTEXT_DATABASE.md) - Base de Datos
- **Temas:** Esquema SQL, modelos SQLAlchemy, relaciones, integridad referencial
- **Tablas:** users, conversations, messages, sessions, system_prompts
- **Índices:** Optimización de consultas y performance
- **Seguridad:** Hashing de contraseñas, aislamiento de datos, validaciones
- **Uso:** Referencia para cambios en BD, migraciones, consultas complejas

### 2. [CONTEXT_AI_ENGINE.md](./CONTEXT_AI_ENGINE.md) - Motor de IA
- **Temas:** Ollama, modelo Qwen 2.5:3B, streaming de inferencia
- **Flujo:** Chat API completo desde frontend a LLM y respuesta
- **System Prompts:** Gestión y selección automática de prompts por defecto
- **Performance:** Límites de tokens, throughput, optimización
- **Testing:** Pruebas manuales del motor de IA
- **Uso:** Integración Ollama, debugging de inferencia, cambios de modelo

### 3. [CONTEXT_FRONTEND.md](./CONTEXT_FRONTEND.md) - Frontend (Next.js)
- **Temas:** Arquitectura Next.js 14, componentes React, state management
- **Componentes:** ChatWindow, ConversationsList, AdminPanel, SystemPromptsManager
- **Auth:** Flujo de login, route protection, middleware
- **State:** Zustand (auth), React Query (API data)
- **Build:** Turbopack, chunks, optimización
- **Uso:** Desarrollo de componentes, debugging de build, problemas de chunks

### 4. [CONTEXT_BACKEND.md](./CONTEXT_BACKEND.md) - Backend (FastAPI)
- **Temas:** Rutas API, autenticación, autorización, manejo de errores
- **Auth:** Login, JWT, sesiones, 2FA TOTP, password hashing
- **Permisos:** RBAC (admin, supervisor, trabajador)
- **Endpoints:** Especificación completa de API REST
- **Seguridad:** CORS, cookies secure, validaciones, logging
- **Uso:** Desarrollo de nuevas rutas, debugging de auth, cambios en permisos

### 5. [CONTEXT_INFRASTRUCTURE.md](./CONTEXT_INFRASTRUCTURE.md) - Infraestructura
- **Temas:** Deployment, systemd services, Caddy, VPS management
- **Servicios:** energyapp-api, energyapp-web, ollama
- **Reverse Proxy:** Configuración Caddy, SSL/TLS, rewrites
- **Deploy:** Proceso paso a paso, scripts de automatización
- **Monitoreo:** Health checks, logs, troubleshooting
- **Uso:** Deployment, gestión de VPS, troubleshooting de servicios

## Componentes
- Ollama: `127.0.0.1:11434` con `qwen2.5:3b-instruct` (GGUF Q4).
- App LLM: `/root/energyapp-llm-platform` (FastAPI + UI).
- DB: PostgreSQL 16 (`energyapp`), tablas `users`, `conversations`, `messages`, `sessions`.
- Proxy: Caddy expone `https://[YOUR_DOMAIN]` -> `127.0.0.1:8001`.
- Seguridad base: UFW (80/443), CORS restringido, HTTPS, Fail2ban.
- UX: favicon, bienvenida, streaming con estado "generando", sidebar fijo en dashboard, chat con scroll interno y burbuja "escribiendo", accesos rapidos (admin/trabajador/supervisor), logo en header.
- 2FA TOTP en login si el usuario tiene `totp_enabled`; self-service 2FA para correos `@inacapmail.cl`.

## Cuentas demo
- administrador@alvaradomazzei.cl / admin123 (rol: admin)
- trabajador@alvaradomazzei.cl / worker123 (rol: trabajador)
- supervisor@alvaradomazzei.cl / supervisor123 (rol: supervisor)

Accesos rapidos en el login rellenan estas credenciales.

## Estructura de repo
```
energyapp-llm-platform/
├── frontend/                    ← Next.js 14 (NUEVO)
│   ├── app/
│   │   ├── (auth)/             ← Login, Register
│   │   ├── (dashboard)/        ← Dashboard, Admin, Settings
│   │   ├── layout.tsx
│   │   └── middleware.ts       ← Route protection
│   ├── components/             ← React components
│   ├── hooks/                  ← useAuthCheck, custom hooks
│   ├── lib/                    ← api.ts (cliente HTTP)
│   ├── providers/              ← QueryProvider (React Query)
│   ├── store/                  ← useAuthStore (Zustand)
│   ├── package.json
│   └── next.config.js
│
├── src/                        ← FastAPI backend (sin cambios)
│   ├── main.py
│   ├── models.py
│   ├── routes/
│   │   ├── auth.py            ← Nuevo: GET /auth/me
│   │   ├── conversations.py
│   │   ├── admin.py
│   │   └── config.py
│   ├── auth.py, sessions.py, totp.py
│   └── deps.py
│
├── config/                     ← settings.yaml, .env
├── scripts/                    ← deploy.sh (actualizado para 2 servicios)
├── docs/                       ← Documentación
├── .venv/                      ← Python venv (backend)
└── README.md
```

**Separación clara:**
- `/frontend` → Node.js (Next.js, npm)
- `/src` → Python (FastAPI, pip)
- Ambos en mismo repo para deploy unificado

**Restricciones:**
- Registro: `/auth/register` solo `@alvaradomazzei.cl` y `@inacapmail.cl`
- Cambio de contraseña: solo `@inacapmail.cl`

## Roles (backend y UI)
- Admin: ve todos los usuarios/conversaciones/mensajes; reasigna cualquiera; pestaña Admin visible.
- Supervisor: pestaña Admin visible; solo ve trabajadores y a si mismo; conversaciones/mensajes solo de trabajadores y propias; reasigna dentro de ese scope.
- Trabajador: sin pestaña Admin; solo sus conversaciones.

## Frontend Next.js (FASE 0-3)

### Tecnologías
- **React 18** con TypeScript
- **Tailwind CSS** para estilos
- **React Query** para data fetching y cache
- **Zustand** para state management (auth)
- **Next.js Middleware** para route protection

### Flujo de autenticación
1. Usuario entra a `/login` (no autenticado → permitido)
2. POST `/api/auth/login` → crea `session_token` cookie
3. GET `/api/auth/me` → valida sesión
4. `useAuthStore` (Zustand) guarda usuario en global state
5. Redirige a `/dashboard`
6. Middleware protege `/dashboard` y `/admin` (requieren sesión)

### Componentes principales
- **Login Page** (`app/(auth)/login/page.tsx`) - Formulario de login con validación
- **Dashboard** (`app/(dashboard)/dashboard/page.tsx`) - Chat + sidebar de conversaciones
- **Admin Panel** (`app/(dashboard)/admin/page.tsx`) - 3-columnas: usuarios | conversaciones | mensajes
- **Chat Component** (FASE 2) - Streaming en tiempo real con React hooks
- **Admin Panel Component** (FASE 3) - Interactividad con React Query

### UX/Layout
- Sidebar fijo a la izquierda (conversaciones, usuarios)
- Chat/content ocupa el resto
- Scroll local (no en página)
- Indicadores de "escribiendo" en tiempo real
- Responsive (mobile-friendly con Tailwind)

## Despliegue (prod - FASE 0+)

### Servicios systemd
```bash
# 1. FastAPI backend (puerto 8001)
energyapp-api.service
  ExecStart=/root/energyapp-llm-platform/.venv/bin/uvicorn src.main:app --host 127.0.0.1 --port 8001

# 2. Next.js frontend (puerto 3000)
energyapp-web.service
  ExecStart=/usr/bin/npm run start
  WorkingDirectory=/root/energyapp-llm-platform/frontend
```

### Caddy config
```
[YOUR_DOMAIN] {
    encode gzip

    # Proxy a Next.js (frontend)
    reverse_proxy 127.0.0.1:3000

    # Proxy a FastAPI para /api/*
    handle /api/* {
        uri strip_prefix /api
        reverse_proxy 127.0.0.1:8001
    }

    log {
        output file /var/log/caddy/energyapp-access.log {
            roll_size 5mb
            roll_keep 14
            roll_keep_for 336h
        }
    }
}
```

### Rutas en Next.js
- GET `/login` → page (renderizado)
- GET `/register` → page (renderizado)
- GET `/dashboard` → page (renderizado, requiere sesión)
- GET `/admin` → page (renderizado, solo admin)
- GET `/` → redirect a `/login` o `/dashboard`

### Rutas en FastAPI (API)
- `POST /api/auth/login` → authenticate, set `session_token` cookie
- `GET /api/auth/me` → validate session, return user
- `POST /api/chat` → streaming response
- `GET /api/conversations` → list user's conversations
- `GET /api/admin/*` → admin endpoints (requieren sesión + admin role)

### Health Check
- `GET /api/health` → FastAPI health status
- `GET /` → Next.js redirect

### CORS
- Permitido: `https://[YOUR_DOMAIN]`
- Cookies con `SameSite=Lax`, `HttpOnly`, `Secure`

## Configuracion (ENV)
```
ENERGYAPP_DB_URL=postgresql+psycopg2://energyapp:[DB_PASSWORD]@localhost:5432/energyapp
ENERGYAPP_SECRET_KEY=[SECRET_KEY_CHANGE_THIS]
ENERGYAPP_ALLOWED_ORIGINS=["https://[YOUR_DOMAIN]"]
ENERGYAPP_LOG_TO_FILE=true
ENERGYAPP_LOG_FILE=./logs/app.log
```

## Flujo de actualización (deploy)

### En VPS (después de git push)
```bash
cd /root/energyapp-llm-platform

# 1. Backend (FastAPI)
source .venv/bin/activate
git pull origin main
pip install -r requirements.txt

# 2. Frontend (Next.js)
cd frontend
git checkout .  # resincronizar
npm install
npm run build
cd ..

# 3. Reiniciar servicios
sudo systemctl restart energyapp-api
sudo systemctl restart energyapp-web

# 4. Verificar
sudo systemctl status energyapp-api energyapp-web
sudo journalctl -u energyapp-api -f
sudo journalctl -u energyapp-web -f
```

### Health checks post-deploy
```bash
# Health API
curl http://127.0.0.1:8001/health

# Frontend
curl -I http://127.0.0.1:3000/login

# Full stack (via Caddy)
curl -I https://[YOUR_DOMAIN]/login
```

## Integracion con Ollama
- Cliente en `src/ollama_client.py`.
- Configurable en `config/settings.yaml` o variables de entorno.
- Ping desde UI de config (boton "Probar conexion").
