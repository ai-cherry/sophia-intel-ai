# Business Intelligence Integration Testing Framework

A comprehensive testing strategy for validating integrations with business intelligence platforms including Gong, Slack, Salesforce, Looker, Linear, Asana, Notion, and HubSpot.

## 🎯 Overview

This framework provides systematic testing of BI platform integrations with focus on:
- **Connection reliability** and authentication
- **Data flow validation** and structure integrity  
- **End-to-end workflow** testing
- **Performance benchmarking** and SLA compliance
- **Error handling** and fallback strategies
- **Health monitoring** and alerting

## 📋 Testing Strategy

### 1. Connection Testing (`test_bi_integrations.py`)

Tests fundamental connectivity to each BI platform:

- **Authentication validation** - API keys, OAuth tokens, basic auth
- **Network connectivity** - Timeouts, retries, circuit breakers
- **Response validation** - Status codes, headers, basic structure
- **Rate limit handling** - Respect platform limits and retry-after headers

**Supported Platforms:**
- **Gong** - Call intelligence and analysis
- **HubSpot** - CRM and marketing automation  
- **Salesforce** - CRM and pipeline management
- **Asana** - Task and project coordination
- **Linear** - Project management and issue tracking
- **Slack** - Team communication
- **Notion** - Documentation and knowledge management
- **Looker** - Business intelligence and analytics

### 2. Data Flow Validation

Ensures data integrity and structure consistency:

- **Schema validation** - Required fields, data types, formats
- **Data quality checks** - Completeness, accuracy, consistency
- **Performance thresholds** - Response times, payload sizes
- **Content validation** - Business logic rules, relationships

### 3. End-to-End Workflow Testing

Tests complete business processes:

- **Lead qualification workflows** - CRM → Calls → Messaging → Automation
- **Project optimization workflows** - Projects → AI Analysis → Agent Deployment
- **Call analysis workflows** - Gong → AI Processing → Follow-up Actions

### 4. Performance Benchmarking (`performance_benchmarking.py`)

Comprehensive performance testing:

- **Load testing** - Concurrent users, request volumes
- **Response time analysis** - Average, P95, P99 percentiles  
- **Throughput measurement** - Requests per second
- **Resource monitoring** - CPU, memory, network utilization
- **SLA compliance** - Performance thresholds validation

### 5. Error Handling & Fallbacks (`error_handling.py`)

Resilient integration patterns:

- **Circuit breakers** - Prevent cascade failures
- **Retry logic** - Exponential backoff with jitter
- **Fallback strategies** - Cache, mock data, degraded mode
- **Error classification** - Auth, rate limit, timeout, service errors

## 🚀 Quick Start

### Prerequisites

```bash
# Install dependencies
pip install pytest pytest-asyncio httpx faker psutil

# Ensure MCP server is running
python3 -m uvicorn dev_mcp_unified.core.mcp_server:app --host 127.0.0.1 --port 3333 --reload
```

### Environment Configuration

Set up environment variables for platform integrations:

```bash
# Gong Integration
export GONG_ACCESS_KEY="your-gong-access-key"
export GONG_CLIENT_SECRET="your-gong-client-secret" 
export GONG_BASE_URL="https://api.gong.io"

# HubSpot Integration  
export HUBSPOT_API_KEY="your-hubspot-api-key"

# Salesforce Integration
export SALESFORCE_API_KEY="your-salesforce-api-key"
export SALESFORCE_INSTANCE_URL="https://your-instance.salesforce.com"

# Asana Integration
export ASANA_ACCESS_TOKEN="your-asana-access-token"

# Linear Integration  
export LINEAR_API_KEY="your-linear-api-key"

# OpenRouter for AI agents (if using)
export OPENROUTER_API_KEY="your-openrouter-api-key"
```

### Running Tests

#### Quick Test Suite (Recommended for CI/CD)
```bash
python run_comprehensive_tests.py --quick
```

#### Full Test Suite  
```bash
python run_comprehensive_tests.py
```

#### Platform-Specific Testing
```bash
python run_comprehensive_tests.py --platform gong
```

#### Custom Output Directory
```bash
python run_comprehensive_tests.py --output ./custom_reports
```

### Running Individual Test Components

#### Connection Tests Only
```python
import asyncio
from test_bi_integrations import BIIntegrationTester

async def test_connections():
    async with BIIntegrationTester() as tester:
        results = await tester.test_all_connections()
        print(f"Passed: {results['summary']['passed']}/{results['summary']['total_tests']}")

asyncio.run(test_connections())
```

