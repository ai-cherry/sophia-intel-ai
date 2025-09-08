#!/bin/bash
# Shared environment loader for Sophia Intel AI scripts
set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_success() { echo -e "${GREEN}✅${NC} $1"; }

# Load .env if present
if [ -f ".env" ]; then
  # export variables set in .env
  set -a
  . ./.env
  set +a
  log_info ".env loaded"
fi

