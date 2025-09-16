#!/usr/bin/env bash
set -euo pipefail

# Scaffold or attach the external Workbench UI via git worktree.
# Usage: scripts/scaffold_workbench_ui.sh [path]

TARGET_DIR=${1:-"../worktrees/workbench-ui"}

echo "[scaffold] Attaching Workbench UI worktree at: ${TARGET_DIR}"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  :
else
  echo "Must run from within a git repo" >&2
  exit 1
fi

mkdir -p "$(dirname "${TARGET_DIR}")"

if [ -d "${TARGET_DIR}/.git" ] || [ -d "${TARGET_DIR}/.git/worktrees" ]; then
  echo "[scaffold] Worktree already present at ${TARGET_DIR}"
else
  git worktree add "${TARGET_DIR}" -b workbench-ui || true
fi

echo "[scaffold] Syncing .env.master schema to worktree (if exists)"
if [ -f ./.env.master ]; then
  cp ./.env.master "${TARGET_DIR}/.env.master" || true
fi

cat <<'EON'
Done.
- Develop Workbench in the external worktree.
- Keep UI artifacts out of this repo to avoid drift.
EON

