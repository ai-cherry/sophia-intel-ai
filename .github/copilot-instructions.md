# GitHub Copilot Instructions for Sophia Intel

## Cloud-First Development Standards

### Non-Negotiable Rules for this Workspace

* Do **not** install OS packages globally or mutate the Codespaces base image beyond the `Dockerfile` here.
* Keep **Python 3.11** and **uv** as the dependency manager; pin dependencies via `requirements.txt`.
* Never push directly to `main`. Always create a branch + PR with conventional commit messages.
* Don't edit system-level config. Operate only inside the repo and its devcontainer.
* Keep secrets out of the repo. Use `.env` locally in Codespaces and **GitHub Secrets** in CI.
* Prefer **actionable diffs** (patches / PRs) over silent in-place edits.
* All new features must include unit tests or an integration check.
* Output structured JSON where appropriate (for LLM/agent responses).

### Agent Response Format

All agents MUST return responses in this exact JSON structure:

```json
{
  "summary": "Brief description of what was done",
  "patch": "unified diff format patch"
}
```

### Architecture Guidelines

- **Single responsibility**: One orchestrator, one base agent, one coding agent, one MCP memory service
- **LLM routing**: Always via Portkey → OpenRouter integration
- **Vector memory**: Qdrant cloud instances preferred
- **Agent framework**: Use Agno for conversation history and model integration
- **MCP servers**: Deploy to Lambda Labs behind API gateway

### Code Quality Standards

- **Type hints required** for all function signatures
- **Async/await** for all I/O operations
- **Error handling** with proper logging via loguru
- **Configuration** via YAML defaults + env overrides
- **Tests** using pytest for all new functionality

### Commit Message Format

Follow conventional commits:
- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation updates
- `refactor:` - Code refactoring
- `test:` - Adding/updating tests
- `chore:` - Build/dependency updates

### Environment Management

- **Development**: Use `.env` file in Codespaces (never committed)
- **CI/CD**: Use GitHub Secrets for API keys and credentials
- **Production**: Environment variables via deployment platform

### MCP Integration Patterns

When working with MCP (Model Context Protocol):
- Store context with session isolation
- Query with semantic similarity
- Include metadata for rich context
- Use global search sparingly

### File Organization

```
sophia-intel/
├── agents/           # Agent implementations only
├── backend/          # Main FastAPI application  
├── config/           # Configuration management
├── mcp_servers/      # Memory & context services
├── services/         # External service clients
├── scripts/          # Utility and deployment scripts
├── .prompts/         # Reusable prompt templates
├── docs/             # Additional documentation
└── tests/            # All test files
```

### Development Workflow

1. **Create branch** from main: `git checkout -b feat/description`
2. **Implement changes** following architecture guidelines
3. **Add tests** for new functionality
4. **Update documentation** if API changes
5. **Commit** with conventional message format
6. **Push and create PR** with template checklist
7. **Code review** before merge to main

### Debugging Standards

- Use **MCP context storage** to persist debugging sessions
- Include **reproduction steps** in all bug reports
- **Log structured data** for easy parsing and analysis
- Prefer **integration tests** over unit tests for agent workflows

### Security Practices

- **Never hardcode** API keys or secrets
- **Validate all inputs** from external APIs
- **Use environment variables** for configuration
- **Sanitize outputs** before logging or storage
- **Rate limit** external API calls appropriately