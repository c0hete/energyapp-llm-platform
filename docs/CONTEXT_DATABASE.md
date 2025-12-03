# Database Context: EnergyApp LLM Platform

**Purpose:** Comprehensive reference for database schema, models, and relationships in the EnergyApp LLM Platform.

## Database Overview

- **Production:** PostgreSQL 16 (`energyapp` database)
- **Development:** SQLite (local development)
- **Connection:** `postgresql+psycopg2://energyapp:password@localhost:5432/energyapp`
- **ORM:** SQLAlchemy 2.0+
- **Migrations:** Alembic (if configured) or manual schema management

## Core Tables and Models

### 1. **users** Table
Primary table for user accounts and authentication.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',  -- admin, supervisor, trabajador, user
    active BOOLEAN DEFAULT TRUE,
    totp_secret VARCHAR(32) NULL,
    totp_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Fields:**
- `email`: Unique identifier, used for login
- `password_hash`: Bcrypt-hashed password (never store plaintext)
- `role`: RBAC - determines API access and UI visibility
  - `admin`: Full access, can manage users, reasign conversations
  - `supervisor`: Sees subordinates, can reasign conversations within scope
  - `trabajador`: Only own conversations
  - `user`: Basic user (legacy role)
- `totp_enabled`: Flag for 2FA TOTP activation
- `totp_secret`: Base32-encoded secret for TOTP (used with authenticator apps)

**Constraints:**
- Registration only for `@alvaradomazzei.cl` and `@inacapmail.cl` domains
- Password changes only for `@inacapmail.cl` domain
- `@inacapmail.cl` users can self-enable 2FA

---

### 2. **conversations** Table
Stores chat conversations, organized by user.

```sql
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    description TEXT,
    system_prompt_id INTEGER REFERENCES system_prompts(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_pinned BOOLEAN DEFAULT FALSE
);
```

**Fields:**
- `user_id`: Owner of the conversation
- `title`: Auto-generated or user-defined conversation title
- `system_prompt_id`: Reference to selected system prompt for this conversation
- `is_pinned`: UI flag to pin conversation in sidebar
- `updated_at`: Auto-refreshed when new messages arrive

**Relationships:**
- One user → Many conversations (1:N)
- One system_prompt → Many conversations (1:N)

**Admin Features:**
- Conversations can be reassigned to other users via `PATCH /api/admin/conversations/{id}/reassign`
- Supervisors see only conversations of subordinates
- Admins see all conversations

---

### 3. **messages** Table
Stores individual messages within conversations.

```sql
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Fields:**
- `role`: Either `user` (human input) or `assistant` (LLM response)
- `content`: Full message text (can be long due to streaming)
- `created_at`: Message timestamp (used for sorting)

**Relationships:**
- One conversation → Many messages (1:N)
- Cascade delete: Deleting conversation deletes all messages

**Chat Flow:**
1. User sends message → POST `/api/chat` with `conversation_id`
2. Create new message with `role='user'`
3. Call Ollama API for inference
4. Create message with `role='assistant'` (streamed)
5. Return streaming response to frontend

---

### 4. **sessions** Table
Persistent session storage for security auditing.

```sql
CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    ip_address VARCHAR(45),  -- IPv4 or IPv6
    user_agent VARCHAR(500),
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP
);
```

**Fields:**
- `session_token`: Secure token stored in `session_token` cookie
- `ip_address`: IP of login for audit trail
- `user_agent`: Browser/app identifier
- `expires_at`: Session TTL (typically 7-30 days)
- `last_activity`: Track session usage

**Session Flow:**
1. User POSTs `/api/auth/login` with email + password
2. Backend validates credentials
3. Create `sessions` record with random token
4. Set `session_token` cookie (HttpOnly, Secure, SameSite=Lax)
5. Frontend uses cookie automatically for authenticated requests

**Logout:**
1. POST `/api/auth/logout`
2. Delete session record from DB
3. Clear cookie in browser

---

### 5. **system_prompts** Table
Manages system prompts that users can select per conversation.

```sql
CREATE TABLE system_prompts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    content TEXT NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Fields:**
- `name`: Unique identifier (e.g., "default", "spanish", "technical")
- `is_default`: Flag for auto-selection in ChatWindow
- `content`: Full system prompt text sent to Ollama

