#!/bin/bash
# Script to check for required secrets in .env.sophia
set -e

echo "🔒 Checking SOPHIA secrets configuration..."

# Check if .env.sophia exists
if [ ! -f ".env.sophia" ]; then
    echo "❌ Error: .env.sophia file not found"
    exit 1
fi

# Load environment variables without displaying them
export $(grep -v '^#' .env.sophia | xargs) > /dev/null 2>&1

# Define required keys (without displaying values)
REQUIRED_KEYS=(
    "OPENAI_API_KEY"
    "ANTHROPIC_API_KEY"
    "GONG_ACCESS_KEY"
    "ASANA_ACCESS_TOKEN"
    "LINEAR_API_KEY"
    "NOTION_API_KEY"
    "NEON_DB_URL"
    "QDRANT_URL"
    "REDIS_URL"
    "SECRET_KEY"
)

# Check each required key
MISSING_KEYS=()
for key in "${REQUIRED_KEYS[@]}"; do
    if [ -z "${!key}" ]; then
        MISSING_KEYS+=("$key")
    fi
done

# Report results
if [ ${#MISSING_KEYS[@]} -eq 0 ]; then
    echo "✅ All required secrets are configured"
else
    echo "⚠️ The following required keys are missing or empty:"
    for key in "${MISSING_KEYS[@]}"; do
        echo "  - $key"
    done
    echo ""
    echo "Please add these keys to your .env.sophia file."
fi
