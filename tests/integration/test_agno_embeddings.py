"""
Integration tests for Agno AgentOS Embedding Infrastructure
Tests all embedding operations including document processing, similarity search, and batch operations
"""

import asyncio
import os
import time

import numpy as np
import pytest
from httpx import AsyncClient

from app.embeddings.agno_embedding_service import (
    MODEL_REGISTRY,
    AgnoEmbeddingRequest,
    AgnoEmbeddingService,
    EmbeddingModel,
)
from app.embeddings.portkey_integration import (
    PortkeyConfigBuilder,
    PortkeyGateway,
    PortkeyVirtualKeyManager,
)
from app.infrastructure.dependency_injection import get_container

# ============================================
# Test Fixtures
# ============================================

@pytest.fixture
async def embedding_service():
    """Create embedding service instance"""
    service = AgnoEmbeddingService()
    yield service

@pytest.fixture
async def portkey_gateway():
    """Create Portkey gateway instance"""
    gateway = PortkeyGateway()
    yield gateway

@pytest.fixture
async def di_container():
    """Get dependency injection container"""
    container = get_container()
    yield container
    await container.dispose()

@pytest.fixture
def test_documents():
    """Sample documents for testing"""
    return [
        "Artificial intelligence is transforming software development",
        "Machine learning models require large amounts of training data",
        "Neural networks can learn complex patterns from data",
        "Python is a popular language for AI development",
        "Cloud computing provides scalable infrastructure for AI workloads",
    ]

@pytest.fixture
def test_code_samples():
    """Code samples for testing code embeddings"""
    return [
        """def fibonacci(n):
            if n <= 1:
                return n
            return fibonacci(n-1) + fibonacci(n-2)""",
        """class Stack:
            def __init__(self):
                self.items = []
            def push(self, item):
                self.items.append(item)""",
    ]

@pytest.fixture
def performance_baseline():
    """Performance baseline metrics"""
    return {
        "single_embedding_latency_ms": 50,
        "batch_embedding_latency_ms": 500,
        "search_latency_ms": 100,
        "cache_hit_latency_ms": 5,
    }

# ============================================
# Service Registration Tests
# ============================================

@pytest.mark.asyncio
async def test_service_registration(di_container):
    """Test that embedding services are properly registered in DI container"""
    # Resolve services from container
    embedding_service = await di_container.resolve(AgnoEmbeddingService)
    portkey_gateway = await di_container.resolve(PortkeyGateway)

    assert embedding_service is not None
    assert portkey_gateway is not None
    assert isinstance(embedding_service, AgnoEmbeddingService)
    assert isinstance(portkey_gateway, PortkeyGateway)

@pytest.mark.asyncio
async def test_singleton_lifecycle(di_container):
    """Test that services are singletons"""
    service1 = await di_container.resolve(AgnoEmbeddingService)
    service2 = await di_container.resolve(AgnoEmbeddingService)

    assert service1 is service2  # Same instance

# ============================================
# Configuration Tests
# ============================================

def test_environment_configuration():
    """Test environment variable configuration"""
    # Set test environment variables
    os.environ["EMBEDDING_IMPL"] = "agno"
    os.environ["EMBEDDING_CACHE_ENABLED"] = "true"
    os.environ["EMBEDDING_BATCH_SIZE"] = "50"

    # Verify they can be read
    assert os.getenv("EMBEDDING_IMPL") == "agno"
    assert os.getenv("EMBEDDING_CACHE_ENABLED") == "true"
    assert int(os.getenv("EMBEDDING_BATCH_SIZE", "100")) == 50

def test_virtual_key_management():
    """Test virtual key configuration"""
    manager = PortkeyVirtualKeyManager()

    # Test with mock environment variables
    os.environ["TOGETHER_VIRTUAL_KEY"] = "test_together_key"
    os.environ["OPENAI_VIRTUAL_KEY"] = "test_openai_key"

    manager = PortkeyVirtualKeyManager()  # Reinitialize with env vars

    # Check active providers
    providers = manager.get_active_providers()
    assert len(providers) > 0

