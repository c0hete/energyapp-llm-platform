#!/bin/bash
set -e

SERVER="root@184.174.33.249"
REMOTE_PATH="/root/energyapp-llm-platform"
LOCAL_PATH="."

echo "======================================"
echo "Deploying Debug Panel to Production"
echo "======================================"

# 1. Copy updated config.py (7b model)
echo "📦 Copying updated config.py..."
scp src/config.py $SERVER:$REMOTE_PATH/src/config.py

# 2. Copy updated frontend files
echo "📦 Copying frontend components..."
scp frontend/components/ToolCallingDebugPanel.tsx $SERVER:$REMOTE_PATH/frontend/components/
scp frontend/hooks/useChatStream.ts $SERVER:$REMOTE_PATH/frontend/hooks/
scp -r frontend/app $SERVER:$REMOTE_PATH/frontend/

# 3. Copy package.json and build frontend
echo "📦 Copying frontend dependencies..."
scp frontend/package.json $SERVER:$REMOTE_PATH/frontend/

# 4. SSH to server and rebuild + restart services
echo "🔧 Building and restarting services on server..."
ssh $SERVER << 'ENDSSH'
cd /root/energyapp-llm-platform

# Build frontend
echo "Building Next.js..."
cd frontend
npm install
npm run build

# Restart Next.js (assuming PM2)
echo "Restarting Next.js..."
pm2 restart nextjs || npm run start &

# Restart FastAPI (assuming PM2)
cd ..
echo "Restarting FastAPI..."
pm2 restart fastapi || (source .venv/bin/activate && uvicorn src.main:app --host 0.0.0.0 --port 8001 &)

echo "✅ Services restarted!"
pm2 status
ENDSSH

echo ""
echo "======================================"
echo "✅ Deployment Complete!"
echo "======================================"
echo "🌐 Access: https://energyapp.alvaradomazzei.cl"
echo "📊 Debug Panel: Visible in sidebar below conversations"
echo ""
