#!/bin/bash

# Git Repository Cleanup Script
set -e

echo '🧹 Git Repository Cleanup for sophia-intel-ai'
echo '============================================='

cd ~/sophia-intel-ai

echo 'Current branch: '$(git branch --show-current)

# Stash changes
echo 'Stashing local changes...'
git stash push -m 'Cleanup stash '$(date +%Y%m%d-%H%M%S) || echo 'Nothing to stash'

# Update main
echo 'Updating main branch...'
git checkout main
git pull origin main

# Check divergence
echo 'Checking feature branch status...'
AHEAD=$(git rev-list --count main..origin/feature/cli-swarm-command-center 2>/dev/null || echo 0)
echo 'Feature branch has '$AHEAD' unique commits'

# Show branches
echo 'Local branches:'
git branch

echo 'Done! Current status:'
git status --short
