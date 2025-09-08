#!/usr/bin/env bash
set -euo pipefail

violations=()
if rg -n "^app/artemis/" -S --hidden --no-heading >/dev/null 2>&1; then
  violations+=("app/artemis/** detected in repo (not allowed)")
fi
if rg -n "artemis_server_standalone\.py|bin/artemis-" -S --hidden --no-heading >/dev/null 2>&1; then
  violations+=("Artemis server binaries detected (not allowed)")
fi

if (( ${#violations[@]} > 0 )); then
  echo "❌ Artemis-specific code must live in ai-cherry/artemis-cli:" >&2
  for v in "${violations[@]}"; do echo "  - $v" >&2; done
  exit 1
fi

echo "✅ No Artemis-specific code paths detected"

