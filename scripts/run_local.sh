#!/usr/bin/env bash
set -euo pipefail

# Arranque local de EnergyApp LLM Platform (modo desarrollo).
# - Crea/usa entorno virtual .venv
# - Instala dependencias si requirements.txt existe
# - Ejecuta pytest si está disponible

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/.venv"

cd "${PROJECT_ROOT}"

if [[ ! -d "${VENV_DIR}" ]]; then
  python -m venv "${VENV_DIR}"
fi

# Activar venv
if [[ -f "${VENV_DIR}/Scripts/activate" ]]; then
  # Windows (Git Bash / WSL)
  # shellcheck disable=SC1091
  source "${VENV_DIR}/Scripts/activate"
else
  # Linux/Mac
  # shellcheck disable=SC1091
  source "${VENV_DIR}/bin/activate"
fi

python -m pip install --upgrade pip >/dev/null

if [[ -f "requirements.txt" ]]; then
  python -m pip install -r requirements.txt
else
  echo "requirements.txt no encontrado (ok para fase inicial)."
fi

if command -v pytest >/dev/null 2>&1; then
  echo "Ejecutando tests..."
  pytest
else
  echo "pytest no instalado. Instala con: pip install pytest"
fi
