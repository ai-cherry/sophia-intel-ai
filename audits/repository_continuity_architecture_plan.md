# Repository-wide Continuity & Architecture Examination Plan

Summary
- Purpose: provide a repeatable, repository-wide plan to detect, triage, and remediate architecture continuity problems (duplication, dependency cycles, CI fragmentation, security and dependency drift) and deliver concrete artifacts (patch examples, quick-check scripts, graphs, and a prioritized backlog).
- Output location: all artifacts produced by this plan live under `audits/` (examples in `audits/examples/`).

References
- Repository agent rules and persona conventions: [`AGENTS.md`](AGENTS.md:1)
- Service dependency guidance used as an example: [`config/service-dependency-graph.md`](config/service-dependency-graph.md:1)

1. Objectives and success criteria
- Objectives
  - Detect structural risks: import cycles, high fan-in/out, duplicated code (>20 LOC duplicates), duplicated CI workflows.
  - Produce prioritized remediation backlog and low-risk patch examples.
  - Reduce operational cost and cognitive load by consolidating CI and shared helpers.
  - Harden repository against secrets/config drift and dependency vulnerabilities.
- Success criteria (measurable)
  - Import cycles reduced to 0 across production packages.
  - Duplicates >20 LOC reduced by 60% vs baseline.
  - CI runtime minutes reduced by 30% for core pipelines (measured week-over-week).
  - Critical dependency vulnerabilities = 0; high vulnerabilities remediated within 7 days.
  - Test coverage targets (project dependent) — e.g., core services >= 80% branch coverage.
  - Delivery of: prioritized CSV backlog, Graphviz dependency graph (SVG), three example patches in `audits/examples/`, one-day checklist script.

2. Scope variations and methodology differences
- Monorepo vs Polyrepo
  - Monorepo: focus on package-level graphs, shared libs, workspace manifests (pnpm workspaces, Maven multi-module, Nx). Use cross-package import analysis and duplicate detection across packages.
  - Polyrepo: focus on inter-repo service registry, CI duplication across repos, shared infra repos. Emphasize service registry and dependency/version mismatches.
- Project type
  - Microservice-based: analyze service-to-service calls, service registries (Consul, Kubernetes services), API contracts, runtime traces (Jaeger/OTel).
  - Library-focused: emphasize API surface, semantic versioning, packaging, and backwards compatibility tests.
  - Monolithic: emphasize modularization candidates, call-graph hotspots, cyclomatic complexity and refactoring into packages.

3. Data sources to collect (what and why)
- Code (all source files)
  - Why: detect duplicates, import cycles, complexity hotspots, public API surfaces.
- Tests (unit / integration / e2e)
  - Why: coverage gaps, missing regression protection for refactors.
- CI/CD configs (e.g., `.github/workflows/*`, `.gitlab-ci.yml`, `circleci/`)
  - Why: duplicated jobs, wasted minutes, inconsistent checks.
- Infrastructure as Code (Terraform, Pulumi, k8s manifests)
  - Why: detect drift, duplicated infra constructs, privileged resources.
- Dependency manifests (pom.xml, package.json, go.mod, requirements.txt)
  - Why: vulnerability scanning, version skew, transitive dependency cycles.
- Build artifacts and lockfiles (package-lock.json, yarn.lock)
  - Why: deterministic builds, lockfile drift.
- Runtime traces/telemetry (Jaeger, OTel traces, logs)
  - Why: understand runtime coupling, latency hotspots, fan-in/out.
- Service registries and manifests (K8s svc, Consul)
  - Why: runtime topology for dependency graphs.
- Architecture diagrams and docs (Diagrams, ADRs, READMEs)
  - Why: ground-truth vs code reality; identify stale documentation.
- Secrets/config stores / feature flags
  - Why: security and runtime divergence risk.

4. Concrete analysis methods (when to apply each)
- Static analysis (always first-pass): detect syntax-level issues, unused exports, obvious code smells.
- Dependency/graph analysis (apply early for package layout): jdeps, depcruise, madge for JS, go list for Go.
- Code-clone / diff detection (apply where duplication suspected): NiCad, SourcererCC, Deckard, comby.
- Import-cycle detection: madge (JS/TS), jdeps (Java), go list -deps -json (Go).
- Call-graph inspection: tree-sitter + language-specific tools (CodeQL/Joern for deeper graph).
- Runtime tracing & telemetry correlation: Jaeger, OTel data to verify static graph and find actual runtime coupling.
- Config/secret/feature-flag review: gitleaks, detect-secrets, manual review of feature flag definitions.
- CI workflow comparison: rg to find duplicated workflow names, compare ymls, consolidate into reusable workflows.

