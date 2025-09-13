#!/bin/bash

# Nuclear .zshrc fix - removes all voice crap, fixes braces

echo "🔧 Fixing .zshrc - nuking voice functions and orphan braces..."

# Backup
cp ~/.zshrc ~/.zshrc.bak_$(date +%Y%m%d_%H%M%S)

# Comment out all voice-related functions completely
sed -i '' '/^# Voice-activated Claude/,/^# \}/ s/^/# /' ~/.zshrc
sed -i '' '/^# Voice git commit/,/^# \}/ s/^/# /' ~/.zshrc
sed -i '' '/^vcode()/,/^}/ s/^/# /' ~/.zshrc
sed -i '' '/^vgit()/,/^}/ s/^/# /' ~/.zshrc
sed -i '' '/^fsay()/,/^}/ s/^/# /' ~/.zshrc
sed -i '' '/^fgit()/,/^}/ s/^/# /' ~/.zshrc
sed -i '' '/^fcode()/,/^}/ s/^/# /' ~/.zshrc
sed -i '' '/^psay()/,/^}/ s/^/# /' ~/.zshrc
sed -i '' '/^psayv()/,/^}/ s/^/# /' ~/.zshrc
sed -i '' '/^test-bella()/,/^}/ s/^/# /' ~/.zshrc
sed -i '' '/^vibe()/,/^}/ s/^/# /' ~/.zshrc

# Remove ALL orphaned closing braces on their own lines
sed -i '' -E '/^[[:space:]]*\}[[:space:]]*$/d' ~/.zshrc

# Remove duplicate PATH exports for opencode
sed -i '' '/export PATH.*opencode/d' ~/.zshrc

# Add clean PATH export at the end
echo '' >> ~/.zshrc
echo '# Opencode CLI' >> ~/.zshrc
echo 'export PATH="$HOME/.opencode/bin:$PATH"' >> ~/.zshrc

echo "✅ Fixed .zshrc - testing..."

# Test
if source ~/.zshrc 2>&1 | grep -E "error|parse"; then
    echo "❌ Still has errors, checking..."
    source ~/.zshrc 2>&1 | head -5
else
    echo "✅ .zshrc loads clean!"
    which opencode && opencode --version || echo "Opencode: Use full path ~/.opencode/bin/opencode"
fi