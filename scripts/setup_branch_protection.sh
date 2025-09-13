#!/usr/bin/env bash
set -euo pipefail

# Configure branch protection for main and lock legacy-main using GitHub API.
# Requires a PAT with admin:repo and repo:status scopes.
# Usage: OWNER=ai-cherry REPO=sophia-intel-ai GITHUB_TOKEN=... bash scripts/setup_branch_protection.sh

OWNER=${OWNER:-ai-cherry}
REPO=${REPO:-sophia-intel-ai}
API=https://api.github.com

if [ -z "${GITHUB_TOKEN:-}" ]; then
  echo "GITHUB_TOKEN not set." >&2; exit 1
fi

protect_main(){
  cat > /tmp/protect_main.json << 'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": []
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "required_approving_review_count": 1
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_linear_history": true
}
EOF
  curl -sS -o /tmp/resp_main.json -w "%{http_code}\n" \
    -X PUT -H "Authorization: token $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" \
    "$API/repos/$OWNER/$REPO/branches/main/protection" \
    -d @/tmp/protect_main.json
}

lock_legacy(){
  # Minimal protection; disallow force pushes/deletes
  cat > /tmp/protect_legacy.json << 'EOF'
{
  "required_status_checks": null,
  "enforce_admins": true,
  "required_pull_request_reviews": null,
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF
  curl -sS -o /tmp/resp_legacy.json -w "%{http_code}\n" \
    -X PUT -H "Authorization: token $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" \
    "$API/repos/$OWNER/$REPO/branches/legacy-main/protection" \
    -d @/tmp/protect_legacy.json
}

echo "Protecting main..."; code=$(protect_main); echo "HTTP $code"; sed -n '1,60p' /tmp/resp_main.json || true
echo "Locking legacy-main..."; code=$(lock_legacy); echo "HTTP $code"; sed -n '1,60p' /tmp/resp_legacy.json || true

