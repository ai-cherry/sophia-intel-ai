#!/bin/bash
# M3 Environment Verification

echo 'M3 Mac Environment Check'
echo '========================'

# Check architecture
if [[ $(uname -m) == 'arm64' ]]; then
    echo '✅ Architecture: ARM64'
else
    echo '❌ Architecture: NOT ARM64 - Run: arch -arm64 zsh'
    exit 1
fi

# Check Python
if python3 -c 'import platform; exit(0 if platform.machine() == "arm64" else 1)' 2>/dev/null; then
    echo '✅ Python: ARM64'
else
    echo '❌ Python: Not ARM64'
fi

# Check key tools
for tool in redis-server psql node npm; do
    if which $tool | grep -q homebrew; then
        echo "✅ $tool: Homebrew"
    else
        echo "⚠️  $tool: Not from Homebrew"
    fi
done

echo ''
echo 'Ready for M3-optimized deployment!'