5. Recommended tools mapped to each method (install + run)
Note: provide copy-paste install and run commands where possible.

Static code search
- ripgrep (rg): install: `sudo apt install ripgrep` or `brew install ripgrep`
  - Example run: rg -n --hidden --glob '!node_modules' "TODO|FIXME" | head
  - What to look for: TODOs, FIXME, hard-coded addresses, duplicate code patterns.
- comby (structural search): install: curl -sLo /usr/local/bin/comby https...; make executable.
  - Example: comby 'func :name(:params) { :body }' 'func $name($params) { /*extracted*/ }' --lang go **/*.go

Dependency / import graph
- madge (JS/TS): `npm i -g madge`
  - Run: madge --image audits/examples/dependency_graph.svg src/
  - Look for: circular dependencies, large dependency clusters.
- depcruise: `npm i -g dependency-cruiser`
  - Run: depcruise --include-only "^src" --output-type dot src | dot -Tsvg -o audits/examples/deps.svg

Java
- jdeps (JDK): jdeps -verbose:class -dotoutput out.dot build/libs/*.jar
  - Look for: package cycles, high coupling between modules.

Maven
- mvn dependency:tree -Dverbose
  - Look for: duplicate versions, conflicts.

npm / node
- npm ls --all --long
  - Look for: duplicate major versions across workspaces.

Go
- go list -deps -json ./... | jq '.'

Code clone detection
- SourcererCC: Java-based clone detector (build and run)
- NiCad: clone detection (C/Java/Python)
  - Example NiCad run: nicad6/Java nicad_java_input.xml nicad_output -b
  - Look for: duplicated code blocks >20 LOC.

Security / secrets / containers
- Trivy (container + filesystem): `brew install trivy`
  - Run: trivy fs --severity HIGH,CRITICAL .
- Snyk: `npm i -g snyk` then `snyk test`
- gitleaks: `brew install gitleaks` then `gitleaks detect -s .`

CodeQL (semantic queries)
- Install: follow CodeQL docs; CLI: `codeql` (download)
  - Example: codeql database create codeql-db --language=javascript --source-root=.
  - Run query pack: codeql query run path/to/query.ql --database=codeql-db

Semgrep (pattern-based)
- Install: `pip install semgrep` or `brew install semgrep`
  - Run quick scan: semgrep --config=p/r2c-ci --baseline=semgrep-baseline.json
  - What to look for: insecure crypto, hard-coded secrets, inconsistent logging.

Runtime tracing / telemetry
- Jaeger + OTel: instrument services and run queries in Jaeger UI to find high fan-in endpoints.
  - Look for: services with unusually high inbound traffic or high latency edges.

CI duplication analysis
- rg commands (examples below) to find duplicated job names or similar steps
  - Look for repeated YAML job bodies across repositories.

What to look for in output (examples)
- Semgrep: rule hits identifying hard-coded secrets or insecure calls — each hit includes filename:line and snippet.
- CodeQL: query results with flow graphs or dataflow traces.
- Madge: list of circular dependencies, and images showing module clusters.
- Trivy: CVE list with severity and fix suggestion.

6. Example commands and sample outputs / indicators (copy-paste ready)
- Command 1: ripgrep TODOs
  - rg -n --hidden --glob '!node_modules' "TODO|FIXME" | sed -n '1,10p'
  - Sample output: backend/service/foo.go:123:// TODO: remove hack for issue #42
  - Flag: stale TODOs in core code paths
- Command 2: find duplicated CI workflow names
  - rg -n --hidden --glob '.github/workflows/*.yml' "name: " | sed -n '1,20p'
  - Sample output: .github/workflows/ci.yml:3:name: CI
  - Flag: identical job names across many workflows
- Command 3: semgrep quick scan
  - semgrep --config=p/ci --timeout 120 --baseline=semgrep-baseline.json
  - Sample output: src/auth/keys.go:12: Hard-coded API key found
- Command 4: CodeQL database create + run query
  - codeql database create codeql-db --language=javascript --source-root=.
  - codeql query run javascript/ql/src/Security/CWE-798/HardcodedCredentials.ql --database=codeql-db --output=codeql-hardcoded.sarif
  - Sample: results SARIF file with hits showing function and dataflow
- Command 5: madge graph
  - madge --circular --warning --extensions js,ts src/ || true
  - Sample output: Circular dependency found: src/a.js -> src/b.js -> src/a.js
- Command 6: depcruise dot output
  - depcruise --include-only "^src" --output-type dot src > audits/examples/deps.dot
  - dot -Tsvg audits/examples/deps.dot -o audits/examples/deps.svg
- Command 7: trivy scan
  - trivy fs --no-progress --severity HIGH,CRITICAL .
  - Sample output: package xyz CVE-YYYY-XXXX HIGH - upgrade to 1.2.3
- Command 8: gitleaks quick
  - gitleaks detect --source . --report-path audits/examples/gitleaks-report.json
- Command 9: nicad example (conceptual)
  - Nicad execution (Java): nicad6/Java nicad_input.xml nicad_out -b
  - Output: Found 15 clones >20 LOC; cluster in /services/payments/
- Command 10: jdeps
  - jdeps -verbose:class -filter:package -dotoutput jdeps.dot build/libs/*.jar
  - dot -Tpng jdeps.dot -o audits/examples/jdeps.png

7. Heuristics and measurable metrics to prioritize findings
- Duplicate code: blocks >20 LOC count as high; prioritize duplicates with test coverage <40%.
- Clone % thresholds: if more than 5% of repo LOC duplicated => High priority.
- Cycle counts: any non-zero cycle in production packages = Critical (severity P0/P1 depending on impact).
- Cyclomatic complexity: functions >20 complexity = Medium/High.
- Fan-in/out thresholds: modules/services with fan-in >10 or fan-out >10 flagged as architectural hotspots.
- Coverage gaps: core modules <70% = High priority.
- Vulnerabilities: Critical CVEs = Immediate P0; High CVEs = P1 within 7 days.
- CI duplication: identical job body repeated more than 3 times across repo = consolidate candidate.

8. Triage & prioritization process (convert findings -> tickets)
- Scoring model: Impact (1-5) x Effort (1-5) -> Priority tiers
  - Impact: production risk, security, release blocking, dev productivity
  - Effort: low (1) to very high (5)
- Ticket template (CSV compatible): columns = id,title,severity,impact,effort,priority,assignee,component,estimate_days,description,acceptance_criteria
- Labels/severity mapping:
  - p0-critical, p1-high, p2-medium, p3-low
  - Add labels: security, ci, duplication, cycle, infra
- Milestone assignment: small fixes to quick-win milestone (1 week); medium refactors (2-4 weeks); large modularization (quarterly epic).

9. Concrete remediation strategies and refactor patterns
- Extract module / shared helper
  - Pattern: identify duplicated functions, extract to `packages/shared` or `libs/shared` and update imports.
  - Safe rollback: feature flag usage; create a compatibility shim that forwards to extracted helper.
  - Validation: unit tests, smoke tests, canary rollout.
- Interfaces / adapters to break cycles
  - Pattern: introduce interface in low-level package and adapter in higher-level package; move concrete implementation to a lower-level adapter package.
  - Example workflow:
    1. Add interface file e.g., `pkg/foo/iface.go` with minimal contract.
    2. Replace direct imports with interface usage.
    3. Add adapter implementing interface in `pkg/foo/adapter` and update DI wiring.
  - Rollback: revert patch; keep both implementations for short period with runtime switch.
- Facades
  - Pattern: provide a single stable entrypoint for a subsystem to reduce cross-package imports.
- Consolidation of CI workflows
  - Pattern: extract repeated jobs into `.github/workflows/reusable.yml` and use `uses: ./.github/workflows/reusable.yml` or `workflow_call`.
- Packaging/versioning fixes
  - Pattern: align versions across workspaces, bump breaking changes with changelog and migration guide.
- Dependency inversion
  - Pattern: invert imports by moving abstractions to lower-level common package, implement higher-level concrete modules separately.
- Safe validation steps
  - Feature flag gate, canary deployment, smoke tests (health endpoints), telemetry monitoring for error rate and latency.

10. One-day lightweight checklist (shell script)
- See `audits/examples/one-day-checklist.sh` (example script included in `audits/examples/`).
- Purpose: minimal outputs to collect quickly: semgrep quick scan, CodeQL quick DB creation (index-only), rg searches for duplicate workflows, madge/cycle check, trivy quick scan, gitleaks detect (no secret upload).

11. 4-week engagement plan (detailed)
- Roles: Architect, Tech Lead, DevOps/Platform, Security Auditor, 2 Senior Engineers, QA
- Weekly milestones, deliverables, responsibilities, and person-days:

Week 0 (Prep) — Kickoff (1 week, mostly part-time)
- Activities: repo inventory, baseline metrics, initial one-day checklist run, set up tooling access
- Deliverables: baseline CSV, initial dependency graph SVG, one-day checklist outputs
- Person-days (per week):
  - Architect: 3 pd
  - Tech Lead: 2 pd
  - DevOps: 2 pd
  - Security Auditor: 1 pd
  - Senior Engineers (2): 2 pd each
  - QA: 1 pd
- Total PD: 13

Week 1 — Detection & Prioritization
- Activities: run full static scans (semgrep, CodeQL), clone detection, madge/depcruise graphs, CI duplicate detection, vulnerability scans
- Deliverables: prioritized findings CSV, sample patches (low-risk), patch examples in `audits/examples/`
- Person-days:
  - Architect: 4 pd
  - Tech Lead: 4 pd
  - DevOps: 3 pd
  - Security Auditor: 3 pd
  - Senior Engineers: 6 pd (3 each)
  - QA: 2 pd
- Total PD: 22

Week 2 — Quick remediation & consolidation
- Activities: implement low-risk fixes (CI consolidation, shared helpers), prepare larger refactor plans, test harness updates
- Deliverables: PRs for CI consolidation, extracted helpers, updated workflows, test coverage improvements
- Person-days:
  - Architect: 2 pd
  - Tech Lead: 4 pd
  - DevOps: 4 pd
  - Security Auditor: 2 pd
  - Senior Engineers: 8 pd
  - QA: 3 pd
- Total PD: 23

Week 3 — Refactor and rollout
- Activities: break cycles using adapters, stabilize extracted modules, canary deployments, verify telemetry
- Deliverables: refactor PRs, canary deployment runbooks, monitoring dashboards updated
- Person-days:
  - Architect: 2 pd
  - Tech Lead: 3 pd
  - DevOps: 4 pd
  - Security Auditor: 1 pd
  - Senior Engineers: 10 pd
  - QA: 4 pd
- Total PD: 24

Week 4 — Validation, documentation, handoff
- Activities: validate KPIs, finalize backlog, update docs and ADRs, harden CI, schedule follow-ups
- Deliverables: final CSV backlog, dependency graph updated, acceptance criteria met, one-page executive summary
- Person-days:
  - Architect: 3 pd
  - Tech Lead: 3 pd
  - DevOps: 2 pd
  - Security Auditor: 1 pd
  - Senior Engineers: 4 pd
  - QA: 3 pd
- Total PD: 16

Estimated person-day totals (4-week sum)
- Architect: 10 pd
- Tech Lead: 12 pd
- DevOps/Platform: 15 pd
- Security Auditor: 8 pd
- Senior Engineers combined: 30 pd (2 engineers)
- QA: 13 pd
- Grand total: 88 person-days across 4 weeks

12. Required outputs and formats
- Prioritized backlog CSV (columns: id,title,severity,impact,effort,priority,assignee,component,estimate_days,description,acceptance_criteria)
- Graphviz DOT -> generate SVG/PNG:
  - dot -Tsvg audits/examples/dependency_graph.dot -o audits/examples/dependency_graph.svg
- Patch examples (git diff format) stored under `audits/examples/patch_*.diff`
- Remediation roadmap (Gantt/markdown) and acceptance criteria & KPIs
- One-page executive summary (Markdown) with top 5 findings and actions (deliverable).

13. Concrete detection rules and examples
- Semgrep rules (5 exact rules)
  1) semgrep rule: hard-coded AWS keys (YAML)
     - File: copy-paste into a rules file or run inline:
       ```
       rules:
       - id: hardcoded-aws-key
         patterns:
         - pattern: "AKIA[0-9A-Z]{16}"
         message: "Hard-coded AWS access key ID detected"
         languages: [javascript, python, go]
         severity: ERROR
       ```
     - Rationale: secrets in code are immediate security risk.
  2) semgrep rule: exec of user input (shell injection)
       ```
       rules:
       - id: unsafe-shell-exec
         pattern-either:
           - pattern: subprocess.call($CMD)
           - pattern: os.system($CMD)
         message: "Use of shell execution; ensure input is sanitized"
         languages: [python]
         severity: WARNING
       ```
  3) semgrep rule: duplicated workflow signature (YAML)
       ```
       rules:
       - id: duplicate-github-job
         pattern: |
           name: $NAME
           on: $ON
           jobs:
             $JOBNAME:
               steps:
                 - name: Checkout
                   uses: actions/checkout@v2
         message: "Possible duplicated CI job signature - consider reusable workflow"
         languages: [yaml]
         severity: INFO
       ```
  4) semgrep rule: insecure TLS usage (node)
       ```
       rules:
       - id: insecure-tls-accept-any-cert
         pattern: process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0"
         message: "Disabling TLS verification"
         languages: [javascript, typescript]
         severity: ERROR
       ```
  5) semgrep rule: use of eval (JS/TS)
       ```
       rules:
       - id: use-of-eval
         pattern: eval(...)
         message: "Use of eval is unsafe"
         languages: [javascript, typescript]
         severity: WARNING
       ```
- CodeQL examples (5 queries / guidance)
  - Note: codeql requires language support. Example queries (JavaScript / TypeScript / Java) in pseudo-QL format; copy into query files before running.
  1) Hardcoded credentials (JavaScript CodeQL)
     - Query (simplified):
       ```
       import javascript
       from Literal lit
       where lit.getValue().matches("AKIA[0-9A-Z]{16}")
       select lit, "Hardcoded AWS key candidate"
       ```
     - Rationale: find string literals resembling keys.
  2) SQL injection sink flow (JavaScript)
     - Use CodeQL's dataflow library to find flows from untrusted sources to SQL query execution functions (e.g., `query()`).
  3) Dangerous eval / new Function usage (JS)
     - Query: find calls to eval or new Function.
  4) Import cycles (Java)
     - Use CodeQL to build module dependency graph and detect cycles between packages.
  5) Missing authentication checks (Java/TS)
     - Query patterns to find endpoints that call DB without auth-check functions upstream (heuristic).
- ripgrep / regex examples
  - Duplicate workflow names:
    - rg -n --hidden --glob '.github/workflows/*.yml' '^name: ' | sort | uniq -c | sort -nr
  - CI duplication signature (example pattern)
    - rg -n --hidden --glob '.github/workflows/*.yml' "uses: actions/checkout@|actions/setup-node@" --stats
- Example import-cycle trace output (explain)
  - Example madge output:
    - "✖ Found 1 circular dependency!"
    - "Module A -> Module B -> Module C -> Module A"
  - Explanation: follow edges to find minimal set to break via interfaces/adapters or extraction.

14. Prioritized sample remediation backlog (10 example issues)
- Provide CSV-style lines (id,title,severity,assignee,ETA,effort_days)
  - 001,Extract shared string utils to packages/shared,high,Senior Engineer,5d,2
  - 002,Break import cycle between pkg/auth and pkg/db,critical,Senior Engineer,7d,3
  - 003,Consolidate duplicated CI job into reusable workflow,high,DevOps,3d,1
  - 004,Remove hardcoded AWS key in service X,critical,Security Auditor+Engineer,2d,1
  - 005,Upgrade vulnerable dependency lodash (CVE-XXXX),critical,Senior Engineer,2d,1
  - 006,Add semgrep and CodeQL to CI baseline,medium,DevOps,4d,2
  - 007,Write compatibility shim after extracting helper,medium,Tech Lead,5d,2
  - 008,Increase unit coverage for billing service to 80%,high,QA+Engineer,14d,6
  - 009,Refactor large monolith module into two packages,medium,Architect+Engineers,21d,10
  - 010,Audit IaC for S3 public buckets,critical,Security Auditor,3d,2

15. Appendix: repository conventions and example file references
- See repository agent rules: [`AGENTS.md`](AGENTS.md:1)
- Service dependency doc example: [`config/service-dependency-graph.md`](config/service-dependency-graph.md:1)

Examples & quick references (mini-cheat sheet)
- Generate dependency svg
  - madge --image audits/examples/dependency_graph.svg src/
- Quick semgrep run
  - semgrep --config auto --baseline=semgrep-baseline.json --error
- Quick CodeQL (JS) database
  - codeql database create codeql-db --language=javascript --source-root=.
  - codeql query run path/to/query.ql --database=codeql-db --output=codeql-results.sarif

Minimum deliverables (what this plan will generate under audits/)
- audits/repository_continuity_architecture_plan.md (this file)
- audits/examples/one-day-checklist.sh
- audits/examples/patch_extract_helper.diff
- audits/examples/patch_break_cycle.diff
- audits/examples/patch_unify_ci.diff
- audits/examples/dependency_graph.dot

End of plan.
## 16. Remediation & Improvement Plan — focused on safe consolidation and deletion (foundation-level reset)

This section expands the plan with exact heuristics, automated detection commands, canonical selection rules, a prioritized consolidation backlog format, CI gating and verification steps, non-destructive workflow guidance, a risk matrix, and two small case studies. All operations that DELETE or MODIFY files outside `audits/` MUST WAIT for explicit written confirmation from the repo owner. The process below is prescriptive and staged so you can perform a full cleanup safely once permission is granted.

### 16.1 Definitions — what counts as "bad" and "duplicate"
- Bad code (heuristics)
  - Failing tests (unit or integration) or flakey tests covering a module
  - Security anti-patterns (hard-coded credentials, disabled TLS, eval usage)
  - High complexity: functions with cyclomatic complexity > 20 and low test coverage (< 40%)
  - Dead / orphaned code: files not referenced by any build, package, or import chain and with no recent authorship
  - Broken or undocumented public API surface (no README/ADR and no consumers)
- Duplicate code (heuristics)
  - Textual clones: identical code blocks (token-level) >= 20 LOC found by clone detectors
  - Semantic duplicates: different text but same behavior (same sequence of operations) — flagged by similarity tools or by cross-service tests
  - API/behavioral redundancy: two or more modules exposing equivalent APIs used by different consumers
  - CI duplication: identical job bodies repeated across multiple workflow files

### 16.2 Automated detection methodology — exact commands & tools
Run these in a CI runner or a dev machine. Save outputs to `audits/examples/one-day-output/` (script exists: [`audits/examples/one-day-checklist.sh`](audits/examples/one-day-checklist.sh:1)).

1) Textual clone detection (jscpd)
- Install: `npm i -g jscpd`
- Run (JS/TS/Python/Go): 
  - jscpd --min-lines 20 --reporters json --output audits/examples/jscpd-report.json .
- Interpret: look for "percentage" and clone clusters; sort by clone size.

2) Token/semantic clone (SourcererCC / NiCad)
- NiCad for Java/Python/C:
  - (example) run NiCad as documented in NiCad README; produce `nicad-output`.
- SourcererCC (Java-based):
  - Build and run per tool docs; produce a CSV of clone groups.
- Interpret: any clone group with >= 20 LOC or frequency > 2 across packages => candidate to consolidate.

3) Import-cycle detection (madge for JS; jdeps for Java; go tool for Go)
- JS/TS:
  - npm i -g madge
  - madge --circular --extensions js,ts src/ 2>&1 | tee audits/examples/madge-circular.txt || true
- Java:
  - jdeps -verbose:class -filter:package -dotoutput audits/examples/jdeps.dot build/libs/*.jar
  - dot -Tsvg audits/examples/jdeps.dot -o audits/examples/jdeps.svg
- Go:
  - go list -deps -json ./... | jq '.'
- Interpret: cycles are P0 — break via interface/adapters or extraction.

4) Orphaned code detection (refs + build references)
- rg import/export cross-check:
  - rg --hidden --no-ignore -n "from |import |require\(" | sed -n '1,200p' > audits/examples/import_refs.txt
- Build reference check (example for Node):
  - node -e "const fs = require('fs'); /* custom script to detect files not present in any import path */"
