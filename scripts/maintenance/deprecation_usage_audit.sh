#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")"/../.. && pwd)
REPORT="$ROOT_DIR/logs/deprecation_usage_report.md"

shopt -s extglob

echo "Scanning for deprecated/legacy/old markers (fast ripgrep-based)..." >&2

# Collect candidates via name and content markers into temp files (macOS bash compatible)
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
rg --files -S \
  -g '!node_modules/**' -g '!.git/**' -g '!**/__pycache__/**' -g '!.venv/**' -g '!venv/**' -g '!dist/**' -g '!build/**' -g '!out/**' -g '!**/.next/**' \
  | rg -i -n '(deprecated|legacy|obsolete|old)' || true >"$tmpdir/name_hits.txt"

rg -n --no-heading -S \
  -g '!node_modules/**' -g '!.git/**' -g '!**/__pycache__/**' -g '!.venv/**' -g '!venv/**' -g '!dist/**' -g '!build/**' -g '!out/**' -g '!**/.next/**' \
  -e '@deprecated|\bDEPRECATED\b|\bDeprecated\b|#\s*deprecated|//\s*deprecated' \
  | cut -d: -f1 | sort -u >"$tmpdir/content_hits.txt" || true

awk 'NF{print}' "$tmpdir/name_hits.txt" "$tmpdir/content_hits.txt" | sort -u >"$tmpdir/candidates.txt"

readarray -t candidates <"$tmpdir/candidates.txt" 2>/dev/null || candidates=( $(cat "$tmpdir/candidates.txt") )

build_terms() {
  local path="$1"
  local base fname stem snake pascal
  fname=$(basename -- "$path")
  stem="${fname%.*}"
  echo "$stem"
  echo "$fname"
  if [[ "$stem" == *"_"* ]]; then
    pascal=$(python3 - "$stem" <<'PY'
import sys
s=sys.argv[1]
print(''.join(p.capitalize() for p in s.split('_')))
PY
)
    [[ -n "$pascal" ]] && echo "$pascal"
  else
    snake=$(python3 - "$stem" <<'PY'
import re,sys
s=sys.argv[1]
print(re.sub(r'(?<!^)(?=[A-Z])','_',s).lower())
PY
)
    [[ -n "$snake" && "$snake" != "$stem" ]] && echo "$snake"
  fi
}

echo "# Deprecation Usage Audit" > "$REPORT"
echo >> "$REPORT"
echo "This report lists files flagged by name/content as deprecated/legacy/old and counts references via import/text search using ripgrep." >> "$REPORT"
echo >> "$REPORT"

zero_count=0
total=${#candidates[@]}

echo "## Detailed Results" >> "$REPORT"
for path in "${candidates[@]}"; do
  terms=()
  while IFS= read -r t; do terms+=("$t"); done < <(build_terms "$path" | sort -u)
  sum=0
  for t in "${terms[@]}"; do
    # Count references excluding the candidate file itself
    c=$(rg -n -S -g '!node_modules/**' -g '!.git/**' -g '!**/__pycache__/**' -g '!.venv/**' -g '!venv/**' -g '!dist/**' -g '!build/**' -g '!out/**' -g '!**/.next/**' "${t}" | grep -v "^${path//./\.}:" | wc -l | awk '{print $1}') || c=0
    sum=$((sum + c))
  done
  rel="$path"
  echo "### \\`$rel\\` — references: $sum" >> "$REPORT"
  if [[ "$sum" -eq 0 ]]; then
    echo "- No references found." >> "$REPORT"
    echo >> "$REPORT"
    zero_count=$((zero_count + 1))
  else
    # Show a few files referencing any of the terms
    rg -n -S -g '!node_modules/**' -g '!.git/**' -g '!**/__pycache__/**' -g '!.venv/**' -g '!venv/**' -g '!dist/**' -g '!build/**' -g '!out/**' -g '!**/.next/**' "$(printf '%s|' "${terms[@]}")ZZZ" \
      | grep -v "^${path//./\.}:" | cut -d: -f1 | sort | uniq -c | sort -nr | head -10 \
      | awk '{print "- `"$2"` — "$1}' >> "$REPORT" || true
    echo >> "$REPORT"
  fi
done

sed -i '' "1i\\
## Summary\\n- Candidates with zero references: ${zero_count}\\n- Total candidates: ${total}\\n\\n" "$REPORT" 2>/dev/null || \
awk -v zc="$zero_count" -v tot="$total" 'NR==1{print; print ""; print "## Summary\n- Candidates with zero references: "zc"\n- Total candidates: "tot""\n"; next}1' "$REPORT" >"$REPORT.tmp" && mv "$REPORT.tmp" "$REPORT"

echo "Wrote report: $REPORT" >&2
