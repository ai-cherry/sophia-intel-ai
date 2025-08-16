.PHONY: help up down logs smoke clean build

help: ## Show this help
@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

up: ## Start all services
docker-compose up -d
@echo "🚀 Services starting..."
@echo "   API: http://localhost:8000"
@echo "   UI:  http://localhost:5173"

down: ## Stop all services
docker-compose down

logs: ## Show logs
docker-compose logs -f

smoke: ## Run smoke tests
@echo "🧪 Running smoke tests..."
@bash ops/smoke.sh

clean: ## Clean up containers and volumes
docker-compose down -v
docker system prune -f

build: ## Build all images
docker-compose build --no-cache
