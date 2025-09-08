#!/bin/bash
# Sophia Intel AI - Environment Check

echo '=== Checking sophia-intel-ai environment ==='
echo 'Current directory:' $(pwd)
echo ''
echo '=== Git Status ==='
git remote -v
git status --short
echo ''
echo '=== Searching for key files ==='
echo 'CLI files:' 
find . -iname '*cli*' -type f -not -path './node_modules/*' 2>/dev/null | head -5
echo ''
echo 'Grok files:'
find . -iname '*grok*' -type f -not -path './node_modules/*' 2>/dev/null | head -5
echo ''
echo 'Claude/Coder files:'
find . -iname '*claude*' -o -iname '*coder*' -type f -not -path './node_modules/*' 2>/dev/null | head -5
echo ''
echo 'Codex files:'
find . -iname '*codex*' -type f -not -path './node_modules/*' 2>/dev/null | head -5
echo ''
echo '=== Checking for virtual environments ==='
find . -name 'venv' -o -name '.venv' -o -name 'env' -type d 2>/dev/null
echo ''
echo '=== Environment files ==='
ls -la .env* 2>/dev/null
echo ''
echo '=== Main directories ==='
ls -d */ | head -15
