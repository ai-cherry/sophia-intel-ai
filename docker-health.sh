#!/usr/bin/env bash
set -euo pipefail

echo "Health: API" && curl -sf http://localhost:8003/health >/dev/null && echo OK
echo "Health: UI" && curl -sf http://localhost:3000 >/dev/null && echo OK
echo "Health: Telemetry" && curl -sf http://localhost:5003/api/telemetry/health >/dev/null && echo OK
echo "Health: MCP Memory" && curl -sf http://localhost:8081/health >/dev/null && echo OK
echo "Health: MCP FS" && curl -sf http://localhost:8082/health >/dev/null && echo OK
echo "Health: MCP Git" && curl -sf http://localhost:8084/health >/dev/null && echo OK

echo "All health checks passed."

