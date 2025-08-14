# Migration Guide: Portkey → OpenRouter Direct

## Overview
This migration removes the Portkey middleware and implements direct OpenRouter integration for improved performance, reduced complexity, and better cost control.

## Changes Made

### 1. Removed Files
- `services/portkey_client.py` - Replaced with `services/openrouter_client.py`
- `config/portkey_config.json` - Replaced with `config/openrouter_config.json`
- `scripts/test_portkey_fix.py` - No longer needed

### 2. Updated Files
- All workflow files (`.github/workflows/*.yml`)
- Documentation (`README.md`, `.prompts/*.md`)
- Infrastructure code (`infra/*.py`)
- Requirements (`requirements.txt`)

### 3. New Implementation
- **Direct API calls** to OpenRouter (no middleware)
- **Async/await support** for better performance
- **Built-in retry logic** with exponential backoff
- **Cost tracking and estimation**
- **Model recommendation system**
- **Streaming support**

## Code Migration

### Before (Portkey)
```python
from services.portkey_client import PortkeyClient

client = PortkeyClient()
response = await client.chat_completion(messages)
```

### After (Direct OpenRouter)
```python
from services.openrouter_client import OpenRouterClient

async with OpenRouterClient() as client:
    response = await client.chat_completion(messages)
```

## Environment Variables

### Removed
- `PORTKEY_API_KEY`
- `PORTKEY_CONFIG`

### Required
- `OPENROUTER_API_KEY` (existing, no change needed)

## Benefits

1. **Performance**: Direct API calls eliminate middleware latency
2. **Simplicity**: Fewer dependencies and configuration layers
3. **Cost Control**: Built-in cost estimation and tracking
4. **Reliability**: Custom retry logic optimized for OpenRouter
5. **Transparency**: Full control over API interactions

## Testing

Run the test script to verify the migration:
```bash
python3 scripts/test_openrouter_migration.py
```

## Rollback Plan

If needed, the previous Portkey integration can be restored from git history:
```bash
git checkout HEAD~1 -- services/portkey_client.py config/portkey_config.json
```