**Usage:**
- Default prompt auto-selected on ChatWindow load
- Users can select different prompts per conversation
- Admin can create/edit/delete system prompts
- Prompt is prepended to message history sent to Ollama

**Admin Features:**
- Edit system prompts at `/admin` (System Prompts tab)
- Only one `is_default=true` at a time
- Deletion doesn't affect existing conversations (they keep old prompt_id)

---

## Relationships Diagram

```
users (1)
  ├─→ (N) conversations
  │         ├─→ (N) messages
  │         └─→ (1) system_prompts
  │
  └─→ (N) sessions

system_prompts (1)
  └─→ (N) conversations
```

---

## Data Access Patterns

### For Frontend/API

**Get user's conversations:**
```python
conversations = db.query(Conversation).filter(
    Conversation.user_id == user_id
).order_by(Conversation.updated_at.desc()).all()
```

**Get conversation with messages:**
```python
conversation = db.query(Conversation).get(conv_id)
messages = conversation.messages  # Relationship load
```

**Create new message:**
```python
message = Message(
    conversation_id=conv_id,
    role="user",
    content=user_input
)
db.add(message)
db.commit()
```

### For Admin Panel

**Get all users with conversation counts:**
```python
users = db.query(User).filter(User.active == True).all()
# Then: user.conversations for eager load
```

**Get all conversations for a user (supervisor view):**
```python
conversations = db.query(Conversation).filter(
    Conversation.user_id.in_(supervisor_subordinate_ids)
).all()
```

**Reassign conversation:**
```python
conversation = db.query(Conversation).get(conv_id)
conversation.user_id = new_user_id  # Foreign key constraint respected
db.commit()
```

---

## Security Considerations

### Authentication & Authorization
- **Passwords:** Bcrypt hashing with salt (never plaintext)
- **Session Tokens:** Random, secure tokens (not JWTs in sessions table)
- **2FA TOTP:** Optional per user, stored in `totp_secret`
- **Cascade Deletes:** User deletion removes all conversations, messages, sessions

### Data Isolation
- **Middleware Enforces:** Users see only their data; admins see all
- **Row-Level:** No explicit RLS; Python layer checks `user_id` matches
- **Frontend:** Route protection via Next.js middleware

### Sensitive Fields
- `password_hash`: Never exposed in API responses
- `totp_secret`: Never returned to frontend (only managed in settings)
- `session_token`: Sent only as HttpOnly cookie, not in JSON

---

## Indexes & Performance

**Recommended Indexes:**
```sql
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_token ON sessions(session_token);
CREATE INDEX idx_users_email ON users(email);
```

**Query Optimization:**
- Conversations ordered by `updated_at DESC` (pagination recommended)
- Message retrieval grouped by conversation (1 query per conv)
- Admin views use joins to count conversations per user

---

## Development Notes

### SQLAlchemy Model Files
- Location: `src/models.py`
- Uses declarative base with type hints
- Relationships auto-loaded via `relationship()` mapper

### Creating Test Data
- Script: `scripts/seed_admin.py` (creates demo admin user)
- Script: `scripts/init_2fa_demo_users.py` (creates 3 demo users with roles)
- Database: Development uses SQLite; prod uses PostgreSQL

### Schema Migrations
- If using Alembic: `alembic upgrade head` after pulling changes
- If manual: Ensure schema matches `models.py` in `src/models.py`

---

## Related Files

- `src/models.py` → SQLAlchemy models
- `src/routes/auth.py` → User & session management
- `src/routes/conversations.py` → Conversation & message APIs
- `src/routes/admin.py` → Admin endpoints with permission checks
- `src/deps.py` → Dependency injection for auth/permissions
