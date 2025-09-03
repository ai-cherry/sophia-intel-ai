# Codex CLI Setup for Sophia Intel AI

## ✅ Current Status
- **Logged in**: API key authentication (preferred over ChatGPT login)
- **Repository**: Connected to /Users/lynnmusil/sophia-intel-ai
- **Model**: Using GPT-4o (works with your API key)
- **Working**: Successfully analyzing repository context

## 🚀 Basic Usage

### Interactive Mode
```bash
codex
```

### Execute Single Commands
```bash
codex exec "your prompt here"
codex exec --model gpt-4o "analyze the swarms architecture"
```

### Repository-Specific Queries
```bash
# Analyze codebase structure
codex exec "What are the main components of this AI system?"

# Code analysis
codex exec "Explain how the MCP server works in this repository"

# Architecture questions
codex exec "Show me the swarm orchestration pattern being used"

# Implementation help
codex exec "Help me add a new agent to the coding swarm"
```

## 🔧 Configuration

### API Key (Already Set)
```bash
# Environment variable (persistent in ~/.zshrc)
export OPENAI_API_KEY="sk-svcacct-..."

# Login status
codex login status  # Shows: "Logged in using an API key"
```

### Model Selection
```bash
# Default: GPT-5 (may not work with your account type)
# Recommended: GPT-4o (works with your API key)
codex exec --model gpt-4o "your prompt"

# Available models you can use:
# - gpt-4o
# - gpt-4o-mini
# - gpt-4-turbo
```

## 📁 Repository Context

Codex automatically understands:
- **Repository Structure**: All directories and files
- **Git Status**: Current changes and branch
- **File Contents**: Can read and analyze code
- **Architecture**: Understands the AI swarms, MCP server, etc.

### Example Context-Aware Queries:
```bash
# Swarms Analysis
codex exec "Explain the swarm patterns implemented in app/swarms/"

# MCP Server
codex exec "How does the MCP server in dev-mcp-unified/ work?"

# Agent Factory
codex exec "Help me understand the agent factory architecture"

# Business Logic
codex exec "Explain the Sophia business intelligence components"
```

## ⚡ Pro Tips

1. **Use specific models**: Always specify `--model gpt-4o` to avoid 401 errors
2. **Repository awareness**: Codex knows your entire codebase - ask about specific files/components
3. **Code generation**: It can create new files and modify existing ones
4. **Architecture help**: Great for understanding complex systems like your swarms
5. **Debugging**: Can analyze logs, errors, and suggest fixes

## 🔍 Troubleshooting

### If you get 401 Unauthorized:
```bash
# Re-login with API key
codex logout
codex login --api-key "your-key-here"
```

### Model Access Issues:
- Use `--model gpt-4o` instead of default GPT-5
- Your OpenAI account may not have access to newer models

### Environment Issues:
```bash
# Verify API key is set
echo $OPENAI_API_KEY

# Check login status
codex login status
```

## 🎯 Ready to Use!

Codex is now properly connected to your sophia-intel-ai repository and can:
- Analyze your swarms architecture
- Help with MCP server development
- Assist with agent factory implementation
- Understand business logic in Sophia components
- Generate code that fits your existing patterns

Try: `codex exec --model gpt-4o "Help me plan the next phase of the agent factory"`