# GitHub Integration Setup for CLI Agents

## Overview

The Sophia Intel AI system includes comprehensive GitHub integration that allows agents to safely interact with version control, create commits, manage branches, and even create pull requests.

## Quick Setup

### 1. Basic Configuration

Add to your `<repo>/.env.master`:

```bash
# Git Configuration
GIT_USER_NAME="Your Name"
GIT_USER_EMAIL="your.email@example.com"

# Safety Controls
GIT_SAFE_MODE=false        # Set to true for dry-run mode
GIT_ALLOW_PUSH=false       # Set to true to enable pushing
GIT_AUTO_STASH=false       # Set to true to auto-stash changes

# GitHub Authentication (choose one method)
GITHUB_TOKEN=ghp_...       # Personal access token
# OR use SSH keys (recommended)
```

### 2. SSH Key Setup (Recommended)

```bash
# Generate SSH key if you don't have one
ssh-keygen -t ed25519 -C "your.email@example.com"

# Add to SSH agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Copy public key to GitHub
cat ~/.ssh/id_ed25519.pub
# Add this to GitHub Settings > SSH and GPG keys
```

### 3. GitHub CLI Setup (for PR creation)

```bash
# Install GitHub CLI
brew install gh  # macOS
# OR
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo gpg --dearmor -o /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update && sudo apt install gh  # Linux

# Authenticate
gh auth login
```

## Usage

### CLI Commands

```bash
# Check repository status
python sophia_cli.py git status

# Create a feature branch
python sophia_cli.py git branch feature/my-feature

# Commit changes
python sophia_cli.py git commit -m "feat: Add new feature"

# Push changes (requires GIT_ALLOW_PUSH=true)
python sophia_cli.py git push

# Create a pull request
python sophia_cli.py git pr "feat: Add new feature" "Detailed description..."
```

### Agent Integration

Agents automatically use GitHub integration when enabled:

```python
from builder_cli.lib.github import GitHubIntegration

# Initialize
github = GitHubIntegration()

# Commit agent work
result = github.commit_agent_work(
    task_type="feature",
    changes_summary="Implement user authentication",
    detailed_changes=[
        "Added login endpoint",
        "Created user model",
        "Added JWT token generation"
    ]
)

if result["success"]:
    print(f"Committed to branch: {result['branch']}")
    if result["pr_url"]:
        print(f"Pull request: {result['pr_url']}")
```

## Safety Features

### 1. Safe Mode (Default)

When `GIT_SAFE_MODE=true`, all Git operations are simulated:
- No actual commits are made
- No branches are created
- No pushes occur
- Useful for testing

### 2. Push Protection

Pushing is disabled by default. To enable:
1. Set `GIT_ALLOW_PUSH=true` in environment
2. Ensure authentication is configured (SSH or token)

### 3. Branch Protection

Agents automatically:
- Create feature branches for non-trivial changes
- Never push directly to main/master
- Generate descriptive branch names

### 4. Commit Standards

All agent commits follow conventions:
- Semantic commit messages
- Co-author attribution
- Detailed change descriptions

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GIT_USER_NAME` | "Sophia Agent" | Git commit author name |
| `GIT_USER_EMAIL` | "agent@sophia-intel.ai" | Git commit author email |
| `GIT_SAFE_MODE` | "true" | Enable dry-run mode |
| `GIT_ALLOW_PUSH` | "false" | Allow pushing to remote |
| `GIT_AUTO_STASH` | "false" | Auto-stash uncommitted changes |
| `GITHUB_TOKEN` | - | GitHub personal access token |

## Security Best Practices

1. **Never commit secrets**: The system automatically checks for common secret patterns
2. **Use SSH keys**: More secure than tokens for automated systems
3. **Limit token scope**: If using PAT, use minimum required permissions
4. **Review agent commits**: Always review automated commits before merging
5. **Use feature branches**: Agents create branches by default for safety

## Troubleshooting

### Authentication Issues

```bash
# Test SSH connection
ssh -T git@github.com

# Test GitHub CLI
gh auth status

# Check git config
git config --list | grep user
```

### Push Failures

1. Check `GIT_ALLOW_PUSH` is set to "true"
2. Verify authentication is configured
3. Ensure branch permissions allow pushing
4. Check for branch protection rules

### Commit Issues

1. Ensure repository is not in detached HEAD state
2. Check for uncommitted changes blocking operations
3. Verify file permissions allow modifications

## Advanced Configuration

### Custom Commit Templates

Create `.gitmessage` in repository root:

```
feat(<scope>): <summary>

<detailed description>

Refs: #<issue>
```

Configure git to use template:
```bash
git config commit.template .gitmessage
```

### Pre-commit Hooks

Agents respect pre-commit hooks. Install hooks for code quality:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Integration with CI/CD

Agent commits trigger CI/CD pipelines automatically:

1. **Branch creation** → Triggers PR checks
2. **Commits** → Runs tests and linting
3. **PR creation** → Enables review workflow
4. **Merge** → Deploys to staging/production

## Monitoring Agent Activity

Track agent Git operations:

```bash
# View agent commits
git log --author="Sophia Agent"

# Check agent branches
git branch -a | grep agent/

# Review PR history
gh pr list --author="@me"
```

## Support

For issues or questions:
- Check logs: `~/.sophia/logs/git.log`
- Run diagnostic: `python sophia_cli.py git diagnose`
- Report issues: https://github.com/ai-cherry/sophia-intel-ai/issues
