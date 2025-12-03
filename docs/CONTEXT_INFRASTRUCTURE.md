# Infrastructure Context: EnergyApp LLM Platform

**Purpose:** Comprehensive reference for deployment, systemd services, Caddy reverse proxy, server management, and production operations.

## Production Environment

- **Server:** VPS with Ubuntu 24.04 LTS
- **CPU:** 6 vCPU (minimum 4)
- **RAM:** 12 GB (minimum 8)
- **Storage:** 100 GB SSD (minimum 50 GB)
- **Network:** Public IP with domain `energyapp.alvaradomazzei.cl`
- **IP Address:** 184.174.33.249

---

## Systemd Services

### 1. FastAPI Backend Service
**File:** `/etc/systemd/system/energyapp-api.service`

```ini
[Unit]
Description=EnergyApp FastAPI Backend
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/energyapp-llm-platform
ExecStart=/root/energyapp-llm-platform/.venv/bin/uvicorn src.main:app \
    --host 127.0.0.1 \
    --port 8001 \
    --workers 4

Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Environment variables
EnvironmentFile=/root/energyapp-llm-platform/.env.prod
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
```

**Management:**
```bash
# Start service
sudo systemctl start energyapp-api

# Stop service
sudo systemctl stop energyapp-api

# Restart service
sudo systemctl restart energyapp-api

# Check status
sudo systemctl status energyapp-api

# View logs
sudo journalctl -u energyapp-api -f
sudo journalctl -u energyapp-api --lines=50
```

### 2. Next.js Frontend Service
**File:** `/etc/systemd/system/energyapp-web.service`

```ini
[Unit]
Description=EnergyApp Next.js Frontend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/energyapp-llm-platform/frontend
ExecStart=/usr/bin/npm start

Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Environment variables
Environment="PORT=3000"
Environment="NODE_ENV=production"

[Install]
WantedBy=multi-user.target
```

**Management:**
```bash
# Restart service
sudo systemctl restart energyapp-web

# Check status
sudo systemctl status energyapp-web

# View logs
sudo journalctl -u energyapp-web -f
```

### 3. Ollama Service (Optional)
**File:** `/etc/systemd/system/ollama.service` (usually pre-installed)

```ini
[Unit]
Description=Ollama
After=network.target

[Service]
Type=simple
Environment="OLLAMA_HOST=127.0.0.1:11434"
ExecStart=/usr/local/bin/ollama serve

[Install]
WantedBy=multi-user.target
```

---

## Reverse Proxy Configuration (Caddy)

### Caddyfile
**Location:** `/etc/caddy/Caddyfile`

```
energyapp.alvaradomazzei.cl {
    # Enable gzip compression
    encode gzip

    # Log access requests
    log {
        output file /var/log/caddy/energyapp-access.log {
            roll_size 5mb
            roll_keep 14
            roll_keep_for 336h
        }
    }

    # Proxy frontend requests to Next.js
    reverse_proxy 127.0.0.1:3000

    # Special handling for /api/* routes
    handle /api/* {
        # Remove /api prefix before sending to FastAPI
        uri strip_prefix /api

        # Proxy to FastAPI backend
        reverse_proxy 127.0.0.1:8001
    }

    # Error pages
    handle_errors {
        respond "{http.error.status_code} {http.error.status_text}"
    }
}
```

**Caddy Service Management:**
```bash
# Reload configuration (no downtime)
sudo systemctl reload caddy

# Restart service
sudo systemctl restart caddy

# Check status
sudo systemctl status caddy

# View logs
sudo journalctl -u caddy -f
```

### SSL/TLS Certificates
Caddy automatically obtains and renews Let's Encrypt certificates.

```bash
# View certificate info
sudo caddy trust

# Manually renew (usually automatic)
sudo systemctl reload caddy
```

---

## Deployment Process

### Pre-Deployment Checklist
1. ✅ All changes committed to GitHub
2. ✅ Tests passing locally
3. ✅ Build successful on local machine
4. ✅ No uncommitted changes in working directory
5. ✅ Current branch is `main`

### Step-by-Step Deployment

**1. SSH into VPS**
```bash
ssh root@184.174.33.249
cd /root/energyapp-llm-platform
```

**2. Backend (FastAPI) Update**
```bash
# Activate Python environment
source .venv/bin/activate

# Pull latest changes
git pull origin main

# Install/update dependencies
pip install -r requirements.txt

# Migrate database (if needed)
# alembic upgrade head

# Exit venv
deactivate
```

