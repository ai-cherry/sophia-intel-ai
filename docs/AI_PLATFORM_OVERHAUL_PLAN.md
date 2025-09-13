# Sophia + Sophia AI Platform Overhaul Plan

Status: Proposal (written only, no code changes)
Owner: Architecture & Platform Team
Last Updated: 2025-09-05

Purpose

- Deliver a comprehensive, modular, and scalable plan to clean up, upgrade, and enhance the AI platform across both Agent Factories:
  - Sophia: Enterprise Business Intelligence (pay-ready integrations, insights, reporting)
  - Sophia: High-performance coding and refactoring (engineer-focused)
- Standardize micro-swarms, memory/embeddings, prompts/personas, DevEx/CI/CD, security, governance, and observability.
- Establish dedicated Web Research Teams for both domains with fact-checking and citations.

Scope

- Architecture, orchestration, memory/embeddings, provider routing via Portkey, tools/integrations, prompts/personas, security, observability, CI/CD, rollout phases, and operational playbooks.
- No code changes in this document. Implementation will proceed via PRs after approval.

Non-Goals

- Replacing core frameworks wholesale
- Vendor lock-in to any single model provider
- Introducing experimental features that are not production-proven

---

Executive Summary

- Dual-Orchestrator Strategy:
  - Sophia = Enterprise BI/pay-ready domain: integrations, insights, and governance-first.
  - Sophia = Coding excellence domain: planning, implementation, review, security, and performance.
- Shared foundations:
  - Unified orchestration façade (start/run swarms, memory, telemetry, budgets)
  - Tiered memory + retrieval (cache + vector + optional graph)
  - Provider routing via Portkey Virtual Keys, staged model selection (fast vs quality)
  - Standardized micro-swarm roles & success criteria; prompts/personas library
  - Strong security posture (PyJWT, secrets isolation, audit) and observability
- Phased rollout (0→4) prioritizes stability → shared architecture → domain accelerators → research teams.

---

Architecture Overview

High-Level (Dual Orchestrators on Shared Foundations)

    ┌───────────────────────────────────────────────────────────────┐
    │                        Shared Foundations                     │
    │  - Unified Orchestration Façade (APIs, budgets, telemetry)    │
    │  - Memory & Retrieval: Cache + Vector (Weaviate/Qdrant) + G*  │
    │  - Tool Adapter Layer (httpx, retries, typed errors)          │
    │  - Portkey Routing (Virtual Keys, policies, caching)          │
    │  - Security: AuthN/Z, PyJWT, rate-limit, circuit breakers     │
    │  - Observability: OTEL tracing, metrics, logs                 │
    └───────────────────────────────────────────────────────────────┘
           ▲                                         ▲
           │                                         │
    ┌──────┴───────────┐                     ┌───────┴──────────┐
    │   Sophia Factory │                     │  Sophia Factory │
    │  (BI / Pay-Ready)│                     │   (Coding)       │
    │  - BI Swarms     │                     │ - Coding Swarms  │
    │  - Integrations  │                     │ - Refactors/PRs  │
    │  - Reporting     │                     │ - Security/Perf  │
    └──────────────────┘                     └───────────────────┘
           ▲                                         ▲
           │                                         │
    ┌──────┴───────────┐                     ┌───────┴──────────┐
    │ Web Research Team│                     │ Web Research Team│
    │ (Sophia)         │                     │  (Sophia)       │
    │ Deep-search,     │                     │ Tech scouting,   │
    │ fact-check, cite │                     │ CVE tracking     │
    └──────────────────┘                     └───────────────────┘

Notes

- G\* (Graph retrieval) optional for entity reasoning; add as a phase after baseline.
- All providers accessed via Portkey Virtual Keys (VKs); no raw provider keys in code.

---

Standardized Micro-Swarm Pattern

- Modes
  - collaborate: peers contribute artifacts; merge policy determines final output
  - coordinate: lead agent orchestrates delegates; state machine governs handoffs
- Roles (canonical examples)
  - Planner: objectives → plan → acceptance criteria → risks
  - Implementer: codemods/new code/data transforms
  - Reviewer: lint/type/tests; security; policy conformance
  - Analyst (Sophia): BI correlation, KPI deltas, anomaly detection
  - Publisher (Sophia): formatting, dashboards, delivery
  - Security Auditor: bandit/semgrep, secrets scan, policy checks
  - Performance Engineer: profiling, cost/latency tuning
  - Researcher: evidence gathering with citations and confidence
- Success criteria per swarm
  - Output contract (schema), SLOs (latency/cost), acceptance tests, citations (if applicable), and rollback plan.

---

Memory & Embeddings Strategy

- Tiered Memory
  - Short-term cache: ephemeral conversation/task memory (e.g., Redis) to reduce token window cost
  - Vector memory: semantic long-term memory (Weaviate or Qdrant)
  - Optional graph layer: entity/relationship reasoning for complex workflows
