# ADR-004: Agno AgentOS Embedding Integration

## Status

Accepted

## Context

The existing embedding infrastructure had several limitations:

- Multiple inconsistent embedding implementations
- No unified gateway for providers
- Lack of model selection intelligence
- Missing cost optimization
- No support for Together AI's best models

## Decision

Implement a production-ready embedding service following Agno AgentOS patterns with:

1. **Unified Portkey Gateway**: Single interface for all providers
2. **Virtual Key Management**: Secure API key handling
3. **Intelligent Model Selection**: Auto-select best model for use case
4. **Together AI Integration**: Support for BAAI, Alibaba, and other top models
5. **Cost Optimization**: Track and optimize embedding costs
6. **Production Features**: Caching, retries, fallbacks, observability

## Architecture

### Components

#### 1. AgnoEmbeddingService

- Core service implementing Agno patterns
- Model registry with specifications
- Intelligent model selection
- Cache management
- Agent/swarm integration

#### 2. PortkeyGateway

- Unified gateway for all providers
- Virtual key management
- Request/response wrapping
- Provider failover
- Cost tracking

#### 3. Embedding API

- REST endpoints for embedding operations
- WebSocket support for streaming
- Batch processing
- Semantic search
- Model recommendations

### Model Selection Strategy

| Use Case     | Model Selection                 | Rationale                           |
| ------------ | ------------------------------- | ----------------------------------- |
| RAG          | BAAI/bge-large-en-v1.5          | MTEB 64.23, optimized for retrieval |
| Long Context | Alibaba-NLP/gte-modernbert-base | 8K tokens, code retrieval           |
| Ultra-Long   | togethercomputer/m2-bert-32k    | 32K tokens for books/legal          |
| Multilingual | intfloat/e5-large-instruct      | 100+ languages, instruct mode       |
| Fast Search  | BAAI/bge-base-en-v1.5           | Lower latency, good accuracy        |

### Best Practices Implementation

```python
# Agno SDK Pattern
from agno.agent import Agent
from agno.models.openai import OpenAIEmbedding

# Direct Together usage
embedder = TogetherEmbedding(
    id="BAAI/bge-large-en-v1.5",
    api_key="your_together_key"
)

# Via Portkey with virtual key
embedder = OpenAIEmbedding(
    id="BAAI/bge-large-en-v1.5",
    base_url="https://api.portkey.ai/v1",
    api_key="portkey_key",
    extra_body={
        "portkey_config": {
            "provider": "together",
            "virtual_key": "together_virtual_key"
        }
    }
)

# In agent for RAG
agent = Agent(
    embedding_model=embedder,
    extra_body=extra_body
)
```

## Performance Characteristics

### Model Benchmarks (MTEB Scores)

- **intfloat/e5-large-instruct**: 68.32 (multilingual)
- **Alibaba-NLP/gte-modernbert**: 64.38 (general)
- **BAAI/bge-large-en-v1.5**: 64.23 (English)
- **BAAI/bge-base-en-v1.5**: 63.0 (fast)
- **togethercomputer/m2-bert**: 60.0 (long context)

### Cost Analysis

- Together AI: ~$0.0001/1K tokens
- OpenAI: ~$0.00013/1K tokens
- Voyage: ~$0.00015/1K tokens
- Cost savings: 30-50% using Together AI

### Latency Targets

- Cache hit: <5ms
- Together AI: <50ms
- OpenAI: <100ms
- Batch (100 texts): <500ms

## Integration Points

### 1. Memory System

```python
# app/memory/unified_memory_store.py
response = await embedding_service.create_agent_embeddings(
    agent_id="agent_123",
    context="Memory content",
    memory_type="semantic"
)
```

### 2. RAG Pipeline

```python
# app/infrastructure/langgraph/rag_pipeline.py
response = await embedding_service.create_swarm_embeddings(
    swarm_id="swarm_456",
    documents=documents,
    task_type="retrieval"
)
```

### 3. Vector Search

```python
# app/weaviate/weaviate_client.py
embeddings = await embedding_service.embed(
    EmbeddingRequest(
        texts=texts,
        use_case="search"
    )
)
```

## Migration Strategy

### Phase 1: Add New Service (Complete)

- ✅ Create AgnoEmbeddingService
- ✅ Implement PortkeyGateway
- ✅ Add API endpoints

### Phase 2: Update Existing Code

- [ ] Update memory systems to use new service
- [ ] Migrate RAG pipeline
- [ ] Update vector search implementations
- [ ] Add feature flags for gradual rollout

### Phase 3: Deprecate Old Code

- [ ] Remove dual_tier_embeddings.py
- [ ] Remove embedding_pipeline.py (keep utilities)
- [ ] Clean up duplicate implementations

## Monitoring

### Metrics to Track

- Embedding generation latency
- Cache hit rate
- Model usage distribution
- Cost per embedding
- Provider availability

### Alerts

- Latency > 200ms (P95)
- Cache hit rate < 50%
- Provider failures > 1%
- Cost spike > 20%

## Security Considerations

1. **Virtual Keys**: Never expose real API keys
2. **Rate Limiting**: Implement per-user limits
3. **Cost Controls**: Set monthly quotas
4. **Audit Logging**: Track all embedding requests
5. **Data Privacy**: No PII in embeddings

## Consequences

### Positive

- Unified embedding interface
- 30-50% cost reduction
- Better model selection
- Production-ready features
- Agno ecosystem compatibility

### Negative

- Additional complexity
- Dependency on Portkey
- Migration effort required
- Learning curve for team

## References

- [Agno AgentOS Documentation](https://docs.agno.dev)
- [Portkey AI Gateway](https://portkey.ai)
- [Together AI Models](https://together.ai/models)
- [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard)