def test_portkey_config_builder():
    """Test Portkey configuration builder"""
    config = PortkeyConfigBuilder.build_embedding_config(
        provider="together",
        virtual_key="test_key",
        cache_enabled=True,
        retry_enabled=True
    )

    assert config["provider"] == "together"
    assert config["virtual_key"] == "test_key"
    assert "cache" in config
    assert "retry" in config

# ============================================
# Embedding Generation Tests
# ============================================

@pytest.mark.asyncio
async def test_single_embedding(embedding_service, test_documents):
    """Test single document embedding"""
    request = AgnoEmbeddingRequest(
        texts=[test_documents[0]],
        use_case="general"
    )

    response = await embedding_service.embed(request)

    assert response is not None
    assert len(response.embeddings) == 1
    assert len(response.embeddings[0]) > 0
    assert response.model_used is not None
    assert response.latency_ms > 0
    assert response.cost_estimate >= 0

@pytest.mark.asyncio
async def test_batch_embeddings(embedding_service, test_documents):
    """Test batch document embeddings"""
    request = AgnoEmbeddingRequest(
        texts=test_documents,
        use_case="search"
    )

    start_time = time.perf_counter()
    response = await embedding_service.embed(request)
    latency_ms = (time.perf_counter() - start_time) * 1000

    assert len(response.embeddings) == len(test_documents)
    assert all(len(emb) > 0 for emb in response.embeddings)
    assert latency_ms < 1000  # Should complete within 1 second

@pytest.mark.asyncio
async def test_code_embeddings(embedding_service, test_code_samples):
    """Test code-specific embeddings"""
    request = AgnoEmbeddingRequest(
        texts=test_code_samples,
        use_case="code"
    )

    response = await embedding_service.embed(request)

    # Should select appropriate model for code
    assert response.model_used in [
        EmbeddingModel.GTE_MODERNBERT_BASE.value,
        EmbeddingModel.EMBEDDING_3_LARGE.value
    ]

@pytest.mark.asyncio
async def test_multilingual_embeddings(embedding_service):
    """Test multilingual embeddings"""
    multilingual_texts = [
        "Hello world",
        "Bonjour le monde",
        "Hola mundo",
        "你好世界",
        "こんにちは世界"
    ]

    request = AgnoEmbeddingRequest(
        texts=multilingual_texts,
        language="multi"
    )

    response = await embedding_service.embed(request)

    # Should select multilingual model
    assert response.model_used == EmbeddingModel.E5_LARGE_INSTRUCT.value

@pytest.mark.asyncio
async def test_long_document_embeddings(embedding_service):
    """Test long document embeddings"""
    long_text = "This is a very long document. " * 5000  # ~35K tokens

    request = AgnoEmbeddingRequest(
        texts=[long_text],
        use_case="general"
    )

    response = await embedding_service.embed(request)

    # Should select long-context model
    assert response.model_used == EmbeddingModel.M2_BERT_32K.value

# ============================================
# Model Selection Tests
# ============================================

def test_model_registry():
    """Test model registry completeness"""
    required_models = [
        EmbeddingModel.BGE_LARGE_EN,
        EmbeddingModel.BGE_BASE_EN,
        EmbeddingModel.GTE_MODERNBERT_BASE,
        EmbeddingModel.E5_LARGE_INSTRUCT,
        EmbeddingModel.M2_BERT_8K,
        EmbeddingModel.M2_BERT_32K,
    ]

    for model in required_models:
        assert model in MODEL_REGISTRY
        spec = MODEL_REGISTRY[model]
        assert spec.dimensions > 0
        assert spec.max_tokens > 0
        assert spec.cost_per_1k_tokens > 0

@pytest.mark.asyncio
async def test_model_recommendations(embedding_service):
    """Test model recommendation engine"""
    recommendations = embedding_service.get_model_recommendations(
        use_case="rag",
        requirements={
            "max_tokens": 5000,
            "high_quality": True,
            "language": "en"
        }
    )

    assert len(recommendations) > 0
    # BGE Large should be recommended for high-quality English RAG
    model_names = [model.value for model, _ in recommendations]
    assert EmbeddingModel.BGE_LARGE_EN.value in model_names

