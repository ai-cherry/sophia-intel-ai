# Opencode CLI with Portkey Integration - Setup Complete

## ✅ Installation Verified
- **Opencode v0.7.6** installed at `~/.opencode/bin/opencode`
- **ARM64 native** on M3 Mac (macOS 15.6.1)
- **Test repo created** at `~/test-repo` with working Python generation

## 🔧 Configuration Steps

### 1. Basic Auth (Working)
Environment variables detected:
- `ANTHROPIC_API_KEY` ✅
- `OPENAI_API_KEY` ✅  
- `DEEPSEEK_API_KEY` ✅
- `XAI_API_KEY` ✅

### 2. Portkey Integration Setup

**Step 1: Get Portkey Virtual Key**
```bash
# Register at dashboard.portkey.ai
# Create virtual key: Add Key → Link providers → Get pk-vk-xxx
```

**Step 2: Add Portkey via CLI**
```bash
opencode auth login
# Select "Other" → Name: "portkey" 
# API Key: pk-vk-your-virtual-key
# Base URL: https://api.portkey.ai/v1
```

**Step 3: Manual Config Alternative**
Create `~/.config/opencode/opencode.json`:
```json
{
  "providers": {
    "portkey": {
      "baseURL": "https://api.portkey.ai/v1",
      "apiKey": "pk-vk-your-virtual-key",
      "headers": {
        "x-portkey-config": "{\"strategy\": {\"mode\": \"fallback\"}, \"targets\": [{\"virtual_key\": \"anthropic-sub\"}, {\"virtual_key\": \"openai-sub\"}]}"
      }
    }
  }
}
```

## 🚀 Usage Examples

### CLI Mode (Working Now)
```bash
cd ~/test-repo
opencode run "Generate a Python function for API calls"
opencode run --model "anthropic/claude-3-5-sonnet-20241022" "Create a REST API"
```

### TUI Mode 
```bash
cd ~/test-repo  
opencode  # Interactive TUI with chat/code/explorer
```

### With Portkey (After Setup)
```bash
opencode run --provider portkey "Generate secure authentication code"
```

## 🎯 Agent Configuration

Create agents in config:
```json
{
  "agents": {
    "coder": {
      "provider": "portkey",
      "model": "openai/gpt-4o", 
      "instructions": "Write clean, secure code with error handling"
    },
    "reviewer": {
      "provider": "portkey", 
      "model": "anthropic/claude-3.5-sonnet",
      "instructions": "Review code for bugs and security issues"
    }
  }
}
```

Usage:
```bash
opencode agent coder "Build a REST API with authentication"
```

## 🛡️ Portkey Benefits
- **Virtual Keys**: Hide real API keys (pk-vk-xxx format)
- **Fallbacks**: OpenAI → Claude → Groq automatic switching  
- **Load Balancing**: Distribute requests across providers
- **Cost Control**: Set budgets and limits per virtual key
- **Analytics**: Dashboard tracking for usage/costs

## 🔧 Troubleshooting
- **Config errors**: Remove custom config, use env vars + interactive auth
- **TUI issues**: Set `TERM=xterm-256color` in `.zshrc`
- **ARM performance**: Native binary optimized for M3
- **Portkey setup**: Dashboard.portkey.ai for virtual key creation

## 📁 Files Created
- `~/test-repo/hello.py` - Working Python test
- `~/.opencode/bin/opencode` - ARM64 binary
- `~/.config/opencode/` - Config directory ready

**Status**: ✅ Ready for Portkey virtual key integration
**Next**: Get pk-vk-xxx from dashboard.portkey.ai