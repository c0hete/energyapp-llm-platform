# Backend Context: EnergyApp LLM Platform

**Purpose:** Comprehensive reference for FastAPI backend, routes, authentication, authorization, and API endpoints.

## Backend Technology Stack

- **Framework:** FastAPI (Python 3.10+)
- **Database:** SQLAlchemy ORM with PostgreSQL (prod) / SQLite (dev)
- **Authentication:** JWT + Session Cookies + 2FA TOTP
- **Server:** Uvicorn (ASGI)
- **Logging:** Python logging with file rotation
- **Async:** Full async/await support

---

## Project Structure

```
src/
├── main.py                  # App entry point, FastAPI initialization
├── models.py               # SQLAlchemy ORM models
├── auth.py                 # Password hashing, JWT token management
├── sessions.py             # Session creation & validation
├── totp.py                 # 2FA TOTP implementation
├── deps.py                 # Dependency injection (auth, permissions)
├── ollama_client.py        # Ollama LLM client
├── routes/
│   ├── auth.py            # POST /auth/login, GET /auth/me, POST /auth/logout, etc.
│   ├── conversations.py   # POST /chat, GET /conversations, GET /messages, etc.
│   ├── admin.py           # Admin-only endpoints (users, reasign, etc.)
│   └── config.py          # System config endpoints
├── config/                 # Configuration files
│   └── settings.yaml      # Environment-based settings
└── logs/                  # Log files directory
    ├── auth.log
    ├── audit.log
    └── app.log
```

---

## Initialization & Configuration

