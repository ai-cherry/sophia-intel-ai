Title: [component] Short description (e.g., Extract canonical helper)
Description:
- What this PR changes, why, and link to audit/backlog item.

Checklist:
- [ ] I have NOT deleted any files outside audits/ without repo-owner explicit written approval
- [ ] Authoritative tests added/updated (unit/integration)
- [ ] Semgrep and CodeQL quick scans pass locally or in CI
- [ ] jscpd run shows duplicate removed (where applicable) or documented reason
- [ ] madge / import-cycle check run (if applicable)
- [ ] Canary plan included (if runtime change)
- [ ] Rollback plan included and verified
- [ ] Owner (CODEOWNERS) reviewed and approved

Acceptance criteria:
- Describe measurable acceptance criteria (tests, coverage, clone removal, no cycles, canary metrics).

Rollback plan:
- Precise steps to revert if regression detected (revert PR, disable feature flag, redeploy previous tag).

Notes:
- This PR is non-destructive until the repo owner explicitly approves deletions listed in the deletion manifest at audits/examples/deletion_manifest.csv