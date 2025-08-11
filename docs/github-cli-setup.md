# GitHub CLI Setup in Codespaces

## Your Token Status
**You do NOT need to provide the token again!** Since you have `GH_FINE_GRAINED_TOKEN` configured as a Codespaces secret, it's automatically available in your environment.

## Two Options for Installation

### Option 1: Permanent Installation (Recommended)
Add GitHub CLI to your devcontainer so it's always available:

1. Edit `.devcontainer/devcontainer.json` and add the GitHub CLI feature:

```json
{
  "name": "Agno-Dev",
  "image": "mcr.microsoft.com/devcontainers/python:3.11-bullseye",
  "features": {
    "ghcr.io/devcontainers/features/node:1": {
      "version": "20"
    },
    "ghcr.io/devcontainers/features/github-cli:1": {}  // Add this line
  },
  // ... rest of your config
}
```

2. Rebuild your Codespace:
   - Open Command Palette (Cmd/Ctrl+Shift+P)
   - Run: "Codespaces: Rebuild Container"
   - Wait for the rebuild to complete

3. After rebuild, authenticate using your existing token:
```bash
printf "%s" "$GH_FINE_GRAINED_TOKEN" | gh auth login --with-token
```

### Option 2: Quick Installation (Current Session Only)
If you need GitHub CLI right now without rebuilding:

```bash
# Install GitHub CLI
sudo apt-get update
sudo apt-get install -y curl gnupg
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt-get update
sudo apt-get install -y gh

# Authenticate using your existing token
printf "%s" "$GH_FINE_GRAINED_TOKEN" | gh auth login --with-token
```

## Verification Commands
After installation and authentication:

```bash
# Check version
gh --version

# Check authentication status
gh auth status

# View current repo
gh repo view

# Check PR status
gh pr status
```

## Automatic Authentication on Startup
To authenticate automatically every time your Codespace starts, add this to your `.devcontainer/devcontainer.json`:

```json
{
  // ... existing config ...
  "postCreateCommand": "pip install --upgrade pip && pip install -r requirements.txt && printf '%s' \"$GH_FINE_GRAINED_TOKEN\" | gh auth login --with-token 2>/dev/null || true",
  // ... rest of config
}
```

## Key Points
- ✅ Your token is already set as a Codespaces secret
- ✅ It's automatically available as `$GH_FINE_GRAINED_TOKEN`
- ✅ You never need to manually paste or re-enter it
- ✅ The token persists across Codespace restarts
- ✅ Using `printf` with pipe prevents the token from appearing in logs

## Troubleshooting

### Check if token is available:
```bash
echo ${GH_FINE_GRAINED_TOKEN:0:10}...  # Shows first 10 chars
```

### Re-authenticate if needed:
```bash
gh auth logout
printf "%s" "$GH_FINE_GRAINED_TOKEN" | gh auth login --with-token
```

### If token is missing:
1. Go to GitHub Settings → Codespaces → Secrets
2. Ensure `GH_FINE_GRAINED_TOKEN` is set for your repository/organization
3. Restart your Codespace to load the secret