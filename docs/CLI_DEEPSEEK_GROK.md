DeepSeek & Grok CLI

Overview
- CLIs live at repo root: `grok_cli.py`, `deepseek_cli.py`.
- Convenience wrappers: `grok`, `deepseek` (call the Python scripts from `~/sophia-intel-ai`).
- Uses existing LLM client (`app.llm.multi_transport.MultiTransportLLM`).
- Reads keys from `<repo>/.env.master` loaded by `./sophia start` (no prompts).

Required Keys
- Preferred location: `<repo>/.env.master` (picked up by `./sophia`).
- For Grok via OpenRouter: set `OPENROUTER_API_KEY`.
- For Grok direct: set `XAI_API_KEY` (alias `GROK_API_KEY` also supported).
- For DeepSeek via OpenRouter: set `OPENROUTER_API_KEY`.
- For DeepSeek direct: set `DEEPSEEK_API_KEY`.

Grok CLI
- Dry-run (no network):
  `python3 grok_cli.py --prompt "Hello" --dry-run`
- OpenRouter (default if `OPENROUTER_API_KEY` present):
  `python3 grok_cli.py --prompt "Explain RAG in 3 bullets"`
- Direct xAI (if `XAI_API_KEY` present and no OPENROUTER key):
  `python3 grok_cli.py -p "Summarize this repo" --provider xai`
- Override model:
  `python3 grok_cli.py -p "Refactor plan" --model x-ai/grok-code-fast-1`
- System prompt and JSON output:
  `python3 grok_cli.py -s "You are precise" -p "Create a checklist" --json`

DeepSeek CLI
- Dry-run (no network):
  `python3 deepseek_cli.py --prompt "Hello" --dry-run`
- Chat model via OpenRouter (default when `OPENROUTER_API_KEY` present):
  `python3 deepseek_cli.py -p "Draft a PR description"`
- Reasoning (R1) via OpenRouter:
  `python3 deepseek_cli.py -p "Prove Pythagoras" --reasoning`
- Direct DeepSeek (if `DEEPSEEK_API_KEY` present):
  `python3 deepseek_cli.py -p "Optimize SQL query" --provider deepseek`
- From file and system prompt:
  `python3 deepseek_cli.py -f notes.txt -s "Be concise"`

Notes
- Both CLIs auto-detect provider: prefer OpenRouter when available, otherwise direct.
- Env loading order: `./sophia` loads `<repo>/.env.master` only (no fallbacks).
- Pass `--max-tokens` and `--temperature` to tune generation.
- For Portkey VKs (if configured), MultiTransport may route via Portkey automatically.