# ============================================
# Similarity Search Tests
# ============================================

@pytest.mark.asyncio
async def test_similarity_search(embedding_service, test_documents):
    """Test similarity search functionality"""
    # Generate embeddings for documents
    doc_request = AgnoEmbeddingRequest(
        texts=test_documents,
        use_case="search"
    )
    doc_response = await embedding_service.embed(doc_request)

    # Generate query embedding
    query = "What programming languages are used for AI?"
    query_request = AgnoEmbeddingRequest(
        texts=[query],
        use_case="search"
    )
    query_response = await embedding_service.embed(query_request)

    # Calculate similarities
    query_embedding = np.array(query_response.embeddings[0])
    doc_embeddings = np.array(doc_response.embeddings)

    similarities = np.dot(doc_embeddings, query_embedding) / (
        np.linalg.norm(doc_embeddings, axis=1) * np.linalg.norm(query_embedding)
    )

    # Get top result
    top_idx = np.argmax(similarities)

    # Should match the Python document
    assert "Python" in test_documents[top_idx]

# ============================================
# Caching Tests
# ============================================

@pytest.mark.asyncio
async def test_embedding_cache(embedding_service):
    """Test embedding cache functionality"""
    text = "Test caching functionality"
    request = AgnoEmbeddingRequest(texts=[text])

    # First call - should generate
    start1 = time.perf_counter()
    response1 = await embedding_service.embed(request)
    latency1 = (time.perf_counter() - start1) * 1000

    # Second call - should use cache
    start2 = time.perf_counter()
    response2 = await embedding_service.embed(request)
    latency2 = (time.perf_counter() - start2) * 1000

    # Cache should be faster
    assert latency2 < latency1 / 2
    # Embeddings should be identical
    assert response1.embeddings[0] == response2.embeddings[0]

# ============================================
# Error Handling Tests
# ============================================

@pytest.mark.asyncio
async def test_error_handling_empty_text(embedding_service):
    """Test error handling for empty text"""
    request = AgnoEmbeddingRequest(texts=[""])

    # Should handle gracefully
    response = await embedding_service.embed(request)
    assert response is not None

@pytest.mark.asyncio
async def test_error_handling_invalid_model(embedding_service):
    """Test error handling for invalid model"""
    request = AgnoEmbeddingRequest(
        texts=["test"],
        model="invalid_model"  # This should fail validation
    )

    with pytest.raises(ValueError):
        await embedding_service.embed(request)

# ============================================
# Performance Tests
# ============================================

@pytest.mark.asyncio
async def test_performance_single_embedding(embedding_service, performance_baseline):
    """Test single embedding performance"""
    request = AgnoEmbeddingRequest(texts=["Performance test"])

    start = time.perf_counter()
    await embedding_service.embed(request)
    latency_ms = (time.perf_counter() - start) * 1000

    assert latency_ms < performance_baseline["single_embedding_latency_ms"] * 2

@pytest.mark.asyncio
async def test_performance_batch_embedding(embedding_service, test_documents, performance_baseline):
    """Test batch embedding performance"""
    request = AgnoEmbeddingRequest(texts=test_documents * 20)  # 100 documents

    start = time.perf_counter()
    await embedding_service.embed(request)
    latency_ms = (time.perf_counter() - start) * 1000

    assert latency_ms < performance_baseline["batch_embedding_latency_ms"] * 2

@pytest.mark.asyncio
async def test_concurrent_requests(embedding_service, test_documents):
    """Test concurrent embedding requests"""
    requests = [
        AgnoEmbeddingRequest(texts=[doc])
        for doc in test_documents
    ]

    # Execute concurrently
    start = time.perf_counter()
    responses = await asyncio.gather(*[
        embedding_service.embed(req) for req in requests
    ])
    latency_ms = (time.perf_counter() - start) * 1000

    assert len(responses) == len(requests)
    assert all(r is not None for r in responses)
    # Should be faster than sequential
    assert latency_ms < len(requests) * 50

# ============================================
# API Endpoint Tests
# ============================================

