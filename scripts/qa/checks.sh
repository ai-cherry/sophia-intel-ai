#!/usr/bin/env bash

set -e

echo "=== Running QA Checks ==="

# Run ruff for linting
echo "Running Ruff linter..."
if command -v ruff &> /dev/null; then
    ruff check . --select=E,F,W
    echo "✅ Ruff linting passed"
else
    echo "⚠️ Ruff not installed, skipping linting"
fi

# Run mypy for type checking
echo "Running MyPy type checking..."
if command -v mypy &> /dev/null; then
    mypy --ignore-missing-imports .
    echo "✅ MyPy type checking passed"
else
    echo "⚠️ MyPy not installed, skipping type checking"
fi

# Run pytest for unit tests
echo "Running pytest unit tests..."
if command -v pytest &> /dev/null; then
    pytest -q
    echo "✅ Pytest tests passed"
else
    echo "⚠️ pytest not installed, skipping tests"
fi

echo
echo "All QA checks completed."
