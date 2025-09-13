# Migration Plan: Sophia → Sophia Identifiers (Infra + Code)

Goal
- Remove legacy "Sophia" identifiers from infrastructure and code without breaking deployments.
- Proceed in safe phases with rollback options.

Scope
- Kubernetes manifests (names, labels, selectors)
- Pulumi ESC YAML keys and references
- Startup configs and scripts using sophia-prefixed IDs
- Environment variables and config keys

Phase 0 — Inventory (done)
- Detected 1,500+ occurrences across repo; docs scrub completed.
- High-risk areas: k8s/base/applications.yaml, pulumi-esc-*.yaml, startup-config.yml, tests/scripts referencing sophia.

Phase 1 — Non-breaking aliases (recommended)
- Do not rename running resources; add alias keys/vars and update consumers to read Sophia-first, Sophia-legacy as fallback.
- Examples:
  - Pulumi ESC: introduce `mcp_fs_sophia_port` alongside `mcp_fs_sophia_port`; update code to read Sophia key first.
  - Startup config: introduce `sophia` service names in compose/scripts while keeping `sophia` entries for now.
- Rollback: consumers still accept legacy keys.

Phase 2 — Controlled renames (per environment)
- Kubernetes:
  - Create new Deployments/Services with `*-sophia-*` names and labels; switch selectors gradually.
  - Update ArgoCD/KEDA manifests with parallel app names, then cut over.
- Pulumi:
  - Rename stacks/outputs/secret keys with a migration script; keep legacy keys during transition.
- Rollback: revert selectors to legacy; keep legacy services until stable.

Phase 3 — Legacy removal
- After verification across environments, remove Sophia keys/services, update tests, and drop fallbacks.

Concrete Renames (proposal)
- K8s labels and names:
  - `sophia-orchestrator` → `sophia-orchestrator`
  - label `app.kubernetes.io/component: sophia-orchestrator` → `sophia-orchestrator`
- Pulumi keys:
  - `mcp_fs_sophia_port` → `mcp_fs_sophia_port`
  - `sophia_path` → `sophia_path`
- Env/config:
  - `.env.*` values referencing sophia → sophia equivalents
  - startup-config.yml services `sophia`/`rag_sophia` → `sophia_orchestrator`/`rag_sophia`

Validation
- Run `scripts/docs/link_check.py`
- Run local smoke: `./sophia start && curl http://127.0.0.1:4000/v1/models`
- If using k8s: ensure both legacy and new services respond during cutover

Rollback
- Keep legacy resources until verification passes; switch selectors back; revert to legacy keys.

Execution Plan
- PR 1: Add Sophia alias keys/vars (no behavior change); update consumers to prefer Sophia keys.
- PR 2: Add parallel k8s resources with sophia names/labels; document cutover.
- PR 3: Remove legacy paths when safe; drop fallbacks.

