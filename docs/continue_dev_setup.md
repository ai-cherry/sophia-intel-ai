# Continue.dev Setup for SOPHIA

This guide configures the Continue.dev extension for the SOPHIA repo in GitHub Codespaces. It explains auth, models, custom commands, and verification.

---

## 1) Prerequisites
- VS Code (or Codespaces) with the Continue.dev extension.
- SOPHIA Codespace using the repo's `.devcontainer`.
- Environment variable `CONTINUE_API_KEY` available in the shell.
- `config.yaml` at the repo root (see this directory).

---

## 2) Required Environment Variables

### Option 1: Codespaces Secrets (Recommended for CI/CD)
In your GitHub repository, go to Settings > Secrets and variables > Codespaces:
- Add `CONTINUE_API_KEY` with your Continue Hub API key
- Add `GH_API_TOKEN` with your GitHub token
- Add `PULUMI_ESC_TOKEN` for infrastructure management (optional)


### Option 2: Local .env File (Recommended for Development)
Create a local `.env.sophia` file (not committed) for all dev secrets:

```bash
cp .env.template .env.sophia
# Edit .env.sophia with your values (see below)
source .env.sophia
```

**.env.sophia is the canonical place for all dev secrets.**
Codespaces and CI will load from it or from org-level secrets automatically.

Example .env.sophia:
```
CONTINUE_API_KEY=your-continue-hub-key
GH_API_TOKEN=your-github-token
# Optional for Pulumi ESC
PULUMI_ESC_TOKEN=your-pulumi-esc-token
```

### Option 3: Export in Shell (Quick Testing)
```bash
# Continue.dev API Key
export CONTINUE_API_KEY="your-continue-hub-key"

# GitHub API Token (used by GitHub MCP server)
export GH_API_TOKEN="your-github-token"

# Optional: Pulumi ESC token
export PULUMI_ESC_TOKEN="your-pulumi-esc-token"
```

For GitHub tokens, use a Personal Access Token (fine-grained) with these permissions:
- Repository: Read access to metadata, code, pull requests
- Organization: Read access to members


**Note**: Rebuild the Codespace if you added these as Codespaces Secrets or updated `.env.sophia`.

**Pulumi ESC**: If using Pulumi ESC, ensure `PULUMI_ESC_TOKEN` is set in `.env.sophia` or Codespaces secrets.

---

## 3) What This Config Gives You
**Latest models (via Continue Hub + providers):**

| Role | Model |
|------|------|
| Default Chat | Claude 4 Opus (OpenRouter) |
| Fast Chat | Claude 4 Sonnet (OpenRouter) |
| Large Codegen/Refactor | Qwen3 Coder (OpenRouter) |
| Local Autocomplete | qwen2.5-coder 7b (Ollama) |
| Reasoning/Data Synthesis | Gemini 2.5 Pro Beta (Google) |
| Test/Scaffold | Codestral (Mistral) |
| Context-Rich | Kimi K2 (OpenRouter) |

**SOPHIA Guardrails baked into `systemMessage`:**
- MCP-first; no direct external API calls from agents.
- Stability > Resilience > Performance > Quality > Cost/Security.
- Type hints + Google-style docstrings.
- Envelope, health, pagination contracts.
- 429/5xx backoff (max 3), respect `Retry-After`.
- Never log secrets.

**Context Providers:** `schemas/`, `mcp/`, `agents/`, `docs/`, `CONTRIBUTING.md`, `README.md`.

**Slash Commands:**
- `/test` → generate pytest tests (fixtures/mocks, edge cases, fast).
- `/docstring` → produce Google-style docstrings.
- `/refactor` → return a unified diff to align with SOPHIA standards.
- `/mission` → create `missions/<NNN>_new_mission.md` diff from a brief.

Routing picks the best model per command automatically.

---

## 4) Verify It Works
1. **Reload window**: `Developer: Reload Window` in VS Code.
2. **Health quickcheck**:
   - Open any Python file; type `/docstring` on a small function → expect a clean Google-style docstring.
3. **Generate tests**:
   - Highlight a function that uses httpx/backoff/envelopes; run `/test` → expect a pytest file proposal with fixtures and monkeypatch.
4. **Refactor**:
   - Highlight legacy code; run `/refactor` → expect a unified diff aligning to SOPHIA patterns.
5. **Mission**:
   - Select a short feature brief; run `/mission` → expect a diff adding `missions/<NNN>_new_mission.md`.

---

## 5) Troubleshooting
| Symptom | Fix |
|---|---|
| "Unauthorized" or model fails | Ensure `CONTINUE_API_KEY` is set and window reloaded. |
| Local autocomplete missing | Start Ollama (or Continue will fall back to default chat). |
| Model slug error | Update `config.yaml` model field to the exact slug shown on hub.continue.dev. |
| No context awareness | Confirm `config.yaml` is at repo root. Reload window. |

---

## 6) Notes for PRs
- This config is **read-only safe**—no secrets in repo.
- Model choices are centralized here; future upgrades mean adjusting one file.
- Keep the slash command prompts aligned with architecture guardrails.
