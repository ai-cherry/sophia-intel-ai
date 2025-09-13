#!/bin/bash

echo "🚀 Launching Voice Everywhere"
echo "============================="

# Start voice service
python3 voice/unified_voice_system.py --daemon &
VOICE_PID=$!

# Start web servers if needed
if [ "$1" = "--web" ]; then
    npm run dev &
    WEB_PID=$!
fi

echo ""
echo "✅ Voice Active on All Platforms!"
echo ""
echo "📱 Phone: Open https://$(hostname).local:3000/voice"
echo "💻 Laptop: Use 'vc' in terminal"
echo "🔨 Builder: Voice button in UI"
echo "🧠 Sophia: Voice mode enabled"
echo ""
echo "Try saying:"
echo "  • 'Create a React login component'"
echo "  • 'Git commit fixed authentication'"
echo "  • 'Run all tests'"
echo "  • 'Make this function async'"
echo ""
echo "Press Ctrl+C to stop"

wait $VOICE_PID
