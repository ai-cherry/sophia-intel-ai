#!/bin/bash
# setup_services.sh - Install and configure native ARM64 local services
set -e

echo "🚀 Installing native services..."

if ! command -v brew >/dev/null 2>&1; then
  echo "❌ Homebrew not found. Install from https://brew.sh first."
  exit 1
fi

# Redis
brew list --versions redis >/dev/null 2>&1 || brew install redis
brew services start redis || true

# PostgreSQL
brew list --versions postgresql@15 >/dev/null 2>&1 || brew install postgresql@15
brew services start postgresql@15 || true
createdb sophia_db 2>/dev/null || true

# Weaviate (optional; binary install)
mkdir -p "$HOME/sophia-services"
cat > "$HOME/sophia-services/start_weaviate.sh" << 'EOF'
#!/bin/bash
set -e
export PERSISTENCE_DATA_PATH="$HOME/sophia-services/weaviate/data"
export AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED="true"
export DEFAULT_VECTORIZER_MODULE="none"
export QUERY_DEFAULTS_LIMIT="25"
export CLUSTER_HOSTNAME="node1"
if [ -x "$HOME/sophia-services/weaviate/weaviate" ]; then
  "$HOME/sophia-services/weaviate/weaviate" --host 0.0.0.0 --port 8080 --scheme http
else
  echo "Weaviate binary not found. Download from https://github.com/weaviate/weaviate/releases and place in ~/sophia-services/weaviate/"
  exit 1
fi
EOF
chmod +x "$HOME/sophia-services/start_weaviate.sh"

echo "✅ Native services installed/started"
