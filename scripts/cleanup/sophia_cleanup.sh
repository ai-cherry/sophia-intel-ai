#!/bin/bash
# Repository Cleanup Script
# Date: 2025-09-16

set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
ROOT_DIR=$(cd -- "$SCRIPT_DIR/../.." &>/dev/null && pwd)
cd "$ROOT_DIR"
shopt -s nullglob

BACKUP_DIR="$ROOT_DIR/.repo_backup_$(date +%Y%m%d_%H%M%S)"
BACKUP_NAME=$(basename "$BACKUP_DIR")
mkdir -p "$BACKUP_DIR"

echo "\U0001F9F9 Starting comprehensive repository cleanup for sophia-intel-ai..."

move_path() {
  local src="$1"
  if [[ ! -e "$src" ]]; then
    return
  fi
  local rel="${src#./}"
  local dest="$BACKUP_DIR/$rel"
  mkdir -p "$(dirname "$dest")"
  mv "$src" "$dest"
  echo "Moved $src -> $dest"
}

# 1. Move generated/backup patterns
find . \
  -path "./$BACKUP_NAME" -prune -o \
  -path "./.git" -prune -o \
  -path "./.venv" -prune -o \
  -path "./.venv-litellm" -prune -o \
  -type f \
  \( -name "*.tmp" -o -name "*.temp" -o -name "*.bak" -o -name "*.backup" -o -name "*~" -o -name "*.old" \) \
  -print0 | while IFS= read -r -d '' path; do
    move_path "$path"
  done

# 2. Environment copies and secrets placeholders (git-ignored duplicates)
for env_file in \
  ./.env \
  ./.env.local \
  ./.env.local.example \
  ; do
  if [[ -e "$env_file" ]]; then
    move_path "$env_file"
  fi
done

# 3. AI assistant artifacts / backups
for artifact in \
  ./.codexrc.yml.bak* \
  ./.codexrc.yml.fullbak* \
  ./.home/.claude.json.backup \
  ./agent_mcp_startup_report_*.json \
  ./codex-smoke.md \
  ./codex-review-*.md \
  ./logs/qc-scan*.json \
  ./tmp \
  ; do
  move_path "$artifact"
done

# 4. Root-level reports and analysis JSON dumps
find . -maxdepth 1 -type f -name '*report*.json' -print0 | while IFS= read -r -d '' path; do
  move_path "$path"
done
find . -maxdepth 1 -type f -name '*results*.json' -print0 | while IFS= read -r -d '' path; do
  move_path "$path"
done
find . -maxdepth 1 -type f -name '*analysis*.json' -print0 | while IFS= read -r -d '' path; do
  move_path "$path"
done

# 5. Deprecated duplicate docs (root)
for doc in \
  ./ARCHITECTURE.md \
  ./START.md \
  ./STARTUP_GUIDE.md \
  ./COMPLETE_SYSTEM_GUIDE.md \
  ./SYSTEM_OVERVIEW.md \
  ; do
  if [[ -f "$doc" ]]; then
    move_path "$doc"
  fi
done

# 6. Summaries
moved_count=$(find "$BACKUP_DIR" -type f | wc -l | tr -d ' ')
echo "Cleanup complete. Files moved to backup: $moved_count"
echo "Backup directory: $BACKUP_DIR"
