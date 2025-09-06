# Portkey Integration Implementation Guide

## Overview
This document provides a complete implementation guide for integrating Portkey as the centralized LLM routing layer in the Sophia Intel AI system.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Applications                      │
├──────────────────────┬───────────────────────────────┤
│   Artemis Factory    │      Sophia Factory           │
├──────────────────────┴───────────────────────────────┤
│              Portkey Configuration Manager           │
├───────────────────────────────────────────────────────┤
│                  Portkey Client                      │
├───────────────────────────────────────────────────────┤
│              Virtual Keys (Provider Access)          │
├───────────────────────────────────────────────────────┤
│   OpenAI │ Anthropic │ DeepSeek │ Groq │ Others     │
└───────────────────────────────────────────────────────┘
```

## Implementation Files

### Core Configuration
- `/app/core/portkey_config.py` - Centralized Portkey manager
- `/app/core/vector_db_config.py` - Vector database connections

### Factory Integration
- `/app/artemis/portkey_unified_factory.py` - Artemis tactical operations
- `/app/sophia/portkey_unified_factory.py` - Sophia business intelligence

### Testing & Setup
- `/scripts/setup_portkey_keys.py` - Initial configuration setup
- `/scripts/test_portkey_integration.py` - Integration testing

## Setup Instructions

### 1. Configure Environment Variables

Run the setup script to configure all API keys:

```bash
python scripts/setup_portkey_keys.py
```

This will create a `.env` file with all necessary keys configured.

### 2. Verify Configuration

The `.env` file should contain:

```env
# Main Portkey Configuration
PORTKEY_API_KEY=your_portkey_api_key
PORTKEY_BASE_URL=https://api.portkey.ai/v1

# Virtual Keys (one per provider)
OPENAI_VK=openai-vk-xxxxx
ANTHROPIC_VK=anthropic-vk-xxxxx
DEEPSEEK_VK=deepseek-vk-xxxxx
# ... more virtual keys

# Vector Databases
QDRANT_API_KEY=your_qdrant_key
QDRANT_URL=your_qdrant_url
# ... more database configs
```

### 3. Test Integration

Run the comprehensive test suite:

```bash
python scripts/test_portkey_integration.py
```

Expected output:
- ✅ Portkey connection successful
- ✅ Virtual keys configured
- ✅ Provider health checks
- ✅ Completion tests
- ✅ Embedding generation
- ✅ Factory integration

## Usage Examples

### Basic Completion

```python
from app.core.portkey_config import get_portkey_manager

manager = get_portkey_manager()
response = manager.create_completion(
    provider="openai",
    model="gpt-4-turbo",
    messages=[{"role": "user", "content": "Hello"}],
    temperature=0.7
)
```

### Artemis Agent Creation

```python
from app.artemis.portkey_unified_factory import get_portkey_artemis_factory
from app.artemis.portkey_unified_factory import TechnicalAgentRole

factory = get_portkey_artemis_factory()

# Create tactical agent
agent = await factory.create_agent_with_portkey(
    name="SecurityScanner",
    role=TechnicalAgentRole.SECURITY_AUDITOR,
    specialty="vulnerability_detection"
)

# Execute task
result = await factory.execute_with_portkey(
    agent=agent,
    prompt="Analyze this code for security vulnerabilities",
    max_tokens=2000
)
```

### Sophia Business Intelligence

```python
from app.sophia.portkey_unified_factory import get_portkey_sophia_factory
from app.sophia.portkey_unified_factory import BusinessAgentRole

factory = get_portkey_sophia_factory()

# Create business analyst
agent = await factory.create_business_agent(
    name="MarketAnalyst",
    role=BusinessAgentRole.MARKET_ANALYST,
    business_domain="technology"
)

