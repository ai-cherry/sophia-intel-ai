#!/bin/bash
# Install Codex 0.31.0 for M3 Mac

echo 'Installing Codex 0.31.0 for M3 Mac'
echo '=================================='

# Create directory
mkdir -p ~/.codex/bin

# Download Codex for ARM64 Mac
echo 'Downloading Codex 0.31.0...'
curl -L https://github.com/openai/codex/releases/download/rust-v0.31.0/codex-darwin-aarch64 -o ~/.codex/bin/codex

# Make executable
chmod +x ~/.codex/bin/codex

# Add to PATH
echo 'export PATH="$HOME/.codex/bin:$PATH"' >> ~/.zshrc

# Test
~/.codex/bin/codex --version || echo 'Verify manually'

echo 'Done! Run: source ~/.zshrc'
