# Continue.dev + MCP + IaC + GitHub CLI Verification Guide

This document provides steps to verify that all components of our integration are working correctly after a Codespaces reload.

## Prerequisites

Ensure you have these environment variables set in your Codespace:
- `CONTINUE_API_KEY` - Your Continue Hub API key
- `GH_API_TOKEN` - Your GitHub Personal Access Token

You can verify these with:
```bash
bash scripts/check_continue_env.sh
```

## 1. Continue.dev Basic Setup Verification

1. **Reload the VS Code window**
   - Command Palette → "Developer: Reload Window"

2. **Check Continue.dev extension**
   - Confirm Continue.dev sidebar is accessible
   - Chat sidebar should show no errors

3. **Verify slash commands**
   - Open any Python file
   - Select a function or small code block
   - Type `/docstring` and press enter
   - Verify that a Google-style docstring is generated

## 2. MCP Server Verification

1. **Check `/health` command**
   - In Continue.dev chat, type `/health`
   - Verify that both MCP servers (sophia-code and sophia-github) return healthy status
   - Code MCP should return stats from the code index
   - GitHub MCP should return repository metadata

2. **Test Code MCP tools**
   - In Continue.dev chat, enter:
     ```
     run tool code_index { globs: ["agents/**", "libs/**", "mcp/**", "schemas/**", "docs/**"] }
     ```
   - Verify you get file and symbol counts
   - Then try:
     ```
     run tool code_search { query: "mcp server", top_k: 5 }
     ```
   - You should get ranked files and snippets

3. **Test GitHub MCP**
   - In Continue.dev chat, ask it to:
     ```
     Create a throwaway draft PR to test permissions
     ```
   - Verify it can access GitHub API and create a draft PR
   - Delete the draft PR afterward

## 3. Infrastructure as Code Verification

1. **Check Pulumi workflows**
   - Open `.github/workflows/infra-preview.yaml`
   - Make a small change to any file in the `infra/` or `pulumi/` directory
   - Create a PR and verify the Infrastructure Preview workflow runs

2. **Verify OIDC setup**
   - This requires proper AWS/cloud setup (check documentation)
   - Workflow should run but may fail if OIDC isn't configured yet

## 4. Continue Hub Publishing

1. **Check workflow file**
   - Verify `.github/workflows/continue-publish.yaml` exists
   - Ensure `OWNER_SLUG` is set correctly for your organization

2. **Test publication (optional)**
   - Push a small change to `config.yaml` on main branch
   - Check GitHub Actions to see if the publish workflow runs

## Verification Checklist

- [ ] Environment variables (`CONTINUE_API_KEY`, `GH_API_TOKEN`) are set
- [ ] MCP servers start automatically with VS Code
- [ ] `/health` command returns status from both servers
- [ ] Code MCP tools (`code_index`, `code_search`, etc.) work
- [ ] GitHub MCP can access repository data
- [ ] Slash commands (`/docstring`, `/test`, `/refactor`, `/mission`) work
- [ ] Infrastructure workflows exist and are properly configured
- [ ] Continue Hub publishing workflow exists and is properly configured

If any verification steps fail, check the troubleshooting section in `docs/continue_dev_setup.md`.
