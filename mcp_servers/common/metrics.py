# mcp_servers/common/metrics.py
from fastapi import FastAPI, Request
from fastapi.responses import Response, JSONResponse, PlainTextResponse
from prometheus_client import Counter, Histogram, CONTENT_TYPE_LATEST, generate_latest
import time

# Labeled counters/histograms
REQUEST_COUNT = Counter(
    "sophia_requests_total",
    "Total HTTP requests",
    labelnames=("service", "method", "path", "status"),
)
REQUEST_LATENCY = Histogram(
    "sophia_request_latency_seconds",
    "HTTP request latency in seconds",
    labelnames=("service", "method", "path"),
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
)

def init_metrics(app: FastAPI, service_name: str, version: str = "4.2.0") -> None:
    """Attach /metrics and request instrumentation to a FastAPI app."""
    @app.middleware("http")
    async def _metrics_middleware(request: Request, call_next):
        start = time.perf_counter()
        response: Response = await call_next(request)
        elapsed = time.perf_counter() - start
        path = request.url.path
        # protect cardinality: bucket non-essential dynamic paths if you add any later
        REQUEST_COUNT.labels(service_name, request.method, path, str(response.status_code)).inc()
        REQUEST_LATENCY.labels(service_name, request.method, path).observe(elapsed)
        return response

    @app.get("/metrics")
    def _metrics():
        return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)

def register_healthz_if_missing(app: FastAPI, service_name: str, version: str = "4.2.0") -> None:
    """Ensure GET /healthz exists with the v4.2 contract."""
    exists = any(getattr(r, "path", None) == "/healthz" for r in app.routes)
    if not exists:
        @app.get("/healthz")
        def _healthz():
            return JSONResponse({"status": "ok", "service": service_name, "version": version})

