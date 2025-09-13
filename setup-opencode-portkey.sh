#!/bin/bash

# Setup Opencode with Portkey Virtual Keys

echo "🔧 Configuring Opencode to use Portkey Virtual Keys"
echo "===================================================="
echo ""

# Check if you have a Portkey virtual key
if [ -z "$PORTKEY_API_KEY" ] || [ "$PORTKEY_API_KEY" == "pk-vk-your-virtual-key-here" ]; then
    echo "❌ PORTKEY_API_KEY not set or still placeholder!"
    echo ""
    echo "To get your Portkey virtual key:"
    echo "1. Go to dashboard.portkey.ai"
    echo "2. Create account/login"
    echo "3. Go to Virtual Keys → Add Key"
    echo "4. Link your providers (OpenAI, Anthropic, etc.)"
    echo "5. Copy the pk-vk-xxx key"
    echo "6. Add to .env.master: PORTKEY_API_KEY='pk-vk-xxx'"
    echo ""
    read -p "Enter your Portkey virtual key (pk-vk-xxx): " PORTKEY_KEY
    
    if [ -n "$PORTKEY_KEY" ]; then
        # Update .env.master
        sed -i '' "s/pk-vk-your-virtual-key-here/$PORTKEY_KEY/g" ~/sophia-intel-ai/.env.master
        export PORTKEY_API_KEY="$PORTKEY_KEY"
        echo "✅ Updated .env.master with your Portkey key"
    else
        echo "❌ No key provided. Exiting."
        exit 1
    fi
else
    echo "✅ Found PORTKEY_API_KEY: ${PORTKEY_API_KEY:0:20}..."
fi

echo ""
echo "Adding Portkey to Opencode..."

# Create auth.json for Opencode with Portkey
cat > ~/.local/share/opencode/auth.json << EOF
{
  "credentials": [
    {
      "provider": "portkey",
      "name": "Portkey Gateway",
      "apiKey": "$PORTKEY_API_KEY",
      "baseURL": "https://api.portkey.ai/v1",
      "headers": {
        "x-portkey-provider": "openai",
        "x-portkey-mode": "fallback"
      }
    }
  ]
}
EOF

echo "✅ Created Opencode auth.json with Portkey"
echo ""

# Test the configuration
echo "Testing Portkey in Opencode..."
~/.opencode/bin/opencode auth list

echo ""
echo "📋 To use Portkey models in Opencode:"
echo ""
echo "1. Launch Opencode:"
echo "   cd ~/sophia-intel-ai && opencode"
echo ""
echo "2. In TUI, use Portkey models:"
echo "   /model portkey/gpt-4o"
echo "   /model portkey/claude-3-5-sonnet"
echo ""
echo "3. Or via CLI:"
echo "   opencode run --model portkey/gpt-4o 'Your prompt'"
echo ""
echo "Note: The generic models you saw are from raw API keys."
echo "With Portkey, you get virtual key routing, fallbacks, and monitoring."