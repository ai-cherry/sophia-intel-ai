# Documentation Consolidation Plan (Draft)

This plan groups existing Markdown files into categories and maps each category to a single target document, per Phase 1 objectives. No files have been deleted or moved yet.

## Summary Counts
- Total Markdown files: 333
- ADRs: 15
- ARTEMIS-related: 11
- PHASE/roadmap-related: 5
- Deployment-related: 15
- Integration-related: 30
- READMEs: 35

## Targets and Actions
- Core overview: `README.md` (single source of truth)
- Quickstart: `QUICKSTART.md` (setup + essential usage)
- Architecture: `docs/ARCHITECTURE.md` (include Mermaid diagrams)
- API Reference: `docs/API_REFERENCE.md` (generated or curated)
- Deployment: `DEPLOYMENT_GUIDE.md` (merge deployment guides + checklists)
- Integrations: `INTEGRATIONS.md` (consolidate integration docs)
- Roadmap: `ROADMAP.md` (merge PHASE_* docs)
- Changelog: `CHANGELOG.md` (authoritative version history)
- ADRs: keep under `docs/architecture/decisions/` as-is (curate if duplicates)
- ARTEMIS Architecture: `ARTEMIS_ARCHITECTURE.md` (merge ARTEMIS_* technical docs)

## Candidate Files to Merge

### ARTEMIS_* -> ARTEMIS_ARCHITECTURE.md
- See `docs/cleanup-reports/category-ARTEMIS.txt`

### PHASE_* and Roadmaps -> ROADMAP.md
- See `docs/cleanup-reports/category-PHASE.txt`

### Deployment-related -> DEPLOYMENT_GUIDE.md
- See `docs/cleanup-reports/category-DEPLOYMENT.txt`

### Integration-related -> INTEGRATIONS.md
- See `docs/cleanup-reports/category-INTEGRATION.txt`

## Notes
- Preserve unique technical details and remove only redundant/outdated docs.
- Update core docs with accurate, current content; link to ADRs where appropriate.
- After consolidation, archive superseded files for one release before removal.
