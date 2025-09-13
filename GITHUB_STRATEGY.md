# 🎯 GitHub Strategy for Sophia Intel AI
**Single Developer Project - Simple & Effective**

## Core Principles
- **Keep it simple** - No unnecessary complexity
- **Direct to main** - For single developer, skip feature branches
- **Commit often** - Small, frequent commits are better than large ones
- **Clear messages** - Future you will thank present you

---

## 📝 Commit Strategy

### Direct Commits to Main (Recommended for Solo Dev)
```bash
# Make changes
git add .
git commit -m "feat: Add new API endpoint for user auth"
git push origin main
```

### Commit Message Format
Use simple prefixes for clarity:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only
- `refactor:` Code restructuring
- `test:` Adding tests
- `chore:` Maintenance tasks

Examples:
```bash
git commit -m "feat: Add Gemini API integration"
git commit -m "fix: Resolve Redis connection timeout"
git commit -m "docs: Update API key setup instructions"
git commit -m "refactor: Consolidate duplicate auth logic"
```

---

## 🔄 Daily Workflow

### Morning Sync
```bash
# Start your day
git pull origin main
./sophia status  # Check services
```

### During Development
```bash
# Commit frequently (every 1-2 hours of work)
git add -A
git commit -m "feat: Work in progress on dashboard"
git push

# Or use the quick commit alias
git config --global alias.wip '!git add -A && git commit -m "wip: Work in progress" && git push'
git wip  # Quick save to GitHub
```

### End of Day
```bash
# Clean commit before stopping
git add -A
git commit -m "feat: Complete dashboard implementation"
git push origin main
```

---

## 🛡️ Safety Practices

### 1. Protected Files (Never Commit)
Already in `.gitignore`:
- `.env.master` - API keys
- `*.log` - Log files
- `.pids/` - Process IDs
- `__pycache__/` - Python cache

### 2. Pre-Push Checklist
```bash
# Before pushing, always check:
git status           # What's being committed?
git diff --staged    # Review changes
./sophia test        # Run basic tests
```

### 3. Backup Strategy
```bash
# Weekly backup branch (optional but recommended)
git checkout -b backup/2025-09-13
git push origin backup/2025-09-13
git checkout main
```

---

## 🏷️ Release Tags (Monthly)

Mark stable versions monthly:
```bash
# Tag a stable version
git tag -a v1.0.0 -m "September 2025 stable release"
git push origin v1.0.0

# List tags
git tag -l

# Checkout specific version
git checkout v1.0.0
```

---

## 🚫 What NOT to Do

1. **Don't use complex branching** - You're solo, keep it simple
2. **Don't squash commits** - History is valuable
3. **Don't force push** - Unless absolutely necessary
4. **Don't commit sensitive data** - Check `git status` first

---

## ⚡ Quick Commands

Add these aliases to your shell:
```bash
# Add to ~/.zshrc or ~/.bashrc
alias gs='git status'
alias ga='git add -A'
alias gc='git commit -m'
alias gp='git push origin main'
alias gl='git log --oneline -10'

# Quick save everything
alias gsave='git add -A && git commit -m "chore: Save work" && git push'
```

---

## 📊 GitHub Repository Settings

### Recommended Settings for sophia-intel-ai:
1. **Default branch**: main
2. **Branch protection**: OFF (you're solo)
3. **Issues**: ON (track your TODOs)
4. **Wiki**: OFF (use markdown files instead)
5. **Projects**: Optional (use if you like kanban boards)

### Security Settings:
- ✅ Dependabot alerts: ON
- ✅ Secret scanning: ON
- ✅ Private repository: Your choice

---

## 🔧 Maintenance Tasks

### Weekly
```bash
# Clean up local branches
git branch --merged | grep -v main | xargs -r git branch -d

# Update dependencies
pip3 install --upgrade -r requirements.txt
```

### Monthly
```bash
# Create release tag
git tag -a v$(date +%Y.%m) -m "Monthly release"
git push origin --tags

# Review and clean old branches on GitHub
gh repo view --web
```

---

## 💡 Pro Tips for Solo Development

1. **Commit before experiments**
   ```bash
   git commit -am "chore: Checkpoint before trying new approach"
   ```

2. **Use stash for quick switches**
   ```bash
   git stash save "Experimental feature"
   git stash list
   git stash pop
   ```

3. **Track TODOs in GitHub Issues**
   ```bash
   gh issue create --title "Add user authentication" --body "Need to implement JWT auth"
   gh issue list
   ```

4. **Use GitHub as backup**
   - Push at least daily
   - Push before leaving your computer
   - Push completed features immediately

---

## 🚀 Quick Start Each Day

```bash
#!/bin/bash
# Add to your .zshrc or create a 'work' alias

work() {
  cd ~/sophia-intel-ai
  git pull origin main
  ./sophia start
  ./sophia status
  echo "Ready to code! 🚀"
}
```

---

## Summary

**For single developer projects, simplicity wins:**
- Commit directly to main
- Push frequently (multiple times per day)
- Use clear commit messages
- Tag monthly releases
- Keep sensitive files in .gitignore

**Remember**: GitHub is your backup, changelog, and time machine. Use it liberally!

---

*Last Updated: September 13, 2025*