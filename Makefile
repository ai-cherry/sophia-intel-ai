SHELL := /bin/bash

.PHONY: help env.check rag.start rag.test lint dev-up dev-down dev-shell logs status grok-test swarm-start memory-search

help:
	@echo "\033[0;36mMulti-Agent Development Environment\033[0m"
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[0;32m%-18s\033[0m %s\n", $$1, $$2}'

env.check: ## Run environment preflight checks
	python3 scripts/agents_env_check.py || true

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

clean: ## Clean up Docker resources
	@echo "🧹 Cleaning Docker resources..."
	@docker system prune -f
	@docker volume prune -f
