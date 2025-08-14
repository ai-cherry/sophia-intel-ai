#!/usr/bin/env bash
set -euo pipefail
: "${NEON_DATABASE_URL:?MISSING NEON_DATABASE_URL}"
echo "psql -> select now()"
PGCONNECT_TIMEOUT=8 psql "$NEON_DATABASE_URL" -c "select current_database() as db, now() as ts" -tA | sed 's/|/,/' | head -n1