**3. Frontend (Next.js) Update**
```bash
cd frontend

# Clear any uncommitted changes
git checkout .

# Pull latest changes (already done above)
# git pull origin main

# Install dependencies
npm install

# Build for production
npm run build

# Verify build succeeded
ls -la .next/

# Return to project root
cd ..
```

**4. Restart Services**
```bash
# Stop all services
sudo systemctl stop energyapp-api energyapp-web

# Clear caches (optional but recommended)
rm -rf /root/energyapp-llm-platform/frontend/.next
rm -rf /root/energyapp-llm-platform/frontend/.turbo
rm -rf /root/energyapp-llm-platform/frontend/node_modules/.cache

# Start services
sudo systemctl start energyapp-api energyapp-web

# Verify services are running
sudo systemctl status energyapp-api energyapp-web
```

**5. Health Checks**
```bash
# Check API health
curl http://127.0.0.1:8001/health

# Check frontend loads
curl -I http://127.0.0.1:3000/login | grep HTTP

# Check via Caddy (public)
curl -I https://energyapp.alvaradomazzei.cl/login | grep HTTP

# Verify chunks load (CRITICAL)
curl -I https://energyapp.alvaradomazzei.cl/_next/static/chunks/main.js | grep HTTP
```

**6. Monitor Logs**
```bash
# Tail logs in real-time
sudo journalctl -u energyapp-api -f &
sudo journalctl -u energyapp-web -f &

# Check for errors
grep ERROR /var/log/caddy/energyapp-access.log | tail -10
```

---

## Complete Deployment Script

**File:** `scripts/deploy_remote.py`

```python
#!/usr/bin/env python3
import subprocess
import sys
from datetime import datetime

def run_cmd(cmd, ssh=False):
    """Execute command locally or via SSH"""
    if ssh:
        cmd = f'ssh root@184.174.33.249 "{cmd}"'

    print(f"[{datetime.now()}] Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Command failed: {result.stderr}")
        sys.exit(1)

    print(f"✅ {result.stdout.strip()}")
    return result.stdout

def deploy():
    """Deploy to production"""
    print("🚀 Starting deployment...")

    # 1. Verify local repo is clean
    status = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
    if status.stdout.strip():
        print("❌ Uncommitted changes. Commit first.")
        sys.exit(1)

    # 2. SSH: Pull changes
    run_cmd("cd /root/energyapp-llm-platform && git pull origin main", ssh=True)

    # 3. SSH: Backend update
    run_cmd(
        "cd /root/energyapp-llm-platform && "
        "source .venv/bin/activate && "
        "pip install -r requirements.txt && "
        "deactivate",
        ssh=True
    )

    # 4. SSH: Frontend build
    run_cmd(
        "cd /root/energyapp-llm-platform/frontend && "
        "npm install && "
        "npm run build",
        ssh=True
    )

    # 5. SSH: Restart services
    run_cmd("sudo systemctl restart energyapp-api energyapp-web", ssh=True)

    # 6. SSH: Health checks
    run_cmd("curl -I http://127.0.0.1:8001/health", ssh=True)
    run_cmd("curl -I http://127.0.0.1:3000/login", ssh=True)

    print("✅ Deployment complete!")

if __name__ == "__main__":
    deploy()
```

---

## Database Management

### PostgreSQL Backup
```bash
# Backup database
pg_dump -U energyapp energyapp > backup_$(date +%Y%m%d).sql

# Backup to remote location (recommended)
pg_dump -U energyapp energyapp | gzip > /backup/energyapp_$(date +%Y%m%d).sql.gz

# Restore from backup
gunzip < backup_20231201.sql.gz | psql -U energyapp energyapp
```

### Ollama Model Management
```bash
# List available models
ollama list

# Pull model
ollama pull qwen2.5:3b-instruct

# Remove model (if needed)
ollama rm qwen2.5:3b-instruct

# Check model info
ollama show qwen2.5:3b-instruct
```

---

## Firewall Configuration (UFW)

### Setup
```bash
# Enable UFW
sudo ufw enable

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP
sudo ufw allow 80/tcp

# Allow HTTPS
sudo ufw allow 443/tcp

# Check rules
sudo ufw status

# View rules with IPs
sudo ufw show added
```

### Advanced Rules
```bash
# Restrict API to local access only
sudo ufw allow from 127.0.0.1 to 127.0.0.1 port 8001

# Rate limiting (optional)
# Done via Caddy or iptables
```

---

## Monitoring & Alerts

### Health Check Script
**File:** `scripts/check_service.py`

