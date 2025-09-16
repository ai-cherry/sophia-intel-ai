# Integration Test Directory

**For AI Coding Agents**: All business service integration tests are centralized here with standardized structure and pytest markers.

## Directory Structure

```
tests/integration/
├── conftest.py                    # Shared env loading & helpers
├── README.md                      # This index (AI agent entry point)
│
├── slack/                         # Slack API integration tests
│   ├── test_live_api.py          # Core API tests (@pytest.mark.slack)
│   ├── test_business_intelligence.py
│   ├── test_e2e.py
│   └── test_webhook_security.py
│
├── microsoft/                     # Microsoft Graph API tests
│   └── test_graph_smoke.py       # Auth & basic queries (@pytest.mark.microsoft)
│
├── gong/                          # Gong.io API tests
│   └── test_gong_smoke.py         # Connection & calls (@pytest.mark.gong)
│
├── airbyte/                       # Airbyte API tests
│   └── test_airbyte_smoke.py      # Server health & connections (@pytest.mark.airbyte)
│
├── hubspot/                       # HubSpot CRM API tests
│   └── test_hubspot_smoke.py      # Auth & contacts (@pytest.mark.hubspot)
│
├── salesforce/                    # Salesforce API tests
│   └── test_salesforce_smoke.py   # OAuth & SOQL queries (@pytest.mark.salesforce)
│
├── intercom/                      # Intercom API tests
│   └── test_intercom_smoke.py     # Auth & conversations (@pytest.mark.intercom)
│
├── looker/                        # Looker API tests
│   └── test_looker_smoke.py       # Auth & queries (@pytest.mark.looker)
│
├── asana/                         # Asana API tests
│   └── test_asana_smoke.py        # Auth & projects (@pytest.mark.asana)
│
└── linear/                        # Linear API tests
    └── test_linear_smoke.py       # Auth & issues (@pytest.mark.linear)
```

## Test Standards

Each service follows this pattern:

### Required Tests
- **Authentication**: Verify API keys/OAuth tokens work
- **Basic Listing**: List primary objects (users, conversations, projects, etc.)
- **Error Handling**: Test invalid auth, network failures

### Optional Tests (Gated by ENV vars)
- **Write Operations**: Only when `<SERVICE>_ALLOW_WRITE=true`
- **Advanced Features**: Webhooks, real-time, etc.

### Pytest Markers
All tests use:
```python
@pytest.mark.integration
@pytest.mark.<service>  # e.g., @pytest.mark.slack, @pytest.mark.hubspot
```

### Environment Variables
Tests gracefully skip when credentials missing. Required variables documented in `env.example`.

## Running Tests

```bash
# All integration tests
pytest tests/integration/ -m integration -v

# Specific service
pytest tests/integration/slack/ -v
pytest -m "integration and slack" -v

# Skip missing credentials
pytest tests/integration/ -v  # Tests auto-skip when creds missing
```

## Smoke Tools

Companion tools for quick CLI testing:
- `tools/slack/smoke.py`
- `tools/microsoft/smoke.py`
- `tools/airbyte/smoke.py`
- etc.

## Adding New Services

1. Create `tests/integration/<service>/`
2. Add `test_<service>_smoke.py` with standard structure
3. Add env vars to `env.example`
4. Create `tools/<service>/smoke.py`
5. Update this README

## Current Status

| Service | Tests | Smoke Tool | Status |
|---------|-------|------------|--------|
| **Slack** | ✅ | ✅ | Working |
| **Microsoft Graph** | ✅ | ✅ | Needs correct secret |
| **Gong** | ✅ | ❌ | Missing credentials |
| **Airbyte** | ✅ | ✅ | Ready to test |
| **HubSpot** | ✅ | ✅ | Ready to test |
| **Salesforce** | ✅ | ✅ | Ready to test |
| **Intercom** | ✅ | ✅ | Ready to test |
| **Looker** | ✅ | ✅ | Ready to test |
| **Asana** | ✅ | ✅ | Ready to test |
| **Linear** | ✅ | ✅ | Ready to test |
