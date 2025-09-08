#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$HOME/artemis-cli"
REPO_SSH="git@github.com:ai-cherry/artemis-cli.git"

echo "🔎 Checking SSH access to GitHub..."
if ! ssh -T git@github.com 2>&1 | grep -qi "successfully authenticated"; then
  echo "⚠️  SSH authentication to GitHub not confirmed. Ensure your SSH key is loaded (ssh-add -l) and GitHub has the public key."
  exit 1
fi

if [ -d "$REPO_DIR/.git" ]; then
  echo "✅ Found existing Artemis repo at $REPO_DIR"
  (cd "$REPO_DIR" && git remote -v)
else
  echo "⬇️  Cloning Artemis sidecar to $REPO_DIR ..."
  git clone "$REPO_SSH" "$REPO_DIR"
  echo "✅ Cloned Artemis sidecar."
fi

cat <<EOF

Next steps:
  - Export ARTEMIS_PATH=$REPO_DIR (or add to your .env.local)
  - For dev compose with Artemis FS profile:
      docker compose -f docker-compose.dev.yml --profile artemis up -d mcp-filesystem-artemis
  - Artemis repo health:
      (cd $REPO_DIR && git status && git remote -v)
EOF

