#!/usr/bin/env bash
set -euo pipefail

# Fast-path: create new GitHub repo for Workbench, push split history,
# patch path references, and stage removal from backend repo.
#
# Requirements:
# - GitHub CLI `gh` authenticated (`gh auth login`)
# - Network access
# - This script is run from backend repo root (sophia-intel-ai)
#
# Usage:
#   bash scripts/finish_workbench_extraction.sh <owner/repo> [private|public]
# Example:
#   bash scripts/finish_workbench_extraction.sh ai-cherry/sophia-workbench-ui private

NEW_REPO=${1:-}
VISIBILITY=${2:-private}

if [ -z "$NEW_REPO" ]; then
  echo "Usage: $0 <owner/repo> [private|public]" >&2
  exit 2
fi

WT_DIR=${WT_DIR:-"../worktrees/workbench-ui"}

if [ ! -d "$WT_DIR/.git" ]; then
  echo "Worktree not found at $WT_DIR. Run scripts/extract_workbench_repo.sh first." >&2
  exit 2
fi

echo "[github] Creating repo $NEW_REPO ($VISIBILITY) ..."
gh repo create "$NEW_REPO" --"$VISIBILITY" --confirm >/dev/null

echo "[push] Pushing split history to $NEW_REPO ..."
(
  cd "$WT_DIR"
  git remote remove origin >/dev/null 2>&1 || true
  git remote add origin "git@github.com:$NEW_REPO.git"
  git push -u origin HEAD:main

  echo "[patch] Adjusting path references in src/server.ts ..."
  if [ -f src/server.ts ]; then
    sed -i.bak "s/'workbench-ui', 'config'/'config'/g" src/server.ts || true
    rm -f src/server.ts.bak || true
    git add src/server.ts || true
    if ! git diff --cached --quiet; then
      git commit -m "chore: adjust config paths after extraction"
      git push
    fi
  fi
)

echo "[backend] Staging removal of workbench-ui from backend repo ..."
git rm -r workbench-ui || true
git add -A
echo "[backend] Creating commit ..."
git commit -m "chore(workbench): extract to $NEW_REPO"

cat <<EOT
Done.

Next steps:
- Open a PR in this backend repo to remove workbench-ui (already committed locally).
- Share the new repo URL: https://github.com/$NEW_REPO
- In the new repo, ensure env uses REPO_ENV_MASTER_PATH for local dev or add a local .env.master.
EOT

