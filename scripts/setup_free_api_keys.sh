#!/bin/bash
# scripts/setup_free_api_keys.sh
# No-Mock API Strategy - Real Keys Only

set -e

echo "================================"
echo "FREE API KEY SETUP GUIDE"
echo "================================"

cat << 'EOF'

Required FREE API Keys (10 minutes to get all):

1. GitHub Token (FREE - Unlimited)
   → Go to: https://github.com/settings/tokens/new
   → Select scopes: repo, read:user, read:org
   → Generate token
   → Add to .env: GITHUB_TOKEN=ghp_xxxxx

2. OpenAI API Key (FREE - $5 credit)
   → Go to: https://platform.openai.com/signup
   → Create account (use Google/GitHub OAuth)
   → Go to: https://platform.openai.com/api-keys
   → Create new secret key
   → Add to .env: OPENAI_API_KEY=sk-xxxxx

3. HubSpot API Key (FREE - 1000 calls/day)
   → Go to: https://app.hubspot.com/signup/developers
   → Create free developer account
   → Settings → Integrations → API Key
   → Add to .env: HUBSPOT_API_KEY=xxxxx

4. Anthropic Claude (OPTIONAL - Request access)
   → Go to: https://console.anthropic.com
   → Request API access (may take time)
   → If approved: ANTHROPIC_API_KEY=sk-ant-xxxxx

5. For Gong/Enterprise APIs:
   → Use feature flags to disable if no key
   → Don't mock - just hide the features

EOF

echo -e "\n✅ Copy the URLs above and get your free keys"
echo "❌ DO NOT use mock keys - they will confuse AI agents"
echo -e "\n🔧 After getting keys, run: ./scripts/sophia_real_apis.sh"

# Check current .env status
if [ -f ".env" ]; then
    echo -e "\n📋 Current .env status:"
    
    check_key() {
        local key=$1
        local name=$2
        if grep -q "^${key}=" .env && [ -n "$(grep "^${key}=" .env | cut -d'=' -f2)" ]; then
            echo "  ✅ $name: Configured"
        else
            echo "  ⬜ $name: Missing"
        fi
    }
    
    check_key "GITHUB_TOKEN" "GitHub"
    check_key "OPENAI_API_KEY" "OpenAI"
    check_key "HUBSPOT_API_KEY" "HubSpot"
    check_key "ANTHROPIC_API_KEY" "Anthropic"
    check_key "GONG_ACCESS_KEY" "Gong"
else
    echo -e "\n⚠️ No .env file found. Copy from .env.example first:"
    echo "   cp .env.example .env"
fi

echo -e "\n💡 Remember: Features gracefully disable without keys"
echo "   No mocks needed - clean degradation instead"

