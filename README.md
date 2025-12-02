# EnergyApp LLM Platform

Plataforma de IA autohospedada para EnergyApp con FastAPI + Ollama (Qwen 2.5:3B). Pensada para operar en VPS propio con seguridad básica y despliegue automatizado.

## Características
- Inferencia local (Ollama en `127.0.0.1:11434`), sin envío de datos externos.
- **Autenticación Dual** (PHASE 0):
  - JWT para API (access/refresh tokens)
  - Sesiones basadas en cookies con persistencia en BD, auditoría de IP/User-Agent
  - Soporte 2FA TOTP opcional
- Historias de conversación persistidas (users, conversations, messages, sessions).
- **Dos interfaces UI disponibles**:
  - **SPA** (original): servida desde `/static/index.html` con login, chat streaming, pestañas Chat/Config/Admin.
  - **SSR** (PHASE 1): Jinja2 templates - `/login`, `/dashboard`, `/config`, `/admin`, `/register`.
- Panel Admin: listado de usuarios con última actividad, explorador de conversaciones/mensajes, reasignación de conversaciones.
- Config de modelo desde la UI (host/model/temperature/top_p/max_tokens) y ping a Ollama.
- **Logging especializado**: auth.log, audit.log, app.log con rotación automática (PHASE 0).
- CORS restringido a dominio público (`https://energyapp.alvaradomazzei.cl`).
- Servicio uvicorn bajo systemd; reverse proxy Caddy con TLS.

## Roles y visibilidad
- **Admin**: pestaña Admin visible; ve todos los usuarios/conversaciones/mensajes; puede reasignar cualquier conversación.
- **Supervisor**: pestaña Admin visible; ve solo trabajadores y a sí mismo; puede ver/reasignar conversaciones de trabajadores y propias.
- **Trabajador**: sin pestaña Admin; solo ve sus propias conversaciones.
- Cambio de contraseña: solo permitido para cuentas `@inacapmail.cl`.
- 2FA: si `totp_enabled` está activo para la cuenta, el login pide TOTP; activación self-service disponible para cuentas `@inacapmail.cl` vía `/auth/setup-2fa`.

## Dos Interfaces UI (SPA y SSR)

### SPA Original (Deprecated en futuro)
- **URL**: `/static/index.html`
- **Tecnología**: HTML/JS/CSS puro con fetch API
- **Autenticación**: JWT tokens (access + refresh)
- **Estado**: Mantenido para compatibilidad retroactiva

### SSR con Jinja2 (PHASE 1 - Recomendado)
- **URLs**: `/login`, `/dashboard`, `/config`, `/admin`, `/register`
- **Tecnología**: FastAPI + Jinja2 templates + JavaScript vanilla
- **Autenticación**: Session-based (cookies + BD)
- **Ventajas**:
  - Mejor SEO (HTML completo del servidor)
  - Menor complejidad en cliente
  - Integración más directa con sesiones
  - Mejor experiencia de usuario inicial

**Recomendación**: Usar la interfaz SSR (nuevas rutas) en lugar de la SPA. La SPA será deprecada en futuras versiones.

## Cuentas demo (para pruebas rápidas)
- administrador@alvaradomazzei.cl / **admin123** (rol: admin)
- trabajador@alvaradomazzei.cl / **worker123** (rol: trabajador)
- supervisor@alvaradomazzei.cl / **supervisor123** (rol: supervisor)

**Nota importante**: Estas cuentas no pueden cambiar contraseña (solo emails `@inacapmail.cl` pueden). Los accesos rápidos en el login rellenan automáticamente estas credenciales.

## Modelo actual
- **Modelo**: Qwen 2.5:3B Instruct (GGUF Q4)
- **Consumo esperado**: ~2–3 GB RAM durante inferencia

## Estructura
- `src/`: API FastAPI con rutas modulares:
  - `routes/auth.py`: Autenticación (login, register, 2FA, logout)
  - `routes/conversations.py`: Gestión de conversaciones y mensajes
  - `routes/admin.py`: Panel de administración
  - `routes/config.py`: Configuración del modelo Ollama
  - `routes/ssr.py`: Rutas de Server-Side Rendering con Jinja2 (PHASE 1)
  - `models.py`: SQLAlchemy models (User, Conversation, Message, Session)
  - `deps.py`: Dependencias compartidas (autenticación, BD)
  - `ollama_client.py`: Cliente para inferencia Ollama
  - `config.py`: Configuración y Settings
