## Sophia Intel AI API Endpoints

### Embedding Endpoints
#### Create Embedding
```bash
curl -X POST http://localhost:8005/embeddings/create \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, world!",
    "model": "text-embedding-ada-002"
  }'
```

#### Batch Embeddings
```bash
curl -X POST http://localhost:8005/embeddings/batch \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["Hello", "world"],
    "model": "text-embedding-ada-002"
  }'
```

#### Search Embeddings
```bash
curl -X GET "http://localhost:8005/embeddings/search?query=hello&top_k=5"
```

### Cost Dashboard Endpoints
#### Cost Summary
```bash
curl -X GET "http://localhost:8005/costs/summary?days=30"
```

#### Daily Cost Breakdown
```bash
curl -X GET "http://localhost:8005/costs/daily?days=30"
```

#### Model Cost Analysis
```bash
curl -X GET "http://localhost:8005/costs/models?limit=10"
```

### Repository API
#### Get Repository Tree
```bash
curl -X GET "http://localhost:8005/api/repo/tree?path=app&depth=3"
```

#### Search Repository
```bash
curl -X GET "http://localhost:8005/api/repo/search?query=embedding"
```

### Memory API
#### Store Memory
```bash
curl -X POST "http://localhost:8005/api/memory/store" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session_123",
    "messages": [{"role": "user", "content": "Hello"}],
    "metadata": {"source": "roo"}
  }'
```

#### Retrieve Memory
```bash
curl -X GET "http://localhost:8005/api/memory/retrieve/session_123?last_n=5"
```

### Hub Controller
Access the unified hub at: http://localhost:8005/hub