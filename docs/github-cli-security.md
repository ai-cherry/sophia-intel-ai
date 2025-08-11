# GitHub CLI Security Best Practices

## 🔐 Important Security Notice

**NEVER** store or share your GitHub username and password in:
- Code files
- Scripts
- Configuration files
- Terminal history
- Chat messages

GitHub has **deprecated password authentication** for Git operations. Use Personal Access Tokens (PAT) or SSH keys instead.

## ✅ Secure Authentication in Codespaces

### Using Your Existing Token (Recommended)
Your `GH_FINE_GRAINED_TOKEN` is already configured as a Codespaces secret and automatically available:

```bash
# Secure: Uses token from environment variable
printf "%s" "$GH_FINE_GRAINED_TOKEN" | gh auth login --with-token

# NEVER do this:
gh auth login --with-token <<< "ghp_actualTokenHere"  # ❌ Token visible in history
echo $GH_FINE_GRAINED_TOKEN | gh auth login          # ❌ Token might be logged
```

### Token Security Checklist

- ✅ **Store tokens as Codespaces/GitHub secrets** - Never in code
- ✅ **Use `printf` instead of `echo`** - Prevents accidental logging
- ✅ **Pipe tokens directly** - Avoids command history exposure
- ✅ **Set minimal token scopes** - Only grant necessary permissions
- ✅ **Rotate tokens regularly** - Update in Codespaces secrets when you do
- ✅ **Use fine-grained tokens** - Better than classic tokens

## 🛡️ Hardening Configuration

### 1. Lock Git to Use GitHub CLI's Credential Helper
```bash
gh auth setup-git
```
This ensures all git operations use gh's secure credential storage.

### 2. Verify Authentication Status
```bash
# Quick health check
make gh-doctor

# Or manually:
gh auth status
gh repo view
```

### 3. Token Rotation Process
When you rotate your token:

1. Update the secret in GitHub:
   - Go to Settings → Codespaces → Secrets
   - Update `GH_FINE_GRAINED_TOKEN` with new token

2. Rebuild your Codespace or run:
   ```bash
   gh auth refresh -h github.com -s repo,workflow
   ```

## 🚨 If Credentials Are Exposed

If you accidentally expose credentials:

1. **Immediately revoke the token:**
   - GitHub Settings → Developer settings → Personal access tokens
   - Click "Revoke" on the exposed token

2. **Create a new token** with appropriate scopes

3. **Update Codespaces secret** with new token

4. **Check for unauthorized access:**
   ```bash
   gh api user/repos --paginate | jq '.[].full_name'
   gh api /user/keys
   ```

## 🔍 Monitoring Commands

```bash
# Check current authentication
gh auth status

# View token scopes
gh auth status --show-token 2>&1 | grep "Token scopes"

# List all SSH keys
gh api /user/keys

# Recent activity
gh api /users/$(gh api user --jq .login)/events --paginate
```

## 📋 Quick Reference

| Command | Purpose | Security Level |
|---------|---------|----------------|
| `printf "%s" "$TOKEN" \| gh auth login --with-token` | Authenticate with token | ✅ Secure |
| `gh auth setup-git` | Configure git credential helper | ✅ Secure |
| `make gh-doctor` | Health check | ✅ Safe |
| `gh auth login` | Interactive browser login | ✅ Secure |
| `echo $TOKEN \| gh auth login` | Authenticate (risky) | ⚠️ Avoid |
| `gh auth login --with-token <<< "token"` | Hardcoded token | ❌ Never |

## 🎯 Remember

- Tokens are like passwords - treat them with the same security
- Use environment variables, not hardcoded values
- Enable 2FA on your GitHub account
- Review token permissions regularly
- Use the principle of least privilege for token scopes

## 🔒 Additional Security Measures (Implemented)

### 1. CI/CD Authentication Guard
We've added a non-blocking CI check to verify GitHub CLI authentication:

```yaml
# .github/workflows/checks.yml
- name: GitHub CLI auth smoke
  run: |
    gh auth status || (echo "::warning::gh not logged in in CI context (fine for PRs from forks)"; exit 0)
```

This provides visibility without breaking PR builds from forks.

### 2. Pre-Commit Hook for Secret Detection
A git pre-commit hook is now installed to prevent accidental secret commits:

```bash
# .git/hooks/pre-commit (already installed)
# Scans for patterns: ghp_*, ghu_*, api_key, secret, token
# Bypass with: git commit --no-verify (use cautiously)
```

### 3. Quick Auth Check
New lightweight make target for rapid authentication verification:

```bash
make auth-doctor  # Quick auth status check
```

## 📐 Repository Protection Settings

### Recommended GitHub Settings
Navigate to: Settings → Branches → Add rule

- **Require pull request reviews**: ≥1 reviewer
- **Require status checks**:
  - `checks` (linting and tests)
  - `index-on-pr` (if configured)
  - `branch-audit` (if configured)
- **Restrict who can push to main**: Only maintainers
- **Require branches to be up to date**: Yes
- **Include administrators**: Consider enabling

### Advanced Security Features
If available in your GitHub plan:

- **Secret scanning**: Automatically detect exposed secrets
- **Dependency scanning**: Find vulnerable dependencies
- **Code scanning**: Static analysis for security issues

## 🤖 Future Enhancement: GitHub App Migration

Consider migrating from Personal Access Tokens to a GitHub App for:
- **Short-lived tokens**: Automatically expire
- **Fine-grained permissions**: Per-repository access
- **Better audit trail**: App-specific activity logs
- **No user dependency**: Not tied to personal accounts

To implement:
1. Create GitHub App with minimal permissions
2. Generate App manifest with required scopes
3. Wire into GitHub Actions workflows
4. Phase out PAT usage

## 🛠️ Maintenance Commands

```bash
# Full security validation
make gh-doctor

# Quick auth check
make auth-doctor

# Test pre-commit hook
echo "ghp_test" > test.txt && git add test.txt && git commit -m "test"
# Should be blocked by pre-commit hook

# Check for exposed secrets in history
git log -p | grep -E 'ghp_|ghu_|api_key|secret|token' || echo "✅ No secrets found"
```

## 📊 Security Checklist Summary

| Security Measure | Status | Location |
|-----------------|--------|----------|
| Token-based auth only | ✅ | GitHub CLI |
| CI auth verification | ✅ | `.github/workflows/checks.yml` |
| Pre-commit secret scan | ✅ | `.git/hooks/pre-commit` |
| Quick auth check | ✅ | `make auth-doctor` |
| Branch protection | ⏳ | GitHub Settings |
| 2FA enabled | ⏳ | GitHub Account |
| Secret scanning | ⏳ | GitHub Advanced Security |
| GitHub App migration | 📋 | Future enhancement |

---
Last Updated: 2025-08-11
Security Hardening Applied ✅