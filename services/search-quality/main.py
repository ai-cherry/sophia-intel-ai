"""
Search Quality Service - Main FastAPI Application
Provides contextual bandit, RRF fusion, and cross-encoder reranking
"""
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional
import redis.asyncio as redis
from config.python_settings import settings_from_env
import structlog
# Import our search quality components
from contextual_bandit import (
    ProductionContextualBandit,
    ProviderContext,
    create_contextual_bandit,
)
from cross_encoder_reranking import (
    OptimizedCrossEncoderReranker,
    create_cross_encoder_reranker,
)
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from pydantic import BaseModel, Field
from reciprocal_rank_fusion import (
    OptimizedReciprocalRankFusion,
    ProviderResults,
    SearchResult,
    create_rrf_fusion,
)
# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
logger = structlog.get_logger()
# Prometheus metrics
REQUEST_COUNT = Counter(
    "search_quality_requests_total", "Total requests", ["endpoint", "method"]
)
REQUEST_DURATION = Histogram(
    "search_quality_request_duration_seconds", "Request duration", ["endpoint"]
)
ACTIVE_REQUESTS = Gauge("search_quality_active_requests", "Active requests")
BANDIT_SELECTIONS = Counter(
    "bandit_selections_total", "Bandit selections", ["provider"]
)
RRF_FUSIONS = Counter("rrf_fusions_total", "RRF fusions")
RERANKING_OPERATIONS = Counter("reranking_operations_total", "Reranking operations")
# Global components
bandit: Optional[ProductionContextualBandit] = None
rrf_fusion: Optional[OptimizedReciprocalRankFusion] = None
reranker: Optional[OptimizedCrossEncoderReranker] = None
redis_client: Optional[redis.Redis] = None
_settings = settings_from_env()
# Pydantic models
class ProviderContextRequest(BaseModel):
    query_length: int = Field(..., ge=0, le=10000)
    query_type: str = Field(..., regex="^(semantic|factual|news|code)$")
    time_of_day: float = Field(..., ge=0, le=24)
    recent_latency_p95: float = Field(..., ge=0)
    recent_error_rate: float = Field(..., ge=0, le=1)
    cost_per_request: float = Field(..., ge=0)
    provider_load: float = Field(..., ge=0, le=1)
    query_embedding_cluster: int = Field(..., ge=0, le=9)
    user_context: str = Field(default="general")
    urgency_level: float = Field(default=0.5, ge=0, le=1)
class BanditSelectionRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    context: ProviderContextRequest
    force_exploration: bool = Field(default=False)
class BanditRewardRequest(BaseModel):
    provider: str = Field(..., min_length=1)
    context: ProviderContextRequest
    latency_ms: float = Field(..., ge=0)
    success: bool
    cost_cents: float = Field(default=0, ge=0)
    quality_score: Optional[float] = Field(default=None, ge=0, le=1)
class SearchResultRequest(BaseModel):
    id: str = Field(default="")
    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)
    score: float = Field(..., ge=0, le=1)
    provider: str = Field(..., min_length=1)
    rank: int = Field(..., ge=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)
class ProviderResultsRequest(BaseModel):
    provider: str = Field(..., min_length=1)
    results: List[SearchResultRequest]
    total_results: int = Field(..., ge=0)
    latency_ms: float = Field(..., ge=0)
    cost_cents: float = Field(default=0, ge=0)
    quality_score: float = Field(default=1.0, ge=0, le=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)
class RRFFusionRequest(BaseModel):
    provider_results: List[ProviderResultsRequest]
    query: str = Field(default="")
    boost_recent: bool = Field(default=True)
    boost_quality: bool = Field(default=True)
class RerankingRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    results: List[Dict[str, Any]]
    preserve_top_k: int = Field(default=10, ge=0, le=100)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global bandit, rrf_fusion, reranker, redis_client
    logger.info("Starting Search Quality Service...")
    try:
        # Initialize Redis connection
        redis_client = redis.from_url(
            (_settings.REDIS_URL or os.getenv("REDIS_URL", "redis://redis:6379")),
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
        )
        # Test Redis connection
        await redis_client.ping()
        logger.info("Redis connection established")
        # Initialize search quality components
        providers = ["tavily", "serper", "brave", "exa"]
        # Initialize contextual bandit
        bandit = create_contextual_bandit(
            providers=providers, redis_client=redis_client, exploration_decay_rate=0.01
        )
        logger.info("Contextual bandit initialized")
        # Initialize RRF fusion
        rrf_fusion = create_rrf_fusion(
            k_value=60.0, max_results=50, enable_content_deduplication=True
        )
        logger.info("RRF fusion initialized")
        # Initialize cross-encoder reranker
        reranker = create_cross_encoder_reranker(
            redis_client=redis_client,
            model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
            batch_size=32,
            enable_caching=True,
        )
        logger.info("Cross-encoder reranker initialized")
        # Warm up models with sample data
        sample_queries = ["artificial intelligence", "machine learning", "data science"]
        sample_docs = [
            "AI is transforming industries",
            "ML algorithms improve over time",
        ]
        await reranker.warm_up_model(sample_queries, sample_docs)
        logger.info("Search Quality Service started successfully")
        yield
    except Exception as e:
        logger.error(f"Failed to start Search Quality Service: {e}")
        raise
    finally:
        # Cleanup
        logger.info("Shutting down Search Quality Service...")
        if bandit:
            await bandit.close()
        if reranker:
            await reranker.close()
        if redis_client:
            await redis_client.close()
        logger.info("Search Quality Service shutdown complete")
