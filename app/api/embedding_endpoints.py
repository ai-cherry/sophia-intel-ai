"""
Embedding API Endpoints for Sophia Intel AI
Provides REST and WebSocket interfaces for embedding generation
"""

import logging
from typing import Any, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.contracts import APIResponse, create_api_response, create_error_response
from app.embeddings.agno_embedding_service import (
    AgnoEmbeddingRequest,
    AgnoEmbeddingService,
    EmbeddingModel,
)
from app.embeddings.portkey_integration import PortkeyGateway
from app.infrastructure.dependency_injection import get_container
from app.infrastructure.metrics.collector import MetricsCollector

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/embeddings", tags=["embeddings"])

# ============================================
# Request/Response Models
# ============================================


class CreateEmbeddingRequest(BaseModel):
    """Request to create embeddings"""

    text: Union[str, list[str]]
    model: Optional[str] = Field(None, description="Model to use (auto-selected if not provided)")
    use_case: str = Field("general", description="Use case: rag, search, clustering, etc.")
    language: str = Field("en", description="Language code")
    dimensions: Optional[int] = Field(None, description="Target dimensions")
    metadata: dict[str, Any] = Field(default_factory=dict)


class BatchEmbeddingRequest(BaseModel):
    """Request for batch embedding processing"""

    texts: list[str]
    model: Optional[str] = None
    use_case: str = "general"
    batch_size: int = Field(100, ge=1, le=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchRequest(BaseModel):
    """Request for semantic search"""

    query: str
    documents: list[str]
    top_k: int = Field(10, ge=1, le=100)
    model: Optional[str] = None


class ModelRecommendationRequest(BaseModel):
    """Request for model recommendations"""

    use_case: str
    max_tokens: Optional[int] = None
    language: str = "en"
    high_quality: bool = False
    low_cost: bool = False


class EmbeddingAPIResponse(BaseModel):
    """Response from embedding API"""

    embeddings: list[list[float]]
    model: str
    provider: str
    dimensions: int
    tokens_processed: int
    cost_estimate: float
    latency_ms: float
    cached: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchResult(BaseModel):
    """Search result with score"""

    index: int
    text: str
    score: float


class SearchAPIResponse(BaseModel):
    """Response from search API"""

    results: list[SearchResult]
    query_embedding: Optional[list[float]] = None
    model: str
    latency_ms: float


# ============================================
# Dependencies
# ============================================


async def get_embedding_service() -> AgnoEmbeddingService:
    """Get embedding service from DI container"""
    container = get_container()
    if not hasattr(container, "_embedding_service"):
        container._embedding_service = AgnoEmbeddingService()
    return container._embedding_service


async def get_portkey_gateway() -> PortkeyGateway:
    """Get Portkey gateway from DI container"""
    container = get_container()
    if not hasattr(container, "_portkey_gateway"):
        container._portkey_gateway = PortkeyGateway()
    return container._portkey_gateway


async def get_metrics_collector() -> MetricsCollector:
    """Get metrics collector"""
    container = get_container()
    return container.get_service(MetricsCollector)


# ============================================
# API Endpoints
# ============================================


@router.post("/create", response_model=APIResponse)
async def create_embedding(
    request: CreateEmbeddingRequest,
    service: AgnoEmbeddingService = Depends(get_embedding_service),
    metrics: MetricsCollector = Depends(get_metrics_collector),
) -> APIResponse:
    """
    Create embeddings for text using optimal model selection

    Features:
    - Auto-selects best model based on use case
    - Supports 6+ Together AI models
    - Caches results for efficiency
    - Tracks costs and performance
    """
    try:
        # Convert single text to list
        texts = [request.text] if isinstance(request.text, str) else request.text

        # Create embedding request
        embedding_request = AgnoEmbeddingRequest(
            texts=texts,
            model=EmbeddingModel(request.model) if request.model else None,
            use_case=request.use_case,
            language=request.language,
            max_length=request.dimensions,
            metadata=request.metadata,
        )

        # Generate embeddings
        response = await service.embed(embedding_request)

        # Track metrics
        await metrics.record_metric(
            name="embeddings_created",
            value=len(texts),
            tags={"model": response.model_used, "use_case": request.use_case},
        )

        # Create API response
        api_response = EmbeddingAPIResponse(
            embeddings=response.embeddings,
            model=response.model_used,
            provider=response.provider,
            dimensions=response.dimensions,
            tokens_processed=response.tokens_processed,
            cost_estimate=response.cost_estimate,
            latency_ms=response.latency_ms,
            cached=response.cached,
            metadata=response.metadata,
        )

        return create_api_response(
            data=api_response.model_dump(), message=f"Created {len(response.embeddings)} embeddings"
        )

    except Exception as e:
        logger.error(f"Failed to create embeddings: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/batch", response_model=APIResponse)
async def create_batch_embeddings(
    request: BatchEmbeddingRequest,
    service: AgnoEmbeddingService = Depends(get_embedding_service),
    metrics: MetricsCollector = Depends(get_metrics_collector),
) -> APIResponse:
    """
    Create embeddings for multiple texts with batching

    Optimized for:
    - Large document collections
    - Bulk indexing
    - Parallel processing
    """
    try:
        # Process in batches
        all_embeddings = []
        total_cost = 0.0
        total_tokens = 0

        for i in range(0, len(request.texts), request.batch_size):
            batch = request.texts[i : i + request.batch_size]

            # Create embedding request for batch
            embedding_request = AgnoEmbeddingRequest(
                texts=batch,
                model=EmbeddingModel(request.model) if request.model else None,
                use_case=request.use_case,
                metadata={**request.metadata, "batch_index": i // request.batch_size},
            )

            # Generate embeddings
            response = await service.embed(embedding_request)

            all_embeddings.extend(response.embeddings)
            total_cost += response.cost_estimate
            total_tokens += response.tokens_processed

        # Track metrics
        await metrics.record_metric(
            name="batch_embeddings_created",
            value=len(request.texts),
            tags={"batch_size": request.batch_size},
        )

        # Create response
        api_response = EmbeddingAPIResponse(
            embeddings=all_embeddings,
            model=response.model_used,
            provider=response.provider,
            dimensions=response.dimensions,
            tokens_processed=total_tokens,
            cost_estimate=total_cost,
            latency_ms=response.latency_ms,
            metadata=request.metadata,
        )

        return create_api_response(
            data=api_response.model_dump(),
            message=f"Created {len(all_embeddings)} embeddings in batches",
        )

    except Exception as e:
        logger.error(f"Failed to create batch embeddings: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/search", response_model=APIResponse)
async def semantic_search(
    request: SearchRequest, service: AgnoEmbeddingService = Depends(get_embedding_service)
) -> APIResponse:
    """
    Perform semantic search over documents

    Uses cosine similarity to find most relevant documents
    """
    try:
        import numpy as np

        # Generate query embedding
        query_request = AgnoEmbeddingRequest(
            texts=[request.query],
            model=EmbeddingModel(request.model) if request.model else None,
            use_case="search",
        )
        query_response = await service.embed(query_request)
        query_embedding = np.array(query_response.embeddings[0])

        # Generate document embeddings
        doc_request = AgnoEmbeddingRequest(
            texts=request.documents,
            model=EmbeddingModel(request.model) if request.model else None,
            use_case="search",
        )
        doc_response = await service.embed(doc_request)
        doc_embeddings = np.array(doc_response.embeddings)

        # Calculate similarities
        similarities = np.dot(doc_embeddings, query_embedding) / (
            np.linalg.norm(doc_embeddings, axis=1) * np.linalg.norm(query_embedding)
        )

        # Get top-k results
        top_indices = np.argsort(similarities)[-request.top_k :][::-1]

        results = [
            SearchResult(
                index=int(idx),
                text=(
                    request.documents[idx][:200] + "..."
                    if len(request.documents[idx]) > 200
                    else request.documents[idx]
                ),
                score=float(similarities[idx]),
            )
            for idx in top_indices
        ]

        # Create response
        api_response = SearchAPIResponse(
            results=results,
            query_embedding=query_embedding.tolist(),
            model=query_response.model_used,
            latency_ms=query_response.latency_ms + doc_response.latency_ms,
        )

        return create_api_response(
            data=api_response.model_dump(), message=f"Found {len(results)} relevant documents"
        )

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/models", response_model=APIResponse)
async def list_models(
    service: AgnoEmbeddingService = Depends(get_embedding_service),
) -> APIResponse:
    """
    List available embedding models

    Returns models with specifications and capabilities
    """
    from app.embeddings.agno_embedding_service import MODEL_REGISTRY

    models = []
    for model, spec in MODEL_REGISTRY.items():
        models.append(
            {
                "id": model.value,
                "provider": spec.provider.value,
                "dimensions": spec.dimensions,
                "max_tokens": spec.max_tokens,
                "mteb_score": spec.mteb_score,
                "strengths": spec.strengths,
                "use_cases": spec.use_cases,
                "cost_per_1k_tokens": spec.cost_per_1k_tokens,
                "multilingual": spec.multilingual,
            }
        )

    return create_api_response(
        data={"models": models}, message=f"Found {len(models)} available models"
    )


@router.post("/recommend", response_model=APIResponse)
async def recommend_model(
    request: ModelRecommendationRequest,
    service: AgnoEmbeddingService = Depends(get_embedding_service),
) -> APIResponse:
    """
    Get model recommendations based on requirements

    Analyzes use case and constraints to suggest optimal models
    """
    try:
        requirements = {
            "max_tokens": request.max_tokens,
            "language": request.language,
            "high_quality": request.high_quality,
            "low_cost": request.low_cost,
        }

        recommendations = service.get_model_recommendations(
            use_case=request.use_case, requirements=requirements
        )

        results = []
        for model, spec in recommendations:
            results.append(
                {
                    "model": model.value,
                    "provider": spec.provider.value,
                    "dimensions": spec.dimensions,
                    "max_tokens": spec.max_tokens,
                    "mteb_score": spec.mteb_score,
                    "strengths": spec.strengths,
                    "cost_per_1k_tokens": spec.cost_per_1k_tokens,
                    "reason": f"Best for {request.use_case} with {spec.strengths[0]}",
                }
            )

        return create_api_response(
            data={"recommendations": results}, message=f"Found {len(results)} recommended models"
        )

    except Exception as e:
        logger.error(f"Failed to get recommendations: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/stats", response_model=APIResponse)
async def get_embedding_stats(
    service: AgnoEmbeddingService = Depends(get_embedding_service),
    gateway: PortkeyGateway = Depends(get_portkey_gateway),
) -> APIResponse:
    """
    Get embedding service statistics

    Returns cache stats, provider status, and usage metrics
    """
    # Get provider status
    provider_status = gateway.get_provider_status()

    # Get cache stats (if available)
    cache_stats = {"size": len(service._embedding_cache), "providers": list(provider_status.keys())}

    return create_api_response(
        data={"cache": cache_stats, "providers": provider_status},
        message="Embedding service statistics",
    )


# ============================================
# WebSocket Support
# ============================================

from fastapi import WebSocket, WebSocketDisconnect


@router.websocket("/stream")
async def embedding_stream(
    websocket: WebSocket, service: AgnoEmbeddingService = Depends(get_embedding_service)
):
    """
    WebSocket endpoint for streaming embedding requests

    Useful for real-time applications and continuous processing
    """
    await websocket.accept()

    try:
        while True:
            # Receive request
            data = await websocket.receive_json()

            # Process embedding request
            request = AgnoEmbeddingRequest(
                texts=data.get("texts", []),
                use_case=data.get("use_case", "general"),
                language=data.get("language", "en"),
            )

            response = await service.embed(request)

            # Send response
            await websocket.send_json(
                {
                    "embeddings": response.embeddings,
                    "model": response.model_used,
                    "latency_ms": response.latency_ms,
                }
            )

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1000)


# ============================================
# Health Check
# ============================================


@router.get("/health", response_model=APIResponse)
async def health_check(
    service: AgnoEmbeddingService = Depends(get_embedding_service),
    gateway: PortkeyGateway = Depends(get_portkey_gateway),
    metrics: MetricsCollector = Depends(get_metrics_collector),
) -> APIResponse:
    """
    Comprehensive health check for embedding service
    Returns status, model availability, provider health, and performance metrics
    """
    from app.embeddings.agno_embedding_service import MODEL_REGISTRY

    try:
        # Initialize health data
        health_data = {"status": "initializing", "health_score": 0, "checks": {}, "errors": []}

        # 1. Check model registry
        try:
            available_models = list(MODEL_REGISTRY.keys())
            health_data["checks"]["model_registry"] = {
                "status": "healthy",
                "total_models": len(available_models),
                "models": [model.value for model in available_models[:5]],  # First 5 models
            }
        except Exception as e:
            health_data["checks"]["model_registry"] = {"status": "unhealthy", "error": str(e)}
            health_data["errors"].append(f"Model registry check failed: {e}")

        # 2. Check provider status via Portkey
        try:
            gateway.get_provider_status()
            active_providers = gateway.virtual_key_manager.get_active_providers()

            health_data["checks"]["providers"] = {
                "status": "healthy" if len(active_providers) > 0 else "unhealthy",
                "active_count": len(active_providers),
                "providers": active_providers,
            }
        except Exception as e:
            health_data["checks"]["providers"] = {"status": "unhealthy", "error": str(e)}
            health_data["errors"].append(f"Provider check failed: {e}")

        # 3. Test embedding generation
        try:
            test_request = AgnoEmbeddingRequest(texts=["health check test"], use_case="general")
            test_response = await service.embed(test_request)

            health_data["checks"]["embedding_generation"] = {
                "status": "healthy",
                "test_latency_ms": test_response.latency_ms,
                "model_used": test_response.model_used,
            }
        except Exception as e:
            health_data["checks"]["embedding_generation"] = {"status": "unhealthy", "error": str(e)}
            health_data["errors"].append(f"Embedding generation failed: {e}")

        # 4. Check cache status
        try:
            cache_size = (
                len(service._embedding_cache) if hasattr(service, "_embedding_cache") else 0
            )
            service_metrics = service.get_metrics()

            health_data["checks"]["cache"] = {
                "status": "healthy",
                "size": cache_size,
                "hit_rate": round(service_metrics.get("cache_hit_rate", 0), 2),
                "enabled": service_metrics.get("cache_enabled", True),
            }
        except Exception as e:
            health_data["checks"]["cache"] = {"status": "degraded", "error": str(e)}

        # 5. Get performance metrics
        try:
            service_metrics = service.get_metrics()
            health_data["performance_metrics"] = {
                "total_embeddings": service_metrics.get("total_embeddings", 0),
                "avg_latency_ms": round(service_metrics.get("avg_latency_ms", 0), 2),
                "total_cost": round(service_metrics.get("total_cost", 0), 4),
                "cache_hit_rate": round(service_metrics.get("cache_hit_rate", 0), 2),
            }
        except Exception as e:
            health_data["performance_metrics"] = {"error": str(e)}

        # Calculate health score (0-100)
        health_score = 100
        critical_checks = ["model_registry", "providers", "embedding_generation"]

        for check_name in critical_checks:
            if check_name in health_data["checks"]:
                if health_data["checks"][check_name]["status"] == "unhealthy":
                    health_score -= 30
                elif health_data["checks"][check_name]["status"] == "degraded":
                    health_score -= 15

        # Deduct for performance issues
        if health_data.get("performance_metrics", {}).get("avg_latency_ms", 0) > 200:
            health_score -= 10

        # Determine overall status
        if health_score >= 80:
            health_data["status"] = "healthy"
        elif health_score >= 50:
            health_data["status"] = "degraded"
        else:
            health_data["status"] = "unhealthy"

        health_data["health_score"] = max(0, health_score)

        # Add version info
        health_data["version"] = "2.0.0"  # Agno AgentOS embedding version
        health_data["implementation"] = "agno"

        # Record health check metric
        await metrics.record_metric(
            name="health_check",
            value=1,
            tags={"status": health_data["status"], "score": str(health_data["health_score"])},
        )

        # Return appropriate response based on status
        if health_data["status"] == "unhealthy":
            return create_error_response(
                error="Service is unhealthy",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                details=health_data,
            )

        return create_api_response(
            data=health_data,
            message=f"Embedding service is {health_data['status']} (score: {health_data['health_score']})",
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return create_error_response(
            error=str(e),
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"status": "unhealthy", "error": str(e)},
        )