```bash
#!/bin/bash
SERVER="root@184.174.33.249"

# Check API
API_STATUS=$(ssh $SERVER "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8001/health")
if [ "$API_STATUS" != "200" ]; then
    echo "❌ API health check failed: $API_STATUS"
    exit 1
fi

# Check Frontend
WEB_STATUS=$(ssh $SERVER "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:3000/login")
if [ "$WEB_STATUS" != "200" ]; then
    echo "❌ Web health check failed: $WEB_STATUS"
    exit 1
fi

# Check Ollama
OLLAMA_STATUS=$(ssh $SERVER "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:11434/api/tags")
if [ "$OLLAMA_STATUS" != "200" ]; then
    echo "❌ Ollama health check failed: $OLLAMA_STATUS"
    exit 1
fi

echo "✅ All services healthy"
```

### Log Analysis
```bash
# Check for errors in API logs
sudo journalctl -u energyapp-api -p err -S "1 hour ago"

# Check for errors in web logs
sudo journalctl -u energyapp-web -p err -S "1 hour ago"

# Count requests per minute (Caddy)
tail -f /var/log/caddy/energyapp-access.log | grep "$(date +%d/%b/%Y)" | wc -l
```

---

## Troubleshooting

### Symptom: API Returns 500 Errors
**Solution:**
```bash
# Check service is running
sudo systemctl status energyapp-api

# View error logs
sudo journalctl -u energyapp-api -n 50

# Check database connection
ssh root@184.174.33.249 "psql -U energyapp -d energyapp -c 'SELECT 1'"

# Restart service
sudo systemctl restart energyapp-api
```

### Symptom: Frontend Chunks Return 404
**Solution:**
```bash
# Verify .next directory exists
ssh root@184.174.33.249 "ls -la /root/energyapp-llm-platform/frontend/.next/static/chunks/"

# Rebuild frontend
ssh root@184.174.33.249 "cd /root/energyapp-llm-platform/frontend && npm run build"

# Restart web service
sudo systemctl restart energyapp-web
```

### Symptom: Ollama Not Responding
**Solution:**
```bash
# Check Ollama is running
sudo systemctl status ollama

# Check port 11434 is listening
ss -tlnp | grep 11434

# Restart Ollama
sudo systemctl restart ollama

# Verify model is loaded
ollama list
```

### Symptom: Certificate Expired
**Solution:**
```bash
# Caddy auto-renews; force renewal
sudo systemctl reload caddy

# Check certificate expiry
echo | openssl s_client -servername energyapp.alvaradomazzei.cl \
    -connect energyapp.alvaradomazzei.cl:443 2>/dev/null | \
    openssl x509 -noout -dates
```

---

## Performance Tuning

### FastAPI Worker Count
```ini
# In energyapp-api.service
ExecStart=/root/energyapp-llm-platform/.venv/bin/uvicorn src.main:app \
    --host 127.0.0.1 \
    --port 8001 \
    --workers 4  # 1 per CPU core (adjust if needed)
```

### Caddy Connection Limits
```
energyapp.alvaradomazzei.cl {
    # Limit connections
    reverse_proxy 127.0.0.1:3000 {
        health_uri /
        health_interval 10s
        health_timeout 5s
    }
}
```

### Database Connection Pool
```python
# In src/main.py
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)
```

---

## Security Best Practices

### SSH Hardening
```bash
# Generate SSH key (on local machine)
ssh-keygen -t ed25519 -C "deployment"

# Add to VPS authorized_keys
ssh-copy-id -i ~/.ssh/id_ed25519.pub root@184.174.33.249

# Disable password auth (in /etc/ssh/sshd_config)
sudo vi /etc/ssh/sshd_config
# Set: PasswordAuthentication no
sudo systemctl restart sshd
```

### Database Security
```bash
# Create dedicated database user
sudo -u postgres createuser energyapp -P
sudo -u postgres createdb -O energyapp energyapp

# Restrict to local connections (pg_hba.conf)
local   energyapp   energyapp   md5
host    energyapp   energyapp   127.0.0.1/32   md5
```

### API Rate Limiting
```python
# In src/main.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/auth/login")
@limiter.limit("5/minute")
async def login(request: Request):
    # Login limited to 5 attempts per minute
    pass
```

---

## Related Files & References

- `/etc/systemd/system/energyapp-api.service` → FastAPI service configuration
- `/etc/systemd/system/energyapp-web.service` → Next.js service configuration
- `/etc/caddy/Caddyfile` → Reverse proxy configuration
- `/root/energyapp-llm-platform/.env.prod` → Production environment variables
- `scripts/deploy_remote.py` → Automated deployment script
- `scripts/check_service.py` → Health check script
- `docs/CONTEXT_BACKEND.md` → Backend API details
- `docs/CONTEXT_FRONTEND.md` → Frontend deployment details