# Generate insight
insight = await factory.generate_business_insight(
    agent=agent,
    query="What are the key trends in AI adoption?",
    context={"industry": "enterprise_software"}
)
```

## Provider Mapping

### Artemis Technical Roles
| Role | Primary Provider | Fallback Providers |
|------|-----------------|-------------------|
| CODE_REVIEWER | OpenAI | Anthropic, DeepSeek |
| SECURITY_AUDITOR | Anthropic | OpenAI, DeepSeek |
| PERFORMANCE_OPTIMIZER | DeepSeek | Groq, Mistral |
| VULNERABILITY_SCANNER | Groq | Together, Mistral |

### Sophia Business Roles
| Role | Primary Provider | Reason |
|------|-----------------|--------|
| MARKET_ANALYST | Perplexity | Real-time market data |
| SALES_STRATEGIST | OpenAI | Advanced reasoning |
| CUSTOMER_SUCCESS | Anthropic | Empathetic responses |
| FINANCIAL_ANALYST | DeepSeek | Numerical analysis |

## Fallback Mechanism

The system automatically handles provider failures:

1. **Primary Attempt**: Uses the configured provider for the role
2. **Fallback Chain**: If primary fails, tries fallback providers in order
3. **Error Handling**: Returns error only if all providers fail

Example fallback chain:
```
OpenAI → Anthropic → DeepSeek → Error
```

## Vector Database Integration

### Supported Databases
- **Qdrant**: Primary vector store for agent profiles and knowledge
- **Weaviate**: Document storage and semantic search
- **Milvus**: Alternative vector database (optional)

### Collections/Classes
- `artemis_tactical` - Tactical agent profiles and operations
- `sophia_knowledge` - Business intelligence and insights
- `agent_memory` - Cross-system agent memory

## Caching Strategy

### Redis Cache
- **Key Format**: `domain:agent_id:request_hash`
- **TTL**: 3600 seconds (1 hour) default
- **Usage**: Caches completions and embeddings

### Mem0 Memory
- **Purpose**: Long-term agent memory and learning
- **Storage**: Uses Qdrant as backend
- **Access**: Per-agent memory retrieval

## Monitoring & Health Checks

### Health Check Endpoint

```python
# Check all systems
artemis_factory = get_portkey_artemis_factory()
health = await artemis_factory.health_check()

# Returns:
{
    "status": "operational",
    "portkey_providers": {
        "openai": true,
        "anthropic": true,
        "deepseek": true
    },
    "vector_databases": {
        "qdrant": true,
        "weaviate": false,
        "redis": true
    }
}
```

### Metrics Tracked
- Provider availability
- Response times
- Fallback frequency
- Cache hit rates
- Vector database performance

## Troubleshooting

### Common Issues

1. **"No virtual key found"**
   - Ensure virtual key is set in `.env`
   - Check Portkey dashboard for correct key

2. **Provider failures**
   - Verify API limits not exceeded
   - Check provider status page
   - Review fallback configuration

3. **Vector DB connection issues**
   - Verify connection strings
   - Check network connectivity
   - Ensure proper authentication

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Security Considerations

1. **Never commit `.env` files** with real keys
2. **Use `.env.template`** for key structure
3. **Rotate keys regularly** through Portkey dashboard
4. **Monitor usage** for anomalies
5. **Implement rate limiting** at application level

## Performance Optimization

### Best Practices
1. **Use appropriate models** for tasks (GPT-3.5 for simple, GPT-4 for complex)
2. **Enable caching** for repeated queries
3. **Batch embeddings** when possible
4. **Use streaming** for long responses
5. **Monitor token usage** to optimize costs

### Recommended Settings
```python
# Optimal for most use cases
MAX_RETRIES=3
REQUEST_TIMEOUT=60
CACHE_TTL=3600
ENABLE_FALLBACK=true
```

## Next Steps

1. **Production Deployment**
   - Set up monitoring dashboards
   - Configure alerts for failures
   - Implement rate limiting
   - Set up key rotation schedule

2. **Advanced Features**
   - Implement custom routing logic
   - Add A/B testing for providers
   - Build provider performance analytics
   - Create cost optimization strategies

3. **Integration Extensions**
   - Add more specialized agents
   - Implement multi-agent workflows
   - Build semantic caching layer
   - Create provider-specific optimizations

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review test results in `portkey_test_results_*.json`
3. Check Portkey dashboard for API status
4. Review logs for detailed error messages

---

*Last Updated: 2024*
*Version: 1.0.0*