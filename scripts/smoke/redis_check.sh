#!/usr/bin/env bash
set -euo pipefail
: "${REDIS_URL:?MISSING REDIS_URL}"
echo "redis-cli -> PING"
redis-cli -u "$REDIS_URL" --raw PING

