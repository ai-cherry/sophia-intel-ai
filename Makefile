# Sophia Intel AI - Development Makefile
# AI Swarm Orchestration Platform

# Variables
PYTHON := python3
PIP := pip3
NODE := node
NPM := npm
DOCKER := docker
DOCKER_COMPOSE := docker-compose

# Directories
SRC_DIR := .
FRONTEND_DIR := agent-ui
TESTS_DIR := tests
DATA_DIR := data
LOGS_DIR := $(DATA_DIR)/logs

# Ports
API_PORT := 8003
FRONTEND_PORT := 3000
MCP_PORT := 8004

# Colors
RED := \033[31m
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
PURPLE := \033[35m
CYAN := \033[36m
RESET := \033[0m

# Default target
.PHONY: help
help: ## Show this help message
	@echo "$(CYAN)🤖 Sophia Intel AI - Development Commands$(RESET)"
	@echo "$(BLUE)AI Swarm Orchestration Platform$(RESET)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'

.PHONY: check
check: ## Check system dependencies
	@echo "$(BLUE)🔍 Checking dependencies...$(RESET)"
	@which python3 > /dev/null || (echo "$(RED)❌ Python 3 not found$(RESET)" && exit 1)
	@which node > /dev/null || (echo "$(RED)❌ Node.js not found$(RESET)" && exit 1)
	@which npm > /dev/null || (echo "$(RED)❌ npm not found$(RESET)" && exit 1)
	@echo "$(GREEN)✅ Dependencies check passed$(RESET)"

.PHONY: setup
setup: check ## Set up development environment
	@echo "$(BLUE)🔧 Setting up development environment...$(RESET)"
	@mkdir -p $(DATA_DIR)/cost_tracking $(DATA_DIR)/memory $(LOGS_DIR) $(DATA_DIR)/sessions
	@[ -f .env.local ] || cp .env.example .env.local 2>/dev/null || echo "# Add your environment variables here" > .env.local
	@$(PIP) install -e .
	@cd $(FRONTEND_DIR) && $(NPM) install
	@echo "$(GREEN)✅ Development environment setup complete$(RESET)"

.PHONY: install
install: setup ## Alias for setup

.PHONY: dev
dev: ## Start development servers
	@echo "$(BLUE)🚀 Starting development servers...$(RESET)"
	@echo "$(YELLOW)⏳ Starting API server on port $(API_PORT)...$(RESET)"
	@OPENROUTER_API_KEY=$${OPENROUTER_API_KEY} \
	 PORTKEY_API_KEY=$${PORTKEY_API_KEY} \
	 LOCAL_DEV_MODE=true \
	 AGENT_API_PORT=$(API_PORT) \
	 $(PYTHON) -m app.api.unified_server &
	@sleep 3
	@echo "$(YELLOW)⏳ Starting frontend on port $(FRONTEND_PORT)...$(RESET)"
	@cd $(FRONTEND_DIR) && NEXT_PUBLIC_API_URL=http://localhost:$(API_PORT) $(NPM) run dev &
	@echo "$(GREEN)🎉 Services started!$(RESET)"
	@echo "$(CYAN)📱 Frontend: http://localhost:$(FRONTEND_PORT)$(RESET)"
	@echo "$(CYAN)🔧 API Docs: http://localhost:$(API_PORT)/docs$(RESET)"
	@echo "$(CYAN)💰 Cost API: http://localhost:$(API_PORT)/costs/summary$(RESET)"
	@echo "$(YELLOW)Press Ctrl+C to stop services$(RESET)"
	@trap 'kill %1; kill %2' INT; wait

.PHONY: start
start: dev ## Alias for dev

.PHONY: api
api: ## Start only the API server
	@echo "$(BLUE)🚀 Starting API server on port $(API_PORT)...$(RESET)"
	@OPENROUTER_API_KEY=$${OPENROUTER_API_KEY} \
	 PORTKEY_API_KEY=$${PORTKEY_API_KEY} \
	 LOCAL_DEV_MODE=true \
	 AGENT_API_PORT=$(API_PORT) \
	 $(PYTHON) -m app.api.unified_server

.PHONY: frontend
frontend: ## Start only the frontend
	@echo "$(BLUE)🚀 Starting frontend on port $(FRONTEND_PORT)...$(RESET)"
	@cd $(FRONTEND_DIR) && NEXT_PUBLIC_API_URL=http://localhost:$(API_PORT) $(NPM) run dev

.PHONY: build
build: ## Build the project
	@echo "$(BLUE)🏗️  Building project...$(RESET)"
	@cd $(FRONTEND_DIR) && $(NPM) run build
	@echo "$(GREEN)✅ Build complete$(RESET)"

.PHONY: test
test: ## Run all tests
	@echo "$(BLUE)🧪 Running tests...$(RESET)"
	@$(PYTHON) -m pytest $(TESTS_DIR)/ -v
	@cd $(FRONTEND_DIR) && [ -f package.json ] && $(NPM) test --passWithNoTests || true
	@echo "$(GREEN)✅ Tests completed$(RESET)"

.PHONY: test-api
test-api: ## Test API endpoints
	@echo "$(BLUE)🧪 Testing API endpoints...$(RESET)"
	@curl -s http://localhost:$(API_PORT)/health | jq . || echo "$(RED)❌ API not responding$(RESET)"
	@curl -s http://localhost:$(API_PORT)/config | jq . || echo "$(RED)❌ Config endpoint not responding$(RESET)"
	@curl -s http://localhost:$(API_PORT)/costs/summary | jq . || echo "$(RED)❌ Cost API not responding$(RESET)"

.PHONY: lint
lint: ## Lint and format code
	@echo "$(BLUE)🧹 Linting and formatting code...$(RESET)"
	@which black > /dev/null && black . --exclude $(FRONTEND_DIR)/ || echo "$(YELLOW)⚠️  black not installed$(RESET)"
	@which ruff > /dev/null && ruff check . --exclude $(FRONTEND_DIR)/ || echo "$(YELLOW)⚠️  ruff not installed$(RESET)"
	@cd $(FRONTEND_DIR) && $(NPM) run lint || echo "$(YELLOW)⚠️  Frontend linting completed with warnings$(RESET)"
	@echo "$(GREEN)✅ Linting complete$(RESET)"

.PHONY: format
format: ## Format code only
	@echo "$(BLUE)🎨 Formatting code...$(RESET)"
	@which black > /dev/null && black . --exclude $(FRONTEND_DIR)/ || echo "$(YELLOW)⚠️  black not installed$(RESET)"
	@cd $(FRONTEND_DIR) && $(NPM) run format || echo "$(YELLOW)⚠️  Frontend formatting not available$(RESET)"

.PHONY: status
status: ## Check service status
	@echo "$(BLUE)🔍 Checking service status...$(RESET)"
	@curl -s http://localhost:$(API_PORT)/health > /dev/null && echo "$(GREEN)✅ API Server (port $(API_PORT))$(RESET)" || echo "$(RED)❌ API Server (port $(API_PORT))$(RESET)"
	@curl -s http://localhost:$(FRONTEND_PORT) > /dev/null && echo "$(GREEN)✅ Frontend (port $(FRONTEND_PORT))$(RESET)" || echo "$(RED)❌ Frontend (port $(FRONTEND_PORT))$(RESET)"

.PHONY: mcp-health
mcp-health: ## Show MCP health from unified API
	@echo "$(BLUE)🧠 Checking MCP health...$(RESET)"
	@curl -s http://localhost:$(API_PORT)/api/mcp/health | jq . || echo "$(YELLOW)⚠️  MCP health endpoint not reachable. Is the API running?$(RESET)"

.PHONY: mcp-status
mcp-status: ## Show MCP server/domain status summary
	@echo "$(BLUE)🧠 Checking MCP domain/server status...$(RESET)"
	@curl -s http://localhost:$(API_PORT)/api/mcp/status | jq . || echo "$(YELLOW)⚠️  MCP status endpoint not reachable. Is the API running?$(RESET)"

.PHONY: mcp-check
mcp-check: ## Quick MCP readiness check (health + capabilities + git status)
	@echo "$(BLUE)🧠 MCP readiness check...$(RESET)"
	@echo "$(CYAN)• Health$(RESET)"
	@curl -s http://localhost:$(API_PORT)/api/mcp/health | jq '{status,connections,capabilities}' || true
	@echo "$(CYAN)• Capabilities$(RESET)"
	@curl -s http://localhost:$(API_PORT)/api/mcp/capabilities | jq . || true
	@echo "$(CYAN)• Git status$(RESET)"
	@curl -s "http://localhost:$(API_PORT)/api/mcp/git/status?repository=." | jq . || true

.PHONY: mcp-redis-print
mcp-redis-print: ## Print Redis URL from credential manager
	@echo "$(BLUE)🔑 Printing Redis config from UnifiedCredentialManager...$(RESET)"
	@$(PYTHON) - <<'PY'
from app.core.unified_credential_manager import UnifiedCredentialManager
u = UnifiedCredentialManager()
print(u.get_redis_config())
PY

.PHONY: mcp-redis-pass
mcp-redis-pass: ## Set Redis password in credential manager: make mcp-redis-pass PASS=yourpass
	@if [ -z "$(PASS)" ]; then echo "$(YELLOW)Usage: make mcp-redis-pass PASS=yourpass$(RESET)"; exit 1; fi
	@echo "$(BLUE)🔐 Updating Redis password in UnifiedCredentialManager...$(RESET)"
	@PASS="$(PASS)" $(PYTHON) - <<'PY'
import os
from app.core.unified_credential_manager import UnifiedCredentialManager
u = UnifiedCredentialManager()
new = u.update_redis_password(os.environ.get('PASS'))
print({'updated_password': new, 'redis_url': u.get_redis_config()['url']})
PY

# -------------------------------
# Codex Agents setup & commands
# -------------------------------

.PHONY: codex-self-setup
codex-self-setup: ## Configure Codex agents & commands locally in this repo
	@echo "$(BLUE)🧩 Setting up Codex agents (local) ...$(RESET)"
	@chmod +x bin/codex-* || true
	@echo "$(GREEN)✅ Codex agents configured. Try: ./bin/codex-agents$(RESET)"

.PHONY: codex-agents
codex-agents: ## List available Codex agents
	@./bin/codex-agents

.PHONY: codex-fix-routing
codex-fix-routing: ## Launch routing fix agent
	@./bin/codex-fix-routing "Fix Portkey/OpenRouter Gemini→OpenAI routing with safe fallbacks."

.PHONY: codex-fix-all
codex-fix-all: ## Run a full fix workflow (debug -> refactor -> test -> review)
	@./bin/codex-debug "Identify top issues to fix now, propose plan."
	@./bin/codex-refactor "Apply minimal diffs for fixes per plan."
	@./bin/codex-test "Add/update tests to cover fixes."
	@./bin/codex-review "Review the changes for quality and regressions."

.PHONY: codex-daily
codex-daily: ## Run daily maintenance (security, perf, docs)
	@./bin/codex-security "Security audit for recent changes."
	@./bin/codex-perf "Performance scan and quick wins."
	@./bin/codex-docs "Update docs for changes."

.PHONY: logs
logs: ## Show recent logs
	@echo "$(BLUE)📄 Recent logs:$(RESET)"
	@[ -f $(LOGS_DIR)/api.log ] && echo "$(CYAN)--- API Logs ---$(RESET)" && tail -20 $(LOGS_DIR)/api.log || echo "$(YELLOW)No API logs yet$(RESET)"
	@[ -f $(LOGS_DIR)/cost_tracking.log ] && echo "$(CYAN)--- Cost Tracking Logs ---$(RESET)" && tail -20 $(LOGS_DIR)/cost_tracking.log || echo "$(YELLOW)No cost tracking logs yet$(RESET)"

.PHONY: clean
clean: ## Clean build artifacts and caches
	@echo "$(BLUE)🧹 Cleaning build artifacts...$(RESET)"
	@find . -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@find . -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf $(FRONTEND_DIR)/node_modules/.cache 2>/dev/null || true
	@rm -rf $(FRONTEND_DIR)/.next 2>/dev/null || true
	@rm -rf $(FRONTEND_DIR)/out 2>/dev/null || true
	@echo "$(GREEN)✅ Cleanup complete$(RESET)"

.PHONY: clean-all
clean-all: clean ## Clean everything including dependencies
	@echo "$(BLUE)🧹 Deep cleaning...$(RESET)"
	@rm -rf $(FRONTEND_DIR)/node_modules
	@echo "$(YELLOW)⚠️  Run 'make setup' to reinstall dependencies$(RESET)"

.PHONY: deps
deps: ## Install/update dependencies
	@echo "$(BLUE)📦 Installing/updating dependencies...$(RESET)"
	@$(PIP) install -e .
	@cd $(FRONTEND_DIR) && $(NPM) install
	@echo "$(GREEN)✅ Dependencies updated$(RESET)"

.PHONY: upgrade
upgrade: ## Upgrade all dependencies
	@echo "$(BLUE)⬆️  Upgrading dependencies...$(RESET)"
	@$(PIP) install --upgrade -e .
	@cd $(FRONTEND_DIR) && $(NPM) update
	@echo "$(GREEN)✅ Dependencies upgraded$(RESET)"

.PHONY: docker-build
docker-build: ## Build Docker images
	@echo "$(BLUE)🐳 Building Docker images...$(RESET)"
	@$(DOCKER_COMPOSE) build
	@echo "$(GREEN)✅ Docker images built$(RESET)"

.PHONY: docker-up
docker-up: ## Start Docker services
	@echo "$(BLUE)🐳 Starting Docker services...$(RESET)"
	@$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✅ Docker services started$(RESET)"

.PHONY: docker-down
docker-down: ## Stop Docker services
	@echo "$(BLUE)🐳 Stopping Docker services...$(RESET)"
	@$(DOCKER_COMPOSE) down
	@echo "$(GREEN)✅ Docker services stopped$(RESET)"

.PHONY: docker-logs
docker-logs: ## Show Docker logs
	@$(DOCKER_COMPOSE) logs -f

.PHONY: mcp-stdio
mcp-stdio: ## Run minimal stdio MCP (filesystem + memory)
	@echo "$(BLUE)🧰 Starting stdio MCP (fs+memory) ...$(RESET)"
	@./bin/mcp-fs-memory

.PHONY: mcp-stdio-test
mcp-stdio-test: ## Test stdio MCP with a few JSON lines
	@echo '{"id":"1","method":"initialize"}' | ./bin/mcp-fs-memory | sed -n '1p'
	@echo '{"id":"2","method":"fs.list","params":{"path":"."}}' | ./bin/mcp-fs-memory | sed -n '1p'
	@echo '{"id":"3","method":"memory.search","params":{"query":"FastAPI"}}' | ./bin/mcp-fs-memory | sed -n '1p'

.PHONY: docker-up-mcp
docker-up-mcp: ## Start only API + Redis (MCP profile)
	@echo "$(BLUE)🐳 Starting MCP stack (api + redis)...$(RESET)"
	@$(DOCKER_COMPOSE) --profile mcp up -d
	@echo "$(GREEN)✅ MCP stack started (ports: API 8003, Redis 6380)$(RESET)"

.PHONY: docker-down-mcp
docker-down-mcp: ## Stop MCP stack
	@$(DOCKER_COMPOSE) --profile mcp down
	@echo "$(GREEN)✅ MCP stack stopped$(RESET)"

.PHONY: docker-logs-mcp
docker-logs-mcp: ## Tail logs for API + Redis
	@$(DOCKER_COMPOSE) --profile mcp logs -f api redis

.PHONY: backup
backup: ## Backup data directory
	@echo "$(BLUE)💾 Creating backup...$(RESET)"
	@tar -czf backup-$(shell date +%Y%m%d-%H%M%S).tar.gz $(DATA_DIR)/
	@echo "$(GREEN)✅ Backup created$(RESET)"

.PHONY: restore
restore: ## Restore from backup (usage: make restore BACKUP=filename.tar.gz)
	@echo "$(BLUE)📦 Restoring from backup: $(BACKUP)...$(RESET)"
	@tar -xzf $(BACKUP)
	@echo "$(GREEN)✅ Restore complete$(RESET)"

.PHONY: security
security: ## Run security checks
	@echo "$(BLUE)🔒 Running security checks...$(RESET)"
	@which safety > /dev/null && safety check || echo "$(YELLOW)⚠️  safety not installed$(RESET)"
	@which bandit > /dev/null && bandit -r . -x $(FRONTEND_DIR)/ || echo "$(YELLOW)⚠️  bandit not installed$(RESET)"
	@cd $(FRONTEND_DIR) && $(NPM) audit || echo "$(YELLOW)⚠️  npm audit completed with warnings$(RESET)"

.PHONY: docs
docs: ## Generate documentation
	@echo "$(BLUE)📚 Generating documentation...$(RESET)"
	@which sphinx-build > /dev/null && sphinx-build -b html docs/ docs/_build/html/ || echo "$(YELLOW)⚠️  Sphinx not installed$(RESET)"
	@echo "$(GREEN)✅ Documentation generated$(RESET)"

.PHONY: profile
profile: ## Profile API performance
	@echo "$(BLUE)📊 Profiling API performance...$(RESET)"
	@$(PYTHON) -m cProfile -o profile.stats -m app.api.unified_server &
	@sleep 5
	@curl -s http://localhost:$(API_PORT)/costs/summary > /dev/null
	@kill %1
	@$(PYTHON) -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(20)"
	@rm -f profile.stats

.PHONY: load-test
load-test: ## Run load tests against API
	@echo "$(BLUE)🚀 Running load tests...$(RESET)"
	@which ab > /dev/null && ab -n 100 -c 10 http://localhost:$(API_PORT)/health || echo "$(YELLOW)⚠️  Apache Bench (ab) not installed$(RESET)"

.PHONY: init
init: check setup ## Initialize new development environment
	@echo "$(GREEN)🎉 Development environment initialized!$(RESET)"
	@echo "$(CYAN)Next steps:$(RESET)"
	@echo "$(CYAN)  1. Add your API keys to .env.local$(RESET)"
	@echo "$(CYAN)  2. Run 'make dev' to start development servers$(RESET)"
	@echo "$(CYAN)  3. Visit http://localhost:$(FRONTEND_PORT) to see the UI$(RESET)"

# Development workflow targets
.PHONY: reset
reset: clean setup ## Reset development environment
	@echo "$(GREEN)✅ Development environment reset$(RESET)"

.PHONY: fresh
fresh: clean-all setup ## Fresh install (removes all dependencies)
	@echo "$(GREEN)✅ Fresh installation complete$(RESET)"

# Monitoring and debugging
.PHONY: monitor
monitor: ## Monitor service logs in real-time
	@echo "$(BLUE)📡 Monitoring services...$(RESET)"
	@tail -f $(LOGS_DIR)/*.log 2>/dev/null || echo "$(YELLOW)No log files found yet$(RESET)"

.PHONY: debug
debug: ## Start API in debug mode
	@echo "$(BLUE)🐛 Starting API in debug mode...$(RESET)"
	@DEBUG=true \
	 OPENROUTER_API_KEY=$${OPENROUTER_API_KEY} \
	 PORTKEY_API_KEY=$${PORTKEY_API_KEY} \
	 LOCAL_DEV_MODE=true \
	 AGENT_API_PORT=$(API_PORT) \
	 $(PYTHON) -m pdb -m app.api.unified_server

# Quality assurance
.PHONY: qa
qa: lint test security ## Run full quality assurance suite
	@echo "$(GREEN)✅ Quality assurance complete$(RESET)"

.PHONY: ci
ci: setup lint test build ## Run CI pipeline locally
	@echo "$(GREEN)✅ CI pipeline complete$(RESET)"

# Information targets
.PHONY: info
info: ## Show project information
	@echo "$(CYAN)🤖 Sophia Intel AI$(RESET)"
	@echo "$(BLUE)AI Swarm Orchestration Platform$(RESET)"
	@echo ""
	@echo "$(CYAN)Services:$(RESET)"
	@echo "  API Server:  http://localhost:$(API_PORT)"
	@echo "  Frontend:    http://localhost:$(FRONTEND_PORT)"
	@echo "  MCP Server:  http://localhost:$(MCP_PORT)"
	@echo ""
	@echo "$(CYAN)Key Endpoints:$(RESET)"
	@echo "  Health:      http://localhost:$(API_PORT)/health"
	@echo "  API Docs:    http://localhost:$(API_PORT)/docs"
	@echo "  Config:      http://localhost:$(API_PORT)/config"
	@echo "  Cost API:    http://localhost:$(API_PORT)/costs/summary"
	@echo "  Embeddings:  http://localhost:$(API_PORT)/embeddings"

.PHONY: version
version: ## Show version information
	@echo "$(CYAN)Version Information:$(RESET)"
	@$(PYTHON) --version
	@$(NODE) --version
	@$(NPM) --version
	@echo "Docker: $(shell $(DOCKER) --version 2>/dev/null || echo 'not installed')"
