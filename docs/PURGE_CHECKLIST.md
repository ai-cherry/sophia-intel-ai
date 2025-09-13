Purge Checklist (Enforced)

Delete without backups or archives
- UI: `builder-agno-system/`, `start_builder_agno.sh`, `start_sophia_intel.sh`, any `frontend/` dir.
- LiteLLM: `litellm-manager.sh`, `bin/litellm-install`, `bin/litellm-test`, `litellm-config.yaml`, any LiteLLM tests/scripts.
- Legacy MCP servers: `mcp/filesystem.py`, `mcp/git_server.py`.
- Duplicate config: `config/manager.py`, `config/model_manager.py`, `config/integration_adapter.py`, `config/models.json`.
- UI deploy configs: `deploy/fly-ui.toml`, `deploy/fly-squads.toml`, any Dockerfiles/compose that build a UI from this repo.

Canonicalize MCP everywhere
- Start only:
  - `mcp/memory_server.py` (8081),
  - `mcp/filesystem/server.py` (8082),
  - `mcp/git/server.py` (8084).
- Update scripts/infra/docs to these paths only.

Script and Infra
- `infra/docker-compose.yml`: no UI service from this repo.
- `.devcontainer/*`: no UI autostart; print explicit “no UI here” notice.

Docs
- Remove all `builder-agno-system`, in-repo `sophia-intel-app`, LiteLLM, `:4000`, `:8090` references.
- Replace with links to `docs/CODING_UI_STANDALONE.md` and `docs/ONE_TRUE_DEV_FLOW.md`.
