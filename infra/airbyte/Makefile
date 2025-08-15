# Airbyte OSS + MinIO Management Makefile

.PHONY: help minio-up minio-down airbyte-up airbyte-down full-up full-down status logs clean init

# Default target
help:
	@echo "Airbyte OSS + MinIO Management"
	@echo "=============================="
	@echo ""
	@echo "Available targets:"
	@echo "  minio-up      - Start MinIO services"
	@echo "  minio-down    - Stop MinIO services"
	@echo "  airbyte-up    - Start Airbyte services"
	@echo "  airbyte-down  - Stop Airbyte services"
	@echo "  full-up       - Start all services (MinIO + Airbyte)"
	@echo "  full-down     - Stop all services"
	@echo "  status        - Show service status"
	@echo "  logs          - Show service logs"
	@echo "  clean         - Remove all volumes and networks"
	@echo "  init          - Initialize environment and start services"
	@echo ""

# Environment setup
.env:
	@if [ ! -f .env ]; then \
		echo "Creating .env from .env.example..."; \
		cp .env.example .env; \
		echo "Please edit .env with your configuration"; \
	fi

# MinIO operations
minio-up: .env
	@echo "Starting MinIO services..."
	docker-compose -f docker-compose.minio.yml up -d
	@echo "MinIO Console: http://localhost:9001"
	@echo "MinIO API: http://localhost:9000"

minio-down:
	@echo "Stopping MinIO services..."
	docker-compose -f docker-compose.minio.yml down

# Airbyte operations
airbyte-up: .env
	@echo "Starting Airbyte services..."
	docker-compose -f docker-compose.airbyte.yml up -d
	@echo "Waiting for Airbyte to be ready..."
	@timeout 300 bash -c 'until curl -f http://localhost:8001/api/v1/health >/dev/null 2>&1; do sleep 5; done' || echo "Timeout waiting for Airbyte"
	@echo "Airbyte Web UI: http://localhost:8000"
	@echo "Airbyte API: http://localhost:8001"

airbyte-down:
	@echo "Stopping Airbyte services..."
	docker-compose -f docker-compose.airbyte.yml down

# Full stack operations
full-up: minio-up airbyte-up
	@echo "All services started successfully!"
	@echo ""
	@echo "Access URLs:"
	@echo "  Airbyte Web UI: http://localhost:8000"
	@echo "  MinIO Console:  http://localhost:9001"
	@echo ""

full-down: airbyte-down minio-down
	@echo "All services stopped"

# Status and monitoring
status:
	@echo "=== MinIO Services ==="
	docker-compose -f docker-compose.minio.yml ps
	@echo ""
	@echo "=== Airbyte Services ==="
	docker-compose -f docker-compose.airbyte.yml ps

logs:
	@echo "Select service to view logs:"
	@echo "1) MinIO"
	@echo "2) Airbyte Server"
	@echo "3) Airbyte Worker"
	@echo "4) Airbyte DB"
	@echo "5) All Airbyte"
	@read -p "Enter choice [1-5]: " choice; \
	case $$choice in \
		1) docker-compose -f docker-compose.minio.yml logs -f minio ;; \
		2) docker-compose -f docker-compose.airbyte.yml logs -f airbyte-server ;; \
		3) docker-compose -f docker-compose.airbyte.yml logs -f airbyte-worker ;; \
		4) docker-compose -f docker-compose.airbyte.yml logs -f airbyte-db ;; \
		5) docker-compose -f docker-compose.airbyte.yml logs -f ;; \
		*) echo "Invalid choice" ;; \
	esac

# Cleanup operations
clean: full-down
	@echo "Removing all volumes and networks..."
	docker volume rm -f airbyte_workspace airbyte_data airbyte_db airbyte_local minio_data 2>/dev/null || true
	docker network rm -f airbyte_internal minio_network 2>/dev/null || true
	@echo "Cleanup complete"

# Initialization
init: .env
	@echo "Initializing Airbyte OSS + MinIO environment..."
	@echo "1. Creating networks..."
	docker network create airbyte_internal 2>/dev/null || true
	docker network create minio_network 2>/dev/null || true
	@echo "2. Starting services..."
	$(MAKE) full-up
	@echo ""
	@echo "Initialization complete!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Access Airbyte at http://localhost:8000"
	@echo "2. Access MinIO Console at http://localhost:9001"
	@echo "3. Configure your first connection"

# Health checks
health:
	@echo "=== Health Check ==="
	@echo -n "MinIO: "
	@curl -f http://localhost:9000/minio/health/live >/dev/null 2>&1 && echo "✅ Healthy" || echo "❌ Unhealthy"
	@echo -n "Airbyte: "
	@curl -f http://localhost:8001/api/v1/health >/dev/null 2>&1 && echo "✅ Healthy" || echo "❌ Unhealthy"

# Development helpers
dev-setup: init
	@echo "Development environment ready!"
	@echo "Run 'make logs' to monitor services"

# Production helpers
prod-check:
	@echo "=== Production Readiness Check ==="
	@echo "Checking environment variables..."
	@test -n "$$MINIO_ROOT_USER" || (echo "❌ MINIO_ROOT_USER not set" && exit 1)
	@test -n "$$MINIO_ROOT_PASSWORD" || (echo "❌ MINIO_ROOT_PASSWORD not set" && exit 1)
	@echo "✅ Environment variables OK"
	@echo "Checking services..."
	$(MAKE) health