#### Performance Benchmarks Only
```python  
import asyncio
from performance_benchmarking import BIPerformanceBenchmarker

async def run_benchmarks():
    benchmarker = BIPerformanceBenchmarker()
    results = await benchmarker.run_standard_benchmark_suite()
    
    for name, result in results.items():
        print(f"{name}: {result.avg_response_time_ms:.2f}ms avg, {result.success_rate:.1%} success")

asyncio.run(run_benchmarks())
```

#### Mock Data Generation
```python
from mock_data_generator import BIMockDataGenerator, MockDataConfig

generator = BIMockDataGenerator()

# Generate sample Gong calls
config = MockDataConfig(platform="gong", scenario="success", record_count=10)
gong_data = generator.generate_gong_calls(config)

# Generate CRM contacts with data quality issues
config = MockDataConfig(platform="hubspot", scenario="success", data_quality=0.7)
crm_data = generator.generate_crm_contacts(config)
```

## 📊 Test Reports

The framework generates comprehensive reports:

### JSON Reports
- **`comprehensive_test_results_{timestamp}.json`** - Full test results with detailed metrics
- **`test_summary_{timestamp}.json`** - Executive summary for dashboards
- **`bi_performance_benchmark_{timestamp}.json`** - Performance analysis report

### Markdown Reports  
- **`test_report_{timestamp}.md`** - Human-readable test report

### Report Structure
```json
{
  "start_time": "2025-09-03T10:30:00",
  "end_time": "2025-09-03T10:45:00", 
  "connection_tests": {
    "summary": {
      "total_tests": 6,
      "passed": 5,
      "failed": 1,
      "success_rate": 0.83
    }
  },
  "performance_benchmarks": {
    "test_summary": {
      "total_requests": 240,
      "overall_success_rate": 0.95
    }
  },
  "summary": {
    "overall_status": "passed",
    "phases_passed": 5,
    "total_phases": 6,
    "recommendations": [
      "Connection reliability issues detected for Linear integration",
      "Consider optimizing Gong API response times"
    ]
  }
}
```

## 🔧 Configuration

### SLA Thresholds
```python
from performance_benchmarking import SLAThresholds

thresholds = SLAThresholds(
    max_response_time_ms=5000,      # 5 second max response
    max_p95_response_time_ms=8000,   # 8 second P95
    max_p99_response_time_ms=15000,  # 15 second P99  
    min_success_rate=0.95,           # 95% success rate
    max_error_rate=0.05,             # 5% error rate
    min_throughput_rps=1.0           # 1 request/second minimum
)
```

### Circuit Breaker Configuration
```python
from dev_mcp_unified.integrations.error_handling import CircuitBreakerConfig

circuit_config = CircuitBreakerConfig(
    failure_threshold=5,        # Open after 5 failures
    recovery_timeout=60,        # Try again after 60 seconds
    expected_exception=Exception
)
```

### Retry Configuration  
```python
from dev_mcp_unified.integrations.error_handling import RetryConfig

retry_config = RetryConfig(
    max_attempts=3,             # Maximum retry attempts
    base_delay=1.0,            # Base delay in seconds
    max_delay=60.0,            # Maximum delay cap
    exponential_backoff=True,   # Use exponential backoff
    jitter=True                # Add randomization
)
```

## 🏗️ Architecture

### Test Framework Architecture
```
tests/integration/business_intelligence/
├── test_bi_integrations.py      # Core integration testing
├── performance_benchmarking.py  # Performance and load testing  
├── mock_data_generator.py      # Realistic mock data generation
├── run_comprehensive_tests.py   # Test orchestration and reporting
└── README.md                   # Documentation

dev_mcp_unified/integrations/
└── error_handling.py           # Error handling and fallback strategies
```

### Integration Flow
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Test Runner   │───▶│ Integration Test │───▶│  BI Platforms   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Error Handler   │    │ Mock Generator   │    │ Health Monitor  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Circuit Breaker │    │ Performance      │    │    Reporting    │
│   & Fallbacks   │    │  Benchmarker     │    │   & Analytics   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📈 Performance Benchmarks

### Standard Benchmark Suite

| Test Name | Description | Concurrent Users | Total Requests |
|-----------|-------------|------------------|----------------|
| `health_check_baseline` | Basic health endpoint | 1 | 5 |
| `gong_calls_light_load` | Gong calls (7 days) | 2 | 20 |
| `gong_calls_medium_load` | Gong calls (30 days) | 5 | 50 |  
| `crm_contacts_performance` | CRM contacts | 3 | 30 |
| `crm_pipeline_performance` | CRM pipeline | 2 | 20 |
| `dashboard_load_test` | Business dashboard | 4 | 40 |
| `projects_overview_stress` | Projects overview | 3 | 25 |
| `workflow_trigger_performance` | Workflow automation | 2 | 15 |
| `high_concurrency_test` | Stress test | 10 | 100 |

### Performance Metrics

