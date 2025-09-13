#!/usr/bin/env bash
# shellcheck shell=bash
# Unified environment loader for local shells and CI
# Usage: source scripts/env.sh [--quiet]

set -euo pipefail
QUIET=${1:-}

root_dir() {
  cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P
}

ROOT="$(root_dir)"

load_file() {
  local f="$1"
  [[ -f "$f" ]] || return 0
  while IFS= read -r line; do
    [[ -z "$line" || "$line" =~ ^# || "$line" != *"="* ]] && continue
    key="${line%%=*}"; val="${line#*=}"
    export "$key"="$val"
  done < "$f"
  [[ -n "$QUIET" ]] || echo "+ loaded: $f"
}

load_file "$ROOT/.env"
load_file "$ROOT/.env.local"

[[ -n "$QUIET" ]] || echo "Environment loaded. Keys now available in this shell."
