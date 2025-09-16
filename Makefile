.PHONY: help env-check dev up down health logs clean test smoke ui

# Default target
help:
	@echo "Sophia Intel AI - Local Deployment Commands"
	@echo ""
	@echo "Environment:"
	@echo "  env-check    Check .env.master configuration"
	@echo "  env-setup    Create .env.master template"
	@echo ""
	@echo "Local Development (non-Docker):"
	@echo "  dev          Start API + MCP servers locally"
	@echo "  api          Start API server only"
	@echo "  mcp          Start MCP servers only"
	@echo ""  
	@echo "Docker Deployment:"
	@echo "  up           Start all services with Docker"
	@echo "  down         Stop all Docker services"
	@echo "  build        Build Docker images"
	@echo "  logs         Show service logs"
	@echo ""
	@echo "Health & Testing:"
	@echo "  health       Check all service health"
	@echo "  smoke        Quick smoke test"
	@echo "  test         Run integration tests"
	@echo "  ui           Open dashboard UI"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean        Clean Docker resources"
	@echo "  reset        Full reset (stop + clean)"

# Environment setup
env-check:
	@echo "🔍 Checking .env.master configuration..."
	@test -f .env.master || (echo "❌ .env.master not found. Run 'make env-setup'" && exit 1)
	@chmod 600 .env.master
	@echo "✅ .env.master found and secured"
	@grep -q "PORTKEY_API_KEY=" .env.master || echo "⚠️  PORTKEY_API_KEY not set"
	@grep -q "OPENROUTER_API_KEY=" .env.master || echo "⚠️  OPENROUTER_API_KEY not set"

env-setup:
	@if [ ! -f .env.master ]; then \
		echo "📝 Creating .env.master from template..."; \
		cp env.example .env.master 2>/dev/null || echo "# Sophia Intel AI Environment\nPORTKEY_API_KEY=\nOPENROUTER_API_KEY=\nTOGETHER_API_KEY=" > .env.master; \
		chmod 600 .env.master; \
		echo "✅ Created .env.master (please edit with your API keys)"; \
	else \
		echo "⚠️  .env.master already exists"; \
	fi

# Local development (non-Docker)
dev: env-check
	@echo "🚀 Starting Sophia Intel AI locally..."
	@echo "Starting MCP servers in background..."
	@python -m uvicorn mcp.memory_server:app --host 0.0.0.0 --port 8081 &
	@python -m uvicorn mcp.filesystem.server:app --host 0.0.0.0 --port 8082 &
	@python -m uvicorn mcp.git.server:app --host 0.0.0.0 --port 8084 &
	@sleep 2
	@echo "Starting API server..."
	@python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload

api: env-check
	@echo "🚀 Starting API server only..."
	python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload

mcp: env-check
	@echo "🧠 Starting MCP servers..."
	@python -m uvicorn mcp.memory_server:app --host 0.0.0.0 --port 8081 &
	@python -m uvicorn mcp.filesystem.server:app --host 0.0.0.0 --port 8082 &
	@python -m uvicorn mcp.git.server:app --host 0.0.0.0 --port 8084 &
	@echo "✅ MCP servers started on ports 8081, 8082, 8084"

# Docker deployment
up: env-check
	@echo "🐳 Starting Sophia Intel AI with Docker..."
	docker compose up -d
	@echo "⏳ Waiting for services to start..."
	@sleep 10
	@make health

down:
	@echo "🛑 Stopping Docker services..."
	docker compose down

build:
	@echo "🔨 Building Docker images..."
	docker compose build

logs:
	docker compose logs -f

# Health checks
health:
	@echo "🏥 Checking service health..."
	@echo -n "API (8000): "; curl -sf http://localhost:8000/health >/dev/null && echo "✅ OK" || echo "❌ DOWN"
	@echo -n "MCP Memory (8081): "; curl -sf http://localhost:8081/health >/dev/null && echo "✅ OK" || echo "❌ DOWN"
	@echo -n "MCP Filesystem (8082): "; curl -sf http://localhost:8082/health >/dev/null && echo "✅ OK" || echo "❌ DOWN"
	@echo -n "MCP Git (8084): "; curl -sf http://localhost:8084/health >/dev/null && echo "✅ OK" || echo "❌ DOWN"
	@echo -n "Redis (6379): "; (echo "PING" | nc localhost 6379 2>/dev/null | grep -q PONG) && echo "✅ OK" || echo "❌ DOWN"
	@echo -n "Weaviate (8080): "; curl -sf http://localhost:8080/v1/.well-known/ready >/dev/null && echo "✅ OK" || echo "❌ DOWN"

smoke: health
	@echo "💨 Running smoke tests..."
	@echo -n "Dashboard: "; curl -sf http://localhost:8000/dashboard >/dev/null && echo "✅ OK" || echo "❌ FAIL"
	@echo -n "API Docs: "; curl -sf http://localhost:8000/docs >/dev/null && echo "✅ OK" || echo "❌ FAIL"
	@echo -n "Models endpoint: "; curl -sf http://localhost:8000/api/models >/dev/null && echo "✅ OK" || echo "❌ FAIL"

test:
	@echo "🧪 Running integration tests..."
	pytest tests/integration/ -v

ui:
	@echo "🎯 Opening Sophia Intel AI Dashboard..."
	@python -c "import webbrowser; webbrowser.open('http://localhost:8000/dashboard')"

# Cleanup
clean:
	@echo "🧹 Cleaning Docker resources..."
	docker compose down -v
	docker system prune -f
	@echo "✅ Cleanup complete"

reset: down clean
	@echo "🔄 Full reset complete"

# Legacy targets (for compatibility)
run: api
