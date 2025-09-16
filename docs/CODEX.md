Codex Integration Overview

What’s included
- PR review workflow: `.github/workflows/codex-review.yml`
  - Uses `codex-ai/review-action@v1` to generate a PR review.
  - Accepts `CODEX_API_KEY` or `OPENAI_API_KEY` (prefers `CODEX_API_KEY`).
  - Falls back to a local `codex` CLI if present on PATH.
- Example config: `.codexrc.yml.example` for local aliases and default model.
- Full guide: see `docs/development/codex-cli.md` for ARM64 install, auth, aliases, and troubleshooting.
- NPM scripts (optional local helpers):
  - `npm run codex:chat -- -p "Hello"`
  - `npm run codex:agent -- --dir .`
  - `npm run codex:review`

Default model
- Local config prefers `chatgpt-5` for general coding via Codex; `gpt-5-codex` remains available as alias `g5c`.

Complete local setup & Git sync
- See `codex-setup/CODEX_SETUP_INSTRUCTIONS.md` for an end-to-end executable script and an agent prompt to automate verification, key persistence, repo sync, and CI checks.

Secrets
- Add one of the following repo or org secrets in GitHub → Settings → Secrets and variables → Actions:
  - `CODEX_API_KEY` (preferred)
  - `OPENAI_API_KEY` (fallback if `CODEX_API_KEY` is absent)

How to verify
- Open any PR (e.g., a docs edit). The workflow “Codex PR Review” runs and posts a comment.
- In the job logs:
  - “Check API key presence” shows which key is available (masked).
  - If the action succeeds, a `codex-review.md` is created and commented.
  - If the action fails and a local `codex` exists on PATH, the CLI fallback attempts a review.

Notes
- If you prefer disabling Codex CI entirely, remove the workflow at `.github/workflows/codex-review.yml` or move it back to `.github/workflow-templates/`.
- The CLI fallback is best-effort and only runs if a `codex` binary is already available on the runner or environment.
