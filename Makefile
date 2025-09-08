# Sophia Intel AI - Standardized CLI Operations
.PHONY: help health mcp-up mcp-test agents-test clean-artifacts scan-repo

help:
	@echo "Sophia Intel AI - Available Commands:"
	@echo ""
	@echo "  make health       - Run comprehensive repository and environment health checks"
	@echo "  make mcp-up       - Start MCP servers (memory server and unified orchestrator)"
	@echo "  make mcp-test     - Test MCP server health and basic functionality"
	@echo "  make agents-test  - Verify AI agent environment setup (no venvs, MCP access)"
	@echo "  make clean-artifacts - Remove temporary files, caches, and dumps from repository"
	@echo "  make scan-repo    - Generate repository audit report for duplicates and artifacts"
	@echo ""
	@echo "Environment Variables:"
	@echo "  BIND_IP          - IP address for MCP servers (default: 0.0.0.0)"
	@echo "  MCP_MEMORY_PORT  - Port for memory server (default: 8001)"
	@echo "  REDIS_HOST       - Redis host (default: localhost)"
	@echo "  REDIS_PORT       - Redis port (default: 6379)"
	@echo "  QDRANT_URL       - Qdrant URL (default: http://localhost:6333)"

health:
	@echo "🔍 Running comprehensive health checks..."
	@bash scripts/cli_health_check.sh

mcp-up:
	@echo "🚀 Starting MCP servers..."
	@bash scripts/mcp_bootstrap.sh

mcp-test:
	@echo "🧪 Testing MCP server functionality..."
	@bash scripts/mcp_health_check.sh

agents-test:
	@echo "🤖 Verifying AI agent environment..."
	@python3 scripts/agents_env_check.py

clean-artifacts:
	@echo "🧹 Cleaning repository artifacts..."
	@bash scripts/clean_repo_artifacts.sh

scan-repo:
	@echo "📊 Scanning repository for audit report..."
	@bash scripts/scan_repo_artifacts.sh

# Development shortcuts
dev-setup: health mcp-up mcp-test agents-test
	@echo "✅ Development environment ready!"

quick-check: health agents-test
	@echo "✅ Quick environment check complete!"
