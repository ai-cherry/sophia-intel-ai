#!/bin/bash
# cleanup_deployment.sh - Remove conflicting/broken deployment artifacts (non-destructive backup)
set -e

echo "🧹 Cleaning up deployment mess..."

# Stop everything first (best-effort)
docker stop $(docker ps -aq) >/dev/null 2>&1 || true
docker rm $(docker ps -aq) >/dev/null 2>&1 || true
pkill -f "uvicorn|python app\.main_unified|npm run dev" >/dev/null 2>&1 || true

stamp=$(date +%Y%m%d_%H%M%S)
backup_dir="deployment_backup_${stamp}"
mkdir -p "${backup_dir}"

# Backup common deployment artifacts if present
shopt -s nullglob
to_backup=( deploy*.sh start*.sh stop*.sh docker-compose*.yml docker*.yml compose*.yml Makefile )
if ((${#to_backup[@]})); then
  for f in "${to_backup[@]}"; do
    if [ -e "$f" ]; then
      mv "$f" "${backup_dir}/" || true
    fi
  done
fi

# Remove local Python virtual envs to avoid x86_64/arm64 mixups
rm -rf .venv venv env 2>/dev/null || true

echo "✅ Cleanup complete (backups in ${backup_dir})"

