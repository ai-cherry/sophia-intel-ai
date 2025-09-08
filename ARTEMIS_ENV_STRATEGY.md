# Artemis CLI Agent Environment Strategy

## Current Situation Analysis

### Problems Identified
1. **Secret exposure risk**: `.env.template` contains actual API keys (CRITICAL SECURITY ISSUE)
2. **No artemis-cli directory**: Expected at `../artemis-cli` but doesn't exist
3. **Mixed env approaches**: Multiple .env files with overlapping purposes
4. **Docker volume assumptions**: Compose expects artemis-cli to exist for volume mounting

### Current Environment Files
- `.env.example`: Has placeholders for LLM keys (good)
- `.env.template`: Contains ACTUAL API KEYS (security risk!)
- `.env.sophia.example`: Infrastructure only (correct separation)
- `.env.mcp.example`: MCP runtime config (correct separation)
- `.env`: Used by docker-compose.multi-agent.yml (loads all keys)

## Recommended Strategy

### Option 1: User Home Directory (RECOMMENDED)
```bash
# Store sensitive keys in user's home directory
~/.config/artemis/env
```

**Advantages:**
- Secure: Outside git repository
- Persistent: Survives repo updates
- Shareable: Multiple projects can access
- Standard: Follows XDG Base Directory spec

**Implementation:**
```bash
# Create secure config directory
mkdir -p ~/.config/artemis
chmod 700 ~/.config/artemis

# Create env file with restricted permissions
touch ~/.config/artemis/env
chmod 600 ~/.config/artemis/env
```

**Docker Integration:**
```yaml
# docker-compose.multi-agent.yml
services:
  agent-dev:
    env_file:
      - ${HOME}/.config/artemis/env  # User's secure env
      - .env.sophia                   # Local infra settings
```

### Option 2: Local .env.artemis (Git-Ignored)
```bash
# In sophia-intel-ai directory
.env.artemis  # Contains LLM keys, git-ignored
```

**Advantages:**
- Simple: Single location
- Project-specific: Different keys per project

**Disadvantages:**
- Risk of accidental commit
- Must recreate for each clone

### Option 3: Environment Variable Passthrough
```bash
# Export in shell profile
export ARTEMIS_ENV_FILE="$HOME/.artemis/credentials"

# Docker reads from environment
docker-compose --env-file "$ARTEMIS_ENV_FILE" up
```

## Security Best Practices

### 1. File Permissions
```bash
# Restrict to owner only
chmod 600 ~/.config/artemis/env
```

### 2. Template Structure
```bash
# ~/.config/artemis/env
# Artemis Agent API Keys (KEEP SECURE)

# Primary LLM Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
XAI_API_KEY=xai-...
OPENROUTER_API_KEY=sk-or-...

# Additional Providers
GROQ_API_KEY=gsk_...
DEEPSEEK_API_KEY=sk-...
COHERE_API_KEY=...

# Provider Selection
DEFAULT_PROVIDER=openai
FALLBACK_PROVIDERS=anthropic,xai,openrouter
```

### 3. Loading Order
```python
# scripts/unified_orchestrator.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Load in priority order
env_locations = [
    Path.home() / ".config" / "artemis" / "env",  # User config (highest priority)
    Path(".env.artemis"),                          # Project-specific
    Path(".env"),                                  # Fallback
]

for env_path in env_locations:
    if env_path.exists():
        load_dotenv(env_path, override=True)
        break
```

## Migration Steps

### 1. Create Secure Config
```bash
# Create directory structure
mkdir -p ~/.config/artemis
chmod 700 ~/.config/artemis

# Create env file from example
cp .env.example ~/.config/artemis/env
chmod 600 ~/.config/artemis/env

# Edit with your API keys
$EDITOR ~/.config/artemis/env
```

### 2. Update Docker Compose
```yaml
# docker-compose.multi-agent.yml
services:
  agent-dev:
    env_file:
      - ${HOME}/.config/artemis/env  # Secure keys
      - .env.sophia                   # Infra config
    environment:
      - ARTEMIS_CONFIG_PATH=${HOME}/.config/artemis
```

### 3. Update Scripts
```python
# scripts/agents_env_check.py
def check_artemis_env():
    """Check for artemis env in standard locations."""
    locations = [
        Path.home() / ".config" / "artemis" / "env",
        Path(".env.artemis"),
        Path(".env"),
    ]
    
    for loc in locations:
        if loc.exists():
            print(f"✅ Found artemis env: {loc}")
            return True
    
    print("❌ No artemis env found. Run: make artemis-setup")
    return False
```

### 4. Add Setup Target
```makefile
# Makefile
artemis-setup: ## Set up artemis agent environment
	@echo "Setting up Artemis agent environment..."
	@mkdir -p ~/.config/artemis
	@chmod 700 ~/.config/artemis
	@if [ ! -f ~/.config/artemis/env ]; then \
		cp .env.example ~/.config/artemis/env; \
		chmod 600 ~/.config/artemis/env; \
		echo "✅ Created ~/.config/artemis/env"; \
		echo "📝 Edit this file and add your API keys"; \
	else \
		echo "✅ Config already exists: ~/.config/artemis/env"; \
	fi
```

## Testing Strategy

### 1. Verify Loading
```bash
# Test env loading
make env-check

# Should show:
# ✅ Found artemis env: /Users/you/.config/artemis/env
# ✅ OPENAI_API_KEY configured
# ✅ ANTHROPIC_API_KEY configured
# ✅ XAI_API_KEY configured
```

### 2. Docker Validation
```bash
# Test in container
docker-compose -f docker-compose.multi-agent.yml run --rm agent-dev \
  python3 -c "import os; print('Keys loaded:', bool(os.getenv('OPENAI_API_KEY')))"
```

### 3. Security Audit
```bash
# Ensure no keys in repo
git grep -E "sk-|xai-|gsk_" --cached

# Check file permissions
ls -la ~/.config/artemis/env
# Should show: -rw------- (600)
```

## Immediate Actions Required

1. **CRITICAL**: Remove actual API keys from `.env.template`
2. **Create**: `~/.config/artemis/env` with proper permissions
3. **Update**: Docker compose to use secure env location
4. **Add**: `make artemis-setup` target for easy onboarding
5. **Document**: Update README with env setup instructions

## Additional Considerations

### Multi-Environment Support
```bash
# Support multiple environments
~/.config/artemis/
  ├── env           # Default/production
  ├── env.dev       # Development keys
  └── env.test      # Test keys

# Select via environment variable
export ARTEMIS_ENV=dev
```

### Key Rotation Helper
```bash
# scripts/rotate-keys.sh
#!/bin/bash
echo "🔄 Rotating API keys..."
cp ~/.config/artemis/env ~/.config/artemis/env.backup.$(date +%Y%m%d)
echo "📝 Edit ~/.config/artemis/env with new keys"
```

### Validation Script
```python
# scripts/validate_artemis_keys.py
import os
from pathlib import Path

def validate_keys():
    required = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'XAI_API_KEY']
    missing = [k for k in required if not os.getenv(k)]
    
    if missing:
        print(f"❌ Missing keys: {', '.join(missing)}")
        print(f"📝 Add them to ~/.config/artemis/env")
        return False
    
    print("✅ All required keys present")
    return True
```

This strategy provides security, flexibility, and ease of use while keeping sensitive keys out of the repository.