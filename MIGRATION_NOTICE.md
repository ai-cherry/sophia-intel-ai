# Migration Notice: Artemis → Sophia

Artemis was an old label for the technical/coding side of this platform. It has been removed.

What remains (authoritative):
- Sophia platform with a local coding environment via Portkey/OpenRouter, CLI, and Studio UI.
- Single-source environment at `<repo>/.env.master` (chmod 600), managed with `./bin/keys edit`.
- One orchestrator and one set of services (Sophia only).

What changed:
- Kubernetes manifests drop `artemis-*` resources.
- Startup config and scripts no longer reference Artemis.
- Pulumi ESC keys now use Sophia-only naming.
- Docs and UI labels scrubbed to Sophia naming.

Guardrails:
- CI runs a scan for the word “artemis” to prevent regressions (non‑strict for now).
- Use `python3 scripts/audit/find_legacy_artemis.py --strict` locally to fail on any matches.

If you see “Artemis” anywhere, it’s historical context; open a PR to remove or archive it.
