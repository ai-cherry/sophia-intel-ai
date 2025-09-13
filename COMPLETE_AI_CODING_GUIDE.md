# 🚀 Sophia Intel AI - Complete AI Coding Guide

## Table of Contents
1. [Quick Start (2 minutes)](#-quick-start-2-minutes)
2. [Web UI & Dashboard](#-web-ui--dashboard)
3. [AI Coding Examples](#-ai-coding-examples)
4. [API Keys & Security](#-api-keys--security)
5. [Advanced Features](#-advanced-features)
6. [Troubleshooting](#-troubleshooting)

---

## 🎯 Quick Start (2 minutes)

### Step 1: Start Everything
```bash
cd ~/sophia-intel-ai
./sophia start
```

This starts:
- ✅ LiteLLM Proxy (port 4000) - 25+ AI models
- ✅ MCP Memory (port 8081) - Persistent context
- ✅ MCP Filesystem (port 8082) - File operations
- ✅ MCP Git (port 8084) - Version control
- ✅ Redis (port 6379) - Caching

### Step 2: Open Web UI
```bash
# Option 1: Web Dashboard (if available)
open http://localhost:3000

# Option 2: Terminal AI
./dev ai claude -p "Help me build a REST API"

# Option 3: Use with Cursor IDE
cursor .  # MCP servers auto-connect
```

### Step 3: Quick Test
```bash
# Test all systems
./sophia test

# Verify API keys
python3 test_api_keys.py
```

---

## 🌐 Web UI & Dashboard

### Available Interfaces

#### 1. **Unified Hub** (Port 3000)
```bash
# Check if running
curl http://localhost:3000/health

# Access dashboard
open http://localhost:3000
```

Features:
- Service status monitoring
- Chat interface
- API testing
- Real-time metrics

#### 2. **API Server** (Port 8005)
```bash
# Swagger docs
open http://localhost:8005/docs
```

#### 3. **Monitoring** (Port 8002)
```bash
open http://localhost:8002
```

### Starting the Web UI
```bash
# If not auto-started
cd ~/sophia-intel-ai
python3 -m uvicorn app.main_unified:app --port 3000 --reload
```

---

## 💻 AI Coding Examples

### Example 1: Simple Chat Completion
```python
#!/usr/bin/env python3
"""Quick AI chat example."""

from agents.load_env import load_master_env
load_master_env()  # Load all API keys

import openai
client = openai.OpenAI()

response = client.chat.completions.create(
    model="gpt-4-turbo",
    messages=[{"role": "user", "content": "Write a Python fibonacci function"}]
)
print(response.choices[0].message.content)
```

### Example 2: Multi-Model Comparison
```python
#!/usr/bin/env python3
"""Compare responses from multiple AI models."""

import requests

def ask_all_models(prompt):
    """Ask the same question to multiple models via LiteLLM."""
    models = ["gpt-4", "claude-3-5-sonnet", "gemini-1.5-pro", "groq-llama3-70b"]
    
    for model in models:
        response = requests.post(
            "http://localhost:4000/v1/chat/completions",
            headers={"Authorization": "Bearer sk-litellm-master-2025"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 100
            }
        )
        
        if response.status_code == 200:
            content = response.json()['choices'][0]['message']['content']
            print(f"\n{model}:\n{content[:200]}...")
        else:
            print(f"\n{model}: Error {response.status_code}")

# Load environment and run
from agents.load_env import load_master_env
load_master_env()
ask_all_models("Explain quantum computing in one sentence")
```

### Example 3: Context-Aware Agent with Memory
```python
#!/usr/bin/env python3
"""Agent that remembers conversation context."""

import requests
import json

class MemoryAgent:
    def __init__(self, session_id="default"):
        self.session_id = session_id
        self.memory_url = "http://localhost:8081"
        
    def remember(self, content, role="user"):
        """Store in memory."""
        requests.post(
            f"{self.memory_url}/sessions/{self.session_id}/memory",
            json={"content": content, "role": role}
        )
    
    def recall(self):
        """Get conversation history."""
        response = requests.get(
            f"{self.memory_url}/sessions/{self.session_id}/memory"
        )
        if response.status_code == 200:
            data = response.json()
            return [{"role": e["role"], "content": e["content"]} 
                    for e in data.get("entries", [])]
        return []
    
    def chat(self, message):
        """Chat with memory context."""
        # Store user message
        self.remember(message, "user")
        
        # Get full context
        messages = self.recall()
        
        # Call AI with context
        response = requests.post(
            "http://localhost:4000/v1/chat/completions",
            headers={"Authorization": "Bearer sk-litellm-master-2025"},
            json={
                "model": "claude-3-5-sonnet",
                "messages": messages
            }
        )
        
        if response.status_code == 200:
            ai_response = response.json()['choices'][0]['message']['content']
            self.remember(ai_response, "assistant")
            return ai_response
        return "Error calling AI"

# Usage
agent = MemoryAgent("project-x")
print(agent.chat("Let's build a TODO app"))
print(agent.chat("What database should we use?"))  # Remembers context!
```

### Example 4: Code Generation Pipeline
```python
#!/usr/bin/env python3
"""Multi-stage code generation with review."""

from agents.load_env import load_master_env
load_master_env()

import requests

def generate_code(spec):
    """Generate → Review → Refine pipeline."""
    
    # Stage 1: Generate with DeepSeek Coder
    code = call_model("deepseek-coder", f"Generate Python code for: {spec}")
    
    # Stage 2: Review with Claude
    review = call_model("claude-3-5-sonnet", 
        f"Review this code for bugs and improvements:\n{code}")
    
    # Stage 3: Refine with GPT-4
    final = call_model("gpt-4", 
        f"Refine this code based on review:\nCode:{code}\nReview:{review}")
    
    return final

def call_model(model, prompt):
    response = requests.post(
        "http://localhost:4000/v1/chat/completions",
        headers={"Authorization": "Bearer sk-litellm-master-2025"},
        json={"model": model, "messages": [{"role": "user", "content": prompt}]}
    )
    return response.json()['choices'][0]['message']['content']

# Generate a complete feature
code = generate_code("REST API endpoint for user authentication with JWT")
print(code)
```

### Example 5: Using Portkey for Load Balancing
```python
#!/usr/bin/env python3
"""Use Portkey virtual keys for automatic failover."""

import os
from portkey_ai import Portkey

# Load environment
from agents.load_env import load_master_env
load_master_env()

# Initialize with virtual keys for redundancy
portkey = Portkey(
    api_key=os.getenv("PORTKEY_API_KEY"),
    virtual_keys={
        "primary": os.getenv("PORTKEY_VK_ANTHROPIC"),
        "fallback": os.getenv("PORTKEY_VK_OPENAI"),
        "backup": os.getenv("PORTKEY_VK_GROQ")
    }
)

# Automatic failover if primary fails
response = portkey.chat.completions.create(
    model="claude-3-opus",  # Will fallback to GPT-4 if needed
    messages=[{"role": "user", "content": "Design a microservices architecture"}]
)
print(response.choices[0].message.content)
```

---

## 🔑 API Keys & Security

### Current Configuration
All keys are in `.env.master` with proper security:

```bash
# Location
~/sophia-intel-ai/.env.master

# Security Check
ls -la .env.master  # Should show: -rw------- (600)
git check-ignore .env.master  # Should output: .env.master
```

### Available API Keys (23 total)

#### Primary AI (5)
- `ANTHROPIC_API_KEY` - Claude models
- `OPENAI_API_KEY` - GPT models  
- `XAI_API_KEY` / `GROK_API_KEY` - Grok
- No direct Google key; use `OPENROUTER_API_KEY`/`AIMLAPI_API_KEY`/`TOGETHER_API_KEY` for Gemini

#### Fast Inference (6)
- `GROQ_API_KEY` - Ultra-fast inference
- `DEEPSEEK_API_KEY` - Code specialist
- `MISTRAL_API_KEY` - European models
- `PERPLEXITY_API_KEY` - Web search
- `OPENROUTER_API_KEY` - 100+ models
- `TOGETHER_API_KEY` - Open models

#### Specialized (5)
- `ELEVENLABS_API_KEY` - Voice synthesis
- `STABILITY_API_KEY` - Image generation
- `ASSEMBLY_API_KEY` - Speech-to-text
- `HUGGINGFACE_API_TOKEN` - Open source models
- `EDEN_AI_API_KEY` - Multi-provider

#### Infrastructure (7)
- `PORTKEY_API_KEY` - Load balancing
- `PORTKEY_VK_*` - 10 virtual keys for failover
- `MEM0_API_KEY` - Long-term memory
- `LITELLM_MASTER_KEY` - Proxy auth
- `AGNO_API_KEY` - Agent orchestration

### Testing Keys Work
```bash
# Quick test
python3 test_api_keys.py

# Manual test
curl -s -X POST http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer sk-litellm-master-2025" \
  -H "Content-Type: application/json" \
  -d '{"model": "claude-3-5-sonnet", "messages": [{"role": "user", "content": "Hi"}]}'
```

---

## 🚀 Advanced Features

### 1. Terminal AI Commands
```bash
# Quick AI interactions
./dev ai claude -p "Analyze this codebase for security issues"
./dev ai codex "Write SQL for monthly revenue report"
./dev ai lite --usecase analysis.large_context -p "Explain the architecture"
./dev ai lite --model analytical -p "Find performance bottlenecks"
```

### 2. Cursor IDE Integration
MCP servers auto-connect when you open Cursor:
```bash
cursor .  # Opens with full MCP context
```

Config at `.cursor/mcp.json`:
- Memory persistence across sessions
- File system access
- Git integration

### 3. Available Models (25+)
```bash
# List all models
curl http://localhost:4000/v1/models \
  -H "Authorization: Bearer sk-litellm-master-2025" \
  | jq -r '.data[].id'
```

Includes:
- **OpenAI**: gpt-4-turbo, gpt-4, gpt-3.5-turbo, gpt-o1-preview
- **Anthropic**: claude-3-opus, claude-3-5-sonnet, claude-3-5-haiku
- **Google**: gemini-1.5-pro, gemini-1.5-flash, gemini-2.0-flash
- **Groq**: groq-llama3-70b, groq-mixtral-8x7b
- **DeepSeek**: deepseek-coder, deepseek-chat
- **Mistral**: mistral-large, mistral-medium
- **xAI**: grok-2, grok-2-vision
- **Together**: llama3-70b, mixtral-8x22b, qwen-72b
- **Perplexity**: perplexity-online

### 4. Service Monitoring
```bash
# Check all services
./sophia status

# Detailed health
./dev status

# Watch logs
./sophia logs
```

---

## 🔧 Troubleshooting

### Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| "API key not found" | Run `./scripts/ensure_env.sh` to verify keys loaded |
| "Port already in use" | `./sophia clean` then `./sophia start` |
| "Model not available" | Check model name with `/v1/models` endpoint |
| "Web UI not loading" | Start manually: `python3 -m uvicorn app.main_unified:app --port 3000` |
| "Memory not persisting" | Check Redis: `redis-cli -p 6379 ping` |

### Verify Everything Works
```bash
# Full system test
cd ~/sophia-intel-ai
./sophia test
python3 test_api_keys.py
./test_simple.sh
```

---

## 📚 Documentation Structure

### File Purposes:
- **THIS FILE** (`COMPLETE_AI_CODING_GUIDE.md`) - Everything you need to code with AI
- `START_HERE.md` - Focus on API keys and environment setup
- (deprecated) `docs/START_HERE_2025.md` → see `START_HERE.md` for service management and infrastructure
- `agents/AGENT_ENV_EXAMPLES.md` - Code examples for agent development
- `docs/API_KEYS_CONSOLIDATED.md` - Detailed key reference

---

## 🎨 UI/UX Improvements Needed

### Current Pain Points:
1. **No unified dashboard** - Services scattered across ports
2. **Manual startup** - Web UI doesn't auto-start
3. **No visual model selector** - Must know model names
4. **Limited monitoring** - No real-time usage metrics

### Proposed Improvements:
1. **Single Dashboard (Port 3000)**
   - Service health monitoring
   - Model playground with dropdowns
   - API key validation status
   - Usage metrics and costs
   
2. **Auto-start Web UI**
   ```bash
   # Add to sophia script
   python3 -m uvicorn app.main_unified:app --port 3000 &
   ```

3. **Visual Model Selector**
   - Dropdown with categories
   - Show pricing/speed info
   - Test button for each model

4. **Improved Terminal UX**
   ```bash
   # Simpler commands
   ai "Build a TODO app"  # Auto-selects best model
   ai --fast "Quick question"  # Uses Groq
   ai --best "Complex analysis"  # Uses GPT-4/Claude
   ```

---

## 🚦 Quick Reference

```bash
# Start everything
./sophia start

# Quick AI chat
./dev ai claude -p "Your prompt here"

# Open web UI
open http://localhost:3000

# Test a model
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer sk-litellm-master-2025" \
  -H "Content-Type: application/json" \
  -d '{"model": "claude-3-5-sonnet", "messages": [{"role": "user", "content": "Hello"}]}'

# Check status
./sophia status

# Stop everything
./sophia stop
```

---

**Last Updated**: 2025-09-13 | **Status**: ✅ Fully Operational | **API Keys**: 23 configured