- **Response Time** - Average, median, P95, P99, min, max
- **Throughput** - Requests per second (RPS)
- **Success Rate** - Percentage of successful requests
- **Error Rate** - Percentage of failed requests  
- **Resource Utilization** - CPU, memory, network usage

## 🛡️ Error Handling Strategies

### Circuit Breaker Pattern
Prevents cascade failures by "opening" when failure threshold is reached:
- **Closed** - Normal operation
- **Open** - Failures detected, requests blocked  
- **Half-Open** - Testing if service recovered

### Fallback Strategies
1. **Cache Fallback** - Return cached data (even if stale)
2. **Mock Data Fallback** - Generate realistic mock responses
3. **Degraded Mode** - Return minimal/empty responses  
4. **Service Bypass** - Skip non-critical integrations

### Retry Logic
- **Exponential Backoff** - Increasing delays between retries
- **Jitter** - Randomization to prevent thundering herd
- **Respectful Retries** - Honor rate limit headers
- **Smart Classification** - Don't retry auth/config errors

## 🔍 Monitoring & Alerting

### Health Checks
- **Platform Status** - Individual integration health
- **Response Times** - Performance degradation detection
- **Error Rates** - Failure pattern analysis
- **Data Quality** - Schema and content validation

### Alert Conditions
- **Critical** - Platform completely down, auth failures
- **Warning** - High response times, degraded performance
- **Info** - Successful recoveries, configuration changes

## 📝 Usage Examples

### CI/CD Integration
```yaml
# GitHub Actions example
name: BI Integration Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies  
        run: pip install -r requirements.txt
      - name: Start MCP Server
        run: |
          python3 -m uvicorn dev_mcp_unified.core.mcp_server:app --host 127.0.0.1 --port 3333 &
          sleep 10
      - name: Run Integration Tests
        env:
          GONG_ACCESS_KEY: ${{ secrets.GONG_ACCESS_KEY }}
          GONG_CLIENT_SECRET: ${{ secrets.GONG_CLIENT_SECRET }}
        run: python tests/integration/business_intelligence/run_comprehensive_tests.py --quick
```

### Production Monitoring
```python
import asyncio
from test_bi_integrations import BIIntegrationTester

async def health_check():
    """Production health check for monitoring systems"""
    async with BIIntegrationTester() as tester:
        health = await tester.get_integration_health()
        
        if health["overall_status"] != "healthy":
            # Send alert to monitoring system
            send_alert(f"BI Integration unhealthy: {health['overall_status']}")
            
        return health

# Run every 5 minutes in production
```

### Custom Test Scenarios
```python
from test_bi_integrations import BIIntegrationTester, ConnectionTest

async def custom_test():
    # Create custom connection test
    custom_test = ConnectionTest(
        name="custom_endpoint_test",
        endpoint="/api/business/custom",
        auth_method="bearer",
        required_env_vars=["CUSTOM_API_TOKEN"],
        timeout_seconds=15
    )
    
    async with BIIntegrationTester() as tester:
        result = await tester.test_connection(custom_test)
        print(f"Custom test result: {result}")
```

## 🤝 Contributing

### Adding New Platform Integration

1. **Add connection test configuration:**
```python
ConnectionTest(
    name="new_platform_test", 
    endpoint="/api/business/new-platform",
    auth_method="api_key",
    required_env_vars=["NEW_PLATFORM_API_KEY"]
)
```

2. **Add data flow validation:**
```python
DataFlowTest(
    name="new_platform_data_structure",
    source_endpoint="/api/business/new-platform/data",
    expected_fields=["field1", "field2"],
    data_validation_rules={"field1": {"type": "string"}}
)
```

3. **Add mock data generator:**
```python
def generate_new_platform_data(self, config: MockDataConfig):
    # Generate realistic mock data for the platform
    pass
```

4. **Add performance benchmark:**
```python
BenchmarkConfig(
    name="new_platform_performance",
    endpoint="/api/business/new-platform",
    concurrent_users=2,
    total_requests=20
)
```

### Running Development Tests
```bash
# Run with verbose logging
export LOG_LEVEL=DEBUG
python run_comprehensive_tests.py --quick

# Test specific components
pytest test_bi_integrations.py::TestBIIntegrations::test_connection_tests -v

# Generate performance report only
python performance_benchmarking.py
```

## 📚 References

- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [API Testing Best Practices](https://assertible.com/blog/api-testing-best-practices)
- [Performance Testing Guidelines](https://k6.io/docs/testing-guides/)
- [Integration Testing Strategies](https://martinfowler.com/articles/microservice-testing/)

---

🎯 **Integration testing strategy complete!** This framework provides systematic validation of all BI platform integrations with comprehensive error handling, performance benchmarking, and health monitoring.