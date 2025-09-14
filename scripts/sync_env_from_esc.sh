#!/usr/bin/env bash
set -euo pipefail

# Sync environment variables from Pulumi ESC into the current shell or a file.
# This script does not print secrets to stdout; it writes to a target file when specified.

ENV_NAME=${1:-dev}
OUT_FILE=${2:-.env.master}

echo "[esc] Exporting ESC environment: sophia/${ENV_NAME} -> ${OUT_FILE}"
echo "# GENERATED FROM ESC sophia/${ENV_NAME}" >"${OUT_FILE}"
echo "# Do not commit real secrets" >>"${OUT_FILE}"

# Placeholder implementation (avoid requiring pulumi CLI here). Integrate in CI.
cat <<'EOF' >>"${OUT_FILE}"
APP_ENV=dev
SERVICE_NAME=sophia-intel-ai
LOG_LEVEL=INFO
AI_ROUTER=direct
AI_PROVIDER=openai
HTTP_DEFAULT_TIMEOUT_MS=15000
HTTP_RETRY_MAX=3
HTTP_BACKOFF_BASE_MS=200
POSTGRES_URL=postgres://user:pass@localhost:5432/sophia
REDIS_URL=redis://localhost:6379/0
WEAVIATE_URL=http://localhost:8080
NEO4J_URL=bolt://localhost:7687
MCP_TOKEN=
MCP_DEV_BYPASS=1
RATE_LIMIT_RPM=120
READ_ONLY=0
OPENAI_API_KEY=example_openai_key
ANTHROPIC_API_KEY=example_anthropic_key
GOOGLE_GEMINI_API_KEY=example_gemini_key
MISTRAL_API_KEY=example_mistral_key
GROQ_API_KEY=example_groq_key
XAI_API_KEY=example_xai_key
COHERE_API_KEY=example_cohere_key
AI21_API_KEY=example_ai21_key
OPENROUTER_API_KEY=example_openrouter_key
PORTKEY_API_KEY=example_portkey_key
EOF

echo "[esc] Wrote ${OUT_FILE}. Replace placeholders via CI using pulumi esc."

