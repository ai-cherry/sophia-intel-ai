# Devcontainer Notes – No UI In Repo

- This repo is backend-only (BI + MCP). Do not add UI files here.
- External UIs live as sibling worktrees:
  - ../worktrees/forge-ui (3100)
  - ../worktrees/portkey-ui (3200)
  - ../worktrees/sophia-bi-ui (3300)

Use MCP canonical ports (8081/8082/8084) and load <repo>/.env.master server-side.

