#!/bin/bash
set -e

# SOPHIA Intel Go-Live Gauntlet - Phase 2: Application Deployment
echo "🧠 SOPHIA Intel Go-Live Gauntlet - Phase 2"
echo "Deploying Sophia Orchestrator & Agent Swarm Activation"

PRODUCTION_IP="104.171.202.107"
SSH_KEY="$HOME/.ssh/sophia_production_key"

# Function to run commands on production server
run_remote() {
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@$PRODUCTION_IP "$1"
}

# Function to copy files to production server
copy_to_remote() {
    scp -i "$SSH_KEY" -o StrictHostKeyChecking=no "$1" ubuntu@$PRODUCTION_IP:"$2"
}

echo "=== Step 1: Creating secrets ==="

# Encode secrets in base64 (using environment variables)
OPENROUTER_KEY_B64=$(echo -n "$OPENROUTER_API_KEY" | base64 -w 0)
QDRANT_KEY_B64=$(echo -n "$QDRANT_API_KEY" | base64 -w 0)
QDRANT_URL_B64=$(echo -n "$QDRANT_URL" | base64 -w 0)
GITHUB_PAT_B64=$(echo -n "$GITHUB_PAT" | base64 -w 0)

# Create secrets file
cat > /tmp/secrets.yaml << EOF
apiVersion: v1
kind: Secret
metadata:
  name: sophia-secrets
  namespace: sophia-intel
type: Opaque
data:
  openrouter-api-key: "$OPENROUTER_KEY_B64"
  qdrant-api-key: "$QDRANT_KEY_B64"
  qdrant-url: "$QDRANT_URL_B64"
  github-pat: "$GITHUB_PAT_B64"
