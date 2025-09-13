#!/bin/bash

# Link master .env to all tools and CLIs

echo "🔗 Linking Master .env to All Tools"
echo "===================================="
echo ""

MASTER_ENV="$HOME/sophia-intel-ai/.env.master"

# Backup existing files
echo "Creating backups..."
[ -f ~/.config/sophia/env ] && cp ~/.config/sophia/env ~/.config/sophia/env.backup
[ -f ~/sophia-intel-ai/.env ] && cp ~/sophia-intel-ai/.env ~/sophia-intel-ai/.env.backup

# Create symlinks
echo "Creating symlinks..."
ln -sf "$MASTER_ENV" ~/sophia-intel-ai/.env
ln -sf "$MASTER_ENV" ~/.config/sophia/env

echo "✅ Linked .env.master to:"
echo "  - ~/sophia-intel-ai/.env"
echo "  - ~/.config/sophia/env"
echo ""

# Add to .zshrc to source on startup
if ! grep -q "source.*\.env\.master" ~/.zshrc; then
    echo "" >> ~/.zshrc
    echo "# Load master environment" >> ~/.zshrc
    echo "[ -f ~/sophia-intel-ai/.env.master ] && source ~/sophia-intel-ai/.env.master" >> ~/.zshrc
    echo "✅ Added to .zshrc for automatic loading"
fi

# Export for current session
source "$MASTER_ENV"

echo ""
echo "✅ Master environment active!"
echo ""
echo "Available API Keys:"
echo "  • Portkey: ${PORTKEY_API_KEY:0:20}..."
echo "  • OpenAI: ${OPENAI_API_KEY:0:20}..."
echo "  • Anthropic: ${ANTHROPIC_API_KEY:0:20}..."
echo "  • OpenRouter: ${OPENROUTER_API_KEY:0:20}..."
echo "  • Together: ${TOGETHER_API_KEY:0:20}..."
echo "  • Groq: ${GROQ_API_KEY:0:20}..."
echo "  • Mistral: ${MISTRAL_API_KEY:0:20}..."
echo "  • Perplexity: ${PERPLEXITY_API_KEY:0:20}..."
echo ""
echo "All tools now share the same environment!"