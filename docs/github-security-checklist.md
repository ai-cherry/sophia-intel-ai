# GitHub Security Checklist

## ✅ Validation Results (Completed)

### CLI Authentication
- ✅ GitHub CLI authenticated with token (ghu_****)
- ✅ Using HTTPS protocol for git operations
- ✅ Credential helper: Codespaces secure helper
- ✅ Repository access verified (ai-cherry/sophia-intel)

### Local Security Cleanup
- ✅ Shell history cleared (history -c; history -w)
- ✅ Session history disabled (unset HISTFILE)
- ✅ No plaintext passwords in git config

## 🔐 GitHub Account Security Tasks

Please verify these settings on GitHub (github.com → Settings):

### 1. Password & Authentication
- [ ] Confirm password authentication is NOT used for git operations
- [ ] Verify only Personal Access Tokens (PATs) are in use
- [ ] No stored passwords in any credential managers

### 2. Personal Access Token Settings
Navigate to: Settings → Developer settings → Personal access tokens

#### Fine-grained tokens (Recommended)
- [ ] Token has minimal required scopes:
  - `repo` (if needed for private repos)
  - `workflow` (if using GitHub Actions)
  - No unnecessary admin/delete permissions
- [ ] Expiration date is set (recommend 30-90 days)
- [ ] Token is limited to specific repositories if possible

#### Classic tokens (if used)
- [ ] Minimal scopes selected
- [ ] Expiration date configured

### 3. Two-Factor Authentication (2FA)
Navigate to: Settings → Password and authentication → Two-factor authentication

- [ ] 2FA is ENABLED (highly recommended)
- [ ] Backup codes are saved securely
- [ ] Recovery options configured

### 4. Additional Security Measures
- [ ] Review active sessions (Settings → Sessions)
- [ ] Check authorized OAuth apps
- [ ] Review SSH keys if used
- [ ] Enable vigilant mode for commit signing (optional)

## 🚨 Important Notes

1. **Never share tokens**: Treat PATs like passwords
2. **Rotate regularly**: Set expiration dates and rotate tokens
3. **Use fine-grained tokens**: More secure than classic tokens
4. **Enable 2FA**: Critical for account security
5. **Monitor activity**: Check security log regularly

## Token Best Practices

### Creating Secure Tokens
```bash
# When creating tokens:
# - Use descriptive names (e.g., "codespace-sophia-intel")
# - Set shortest practical expiration
# - Grant minimal required permissions
# - Store securely (use GitHub Secrets for CI/CD)
```

### If Token is Compromised
1. Immediately revoke the token on GitHub
2. Generate a new token
3. Update all services using the old token
4. Review security log for unauthorized access

---
Last Updated: 2025-08-11
