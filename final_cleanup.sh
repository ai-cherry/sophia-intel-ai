#!/bin/bash

echo 'FINAL GIT CLEANUP'
echo '================='

cd ~/sophia-intel-ai

# Update main
git checkout main
git pull origin main

echo ''
echo 'Current status:'
git status --short

echo ''
echo 'Local branches:'
git branch

echo ''
echo 'To delete AI remote branches, run:'
echo 'git push origin --delete ai/manus-smoke-20250812-194929'
echo 'git push origin --delete auto/add-a-comment-to-readmemd'
echo 'git push origin --delete auto/add-a-task-priority-feature'
echo 'git push origin --delete auto/add-a-task-priority-feature-to'
echo 'git push origin --delete auto/deploy-pr-#202-to-flyio'
echo 'git push origin --delete codex/analyze-codebase-and-provide-feedback'
echo 'git push origin --delete codex/analyze-codebase-and-provide-feedback-65trup'
echo 'git push origin --delete codex/analyze-codebase-and-provide-feedback-ejfd7m'
echo 'git push origin --delete codex/design-deployment-plan-for-ai-agent-swarms'