- Embedding Choices
  - Default: text-embedding-3-small via Portkey with caching/batching
  - Alternatives: Cohere/Nomic/Voyage etc. via VK for code or multilingual tasks
- Retrieval Quality
  - Chunking: semantic splitting (heading-aware), deduplication, adaptive chunk sizes
  - Evaluation: precision@k, groundedness, hallucination rate reduction, cost/token per answer
  - Caching: query/result cache with TTL; warm caches for recurring BI questions

---

Provider Strategy via Portkey (Staged Diversity)

- Default routing
  - fast_tier: low-latency/low-cost models for routine steps (drafting, routing, summaries)
  - quality_tier: higher-accuracy models for critical or ambiguous steps (planning, safety, finalization)
- Escalation rules
  - Ambiguity score or confidence < threshold (e.g., <0.7) → escalate to quality_tier
  - High-stakes tasks (security, compliance, production config) → quality-only
  - Budget caps per step; if exceeded, delegate to cache or require approval
- Portkey VK Mapping (provided)
  - DEEPSEEK-VK: deepseek-vk-24102f
  - OPENAI-VK: openai-vk-190a60
  - ANTHROPIC-VK: anthropic-vk-b42804
  - OPENROUTER-VK: vkj-openrouter-cc4151
  - PERPLEXITY-VK: perplexity-vk-56c172
  - GROQ-VK: groq-vk-6b9b52
  - MISTRAL-VK: mistral-vk-f92861
  - MILVUS-VK: milvus-vk-34fa02
  - XAI-VK: xai-vk-e65d0f
  - TOGETHER-VK: together-ai-670469
  - QDRANT-VK: qdrant-vk-d2b62a
  - COHERE-VK: cohere-vk-496fa9
  - GEMINI-VK: gemini-vk-3d6108
  - HUGGINGFACE-VK: huggingface-vk-28240e
- Examples (conceptual)
  - Sophia: fast_tier = GROQ/Mistral/OpenRouter-cheap; quality_tier = OpenAI/Anthropic
  - Sophia: fast_tier = OpenRouter-cheap/Mistral; quality_tier = Anthropic/OpenAI/Gemini
- Observability
  - Capture model attribution, latency, token cost, and success per step
  - A/B toggles to experiment with tier assignments

---

Tooling & Integrations

- Tool Adapter Layer
  - httpx with retry/backoff, typed exceptions, request/response logging (PII-safe)
  - Standard adapter interface: config, auth (via VK), timeouts, rate limits, and policies
- Sophia (BI/Pay-Ready)
  - OAuth-first where available (Slack, Linear, Notion, Gong, etc.)
  - Ingestion pattern: source → normalize → embed → index → cache → publish
  - Publisher outputs: Slack posts, Notion pages, email/CSV, dashboards
- Sophia (Coding)
  - Code search (rg/AST), codemods, lint/type/test automation, PR generation
  - Security scans (bandit/semgrep), dependency audits (safety/pip-audit)

---

Web Research Teams (Both Factories)

- Providers
  - Search/QA: Perplexity, Tavily, Exa; optionally Brave; scraping via Apify/Zenrows
- Requirements
  - Citations, timestamps, confidence ratings
  - Dual-agent verification: fact-checker & contradiction detector
  - Memory: cache results to reduce cost; update vector store with curated summaries
- Output Types
  - Sophia: market intel, competitive analyses, KPI context briefs
  - Sophia: API changes, framework deltas, CVEs, migration notes, sample configs

---

Prompts & Personas

- Persona Library
  - Sophia: Strategist (exec brief), Analyst (deep BI), Compliance (governance), Integrations Sherpa (setup)
  - Sophia: Architect (RFC tradeoffs), Implementer (code), Reviewer (quality/security), Perf Engineer (profile)
- Prompt Patterns
  - Planning-first (objectives, constraints, tests, risks)
  - Chain-of-verification: self-checks + unit-test stubs or examples
  - Output contracts: JSON schemas where possible; markdown with sections otherwise
  - Style parameters: concise/verbose modes; code/comment balance

---

Security & Governance

- AuthN/Z and sessions
  - PyJWT in place; consistent exception handling; standardized token verification
- Secrets & Providers
  - All providers via Portkey VK; no raw provider keys in code/CI; rotate VKs periodically
- Egress Control
  - Allow-listed hostnames; request signing; per-tool rate limits; circuit breakers; retries with backoff
- Audit
  - Agent action logs, tool invocation traces, model attribution, final rationale notes

---

Observability, Cost, Performance

- Metrics
  - token_cost, latency_p50/p95, success_rate, handoff_count, retry_count, cache_hit
- Tracing
  - OTEL spans across orchestrator → tools → memory; unique run IDs; link to PRs or BI reports
- Budgets & Quotas
  - Per-agent/per-swarm token caps; escalation requires approval; budget alarms at 80/90/100%
