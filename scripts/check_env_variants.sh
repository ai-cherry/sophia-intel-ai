#!/usr/bin/env bash
set -euo pipefail

allowed=(".env" ".env.local" ".env.template")
violations=()
for f in .env*; do
  [[ -e "$f" ]] || continue
  keep=false
  for a in "${allowed[@]}"; do
    if [[ "$f" == "$a" ]]; then keep=true; break; fi
  done
  if ! $keep; then violations+=("$f"); fi
done

if (( ${#violations[@]} > 0 )); then
  echo "❌ Unauthorized .env files detected:" >&2
  for v in "${violations[@]}"; do echo "  - $v" >&2; done
  exit 1
fi

echo "✅ Env variants check passed"

