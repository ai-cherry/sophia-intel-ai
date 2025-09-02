from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.api import unified_gateway

app = FastAPI()

# Request size limit middleware
async def limit_request_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > 1024 * 1024:  # 1MB
        raise HTTPException(status_code=413, detail="Request too large")
    return await call_next(request)

app.add_middleware(limit_request_size)

# Configure CORS for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-production-domain.com", "https://your-staging-domain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Custom security headers middleware
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Frame-Options"] = "DENY"
    return response

app.include_router(unified_gateway.router)
