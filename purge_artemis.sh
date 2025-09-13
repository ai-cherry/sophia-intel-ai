#!/bin/bash
set -e

echo '🔥 PURGING ALL SOPHIA REFERENCES FROM SOPHIA INTEL AI'
echo '======================================================='

# Phase 1: Remove all Sophia files and directories
echo 'Phase 1: Removing Sophia files and directories...'

# Remove main Sophia directories
rm -rf sophia sophia-v2 sophia-* 2>/dev/null || true

# Remove all JSON files with sophia in name
find . -name '*sophia*.json' -type f -delete 2>/dev/null || true

# Remove all sophia-related archives
find . -name '*sophia*.tar.gz' -type f -delete 2>/dev/null || true
find . -name '*sophia*.zip' -type f -delete 2>/dev/null || true

# Remove sophia files from app directory
find app -name '*sophia*' -type f -delete 2>/dev/null || true

# Remove sophia from tests
find tests -name '*sophia*' -type f -delete 2>/dev/null || true
rm -rf tests/sophia 2>/dev/null || true

# Remove sophia from docs
find docs -name '*sophia*' -type f -delete 2>/dev/null || true

# Remove sophia from scripts
find scripts -name '*sophia*' -type f -delete 2>/dev/null || true

# Remove sophia from k8s
rm -rf k8s/sophia 2>/dev/null || true

# Remove sophia from infrastructure
find infrastructure -name '*sophia*' -type f -delete 2>/dev/null || true

# Remove sophia from config
find config -name '*sophia*' -type f -delete 2>/dev/null || true

# Remove sophia from monitoring
find monitoring -name '*sophia*' -type f -delete 2>/dev/null || true

# Remove sophia from helm charts
find helm -name '*sophia*' -type f -delete 2>/dev/null || true

echo '✅ Sophia files removed'

echo ''
echo '======================================================='
echo '✅ SOPHIA HAS BEEN COMPLETELY PURGED FROM THE SYSTEM'
echo '======================================================='
