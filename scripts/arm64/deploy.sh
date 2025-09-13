#!/bin/bash
# deploy.sh - Single ARM64-native deployment for local dev
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; BLUE='\033[0;34m'; NC='\033[0m'

# Resolve repo root relative to this script
ROOT_DIR="$(cd "$(dirname "$0")"/../.. && pwd)"
cd "$ROOT_DIR"

echo -e "${BLUE}Sophia ARM64-Native Deployment${NC}"
echo "================================"

if [[ $(uname -m) != "arm64" ]]; then
  echo -e "${RED}ERROR: Requires Apple Silicon (M1/M2/M3)${NC}"; exit 1
fi

mkdir -p "$ROOT_DIR/.pids" "$ROOT_DIR/logs"

check_service() {
  local name=$1 port=$2
  if lsof -i :$port >/dev/null 2>&1; then
    echo -e "${GREEN}✅ $name running on port $port${NC}"; return 0
  else
    echo -e "${RED}❌ $name not running on port $port${NC}"; return 1
  fi
}

check_redis() {
  if command -v redis-cli >/dev/null 2>&1; then
    if redis-cli -h 127.0.0.1 -p 6379 ping >/dev/null 2>&1; then
      echo -e "${GREEN}✅ Redis responding on 127.0.0.1:6379${NC}"; return 0
    fi
  fi
  check_service "Redis" 6379; return $?
}

check_postgres() {
  if command -v pg_isready >/dev/null 2>&1; then
    if pg_isready -q -h 127.0.0.1 -p 5432; then
      echo -e "${GREEN}✅ PostgreSQL is ready on 127.0.0.1:5432${NC}"; return 0
    fi
    if pg_isready -q; then
      echo -e "${GREEN}✅ PostgreSQL is ready (UNIX socket)${NC}"; return 0
    fi
  fi
  check_service "PostgreSQL" 5432; return $?
}

echo -e "\n${BLUE}Starting Services...${NC}"

# Redis
if ! check_redis; then
  echo "Starting Redis..."; brew services start redis || true; sleep 2; check_service "Redis" 6379 || true
fi

# PostgreSQL
if ! check_postgres; then
  echo "Starting PostgreSQL..."; brew services start postgresql@15 || true; sleep 2; check_service "PostgreSQL" 5432 || true
fi

# Weaviate (optional)
if ! check_service "Weaviate" 8080; then
  if [ -x "$HOME/sophia-services/start_weaviate.sh" ]; then
    echo "Starting Weaviate..."; nohup "$HOME/sophia-services/start_weaviate.sh" > "$ROOT_DIR/logs/weaviate.log" 2>&1 &
    echo $! > "$ROOT_DIR/.pids/weaviate.pid"; sleep 3
  else
    echo "(Weaviate not configured; skip)"
  fi
fi

echo -e "\n${BLUE}Setting up Python environment...${NC}"
if [ ! -d "$ROOT_DIR/.venv" ]; then
  echo "Missing .venv. Run scripts/arm64/setup_arm64.sh first."; exit 1
fi
source "$ROOT_DIR/.venv/bin/activate"

echo -e "\n${BLUE}Starting Sophia API...${NC}"
if ! check_service "Sophia API" 8003; then
  nohup python -m uvicorn app.main_unified:app --host 0.0.0.0 --port 8003 --reload > "$ROOT_DIR/logs/api.log" 2>&1 &
  echo $! > "$ROOT_DIR/.pids/api.pid"; sleep 3; check_service "Sophia API" 8003 || true
fi

# UI (optional)
if [ -d "$ROOT_DIR/sophia-intel-app" ]; then
  echo -e "\n${BLUE}Starting UI...${NC}"
  if ! check_service "UI" 3000; then
    if command -v npm >/dev/null 2>&1; then
      (cd "$ROOT_DIR/sophia-intel-app" && nohup npm run dev > "$ROOT_DIR/logs/ui.log" 2>&1 & echo $! > "$ROOT_DIR/.pids/ui.pid") || echo "UI failed to start (npm?)"
      sleep 5; check_service "UI" 3000 || true
  else
      echo "npm not found; skipping UI"
    fi
  fi
fi

echo -e "\n${BLUE}Deployment Status:${NC}\n=================="
check_redis
check_postgres
check_service "Weaviate" 8080
check_service "Sophia API" 8003
check_service "UI" 3000

echo -e "\n${GREEN}Access Points:${NC}"
echo "• API: http://localhost:8003"
echo "• UI: http://localhost:3000"
echo "• Weaviate: http://localhost:8080"
echo "• CLI: sophia <command> (after setup_cli.sh)"

echo -e "\n${BLUE}To stop all services:${NC}"
echo "scripts/arm64/stop.sh"
