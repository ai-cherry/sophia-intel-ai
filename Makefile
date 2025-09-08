SHELL := /bin/bash

.PHONY: env.check rag.start rag.test lint

env.check:
	python3 scripts/agents_env_check.py || true

rag.start:
	./unified-start.sh --with-rag

rag.test:
	@set -e; \
	for port in 8767 8768; do \
		echo "Testing health on $$port"; \
		curl -sf http://localhost:$$port/health >/dev/null || (echo "Service $$port not healthy" && exit 1); \
	done; \
	echo "RAG services healthy"

lint:
	ruff check . || true

