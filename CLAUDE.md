# Claude Code Configuration - Multi-Tool Environment

## MCP Integration
- Memory Server: http://localhost:8081
- Filesystem Server: http://localhost:8082  
- Git Server: http://localhost:8084

## Core Rules
- NO try/catch spam - handle errors at boundaries only
- Functional > OOP when reasonable
- Use background tasks for long operations
- Atomic commits with conventional format
- Always lint: black (Python), prettier (JS/TS)

## File Organization
- `/src` or `/app` - Source code
- `/tests` - Test files
- `/docs` - Documentation
- `/scripts` - Utility scripts
- NO files in root except configs

## Commands
- Use `--mode plan` for complex tasks
- Background: `--background` for tests/builds
- Preview: `--preview` before commits

## Integration with Other Tools
- Opencode: Share env vars via .env
- Codex: Git operations coordinated
- Cursor: Rules sync via .cursorrules
- MCP: Shared context via servers

## Security
- NEVER commit .env or secrets
- Use environment variables
- Validate all inputs
- No eval() or exec()