### Main App (src/main.py)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Create FastAPI app
app = FastAPI(
    title="EnergyApp LLM API",
    description="Self-hosted LLM platform with Ollama",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://energyapp.alvaradomazzei.cl"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routes
from src.routes import auth, conversations, admin, config

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(conversations.router, tags=["conversations"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(config.router, prefix="/config", tags=["config"])

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
```

### Settings Configuration (config/settings.yaml)

```yaml
database:
  url: "postgresql+psycopg2://energyapp:password@localhost:5432/energyapp"

security:
  secret_key: "change_this_to_random_value"
  algorithm: "HS256"
  access_token_expire_minutes: 30
  refresh_token_expire_days: 7
  session_expire_days: 30

ollama:
  base_url: "http://127.0.0.1:11434"
  model: "qwen2.5:3b-instruct"
  temperature: 0.7
  top_p: 0.9

cors:
  allowed_origins:
    - "https://energyapp.alvaradomazzei.cl"

logging:
  level: "INFO"
  file: "./logs/app.log"
  max_size: "10MB"
```

---

## Authentication Flow

### 1. Login Endpoint
**POST /auth/login**

```python
# src/routes/auth.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

router = APIRouter()

@router.post("/login")
async def login(
    request: LoginRequest,  # {email, password, [totp_code]}
    db: Session = Depends(get_db)
):
    # 1. Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(401, "Invalid credentials")

    # 2. Verify password hash
    from src.auth import verify_password
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")

    # 3. Check 2FA requirement
    if user.totp_enabled and not request.totp_code:
        # Return 202 Accepted - needs 2FA
        return JSONResponse(
            status_code=202,
            content={"message": "2FA required", "code": user.id}
        )

    # 4. Verify TOTP if provided
    if user.totp_enabled and request.totp_code:
        from src.totp import verify_totp
        if not verify_totp(user.totp_secret, request.totp_code):
            raise HTTPException(401, "Invalid TOTP code")

    # 5. Create session
    from src.sessions import create_session
    session_token = await create_session(
        user_id=user.id,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )

    # 6. Return with session cookie
    response = JSONResponse({"user": user.to_dict()})
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,  # HTTPS only in prod
        samesite="Lax",
        max_age=30 * 24 * 60 * 60  # 30 days
    )
    return response
```

**Request:**
```json
{
  "email": "user@alvaradomazzei.cl",
  "password": "password123",
  "totp_code": "123456"  // Optional, only if 2FA enabled
}
```

**Response (success):**
```json
{
  "id": 1,
  "email": "user@alvaradomazzei.cl",
  "role": "trabajador",
  "full_name": "John Doe"
}
// Plus: Set-Cookie: session_token=...
```

**Response (2FA required):**
```json
{
  "status_code": 202,
  "message": "2FA required",
  "code": 1
}
```

### 2. Auth Check Endpoint
**GET /auth/me**

```python
@router.get("/me")
async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
):
    # 1. Extract session token from cookie
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(401, "Not authenticated")

    # 2. Validate session token
    from src.sessions import validate_session
    user_id = await validate_session(token, db)
    if not user_id:
        raise HTTPException(401, "Invalid or expired session")

    # 3. Get user from DB
    user = db.query(User).get(user_id)
    if not user or not user.active:
        raise HTTPException(401, "User not found or inactive")

    return user.to_dict()
```

**Response:**
```json
{
  "id": 1,
  "email": "user@alvaradomazzei.cl",
  "role": "trabajador",
  "full_name": "John Doe",
  "totp_enabled": false
}
```

### 3. Logout Endpoint
**POST /auth/logout**

```python
@router.post("/logout")
async def logout(
    request: Request,
    db: Session = Depends(get_db)
):
    token = request.cookies.get("session_token")
    if token:
        # Delete session from DB
        session = db.query(Session).filter(Session.session_token == token).first()
        if session:
            db.delete(session)
            db.commit()

    # Clear cookie
    response = JSONResponse({"message": "Logged out"})
    response.delete_cookie("session_token")
    return response
```

---

## Authorization & Permissions

### Dependency Injection (deps.py)

```python
# src/deps.py
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """Validate session and return current user"""
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(401, "Not authenticated")

    session = db.query(Session).filter(
        Session.session_token == token,
        Session.expires_at > datetime.utcnow()
    ).first()

    if not session:
        raise HTTPException(401, "Invalid or expired session")

    user = db.query(User).get(session.user_id)
    if not user or not user.active:
        raise HTTPException(401, "User not found")

    return user

async def require_admin(
    user: User = Depends(get_current_user)
) -> User:
    """Ensure user has admin role"""
    if user.role != "admin":
        raise HTTPException(403, "Admin access required")
    return user

async def require_supervisor(
    user: User = Depends(get_current_user)
) -> User:
    """Ensure user has admin or supervisor role"""
    if user.role not in ["admin", "supervisor"]:
        raise HTTPException(403, "Supervisor access required")
    return user
```

### Usage in Routes

```python
@router.get("/admin/users")
async def list_users(
    user: User = Depends(require_admin),  # Only admins
    db: Session = Depends(get_db)
):
    users = db.query(User).filter(User.active == True).all()
    return [u.to_dict() for u in users]

@router.get("/conversations")
async def get_conversations(
    user: User = Depends(get_current_user),  # Any authenticated user
    db: Session = Depends(get_db)
):
    # Regular users see only their own; admins see all
    if user.role == "admin":
        convs = db.query(Conversation).all()
    else:
        convs = db.query(Conversation).filter(
            Conversation.user_id == user.id
        ).all()

    return convs
```

---

## Core API Endpoints

### Chat Endpoint
**POST /chat**

```python
# src/routes/conversations.py
@router.post("/chat")
async def chat(
    request: ChatRequest,  # {conversation_id, message, system_prompt_id}
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Validate ownership
    conversation = db.query(Conversation).get(request.conversation_id)
    if not conversation:
        raise HTTPException(404, "Conversation not found")

    if conversation.user_id != user.id and user.role != "admin":
        raise HTTPException(403, "Not your conversation")

    # 2. Save user message
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message
    )
    db.add(user_message)
    db.commit()

    # 3. Get system prompt
    system_prompt = db.query(SystemPrompt).get(
        request.system_prompt_id
    ) or db.query(SystemPrompt).filter(
        SystemPrompt.is_default == True
    ).first()

    # 4. Build message history
    messages = [
        {"role": "system", "content": system_prompt.content},
        *build_conversation_context(conversation, db)
    ]

    # 5. Stream from Ollama
    async def generate():
        full_response = ""
        async for token in ollama_client.stream_chat(
            model="qwen2.5:3b-instruct",
            messages=messages
        ):
            full_response += token
            yield f"data: {json.dumps({'token': token})}\n\n"

        # 6. Save assistant response
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=full_response
        )
        db.add(assistant_message)
        conversation.updated_at = datetime.utcnow()
        db.commit()

    return StreamingResponse(generate(), media_type="text/event-stream")
```

### Conversations Endpoint
**GET /conversations**

```python
@router.get("/conversations")
async def get_conversations(
    limit: int = 50,
    offset: int = 0,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Conversation)

    # Filter by role
    if user.role == "trabajador":
        query = query.filter(Conversation.user_id == user.id)
    elif user.role == "supervisor":
        # Supervisor sees own + subordinates' conversations
        supervisor_id = user.id
        subordinate_ids = get_subordinates_for_supervisor(supervisor_id, db)
        query = query.filter(
            Conversation.user_id.in_([supervisor_id, *subordinate_ids])
        )
    # Admin sees all (no filter)

    total = query.count()
    conversations = query.order_by(
        Conversation.updated_at.desc()
    ).offset(offset).limit(limit).all()

    return {
        "total": total,
        "data": [c.to_dict() for c in conversations]
    }
