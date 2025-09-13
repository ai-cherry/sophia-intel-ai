# Portkey + LiteLLM Integration with Opencode

## ✅ Configuration Complete

### 1. Opencode Config (`~/.config/opencode/opencode.json`)
Created with:
- **Portkey provider** configured with baseURL and virtual key placeholder
- **LiteLLM provider** for local proxy (disabled by default)
- **Agents** configured for coder/reviewer roles
- **Fallback providers** for automatic switching

### 2. LiteLLM Config (`litellm-config.yaml`)
Set up with:
- All your API keys (OpenAI, Anthropic, DeepSeek, xAI)
- Master key: `sk-litellm-master-key-2025`
- Portkey routing option for guarded models
- Fallback models and retry policies

## 📋 Next Steps

### To Use Portkey:
1. Get virtual key from dashboard.portkey.ai:
   - Create account → Virtual Keys → Add Key
   - Link your provider (OpenAI/Anthropic)
   - Get `pk-vk-xxx` key
   
2. Update config:
   ```bash
   sed -i '' 's/pk-vk-your-virtual-key-here/pk-vk-YOUR-ACTUAL-KEY/g' ~/.config/opencode/opencode.json
   ```

3. Test:
   ```bash
   opencode run --provider portkey "Generate code"
   ```

### To Use LiteLLM:
1. Install LiteLLM:
   ```bash
   pip install litellm
   ```

2. Start proxy:
   ```bash
   cd ~/sophia-intel-ai
   litellm --config litellm-config.yaml --port 4000
   ```

3. Enable in Opencode config:
   ```bash
   # Edit ~/.config/opencode/opencode.json
   # Change "disabled": true to "disabled": false for litellm provider
   ```

4. Test:
   ```bash
   opencode run --provider litellm "Generate code"
   ```

## 🚀 Current Status
- ✅ Opencode installed (v0.7.6)
- ✅ Config files created
- ✅ Environment API keys detected
- ⏳ Awaiting Portkey virtual key
- ⏳ LiteLLM proxy not running (start when needed)

## 🔧 Quick Commands
```bash
# Launch TUI
cd ~/test-repo && opencode

# Use with Anthropic (working now)
opencode run "Your prompt"

# Use with Portkey (after setup)
opencode run --provider portkey "Your prompt"

# Use with LiteLLM (after starting proxy)
opencode run --provider litellm "Your prompt"
```