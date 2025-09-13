#!/usr/bin/env bash
set -euo pipefail

echo "🔧 Phase 2: Environment Setup"

# Choose Python 3.12 if available, else fall back to python3
PYTHON_CMD=${PYTHON_CMD:-}
if [ -z "${PYTHON_CMD}" ]; then
  if command -v python3.12 >/dev/null 2>&1; then
    PYTHON_CMD=python3.12
  else
    PYTHON_CMD=python3
  fi
fi
echo "Using Python: $($PYTHON_CMD -V 2>/dev/null || echo unknown)"

# Create virtual environment at .venv (used by existing scripts)
if [ ! -d .venv ]; then
  echo "Creating .venv..."
  $PYTHON_CMD -m venv .venv
fi
source .venv/bin/activate

echo "Upgrading pip/setuptools/wheel"
pip install --upgrade pip setuptools wheel >/dev/null

echo "Installing backend deps (sophia-api)"
pip install -r sophia-api/requirements.txt

echo "Installing WS helper"
pip install websockets >/dev/null

echo "✅ Environment setup complete!"

