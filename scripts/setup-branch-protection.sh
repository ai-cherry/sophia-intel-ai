#!/usr/bin/env bash
set -e

# Branch Protection Setup Script
# Configures main branch protection rules for the repository

# Repository details - update these
OWNER="ai-cherry"
REPO="sophia-intel"

echo "🔒 Setting up branch protection for $OWNER/$REPO..."

# Check if gh is authenticated
if ! gh auth status >/dev/null 2>&1; then
    echo "❌ GitHub CLI not authenticated. Run 'make gh-login' first."
    exit 1
fi

# Apply branch protection rules
gh api -X PUT "repos/$OWNER/$REPO/branches/main/protection" --input - <<'JSON'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["lint-format-test"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true,
  "lock_branch": false,
  "allow_fork_syncing": false
}
JSON

echo "✅ Branch protection enabled for main branch"
echo ""
echo "Protection settings applied:"
echo "  • Required status checks: lint-format-test (CI Checks)"
echo "  • Required PR reviews: 1 approver minimum"
echo "  • Code owner reviews: Required"
echo "  • Enforce for admins: Yes"
echo "  • Dismiss stale reviews: Yes"
echo "  • Force pushes: Disabled"
echo "  • Branch deletion: Disabled"
echo "  • Require conversation resolution: Yes"
