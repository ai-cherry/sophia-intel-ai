#!/usr/bin/env bash
set -euo pipefail

echo "🔧 Local CI Build Script - SOPHIA Intel"
echo "======================================="
echo ""

# 1) Detect FE_DIR
echo "🔍 Detecting frontend directory..."
FE_CANDIDATES=""
for pkg in $(find . -name "package.json" -not -path "*/node_modules/*" -not -path "*/.git/*"); do
  if grep -q '"build"' "$pkg" && ! grep -q '"@pulumi/' "$pkg"; then
    FE_CANDIDATES="$FE_CANDIDATES $(dirname "$pkg")"
  fi
done

# Prefer common locations if multiple
PICK=""
for cand in apps/dashboard apps/web frontend dashboard; do
  if echo "$FE_CANDIDATES" | grep -qw "$cand"; then PICK="$cand"; break; fi
done
if [ -z "${PICK:-}" ]; then
  FE_CANDIDATES=$(echo "$FE_CANDIDATES" | tr ' ' '\n' | sort -u | tr '\n' ' ')
  COUNT=$(echo "$FE_CANDIDATES" | wc -w)
  if [ "$COUNT" = "1" ]; then
    PICK="$(echo "$FE_CANDIDATES" | tr -d ' ')"
  else
    echo "❌ Found multiple FE candidates: $FE_CANDIDATES"
    exit 1
  fi
fi

echo "✅ Frontend directory: $PICK"

# 2) Build frontend
echo ""
echo "📦 Installing and building frontend..."
pushd "$PICK" >/dev/null

if [ -f package-lock.json ]; then 
  echo "Using npm ci (lockfile found)"
  npm ci
else 
  echo "Using npm install (no lockfile)"
  npm install
fi

echo "Building frontend..."
VITE_API_URL="${VITE_API_URL:-https://api.sophia-intel.ai}" NODE_ENV=production npm run build

popd >/dev/null
echo "✅ Frontend build completed"

# 3) Backend dependencies
echo ""
echo "🐍 Installing backend dependencies..."
BE_REQ=""
if [ -f "backend/requirements.txt" ]; then
  BE_REQ="backend/requirements.txt"
else
  CAND=$(find . -name "requirements.txt" -not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "*/.venv/*" | head -n1 || true)
  if [ -n "$CAND" ]; then BE_REQ="$CAND"; fi
fi

if [ -n "$BE_REQ" ]; then
  echo "Installing Python dependencies from: $BE_REQ"
  python -m pip install --upgrade pip
  pip install -r "$BE_REQ"
  echo "✅ Python dependencies installed"
else
  echo "⚠️ No requirements.txt found, skipping Python dependencies"
fi

# 4) Backend import probe
echo ""
echo "🧪 Testing backend imports..."
BE_IMPORT=""
if [ -f "backend/__init__.py" ] && [ -f "backend/simple_main.py" ]; then
  BE_IMPORT="backend.simple_main"
elif [ -f "backend/main.py" ]; then
  BE_IMPORT="backend.main"
fi

if [ -n "$BE_IMPORT" ]; then
  python - <<PY
import importlib
import sys
mod = "$BE_IMPORT"
try:
  importlib.import_module(mod)
  print(f"✅ Import OK: {mod}")
except Exception as e:
  print(f"❌ Import failed: {e}")
  sys.exit(1)
PY
else
  echo "⚠️ No backend module found for import testing"
fi

echo ""
echo "🎉 Local CI build completed successfully!"
echo ""
echo "📋 Summary:"
echo "  Frontend: $PICK (built)"
echo "  Backend: ${BE_REQ:-none} (dependencies installed)"
echo "  Import test: ${BE_IMPORT:-skipped}"

