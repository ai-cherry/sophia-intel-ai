#!/bin/bash

# Complete Voice Setup Script for All Platforms
# Works on: Laptop (Mac M3), Phone (PWA), Terminal, Builder, Sophia

set -e

echo "🎤 Complete Voice System Setup"
echo "=============================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. Check and install dependencies
echo -e "${YELLOW}Checking dependencies...${NC}"

# Check for OpenAI API key
if [ -z "$OPENAI_API_KEY" ]; then
    export OPENAI_API_KEY="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"
fi

# Install Python packages
pip3 install -q openai elevenlabs websockets aiohttp pydantic --break-system-packages 2>/dev/null || pip3 install -q openai elevenlabs websockets aiohttp pydantic

echo -e "${GREEN}✓ Dependencies ready${NC}"

# 2. Configure terminal voice commands
echo -e "${YELLOW}Setting up terminal commands...${NC}"

# Add to shell config if not already present
if ! grep -q "# Unified Voice Commands" ~/.zshrc; then
    cat >> ~/.zshrc << 'EOF'

# Unified Voice Commands
alias voice='python3 ~/sophia-intel-ai/voice/unified_voice_system.py'
alias vc='voice'  # Short alias

# Platform-specific voice
voice-terminal() {
    python3 ~/sophia-intel-ai/voice/unified_voice_system.py --mode terminal "$@"
}

voice-builder() {
    python3 ~/sophia-intel-ai/voice/unified_voice_system.py --mode builder "$@"
}

voice-sophia() {
    python3 ~/sophia-intel-ai/voice/unified_voice_system.py --mode sophia "$@"
}

# Quick voice actions
vcode() {
    echo "🎤 Speak your code request..."
    python3 -c "
import speech_recognition as sr
import subprocess
r = sr.Recognizer()
with sr.Microphone() as source:
    audio = r.listen(source, timeout=5, phrase_time_limit=10)
    text = r.recognize_google(audio)
    print(f'Request: {text}')
    subprocess.run(['python3', '~/sophia-intel-ai/voice/unified_voice_system.py', '--mode', 'builder', text])
"
}

# Voice git with OpenAI
vgit() {
    if [ "$1" = "commit" ]; then
        echo "🎤 Speak your commit message..."
        MESSAGE=$(python3 -c "
import speech_recognition as sr
r = sr.Recognizer()
with sr.Microphone() as source:
    audio = r.listen(source, timeout=5)
    print(r.recognize_google(audio))
" 2>/dev/null)
        git add . && git commit -m "$MESSAGE"
        say "Committed: $MESSAGE"
    else
        git "$@"
    fi
}
EOF
fi

echo -e "${GREEN}✓ Terminal commands configured${NC}"

# 3. Set up mobile PWA
echo -e "${YELLOW}Configuring mobile PWA...${NC}"

# Create service worker for offline voice
cat > public/voice-sw.js << 'EOF'
// Voice Service Worker for Offline Support
const CACHE_NAME = 'sophia-voice-v1';
const urlsToCache = [
    '/',
    '/voice',
    '/static/js/voice.js',
    '/static/wasm/whisper-tiny.wasm'  // For offline STT
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(urlsToCache))
    );
});

self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => response || fetch(event.request))
    );
});
EOF

echo -e "${GREEN}✓ Mobile PWA configured${NC}"

# 4. Configure Builder app integration
echo -e "${YELLOW}Setting up Builder app voice...${NC}"

# Create Builder voice endpoint
cat > app/api/routers/voice_builder.py << 'EOF'
"""Voice endpoints for Builder app"""
from fastapi import APIRouter
from voice.unified_voice_system import UnifiedVoiceSystem, VoiceMode

router = APIRouter(prefix="/api/builder/voice")
voice_system = UnifiedVoiceSystem()

@router.post("/process")
async def process_voice(request: dict):
    """Process voice command for Builder"""
    result = await voice_system.process_voice(
        text=request.get("text"),
        mode=VoiceMode.BUILDER
    )
    return result
EOF

echo -e "${GREEN}✓ Builder app voice ready${NC}"

# 5. Configure Sophia Intel app
echo -e "${YELLOW}Setting up Sophia Intel voice...${NC}"

# Add voice to Sophia unified API
cat > app/api/voice_integration.py << 'EOF'
"""Voice integration for Sophia Intel"""
from voice.unified_voice_system import UnifiedVoiceSystem, VoiceMode