- Caching & Batching
  - Embedding batchers; response caches; cost-aware fallbacks

---

CI/CD & Quality Gates

- Pre-commit
  - Black/isort/ruff; mypy; yaml/json/toml checks; detect-secrets baseline; safety scan; bandit/semgrep
  - Stage-by-stage enforcement (formatters → linters → security) to reduce friction
- CI Pipelines
  - uv lockfile caching; unit/integration tests; coverage gates; image lint/vuln scan; artifact retention
- PR Policy
  - Small PRs; linked ADRs; green checks required; no direct pushes to main; rollback instructions included

---

Phased Rollout (Detailed)

Phase 0 – Stabilize & Baseline (1–2 weeks)

- Dependency hygiene confirmed with uv lockfiles
- Pre-commit suite green baseline; detect-secrets baseline added
- pip-audit/safety scan in CI with policy gate
- Portkey VK enforced; configs linted for secret usage
  Acceptance Criteria: CI green; audits clean; no raw provider keys; logs/traces present in non-prod

Phase 1 – Orchestration & Memory Unification (2 weeks)

- Unified façade for swarms (start/run, budgets, telemetry)
- Tiered memory: cache + vector; retrieval improvements; chunking standards
- Tool adapters unified with retries/errors
  Acceptance Criteria: Both factories invoke shared façade and memory; retrieval metrics improved vs baseline

Phase 2 – Sophia BI/Pay-Ready (2–3 weeks)

- OAuth upgrades; ingestion → normalize → embed → index → publish pattern
- BI swarms: Ingestor, Summarizer, Analyst, Publisher with SLOs
- Governance: PII minimization, auditability, environment segmentation
  Acceptance Criteria: End-to-end BI flows for target integrations with citations, dashboards, budget controls

Phase 3 – Sophia Coding Factory (2–3 weeks)

- Coding swarms: Planner, Implementer, Reviewer, Security, Perf, Migrator
- PR automation; refactor codemods; tests; coverage gates; rollback playbooks
  Acceptance Criteria: Multi-file refactor PRs with passing checks and measurable reduction in manual fixes

Phase 4 – Web Research Teams (1–2 weeks)

- Providers wired via VK; fact-check and contradiction detection dual-agent
- Caching; confidence scores; outputs for BI and coding tracks
  Acceptance Criteria: Research briefs with citations; reduced latency/cost via caching; confidence ≥ threshold

---

Red Team Swarm (Added)

- Purpose
  - Random spot-checks for hallucinations, data misuse, risky operations across outputs
  - Feed findings into training signals: prompt tuning, policy updates, escalation thresholds
- Operation
  - Sample recent outputs daily/weekly by category; rate for groundedness, compliance, safety
  - Maintain a “risk registry” with remediation actions and owner
- Metrics
  - Hallucination rate trend, policy violation counts, mean time to remediation

---

Staged Provider Diversity (Added)

- Two-tier policy via Portkey
  - fast_tier: default low-cost/low-latency models for drafts, routing, summaries
  - quality_tier: high-accuracy models for planning, final answers, safety-critical decisions
- Thresholds & Controls
  - Confidence/ambiguity threshold; high-stakes tags; budget caps; A/B experiments
- VKs (for quick reference)
  - DeepSeek: deepseek-vk-24102f | OpenAI: openai-vk-190a60 | Anthropic: anthropic-vk-b42804
  - OpenRouter: vkj-openrouter-cc4151 | Perplexity: perplexity-vk-56c172 | Groq: groq-vk-6b9b52
  - Mistral: mistral-vk-f92861 | Milvus: milvus-vk-34fa02 | xAI: xai-vk-e65d0f
  - Together: together-ai-670469 | Qdrant: qdrant-vk-d2b62a | Cohere: cohere-vk-496fa9
  - Gemini: gemini-vk-3d6108 | HuggingFace: huggingface-vk-28240e

---

Risks & Mitigations

- Tool/API changes → Abstraction via adapters; provider fallbacks; feature flags
- Prompt/persona drift → Versioned prompt library; A/B validation; golden tests
- Data governance drift → Allow-listing; audit; retention policies; periodic compliance checks
- Dev friction → Gradual pre-commit enforcement; autofixes; clear docs; fast CI feedback

---

Operational Playbook (Highlights)

- Incident response: on-call runbook; quick disable switches for risky tools; budget kill-switches
- Cost governance: dashboards; weekly cost review; auto alerts; per-swarm budgets
- Secrets hygiene: rotate VKs; no raw keys; env-var mapping by environment; periodic audits
- Performance: profiling toolkit; token usage monitoring; cache warmers for hotspots

---

Approval & Next Steps

- Review this plan; adjust timelines and acceptance criteria as needed
- Upon approval, implementation proceeds by phases via small PRs
- Each PR must include tests, docs updates, and evidence of meeting acceptance criteria
