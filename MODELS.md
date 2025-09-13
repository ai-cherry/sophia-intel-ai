Centralized Model Controls

Purpose
- Give you one place to see and change which LLM models are used by your CLIs and use cases.

Config file
- `config/models.json`
  - `aliases`: alias → model
  - `usecases`: usecase → alias (e.g., coding.fast → fast)
  - `cli_defaults`: cli → alias (claude|gemini|lite|codex)

CLI helper
- `./dev models show`                      # view config
- `./dev models set alias <alias> <model>` # map alias to model
- `./dev models set usecase <use> <alias>` # map usecase to alias
- `./dev models set cli <cli> <alias>`     # set default alias per CLI
- `./dev models resolve alias <alias>`     # print model
- `./dev models resolve usecase <use>`     # print model
- `./dev models resolve cli <cli>`         # print model

Using models in terminal
- `./dev ai claude -p "…"` → uses cli default model for claude
- Use Gemini via LiteLLM: `./dev ai lite --usecase analysis.large_context -p "…"` or `--model gemini-1.5-pro`
- `./dev ai lite --model gpt-4-turbo -p "…"` → force a specific model

Tips
- Keep `aliases` in sync with the models declared in `litellm-complete.yaml`.
- For quick switching, set CLI defaults to your preferred aliases:
  `./dev models set cli gemini analytical`
