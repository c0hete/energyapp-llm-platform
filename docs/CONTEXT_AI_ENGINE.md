# AI Engine Context: EnergyApp LLM Platform

**Purpose:** Comprehensive reference for the AI inference engine, Ollama integration, and LLM configuration in EnergyApp.

## AI Architecture Overview

- **Inference Engine:** Ollama (local, self-hosted)
- **Model:** Qwen 2.5:3B Instruct (GGUF Q4 quantization)
- **Endpoint:** `http://127.0.0.1:11434`
- **Inference:** Streaming responses via FastAPI SSE
- **No External APIs:** All data stays on local infrastructure

---

## Ollama Integration

### Installation & Setup

**On VPS (Ubuntu 24.04):**
```bash
# Download and install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama daemon
systemctl start ollama

# Pull Qwen 2.5:3B model
ollama pull qwen2.5:3b-instruct

# Verify model is loaded
ollama list
```

**Local Development (Windows/macOS):**
- Download from https://ollama.ai
- Install and run Ollama.app
- Model auto-downloads on first request

### Model Details

**Qwen 2.5:3B Instruct**
- Size: ~2.0 GB (quantized Q4)
- RAM Usage: ~2-3 GB during inference (with context)
- Max Context: 32K tokens
- Input Format: Instruct/Chat format
- Output: Streaming text tokens
- Quantization: Q4_K_M (good quality/speed balance)

**Why Qwen 2.5:3B?**
- Lightweight: Runs on modest hardware (6 vCPU, 12 GB RAM)
- Good quality: Strong instruction following for business tasks
- Fast: ~50-100 tokens/second on typical server
- No licensing: Open model (Apache 2.0 or similar)

---

## Chat API Flow

### 1. Frontend (Next.js)
**Location:** `frontend/components/ChatWindow.tsx`

```typescript
// User sends message
const response = await fetch('/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    conversation_id: convId,
    message: userMessage,
    system_prompt_id: promptId
  })
});

// Stream response
const reader = response.body.getReader();
while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  const text = new TextDecoder().decode(value);
  // Append to message display
}
```

---

### 2. Backend (FastAPI)
**Location:** `src/routes/conversations.py` → `POST /api/chat`

**Step 1: Validate & Prepare**
```python
@router.post("/chat")
async def chat(request: ChatRequest, db: Session = Depends(get_db), user = Depends(get_current_user)):
    conversation = db.query(Conversation).get(request.conversation_id)
    if conversation.user_id != user.id and user.role != "admin":
        raise HTTPException(403, "Not authorized")

    # Save user message
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message
    )
    db.add(user_message)
    db.commit()
```

**Step 2: Build Message Context**
```python
# Retrieve system prompt
system_prompt = db.query(SystemPrompt).get(request.system_prompt_id)
or system_prompt = db.query(SystemPrompt).filter(
    SystemPrompt.is_default == True
).first()

# Retrieve conversation history (last 10 messages)
history = db.query(Message).filter(
    Message.conversation_id == conversation.id
).order_by(Message.created_at.desc()).limit(10).all()
history.reverse()  # Oldest first

# Build message list for Ollama
messages = [
    {"role": "system", "content": system_prompt.content},
    *[{"role": m.role, "content": m.content} for m in history],
    {"role": "user", "content": request.message}
]
```

**Step 3: Stream Inference**
```python
# Call Ollama with streaming
async def stream_from_ollama():
    async with ollama_client.stream_chat(
        model="qwen2.5:3b-instruct",
        messages=messages,
        temperature=0.7,
        top_p=0.9
    ) as stream:
        full_response = ""
        async for chunk in stream:
            token = chunk.get("message", {}).get("content", "")
            full_response += token
            yield f"data: {json.dumps({'token': token})}\n\n"
```

**Step 4: Save Assistant Response**
```python
# After streaming completes
assistant_message = Message(
    conversation_id=conversation.id,
    role="assistant",
    content=full_response
)
db.add(assistant_message)
db.commit()

# Update conversation updated_at timestamp
conversation.updated_at = datetime.utcnow()
db.commit()
```

**Step 5: Return Stream**
```python
return StreamingResponse(
    stream_from_ollama(),
    media_type="text/event-stream",
    headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    }
)
```

---

### 3. Ollama Client
**Location:** `src/ollama_client.py`

```python
import httpx

class OllamaClient:
    def __init__(self, base_url: str = "http://127.0.0.1:11434"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()

    async def stream_chat(self, model: str, messages: list, temperature: float = 0.7, top_p: float = 0.9):
        """Stream chat completion from Ollama"""
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "stream": True
        }

        async with self.client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response:
            async for line in response.aiter_lines():
                if line:
                    chunk = json.loads(line)
                    yield chunk
```

---

## System Prompts

### Default System Prompt
Located in DB table `system_prompts` with `is_default=true`:

```
Eres un asistente de IA amable y útil. Responde preguntas en español e inglés con claridad y precisión.
Proporciona respuestas concisas pero completas. Mantén un tono profesional y amigable.
```

