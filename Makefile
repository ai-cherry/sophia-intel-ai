.PHONY: dev-docker dev-native stop logs status clean

ROOT := $(shell pwd)

dev-docker: ## Start full stack via Docker (API 8000, UI 3000, MCP 8081/8082/8084)
	@bash scripts/ports/check_conflicts.sh || { echo "Resolve port conflicts in infra/ports.env, then retry."; exit 2; }
	docker compose -f infra/docker-compose.yml --profile dev up -d
	@echo "→ UI:  http://localhost:3000"
	@echo "→ API: http://localhost:8000/api/health"

dev-native: ## Start API+UI+MCP locally (no Docker)
	@bash scripts/ports/check_conflicts.sh || { echo "Resolve port conflicts in infra/ports.env, then retry."; exit 2; }
	bash scripts/dev/start_local_unified.sh

stop: ## Stop Docker stack
	docker compose -f infra/docker-compose.yml down || true

logs: ## Tail Docker logs
	docker compose -f infra/docker-compose.yml logs -f --tail=200

status: ## Quick health checks
	@curl -sf http://localhost:8000/api/health >/dev/null 2>&1 && echo "API 8000: OK" || echo "API 8000: DOWN"
	@curl -sf http://localhost:3000 >/dev/null 2>&1 && echo "UI 3000: OK" || echo "UI 3000: DOWN"
	@curl -sf http://localhost:8081/health >/dev/null 2>&1 && echo "MCP Memory 8081: OK" || echo "MCP Memory 8081: DOWN"
	@curl -sf http://localhost:8082/health >/dev/null 2>&1 && echo "MCP FS 8082: OK" || echo "MCP FS 8082: DOWN"
	@curl -sf http://localhost:8084/health >/dev/null 2>&1 && echo "MCP Git 8084: OK" || echo "MCP Git 8084: DOWN"

clean: stop ## Remove dangling resources
	@echo "Clean complete"