- Heuristic: files not referenced by any import and no recent commits => candidate for archive/delete.

5) Security & secret scanning
- gitleaks:
  - gitleaks detect --source . --report-path audits/examples/gitleaks.json || true
- semgrep (security rules):
  - semgrep --config=p/ci --timeout 120 --baseline=semgrep-baseline.json > audits/examples/semgrep-ci.txt || true
- trivy (filesystem):
  - trivy fs --no-progress --severity HIGH,CRITICAL . | tee audits/examples/trivy_quick.txt || true

6) CI duplication scanning
- ripgrep:
  - rg -n --hidden --glob '.github/workflows/*.yml' -S "uses:|run:" | sed -n '1,500p' > audits/examples/ci-snippets.txt
- Aggregation:
  - rg -n --hidden --glob '.github/workflows/*.yml' '^name: ' | sort | uniq -c | sort -nr > audits/examples/ci_workflow_name_counts.txt

7) Coverage and complexity
- Extract complexity (JS using eslint)
  - npm i -g eslint eslint-plugin-complexity
  - eslint --rule 'complexity: ["error", 20]' . || true
- Python radon:
  - pip install radon
  - radon cc -s -n B -i tests . > audits/examples/radon_cc.txt
- Coverage:
  - Run test coverage and export (e.g., `pytest --cov=./ --cov-report=xml:audits/examples/coverage.xml`)

