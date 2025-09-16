# Workbench UI Integration

The Workbench UI has been extracted to a separate repository to comply with architectural principles.

## Repository Information
- **New Repository**: `https://github.com/ai-cherry/sophia-workbench-ui` (to be created)
- **Local Worktree**: `../worktrees/workbench-ui`
- **Purpose**: Backend service for Sophia Intel AI Workbench interface

## Quick Start

### Clone the Workbench Repository
```bash
# If using worktree (recommended for development)
git worktree add ../worktrees/workbench-ui workbench-ui-split

# Or clone directly
git clone https://github.com/ai-cherry/sophia-workbench-ui.git ../sophia-workbench-ui
```

### Run Workbench UI
```bash
cd ../worktrees/workbench-ui
npm install

# Set environment to use main repo's .env.master
export REPO_ENV_MASTER_PATH=$(pwd)/../sophia-intel-ai/.env.master
export PORTKEY_API_KEY=your-key-here

# Start development server (port 3200)
npm run dev
```

## Environment Variables

### Required
- `REPO_ENV_MASTER_PATH`: Path to main repository's `.env.master` file
- `PORTKEY_API_KEY`: Portkey API key for AI routing

### MCP Server URLs (defaults to localhost)
- `MCP_MEMORY_URL`: http://localhost:8081
- `MCP_FILESYSTEM_URL`: http://localhost:8082
- `MCP_GIT_URL`: http://localhost:8084
- `MCP_VECTOR_URL`: http://localhost:8085

## Architecture

The Workbench UI provides backend services for:
- **Policy Enforcement**: Using POLICIES/access.yml from main repo
- **Git Operations**: Repository management and version control
- **Model Configuration**: AI model aliases and routing
- **Provider Integration**: Portkey, OpenRouter, and direct AI provider support

## Development Workflow

1. **Start MCP servers** (in main repo):
   ```bash
   cd ~/sophia-intel-ai
   ./scripts/start_all_mcp.sh
   ```

2. **Start Workbench** (in worktree):
   ```bash
   cd ../worktrees/workbench-ui
   REPO_ENV_MASTER_PATH=~/sophia-intel-ai/.env.master npm run dev
   ```

3. **Access API**: http://localhost:3200

## API Endpoints

- `GET /health` - Health check
- `POST /api/chat` - AI chat completions
- `POST /api/apply` - Apply code changes with policy guard
- `GET /api/models` - List available models
- `GET /api/config` - Get configuration

## Deployment

### Local Development
```bash
npm run dev
```

### Production Build
```bash
npm run build
npm start
```

### Docker
```bash
docker build -t sophia-workbench-ui .
docker run -p 3200:3200 \
  -e REPO_ENV_MASTER_PATH=/config/.env.master \
  -v ~/sophia-intel-ai/.env.master:/config/.env.master:ro \
  sophia-workbench-ui
```

## Troubleshooting

### Common Issues

1. **Cannot find .env.master**
   - Ensure `REPO_ENV_MASTER_PATH` points to the correct file
   - Use absolute paths when in doubt

2. **MCP servers not accessible**
   - Verify MCP servers are running: `ps aux | grep mcp`
   - Check ports: `lsof -i :8081-8085`
   - Ensure no firewall blocking local connections

3. **Policy enforcement errors**
   - Verify POLICIES/access.yml exists in main repo
   - Check file permissions

## Migration Notes

This service was extracted from the main repository to maintain clean separation of concerns:
- Main repo: Backend services, MCP servers, CLI tools
- Workbench repo: Workbench-specific backend service
- Future: Separate frontend UI repositories

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## License

Same as main Sophia Intel AI repository.
