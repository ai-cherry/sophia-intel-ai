# Sales Intelligence Swarm

A comprehensive real-time sales intelligence system that transforms sales calls into actionable insights through specialized AI agents working in concert.

## 🎯 Overview

The Sales Intelligence Swarm provides:

- **Real-Time Gong Integration**: Live call monitoring and analysis
- **Immediate Feedback System**: Instant coaching and recommendations during calls
- **Advanced Analytics**: Sentiment, competitor mentions, deal risk assessment
- **Enhanced Chat Interface**: Universal Sophia chat for sales intelligence
- **Live Dashboard**: Real-time call metrics and alerts

## 🏗️ Architecture

### Core Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Gong API      │────│  Stream Pipeline │────│   Agent Swarm   │
│  WebSocket/     │    │                  │    │                 │
│  Webhooks       │    │  - Buffer        │    │ • Transcription │
└─────────────────┘    │  - Parse         │    │ • Sentiment     │
                       │  - Route         │    │ • Competitive   │
                       └──────────────────┘    │ • Risk Analysis │
                                               │ • Coaching      │
                                               └─────────────────┘
                                                        │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Universal Sophia│────│  Feedback Engine │────│  Live Dashboard │
│     Interface   │    │                  │    │                 │
│                 │    │ • Real-time      │    │ • Call Metrics  │
│ • Chat          │    │ • Coaching Tips  │    │ • Alerts        │
│ • Commands      │    │ • Risk Alerts    │    │ • Analytics     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Specialized Agents

| Agent | Primary Function | Real-time Capability |
|-------|-----------------|---------------------|
| **TranscriptionAgent** | Audio-to-text conversion | High-frequency updates |
| **SentimentAgent** | Emotion & tone analysis | Real-time mood tracking |
| **CompetitiveAgent** | Competitor mention detection | Immediate notifications |
| **RiskAssessmentAgent** | Deal risk evaluation | Continuous assessment |
| **CoachingAgent** | Sales technique analysis | Instant feedback |
| **SummaryAgent** | Call outcome synthesis | Post-call processing |

## 🚀 Quick Start

### Installation

```bash
cd app/swarms/sales_intelligence
pip install -r requirements.txt
```

### Environment Setup

```bash
# Required for Gong integration
export GONG_ACCESS_KEY=your_gong_access_key
export GONG_CLIENT_SECRET=your_gong_client_secret

# Optional for enhanced features
export REDIS_URL=redis://localhost:6379
export OPENAI_API_KEY=your_openai_key
```

### Basic Usage

```python
from app.swarms.sales_intelligence import SalesIntelligenceOrchestrator

# Initialize orchestrator
orchestrator = SalesIntelligenceOrchestrator(
    gong_access_key="your_key",
    gong_client_secret="your_secret"
)

await orchestrator.initialize()

# Start monitoring a call
result = await orchestrator.start_call_monitoring("call_id_123")

# Query through Sophia interface
response = await orchestrator.process_sophia_query(
    "What's the status of the current call?"
)
```

## 📊 Dashboard Access

### Web Dashboard

Access the live dashboard at: `http://localhost:3333/sales-dashboard`

### WebSocket Connections

- Call-specific updates: `ws://localhost:3333/ws/sales/{call_id}`
- General updates: `ws://localhost:3333/ws/sales`

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/sales/query` | POST | Process Sophia queries |
| `/api/sales/start-monitoring` | POST | Start call monitoring |
| `/api/sales/dashboard/call/{call_id}` | GET | Get call dashboard data |
| `/api/sales/dashboard/team` | GET | Get team dashboard data |

## 🤖 Sophia Integration

### Natural Language Commands

The system supports natural language queries through Universal Sophia:

```
"What's the status of the current call?"
"How risky is this deal?"
"Any competitors mentioned?"
"Give me coaching feedback"
"What's the sentiment like?"
"Show me performance metrics"
```

### Command Types

- **Call Status**: Live call progress and metrics
- **Risk Assessment**: Deal probability and red flags
- **Competitive Intel**: Competitor mentions and positioning
- **Coaching Feedback**: Real-time sales technique improvements
- **Sentiment Analysis**: Emotional state and engagement tracking
- **Performance Metrics**: Individual and team analytics

## 🔧 Configuration

### Agent Configuration

```python
# Custom agent configuration
config = {
    "transcription": {
        "confidence_threshold": 0.8,
        "speaker_identification": True
    },
    "sentiment": {
        "emotional_analysis": True,
        "stress_detection": True
    },
    "competitive": {
        "competitor_database": "path/to/competitors.json",
        "threat_threshold": 0.7
    },
    "risk_assessment": {
        "historical_data_weight": 0.3,
        "real_time_weight": 0.7
    },
    "coaching": {
        "performance_standards": {
            "talk_time_ratio": 0.35,
            "question_quality": 0.7
        }
    }
}
```

### Feedback Engine Configuration

```python
# Feedback delivery configuration
feedback_config = {
    "delivery_channels": ["popup", "sidebar", "dashboard"],
    "priority_thresholds": {
        "critical": 0.9,
        "high": 0.7,
        "medium": 0.5
    },
    "coaching_prompts": {
        "enabled": True,
        "urgency_threshold": 4
    }
}
```

## 📈 Metrics and Analytics

### Key Metrics Tracked

- **Call Quality Score**: Overall call performance (0-100)
- **Sentiment Score**: Emotional engagement (-1 to 1)
- **Risk Score**: Deal probability (0 to 1)
- **Talk Time Ratio**: Speaker balance
- **Question Quality**: Open-ended question ratio
- **Competitive Activity**: Competitor mention tracking
- **Buying Signals**: Purchase intent indicators
- **Coaching Score**: Sales technique assessment

### Real-time Alerts

- **Critical Risk**: Deal probability drops below threshold
- **Negative Sentiment**: Customer dissatisfaction detected
- **Competitive Threat**: High-risk competitor activity
- **Coaching Opportunity**: Performance improvement suggestions
- **Buying Signal**: Purchase intent detected

## 🧪 Testing

### Run Tests

```bash
# Run all tests
python -m pytest app/swarms/sales_intelligence/tests.py -v

