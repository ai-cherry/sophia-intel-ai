# 🔀 Git Branching Strategy

## 📊 Branch Structure

### **main** (Protected)
- Production-ready code
- All features fully tested
- Requires PR from development
- Protected branch rules:
  - Require pull request reviews
  - Dismiss stale pull request approvals
  - Require status checks to pass
  - Include administrators

### **development** (Default for work)
- Active development branch
- All new features go here first
- Regularly synced with main
- Daily work happens here

### **feature/** branches
- For specific features: `feature/voice-improvements`
- Branch from development
- PR back to development
- Delete after merge

### **hotfix/** branches
- For urgent production fixes
- Branch from main
- PR to both main AND development
- Delete after merge

---

## 🔄 Workflow

### **Daily Development**
```bash
# Start on development branch
git checkout development
git pull origin development

# Create feature branch
git checkout -b feature/your-feature

# Work and commit
git add .
git commit -m "feat: your feature"

# Push to GitHub
git push origin feature/your-feature

# Create PR to development (via GitHub UI)
```

### **Sync Development with Main**
```bash
# On development branch
git checkout development
git pull origin main
git push origin development
```

### **Deploy to Production**
```bash
# Create PR from development to main
# Via GitHub UI or:
gh pr create --base main --head development \
  --title "Release: Development to Main" \
  --body "Production deployment of tested features"
```

---

## 📝 Commit Message Format

### **Types**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `style:` Formatting
- `refactor:` Code restructuring
- `test:` Tests
- `chore:` Maintenance

### **Examples**
```
feat(voice): Add bidirectional audio support
fix(api): Resolve timeout in voice endpoint
docs: Update voice system documentation
refactor(voice): Reorganize voice modules
```

---

## 🛡️ Protection Rules

### **Main Branch**
1. Go to GitHub Settings → Branches
2. Add rule for `main`:
   - ✅ Require pull request reviews (1)
   - ✅ Dismiss stale PR approvals
   - ✅ Require branches to be up to date
   - ✅ Include administrators
   - ✅ Restrict who can push

### **Development Branch**
1. Add rule for `development`:
   - ✅ Require pull request reviews (optional)
   - ✅ Require branches to be up to date
   - ⬜ Allow direct pushes (for quick fixes)

---

## 🚀 Current Status

- **main**: Production-ready with voice system ✅
- **development**: Synced with main ✅
- Both branches pushed to GitHub ✅

---

## 📋 Quick Commands

```bash
# Check current branch
git branch

# Switch to development
git checkout development

# Update from remote
git pull origin development

# Create feature branch
git checkout -b feature/new-feature

# Push changes
git add .
git commit -m "feat: description"
git push origin feature/new-feature

# Create PR
gh pr create

# Merge PR (after review)
gh pr merge
```

---

## 🔒 Security Notes

- Never commit secrets or API keys
- Use environment variables
- Review changes before pushing
- Test locally before PR

---

**Last Updated**: September 11, 2025
**Repository**: github.com/ai-cherry/sophia-intel-ai