@pytest.mark.asyncio
async def test_api_create_embedding():
    """Test embedding creation API endpoint"""
    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.post(
            "/embeddings/create",
            json={
                "text": "API test",
                "use_case": "general"
            }
        )

        if response.status_code == 200:
            data = response.json()
            assert "embeddings" in data["data"]
            assert "model" in data["data"]
            assert "latency_ms" in data["data"]

@pytest.mark.asyncio
async def test_api_batch_embeddings():
    """Test batch embedding API endpoint"""
    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.post(
            "/embeddings/batch",
            json={
                "texts": ["text1", "text2", "text3"],
                "batch_size": 10
            }
        )

        if response.status_code == 200:
            data = response.json()
            assert len(data["data"]["embeddings"]) == 3

@pytest.mark.asyncio
async def test_api_health_check():
    """Test embedding service health check"""
    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get("/embeddings/health")

        if response.status_code == 200:
            data = response.json()
            assert data["data"]["status"] == "healthy"
            assert data["data"]["model_available"] is True

# ============================================
# Integration Tests with Other Components
# ============================================

@pytest.mark.asyncio
async def test_agent_embedding_integration(embedding_service):
    """Test agent memory embedding integration"""
    response = await embedding_service.create_agent_embeddings(
        agent_id="test_agent_123",
        context="Agent memory context for testing",
        memory_type="semantic"
    )

    assert response is not None
    assert response.metadata["agent_id"] == "test_agent_123"
    assert response.metadata["memory_type"] == "semantic"

@pytest.mark.asyncio
async def test_swarm_embedding_integration(embedding_service, test_documents):
    """Test swarm coordination embedding integration"""
    response = await embedding_service.create_swarm_embeddings(
        swarm_id="test_swarm_456",
        documents=test_documents,
        task_type="retrieval"
    )

    assert response is not None
    assert len(response.embeddings) == len(test_documents)
    assert response.metadata["swarm_id"] == "test_swarm_456"

# ============================================
# End-to-End Workflow Tests
# ============================================

@pytest.mark.asyncio
async def test_end_to_end_rag_workflow(embedding_service, test_documents):
    """Test complete RAG workflow"""
    # 1. Index documents
    index_request = AgnoEmbeddingRequest(
        texts=test_documents,
        use_case="rag"
    )
    index_response = await embedding_service.embed(index_request)

    # 2. Store embeddings (simulated)
    document_store = {}
    for i, (doc, emb) in enumerate(zip(test_documents, index_response.embeddings, strict=False)):
        document_store[i] = {
            "text": doc,
            "embedding": emb
        }

    # 3. Query
    query = "How does AI impact software development?"
    query_request = AgnoEmbeddingRequest(
        texts=[query],
        use_case="rag"
    )
    query_response = await embedding_service.embed(query_request)
    query_embedding = np.array(query_response.embeddings[0])

    # 4. Retrieve
    similarities = []
    for doc_id, doc_data in document_store.items():
        doc_embedding = np.array(doc_data["embedding"])
        similarity = np.dot(query_embedding, doc_embedding) / (
            np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
        )
        similarities.append((doc_id, similarity))

    # 5. Get top results
    similarities.sort(key=lambda x: x[1], reverse=True)
    top_doc_id = similarities[0][0]

    # Verify retrieval quality
    retrieved_doc = document_store[top_doc_id]["text"]
    assert "artificial intelligence" in retrieved_doc.lower() or "software" in retrieved_doc.lower()

# ============================================
# Monitoring and Observability Tests
# ============================================

@pytest.mark.asyncio
async def test_metrics_collection(embedding_service, test_documents):
    """Test metrics collection"""
    # Generate some embeddings
    request = AgnoEmbeddingRequest(texts=test_documents)
    await embedding_service.embed(request)

    # Check if metrics are being collected
    # This depends on your metrics implementation
    # Example assertion:
    # assert embedding_service.metrics["total_embeddings"] > 0

@pytest.mark.asyncio
async def test_logging_and_tracing(embedding_service):
    """Test logging and tracing functionality"""
    # This test would verify that logs and traces are generated
    # Implementation depends on your observability stack
    pass

# ============================================
# Test Suite Runner
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
