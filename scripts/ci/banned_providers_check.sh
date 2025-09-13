#!/usr/bin/env bash
set -euo pipefail

# Enforce Portkey+OpenRouter virtual key strategy:
# - Ban direct OpenAI/Anthropic SDK usage in application code
# - Ban vendor API keys in code/scripts
#
# Allowed: docs, examples, and a future dedicated gateway adapter folder if whitelisted.
# Strictness: ENFORCE_STRICT=1 to fail; default warn-only.

STRICT=${ENFORCE_STRICT:-0}
fail=0

warn() { echo "[LLM-GUARD][WARN] $*"; }
err()  { echo "[LLM-GUARD][ERROR] $*"; fail=1; }

SEARCH_PATHS=(app sophia-intel-app builder-agno-system)

# 1) Ban direct provider SDK imports in code paths
if rg -n "^\s*import\s+openai|^\s*from\s+openai\s+import|^\s*import\s+anthropic|^\s*from\s+anthropic\s+import" "${SEARCH_PATHS[@]}" 2>/dev/null; then
  ${STRICT} -eq 1 && err "Direct provider SDK imports found (use Portkey gateway)" || warn "Direct provider SDK imports detected"
fi

# 2) Ban vendor API key variables in code/scripts
if rg -n "OPENAI_API_KEY|ANTHROPIC_API_KEY" "${SEARCH_PATHS[@]}" 2>/dev/null; then
  ${STRICT} -eq 1 && err "Vendor API keys referenced in code (use PORTKEY_API_KEY only)" || warn "Vendor key references detected in code"
fi

# 3) Recommend presence of Portkey usage (optional informational)
if ! rg -n "portkey|openrouter" app 2>/dev/null | head -n1 >/dev/null; then
  warn "No obvious Portkey/OpenRouter references in backend code (ensure gateway in use)"
fi

if [[ ${STRICT} -eq 1 && ${fail} -ne 0 ]]; then
  exit 2
fi
exit 0

