# Roo Code Setup for SOPHIA

This document outlines the setup and usage of Roo Code with custom modes and MCP servers for the SOPHIA project.

## 🏗️ Setup Overview

SOPHIA integrates Roo Code with four custom modes and a lightweight MCP stack:

1. **Four powerful modes** (architect, builder, tester, operator) defined in `.roomodes` (YAML)
2. **Local MCP servers** for code context and documentation search
3. **Remote GitHub MCP** via OAuth

## 🚀 Step 1: Load Custom Modes

1. Open the Roo sidebar in VS Code
2. Click on **Prompts** tab
3. Click on the "**⋯**" menu next to Project Prompts
4. Select **Edit Project Modes**
5. Ensure it points to `.roomodes` (YAML format)

You should now see all four custom modes in the mode selector:

- 🏛️ **SOPHIA Architect** - For architecture, refactoring, and reviews
- 🏗️ **Feature Builder** - For new features and components
- 🧪 **Test Engineer** - For comprehensive test coverage
- 🛠️ **Operator (DevOps/IaC)** - For infrastructure and CI/CD

## 🔌 Step 2: Enable MCP Servers

### Local MCP Servers

1. Open VS Code's MCP view (Command Palette → "MCP: Show MCP View")
2. Find the following servers in the list:
   - `code-context`
   - `docs-mcp` 
3. Click **Start** for each server

Or run them from the terminal:

```bash
bash scripts/start_all_mcps.sh
```

### GitHub MCP (Remote)

1. In VS Code's MCP view, search for "GitHub"
2. Click **Install** button (this will open OAuth flow)
3. Complete the authentication process
4. GitHub MCP will now be available as a remote server

## 🛠️ Step 3: Verification

Run the following commands to verify the setup:

```bash
# Make scripts executable and install dependencies
bash scripts/setup.sh

# Check that MCP servers can be loaded
bash scripts/mcp/healthcheck.sh

# Start all MCP servers
bash scripts/start_all_mcps.sh

# Run QA checks
bash scripts/qa/checks.sh
```

## 🧪 Mode Usage Examples

### 🏛️ Architect Mode

Best for: Refactoring, PR reviews, dependency checks, performance audits

Sample prompt:
```
Audit `apps/api/memory_manager.py` for hotspots; propose 3-file refactor; generate diffs + tests.
```

### 🏗️ Builder Mode

Best for: New agents/components, APIs, small MCP adapters

Sample prompt:
```
Scaffold `GET /v1/health` in FastAPI with pydantic models + pytest; wire router; update README section.
```

### 🧪 Test Engineer Mode

Best for: Test creation, gap analysis, flake prevention, coverage boosts

Sample prompt:
```
Write pytest for `services/memory/vector_store.py`: empty/large/error paths; no network; fixtures + fakes.
```

### 🛠️ Operator Mode

Best for: CI workflows, IaC diffs/previews, deploy safety checks

Sample prompt:
```
Render a Pulumi preview for our S3 bucket changes; do not apply; update CI job to gate on preview; docs snippet.
```

## 🔧 Troubleshooting

### MCP Server Issues

- **Logs**: Check server logs in VS Code's "Output" panel (select "MCP" from the dropdown)
- **Restart**: Use `scripts/stop_all_mcps.sh` then `scripts/start_all_mcps.sh`
- **Configuration**: Review `.vscode/mcp.json` and `mcp/docs-mcp.config.json`

### Mode Issues

- Verify `.roomodes` file exists and is properly formatted
- Check that you've loaded the modes in Roo (Step 1)
- Ensure all required MCP servers are running

## 📁 File Locations

- **Modes**: `.roomodes` (YAML)
- **Mode Rules**: `.roo/rules-<mode_name>/` (documentation for each mode)
- **MCP Config**: `.vscode/mcp.json` (VS Code config)
- **Docs MCP Config**: `mcp/docs-mcp.config.json` (for documentation search)
- **MCP Servers**:
  - `mcp/code_context/server.py` (code search/navigation)
  - `mcp/docs_search/server.py` (documentation search)
