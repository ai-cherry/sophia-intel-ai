#!/usr/bin/env bash
set -euo pipefail

# Whitelist of allowed root-level markdown files
whitelist=(
  "README.md" "QUICKSTART.md" "ARCHITECTURE.md" "API_REFERENCE.md"
  "DEPLOYMENT_GUIDE.md" "INTEGRATIONS.md" "CHANGELOG.md"
  "CONTRIBUTING.md" "TROUBLESHOOTING.md" "SECURITY.md" "ROADMAP.md"
  "LOCAL_DEV_AND_DEPLOYMENT.md"
)

allowed_set=$(printf '%s\n' "${whitelist[@]}" | sort)

violations=()
count=0
for f in *.md; do
  [[ -e "$f" ]] || continue
  count=$((count+1))
  if ! grep -qxF "$f" <<< "$allowed_set"; then
    violations+=("$f")
  fi
done

# hard cap at 15 root markdown files
if (( count > 15 )); then
  echo "❌ Too many root markdown files ($count). Max allowed: 15" >&2
  exit 1
fi

if (( ${#violations[@]} > 0 )); then
  echo "❌ Non-whitelisted root markdown files detected:" >&2
  for v in "${violations[@]}"; do echo "  - $v" >&2; done
  exit 1
fi

echo "✅ Root markdown policy check passed"

