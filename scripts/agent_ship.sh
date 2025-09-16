#!/usr/bin/env bash
set -euo pipefail

# agent_ship.sh — dead-simple agent commit/push helper
# Usage:
#   ./scripts/agent_ship.sh "feat: update memory retrieval"
# Behavior:
#   - Ensures we are on a non-default branch (creates agent/<date>-<slug> if on default)
#   - Adds all changes, commits with the provided message (or a default)
#   - Pushes to origin and prints next steps
#   - auto-pr-on-push workflow will open a draft PR automatically for agent/* branches

msg=${1:-"agent: automated update"}

branch=$(git rev-parse --abbrev-ref HEAD)
default_branch=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo main)

slug() { echo "$1" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g;s/^-+|-+$//g' | cut -c1-32; }

if [ "$branch" = "$default_branch" ]; then
  ts=$(date +%Y%m%d-%H%M%S)
  new_branch="agent/${ts}-$(slug "$msg")"
  echo "On default branch '$default_branch'. Creating '$new_branch'..."
  git checkout -b "$new_branch"
  branch="$new_branch"
fi

git add -A
if ! git diff --cached --quiet; then
  git commit -m "$msg"
else
  echo "No staged changes to commit. Exiting."; exit 0
fi

git push -u origin "$branch"
echo
echo "Pushed to $branch. If the branch matches agent/**, a draft PR will open automatically via GitHub Actions."
echo "Repo: $(git config --get remote.origin.url)"
