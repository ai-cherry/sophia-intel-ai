.PHONY: deps index swarm mcp

deps:
	python -m pip install -U -r requirements.txt

index:
	python scripts/index_repo.py

swarm:
	python -m swarm.cli --task "$(task)"

mcp:
	python mcp_servers/enhanced_unified_server.py --host 127.0.0.1 --port 8765
