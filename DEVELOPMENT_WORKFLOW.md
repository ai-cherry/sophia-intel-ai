# Development Workflow Guide

## 📋 Branch Strategy

### Main Branches
- **`main`**: Production-ready code, protected, requires PR approval
- **`development`**: Integration branch for all features, deploy here first
- **`backup-main-YYYYMMDD`**: Backup snapshots of main branch

### Development Workflow

1. **Start New Feature**
   ```bash
   git checkout development
   git pull origin development
   git checkout -b feature/voice-enhancements
   ```

2. **Daily Development**
   ```bash
   # Work on your feature
   git add .
   git commit -m "feat(voice): add new feature with detailed description"
   git push origin feature/voice-enhancements
   ```

3. **Integration Testing**
   ```bash
   # Merge to development for testing
   git checkout development
   git pull origin development
   git merge feature/voice-enhancements
   git push origin development
   ```

4. **Production Release**
   ```bash
   # Only after thorough testing in development
   git checkout main
   git pull origin main
   git merge development
   git push origin main
   ```

## 🔧 Current Project Status

### Recently Completed ✅
- **Unified Voice System**: Balanced Bella voice across all platforms
- **Cross-Platform Integration**: Terminal, Builder, Sophia Intel, Mobile ready
- **Tech Debt Cleanup**: Removed duplicate files and old backups
- **Shell Aliases Fixed**: All voice commands work properly
- **Enhanced Voice Quality**: ElevenLabs v3 with balanced settings

### Voice System Architecture
```
voice/
├── unified_voice_system.py      # Main system
├── personality/
│   ├── elevenlabs_flirty.py    # Balanced Bella implementation
│   └── flirty_assistant.py     # Mac fallback
└── terminal_integration.py     # Terminal commands

app/api/routers/
└── voice_builder.py            # Builder app endpoints

Terminal Commands:
- vc "text"           # Quick voice
- psay "text"         # Premium Bella
- voice-test          # Test system
```

### Voice Configuration
- **Voice**: Bella - Bubbly Best Friend (`wrxvN1LZJIfL3HHvffqe`)
- **Model**: ElevenLabs v3
- **Settings**: stability=0.5, similarity_boost=0.775, style=0.6
- **Context-Aware**: Different SSML for success/error/general/coding

## 📦 Git Commit Standards

### Commit Message Format
```
type(scope): brief description

Detailed explanation of changes
- Feature A implemented
- Bug B fixed
- Enhancement C added

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Commit Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

## 🚀 Deployment Strategy

### Development Deployment
```bash
# Test in development first
git checkout development
./deploy_local_complete.sh
# Run comprehensive tests
python test_unified_voice.py
```

### Production Deployment
```bash
# Only after development testing passes
git checkout main
git merge development
git push origin main
# Production deploy
./launch_production.sh
```

## 🧹 Maintenance Tasks

### Weekly Cleanup
```bash
# Remove old backup branches (keep last 3)
git branch -r | grep backup-main | head -n -3 | xargs -I {} git push origin --delete {}

# Clean local branches
git branch --merged development | grep -v "main\|development" | xargs -n 1 git branch -d
```

### Monthly Audits
- Review and update dependencies
- Avoid accumulating large doc archives in-repo; prefer concise live docs.
- Validate all voice commands work
- Update documentation

## 🎯 Next Sprint Goals

### High Priority
1. **Mobile PWA Enhancement**: Complete mobile voice interface
2. **Builder Integration**: Full voice-to-code pipeline
3. **Sophia Intel Integration**: Deep voice integration with all agents
4. **Performance Optimization**: Reduce voice latency <500ms

### Medium Priority
1. **Voice Command Expansion**: Add more specialized commands
2. **Multi-Language Support**: Expand beyond English
3. **Voice Authentication**: User-specific voice profiles
4. **Analytics Dashboard**: Voice usage metrics

## 🔍 Quality Gates

### Pre-Push Checklist
- [ ] All tests pass (`python test_unified_voice.py`)
- [ ] Voice commands work in terminal
- [ ] No merge conflicts
- [ ] Commit messages follow standards
- [ ] No sensitive data in commits

### Pre-Production Checklist
- [ ] Development deployment successful
- [ ] All voice endpoints tested
- [ ] Performance benchmarks met
- [ ] Security audit passed
- [ ] Documentation updated

## 📞 Emergency Procedures

### Rollback Process
```bash
# If production issues occur
git checkout main
git reset --hard backup-main-20250911  # Use latest backup
git push origin main --force-with-lease

# Redeploy
./launch_production.sh
```

### Hotfix Process
```bash
git checkout main
git checkout -b hotfix/critical-voice-fix
# Make minimal fix
git commit -m "hotfix: critical voice system fix"
git checkout main
git merge hotfix/critical-voice-fix
git push origin main
# Also merge to development
git checkout development
git merge main
git push origin development
```

---

**Last Updated**: September 11, 2025
**Voice System Status**: ✅ Production Ready
**Current Sprint**: Voice System Enhancement & Mobile PWA