### Custom Prompts
Admin can manage system prompts via `/admin` panel (System Prompts tab):
- Create new prompts
- Mark one as default (auto-selected in ChatWindow)
- Edit existing prompts
- Delete prompts

### Prompt Selection Flow
```
ChatWindow mounted
  ↓
useEffect: Load system prompts via useSystemPrompts hook
  ↓
Find prompt with is_default=true
  ↓
Auto-select it (setSelectedPromptId)
  ↓
User can override with dropdown
  ↓
Selected prompt sent in POST /api/chat
```

---

## Performance Optimization

### Token Limits
- **Max Context:** 32K tokens (Qwen 2.5:3B)
- **Typical Conversation:** 5-15 messages = ~500-1500 tokens
- **Strategy:** Load last 10 messages + new message (stays well under limit)

### Streaming Optimization
- **Chunk Size:** Tokens sent as they're generated
- **Latency:** ~100ms for first token; then streaming
- **Throughput:** ~50-100 tokens/second

### Database Optimization
- **Message Retrieval:** `SELECT * FROM messages WHERE conversation_id = ? LIMIT 10` (indexed)
- **Sorting:** `ORDER BY created_at DESC` (reversed in memory for context)
- **Batch Saves:** User message + assistant message in single transaction

---

## Error Handling

### Ollama Connection Errors
**If Ollama is down:**
```python
except httpx.ConnectError:
    return JSONResponse({
        "error": "Servicio de IA no disponible",
        "details": "Ollama no responde en 127.0.0.1:11434"
    }, status_code=503)
```

**Health Check Endpoint:**
```python
@router.get("/health")
async def health():
    try:
        await ollama_client.list_models()
        return {"status": "ok", "ollama": "healthy"}
    except:
        return JSONResponse({"status": "degraded", "ollama": "offline"}, 503)
```

### Model Not Found
```python
except OllamaModelError:
    return JSONResponse({
        "error": "Modelo no encontrado",
        "details": "qwen2.5:3b-instruct no está disponible. Ejecuta: ollama pull qwen2.5:3b-instruct"
    }, status_code=503)
```

---

## Configuration

### Environment Variables
```bash
# .env or systemd service
ENERGYAPP_OLLAMA_BASE_URL=http://127.0.0.1:11434
ENERGYAPP_OLLAMA_MODEL=qwen2.5:3b-instruct
ENERGYAPP_OLLAMA_TEMPERATURE=0.7
ENERGYAPP_OLLAMA_TOP_P=0.9
```

### Ollama Settings
```bash
# Ollama config (if needed for specific deployment)
OLLAMA_HOST=127.0.0.1:11434
OLLAMA_MODELS=/root/.ollama/models
```

### Model Switching
To use a different model:
1. Pull model: `ollama pull [model-name]`
2. Update env var: `ENERGYAPP_OLLAMA_MODEL=[model-name]`
3. Restart FastAPI service: `systemctl restart energyapp-api`
4. Verify: `curl http://127.0.0.1:8001/api/health`

**Alternative Models:**
- `mistral:latest` (~4B, fast)
- `neural-chat:latest` (~13B, better quality, slower)
- `llama2:latest` (~7B, good balance)

---

## Testing the AI Engine

### Manual Testing
```bash
# 1. Check Ollama is running
curl http://127.0.0.1:11434/api/tags

# 2. Test model directly
curl http://127.0.0.1:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:3b-instruct",
    "messages": [{"role": "user", "content": "Hola, ¿quién eres?"}],
    "stream": true
  }'

# 3. Test via FastAPI endpoint
curl http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": 1,
    "message": "Hola",
    "system_prompt_id": 1
  }'
```

### Frontend Testing
1. Login to `/dashboard`
2. Send message in chat
3. Open Network tab (DevTools) → see `/api/chat` request
4. Response should be `text/event-stream` with `data: {...}` chunks

---

## Monitoring & Logging

### Log Files
- **FastAPI:** `/var/log/energyapp-api.log` (systemd journal)
- **Ollama:** Logs to stdout (capture via `systemctl status ollama`)

### Key Events to Monitor
```python
# In FastAPI routes
import logging
logger = logging.getLogger(__name__)

logger.info(f"Chat request: conversation_id={conv_id}, user={user_id}")
logger.info(f"Ollama inference started for {len(messages)} context messages")
logger.info(f"Response streamed: {token_count} tokens in {elapsed_ms}ms")
logger.error(f"Ollama connection failed: {error}")
```

### Performance Metrics
- First token latency
- Tokens/second
- Ollama uptime
- Model load/unload cycles

---

## Related Files & References

- `src/ollama_client.py` → Ollama client implementation
- `src/routes/conversations.py` → Chat API endpoint
- `frontend/components/ChatWindow.tsx` → Frontend streaming logic
- `src/models.py` → Message, Conversation, SystemPrompt models
- `docs/arquitectura.md` → Full architecture overview
- Ollama docs: https://github.com/ollama/ollama
