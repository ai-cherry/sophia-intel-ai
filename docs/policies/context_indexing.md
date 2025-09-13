# Context & Indexing Policy

Purpose
- Centralize rules for attaching repository/business context to agents and for building/maintaining vector indexes.

Context Rules
- Respect domain scope on every task: `builder` may read/patch code paths; `sophia` may read business data paths only.
- Default attachment order: symbol search → targeted file reads → proposed patch; avoid whole‑repo dumps.
- Budgets (defaults): max 25 files or 150k chars per request; increase only with approval.

Indexing Rules
- Embeddings computed via the LLM gateway; vector DB runs with `vectorizer=none`.
- Inclusion: `**/*.{py,ts,tsx,md}`; Exclusion: `node_modules`, `build`, `.next`, `dist`, large binaries.
- Dedup: content hash + normalized path; update on rename; TTLs configurable.
- Namespaces: `builder:code:<env>` and `sophia:bi:<env>`.

Validation
- Indexers must read this policy (JSON at `config/context_policy.json`) and emit metrics on batch size, duration, and dedup ratio.

