#!/usr/bin/env bash
set -euo pipefail

# Levanta la API en modo desarrollo (uvicorn).

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/.venv"

cd "${PROJECT_ROOT}"

if [[ ! -d "${VENV_DIR}" ]]; then
  python -m venv "${VENV_DIR}"
fi

# Activar venv
if [[ -f "${VENV_DIR}/Scripts/activate" ]]; then
  # shellcheck disable=SC1091
  source "${VENV_DIR}/Scripts/activate"
else
  # shellcheck disable=SC1091
  source "${VENV_DIR}/bin/activate"
fi

python -m pip install --upgrade pip >/dev/null
python -m pip install -r requirements.txt

export ENERGYAPP_ENV=dev
export ENERGYAPP_DB_URL="sqlite:///./data/app.db"

uvicorn src.main:app --reload --port 8000 --host 0.0.0.0
