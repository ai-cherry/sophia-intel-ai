# GitHub CLI Health Check and Authentication
.PHONY: gh-doctor
gh-doctor:
	@echo "🔍 GitHub CLI Health Check..."
	@gh --version
	@gh auth status || (echo "❌ gh not authenticated" && exit 1)
	@gh repo view >/dev/null && echo "✅ GitHub CLI ready - repo access OK"
	@git config --get user.name || echo "⚠️  Git user.name not set"
	@git config --get user.email || echo "⚠️  Git user.email not set"

# Quick GitHub CLI authentication using existing token
.PHONY: gh-login
gh-login:
	@echo "🔐 Authenticating GitHub CLI with token..."
	@printf '%s' "$$GH_FINE_GRAINED_TOKEN" | gh auth login --with-token
	@gh auth setup-git
	@echo "✅ GitHub CLI authenticated and git configured"

# Refresh GitHub CLI authentication (for token rotation)
.PHONY: gh-refresh
gh-refresh:
	@echo "🔄 Refreshing GitHub CLI authentication..."
	@gh auth refresh -h github.com -s repo,workflow
	@echo "✅ GitHub CLI authentication refreshed"

# Lightweight auth check for humans
.PHONY: auth-doctor
auth-doctor:
	@gh auth status && git config --get credential.helper && echo "✅ gh OK"

# Show current PR status
.PHONY: pr-status
pr-status:
	@gh pr status

# Python Development
.PHONY: install
install:
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -r requirements.dev.txt

.PHONY: test
test:
	python -m pytest tests/

.PHONY: lint
lint:
	python -m ruff check .
	python -m black --check .

.PHONY: format
format:
	python -m ruff check --fix .
	python -m black .

# Docker
.PHONY: docker-up
docker-up:
	docker-compose up -d

.PHONY: docker-down
docker-down:
	docker-compose down

.PHONY: docker-logs
docker-logs:
	docker-compose logs -f

# Help
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  gh-doctor    - Check GitHub CLI authentication and configuration"
	@echo "  auth-doctor  - Quick auth check (lightweight version)"
	@echo "  gh-login     - Authenticate GitHub CLI with token"
	@echo "  gh-refresh   - Refresh GitHub CLI authentication (after token rotation)"
	@echo "  pr-status    - Show current PR status"
	@echo "  install      - Install Python dependencies"
	@echo "  test         - Run tests"
	@echo "  lint         - Run linters"
	@echo "  format       - Format code"
	@echo "  docker-up    - Start Docker services"
	@echo "  docker-down  - Stop Docker services"
	@echo "  docker-logs  - Show Docker logs"
	@echo "  help         - Show this help message"

.DEFAULT_GOAL := help