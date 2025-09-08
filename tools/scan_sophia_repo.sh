#!/bin/bash
set -euo pipefail

echo "🔍 SCANNING SOPHIA-INTEL-AI REPOSITORY"
echo "======================================"

out_dir="scan_results"
mkdir -p "$out_dir"

echo "Checking for duplicate basenames..."
find . -type f \( -name "*.py" -o -name "*.ts" -o -name "*.tsx" \) \
  | xargs -I {} basename {} \
  | sort | uniq -d > "$out_dir/duplicates.txt" || true

echo "Scanning for suspicious imports..."
rg -n "(^|\s)(from|import)\s+(artemis|super_orchestrator|broken)\b" -g "*.{py,ts,tsx}" \
  > "$out_dir/broken_imports.txt" || true

echo "Listing package manifests..."
ls -la package.json agent-ui/package.json requirements.txt pyproject.toml 2>/dev/null \
  > "$out_dir/package_files.txt" || true

echo "Finding TODO/FIXME/HACK..."
rg -n "TODO|FIXME|HACK|XXX|BUG" -g "*.{py,ts,tsx}" > "$out_dir/todos.txt" || true

echo "Finding empty or stub files (< 100 bytes)..."
find . -type f \( -name "*.py" -o -name "*.ts" -o -name "*.tsx" \) -size -100c \
  > "$out_dir/empty_files.txt" || true

echo "Analyzing directory structure..."
command -v tree >/dev/null 2>&1 && tree -d -L 3 -I 'node_modules|__pycache__|.git|dist|build' > "$out_dir/directory_structure.txt" || true

echo "Collecting config files..."
find . \( -name "*.env*" -o -name "*config*" -o -name "*.ya?ml" \) | head -200 > "$out_dir/config_files.txt" || true

echo "Scanning for potential secrets..."
rg -n "api_key|secret|password|token" -g "*.{py,ts,tsx}" -S \
  | rg -v "\.env|example|template" | head -200 > "$out_dir/security_concerns.txt" || true

echo "Catching bare excepts and catch blocks..."
rg -n "except:\s*$" -g "*.py" > "$out_dir/bare_excepts.txt" || true
rg -n "catch\s*\(" -g "*.{ts,tsx}" > "$out_dir/catch_blocks.txt" || true

echo "Detecting raw '<' in TSX text spans..."
rg -n ">\s*<\s*\d" agent-ui/src -g "*.tsx" > "$out_dir/tsx_lt_text.txt" || true

cat > "$out_dir/REPORT.md" << REPORT
# SOPHIA-INTEL-AI REPOSITORY SCAN REPORT

## Statistics
- Duplicate basenames: $(wc -l < "$out_dir/duplicates.txt")
- Suspicious imports: $(wc -l < "$out_dir/broken_imports.txt")
- TODO/FIXME/etc: $(wc -l < "$out_dir/todos.txt")
- Empty/stub files: $(wc -l < "$out_dir/empty_files.txt")
- Potential secrets (top 200): $(wc -l < "$out_dir/security_concerns.txt")
- Bare excepts: $(wc -l < "$out_dir/bare_excepts.txt")
- TSX raw '< number' instances: $(wc -l < "$out_dir/tsx_lt_text.txt")

## Critical (first 5)
$(sed -n '1,5p' "$out_dir/broken_imports.txt")

## Security (first 5)
$(sed -n '1,5p' "$out_dir/security_concerns.txt")

## TODOs (first 10)
$(sed -n '1,10p' "$out_dir/todos.txt")
REPORT

echo "✅ Scan complete. See $out_dir/REPORT.md"

