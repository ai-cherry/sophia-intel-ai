# Repo Cleanup Summary (Draft)

- Total Markdown files detected: 333
- ADR files: 15
- ARTEMIS docs: 11
- PHASE/roadmap docs: 5
- Deployment docs: 15
- Integration docs: 30
- READMEs: 35

## Recommended Next Actions
- Approve creation of the following core docs as single sources of truth:
  - README.md, QUICKSTART.md, docs/ARCHITECTURE.md, docs/API_REFERENCE.md
  - DEPLOYMENT_GUIDE.md, INTEGRATIONS.md, ROADMAP.md, CHANGELOG.md, ARTEMIS_ARCHITECTURE.md
- On approval, merge contents listed in category files into targets and archive superseded files.
- Keep ADRs in docs/architecture/decisions/; remove exact duplicates if found.
- Review temp/cache candidates in temp-and-cache.txt and remove those safe to delete.
- Review one-time-scripts.txt and decide which are historical vs. needed entry points.
- Review deprecation-and-todos.txt and address or remove obsolete code.

All detailed lists are in docs/cleanup-reports/.
