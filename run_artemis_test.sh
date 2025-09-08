#!/bin/bash
# Artemis real testing script

# Load environment
set -a
source .env.artemis.local
set +a

# Export key variables that Artemis needs
export WEAVIATE_URL WEAVIATE_API_KEY
export OPENAI_API_KEY ANTHROPIC_API_KEY OPENROUTER_API_KEY
export XAI_API_KEY GROQ_API_KEY GEMINI_API_KEY
export LLM_FORCE_PROVIDER=openai
export LLM_FORCE_MODEL=gpt-4

echo "=== Artemis Real Testing ==="
echo "1. Checking readiness..."
./bin/artemis-run scout --check

echo -e "\n2. Running scout with approval mode..."
echo "Task: Analyze repository for AI integration points and architectural hotspots"
./bin/artemis-run scout --approval suggest --task "Analyze repository for AI integration points and architectural hotspots"
