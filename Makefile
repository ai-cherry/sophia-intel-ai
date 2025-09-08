SHELL := /bin/bash

.PHONY: help env.check env.doctor env.doctor.merge env.clean-deprecated env.source keys-check health health-infra mcp-test full-start api-build api-up api-restart dev-mcp-up dev-artemis-up mcp-rebuild ui-up ui-health ui-smoke dev-all nuke-fragmentation rag.start rag.test lint dev-up dev-down dev-shell logs status grok-test swarm-start memory-search mcp-status env-docs artemis-setup refactor.discovery refactor.scan-http refactor.probe refactor.check webui-health router-smoke sophia sophia-start sophia-stop sophia-health sophia-logs sophia-clean sophia-test-integrations next-ui-up doctor-all artemis.sidecar-setup api-dev

help:
	@echo "\033[0;36mMulti-Agent Development Environment\033[0m"
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[0;32m%-18s\033[0m %s\n", $$1, $$2}'

env.check: ## Run environment preflight checks
	python3 scripts/agents_env_check.py || true

env.doctor: ## Diagnose env fragmentation and conflicts
	python3 scripts/env_doctor.py

env.doctor.merge: ## Merge sources into .env.local
	python3 scripts/env_doctor.py --merge

env.clean-deprecated: ## Remove deprecated env examples (keeps .env.template authoritative)
	@for f in .env.example .env.mcp.example .env.sophia.example; do \
		if [ -f $$f ]; then echo "Removing $$f" && rm -f $$f; fi; \
	done; \
	echo "Deprecated env examples removed. Use .env.template + ~/.config/artemis/env"

env.source: ## Source unified environment in current shell (bash/zsh: `source <(make env.source)`)
	@cat scripts/env.sh

keys-check: ## Verify required keys present (local or container)
	@python3 scripts/env_doctor.py | sed -n '/Required keys status:/,/Optional keys/p'

health: ## Run full health check
	@echo "\xF0\x9F\x8F\xA5 Running health check..."
	@python3 scripts/env_doctor.py
	@bash scripts/check_env_variants.sh
	@bash scripts/check_root_docs.sh
	@ruff check . --select F401,F841 --quiet || true
	@echo "\xE2\x9C\x85 Health check complete"

health-infra: ## Check infrastructure services (Redis, Postgres, Weaviate)
	@echo "Checking Redis..."
	@if command -v redis-cli >/dev/null 2>&1; then \
		(redis-cli -h localhost ping || echo "Redis ping failed"); \
	else \
		(nc -z localhost 6379 >/dev/null 2>&1 && echo "Redis port 6379 open" || echo "Redis not reachable on 6379"); \
	fi
	@echo "Checking Postgres..."
	@if command -v pg_isready >/dev/null 2>&1; then \
		pg_isready -h localhost -p 5432 || true; \
	else \
		(nc -z localhost 5432 >/dev/null 2>&1 && echo "Postgres port 5432 open" || echo "Postgres not reachable on 5432"); \
	fi
	@echo "Checking Weaviate..."
	@curl -sf http://localhost:8080/v1/.well-known/ready >/dev/null && echo "Weaviate ready" || echo "Weaviate not ready"

mcp-test: ## Test MCP server connections
	@curl -sf http://localhost:8081/health >/dev/null && echo "\xE2\x9C\x93 Memory MCP" || echo "Memory MCP not responding"
	@curl -sf http://localhost:8082/health >/dev/null && echo "\xE2\x9C\x93 Filesystem MCP" || echo "Filesystem MCP not responding"
	@curl -sf http://localhost:8084/health >/dev/null && echo "\xE2\x9C\x93 Git MCP" || echo "Git MCP not responding"

full-start: ## Start everything in correct order
	@docker compose -f docker-compose.dev.yml up -d redis postgres weaviate
	@sleep 5
	@docker compose -f docker-compose.dev.yml up -d mcp-memory mcp-filesystem-sophia mcp-git
	@sleep 3
	@docker compose -f docker-compose.dev.yml up -d agent-dev
	@echo "\xE2\x9C\x93 Sophia stack running"

dev-mcp-up: ## Start only MCP servers (dev)
	@docker compose -f docker-compose.dev.yml up -d mcp-memory mcp-filesystem-sophia mcp-git

dev-artemis-up: ## Enable Artemis profile (requires ARTEMIS_PATH)
	@if [ -z "$(ARTEMIS_PATH)" ]; then echo "ARTEMIS_PATH not set"; exit 1; fi
	@docker compose -f docker-compose.dev.yml --profile artemis up -d

api-build: ## Build API image (prod compose)
	@docker compose -f docker-compose.yml build api --no-cache

api-up: ## Start API service (prod compose)
	@docker compose -f docker-compose.yml up -d api

api-restart: ## Rebuild and start API (prod compose)
	@$(MAKE) api-build
	@$(MAKE) api-up

mcp-rebuild: ## Rebuild and start MCP services (memory, fs-sophia, git)
	@docker compose -f docker-compose.dev.yml build mcp-memory mcp-filesystem-sophia mcp-git
	@docker compose -f docker-compose.dev.yml up -d mcp-memory mcp-filesystem-sophia mcp-git
	@echo "Checking MCP health..."
	@curl -sf http://localhost:${MCP_MEMORY_PORT:-8081}/health >/dev/null && echo "✓ Memory MCP" || echo "✗ Memory MCP"
	@curl -sf http://localhost:${MCP_FS_SOPHIA_PORT:-8082}/health >/dev/null && echo "✓ FS MCP (Sophia)" || echo "✗ FS MCP (Sophia)"
	@curl -sf http://localhost:${MCP_GIT_PORT:-8084}/health >/dev/null && echo "✓ Git MCP" || echo "✗ Git MCP"

ui-up: ## Start UI backend locally (http://localhost:8000)
	@echo "Starting UI backend on http://localhost:8000"
	@python3 -m uvicorn webui.backend.main:app --host 0.0.0.0 --port 8000

next-ui-up: ## Start Next.js UI (agent-ui) on http://localhost:3000
	@echo "🔗 Ensure NEXT_PUBLIC_API_URL=http://localhost:8003 in agent-ui/.env.local"
	@cd agent-ui && \
		( \
		  if command -v pnpm >/dev/null 2>&1; then \
		    echo "Using pnpm"; pnpm install && pnpm dev; \
		  elif command -v npm >/dev/null 2>&1; then \
		    echo "pnpm not found; falling back to npm"; npm install && npm run dev; \
		  elif command -v yarn >/dev/null 2>&1; then \
		    echo "pnpm/npm not found; using yarn"; yarn install && yarn dev; \
		  else \
		    echo "No package manager found (pnpm/npm/yarn)"; exit 1; \
		  fi \
		)

ui-health: ## Check UI backend health
	@echo "UI backend health:" && (curl -sf http://localhost:8000/health | sed -e 's/^/  /' || (echo "  not responding" && exit 1))

ui-smoke: ## Basic UI tools proxy smoke (FS list in repo root)
	@echo "Invoking FS list via UI backend /tools/invoke..."
	@curl -s -X POST http://localhost:8000/tools/invoke \
		-H 'Content-Type: application/json' \
		-d '{"capability":"fs","scope":"sophia","action":"list","params":{"path":"."}}' || echo "Smoke failed"

dev-all: ## Start infra+MCP and Next.js UI; auto-enable FS Artemis if present
	@echo "Starting Sophia dev environment (infra + MCP + UI)..."
	@bash scripts/dev.sh all
	@if [ -d "$$HOME/artemis-cli" ]; then \\
		echo "Detected $$HOME/artemis-cli — enabling FS Artemis (profile)"; \\
		export ARTEMIS_PATH="$$HOME/artemis-cli"; \\
		docker compose -f docker-compose.dev.yml --profile artemis up -d mcp-filesystem-artemis; \\
		echo "FS Artemis up at http://localhost:$${MCP_FS_ARTEMIS_PORT:-8083}/health"; \\
	else \\
		echo "No ~/artemis-cli detected. Skipping FS Artemis."; \\
	fi
	@echo "\n=== Endpoints ==="; \\
	 echo "Memory MCP:      http://localhost:$${MCP_MEMORY_PORT:-8081}/health"; \\
	 echo "FS (Sophia) MCP: http://localhost:$${MCP_FS_SOPHIA_PORT:-8082}/health"; \\
	 echo "Git MCP:         http://localhost:$${MCP_GIT_PORT:-8084}/health"; \\
	 echo "Sophia UI:       http://localhost:3000/dashboard"; \\
	 echo "Sophia Chat:     http://localhost:3000/chat"; \\
	 if [ -d "$$HOME/artemis-cli" ]; then echo "FS (Artemis) MCP: http://localhost:$${MCP_FS_ARTEMIS_PORT:-8083}/health"; fi; \\
	 echo "\n(Next.js will print \"ready on http://localhost:3000\" when up.)"
	@$(MAKE) next-ui-up

doctor-all: ## Verify keys, infra, MCP, Next.js UI, and optional Artemis chat
	@echo "\n[doctor] Verifying keys..."; \\
	 $(MAKE) -s keys-check || true; \\
	 echo "\n[doctor] Infra health..."; \\
	 $(MAKE) -s health-infra || true; \\
	 echo "\n[doctor] MCP health..."; \\
	 $(MAKE) -s mcp-test || true; \\
	 echo "\n[doctor] API health..."; \\
	 (curl -sf http://localhost:8003/health | sed -e 's/^/  /' || echo "  API not responding") ; \\
	 if [ -d "$$HOME/artemis-cli" ]; then \\
	   echo "\n[doctor] Artemis chat (optional)..."; \\
	   (curl -sf http://localhost:8095/health >/dev/null && echo "✓ Artemis chat: http://localhost:8095/health") || echo "! Artemis chat not responding on 8095"; \\
	 fi; \\
	 echo "\n[doctor] docker compose status (dev)..."; \\
	 docker compose -f docker-compose.dev.yml ps || true

artemis.sidecar-setup: ## One-time: clone Artemis sidecar repo to ~/artemis-cli via SSH
	@bash scripts/setup_artemis_sidecar.sh

api-dev: ## Run Sophia production server locally on port 8003
	uvicorn app.api.production_server:create_production_app --host 0.0.0.0 --port 8003

nuke-fragmentation: ## Nuclear option - force consolidation (DESTRUCTIVE)
	@echo "\xE2\x9A\xA0\xEF\xB8\x8F  This will delete non-canonical files. Ctrl-C to abort..." && sleep 5
	@python3 scripts/nuke_fragmentation.py --confirm

rag.start: ## Start unified API with optional RAG
	./unified-start.sh --with-rag

rag.test: ## Verify RAG services health
	@set -e; \
	for port in 8767 8768; do \
		echo "Testing health on $$port"; \
		curl -sf http://localhost:$$port/health >/dev/null || (echo "Service $$port not healthy" && exit 1); \
	done; \
	echo "RAG services healthy"

lint: ## Lint with ruff (non-failing)
	ruff check . || true

compose.lint: ## Validate docker-compose syntax
	docker compose -f docker-compose.multi-agent.yml config -q

mcp.smoke: ## Build and smoke-check MCP containers (health endpoints)
	@echo "Building MCP images and checking health..."; \
	docker build -f automation/docker/Dockerfile.mcp-filesystem -t sophia-mcp-fs . >/dev/null; \
	docker build -f automation/docker/Dockerfile.mcp-git -t sophia-mcp-git . >/dev/null; \
	docker build -f automation/docker/Dockerfile.mcp-memory -t sophia-mcp-memory . >/dev/null; \
	(docker run --rm -p 8082:8000 sophia-mcp-fs >/dev/null 2>&1 &) && sleep 2 && curl -sf http://localhost:8082/health >/dev/null && echo "FS MCP: OK" && pkill -f 'sophia-mcp-fs' || true; \
	(docker run --rm -p 8084:8000 -e SSH_AUTH_SOCK=$$SSH_AUTH_SOCK -v $$SSH_AUTH_SOCK:$$SSH_AUTH_SOCK sophia-mcp-git >/dev/null 2>&1 &) && sleep 2 && curl -sf http://localhost:8084/health >/dev/null && echo "Git MCP: OK" && pkill -f 'sophia-mcp-git' || true; \
	(docker run --rm -p 8081:8000 sophia-mcp-memory >/dev/null 2>&1 &) && sleep 2 && curl -sf http://localhost:8081/health >/dev/null && echo "Memory MCP: OK" && pkill -f 'sophia-mcp-memory' || true; \
	echo "MCP smoke complete"

ci.smoke: ## CI-friendly smoke: env, compose lint, compile key packages
	@echo "🔎 Running CI smoke checks..."; \
	$(MAKE) env.check; \
	$(MAKE) compose.lint; \
	python3 -c "import compileall,sys; ok=all(compileall.compile_dir(p, quiet=1) for p in ('app','backend','mcp')); print('compileall:', 'OK' if ok else 'FAILED'); sys.exit(0 if ok else 1)"

# Terminal-first multi-agent stack (docker-compose.multi-agent.yml)
dev-up: ## Start multi-agent environment
	bash ./scripts/multi-agent-docker-env.sh up

dev-down: ## Stop multi-agent environment
	bash ./scripts/multi-agent-docker-env.sh down

dev-shell: ## Enter agent-dev shell
	bash ./scripts/multi-agent-docker-env.sh shell

logs: ## Tail logs (optionally: make logs SVC=redis)
	bash ./scripts/multi-agent-docker-env.sh logs $(SVC)

status: ## Show compose status
	bash ./scripts/multi-agent-docker-env.sh status

grok-test: ## One-off Grok test in container
	bash ./scripts/quick-grok-test.sh

swarm-start: ## Start multi-agent swarm (use: make swarm-start TASK="your task")
	@if [[ -z "$(TASK)" ]]; then echo "TASK required: make swarm-start TASK=\"Build feature\""; exit 1; fi
	@docker compose -f docker-compose.multi-agent.yml run --rm agent-dev \
		python3 scripts/sophia.py swarm start --task "$(TASK)" --agents "grok,claude,deepseek"

memory-search: ## Search shared memory (use: make memory-search QUERY="search term")
	@docker compose -f docker-compose.multi-agent.yml run --rm agent-dev \
		python3 scripts/sophia.py memory search "$(QUERY)"

mcp-status: ## Check MCP service health endpoints
	@echo "MCP Memory:   " && (curl -sf http://localhost:8081/health | jq '.' || echo "not responding")
	@echo "MCP FS Sophia:" && (curl -sf http://localhost:8082/health | jq '.' || echo "not responding")
	@echo "MCP FS Artemis:" && (curl -sf http://localhost:8083/health | jq '.' || echo "not responding")
	@echo "MCP Git:      " && (curl -sf http://localhost:8084/health | jq '.' || echo "not responding")

webui-health: ## Verify WebUI backend health
	@curl -sf http://localhost:3001/health | jq '.' || (echo "WebUI not responding" && exit 1)

router-smoke: ## Smoke test router via WebUI backend /agents/complete
	@curl -s -X POST http://localhost:3001/agents/complete \
		-H 'Content-Type: application/json' \
		-d '{"task_type":"generation","messages":[{"role":"user","content":"Say hi in one word"}],"provider":"openrouter","model":"anthropic/claude-3.5-sonnet"}' | jq '.'

clean: ## Clean up Docker resources
	@echo "🧹 Cleaning Docker resources..."
	@docker system prune -f
	@docker volume prune -f

stop-all: ## Stop Sophia dev compose and kill dev processes
	@docker compose -f docker-compose.dev.yml down || true
	@pkill -f "next dev" || true
	@pkill -f "uvicorn" || true

restart-all: ## Restart dev stack (stop-all + dev-all)
	@$(MAKE) stop-all
	@sleep 2
	@$(MAKE) dev-all

env-docs: ## Show environment guide for SSH agent and env files
	@echo "Environment Guide (ENVIRONMENT_GUIDE.md)" && echo "------------------------------"
	@sed -n '1,200p' ENVIRONMENT_GUIDE.md | sed -e 's/^/  /'

artemis-setup: ## Set up artemis agent secure environment
	@echo "🔐 Setting up Artemis agent environment..."
	@mkdir -p ~/.config/artemis
	@chmod 700 ~/.config/artemis
	@if [ ! -f ~/.config/artemis/env ]; then \
		echo "✅ Created ~/.config/artemis/env"; \
		echo "📝 Edit this file and add your API keys"; \
		echo "   Run: vi ~/.config/artemis/env"; \
	else \
		echo "✅ Config already exists: ~/.config/artemis/env"; \
		echo "🔑 $(shell grep -c 'API_KEY=' ~/.config/artemis/env) API keys configured"; \
	fi
	@chmod 600 ~/.config/artemis/env 2>/dev/null || true

# --- Phase 2 refactor helpers ---
refactor.discovery: ## List Python files >50KB in app/
	@python3 scripts/development/refactor_tools.py discover --path app --min-kb 50

refactor.scan-http: ## Scan for requests/httpx/aiohttp imports in app/
	@python3 scripts/development/refactor_tools.py scan-http --path app

refactor.probe: ## Probe import (use: make refactor.probe MODULE=app.pkg.mod)
	@if [[ -z "$(MODULE)" ]]; then echo "MODULE required: make refactor.probe MODULE=app.artemis.agent_factory"; exit 1; fi
	@python3 scripts/development/refactor_tools.py probe-import --module $(MODULE)

refactor.check: ## Quick refactor sanity (env.check + sample probes)
	@$(MAKE) env.check

# === SOPHIA BUSINESS INTELLIGENCE TARGETS ===

sophia: sophia-start ## Alias for sophia-start

sophia-start: ## Start Sophia Business Intelligence (one command)
	@chmod +x scripts/sophia-start.sh
	@bash scripts/sophia-start.sh

sophia-stop: ## Stop all Sophia services
	@echo "🛑 Stopping Sophia services..."
	@pkill -f "uvicorn.*8003" 2>/dev/null || true
	@pkill -f "next.*dev" 2>/dev/null || true
	@docker-compose -f docker-compose.dev.yml stop redis postgres weaviate 2>/dev/null || true
	@echo "✅ Sophia stopped"

sophia-health: ## Check Sophia health and integration status
	@echo "🏥 Sophia Health Check:"
	@echo ""
	@echo "API Health:"
	@curl -sf http://localhost:8003/health | jq '.' 2>/dev/null || echo "  API not responding"
	@echo ""
	@echo "Integration Health:"
	@curl -sf http://localhost:8003/health/integrations | jq '.integrations | to_entries | .[] | "\(.key): \(.value.status)"' 2>/dev/null || echo "  Integration health not available"
	@echo ""
	@echo "Overall Status:"
	@curl -sf http://localhost:8003/health/integrations | jq '{"overall": .overall, "healthy": .healthy_count, "total": .total_integrations}' 2>/dev/null || echo "  Status not available"

sophia-logs: ## View Sophia logs (API and UI)
	@echo "📋 Sophia Logs:"
	@echo ""
	@echo "=== API Logs (last 20 lines) ==="
	@tail -n 20 logs/sophia-api.log 2>/dev/null || echo "No API logs found"
	@echo ""
	@echo "=== UI Logs (last 20 lines) ==="
	@tail -n 20 logs/sophia-ui.log 2>/dev/null || echo "No UI logs found"
	@echo ""
	@echo "For continuous logs: tail -f logs/sophia-*.log"

sophia-clean: sophia-stop ## Clean Sophia data and logs
	@echo "🧹 Cleaning Sophia..."
	@docker-compose -f docker-compose.dev.yml down -v 2>/dev/null || true
	@rm -rf logs/sophia-*.log
	@rm -rf data/
	@rm -rf agent-ui/.next 2>/dev/null || true
	@rm -rf agent-ui/node_modules 2>/dev/null || true
	@echo "✅ Sophia cleaned"

sophia-test-integrations: ## Test Sophia integration connections
	@echo "🧪 Testing Sophia integrations..."
	@python3 -c "from app.api.routers.health_integrations import *; import asyncio; asyncio.run(get_integration_health())" | jq '.' 2>/dev/null || echo "Test failed - make sure API is running"
	@python3 scripts/development/refactor_tools.py probe-import --module app.artemis.agent_factory || true
	@python3 scripts/development/refactor_tools.py scan-http --path app | head -n 40
