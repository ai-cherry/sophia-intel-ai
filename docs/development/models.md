# Approved AI Models

This document lists the approved and tested AI models available in the Sophia Intel platform.

## Overview

The AI Router has been configured to use only approved models that have been tested and validated for production use. This ensures reliability, cost-effectiveness, and consistent performance.

## Approved Models

### OpenAI Models

#### GPT-4o
- **Model**: `gpt-4o`
- **Provider**: OpenAI
- **Cost**: $0.03 per 1K tokens
- **Context Window**: 128,000 tokens
- **Specialties**: Code Generation, Reasoning, Analysis
- **Function Calling**: ✅ Yes
- **Structured Output**: ✅ Yes
- **Rate Limit**: 10,000 RPM

**Use Cases**:
- Complex code generation and review
- Advanced reasoning tasks
- Data analysis and insights
- Technical documentation

#### GPT-4o Mini
- **Model**: `gpt-4o-mini`
- **Provider**: OpenAI
- **Cost**: $0.0015 per 1K tokens
- **Context Window**: 128,000 tokens
- **Specialties**: General Chat, Documentation
- **Function Calling**: ✅ Yes
- **Structured Output**: ✅ Yes
- **Rate Limit**: 30,000 RPM

**Use Cases**:
- General conversation and chat
- Documentation generation
- Simple code tasks
- Cost-effective operations

## Model Selection Strategy

The AI Router automatically selects the optimal model based on:

1. **Task Type**: Different models excel at different tasks
2. **Cost Preference**: Balance between cost and performance
3. **Quality Requirements**: Higher quality tasks use premium models
4. **Latency Requirements**: Fast models for real-time applications
5. **Context Length**: Models with appropriate context windows

## Cost Analysis

| Model | Cost per 1K tokens | Quality Score | Best Use Case |
|-------|-------------------|---------------|---------------|
| gpt-4o | $0.03 | 0.95 | Complex reasoning, code generation |
| gpt-4o-mini | $0.0015 | 0.88 | General chat, documentation |

## Performance Characteristics

### Response Times
- **gpt-4o**: ~2.5 seconds average
- **gpt-4o-mini**: ~1.8 seconds average

### Quality Scores
Quality scores are based on comprehensive testing across various task types:
- **gpt-4o**: 95% quality score
- **gpt-4o-mini**: 88% quality score

## Integration

Models are accessed through the AI Router which handles:
- Automatic model selection
- Load balancing
- Fallback strategies
- Cost optimization
- Performance monitoring

## Configuration

Models are configured in `mcp_servers/ai_router.py` with the following parameters:
- Provider and model name
- Cost per token
- Performance characteristics
- Supported features
- Rate limits

## Monitoring

The platform tracks:
- Model usage statistics
- Cost per request
- Response times
- Error rates
- Quality metrics

## Future Additions

Additional models may be approved and added based on:
- Performance testing results
- Cost-benefit analysis
- Specific use case requirements
- Community feedback

## API Usage

```python
from mcp_servers.ai_router import AIRouter, TaskRequest, TaskType

router = AIRouter()

# The router will automatically select the best model
request = TaskRequest(
    prompt="Generate a Python function to calculate fibonacci numbers",
    task_type=TaskType.CODE_GENERATION,
    quality_requirement="high"
)

decision = await router.route_request(request)
response = await router.execute_task(request, decision)
```

## Support

For questions about model selection or to request additional models:
- Create an issue in the GitHub repository
- Contact the development team
- Review performance metrics in the dashboard

---

**Last Updated**: August 2025  
**Models Count**: 2 approved models  
**Total Providers**: 1 (OpenAI)

