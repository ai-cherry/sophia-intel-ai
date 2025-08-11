#!/usr/bin/env bash
set -e

# Script to flip linters from warning to blocking mode
# Run this when you're ready to enforce strict linting

echo "🔧 Hardening linters to blocking mode..."

# Update checks.yml to make linters blocking
cat > .github/workflows/checks.yml << 'EOF'
name: CI Checks

on:
  pull_request:
    branches: [ main ]
  push:
    branches: [ main ]

jobs:
  lint-format-test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements.dev.txt

      - name: GitHub CLI auth smoke
        run: |
          gh auth status || (echo "::warning::gh not logged in in CI context (fine for PRs from forks)"; exit 0)

      - name: Run linters (BLOCKING)
        run: |
          ruff check .
          black --check .

      - name: Run tests
        run: pytest -q --maxfail=5 --disable-warnings
EOF

echo "✅ Linters are now BLOCKING in CI/CD"
echo ""
echo "To apply:"
echo "  1. Review changes: git diff .github/workflows/checks.yml"
echo "  2. Commit: git add .github/workflows/checks.yml && git commit -m 'chore: make linters blocking'"
echo "  3. Push: git push"
echo ""
echo "Note: This will prevent merges if code doesn't pass ruff and black checks."