# Create FastAPI app
app = FastAPI(
    title="Sophia AI Search Quality Service",
    description="Advanced search optimization with contextual bandit, RRF fusion, and cross-encoder reranking",
    version="1.0.0",
    lifespan=lifespan,
)
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=(os.getenv("ALLOWED_ORIGINS", "*").split(",") if _settings.APP_ENV == "dev" else os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Dependency to get Redis client
async def get_redis() -> redis.Redis:
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")
    return redis_client
# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Redis connection
        if redis_client:
            await redis_client.ping()
        # Check component status
        components_status = {
            "bandit": bandit is not None,
            "rrf_fusion": rrf_fusion is not None,
            "reranker": reranker is not None and reranker.model is not None,
            "redis": redis_client is not None,
        }
        all_healthy = all(components_status.values())
        return {
            "status": "healthy" if all_healthy else "degraded",
            "components": components_status,
            "timestamp": time.time(),
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {e}")
# Contextual Bandit endpoints
@app.post("/bandit/select")
async def select_provider(request: BanditSelectionRequest):
    """Select optimal search provider using contextual bandit"""
    if not bandit:
        raise HTTPException(status_code=503, detail="Bandit not available")
    REQUEST_COUNT.labels(endpoint="bandit_select", method="POST").inc()
    ACTIVE_REQUESTS.inc()
    try:
        with REQUEST_DURATION.labels(endpoint="bandit_select").time():
            # Convert request to ProviderContext
            context = ProviderContext(**request.context.dict())
            # Select provider
            provider, confidence, metadata = await bandit.select_provider(
                context=context, force_exploration=request.force_exploration
            )
            # Update metrics
            BANDIT_SELECTIONS.labels(provider=provider).inc()
            return {
                "provider": provider,
                "confidence": confidence,
                "metadata": metadata,
                "query": request.query,
            }
    except Exception as e:
        logger.error(f"Provider selection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Selection failed: {e}")
    finally:
        ACTIVE_REQUESTS.dec()
@app.post("/bandit/reward")
async def update_reward(request: BanditRewardRequest):
    """Update bandit with reward signal"""
    if not bandit:
        raise HTTPException(status_code=503, detail="Bandit not available")
    REQUEST_COUNT.labels(endpoint="bandit_reward", method="POST").inc()
    try:
        # Convert request to ProviderContext
        context = ProviderContext(**request.context.dict())
        # Update reward
        await bandit.update_reward(
            provider=request.provider,
            context=context,
            latency_ms=request.latency_ms,
            success=request.success,
            cost_cents=request.cost_cents,
            quality_score=request.quality_score,
        )
        return {"status": "success", "provider": request.provider}
    except Exception as e:
        logger.error(f"Reward update failed: {e}")
        raise HTTPException(status_code=500, detail=f"Reward update failed: {e}")
@app.get("/bandit/metrics")
async def get_bandit_metrics():
    """Get bandit performance metrics"""
    if not bandit:
        raise HTTPException(status_code=503, detail="Bandit not available")
    try:
        metrics = bandit.get_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Failed to get bandit metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics retrieval failed: {e}")
# RRF Fusion endpoints
@app.post("/rrf/fuse")
async def fuse_results(request: RRFFusionRequest):
    """Fuse search results using Reciprocal Rank Fusion"""
    if not rrf_fusion:
        raise HTTPException(status_code=503, detail="RRF fusion not available")
    REQUEST_COUNT.labels(endpoint="rrf_fuse", method="POST").inc()
    ACTIVE_REQUESTS.inc()
    try:
        with REQUEST_DURATION.labels(endpoint="rrf_fuse").time():
            # Convert request to ProviderResults
            provider_results = []
            for pr in request.provider_results:
                # Convert SearchResultRequest to SearchResult
                results = []
                for sr in pr.results:
                    result = SearchResult(**sr.dict())
                    results.append(result)
                provider_result = ProviderResults(
                    provider=pr.provider,
                    results=results,
                    total_results=pr.total_results,
                    latency_ms=pr.latency_ms,
                    cost_cents=pr.cost_cents,
                    quality_score=pr.quality_score,
                    metadata=pr.metadata,
                )
                provider_results.append(provider_result)
            # Perform fusion
            fused_results, fusion_metadata = rrf_fusion.fuse_results(
                provider_results=provider_results,
                query=request.query,
                boost_recent=request.boost_recent,
                boost_quality=request.boost_quality,
            )
            # Update metrics
            RRF_FUSIONS.inc()
            # Convert results back to dict format
            results_dict = []
            for result in fused_results:
                result_dict = {
                    "id": result.id,
                    "title": result.title,
                    "content": result.content,
                    "url": result.url,
                    "score": result.score,
                    "provider": result.provider,
                    "rank": result.rank,
                    "metadata": result.metadata,
                }
                results_dict.append(result_dict)
            return {"results": results_dict, "metadata": fusion_metadata}
    except Exception as e:
        logger.error(f"RRF fusion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Fusion failed: {e}")
    finally:
        ACTIVE_REQUESTS.dec()
@app.get("/rrf/metrics")
async def get_rrf_metrics():
    """Get RRF fusion metrics"""
    if not rrf_fusion:
        raise HTTPException(status_code=503, detail="RRF fusion not available")
    try:
        metrics = rrf_fusion.get_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Failed to get RRF metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics retrieval failed: {e}")
# Cross-Encoder Reranking endpoints
@app.post("/rerank")
async def rerank_results(request: RerankingRequest):
    """Rerank search results using cross-encoder"""
    if not reranker:
        raise HTTPException(status_code=503, detail="Reranker not available")
    REQUEST_COUNT.labels(endpoint="rerank", method="POST").inc()
    ACTIVE_REQUESTS.inc()
    try:
        with REQUEST_DURATION.labels(endpoint="rerank").time():
            # Perform reranking
            reranked_results, reranking_metadata = await reranker.rerank_results(
                query=request.query,
                results=request.results,
                preserve_top_k=request.preserve_top_k,
            )
            # Update metrics
            RERANKING_OPERATIONS.inc()
            # Convert results to dict format
            results_dict = []
            for result in reranked_results:
                result_dict = {
                    "id": result.id,
                    "title": result.title,
                    "content": result.content,
                    "url": result.url,
                    "original_score": result.original_score,
                    "rerank_score": result.rerank_score,
                    "final_rank": result.final_rank,
                    "provider": result.provider,
                    "metadata": result.metadata,
                }
                results_dict.append(result_dict)
            return {"results": results_dict, "metadata": reranking_metadata}
    except Exception as e:
        logger.error(f"Reranking failed: {e}")
        raise HTTPException(status_code=500, detail=f"Reranking failed: {e}")
    finally:
        ACTIVE_REQUESTS.dec()
@app.get("/rerank/metrics")
async def get_reranking_metrics():
    """Get reranking performance metrics"""
    if not reranker:
        raise HTTPException(status_code=503, detail="Reranker not available")
    try:
        metrics = reranker.get_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Failed to get reranking metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics retrieval failed: {e}")
# Prometheus metrics endpoint
@app.get("/metrics")
async def get_prometheus_metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
# Combined pipeline endpoint
@app.post("/pipeline/search")
async def search_pipeline(
    query: str,
    providers: List[str],
    context: ProviderContextRequest,
    enable_reranking: bool = True,
    preserve_top_k: int = 10,
):
    """Complete search quality pipeline: bandit selection + RRF fusion + reranking"""
    if not all([bandit, rrf_fusion, reranker]):
        raise HTTPException(status_code=503, detail="Pipeline components not available")
    REQUEST_COUNT.labels(endpoint="search_pipeline", method="POST").inc()
    ACTIVE_REQUESTS.inc()
    try:
        with REQUEST_DURATION.labels(endpoint="search_pipeline").time():
            # Step 1: Provider selection (if not specified)
            if not providers:
                provider_context = ProviderContext(**context.dict())
                selected_provider, confidence, selection_metadata = (
                    await bandit.select_provider(context=provider_context)
                )
                providers = [selected_provider]
            # Step 2: Simulate search results (in real implementation, call actual search providers)
            # This is a placeholder - replace with actual search provider calls
            actual_results = []
            for i, provider in enumerate(providers):
                provider_result = ProviderResults(
                    provider=provider,
                    results=[
                        SearchResult(
                            id=f"{provider}_{j}",
                            title=f"Result {j} from {provider}",
                            content=f"Content for {query} from {provider}",
                            url=f"https://example.com/{provider}/{j}",
                            score=0.9 - (j * 0.1),
                            provider=provider,
                            rank=j + 1,
                        )
                        for j in range(5)
                    ],
                    total_results=5,
                    latency_ms=100 + (i * 50),
                    quality_score=0.8 + (i * 0.05),
                )
                actual_results.append(provider_result)
            # Step 3: RRF Fusion
            fused_results, fusion_metadata = rrf_fusion.fuse_results(
                provider_results=actual_results,
                query=query,
                boost_recent=True,
                boost_quality=True,
            )
            # Step 4: Cross-encoder reranking (if enabled)
            if enable_reranking:
                # Convert to dict format for reranker
                results_for_reranking = []
                for result in fused_results:
                    result_dict = {
                        "id": result.id,
                        "title": result.title,
                        "content": result.content,
                        "url": result.url,
                        "score": result.score,
                        "provider": result.provider,
                        "rank": result.rank,
                        "metadata": result.metadata,
                    }
                    results_for_reranking.append(result_dict)
                reranked_results, reranking_metadata = await reranker.rerank_results(
                    query=query,
                    results=results_for_reranking,
                    preserve_top_k=preserve_top_k,
                )
                # Convert back to dict format
                final_results = []
                for result in reranked_results:
                    result_dict = {
                        "id": result.id,
                        "title": result.title,
                        "content": result.content,
                        "url": result.url,
                        "original_score": result.original_score,
                        "rerank_score": result.rerank_score,
                        "final_rank": result.final_rank,
                        "provider": result.provider,
                        "metadata": result.metadata,
                    }
                    final_results.append(result_dict)
                pipeline_metadata = {
                    "fusion_metadata": fusion_metadata,
                    "reranking_metadata": reranking_metadata,
                    "reranking_enabled": True,
                }
            else:
                # Convert fused results to dict format
                final_results = []
                for result in fused_results:
                    result_dict = {
                        "id": result.id,
                        "title": result.title,
                        "content": result.content,
                        "url": result.url,
                        "score": result.score,
                        "provider": result.provider,
                        "rank": result.rank,
                        "metadata": result.metadata,
                    }
                    final_results.append(result_dict)
                pipeline_metadata = {
                    "fusion_metadata": fusion_metadata,
                    "reranking_enabled": False,
                }
            return {
                "query": query,
                "results": final_results,
                "metadata": pipeline_metadata,
            }
    except Exception as e:
        logger.error(f"Search pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {e}")
    finally:
        ACTIVE_REQUESTS.dec()
if __name__ == "__main__":
    import os
    import uvicorn
    bind_ip = os.getenv("BIND_IP", "0.0.0.0")
    uvicorn.run(app, host=bind_ip, port=8200)
