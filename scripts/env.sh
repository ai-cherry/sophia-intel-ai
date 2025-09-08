#!/usr/bin/env bash
# shellcheck shell=bash
# Unified environment loader for local shells and CI
# Usage: source scripts/env.sh [--quiet]

set -euo pipefail
QUIET=${1:-}

# Resolve repo root robustly across bash/zsh and when sourced
_resolve_script() {
  if [ -n "${BASH_SOURCE:-}" ]; then
    printf '%s' "${BASH_SOURCE[0]}"
  elif [ -n "${ZSH_VERSION:-}" ]; then
    # zsh: path to currently sourced script
    printf '%s' "${(%):-%x}"
  else
    # Fallback: not reliable when sourced, but better than nothing
    printf '%s' "$0"
  fi
}

root_dir() {
  # Prefer git root when available
  if command -v git >/dev/null 2>&1; then
    local gr
    gr=$(git rev-parse --show-toplevel 2>/dev/null || true)
    if [ -n "$gr" ]; then printf '%s' "$gr"; return; fi
  fi
  # Fallback to script location
  local scr
  scr=$(_resolve_script)
  cd "$(dirname "$scr")/.." 2>/dev/null || cd "$(pwd)"
  pwd -P
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

load_file "$HOME/.config/artemis/env"
load_file "$ROOT/.env"
load_file "$ROOT/.env.local"

[[ -n "$QUIET" ]] || echo "Environment loaded. Keys now available in this shell."
