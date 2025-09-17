#!/usr/bin/env bash
# One-day lightweight checklist for Repository Continuity & Architecture Examination
# Saves minimal outputs to audits/examples/one-day-output/
#
# See master plan: [`audits/repository_continuity_architecture_plan.md`](audits/repository_continuity_architecture_plan.md:1)
set -euo pipefail

OUTDIR="audits/examples/one-day-output"
mkdir -p "$OUTDIR"

echo "1) Basic repo stats" | tee "$OUTDIR/00-summary.txt"
echo "Date: $(date --iso-8601=seconds)" >> "$OUTDIR/00-summary.txt"
echo "Top-level dirs:" >> "$OUTDIR/00-summary.txt"
ls -1 | sed -n '1,200p' >> "$OUTDIR/00-summary.txt"

echo
echo "2) Quick ripgrep scans (TODO/FIXME, large files, possible duplicated CI names)"
rg -n --hidden --glob '!node_modules' "TODO|FIXME" | sed -n '1,200p' > "$OUTDIR/todos.txt" || true
rg -n --hidden --glob '.github/workflows/*.yml' '^name: ' | sort | uniq -c | sort -rn > "$OUTDIR/ci_workflow_name_counts.txt" || true
echo "Saved: $OUTDIR/todos.txt, $OUTDIR/ci_workflow_name_counts.txt"

echo
echo "3) Semgrep quick scan (default rules, timeboxed 60s)"
if command -v semgrep >/dev/null 2>&1; then
  semgrep --config=auto --timeout=60 --error 2>/dev/null | sed -n '1,200p' > "$OUTDIR/semgrep_quick.txt" || true
  echo "Saved semgrep quick results to $OUTDIR/semgrep_quick.txt"
else
  echo "semgrep not installed - skipping (install with pip install semgrep)" > "$OUTDIR/semgrep_quick.txt"
fi

echo
echo "4) CodeQL skeleton: create DB (language autodetect) - no queries run (fast index)"
if command -v codeql >/dev/null 2>&1; then
  # This is intentionally conservative: only create DB for JS/TS example if present
  if rg -n --hidden --glob '!node_modules' "package.json" | sed -n '1,1p' >/dev/null 2>&1; then
    codeql database create "$OUTDIR/codeql-db" --language=javascript --source-root=. --no-git-archive-check >/dev/null 2>&1 || true
    echo "CodeQL DB created at $OUTDIR/codeql-db (or skipped on errors)."
  else
    echo "No package.json detected - skipping CodeQL JS DB creation." > "$OUTDIR/codeql_quick.txt"
  fi
else
  echo "codeql CLI not found - skip CodeQL quick step" > "$OUTDIR/codeql_quick.txt"
fi

echo
echo "5) Dependency / import cycle quick checks (madge / depcruise)"
if command -v madge >/dev/null 2>&1; then
  madge --circular --extensions js,ts src 2>&1 | sed -n '1,200p' > "$OUTDIR/madge_circular.txt" || true
else
  echo "madge not installed - skipping" > "$OUTDIR/madge_circular.txt"
fi

echo
echo "6) Vulnerability surface quick checks (trivy, snyk placeholders)"
if command -v trivy >/dev/null 2>&1; then
  trivy fs --no-progress --severity HIGH,CRITICAL . | sed -n '1,200p' > "$OUTDIR/trivy_quick.txt" || true
else
  echo "trivy not installed - skipping" > "$OUTDIR/trivy_quick.txt"
fi

echo
echo "7) Secrets quick scan (gitleaks / detect-secrets)"
if command -v gitleaks >/dev/null 2>&1; then
  gitleaks detect --source . --report-path "$OUTDIR/gitleaks.json" || true
else
  echo "gitleaks not installed - skipping" > "$OUTDIR/gitleaks.json"
fi

echo
echo "8) Minimal clone/dup detection heuristic (rg repeated function names)"
# Heuristic: find functions with identical name counts (JS/Go/Python)
rg -n --hidden --glob '!node_modules' "def |func |function " | sed -n '1,500p' > "$OUTDIR/function_defs_snippet.txt" || true

echo
echo "Checklist complete. Collected outputs:"
ls -la "$OUTDIR" || true
echo
echo "Next steps: run full suite as described in plan: [`audits/repository_continuity_architecture_plan.md`](audits/repository_continuity_architecture_plan.md:1)"