8) Dependency centrality and usage (graph metrics)
- depcruise / madge output -> convert to DOT -> analyze node degrees (fan-in/fan-out)
  - depcruise --include-only "^src" --output-type dot src > audits/examples/deps.dot
  - dot -Tsvg audits/examples/deps.dot -o audits/examples/deps.svg
  - Use `awk`/Python to compute degree centrality and flag top nodes.

### 16.3 Rule set for selecting canonical implementation
When multiple implementations are candidates for consolidation, choose the canonical implementation using the following ordered criteria (tie-breakers lower in list):
1. Active usage: Implementation with the most live consumers in the repo (imports / call sites).
2. Test coverage: Higher test coverage (prefer >= 70% at module level).
3. Single source of truth: Implementation already published as package or maintained in `packages/` or `libs/`.
4. Performance: Measured performance of candidate implementation (benchmarks) — choose best.
5. Clarity & maintainability: fewer cyclomatic complexity, clearer API (less parameters, documented).
6. Licensing: compatible license (no conflicts).
7. API stability: fewer breaking changes historically (via git blame/annotate).
8. Ownership: active maintainer or team with capacity.
If none meets criteria well, extract a new canonical implementation by merging best parts and add full tests.

### 16.4 Prioritized backlog format and generation (CSV)
- CSV header (example):
  - id,title,severity,impact,effort,priority,assignee,component,estimate_days,description,acceptance_criteria,rollback_plan