- `templates/`: Plantillas Jinja2 (PHASE 1):
  - `base.html`: Plantilla base con estilos compartidos
  - `login.html`: Página de login con soporte 2FA
  - `dashboard.html`: Interfaz principal de chat
  - `register.html`: Formulario de registro
  - `config.html`: Página de configuración
  - `admin.html`: Panel de administración
- `static/`: UI SPA original (HTML/JS/CSS, deprecado en futuro)
- `config/`: Archivo de configuración base (`settings.yaml`)
- `scripts/`: Utilidades (dev_api.sh, seed_admin.py, deploy.sh)
- `docs/`: Documentación de arquitectura y operación
- `data/`, `logs/`: Carpetas locales (se crean al iniciar)

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

**Interfaz SSR (Recomendado - PHASE 1)**:
- Login: http://localhost:8000/login
- Dashboard: http://localhost:8000/dashboard (después de autenticarse)
- Config: http://localhost:8000/config
- Admin: http://localhost:8000/admin

**Interfaz SPA Original (Deprecated)**:
- UI: http://localhost:8000/static/index.html

**Health Check**:
- http://localhost:8000/health

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

## Arquitectura (PHASE 0 + PHASE 1)

### Autenticación Dual

**Sesión Basada en Cookies (para SSR)**:
1. POST `/auth/login` → Valida credenciales, crea sesión en BD
2. Respuesta incluye cookie `session_id` (HTTP-only, Secure)
3. Sesiones persistidas en tabla `sessions` con auditoría de IP/User-Agent
4. Cookie se envía automáticamente en requests posteriores
5. `get_current_user_from_session` extrae usuario desde DB

**JWT Tokens (para SPA/API)**:
1. POST `/auth/login` → Devuelve `access_token` + `refresh_token`
2. Cliente almacena tokens en memoria
3. Headers: `Authorization: Bearer <access_token>`
4. `/auth/refresh` renueva tokens cuando expiran

**2FA TOTP (Opcional)**:
- Si habilitado: `/auth/login` responde con `needs_2fa=True` y `session_token`
- Usuario envía código de 6 dígitos a `/auth/verify-2fa`
- Recién entonces se devuelven tokens/sesión

### Flujo de Renderizado

**SSR (Server-Side Rendering)**:
```
Usuario → GET /login → FastAPI + Jinja2 → HTML completo → Navegador
          (sin JS necesario para login)
```

**SPA (Single Page Application)**:
```
Usuario → GET /static/index.html → HTML vacío + JS →
          (JS carga datos via API y renderiza)
```

### Modelo de Datos

```
User
├── id (PK)
├── email (unique)
├── password_hash
├── role (admin|supervisor|trabajador)
├── totp_enabled / totp_secret
└── created_at / updated_at

Session (PHASE 0)
├── id (PK)
├── user_id (FK)
├── session_id (unique)
├── ip_address (auditoría)
├── user_agent (auditoría)
├── created_at / expires_at

Conversation
├── id (PK)
├── user_id (FK)
├── title
├── status
└── created_at

Message
├── id (PK)
├── conversation_id (FK)
├── role (user|assistant)
├── content
└── created_at
```

### Logging Especializado (PHASE 0)

- **auth.log**: Intentos de login, logout, cambios de contraseña, 2FA
- **audit.log**: Acciones administrativas, reasignación de conversaciones
- **app.log**: Errores generales, eventos del sistema
- Rotación automática por tamaño (10 MB por defecto)

## 2FA (TOTP)
- Si el usuario tiene 2FA habilitado (`totp_enabled=True` y `totp_secret`), el login responde `needs_2fa=True` y entrega `session_token`; el código TOTP se valida en `/auth/verify-2fa` y recién ahí se devuelven tokens.
- Endpoint de soporte/demo para QR de cuentas demo: `/auth/demo-qr-codes`.
- En la UI, al requerir 2FA se muestra el QR y el campo de código de 6 dígitos.
- Activación self-service: `/auth/setup-2fa` (solo emails `@inacapmail.cl`).

## Registro con dominio permitido
- `/auth/register` admite nuevos usuarios solo con correos `@alvaradomazzei.cl` o `@inacapmail.cl`.

## Licencia
MIT. Autor: Jose Alvarado Mazzei, 2025.
