#!/usr/bin/env bash
set -euo pipefail

SCRIPTS=$(ls scripts/*.py 2>/dev/null | wc -l | tr -d ' ')
DIRS=$(find . -maxdepth 1 -type d -not -path '*/.*' | wc -l | tr -d ' ')
DOCS=$(find . -name "*.md" | wc -l | tr -d ' ')
SCORE=$((SCRIPTS + DIRS + DOCS))
echo "Fragmentation Score: ${SCORE}"
echo "  - Scripts: ${SCRIPTS}"
echo "  - Dirs:    ${DIRS}"
echo "  - Docs:    ${DOCS}"
echo "Target: < 100"