- Generate using scripts:
  - Example command to create a starter backlog CSV:
    - printf "id,title,severity,impact,effort,priority,assignee,component,estimate_days,description,acceptance_criteria,rollback_plan\n" > audits/examples/prioritized_backlog.csv
    - Then append items (see sample items in previous section). Use `jq`/Python to transform detection outputs into CSV rows.

### 16.5 Non-destructive workflow & staging guidance (policy)
Policy (read carefully)
- Do not delete or modify repository files outside `audits/` without explicit written confirmation from the repository owner.
- All changes must go through PRs with CI gating described below.
- Use feature flags, compatibility shims, and adapters to allow phased removal.
- PR must include:
  - Tests covering impacted code paths
  - Backwards compatibility checks (contract tests)
  - Rollback steps and feature-flag off path
  - Owner sign-off and security audit for removals that affect credentials/infra

Non-destructive PR pattern
1. Add canonical implementation and tests in a new package (or `libs/`).
2. Create adapter/shim in legacy locations that forwards to canonical implementation.
3. Update callers to prefer canonical implementation in incremental PRs.
4. Remove legacy implementations once 100% of call sites are moved and CI + canary metrics are green.

Example feature flagging pattern
- Add config flag `use_new_impl` defaulting to false in runtime config.
- Roll out PR with flag available and feature off.
- Switch flag on for 1% of traffic in canary; monitor errors and latency.
- Increase to 100% then remove legacy code after validation.

