#!/bin/bash
set -e

echo "🚀 GitHub CLI Setup & Health Check"
echo "=================================="

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI not found. Installing..."
    sudo apt-get update
    sudo apt-get install -y gh
fi

# Check for token
if [ -z "$GH_FINE_GRAINED_TOKEN" ]; then
    echo "❌ GH_FINE_GRAINED_TOKEN not found in environment"
    echo "Please ensure it's configured as a Codespaces secret"
    exit 1
fi

# Authenticate using token (never echo it)
echo "🔐 Authenticating with GitHub..."
printf '%s' "$GH_FINE_GRAINED_TOKEN" | gh auth login --with-token 2>/dev/null

# Setup git to use gh credential helper
echo "🔧 Configuring git credential helper..."
gh auth setup-git

# Configure git user if not set
if [ -z "$(git config --get user.name)" ]; then
    echo "📝 Setting git user.name to GitHub username..."
    gh_user=$(gh api user --jq .login)
    git config --global user.name "$gh_user"
fi

if [ -z "$(git config --get user.email)" ]; then
    echo "📝 Setting git user.email..."
    gh_email=$(gh api user --jq .email)
    if [ "$gh_email" != "null" ] && [ -n "$gh_email" ]; then
        git config --global user.email "$gh_email"
    else
        echo "⚠️  Could not auto-detect email. Please set manually:"
        echo "    git config --global user.email 'your-email@example.com'"
    fi
fi

# Health check
echo ""
echo "🔍 Running health check..."
echo "---------------------------"
gh --version
echo ""
gh auth status
echo ""
echo "Repository access:"
gh repo view --json name,owner --jq '"✅ Connected to: \(.owner.login)/\(.name)"' || echo "❌ Could not access repository"
echo ""
echo "Git configuration:"
echo "  User: $(git config --get user.name || echo 'not set')"
echo "  Email: $(git config --get user.email || echo 'not set')"
echo ""
echo "✅ GitHub CLI setup complete!"
echo ""
echo "Quick commands to try:"
echo "  gh pr status      # View PR status"
echo "  gh issue list     # List issues"
echo "  gh repo view      # View repo info"
echo "  make gh-doctor    # Run health check anytime"