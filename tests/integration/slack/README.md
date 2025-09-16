# Slack Integration Testing Framework

This directory contains comprehensive tests for the Slack integration, covering both inbound (pull) webhook handling and outbound (push) API interactions.

## 📁 Directory Structure

```
tests/integration/slack/
├── README.md                    # This documentation
├── conftest.py                  # Shared fixtures, mocks, and test data
├── test_webhook_security.py     # Inbound webhook security tests
├── test_slack_client.py         # Outbound Slack client tests
├── test_business_intelligence.py # BI integration tests
└── test_e2e.py                  # End-to-end tests (real Slack)
```

## 🧪 Test Categories

### Unit Tests (`@pytest.mark.unit`)
- No external dependencies
- Mock all Slack API calls
- Fast execution (< 1s per test)
- 85% coverage target

### Integration Tests (`@pytest.mark.integration`)
- Mocked Slack interactions
- Real Redis connections
- Test complete workflows
- Focus on component integration

### End-to-End Tests (`@pytest.mark.e2e`)
- **Requires real Slack tokens**
- Real Slack workspace interactions
- Performance validation
- Manual trigger only

### Security Tests
- Signature verification
- Token validation
- Rate limit compliance
- HMAC timing attack protection

## 🔧 Setup and Configuration

### Environment Variables

#### Required for Unit/Integration Tests:
```bash
# Mock tokens (any format for unit tests)
export SLACK_BOT_TOKEN="xoxb-test-token"
export SLACK_SIGNING_SECRET="test-signing-secret" 
export REDIS_URL="redis://localhost:6379"
```

#### Required for E2E Tests:
```bash
# Real Slack tokens from https://api.slack.com/apps
export SLACK_BOT_TOKEN="xoxb-your-real-bot-token"
export SLACK_SIGNING_SECRET="your-real-signing-secret"
export SLACK_USER_TOKEN="xoxp-your-user-token"  # Optional, for search
export SLACK_APP_TOKEN="xapp-your-app-token"    # Optional, for Socket Mode
export SLACK_TEST_CHANNEL="#ci-slack-tests"     # Test channel name
```

### Required Slack Scopes

#### Bot Token Scopes:
- `chat:write` - Send messages
- `channels:read` - List channels
- `users:read` - List users  
- `app_mentions:read` - Receive mentions
- `commands` - Handle slash commands
- `chat:write.public` - Post to public channels

#### User Token Scopes (Optional):
- `search:read` - Search messages

## 🚀 Running Tests

### Quick Start
```bash
# Run all unit tests
pytest tests/integration/slack/ -m unit -v

# Run integration tests (requires Redis)
pytest tests/integration/slack/ -m integration -v

# Run security tests
pytest tests/integration/slack/ -k "security or signature" -v
```

### Coverage Reports
```bash
# Unit tests with coverage
pytest tests/integration/slack/ -m unit \
  --cov=app.integrations.slack_optimized_client \
  --cov=app.api.routers.slack_business_intelligence \
  --cov-report=html \
  --cov-fail-under=85

# View coverage report
open htmlcov/index.html
```

### E2E Tests (Production-like)
```bash
# 1. Validate tokens first
python scripts/test_slack_tokens.py

# 2. Run E2E tests
pytest tests/integration/slack/ -m e2e -v --tb=short
```

### Performance Tests
```bash
# Run slow/performance tests
pytest tests/integration/slack/ -m slow -v --durations=10
```

## 📋 Test Fixtures

### Available Fixtures (from `conftest.py`)

- `test_env_vars` - Mock environment variables
- `fake_redis` - In-memory Redis for testing
- `test_client` - FastAPI test client
- `signature_helper` - Slack signature generation
- `event_builder` - Slack event payload builder
- `sample_data` - Sample Slack messages/users
- `slack_client_with_mocks` - Fully mocked Slack client
- `mock_sophia_intelligence` - Mocked BI service

### Example Usage
```python
@pytest.mark.unit
async def test_message_sending(slack_client_with_mocks):
    client, mock_slack_client, _, _ = slack_client_with_mocks
    
    await client.send_message(
        channel="C123456",
        text="Test message"
    )
    
    mock_slack_client.chat_postMessage.assert_called_once()
```

## 🔐 Security Testing

### Webhook Signature Verification
Tests the HMAC-SHA256 signature verification that protects against:
- Request tampering
- Replay attacks
- Timing attacks
- Missing/invalid signatures

### Token Validation
Validates that tokens have required scopes and proper format:
- Bot tokens start with `xoxb-`
- User tokens start with `xoxp-`  
- App tokens start with `xapp-`
- Signing secrets are properly configured

## 🏗️ CI/CD Integration

### GitHub Actions Workflow
Located at `.github/workflows/slack-integration-tests.yml`

**Triggers:**
- Push to `main`/`develop` branches
- PRs affecting Slack code
- Daily scheduled runs
- Manual dispatch with E2E option

**Jobs:**
- `unit-tests` - Fast unit/integration tests
- `security-tests` - Security and compliance
- `e2e-tests` - Real Slack testing (scheduled/manual)
- `performance-tests` - Load and timing tests
- `quality-checks` - Linting and type checking

### Coverage Requirements
- **Minimum**: 85% line coverage
- **Target**: 90% line coverage
- **Files**: All Slack integration modules

## 🐛 Troubleshooting

### Common Issues

**Token Validation Failures:**
```bash
# Check token scopes
python scripts/test_slack_tokens.py
```

**Redis Connection Issues:**
```bash
# Start local Redis
docker run -p 6379:6379 redis:7-alpine
```

**Import Errors:**
```bash
# Install in development mode
poetry install
```

**Rate Limiting:**
```bash
# E2E tests may hit rate limits - add delays or reduce test frequency
```

### Debug Mode
```bash
# Run with verbose output
pytest tests/integration/slack/ -v -s --tb=long

# Run single test with debugging
pytest tests/integration/slack/test_slack_client.py::TestMessageSending::test_send_message_basic -v -s
```

## 📝 Writing New Tests

### Test Naming Convention
- `test_<feature>_<scenario>` - Clear descriptive names
- `test_<component>_<action>_<expected_result>` - For complex tests

### Required Markers
```python
@pytest.mark.unit          # No external dependencies
@pytest.mark.integration   # Mocked externals, real internals
@pytest.mark.e2e          # Real Slack interactions
@pytest.mark.slow         # Takes >5 seconds
```

### Example Test Structure
```python
@pytest.mark.unit
class TestSlackClient:
    async def test_send_message_success(self, slack_client_with_mocks):
        # Arrange
        client, mock_slack, _, _ = slack_client_with_mocks
        
        # Act
        response = await client.send_message("C123", "Hello")
        
        # Assert
        assert response["ok"] is True
        mock_slack.chat_postMessage.assert_called_once_with(
            channel="C123",
            text="Hello"
        )
```

## 🔗 Related Documentation

- [Slack API Documentation](https://api.slack.com/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [Pytest Documentation](https://docs.pytest.org/)
- [GitHub Actions Workflow Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)

## 📈 Coverage Goals

### Current Status
- **Unit Tests**: Target 85% minimum
- **Integration Tests**: Focus on critical paths
- **E2E Tests**: Happy path + edge cases
- **Security Tests**: 100% of auth flows

### Test Metrics Dashboard
Coverage reports are uploaded to Codecov and available in the GitHub Actions artifacts.

---

**Last Updated**: 2025-09-15  
**Maintained By**: Sophia Intel AI Team  
**Review Frequency**: Monthly or when Slack API changes
