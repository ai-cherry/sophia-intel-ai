#!/bin/bash
# setup_arm64.sh - Create ARM64-native Python environment on Apple Silicon
set -e

echo "🔧 Setting up ARM64-native environment..."

if [[ $(uname -m) != "arm64" ]]; then
  echo "❌ Not on ARM64 - this script is for M1/M2/M3 Macs only"
  exit 1
fi

# Ensure Homebrew exists
if ! command -v brew >/dev/null 2>&1; then
  echo "❌ Homebrew not found. Install from https://brew.sh first."
  exit 1
fi

# Prefer Python 3.11 for stable ARM64 wheels
brew list --versions python@3.11 >/dev/null 2>&1 || brew install python@3.11

"$(brew --prefix)"/opt/python@3.11/bin/python3.11 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip wheel setuptools

cat > requirements_arm64.txt << 'EOF'
# Core
fastapi==0.104.1
uvicorn[standard]==0.30.1
httpx==0.25.2
redis==5.0.1
click==8.1.7
rich==13.7.0

# Dev tools
ruff==0.5.7
black==24.4.2

# AI/LLM SDKs
openai==1.12.0
anthropic==0.18.1
google-generativeai==0.3.2

# Database
asyncpg==0.29.0
sqlalchemy==2.0.23

# Utilities
python-dotenv==1.0.0
pyyaml==6.0.1
gitpython==3.1.40
watchdog==3.0.0

# Scientific / math
numpy==1.26.4

# Observability
opentelemetry-api==1.25.0
opentelemetry-sdk==1.25.0
opentelemetry-exporter-otlp-proto-grpc==1.25.0
# Keep OpenTelemetry packages aligned to avoid resolver conflicts
opentelemetry-exporter-prometheus==0.46b0
opentelemetry-instrumentation-fastapi==0.46b0
opentelemetry-instrumentation-asyncpg==0.46b0
opentelemetry-instrumentation-redis==0.46b0
opentelemetry-instrumentation-requests==0.46b0
opentelemetry-instrumentation-logging==0.46b0
opentelemetry-instrumentation-httpx==0.46b0
opentelemetry-semantic-conventions==0.46b0
opentelemetry-semantic-conventions-ai==0.1.0

# Avoid heavy/no wheel packages on ARM64:
# - tensorflow (use tensorflow-macos separately if needed)
# - grpcio (build from source only when required)
EOF

pip install -r requirements_arm64.txt

echo "✅ ARM64 environment ready (venv: .venv)"
