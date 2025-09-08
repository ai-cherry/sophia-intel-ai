"""
Neural API Gateway - Intelligent Routing for Sophia AI
Handles request classification and routing to appropriate neural services
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import httpx
import redis.asyncio as redis
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import json
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Metrics
REQUEST_COUNT = Counter('neural_gateway_requests_total', 'Total requests', ['endpoint', 'method'])
REQUEST_DURATION = Histogram('neural_gateway_request_duration_seconds', 'Request duration')
ACTIVE_CONNECTIONS = Gauge('neural_gateway_active_connections', 'Active connections')
CACHE_HITS = Counter('neural_gateway_cache_hits_total', 'Cache hits')
CACHE_MISSES = Counter('neural_gateway_cache_misses_total', 'Cache misses')
CB_STATE = Gauge('neural_gateway_cb_state', 'Circuit breaker state (0=closed,1=open,2=half_open)', ['target'])
CB_OPEN_TOTAL = Counter('neural_gateway_cb_open_total', 'Times circuit opened', ['target'])
CB_FAILURE_TOTAL = Counter('neural_gateway_cb_failure_total', 'Failures recorded', ['target'])
CB_SUCCESS_TOTAL = Counter('neural_gateway_cb_success_total', 'Successes recorded', ['target'])

# Global clients
http_client: Optional[httpx.AsyncClient] = None
cache_client: Optional[redis.Redis] = None

class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., description="User message")
    context: Optional[List[str]] = Field(None, description="Conversation context")
    stream: bool = Field(False, description="Stream response")
    temperature: float = Field(0.6, ge=0.0, le=2.0)
    max_tokens: int = Field(4096, ge=1, le=32768)

class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    latency_ms: float
    source: str
    cache_hit: bool
    cost_estimate: float

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    services: Dict[str, str]
    uptime_seconds: float
    cache_connected: bool

class NeuralGateway:
    """Intelligent neural request router"""

    def __init__(self):
        self.start_time = time.time()
        self.neural_engine_url = "http://neural-engine:8001"
        self.asip_orchestrator_url = "http://asip-orchestrator:8100"
        # Circuit breaker state per target
        self._cb: dict[str, dict[str, float | int]] = {
            # state: 0=closed,1=open,2=half_open
            'neural_engine': {'state': 0, 'failures': 0, 'opened_at': 0.0},
            'asip_orchestrator': {'state': 0, 'failures': 0, 'opened_at': 0.0},
        }
        self._cb_threshold = 3  # failures to open
        self._cb_open_seconds = 10.0  # time to half-open
        self._cb_half_open_max = 1  # allow 1 trial in half-open
        CB_STATE.labels(target='neural_engine').set(0)
        CB_STATE.labels(target='asip_orchestrator').set(0)

    async def initialize(self):
        """Initialize gateway components"""
        global http_client, cache_client

        # Initialize HTTP client
        http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
        )

        # Initialize Redis cache
        try:
            cache_client = redis.Redis(
                host="redis-neural-cache",
                port=6379,
                db=1,  # Use different DB than neural engine
                decode_responses=True,
                socket_timeout=5.0
            )
            await cache_client.ping()
            logger.info("Connected to Redis cache")
        except Exception as e:
            logger.warning(f"Redis cache not available: {e}")
            cache_client = None

    async def shutdown(self):
        """Cleanup resources"""
        global http_client, cache_client

        if http_client:
            await http_client.aclose()

        if cache_client:
            await cache_client.close()

    def _classify_request(self, message: str, context: Optional[List[str]] = None) -> str:
        """Classify request to determine routing strategy"""
        message_lower = message.lower()

        # Complex reasoning indicators
        reasoning_keywords = [
            "analyze", "explain", "compare", "evaluate", "reason", "logic",
            "why", "how", "what if", "implications", "consequences"
        ]

        # Code-related indicators
        code_keywords = [
            "code", "function", "class", "python", "javascript", "api",
            "debug", "error", "implement", "algorithm"
        ]

        # Simple query indicators
        simple_keywords = [
            "hello", "hi", "thanks", "yes", "no", "ok", "sure"
        ]

        # Check for simple queries first
        if any(keyword in message_lower for keyword in simple_keywords) and len(message) < 50:
            return "simple"

        # Check for code-related queries
        if any(keyword in message_lower for keyword in code_keywords):
            return "code"

        # Check for complex reasoning
        if any(keyword in message_lower for keyword in reasoning_keywords) or len(message) > 200:
            return "reasoning"

        # Default to standard
        return "standard"

    def _generate_cache_key(self, request: ChatRequest) -> str:
        """Generate cache key for request"""
        cache_data = {
            "message": request.message,
            "context": request.context or [],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        return f"chat:{hashlib.sha256(cache_str.encode()).hexdigest()[:16]}"

    async def _check_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Check cache for existing response"""
        if not cache_client:
            return None

        try:
            cached_data = await cache_client.get(cache_key)
            if cached_data:
                CACHE_HITS.inc()
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Cache read error: {e}")

        CACHE_MISSES.inc()
        return None

    async def _store_cache(self, cache_key: str, response_data: Dict[str, Any], ttl: int = 3600):
        """Store response in cache"""
        if not cache_client:
            return

        try:
            await cache_client.setex(cache_key, ttl, json.dumps(response_data))
        except Exception as e:
            logger.warning(f"Cache write error: {e}")

    async def _route_to_neural_engine(self, request: ChatRequest) -> Dict[str, Any]:
        """Route request to neural engine"""
        if not http_client:
            raise HTTPException(status_code=503, detail="HTTP client not initialized")

        payload = {
            "query": request.message,
            "context": request.context,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "use_cache": True
        }

        target = 'neural_engine'
        # Circuit breaker guard
        now = time.time()
        st = self._cb[target]
        # Transition from open to half-open if window passed
        if st['state'] == 1 and now - float(st['opened_at']) >= self._cb_open_seconds:
            st['state'] = 2  # half-open
            st['failures'] = 0
            CB_STATE.labels(target=target).set(2)
        if st['state'] == 1:
            raise HTTPException(status_code=503, detail="Neural engine temporarily unavailable (circuit open)")
        try:
            response = await http_client.post(
                f"{self.neural_engine_url}/neural/inference",
                json=payload,
                timeout=60.0
            )
            response.raise_for_status()
            CB_SUCCESS_TOTAL.labels(target=target).inc()
            # On success from half-open, close the circuit
            if st['state'] == 2:
                st['state'] = 0
                st['failures'] = 0
                CB_STATE.labels(target=target).set(0)
            return response.json()
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            CB_FAILURE_TOTAL.labels(target=target).inc()
            st['failures'] = int(st['failures']) + 1
            # Open circuit if threshold exceeded (only if not already open)
            if st['state'] != 1 and int(st['failures']) >= self._cb_threshold:
                st['state'] = 1
                st['opened_at'] = now
                CB_OPEN_TOTAL.labels(target=target).inc()
                CB_STATE.labels(target=target).set(1)
            logger.error(f"Neural engine error: {e}")
            if isinstance(e, httpx.HTTPStatusError):
                raise HTTPException(status_code=e.response.status_code, detail="Neural engine error")
            raise HTTPException(status_code=503, detail="Neural engine unavailable")

    async def _route_to_asip(self, request: ChatRequest) -> Dict[str, Any]:
        """Route request to ASIP orchestrator"""
        if not http_client:
            raise HTTPException(status_code=503, detail="HTTP client not initialized")

        payload = {
            "message": request.message,
            "context": request.context,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens
        }

        target = 'asip_orchestrator'
        now = time.time()
        st = self._cb[target]
        if st['state'] == 1 and now - float(st['opened_at']) >= self._cb_open_seconds:
            st['state'] = 2
            st['failures'] = 0
            CB_STATE.labels(target=target).set(2)
        if st['state'] == 1:
            raise HTTPException(status_code=503, detail="ASIP orchestrator temporarily unavailable (circuit open)")
        try:
            response = await http_client.post(
                f"{self.asip_orchestrator_url}/chat",
                json=payload,
                timeout=60.0
            )
            response.raise_for_status()
            CB_SUCCESS_TOTAL.labels(target=target).inc()
            if st['state'] == 2:
                st['state'] = 0
                st['failures'] = 0
                CB_STATE.labels(target=target).set(0)
            return response.json()
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            CB_FAILURE_TOTAL.labels(target=target).inc()
            st['failures'] = int(st['failures']) + 1
            if st['state'] != 1 and int(st['failures']) >= self._cb_threshold:
                st['state'] = 1
                st['opened_at'] = now
                CB_OPEN_TOTAL.labels(target=target).inc()
                CB_STATE.labels(target=target).set(1)
            logger.error(f"ASIP orchestrator error: {e}")
            if isinstance(e, httpx.HTTPStatusError):
                raise HTTPException(status_code=e.response.status_code, detail="ASIP orchestrator error")
            raise HTTPException(status_code=503, detail="ASIP orchestrator unavailable")

    async def process_chat(self, request: ChatRequest) -> ChatResponse:
        """Process chat request with intelligent routing"""
        start_time = time.perf_counter()

        # Generate cache key
        cache_key = self._generate_cache_key(request)

        # Check cache first
        cached_response = await self._check_cache(cache_key)
        if cached_response:
            cached_response["cache_hit"] = True
            cached_response["latency_ms"] = (time.perf_counter() - start_time) * 1000
            return ChatResponse(**cached_response)

        # Classify request for routing
        request_type = self._classify_request(request.message, request.context)

        # Route based on classification
        if request_type in ["reasoning", "code"]:
            # Use neural engine for complex tasks
            result = await self._route_to_neural_engine(request)
            source = "neural_engine"
        else:
            # Use ASIP orchestrator for standard tasks
            try:
                result = await self._route_to_asip(request)
                source = "asip_orchestrator"
            except HTTPException:
                # Fallback to neural engine if ASIP fails
                result = await self._route_to_neural_engine(request)
                source = "neural_engine_fallback"

        # Calculate latency
        latency_ms = (time.perf_counter() - start_time) * 1000

        # Prepare response
        response_data = {
            "response": result.get("response", result.get("text", "")),
            "latency_ms": latency_ms,
            "source": source,
            "cache_hit": False,
            "cost_estimate": result.get("cost_estimate", 0.0)
        }

        # Cache response
        await self._store_cache(cache_key, response_data)

        return ChatResponse(**response_data)

    async def health_check(self) -> HealthResponse:
        """Comprehensive health check"""
        services = {}

        # Check neural engine
        try:
            if http_client:
                response = await http_client.get(f"{self.neural_engine_url}/health", timeout=5.0)
                services["neural_engine"] = "healthy" if response.status_code == 200 else "unhealthy"
            else:
                services["neural_engine"] = "not_initialized"
        except:
            services["neural_engine"] = "unreachable"

        # Check ASIP orchestrator
        try:
            if http_client:
                response = await http_client.get(f"{self.asip_orchestrator_url}/health", timeout=5.0)
                services["asip_orchestrator"] = "healthy" if response.status_code == 200 else "unhealthy"
            else:
                services["asip_orchestrator"] = "not_initialized"
        except:
            services["asip_orchestrator"] = "unreachable"

        # Check cache
        cache_connected = False
        if cache_client:
            try:
                await cache_client.ping()
                cache_connected = True
            except:

        # Determine overall status
        healthy_services = sum(1 for status in services.values() if status == "healthy")
        total_services = len(services)

        if healthy_services == total_services:
            status = "healthy"
        elif healthy_services > 0:
            status = "degraded"
        else:
            status = "unhealthy"

        return HealthResponse(
            status=status,
            services=services,
            uptime_seconds=time.time() - self.start_time,
            cache_connected=cache_connected
        )

# Initialize gateway
gateway = NeuralGateway()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    await gateway.initialize()
    yield
    await gateway.shutdown()

# Create FastAPI application
app = FastAPI(
    title="Sophia AI Neural Gateway",
    description="Intelligent routing for neural AI services",
    version="3.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Metrics collection middleware"""
    start_time = time.perf_counter()
    ACTIVE_CONNECTIONS.inc()

    try:
        response = await call_next(request)
        REQUEST_COUNT.labels(endpoint=request.url.path, method=request.method).inc()
        return response
    finally:
        REQUEST_DURATION.observe(time.perf_counter() - start_time)
        ACTIVE_CONNECTIONS.dec()

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """Main chat endpoint with intelligent routing"""
    return await gateway.process_chat(request)

@app.get("/health", response_model=HealthResponse)
async def health_endpoint() -> HealthResponse:
    """Health check endpoint"""
    return await gateway.health_check()

@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    return generate_latest().decode()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Sophia AI Neural Gateway",
        "version": "3.0.0",
        "status": "operational",
        "routes": {
            "chat": "/chat",
            "health": "/health",
            "metrics": "/metrics"
        }
    }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="${BIND_IP}",
        port=8000,
        workers=4,
        log_level="info"
    )