### 16.6 CI gating and automated verification steps (copy-paste)
- Pre-merge CI (required for any consolidation PR)
  - Unit tests: `npm ci && npm test` or `pytest -q`
  - Lint: `npm run lint` or `ruff check .`
  - Security scans (light): `semgrep --config=auto --timeout=120` (fail on ERROR)
  - Dependency check: `npm audit --audit-level=high` or `snyk test`
  - Clone/Coverage checks: run jscpd and coverage scripts and fail if thresholds exceeded
- Post-merge verification (canary)
  - Build staging artifact: `./scripts/build-artifact.sh`
  - Deploy to canary namespace
  - Smoke: `curl -f http://canary/health` (retry 5x)
  - Trace verification: ensure OTel traces for a set of requests exist
  - Metrics: check error_rate < baseline + delta, latency p95 < baseline + delta

Verification commands (examples)
- Run full test suite and coverage:
  - For Python: `pytest --cov=src --cov-report=xml:audits/examples/coverage.xml`
- Run jscpd clone check:
  - jscpd --min-lines 20 --reporters json --output audits/examples/jscpd-report.json .
- Quick smoke after deployment (example):
  - curl -sSf -o /dev/null http://$CANARY_HOST/health || exit 1

### 16.7 Risk matrix and escalation
- Severity mapping:
  - Critical (P0): Removing code that disables security or breaks auth, or breaking public API used by external customers
  - High (P1): Breaking internal infra or critical pipelines or introducing regressions in core services
  - Medium (P2): Developer experience or non-critical features
  - Low (P3): Cosmetic or docs-only changes
