You are advising on Phase 2: Portkey routing, fallbacks, and budget/latency policy for Sophia’s Agno + Portkey + MCP system.

Context
- Models and VKs are configured in `config/models.yaml` using the user’s performance-first preferences (Grok Code Fast, ChatGPT-5 → Opus 4.1 → Sonoma Sky Alpha, Gemini 2.5 Flash, DeepSeek + Qwen, Grok-4 + GPT-4.1 mini, Llama-4 Scout/Maverick).
- Environment variables live in `~/.config/artemis/env` and are loaded via `scripts/env.sh`. No secrets are committed.
- Phase 1 is complete: health checks for MCP (8081–8086), Redis, Postgres; env presence; model factory and call-spec builder.

Objective
Design `agno_core/adapters/router.py` logic and budgets to:
- Select optimal model per task under strict latency/quality targets.
- Apply soft/hard budgets per VK with automatic downgrade/escalation.
- Use circuit breakers and cooldowns for provider errors.
- Output Portkey call specs (no direct provider clients).
- Support coordinator-driven escalations on low-confidence outcomes.

Decisions Needed
1) Escalation thresholds: attempts before escalating to “premium”; cooldowns for 429/5xx.
2) Budget policy: daily caps per VK; soft-cap behavior (downgrade vs. queue); hard-cap block + alert.
3) Confidence signals: self-eval rubric vs. evaluator agent vs. heuristic (e.g., hallucination risk) for triggering escalation.
4) Multi-VK preference: tie-breakers when several VKs can serve a provider/model (latency history vs. cost per 1k tokens).
5) Context policy: auto-route to Gemini 2.5 Flash for ≥500k tokens vs. semantic chunking + standard models.

Constraints and Integrations
- All LLM traffic routes through Portkey VKs; AIML API support can be added via a separate adapter behind a feature flag or Portkey passthrough if available.
- Inter-repo boundaries per AGENTS.md: no cross-imports with Artemis; MCP + HTTP only.
- AI voice (TTS) runs as a tool integration (e.g., ElevenLabs) invoked by agents; keys remain outside repo.

Deliverables to Specify
- Router API shape (TaskSpec inputs; SelectedRoute outputs with primary + fallbacks).
- Concrete p95 latency targets: fast 150ms; coding 1500ms; reasoning 2000ms; general 800ms; advanced_context 5000ms.
- Escalation policy: attempts_before_escalation, cooldown_seconds_on_error.
- Budget rules in `config/budgets.yaml` and how alerts surface in UI.
- Example routing rules for urgent, code_generation, large_context, creative, and analysis tasks.
- Dry-run simulation strategy (no network) using synthetic latencies and error distributions.

Please propose:
- The exact routing rules and thresholds.
- Confidence evaluation method and triggers.
- A fallback ordering for each category.
- How to expose telemetry (decisions, latencies, budget state) to the web UI.

