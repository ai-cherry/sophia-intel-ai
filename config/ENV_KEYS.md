# Environment Keys (Canonical)

This document summarizes the canonical environment variables shared across services. See `config/env.schema.json` for the authoritative schema and validation.

- APP_ENV: dev | staging | prod (default: dev)
- SERVICE_NAME: string (default: sophia-intel-ai)
- LOG_LEVEL: DEBUG | INFO | WARNING | ERROR (default: INFO)

- AI_ROUTER: portkey | openrouter | direct (default: direct)
- AI_PROVIDER: openai | anthropic | gemini | mistral | groq | xai | cohere | ai21 (default: openai)

- HTTP_DEFAULT_TIMEOUT_MS: integer ms (default: 15000)
- HTTP_RETRY_MAX: integer (0–10, default: 3)
- HTTP_BACKOFF_BASE_MS: integer ms (default: 200)

- POSTGRES_URL: connection string
- REDIS_URL: connection string
- WEAVIATE_URL: url
- NEO4J_URL: url

- MCP_TOKEN: bearer token (dev can be blank)
- MCP_DEV_BYPASS: 0 | 1 (default: 0)
- RATE_LIMIT_RPM: integer (default: 120)
- READ_ONLY: 0 | 1 (default: 0)

- OPENAI_API_KEY: string (placeholder in .env.master)
- ANTHROPIC_API_KEY: string (placeholder in .env.master)
- GOOGLE_GEMINI_API_KEY: string (placeholder in .env.master)
- MISTRAL_API_KEY: string (placeholder in .env.master)
- GROQ_API_KEY: string (placeholder in .env.master)
- XAI_API_KEY: string (placeholder in .env.master)
- COHERE_API_KEY: string (placeholder in .env.master)
- AI21_API_KEY: string (placeholder in .env.master)
- OPENROUTER_API_KEY: string (placeholder in .env.master)
- PORTKEY_API_KEY: string (placeholder in .env.master)

Notes
- `.env.master` provides safe placeholders that avoid triggering GitHub secret detectors.
- Real values come from Pulumi ESC in CI/CD by environment (dev/staging/prod).
- Load order (dev): process env overrides `.env.master`. In CI/prod: process env only.

