# Integration Testing Guide

This repo centralizes live integration tests under `tests/integration/` and provides simple smoke tools in `tools/`.

## Structure
- `tests/integration/slack/` — Slack pytest tests
- `tests/integration/microsoft/` — Microsoft Graph pytest smoke
- `tests/integration/gong/` — Gong pytest smoke
- `tests/integration/conftest.py` — Loads `.env.local` automatically when present
- `tools/slack/smoke.py` — Manual Slack smoke (auth.test, channels, optional post)
- `tools/microsoft/smoke.py` — Manual Microsoft smoke (users, groups/teams, drive root)

## Running
- Install test deps:
  - `pip install -e .[test]`
- Ensure live credentials are in `.env.local` (gitignored)
- Run all integration tests:
  - `pytest -k integration -q`
- Target a provider:
  - `pytest tests/integration/slack -q`
  - `pytest tests/integration/microsoft -q`
  - `pytest tests/integration/gong -q`

## Environment Variables

### Slack
- **Required**: `SLACK_BOT_TOKEN` (starts with xoxb-)
- **Webhook tests**: `SLACK_SIGNING_SECRET`
- **Optional**: `SLACK_USER_TOKEN`, `SLACK_APP_TOKEN`
- **Test posting**: `SLACK_TEST_CHANNEL` (channel ID) or `SLACK_TEST_CHANNEL_NAME` (channel name)

### Microsoft Graph
- **Required**: `MS_TENANT_ID|MICROSOFT_TENANT_ID`, `MS_CLIENT_ID|MICROSOFT_CLIENT_ID`
- **Authentication** (choose one):
  - **Client Secret**: `MS_CLIENT_SECRET|MICROSOFT_SECRET_KEY` (use secret VALUE, not ID)
  - **Certificate**: `MICROSOFT_CERTIFICATE_ID` + `MICROSOFT_SIGNING_CERTIFICATE` or `MICROSOFT_SIGNING_CERTIFICATE_BASE64`

**Certificate Setup Tips:**
- Use `MICROSOFT_SIGNING_CERTIFICATE_BASE64` to avoid multiline .env parsing issues
- Encode your PEM certificate: `base64 -i mycert.pem | tr -d '\n' > cert.b64`
- Required Azure permissions: User.Read.All, Group.Read.All, Files.Read.All (Application permissions with admin consent)

### Gong
- **Required**: `GONG_ACCESS_KEY`, `GONG_CLIENT_SECRET`

## Notes
- Tests skip gracefully when required env vars are missing.
- Smoke tools provide quick manual verification but CI should rely on pytest.
- Expand tests here as new capabilities are added to integrations.
