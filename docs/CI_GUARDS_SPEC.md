CI Guards Spec (Hard Fail)

Workflow: `.github/workflows/no-legacy-stack.yml`
- Fails on forbidden patterns anywhere in repo (code + docs + configs):
  - `builder-agno-system`
  - `sophia-intel-app` (as in-repo path; allow only if explicitly saying “external”)
  - local LLM proxy ports or binaries
  - `/frontend\b`
  - `mcp/filesystem.py`
  - `mcp/git_server.py`
  - `npx\s+create-sophia-intel-app`
  - `http://localhost:4000`
  - `:8090`

Runtime linter (hard fail)
- No `dotenv`/`from dotenv`/`load_dotenv`; no `~/.config` or `expanduser(.config)` in `app/`, `mcp/`, `backend/`, `services/` (exclude lockfiles).

One-True-Dev messaging
- `README.md` and `AGENTS.md` must link to `docs/ONE_TRUE_DEV_FLOW.md` and `docs/CODING_UI_STANDALONE.md` and explicitly state “No UI in this repo”.
