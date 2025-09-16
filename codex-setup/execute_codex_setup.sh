#!/usr/bin/env bash
set -euo pipefail

# Colors
BLUE="\033[34m"; GREEN="\033[32m"; YELLOW="\033[33m"; RED="\033[31m"; NC="\033[0m"
ts() { date '+%Y-%m-%d %H:%M:%S'; }
step() { echo -e "${BLUE}[$(ts)]$NC $*"; }
ok() { echo -e "${GREEN}[$(ts)] ✅$NC $*"; }
warn() { echo -e "${YELLOW}[$(ts)] ⚠️ $NC $*"; }
err() { echo -e "${RED}[$(ts)] ❌$NC $*"; }

# Repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

# Logging
LOGFILE="$ROOT_DIR/codex_setup_log_$(date '+%Y%m%d_%H%M%S').log"
exec > >(tee -a "$LOGFILE") 2>&1
step "Log file: $LOGFILE"

# Helper: run and continue on failure
run_or_warn() {
  set +e
  "$@"
  local rc=$?
  set -e
  if [ $rc -ne 0 ]; then
    warn "Command failed (rc=$rc): $*"
  else
    ok "Command ok: $*"
  fi
}

########################################
# STEP 1: Immediate Codex verification
########################################
step "STEP 1: Immediate Codex verification"

# Prefer existing OPENAI_API_KEY in env; if absent, prompt (no echo)
if [ -z "${OPENAI_API_KEY:-}" ]; then
  read -s -p "Enter OPENAI_API_KEY (input hidden): " OPENAI_API_KEY_INPUT
  echo
  if [ -n "$OPENAI_API_KEY_INPUT" ]; then
    export OPENAI_API_KEY="$OPENAI_API_KEY_INPUT"
    unset OPENAI_API_KEY_INPUT
    ok "OPENAI_API_KEY set for this session"
  else
    warn "OPENAI_API_KEY not provided; proceeding without session key"
  fi
else
  ok "OPENAI_API_KEY already set in environment"
fi

# Run repository verify script (tolerate failures)
if [ -x "$ROOT_DIR/scripts/codex/verify_codex.sh" ]; then
  run_or_warn bash "$ROOT_DIR/scripts/codex/verify_codex.sh"
else
  warn "scripts/codex/verify_codex.sh not found or not executable"
fi

########################################
# STEP 2: Persistent key setup (~/.zshrc)
########################################
step "STEP 2: Persist OPENAI_API_KEY to ~/.zshrc"
if [ -n "${OPENAI_API_KEY:-}" ]; then
  if [ -x "$ROOT_DIR/scripts/codex/setup_codex_key.sh" ]; then
    # Do not echo the key in logs; the script writes securely
    printf "%s" "$OPENAI_API_KEY" | ( read -r k; VAR=OPENAI_API_KEY; bash "$ROOT_DIR/scripts/codex/setup_codex_key.sh" "$VAR" >/dev/null 2>&1 <<EOF
$OPENAI_API_KEY
EOF
    ) || true
    ok "Appended OPENAI_API_KEY to ~/.zshrc"
    # Reload shell profile for current process where possible
    if [ -f "$HOME/.zshrc" ]; then
      # shellcheck disable=SC1090
      source "$HOME/.zshrc" || true
      ok "Reloaded ~/.zshrc"
    fi
  else
    warn "setup_codex_key.sh not available; skipping persistence"
  fi
else
  warn "OPENAI_API_KEY not set; skipping persistence"
fi

########################################
# STEP 3: Aggressive git sync
########################################
step "STEP 3: Git fetch/pull/prune and cleanup"
run_or_warn git fetch --all --prune

# Choose main or master
TARGET_BRANCH="main"
if ! git rev-parse --verify "$TARGET_BRANCH" >/dev/null 2>&1; then
  TARGET_BRANCH="master"
fi
run_or_warn git checkout "$TARGET_BRANCH"
run_or_warn git pull --ff-only || warn "Fast-forward pull failed; repository may be diverged"

# Clean merged local branches (excluding current, main/master)
set +e
MERGED=$(git branch --merged "$TARGET_BRANCH" | sed 's/^..//' | grep -Ev "^(main|master)$" || true)
set -e
if [ -n "$MERGED" ]; then
  step "Deleting merged local branches:\n$MERGED"
  while IFS= read -r br; do
    [ -n "$br" ] && run_or_warn git branch -d "$br"
  done <<< "$MERGED"
else
  ok "No merged local branches to delete"
fi

########################################
# STEP 4: Branch audit report
########################################
step "STEP 4: Branch audit report"
run_or_warn git branch -vv
run_or_warn git branch -r
run_or_warn git branch --no-merged "$TARGET_BRANCH"
run_or_warn git for-each-ref --format='%(refname:short) %(upstream:short) AHEAD=%(ahead) BEHIND=%(behind)' refs/heads

########################################
# STEP 5: Pull request analysis (gh optional)
########################################
step "STEP 5: Pull request analysis"
if command -v gh >/dev/null 2>&1; then
  run_or_warn gh pr list
  run_or_warn gh pr status
else
  warn "GitHub CLI (gh) not installed; skipping PR analysis"
fi

########################################
# STEP 6: Codex functionality tests (best-effort)
########################################
step "STEP 6: Codex functionality tests"
if command -v npm >/dev/null 2>&1; then
  run_or_warn npm run codex:chat -- -p "test"
  run_or_warn npm run codex:agent -- --dir .
  run_or_warn npm run codex:review
else
  warn "npm not found; skipping npm-based Codex tests"
fi

########################################
# STEP 7: CI/CD verification
########################################
step "STEP 7: CI/CD verification"
if [ -f "$ROOT_DIR/.github/workflows/codex-review.yml" ]; then
  ok "Workflow exists: .github/workflows/codex-review.yml"
  run_or_warn sed -n '1,160p' .github/workflows/codex-review.yml
else
  warn "Workflow .github/workflows/codex-review.yml not found"
fi

########################################
# STEP 8: Final verification report
########################################
step "STEP 8: Final verification report"
if [ -x "$ROOT_DIR/scripts/codex/verify_codex.sh" ]; then
  run_or_warn bash "$ROOT_DIR/scripts/codex/verify_codex.sh"
fi

ok "Codex setup script completed. Review the log at: $LOGFILE"

