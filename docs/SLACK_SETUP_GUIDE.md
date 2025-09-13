# Slack + Sophia Intel Integration Guide (For Slack Admin)

This guide explains exactly how to set up Sophia Intel in Slack for broad Business Intelligence access and personalized usage for two users: the CEO (you) and Tiffany York (CPO).

Use this as your checklist while you work through Slack’s App configuration and our Sophia stack.

---

## 1) Prerequisites (Admin)
- Slack workspace admin permissions
- API host for Sophia Intel (choose one):
  - Local: `http://localhost:8000`
  - Staging/Prod: `https://<api-host>`
- Secrets managed outside the repo, per AGENTS.md
  - Store in `<repo>/.env.master`
  - Required: `SLACK_SIGNING_SECRET`, `SLACK_BOT_TOKEN` (after install), `SLACK_CLIENT_ID`, `SLACK_CLIENT_SECRET`

## 2) Create the Slack App (Manifest)
1. Go to https://api.slack.com/apps → “Create New App” → “From an app manifest”.
2. Choose your workspace.
3. Paste the manifest from `docs/SLACK_APP_MANIFEST.yml`.
   - Replace `<API_HOST>` with your actual host (e.g., `localhost:8000` for local).
   - Click “Next” → “Create”.
4. In “Basic Information”, verify:
   - Bot user exists (Sophia), interactivity is enabled, events are configured, and slash commands are present.

## 3) Install the App to the Workspace
- Click “Install to Workspace” and approve the requested scopes.
- After install, Slack reveals the `Bot User OAuth Token` (starts with `xoxb-...`).
- Copy the following into `<repo>/.env.master`:
  - `SLACK_BOT_TOKEN=...`
  - `SLACK_SIGNING_SECRET=...` (from “Basic Information → App Credentials”)
  - `SLACK_CLIENT_ID=...` and `SLACK_CLIENT_SECRET=...`

## 4) Configure Slack in Sophia (Admin)
- Ensure the Sophia API loads the central env (already supported by the app):
  - No need to export a path; start services via `./sophia`.
- Start services (local example):
  - API: `python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
  - MCP FS (optional): `python3 -m uvicorn mcp.filesystem.server:app --port 8082`
- In the Sophia Intel UI (http://localhost:3000 or your host):
  - Go to Settings → Integrations → Slack.
  - Click “Test Connection”. It should show the Slack team, bot user, and health.

## 5) Invite Sophia to Channels (BI scope)
- Add @Sophia to the channels we’ll ingest & analyze:
  - Public/product BI: `#product`, `#roadmap`, `#design`, `#research`
  - Business BI: `#sales`, `#cs`, `#exec-brief`, `#ops`
  - Private channels as needed (invite @Sophia manually)
- Note: Slack only lets the bot read channels it’s a member of. Private channels require explicit invites.

## 6) Commands and Events (Verification)
- In any channel where @Sophia is a member, try:
  - `/sophia help` → Should respond with a help string.
  - `@Sophia summarize this channel` → Should post a threaded response or instruct you to DM.
- DM the bot 
  - Send: `Hi` or `pipeline health this week?` → Bot should respond.

## 7) Personalization for CEO and Tiffany (two test accounts)
- In the Sophia Intel UI:
  1. Add two users (CEO and Tiffany) and assign roles (Owner/CEO, CPO).
  2. In Integrations → Slack, click “Link Slack” for each user to start OAuth.
  3. Each user completes auth and lands back in the UI.
  4. Each user opens “Preferences”:
     - Domains of interest (CEO: Exec overview; Tiffany: Product & Research)
     - Notification cadence (daily summary or off)
     - Model routing preferences (CEO: high-quality; Tiffany: product-centric)
- Testing personalized bots:
  - CEO DMs @Sophia: `daily exec summary` → Should tailor to Exec channels.
  - Tiffany DMs @Sophia: `product risk scan` → Should focus on product/roadmap channels.

## 8) Optional: Slash Commands (Examples)
- `/bi pipeline` – Sales pipeline summary
- `/bi product risks` – Product risks from #product/#roadmap
- `/sophia-settings` – Opens a modal for personal preferences
- `/ingest channels all` – Admin-only, reindex Slack (use carefully)

## 9) Privacy, Security, and Retention
- The bot only reads channels it’s in.
- PII redaction is on by default in BI summaries.
- Retention defaults to 90 days for Slack-derived content (configurable).
- You can disable DM ingestion if desired (keeps @Sophia’s DMs private to the user).

## 10) Troubleshooting (Admin)
- App not responding?
  - Check API logs; ensure `SLACK_BOT_TOKEN` and `SLACK_SIGNING_SECRET` are set.
  - Hit: `GET /api/slack/health` (if available) or test “Test Connection” in the UI.
  - Verify request URLs in the Slack app (events, interactivity, commands) point to `<API_HOST>`.
- Bot not “seeing” a channel?
  - Ensure @Sophia is invited to that channel.
  - Private channels: @Sophia must be explicitly invited.
- Rate limits or timeouts?
  - Try your BI queries in smaller scope or during off-peak; the backend queues and retries automatically.

---

## Appendix A — Admin Customization (Our Tech Stack)
- Model routing
  - The system supports 17 documented models and policies. You can set a default (e.g., `free_tier`) for Slack chat, and override by role (e.g., CEO → Grok 4 for reasoning; coding → Qwen3 Coder).
  - Edit `config/user_models_config.yaml` or use the UI once available.
- Channel scopes
  - Use the dashboard to check which channels are connected. Remove or add channels any time by inviting/removing @Sophia.
- Schedules
  - Set daily or weekly summaries to post to `#exec-brief` or Tiffany’s DM.

## Appendix B — Personal Bot Tips
- DM @Sophia to keep personal explorations separate.
- Use `/sophia-settings` to adjust personal preferences and notification cadence.
- Use “Reply in Slack” from the UI chat to post results into a channel/thread.

---

## After Setup — AI‑Assisted Slack Audit (What We’ll Do Next)
Once the app is connected and the bot is present in the right channels, we will:

1. Run a Slack Audit Session in Sophia
   - In the Sophia Intel UI, open “Slack Audit”.
   - Start an interactive session with prompts like:
     - “Identify channel sprawl and stale channels in the last 90 days.”
     - “Group channels by business function and propose a clean structure.”
     - “Locate overlapping channels and propose merges or archiving.”
     - “Summarize recurring themes and propose a new taxonomy.”

2. Create a Cleanup Plan
   - Produce a concrete PRD-like document with:
     - Proposed channel taxonomy (Sales, CS, Product, Eng, Ops, Exec)
     - Archival list (inactive > 90 days)
     - Consolidation proposals (overlaps, duplicates)
     - Role- and team‑based default subscriptions

3. Execute Iteratively
   - Announce the plan in `#exec-brief`.
   - Apply changes gradually: rename/archive, set new conventions, update onboarding docs.
   - Re-run the Audit Session monthly to keep Slack tidy.

> Outcome: Cleaner, searchable Slack with clear ownership and streams aligned to BI needs, and safer defaults for privacy.

---

## Quick Reference (Admin)
- Slack App → Manifest: `docs/SLACK_APP_MANIFEST.yml`
- Env vars (store in `<repo>/.env.master`): `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`, `SLACK_CLIENT_ID`, `SLACK_CLIENT_SECRET`
- API endpoints:
  - Events: `POST /api/slack/webhook`
  - Interactivity: `POST /api/slack/interactivity`
  - Commands: `POST /api/slack/commands`
  - OAuth callback: `GET /api/slack/oauth/callback`
- Sophia Intel UI: Integrations → Slack → Test Connection
