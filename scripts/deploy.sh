#!/bin/bash
set -e  # Exit on error

echo "======================================"
echo "EnergyApp LLM - Deployment Script"
echo "======================================"

# 1. Navigate to project root
cd /root

# 2. Set environment variables
echo "Setting environment variables..."
export ENERGYAPP_DB_URL="postgresql+psycopg2://energyapp:energyapp_db_demo@localhost:5432/energyapp"
export ENERGYAPP_SECRET_KEY="cambia_esto_tambien"

# 3. Create or activate virtual environment
echo "Setting up Python virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate

# 4. Install dependencies
echo "Installing dependencies from requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

# 5. Start Uvicorn server
echo "======================================"
echo "Starting Uvicorn server..."
echo "API disponible en: http://0.0.0.0:8000"
echo "Health check: http://localhost:8000/health"
echo "======================================"

uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
