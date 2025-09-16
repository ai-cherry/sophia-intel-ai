# Naming Conventions and Anti‑Duplication Guide

This document standardizes names and structure across the Sophia Intel repository to prevent drift and duplication.

## High‑Level
- One canonical API entry point: `app/api/main.py`
- One unified dashboard UI served from the same app: `GET /dashboard` (file: `app/ui/dashboard.html`)
- All new UI surfaces must integrate into `/dashboard` and use `/static` for assets.

## Modules & Routers
- Routers live under `app/api/routers/` and use snake_case file names.
- Each router declares either:
  - A relative prefix (e.g., `APIRouter(prefix="/chat")`) and is included in `main.py` under `/api`, or
  - A full `/api/...` prefix and is included without extra prefix.
- The router instance must be named `router`.
- Include routers once in `main.py` — never under multiple prefixes.

## Endpoints
- Use `/api/<domain>/...` structure for JSON APIs.
- Health endpoints live either under domain health routers or `/health` for service health; metrics are at `/metrics`.
- For SSE, use `/api/<domain>/stream` with `text/event-stream` content type.

## UI
- Unified dashboard: `app/ui/dashboard.html` (tabs for Chat, Models, Agents, Swarms, Observability, Integrations, Brain Training).
- Frontend assets under `app/static/` only.
- Do not add new UI files under other directories.

## Integrations
- Integration routers and clients should live under `app/api/routers/<integration>.py` and `app/integrations/<integration>_*.py`.
- Prefer “optimized_client” or “_client.py” suffixes for integration clients.

## Tests
- Integration tests live under `tests/integration/<domain>/`.
- Unit tests live under `tests/unit/<domain>/`.
- Legacy root‑level `test_*.py` files are ignored by default; do not add new tests at repo root.

## Anti‑Duplication Rules
- No additional hub templates (e.g., `hub.html`) or duplicate dashboards.
- No duplicate chat frontends (e.g., old `/chat/completions` UI). Chat must go through `/api/chat/query` or `/api/chat/stream`.
- Before adding a new router or UI, search for existing patterns:
  - `rg -n "APIRouter\(|/api/" app/api/routers`
  - `rg -n "dashboard|brain|ingest|upload" app/`
- Use `scripts/check_duplicates.py` before commit.

## Configuration & RBAC
- Use environment values loaded via `app/core/env.load_env_once()`.
- Write operations on Models/Factory are guarded by `ADMIN_API_KEY` via `X-Admin-Key` header (dev open when unset).

By adhering to these conventions, we keep the codebase consistent and avoid fragmentation.
