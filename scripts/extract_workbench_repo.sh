#!/usr/bin/env bash
set -euo pipefail

# History-preserving extraction of workbench-ui into a standalone repo or worktree.
# This script does NOT push to remotes by default; it prints next steps.

PREFIX_DIR=${1:-workbench-ui}
SPLIT_BRANCH=${2:-workbench-ui-split}
TARGET_DIR=${3:-"../worktrees/workbench-ui"}

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Run from within the repository root" >&2
  exit 1
fi

if [ ! -d "$PREFIX_DIR" ]; then
  echo "Directory not found: $PREFIX_DIR" >&2
  exit 1
fi

echo "[extract] Creating subtree split for '$PREFIX_DIR' into branch '$SPLIT_BRANCH'..."
git subtree split --prefix="$PREFIX_DIR" -b "$SPLIT_BRANCH"

echo "[extract] Adding worktree at: $TARGET_DIR"
mkdir -p "$(dirname "$TARGET_DIR")"
git worktree add "$TARGET_DIR" "$SPLIT_BRANCH" || true

cat <<'EOT'
Done.

Next steps:
1) Create a new remote repository (e.g., GitHub) and note its URL.
2) From the worktree directory, set remote and push:
   cd ../worktrees/workbench-ui
   git remote add origin <NEW_REMOTE_URL>
   git push -u origin HEAD:main

3) In this (backend) repo, open a PR to remove the 'workbench-ui' directory:
   git rm -r workbench-ui
   git commit -m "chore(workbench): extract to separate repo"

4) Merge the PR and share the new repo URL and worktree instructions with the team.

Rollback:
- If needed, delete the worktree and branch:
   git worktree remove ../worktrees/workbench-ui
   git branch -D workbench-ui-split
EOT
