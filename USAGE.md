# Sophia Intel AI - Usage Guide

## 🚀 Quick Start

### First Time Setup
```bash
# Run the smart startup (handles everything)
./startup.sh

# Or use the standard start
./dev start
```

### Daily Usage
```bash
# Start everything
./dev start

# Check status
./dev status
./dev check

# Stop everything
./dev stop
```

## 💬 Using AI Models (25 Available)

### Via Portkey (server routes)
```bash
# Chat completion via Next.js proxy (uses Portkey VKs server-side)
curl http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openrouter/google/gemini-1.5-pro",
    "messages": [{"role": "user", "content": "Write a haiku about coding"}],
    "stream": false
  }'
```

### Via API
```bash
# Chat completion
curl http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer sk-litellm-master-2025" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Write a haiku about coding"}]
  }'

# List models
curl http://localhost:4000/v1/models \
  -H "Authorization: Bearer sk-litellm-master-2025"
```

### Model Aliases and Providers
- **OpenRouter**: openai/gpt-4o-mini, google/gemini-1.5-pro, anthropic/claude-3.5-sonnet
- **Together AI**: togethercomputer/llama-3.1-8b-instruct, mistralai/Mixtral-8x7B-Instruct-v0.1
- **Hugging Face**: meta-llama/Meta-Llama-3.1-8B-Instruct

## 🧠 Using MCP Servers

### Memory Server (Port 8081)
```bash
# Store memory
curl -X POST http://localhost:8081/sessions/main/memory \
  -H "Content-Type: application/json" \
  -d '{"content": "Important fact to remember", "role": "user"}'

# Retrieve memories
curl http://localhost:8081/sessions/main/memory

# Health check
curl http://localhost:8081/health
```

### Filesystem Server (Port 8082)
```bash
# List files
curl http://localhost:8082/files

# Search files
curl http://localhost:8082/search?query=test

# Health check
curl http://localhost:8082/health
```

### Git Server (Port 8084)
```bash
# Get repo info
curl http://localhost:8084/repos

# Get commits
curl http://localhost:8084/commits

# Health check
curl http://localhost:8084/health
```

## 🛠 Using CLI Tools

### Opencode
```bash
# Launch Opencode
./dev opencode
# or
./dev oc

# Opencode uses the server proxy (Portkey) by default
```

### Claude Code
```bash
# Launch Claude
./dev claude
# or
./dev cl
```

### AI Router
```bash
# Unified AI interface
./dev ai chat "Your prompt here"
./dev ai models
./dev ai help
```

## 📊 Common Workflows

### 1. Code Generation
```bash
# Using server proxy (Portkey VK)
curl http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "together_ai/mistralai/Mixtral-8x7B-Instruct-v0.1",
    "messages": [{"role": "user", "content": "Write a REST API in FastAPI"}]
  }'
```

### 2. Multi-Model Comparison
```bash
# Ask same question to different models
for model in gpt-4 claude-3-5-sonnet gemini-1.5-pro; do
  echo "=== $model ==="
  litellm-cli chat $model -p "Explain quantum computing in one sentence"
done
```

### 3. Memory-Enhanced Conversations
```bash
# Store context
curl -X POST http://localhost:8081/sessions/project/memory \
  -H "Content-Type: application/json" \
  -d '{"content": "Project uses React 18 with TypeScript", "role": "system"}'

# Use in conversation (the AI can reference stored memories)
curl http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openrouter/openai/gpt-4o-mini",
    "messages": [{"role": "user", "content": "What framework is our project using?"}]
  }'
```

## 🔧 Troubleshooting

### If services won't start:
```bash
# Kill all services and restart
./sophia stop
pkill -f mcp
./sophia start
```

### If LiteLLM gives auth errors:
```bash
# Always use the master key
export LITELLM_API_KEY="sk-litellm-master-2025"

# Or in API calls
-H "Authorization: Bearer sk-litellm-master-2025"
```

### Check what's running:
```bash
# Comprehensive check
./dev check

# Detailed status
./dev status

# Just ports
./dev doctor
```

## 🎯 Best Practices

1. **Always use `./startup.sh` for first start of the day** - It handles cleanup and validation

2. **Check logs if something fails**:
   ```bash
   tail -f logs/mcp-*.log
   ```

4. **For production workloads**, use specific models:
   - Fast: `groq-mixtral`, `gpt-3.5-turbo`
   - Quality: `gpt-4`, `claude-3-5-sonnet`
   - Code: `grok-code-fast`, `deepseek-chat`
   - Long context: `gemini-1.5-pro` (1M tokens)

## 📝 Environment Variables

Key variables (in `.env.master`):
- `LITELLM_MASTER_KEY`: sk-litellm-master-2025
- `ANTHROPIC_API_KEY`: Your Anthropic key
- `OPENAI_API_KEY`: Your OpenAI key
- No direct Google key. Use `OPENROUTER_API_KEY`/`AIMLAPI_API_KEY`/`TOGETHER_API_KEY` for Gemini.
- All other provider keys...

## 🔗 Quick Links

- **LiteLLM Proxy**: http://localhost:4000
- **Memory Server**: http://localhost:8081
- **Filesystem Server**: http://localhost:8082
- **Git Server**: http://localhost:8084
- **Redis**: localhost:6379

## 💡 Pro Tips

1. **Parallel requests** to multiple models:
   ```bash
   parallel -j 3 'litellm-cli chat {} -p "Explain AI"' ::: gpt-4 claude-3-5-sonnet gemini-1.5-pro
   ```

2. **Stream responses** for long outputs:
   ```bash
   curl http://localhost:4000/v1/chat/completions \
     -H "Authorization: Bearer sk-litellm-master-2025" \
     -H "Content-Type: application/json" \
     -d '{"model": "gpt-4", "messages": [...], "stream": true}'
   ```

3. **Use model aliases** for convenience:
   - `cheap` → gpt-3.5-turbo
   - `fast` → groq-mixtral
   - `analytical` → gemini-1.5-pro
   - `online` → perplexity-online
