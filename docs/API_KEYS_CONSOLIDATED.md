# API Keys - FINALLY FUCKING CONSOLIDATED

## THE SINGLE SOURCE OF TRUTH
**Location**: `/Users/lynnmusil/sophia-intel-ai/.env.master`

## Your Actual API Keys (Not Placeholders!)

### Primary AI Providers
- **Anthropic**: `sk-ant-api03-XK_Q7m6...` ✅
- **OpenAI**: `sk-svcacct-zQTWLUH06...` ✅  
- **XAI/Grok**: `xai-4WmKCCbqXhuxL56t...` ✅
- **Gemini (via OpenRouter)**: uses `OPENROUTER_API_KEY` ✅

### Additional Providers
- **Groq**: `gsk_Dy4dN7znDj9KKbr5...` ✅
- **DeepSeek**: `sk-c8a5f1725d7b4f96b...` ✅
- **Mistral**: `jCGVZEeBzppPH0pPVL0v...` ✅
- **Perplexity**: `pplx-XfpqjxkJeB3bz3Hm...` ✅
- **OpenRouter**: `sk-or-v1-d00d1c302a67...` ✅
- **Together AI**: `tgp_v1_HE_uluFh-fELZ...` ✅

### Specialized Services  
- **ElevenLabs**: `sk_0b68a8ac28119888...` ✅
- **Stability AI**: `sk-d3ym0y0RKM841TtSR...` ✅
- **Assembly AI**: `915990f9d7b64eb2bf8f...` ✅
- **HuggingFace**: `hf_cQmhkxTVfCYcdYnYR...` ✅
- **Mem0**: `m0-migu5eMnfwT41nhTg...` ✅
- **Portkey**: `nYraiE8dOR9A1gDwaRNp...` ✅

## How It's Used

### 1. Master Control Script (`sophia`)
Automatically sources `.env.master` on every start:
```bash
./sophia start  # All services get real keys
```

### 2. Dev CLI (`./dev`)
Inherits from sophia script

### 3. Python Scripts
```python
import os
from pathlib import Path

env_file = Path.home() / "sophia-intel-ai" / ".env.master"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value.strip('"')
```

### 4. Shell Scripts
```bash
source ~/sophia-intel-ai/.env.master
```

### 5. Node.js
```javascript
require('dotenv').config({ 
  path: '/Users/lynnmusil/sophia-intel-ai/.env.master' 
});
```

## File Security
```bash
-rw-------@ 1 lynnmusil  staff  5051  # Mode 600 - Only you can read/write
```

## Other Files That Had Keys (Now Obsolete)
- `centralized_config.yaml` - Still has keys but not primary source
- Various `.env.example`, `.env.template` files - Ignore these
- Random Python/YAML files - All should reference `.env.master`

## Testing Keys Work
```bash
# Quick test
cd ~/sophia-intel-ai
./scripts/ensure_env.sh  # Verifies all keys present

# Test with LiteLLM (Gemini via OpenRouter)
curl -s http://localhost:4000/v1/models \
  -H "Authorization: Bearer sk-litellm-master-2025" \
  | jq '.data | length'
# Should show 25+ models
```

## Troubleshooting

### If a service can't find keys:
1. Check it's sourcing `.env.master`
2. Run `./scripts/ensure_env.sh` to verify
3. Restart service with `./sophia restart`

### If you get "your-key-here" errors:
Some file is using a template instead of `.env.master`. Find it:
```bash
grep -r "your-key-here" ~/sophia-intel-ai --include="*.env*" --include="*.py"
```

## THE RULE
**`.env.master` is the ONLY place for real keys. Everything else must reference it.**

No more bullshit. No more duplicates. No more "your-key-here".

---

Last verified: 2025-09-13 04:38 AM
Total API keys: 22
All working: YES
