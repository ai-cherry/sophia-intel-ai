#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && cd .. && pwd)
HOMEBREW_PREFIX="/opt/homebrew/bin"
APPLE_PORTS=(3000 8000 8080 8081 8082 8084)

info() { printf '\033[1;34m[preflight]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[preflight]\033[0m %s\n' "$*"; }
err()  { printf '\033[1;31m[preflight]\033[0m %s\n' "$*"; }

port_in_use() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    lsof -Pi :"$port" -sTCP:LISTEN -t >/dev/null 2>&1
  else
    return 1
  fi
}

info "Running Apple Silicon checks for sophia-intel-ai..."

if [[ ":$PATH:" != *":$HOMEBREW_PREFIX:"* ]]; then
  warn "PATH missing $HOMEBREW_PREFIX. Add 'export PATH=$HOMEBREW_PREFIX:\\$PATH' to your shell profile."
else
  info "Homebrew prefix present in PATH."
fi

ARCH=$(uname -m 2>/dev/null || echo unknown)
if [[ "$ARCH" != "arm64" ]]; then
  warn "Host architecture is $ARCH (expected arm64)."
else
  info "Host architecture: arm64"
fi

if command -v xcode-select >/dev/null 2>&1; then
  if xcode-select -p >/dev/null 2>&1; then
    info "Command Line Tools path: $(xcode-select -p)"
  else
    warn "xcode-select active developer dir unset. Run 'sudo xcode-select --switch /Library/Developer/CommandLineTools'."
  fi
else
  warn "xcode-select missing. Install via 'xcode-select --install'."
fi

if command -v node >/dev/null 2>&1; then
  node_arch=$(node -p 'process.arch' 2>/dev/null || echo unknown)
  info "Node $(node -v) (arch $node_arch)"
  if [[ "$node_arch" != "arm64" ]]; then
    warn "Node is not an arm64 build; reinstall through nvm/asdf."
  fi
else
  warn "Node not found; install via nvm/asdf if you plan to run frontend tooling."
fi

PY_CMD=${PYTHON_BIN:-python3}
if command -v "$PY_CMD" >/dev/null 2>&1; then
  info "Python: $($PY_CMD -V 2>&1)"
  if ! "$PY_CMD" -c "import ssl" >/dev/null 2>&1; then
    warn "Python SSL import failed. Rebuild Python with Homebrew OpenSSL headers."
  fi
else
  warn "python3 not found; backend scripts may fail."
fi

if ! command -v mkcert >/dev/null 2>&1; then
  warn "mkcert not installed. Install with 'brew install mkcert' for local HTTPS certificates."
else
  info "mkcert installed."
fi

if command -v docker >/dev/null 2>&1; then
  info "Docker: $(docker --version 2>/dev/null)"
  if [[ "${TEST_HOST_DOCKER:-0}" == "1" ]]; then
    info "Testing host.docker.internal reachability (TEST_HOST_DOCKER=1)"
    docker run --rm alpine sh -lc "apk add --no-cache curl >/dev/null && curl -s http://host.docker.internal:8080" >/dev/null 2>&1 || \
      warn "Unable to reach host.docker.internal:8080 from container."
  fi
else
  warn "Docker not installed. Consider Docker Desktop, Colima, or OrbStack."
fi

for port in "${APPLE_PORTS[@]}"; do
  if port_in_use "$port"; then
    warn "Port $port currently occupied. Use 'sudo lsof -i :$port' and 'kill -15 <PID>'."
  else
    info "Port $port available."
  fi
done

NEXT_CACHE_PATHS=("$ROOT_DIR/.next" "$ROOT_DIR/workbench-ui/.next")
for cache_path in "${NEXT_CACHE_PATHS[@]}"; do
  if [[ -d "$cache_path" ]]; then
    if [[ "${RESET_NEXT_CACHE:-0}" == "1" ]]; then
      info "RESET_NEXT_CACHE=1 -> deleting $cache_path"
      rm -rf "$cache_path"
    else
      warn "Next.js cache detected at $cache_path. Remove it if UI behaviour looks stale."
    fi
  fi
done

MSW_FILES=("$ROOT_DIR/public/mockServiceWorker.js" "$ROOT_DIR/workbench-ui/public/mockServiceWorker.js")
for msw in "${MSW_FILES[@]}"; do
  if [[ -f "$msw" ]]; then
    warn "Mock Service Worker present ($msw). Ensure it is disabled outside development."
  fi
done

echo
info "Preflight complete. Follow-up commands:"
cat <<'EON'
  - Flush DNS if hostnames misbehave: sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder
  - Issue trusted HTTPS certs: brew install mkcert && mkcert -install && mkcert localhost 127.0.0.1 ::1
  - For x86-only containers: colima start --arch x86_64 (switch back to arm64 when done)
EON
