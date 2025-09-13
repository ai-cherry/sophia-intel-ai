#!/usr/bin/env bash
set -euo pipefail

# Centralizes the Master Architect persona for Codex and Claude CLIs
# - Creates ~/.config/{codex,claude}/personas
# - Symlinks repo persona to both CLIs as master-architect.txt
# - Optionally scaffolds default config files if missing (no secrets)

REPO_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
PERSONA_SRC="$REPO_ROOT/configs/agents/master_architect_persona.md"

if [[ ! -f "$PERSONA_SRC" ]]; then
  echo "Persona source not found: $PERSONA_SRC" >&2
  exit 1
fi

mkdir -p "$HOME/.config/codex/personas" || true
mkdir -p "$HOME/.config/claude/personas" || true
mkdir -p "$HOME/.config/sophia" || true

# Symlink persona to both CLIs
ln -sf "$PERSONA_SRC" "$HOME/.config/codex/personas/master-architect.txt"
ln -sf "$PERSONA_SRC" "$HOME/.config/claude/personas/master-architect.txt"

echo "Linked Master Architect persona to:"
echo "  ~/.config/codex/personas/master-architect.txt"
echo "  ~/.config/claude/personas/master-architect.txt"

# Scaffold default configs if missing (safe, no keys)
CODEX_CFG="$HOME/.config/codex/config.toml"
CLAUDE_CFG="$HOME/.config/claude/settings.json"

if [[ ! -f "$CODEX_CFG" ]]; then
  cat > "$CODEX_CFG" << 'EOF'
[model]
default = "gpt-4o-mini"
temperature = 0.1
max_tokens = 4096
retries = 3

[repo]
ignore_gitignore = false
index_depth = 5

[api]
rate_limit = 60
EOF
  echo "Wrote default Codex config: $CODEX_CFG"
fi

if [[ ! -f "$CLAUDE_CFG" ]]; then
  mkdir -p "$(dirname "$CLAUDE_CFG")"
  cat > "$CLAUDE_CFG" << 'EOF'
{
  "model": "claude-3-5-sonnet-20240620",
  "temperature": 0.2,
  "max_tokens": 4096,
  "retries": 3,
  "rate_limit": 50
}
EOF
  echo "Wrote default Claude settings: $CLAUDE_CFG"
fi

cat << 'NOTE'
Setup complete.

Next steps:
- Put keys in ~/.config/sophia/env (do NOT store in repo), e.g.:
    export OPENAI_API_KEY=... 
    export ANTHROPIC_API_KEY=...
- Source them in your shell or via direnv.
- Optional: add aliases to call the dev-assistant wrapper.
NOTE

