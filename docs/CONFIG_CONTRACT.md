# Config Contract

Authoritative schema: `config/env.schema.json`.

Contracts
- Keys and types must match the schema.
- New keys require schema update + loader update (Python/TS) + docs update.
- Consumers should import loaders:
  - Python: `from config.python_settings import settings_from_env`
  - TS/Node: `import { loadConfig } from '../config/tsSchema'`

Provider Routing
- `AI_ROUTER`: `portkey` | `openrouter` | `direct`
- `AI_PROVIDER`: `openai` | `anthropic` | `gemini` | `mistral` | `groq` | `xai` | `cohere` | `ai21`
- Adapters should implement consistent timeouts/retries using:
  - `HTTP_DEFAULT_TIMEOUT_MS`, `HTTP_RETRY_MAX`, `HTTP_BACKOFF_BASE_MS`

Precedence
- Dev: `.env.master` → overridden by process env
- CI/Prod: process env only (from ESC)

