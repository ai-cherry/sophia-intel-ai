#!/usr/bin/env python3
"""
Proxy bridge to connect UI on 7777 to API server on 8000
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import httpx
import uvicorn

app = FastAPI()

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BACKEND_URL = "http://localhost:8000"

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def proxy(path: str, request: Request):
    """Proxy all requests to the backend server."""
    
    # Build the backend URL
    url = f"{BACKEND_URL}/{path}"
    
    # Get the query params
    params = dict(request.query_params)
    
    # Get headers
    headers = dict(request.headers)
    headers.pop("host", None)
    
    # Get body if present
    body = None
    if request.method in ["POST", "PUT"]:
        body = await request.body()
    
    # Make the request to backend
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.request(
            method=request.method,
            url=url,
            params=params,
            headers=headers,
            content=body,
            follow_redirects=True
        )
        
        # Check if it's a streaming response
        if "text/event-stream" in response.headers.get("content-type", ""):
            async def stream():
                async for chunk in response.aiter_bytes():
                    yield chunk
            
            return StreamingResponse(
                stream(),
                media_type=response.headers.get("content-type"),
                headers=dict(response.headers)
            )
        
        # Return regular response
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )

if __name__ == "__main__":
    print("🌉 Starting proxy bridge on port 7777 -> 8000")
    uvicorn.run(app, host="0.0.0.0", port=7777)