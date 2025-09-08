Title: Fully boot Sophia + Artemis sidecar, MCP, UI, voice, LLM, and validate end-to-end (macOS)

Context
- Repos:
  - Sophia (product): ~/sophia-intel-ai (this repo)
  - Artemis (sidecar): ~/artemis-cli (SSH)
- Secrets live in ~/.config/artemis/env
- Goals: one-button startup, full MCP, Sophia UI, voice, chat, and quick verification.

Steps
1) Verify SSH and remotes
   - ssh -T git@github.com (should say “successfully authenticated”)
   - cd ~/sophia-intel-ai && git remote -v
   - If Artemis isn’t present: make artemis.sidecar-setup (clones to ~/artemis-cli)

2) Verify secrets and environment
   - Ensure ~/.config/artemis/env contains (one per line):
     - OPENAI_API_KEY, ANTHROPIC_API_KEY, PORTKEY_API_KEY, ELEVENLABS_API_KEY
     - JWT_SECRET, POSTGRES_URL, REDIS_URL, WEAVIATE_URL
   - cd ~/sophia-intel-ai && source scripts/env.sh --quiet && make keys-check

3) Start core services
   - In terminal A: make dev-all   # starts Redis, Weaviate, MCP, and Next.js UI
   - In terminal B: make api-dev   # starts FastAPI on http://localhost:8003

4) Open the UI and test chat
   - Dashboard: http://localhost:3000/dashboard
   - Chat:      http://localhost:3000/chat

5) Test voice
   - TTS: POST http://localhost:8003/api/voice/synthesize (JSON: {"text":"Hello","system":"sophia","persona":"smart"})
   - STT: POST http://localhost:8003/api/voice/transcribe (audio_base64, audio_format)

6) MCP verification
   - Memory:  curl -sf http://localhost:8081/health
   - FS (Sophia): curl -sf http://localhost:8082/health
   - Git:     curl -sf http://localhost:8084/health
   - Optional Artemis FS: docker compose -f docker-compose.dev.yml --profile artemis up -d mcp-filesystem-artemis (requires ARTEMIS_PATH)

7) Fix common issues
   - UI CORS errors: export CORS_ORIGINS=http://localhost:3000, restart API
   - Missing voice: set ELEVENLABS_API_KEY (TTS) and OPENAI_API_KEY (STT)
   - Missing Artemis: make artemis.sidecar-setup

Where to go after startup
- Sophia Dashboard: http://localhost:3000/dashboard
- Sophia Chat: http://localhost:3000/chat
- API Health: http://localhost:8003/health and /health/integrations
