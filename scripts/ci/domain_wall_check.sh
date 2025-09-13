#!/usr/bin/env bash
set -euo pipefail

# Domain wall checks between Sophia (sophia-intel-app + app/api/*) and Builder (builder-agno-system)
# - Ensures Sophia API does not mount Builder routers
# - Ensures Sophia UI does not import from Builder UI and vice versa
# - Ensures API entrypoint consistency
#
# Strictness: set ENFORCE_STRICT=1 to fail on any finding. Default is warn only.

STRICT=${ENFORCE_STRICT:-0}
fail=0

warn() { echo "[DOMAIN-WALL][WARN] $*"; }
err()  { echo "[DOMAIN-WALL][ERROR] $*"; fail=1; }

# 1) Prevent mounting Builder routers in Sophia API
if rg -n "from\s+app\.api\.routers\.builder\s+import\s+router|include_router\(builder_router\)" app/api 2>/dev/null; then
  ${STRICT} -eq 1 && err "Sophia API mounts Builder router (forbidden)" || warn "Sophia API appears to reference Builder router"
fi

# 2) Prevent Sophia UI importing Builder UI and vice versa
if rg -n "from\s+['\"]..?/builder-agno-system|require\(['\"]..?/builder-agno-system" sophia-intel-app 2>/dev/null; then
  ${STRICT} -eq 1 && err "Sophia UI imports Builder UI (forbidden)" || warn "Sophia UI appears to import Builder UI"
fi
if rg -n "from\s+['\"]..?/sophia-intel-app|require\(['\"]..?/sophia-intel-app" builder-agno-system 2>/dev/null; then
  ${STRICT} -eq 1 && err "Builder UI imports Sophia UI (forbidden)" || warn "Builder UI appears to import Sophia UI"
fi

# 3) API entrypoint consistency: prefer uvicorn app.api.unified_server:app
if rg -n "sophia_unified_server\.py|sophia_unified_server:app" infra scripts . 2>/dev/null; then
  ${STRICT} -eq 1 && err "Legacy entrypoint 'sophia_unified_server' still referenced" || warn "Legacy entrypoint references found (consider cleaning up)"
fi

if [[ ${STRICT} -eq 1 && ${fail} -ne 0 ]]; then
  exit 2
fi
exit 0