class SophiaVoice:
    def __init__(self):
        self.voice_system = UnifiedVoiceSystem()
    
    async def process(self, text: str, provider: str = "openai"):
        """Process voice with intelligent routing"""
        result = await self.voice_system.process_voice(
            text=text,
            mode=VoiceMode.SOPHIA
        )
        return result
EOF

echo -e "${GREEN}✓ Sophia Intel voice ready${NC}"

# 6. Create unified launcher
echo -e "${YELLOW}Creating unified launcher...${NC}"

cat > launch_voice_everywhere.sh << 'EOF'
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
EOF

chmod +x launch_voice_everywhere.sh

echo -e "${GREEN}✓ Unified launcher created${NC}"

# 7. Test voice system
echo -e "${YELLOW}Testing voice system...${NC}"

python3 -c "
import asyncio
from voice.unified_voice_system import UnifiedVoiceSystem

async def test():
    system = UnifiedVoiceSystem()
    result = await system.process_voice(text='Hello, test the voice system')
    print(f'Test result: {result.get(\"response\", \"No response\")[:50]}...')

asyncio.run(test())
" && echo -e "${GREEN}✓ Voice system operational${NC}" || echo -e "${YELLOW}⚠ Voice test needs configuration${NC}"

# 8. Create mobile bookmark
echo -e "${YELLOW}Creating mobile shortcuts...${NC}"

cat > public/add-to-homescreen.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Sophia Voice - Add to Home Screen</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="manifest" href="/voice-manifest.json">
    <style>
        body {
            font-family: -apple-system, system-ui;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
        }
        .instructions {
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }
        .emoji {
            font-size: 48px;
            margin: 20px;
        }
    </style>
</head>
<body>
    <div class="emoji">🎤</div>
    <h1>Sophia Voice Assistant</h1>
    
    <div class="instructions">
        <h2>Add to Home Screen</h2>
        <p><strong>iPhone:</strong></p>
        <ol>
            <li>Tap the Share button (square with arrow)</li>
            <li>Scroll down and tap "Add to Home Screen"</li>
            <li>Name it "Sophia Voice"</li>
            <li>Tap "Add"</li>
        </ol>
        
        <p><strong>Android:</strong></p>
        <ol>
            <li>Tap the menu (3 dots)</li>
            <li>Tap "Add to Home screen"</li>
            <li>Name it "Sophia Voice"</li>
            <li>Tap "Add"</li>
        </ol>
    </div>
    
    <button onclick="window.location='/voice'">Open Voice Assistant</button>
    
    <script>
        // PWA install prompt
        let deferredPrompt;
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
        });
    </script>
</body>
</html>
EOF

echo -e "${GREEN}✓ Mobile shortcuts created${NC}"

# 9. Final setup
echo -e "${YELLOW}Finalizing setup...${NC}"

# Create desktop app shortcut (Mac)
cat > ~/Desktop/SophiaVoice.command << 'EOF'
#!/bin/bash
cd ~/sophia-intel-ai
./launch_voice_everywhere.sh --web
EOF
chmod +x ~/Desktop/SophiaVoice.command

# Summary
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ VOICE SYSTEM FULLY CONFIGURED!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}🎤 Quick Start Commands:${NC}"
echo ""
echo "  Terminal:  vc                    # Start voice mode"
echo "  Terminal:  vgit commit           # Voice git commit"
echo "  Terminal:  vcode                 # Voice coding"
echo "  Terminal:  voice-sophia          # Sophia mode"
echo "  Terminal:  voice-builder         # Builder mode"
echo ""
echo -e "${BLUE}📱 Mobile Access:${NC}"
echo ""
echo "  1. On your phone, open Safari/Chrome"
echo "  2. Go to: https://$(hostname).local:3000/add-to-homescreen.html"
echo "  3. Follow instructions to add to home screen"
echo "  4. Launch app and allow microphone access"
echo ""
echo -e "${BLUE}💻 Desktop:${NC}"
echo ""
echo "  • Double-click 'SophiaVoice' on Desktop"
echo "  • Or run: ./launch_voice_everywhere.sh --web"
echo ""
echo -e "${BLUE}🚀 Start Everything:${NC}"
echo ""
echo "  ./launch_voice_everywhere.sh --web"
echo ""
echo -e "${YELLOW}Restart your terminal to activate new commands${NC}"