# Run specific test categories
python -m pytest app/swarms/sales_intelligence/tests.py::TestSalesAgents -v
python -m pytest app/swarms/sales_intelligence/tests.py::TestPerformanceBenchmarks -v
```

### Performance Benchmarks

```python
from app.swarms.sales_intelligence.tests import TestPerformanceBenchmarks

# Run performance tests
await TestPerformanceBenchmarks().test_agent_processing_speed()
await TestPerformanceBenchmarks().test_concurrent_call_processing()
```

## 🔒 Security Considerations

### Data Privacy

- All call data is processed in real-time and not permanently stored
- Sensitive information is filtered and redacted
- RBAC integration ensures proper access control
- Encryption in transit and at rest

### API Security

- JWT-based authentication for API endpoints
- Rate limiting on all endpoints
- Input validation and sanitization
- Audit logging for all operations

## 📚 Examples

### Example 1: Basic Call Monitoring

```python
import asyncio
from app.swarms.sales_intelligence import SalesIntelligenceOrchestrator

async def monitor_call():
    orchestrator = SalesIntelligenceOrchestrator()
    await orchestrator.initialize()
    
    # Start monitoring
    result = await orchestrator.start_call_monitoring("call_123")
    print(f"Monitoring started: {result}")
    
    # Query status
    status = await orchestrator.process_sophia_query(
        "What's the status of call call_123?"
    )
    print(f"Call status: {status}")

asyncio.run(monitor_call())
```

### Example 2: Custom Feedback Handler

```python
from app.swarms.sales_intelligence import SalesFeedbackSystem, DeliveryChannel

async def custom_feedback_handler(message):
    print(f"Custom Alert: {message.title}")
    print(f"Message: {message.message}")
    print(f"Action Items: {', '.join(message.action_items)}")

# Setup custom delivery
feedback_system = SalesFeedbackSystem()
feedback_system.feedback_engine.register_delivery_handler(
    DeliveryChannel.POPUP,
    custom_feedback_handler
)
```

### Example 3: Dashboard Integration

```python
from app.swarms.sales_intelligence import create_dashboard_app

# Create FastAPI app with dashboard
dashboard_app = create_dashboard_app(dashboard_instance)

# Mount as sub-application
main_app.mount("/sales", dashboard_app)
```

## 🔄 Integration Points

### Existing System Integration

The Sales Intelligence Swarm integrates seamlessly with:

- **Universal Sophia**: Natural language query processing
- **MCP Server**: Core infrastructure and RBAC
- **Gong Platform**: Real-time call data streaming
- **Business Intelligence**: Existing BI integrations
- **Agent Factory**: Swarm orchestration framework

### Webhook Integration

```python
# Setup webhooks for external systems
@app.post("/webhooks/gong")
async def gong_webhook(request: dict):
    event_type = request.get("eventType")
    
    if event_type == "callStarted":
        await orchestrator.start_call_monitoring(request["callId"])
    
    return {"status": "processed"}
```

## 🚨 Troubleshooting

### Common Issues

1. **Gong Connection Failed**
   - Verify API credentials
   - Check network connectivity
   - Ensure WebSocket support

2. **Agent Processing Slow**
   - Check system resources
   - Optimize agent configuration
   - Consider scaling horizontally

3. **Dashboard Not Updating**
   - Verify WebSocket connections
   - Check Redis connectivity
   - Review error logs

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable debug mode
orchestrator = SalesIntelligenceOrchestrator(debug=True)
```

## 🛣️ Roadmap

### Immediate Enhancements

- [ ] Voice tone analysis integration
- [ ] Advanced competitive positioning
- [ ] Custom coaching frameworks
- [ ] Enhanced mobile dashboard

### Future Features

- [ ] Multi-language support
- [ ] Advanced AI model integration
- [ ] Predictive analytics
- [ ] Custom agent development SDK

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone repository
git clone https://github.com/your-org/sophia-intel-ai.git

# Install dependencies
cd app/swarms/sales_intelligence
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests.py -v
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Gong.io for sales call intelligence platform
- OpenAI for language model capabilities
- FastAPI for robust web framework
- Redis for real-time data management

---

**💡 Tips for Maximum Impact:**

1. **Start Small**: Begin with one or two agents, then scale up
2. **Train Your Team**: Ensure sales reps understand the feedback system
3. **Customize**: Adapt agent configurations to your sales process
4. **Monitor Performance**: Use built-in analytics to optimize settings
5. **Iterate**: Continuously improve based on real-world usage

For support, please open an issue or contact the Sophia Intelligence Team.