# Policies

Authoritative policies for authority order, model routing, and access control.

- Files live under `POLICIES/` in YAML format and are version-controlled.
- MCP-specific policy files remain under `mcp/policies/` and should reference or align with root policies here.

Contents
- `POLICIES/authority.yml` — which subsystem or document is authoritative per concern.
- `POLICIES/routing.yml` — model routing rules and thresholds.
- `POLICIES/access.yml` — authentication/authorization for services and tools.

Change Control
- Propose changes via PR; include rationale and impact.
- Update related docs (README/ARCHITECTURE/DEPLOYMENT) when behavior changes.

