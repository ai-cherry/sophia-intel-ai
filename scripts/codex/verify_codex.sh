#!/usr/bin/env bash
set -euo pipefail

pass() { echo -e "✅ $*"; }
warn() { echo -e "⚠️  $*"; }
fail() { echo -e "❌ $*"; exit 1; }

echo "Verifying Codex CLI setup..."

if ! command -v codex >/dev/null 2>&1; then
  warn "codex not found on PATH. Try: arch -arm64 brew install codex-cli OR arch -arm64 npm install -g @codex/cli"
  exit 1
fi
pass "codex found: $(which codex)"

ARCH_INFO=$(file "$(command -v codex)" || true)
echo "$ARCH_INFO" | grep -qi "arm64" && pass "Binary is ARM64" || warn "Binary may not be ARM64: $ARCH_INFO"

if codex --version >/dev/null 2>&1; then
  pass "codex --version runs"
else
  warn "codex --version failed"
fi

KEY_VAR=""
if [[ -n "${CODEX_API_KEY:-}" ]]; then
  KEY_VAR="CODEX_API_KEY"
elif [[ -n "${OPENAI_API_KEY:-}" ]]; then
  KEY_VAR="OPENAI_API_KEY"
fi

if [[ -z "$KEY_VAR" ]]; then
  warn "No CODEX_API_KEY or OPENAI_API_KEY set in this shell. Run: source ~/.zshrc (or add with scripts/codex/setup_codex_key.sh <VAR_NAME>)"
else
  pass "$KEY_VAR present in environment"
fi

echo "Attempting a minimal chat call (will not fail the script if it errors)"
set +e
codex chat -m gpt-5-codex -p "ping" >/dev/null 2>&1
RET=$?
set -e
if [[ "$RET" -eq 0 ]]; then
  pass "Chat call succeeded"
else
  warn "Chat call failed (network or auth). Check key and connectivity."
fi

echo "Verification complete."
