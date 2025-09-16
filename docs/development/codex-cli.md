Codex CLI (Apple Silicon Ready)

Overview
- Purpose: Native CLI for quick chats, one‑shots, and repo agent runs.
- Scope: Developer local tool only. This repo does not depend on Codex at runtime.
- Policy: Follow External Toolbox policy — installed per‑user, not vendored here. CI workflow is provided as a template, not enabled.

Install (ARM64 macOS, M1/M2/M3)
- Homebrew (preferred):
  - `arch -arm64 brew install codex-cli`
  - If previously installed via Rosetta: `arch -arm64 brew uninstall codex-cli && arch -arm64 brew install codex-cli`
- npm (alternative):
  - `arch -arm64 npm install -g @codex/cli`

Verify Binary & PATH
- Binary arch: `file $(which codex)` → should output `Mach-O 64-bit executable arm64`.
- If `codex` not found and you use Homebrew, ensure Apple Silicon prefix on PATH:
  - `echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile && source ~/.zprofile`

Authenticate
- Add key to shell init (no quotes around value):
  - `echo 'export CODEX_API_KEY="sk-xxxxx"' >> ~/.zshrc && source ~/.zshrc`
- Security: Do not commit keys. This repo never stores provider secrets.

Config (aliases + defaults)
- Create `~/.codexrc.yml` or copy our example:
  - From repo root: `cp .codexrc.yml.example ~/.codexrc.yml`
- Recommended content:
  - `default_model: gpt-5-codex`
  - `aliases:`
    - `g5c: gpt-5-codex`
    - `g5: gpt-5`
    - `g4: gpt-4`
    - `codex: gpt-5-codex`

Usage
- Quick chat: `codex chat --model gpt-5-codex -p "Summarize our MCP servers"`
- One‑shot run: `codex run "Generate a FastAPI SSE route" --model gpt-5-codex`
- Agent in a repo: `codex agent --model gpt-5-codex --dir ~/my-project`
- With aliases (after config): `codex chat -m g5c -p "Draft migration plan"`

GitHub PR Review (Template Only)
- A PR review workflow is enabled in this repo at `.github/workflows/codex-review.yml`.
- It prefers `CODEX_API_KEY` but also accepts `OPENAI_API_KEY` (fallback).
- It uses a GitHub Action by default and only attempts a CLI fallback if a `codex` binary is present on PATH.

Template snippet
```
name: Codex PR Review
on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
permissions:
  contents: read
  pull-requests: write
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install Codex CLI
        run: npm install -g @codex/cli
      - name: Run GPT-5-Codex review
        env:
          CODEX_API_KEY: ${{ secrets.CODEX_API_KEY }}
        run: |
          codex review --model gpt-5-codex --format markdown > codex-review.md || true
      - name: Comment review on PR
        if: always()
        uses: actions/github-script@v7
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          script: |
            const fs = require('fs');
            const { context, core } = require('@actions/github');
            const body = fs.existsSync('codex-review.md') ? fs.readFileSync('codex-review.md', 'utf8') : 'Codex review did not produce output.';
            const pr = context.payload.pull_request;
            if (!pr) {
              core.setFailed('No pull request context.');
            } else {
              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: pr.number,
                body
              });
            }
```

Troubleshooting
- Rosetta contamination: `ps -o arch= -p $(pgrep -f codex)` → must show `arm64`. If `i386`, reinstall via `arch -arm64`.
- Node path (for npm installs): `arch -arm64 node -v` should use ARM64 Node; if not, reinstall Node (nvm/Homebrew) under ARM64.
- Key not picked up: ensure `echo $CODEX_API_KEY` prints a value in your current shell.

Alignment with AGENTS.md
- No cross‑imports or in‑repo UI; Codex remains a developer tool.
- CI template is optional and lives as a template only (policy‑compliant).
- No hardcoded secrets; use env variables and GitHub Actions secrets.