- Escalation path:
  - If P0 failure in canary: immediately revert to previous commit (PR rollback) and open incident with SRE and Security Auditor.
  - For P1 regression: pause rollout, open rollback PR, escalate to Tech Lead and Architect.
- Rollback mechanisms:
  - Revert PR, disable feature flag, restore previous canary image tag.

### 16.8 Two example consolidation case studies (full before/after summaries)
Case Study A — Extract shared formatting helper (small)
- Before: duplicated `format_currency` helper in `services/payments/payment_processor.py` and `services/invoices/invoice_generator.py`.
- Detection evidence: `jscpd` clone group id 42; `rg` shows two files with same helper.
- Chosen canonical: new `libs/shared/formatting.py` (because both modules had low coverage but single consumer set).
- Steps:
  1. Add new file `libs/shared/formatting.py` with function and unit tests (PR A1).
  2. Replace imports in `payments` and `invoices` with `from libs.shared.formatting import format_currency` (PR A2).
  3. Run full tests, run `jscpd` to confirm clone removed.
  4. After 1 week and Canary verification, delete legacy duplicates.
- Example patch: [`audits/examples/patch_extract_helper.diff`](audits/examples/patch_extract_helper.diff:1)
- Acceptance criteria:
  - Unit tests pass.
  - jscpd shows clone group removed.
  - CI runtime unchanged or improved.
