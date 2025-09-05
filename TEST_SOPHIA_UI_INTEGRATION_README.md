# Sophia UI Integration Test Suite

Comprehensive test script that validates the complete integration flow for the Sophia Intelligence Platform.

## Features

✅ **API Route Testing**

- Tests persona API endpoints and functionality
- Validates Agent Factory integration
- Checks dashboard data endpoints
- Tests integration intelligence capabilities

✅ **WebSocket Testing**

- Validates real-time connection establishment
- Tests persona-specific WebSocket endpoints
- Verifies message delivery and real-time updates

✅ **Cross-Platform Integration**

- Tests platform data correlation
- Validates multi-platform connectivity
- Checks data aggregation capabilities

✅ **Executive Dashboard Validation**

- Tests cost tracking and metrics
- Validates system health monitoring
- Checks performance data aggregation

✅ **Interactive Demo Mode**

- Showcases complete system capabilities
- Provides guided walkthrough
- Perfect for demonstrations

## Quick Start

### 1. Run Interactive Demo

```bash
python test_sophia_ui_integration.py --demo
```

### 2. Run Complete Test Suite

```bash
python test_sophia_ui_integration.py --full-suite
```

### 3. Test Specific Component

```bash
python test_sophia_ui_integration.py --component websocket
python test_sophia_ui_integration.py --component api
python test_sophia_ui_integration.py --component dashboard
```

### 4. Custom Configuration

```bash
python test_sophia_ui_integration.py --full-suite \
    --base-url http://localhost:8000 \
    --ws-url ws://localhost:8000 \
    --verbose \
    --output results.json
```

## Command Line Options

| Option         | Description               | Example                            |
| -------------- | ------------------------- | ---------------------------------- |
| `--demo`       | Run interactive demo mode | `--demo`                           |
| `--full-suite` | Run all test categories   | `--full-suite`                     |
| `--component`  | Test specific component   | `--component api`                  |
| `--base-url`   | Override API base URL     | `--base-url http://localhost:8000` |
| `--ws-url`     | Override WebSocket URL    | `--ws-url ws://localhost:8000`     |
| `--verbose`    | Enable debug logging      | `--verbose`                        |
| `--output`     | Save results to file      | `--output test_results.json`       |

## Test Categories

### 🔍 API Tests

- **Health Check**: Basic server connectivity
- **Persona Routes**: AI team member interactions
- **Agent Factory**: Swarm creation and inventory
- **Dashboard Routes**: Data aggregation endpoints
- **Integration Routes**: Cross-platform capabilities

### 🔌 WebSocket Tests

- **Basic Connection**: WebSocket establishment
- **Persona WebSocket**: Real-time persona chat
- **Real-time Updates**: Live system monitoring

### 🌐 Cross-Platform Tests

- **Platform Correlation**: Multi-platform data integration
- **Data Aggregation**: Combined platform metrics

### 📊 Dashboard Tests

- **Executive Metrics**: High-level system overview
- **Cost Tracking**: Usage and expense monitoring
- **System Health**: Component status monitoring

## Expected Outputs

### Success Case

```
🎯 SOPHIA UI INTEGRATION TEST RESULTS
=====================================
📊 Test Summary:
   Total Tests: 15
   Success Rate: 93.3%
   Duration: 12.45 seconds
   Status: EXCELLENT

✅ PASS: 14
⚠️  WARNING: 1

💡 Recommendations:
✅ All systems functioning well!

📋 Category Breakdown:
✅ basic: 1/1 (100.0%)
✅ personas: 2/2 (100.0%)
✅ agent_factory: 3/3 (100.0%)
⚠️  websocket: 2/3 (66.7%)
✅ dashboard: 2/2 (100.0%)
```

### Failure Case

```
🎯 SOPHIA UI INTEGRATION TEST RESULTS
=====================================
📊 Test Summary:
   Total Tests: 15
   Success Rate: 60.0%
   Duration: 8.23 seconds
   Status: FAIR

✅ PASS: 9
❌ FAIL: 4
⚠️  WARNING: 2

💡 Recommendations:
🔴 4 critical issues need immediate attention
🟡 2 components may need implementation or configuration
🚨 websocket component appears to be non-functional

📋 Category Breakdown:
✅ basic: 1/1 (100.0%)
⚠️  personas: 1/2 (50.0%)
✅ agent_factory: 3/3 (100.0%)
❌ websocket: 0/3 (0.0%)
✅ dashboard: 2/2 (100.0%)
```

## Demo Mode Scenarios

The interactive demo includes 5 scenarios:

1. **AI Team Member Interaction** - Shows persona agent capabilities
2. **Agent Factory Swarm Creation** - Demonstrates swarm creation
3. **Real-time WebSocket Updates** - Shows live monitoring
4. **Cross-Platform Integration** - Displays platform correlation
5. **Executive Dashboard** - Shows high-level metrics

## Troubleshooting

### Common Issues

**Connection Refused**

```bash
# Check if services are running
curl http://localhost:8003/health
```

**WebSocket Connection Failed**

```bash
# Test alternative ports
python test_sophia_ui_integration.py --ws-url ws://localhost:8000
```

**Missing Dependencies**

```bash
pip install aiohttp websockets
```

### Service Dependencies

Ensure these services are running:

- **Unified Server** (port 8003): Main API server
- **WebSocket Service**: Real-time communication
- **Message Bus**: Inter-service communication
- **Database**: Data persistence layer

### Debugging

Enable verbose logging for detailed output:

```bash
python test_sophia_ui_integration.py --full-suite --verbose
```

Check the generated log file:

```bash
tail -f sophia_ui_test.log
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
- name: Run Sophia Integration Tests
  run: |
    python test_sophia_ui_integration.py --full-suite --output ci_results.json

- name: Upload Test Results
  uses: actions/upload-artifact@v3
  with:
    name: sophia-integration-results
    path: ci_results.json
```

### Docker Integration

```bash
docker run --network host sophia-platform \
  python test_sophia_ui_integration.py --full-suite
```

## Advanced Usage

### Custom Test Configuration

Edit `test_config.json` to customize:

- API endpoints
- Timeout values
- Test data samples
- Expected response formats

### Programmatic Usage

```python
from test_sophia_ui_integration import SophiaUIIntegrationTester, TestConfig

config = TestConfig()
config.BASE_URL = "http://your-server:8003"

tester = SophiaUIIntegrationTester(config)
results = await tester.run_full_test_suite()
print(f"Success rate: {results['summary']['success_rate']}%")
```

## Contributing

To add new test cases:

1. Create test method in appropriate tester class
2. Add to test category in `_run_*_tests()` method
3. Update expected endpoints in `test_config.json`
4. Add documentation to this README

## Support

For issues with the test suite:

1. Check service logs: `tail -f sophia_ui_test.log`
2. Verify service status: `curl http://localhost:8003/health`
3. Run demo mode first: `python test_sophia_ui_integration.py --demo`

The test suite provides comprehensive validation of the Sophia Intelligence Platform integration stack, ensuring all components work together seamlessly.
