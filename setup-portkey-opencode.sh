#!/bin/bash

# Setup script for Opencode + Portkey integration

echo "🚀 Opencode + Portkey Setup Script"
echo "=================================="

# Check if opencode is installed
if ! command -v opencode &> /dev/null && ! [ -f "$HOME/.opencode/bin/opencode" ]; then
    echo "❌ Opencode not found. Installing..."
    curl -fsSL https://opencode.ai/install | bash
else
    echo "✅ Opencode already installed"
fi

# Add to PATH if needed
export PATH="$HOME/.opencode/bin:$PATH"

echo ""
echo "📋 Current Setup:"
echo "- Opencode version: $(opencode --version 2>/dev/null || echo 'Not in PATH')"
echo "- Config directory: ~/.config/opencode/"
echo ""

echo "🔑 To add Portkey integration:"
echo "1. Get your virtual key from dashboard.portkey.ai"
echo "2. Run: opencode auth login"
echo "3. Select 'Other'"
echo "4. Enter:"
echo "   - Name: portkey"
echo "   - API Key: pk-vk-YOUR-VIRTUAL-KEY"
echo "   - Base URL: https://api.portkey.ai/v1"
echo ""

echo "🧪 Test commands:"
echo "# With environment API keys (working now):"
echo "opencode run 'Generate a Python function'"
echo ""
echo "# With Portkey (after setup):"
echo "opencode run --model 'portkey/gpt-4o' 'Generate code'"
echo ""

