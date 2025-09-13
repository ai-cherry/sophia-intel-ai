#!/bin/bash

# Quick script to add your Portkey virtual key

echo "🔑 Add Portkey Virtual Key to All Tools"
echo "========================================"
echo ""

# Check if key is already set
CURRENT_KEY=$(grep PORTKEY_API_KEY .env.master | cut -d'"' -f2)

if [ "$CURRENT_KEY" != "pk-vk-your-virtual-key-here" ] && [ -n "$CURRENT_KEY" ]; then
    echo "✅ Found existing Portkey key: ${CURRENT_KEY:0:20}..."
    read -p "Replace with new key? (y/n): " REPLACE
    if [ "$REPLACE" != "y" ]; then
        echo "Keeping existing key."
        exit 0
    fi
fi

echo "To get your Portkey virtual key:"
echo "1. Go to https://dashboard.portkey.ai"
echo "2. Sign in/Sign up"
echo "3. Go to 'Virtual Keys' in sidebar"
echo "4. Click 'Add Key'"
echo "5. Link your API providers (OpenAI, Anthropic, OpenRouter, etc.)"
echo "6. Copy the pk-vk-xxx key"
echo ""

read -p "Enter your Portkey virtual key (pk-vk-xxx): " NEW_KEY

if [ -z "$NEW_KEY" ]; then
    echo "❌ No key provided"
    exit 1
fi

echo ""
echo "Updating all configurations..."

# Update .env.master
sed -i '' "s/pk-vk-your-virtual-key-here/$NEW_KEY/g" ~/sophia-intel-ai/.env.master
echo "✅ Updated .env.master"

# Update Opencode auth.json
sed -i '' "s/pk-vk-your-virtual-key-here/$NEW_KEY/g" ~/.local/share/opencode/auth.json
echo "✅ Updated Opencode auth.json"

# Export for current session
export PORTKEY_API_KEY="$NEW_KEY"

echo ""
echo "✅ Portkey key configured!"
echo ""
echo "Now you can use ANY model through Portkey:"
echo ""
echo "In Opencode TUI:"
echo "  /switch portkey"
echo "  Then use any model:"
echo "  - gpt-4o"
echo "  - claude-3-5-sonnet"  
echo "  - openrouter/mistralai/mistral-7b-instruct"
echo "  - together/meta-llama/Llama-3-70b-chat"
echo ""
echo "Or via CLI:"
echo "  opencode run --provider portkey --model 'gpt-4o' 'Your prompt'"
echo "  opencode run --provider portkey-openrouter --model 'mistralai/mistral-7b' 'Your prompt'"
echo ""
echo "Test it now:"
echo "  cd ~/sophia-intel-ai && opencode"