- Rollback:
  - Revert PRs A2 then A1; or re-enable legacy helper and remove new import.

Case Study B — Breaking an import cycle via interface/adapters (medium)
- Before: `pkg/auth` and `pkg/db` had cyclic dependency discovered by `madge` (cycle path A -> B -> A).
- Detection evidence: `madge --circular` output: "pkg/auth -> pkg/db -> pkg/auth"
- Chosen approach: introduce `pkg/auth/interfaces` with `Authenticator` interface and `pkg/auth/adapter` implementing it using `pkg/db`. Update `services/api` to accept `auth.Authenticator` via DI.
- Steps:
  1. Add `pkg/auth/interface.go` (PR B1).
  2. Add `pkg/auth/adapter/db_auth_adapter.go` (PR B1).
  3. Update `pkg/db` to remove dependency on `pkg/auth` (PR B2).
  4. Update `services/api` constructor to accept `auth.Authenticator` (PR B3).
  5. Run full tests and madge — cycles must be gone.
- Example patch: [`audits/examples/patch_break_cycle.diff`](audits/examples/patch_break_cycle.diff:1)
- Acceptance criteria:
  - `madge --circular` returns no cycles.
  - Integration tests for auth paths pass.
  - Canary shows no auth regressions.
- Rollback:
  - Revert PRs in reverse order or keep legacy wiring until all consumers migrated.

### 16.9 4-week detailed engagement (cleanup-first variant)
Because you indicated you want a foundation-level reset (delete everything except a minimal skeleton), the plan below describes a conservative 4-week *preparation + staged deletion* engagement. IMPORTANT: no destructive deletions will be executed until you explicitly confirm deletion scope in writing.

Week 0 — Inventory & Baseline (run one-day checklist + full scans)
- Deliverables: CSV backlog, detailed clone/cycle reports, candidate canonical picks.
- Approvals: Tech Lead + Architect + Repo Owner confirm deletion policy and scope.

Week 1 — Implement canonical packages and shims (non-destructive)
- Add canonical implementations and comprehensive tests under `libs/` or `packages/`.
- Add compatibility shims in legacy paths.
- Add CI gating and pre-merge checks for clone & cycle removal.

Week 2 — Migrate callers incrementally (non-destructive)
- Gradual PRs changing callers to canonical implementations, each gated by CI, feature-flagged if applicable.

Week 3 — Canary verification & signoff
- Deploy to canary, run smoke and load tests, validate telemetry, finalize removal candidates list.

Week 4 — Controlled destructive cleanup (ONLY AFTER OWNER APPROVAL)
- Remove legacy files and unused CI/infrastructure files as per approved deletion manifest.
- Create a single cleanup PR per logical area (services/ libs/ infra/ ci/)
- Post-merge: run full CI, run smoke tests, monitor for 48 hours.

### 16.10 Communication, ownership & final policy
- Before cleanup, update CODEOWNERS and open an RFC/PR describing the deletion manifest and rationale.
- Post-cleanup, update docs, ADRs, and register new owners in `CODEOWNERS`.
- Keep a public changelog entry describing what was removed and why.

### 16.11 Next action (required from you)
I will prepare the prioritized CSV backlog file and two additional example consolidation patches (full tests and a minimal PR checklist) and place them under `audits/examples/` if you confirm: "Approve staging: prepare cleanup artifacts but DO NOT delete files."  
If you confirm "Approve destructive cleanup now", I will return a safe, fully scripted deletion plan and the exact git commands to delete files (but I will NOT execute them — you must run them or confirm to proceed).  

Final reminder: no destructive deletions or modifications of files outside `audits/` will be made until you explicitly confirm the deletion scope in writing (this is the enforced policy).