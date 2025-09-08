**Phase 2: Routing, Budgets, and Reliability Design**

Objective
- Implement a production-grade model router that chooses the best model per task, applies budget and latency policies, handles provider errors gracefully, and emits telemetry. All calls go through Portkey VKs.

Guiding Principles
- Performance-first: meet p95 latency targets while maximizing quality.
- Safety and reliability: circuit breakers and cooldowns on provider errors.
- Cost awareness: daily soft/hard caps per VK with auto-downgrades.
- Observability: emit structured telemetry for UI dashboards.

Key Components
- Router (`agno_core/adapters/router.py`)
  - Inputs: `TaskSpec(task_type, urgency_ms, context_tokens, creative, strict_quality)`.
  - Outputs: `SelectedRoute(category, primary_spec, fallback_specs)` where specs are Portkey call-spec dicts.
  - Decision rules:
    - Urgent (<= 500ms) → `fast_operations` (e.g., Grok Code Fast).
    - Large context (>= 500k tokens) → `advanced_context` (e.g., Gemini 2.5 Flash).
    - Creative/ideation → `specialized.maverick` (Llama Maverick).
    - Code: `coding` (DeepSeek) with `secondary` fallback (Qwen).
    - Analysis/architecture/strict quality → `reasoning` with configured `fallback_chain`.
    - Default → `general`.
  - Fallbacks from `config/models.yaml`:
    - Reasoning: `fallback_chain`.
    - Coding: `secondary`.
    - General: `fallback`.

- Budgets (`agno_core/adapters/budget.py`)
  - Loads `config/budgets.yaml` and exposes per-VK budgets.
  - Tracks spend via an in-memory counter (pluggable storage in Phase 4).
  - API: `BudgetManager.check_and_reserve(vk_env, estimated_cost)` returns decision (`allow`, `soft_cap`, `blocked`).
  - Soft-cap behavior: router will prefer a cheaper fallback. Hard-cap: block and produce alert event.

- Circuit Breaker (`agno_core/adapters/circuit_breaker.py`)
  - Tracks error rates and opens a circuit per VK when encountering consecutive provider errors (e.g., 429, 5xx).
  - Config: `cooldown_seconds_on_error` from `config/budgets.yaml` (escalation policy section).
  - API: `is_open(vk_env)`, `on_success(vk_env)`, `on_error(vk_env)`.

- Telemetry (`agno_core/adapters/telemetry.py`)
  - Emits structured events for routing decisions, fallbacks, budget outcomes, and errors.
  - Pluggable sink: for now, in-memory ring buffer + stdout logger. Later: send to `webui` or Prometheus exporters.
  - Event shape example:
    - `{"type":"route_decision","task":"code_generation","category":"coding","primary":"deepseek/...","vk":"PORTKEY_VK_DEEPSEEK","latency_target_ms":1500}`

Latency & Budget Targets
- Targets (`config/budgets.yaml`):
  - p95: fast 150ms; coding 1500ms; reasoning 2000ms; general 800ms; advanced_context 5000ms.
  - Budgets per VK (soft/hard caps in USD/day). Router consults before choosing.
- Escalation policy:
  - `attempts_before_escalation`: 2
  - `cooldown_seconds_on_error`: 120
  - On low-confidence or repeated failures, coordinator may escalate to premium (e.g., Opus) if budget allows.

Router Control Flow (pseudocode)
1. Classify task → select category/subkey.
2. Build primary Portkey spec via `ModelFactory`.
3. Estimate cost (heuristic: tokens × provider CPM map; refine later via telemetry).
4. Budgets: `check_and_reserve(vk, estimate)`:
   - allow → continue
   - soft_cap → prefer next fallback if available and suitable; else continue with warning
   - blocked → skip to fallback; if all blocked → error
5. Circuit breaker: if `is_open(vk)` → skip to fallback.
6. Return `SelectedRoute` with fallbacks (already filtered by budget/CB where possible). Telemetry event: `route_decision`.

Confidence and Escalation
- Primary self-evaluation rubric returns confidence ∈ [0,1]. If < threshold (e.g., 0.6) after N attempts → escalate.
- Optionally add evaluator agent in Phase 3 to validate outputs for critical tasks.

Testing Strategy
- Unit tests (no network): validate category selection, fallback ordering, budget and CB decisions for synthetic scenarios.
- Simulation: synthetic distributions of latencies and error rates to exercise downgrade/escalation logic.

Rollout
- Phase 2a: Implement budgets, CB, and telemetry scaffolding (this PR).
- Phase 2b: Wire router to use budgets/CB/telemetry and add cost estimator + dry-run simulator.
- Phase 2c: Expose telemetry in `webui` and Next.js UI; add toggles for budgets and escalation thresholds.

