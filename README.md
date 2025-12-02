# EnergyApp LLM Platform

Plataforma de IA autohospedada con FastAPI + Ollama (Qwen 2.5:3B). Pensada para operar en VPS propio con seguridad basica y despliegue simple.

## Caracteristicas principales
- **Inferencia local:** Ollama + Qwen 2.5:3B (sin envio de datos a terceros).
- **Frontend moderno:** Next.js 14 + React 18 + TypeScript + Tailwind + React Query.
- **Backend robusto:** FastAPI con auth dual (JWT + Sesiones + 2FA TOTP).
- **Autenticacion:**
  - JWT para API (access/refresh tokens).
  - Sesiones por cookies persistidas en BD (auditoría de IP/User-Agent).
  - 2FA TOTP configurable.
  - Middleware de Next.js para protección de rutas.
- **Historico completo:** conversaciones, mensajes, sesiones persistidas en PostgreSQL.
- **Admin panel interactivo:** 3 columnas (usuarios | conversaciones | mensajes) con reasignación.
- **Dashboard con chat streaming:** Sidebar fijo, chat responsive, indicador "escribiendo".
- **Roles y permisos:** admin, supervisor, trabajador con control granular.
- **Logging:** auth.log, audit.log, app.log con rotación.
- **Infraestructura:** 2 servicios systemd (FastAPI + Next.js), proxy Caddy con TLS.

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
```
energyapp-llm-platform/
├── frontend/              ← Next.js 14 (React + TypeScript + Tailwind)
│   ├── app/               ← App Router (login, dashboard, admin, settings)
│   ├── components/        ← React components reutilizables
│   ├── hooks/             ← useAuthCheck, custom hooks
│   ├── lib/               ← api.ts (cliente HTTP)
│   ├── providers/         ← QueryProvider (React Query)
│   ├── store/             ← useAuthStore (Zustand)
│   ├── middleware.ts      ← Route protection
│   └── package.json
│
├── src/                   ← FastAPI backend
│   ├── main.py            ← App entry point
│   ├── routes/            ← auth.py, conversations.py, admin.py, config.py
│   ├── models.py          ← SQLAlchemy (users, conversations, messages, sessions)
│   ├── deps.py            ← Dependency injection (auth, permissions)
│   ├── sessions.py        ← Session management
│   ├── auth.py            ← Password hashing, JWT tokens
│   ├── totp.py            ← 2FA TOTP
│   └── ollama_client.py   ← Ollama integration
│
├── config/                ← settings.yaml (configurable)
├── scripts/               ← deploy.sh, seed_admin.py, etc.
├── docs/                  ← Arquitectura.md, deployment docs
├── .venv/                 ← Python virtual environment
├── requirements.txt       ← Python dependencies
├── package.json           ← Node.js dependencies (si no está en /frontend)
└── README.md              ← Este archivo
```

## Requisitos

### Backend
- Python 3.10+ (local usamos 3.13.8)
- PostgreSQL 16 (prod) o SQLite (dev)
- Ollama en `localhost:11434` con `qwen2.5:3b-instruct`

### Frontend (FASE 0+)
- Node.js 18+ (usamos 20 o 22)
- npm 10+ o yarn

### VPS (Producción)
- Ubuntu 24.04 LTS
- CPU: 6 vCPU (mínimo 4)
- RAM: 12 GB (mínimo 8)
- Storage: 100 GB SSD (mínimo 50 GB)

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

### 1. Backend (FastAPI)
```bash
python -m venv .venv
.\.venv\Scripts\activate           # Windows (en Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
# Accedible en http://localhost:8000/docs
```

### 2. Frontend (Next.js) - Terminal separada
```bash
cd frontend
npm install
npm run dev
# Accedible en http://localhost:3000
# Auto-proxy a http://localhost:8000/api (via next.config.js)
```

### Acceso de prueba
- Email: `administrador@alvaradomazzei.cl`
- Password: `admin123`

**Nota:** En dev, ambos servicios corren en localhost. En prod, Caddy proxea Next.js (puerto 3000) + FastAPI (puerto 8001).

## Rutas principales

### Frontend (Next.js)
- `GET /login` → Login page (SSR)
- `GET /register` → Register page (SSR)
- `GET /dashboard` → Chat dashboard (protegido)
- `GET /admin` → Admin panel (solo admin)
- `GET /settings` → Config page (protegido)

### API (FastAPI)
- `POST /api/auth/login` → Authenticate, set session cookie
- `GET /api/auth/me` → Validate session, return user
- `POST /api/auth/register` → Create account
- `POST /api/chat` → Chat with streaming
- `GET /api/conversations` → List user's conversations
- `GET /api/admin/*` → Admin endpoints (requieren admin role)
- `GET /api/health` → API health status

### Legado (deprecado)
- `GET /static/index.html` → SPA viejo (será eliminado en FASE 3)

## Despliegue en VPS

### Proceso de actualización
```bash
cd /root/energyapp-llm-platform

# 1. Backend (FastAPI)
source .venv/bin/activate
git pull origin main
pip install -r requirements.txt

# 2. Frontend (Next.js)
cd frontend
git checkout .
npm install
npm run build
cd ..

# 3. Reiniciar servicios
sudo systemctl restart energyapp-api
sudo systemctl restart energyapp-web

# 4. Logs
sudo journalctl -u energyapp-api -f
sudo journalctl -u energyapp-web -f
```

### Servicios systemd
- `energyapp-api.service` → FastAPI en puerto 8001
- `energyapp-web.service` → Next.js en puerto 3000

### Reverse proxy (Caddy)
- `https://energyapp.alvaradomazzei.cl/` → Next.js frontend
- `https://energyapp.alvaradomazzei.cl/api/*` → FastAPI backend