```

### Admin Endpoints

**GET /admin/users**
```python
@router.get("/users")
async def list_users(
    user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    users = db.query(User).filter(User.active == True).all()
    return [u.to_dict() for u in users]
```

**GET /admin/conversations/{user_id}**
```python
@router.get("/conversations/{user_id}")
async def get_user_conversations(
    user_id: int,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    conversations = db.query(Conversation).filter(
        Conversation.user_id == user_id
    ).order_by(Conversation.updated_at.desc()).all()

    return [c.to_dict() for c in conversations]
```

**PATCH /admin/conversations/{conversation_id}/reassign**
```python
@router.patch("/conversations/{conversation_id}/reassign")
async def reassign_conversation(
    conversation_id: int,
    request: ReassignRequest,  # {target_user_id}
    user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    conversation = db.query(Conversation).get(conversation_id)
    if not conversation:
        raise HTTPException(404, "Conversation not found")

    # Verify target user exists and is active
    target_user = db.query(User).get(request.target_user_id)
    if not target_user or not target_user.active:
        raise HTTPException(400, "Target user not found")

    # Reassign
    conversation.user_id = request.target_user_id
    conversation.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Conversation reassigned", "data": conversation.to_dict()}
```

---

## Security Practices

### Password Hashing
```python
# src/auth.py
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)
```

### Session Token Generation
```python
# src/sessions.py
import secrets
from datetime import datetime, timedelta

async def create_session(
    user_id: int,
    ip_address: str,
    user_agent: str,
    db: Session
) -> str:
    token = secrets.token_urlsafe(32)  # 256 bits of entropy
    expires_at = datetime.utcnow() + timedelta(days=30)

    session = Session(
        user_id=user_id,
        session_token=token,
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=expires_at
    )
    db.add(session)
    db.commit()
    return token
```

### CORS & Headers
```python
# Only allow requests from trusted origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://energyapp.alvaradomazzei.cl"],
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type"],
    allow_credentials=True  # Allow cookies
)

# Secure cookie settings
response.set_cookie(
    "session_token",
    value=token,
    httponly=True,      # No JavaScript access
    secure=True,        # HTTPS only
    samesite="Lax"      # CSRF protection
)
```

---

## Error Handling

### Standard Error Responses

```python
# 400 Bad Request
raise HTTPException(400, detail="Invalid input format")

# 401 Unauthorized
raise HTTPException(401, detail="Not authenticated")

# 403 Forbidden
raise HTTPException(403, detail="Insufficient permissions")

# 404 Not Found
raise HTTPException(404, detail="Resource not found")

# 409 Conflict
raise HTTPException(409, detail="Resource already exists")

# 429 Too Many Requests
from fastapi_limiter import FastAPILimiter
@limiter.limit("5/minute")

# 500 Internal Server Error
logger.error(f"Unexpected error: {str(e)}", exc_info=True)
raise HTTPException(500, detail="Internal server error")
```

---

## Logging

### Setup
```python
# src/main.py
import logging
from logging.handlers import RotatingFileHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            'logs/app.log',
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
    ]
)

logger = logging.getLogger(__name__)
```

### Usage
```python
logger.info(f"User {user.email} logged in from {ip_address}")
logger.warning(f"Failed login attempt for {email}")
logger.error(f"Chat error for conversation {conv_id}", exc_info=True)
```

---

## Development vs Production

### Development
```bash
# .env.dev
ENERGYAPP_DB_URL=sqlite:///./test.db
ENERGYAPP_SECRET_KEY=dev_key_not_secure
ENERGYAPP_DEBUG=true

# Run with reload
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Production
```bash
# .env.prod
ENERGYAPP_DB_URL=postgresql+psycopg2://...@/energyapp
ENERGYAPP_SECRET_KEY=<secure_random_key>
ENERGYAPP_DEBUG=false
ENERGYAPP_CORS_ORIGINS=["https://energyapp.alvaradomazzei.cl"]

# Run via systemd (no reload)
uvicorn src.main:app --host 127.0.0.1 --port 8001 --workers 4
```

---

## Related Files & References

- `src/main.py` → FastAPI initialization
- `src/models.py` → SQLAlchemy ORM models
- `src/routes/auth.py` → Authentication endpoints
- `src/routes/conversations.py` → Chat & conversation endpoints
- `src/routes/admin.py` → Admin management endpoints
- `src/deps.py` → Dependency injection & authorization
- `src/ollama_client.py` → Ollama integration
- `src/auth.py`, `src/sessions.py`, `src/totp.py` → Security utilities
- `docs/CONTEXT_AI_ENGINE.md` → AI inference details
- `docs/CONTEXT_DATABASE.md` → Database schema & models
