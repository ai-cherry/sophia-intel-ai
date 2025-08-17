"""
Analytics Middleware for SOPHIA Intel
Automatic request/response tracking with comprehensive metrics collection
"""

import asyncio
import json
import time
import uuid
from typing import Any, Callable, Dict, Optional

from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from loguru import logger

from backend.observability_service import ObservabilityService


class AnalyticsMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatic request/response tracking and analytics collection
    """
    
    def __init__(self, app, observability_service: ObservabilityService):
        super().__init__(app)
        self.observability = observability_service
        
        # Endpoints to track (can be configured)
        self.tracked_endpoints = {
            "/chat",
            "/chat/stream",
            "/research",
            "/health",
            "/metrics"
        }
        
        # Endpoints to exclude from tracking
        self.excluded_endpoints = {
            "/favicon.ico",
            "/robots.txt",
            "/static"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and response with analytics tracking"""
        
        # Check if endpoint should be tracked
        path = request.url.path
        if not self._should_track_endpoint(path):
            return await call_next(request)
        
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Extract request information
        session_id = self._extract_session_id(request)
        user_agent = request.headers.get("user-agent")
        ip_address = self._extract_ip_address(request)
        request_size = self._estimate_request_size(request)
        
        # Extract additional metadata
        metadata = {
            "path": path,
            "query_params": dict(request.query_params),
            "content_type": request.headers.get("content-type"),
            "referer": request.headers.get("referer"),
            "accept": request.headers.get("accept")
        }
        
        # Track request start
        request_metrics = await self.observability.track_request_start(
            request_id=request_id,
            endpoint=path,
            method=request.method,
            session_id=session_id,
            user_agent=user_agent,
            ip_address=ip_address,
            request_size=request_size,
            metadata=metadata
        )
        
        # Add request ID to request state for downstream use
        request.state.request_id = request_id
        request.state.analytics_start_time = time.time()
        
        # Process request
        response = None
        error = None
        backend_used = None
        
        try:
            response = await call_next(request)
            
            # Extract backend information from response headers or request state
            backend_used = getattr(request.state, 'backend_used', None)
            if not backend_used:
                backend_used = response.headers.get("X-Backend-Used")
            
        except Exception as e:
            error = str(e)
            logger.error(f"Request {request_id} failed: {error}")
            
            # Create error response
            response = Response(
                content=json.dumps({"error": "Internal server error", "request_id": request_id}),
                status_code=500,
                media_type="application/json"
            )
        
        # Calculate response size
        response_size = self._estimate_response_size(response)
        
        # Track request end
        await self.observability.track_request_end(
            request_id=request_id,
            status_code=response.status_code,
            backend_used=backend_used,
            response_size=response_size,
            error=error,
            metadata={
                "response_headers": dict(response.headers),
                "processing_time": time.time() - request_metrics.start_time
            }
        )
        
        # Add analytics headers to response
        response.headers["X-Request-ID"] = request_id
        if backend_used:
            response.headers["X-Backend-Used"] = backend_used
        
        return response
    
    def _should_track_endpoint(self, path: str) -> bool:
        """Determine if endpoint should be tracked"""
        # Exclude specific endpoints
        for excluded in self.excluded_endpoints:
            if path.startswith(excluded):
                return False
        
        # Include specific endpoints or all if none specified
        if not self.tracked_endpoints:
            return True
        
        for tracked in self.tracked_endpoints:
            if path.startswith(tracked):
                return True
        
        return False
    
    def _extract_session_id(self, request: Request) -> Optional[str]:
        """Extract session ID from request"""
        # Try multiple sources for session ID
        
        # 1. Query parameter
        session_id = request.query_params.get("session_id")
        if session_id:
            return session_id
        
        # 2. Header
        session_id = request.headers.get("X-Session-ID")
        if session_id:
            return session_id
        
        # 3. Cookie
        session_id = request.cookies.get("session_id")
        if session_id:
            return session_id
        
        # 4. Authorization header (extract user ID)
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # Would decode JWT token to extract user ID
            # For now, use a hash of the token
            import hashlib
            token_hash = hashlib.md5(auth_header.encode()).hexdigest()[:8]
            return f"auth_{token_hash}"
        
        return None
    
    def _extract_ip_address(self, request: Request) -> Optional[str]:
        """Extract client IP address"""
        # Try multiple headers for IP address
        ip_headers = [
            "X-Forwarded-For",
            "X-Real-IP",
            "X-Client-IP",
            "CF-Connecting-IP"  # Cloudflare
        ]
        
        for header in ip_headers:
            ip = request.headers.get(header)
            if ip:
                # Take first IP if comma-separated
                return ip.split(",")[0].strip()
        
        # Fallback to client host
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return None
    
    def _estimate_request_size(self, request: Request) -> Optional[int]:
        """Estimate request size in bytes"""
        try:
            size = 0
            
            # Headers size
            for name, value in request.headers.items():
                size += len(name) + len(value) + 4  # ": " and "\r\n"
            
            # Content length if available
            content_length = request.headers.get("content-length")
            if content_length:
                size += int(content_length)
            
            # URL size
            size += len(str(request.url))
            
            return size
            
        except Exception as e:
            logger.warning(f"Failed to estimate request size: {e}")
            return None
    
    def _estimate_response_size(self, response: Response) -> Optional[int]:
        """Estimate response size in bytes"""
        try:
            size = 0
            
            # Headers size
            for name, value in response.headers.items():
                size += len(name) + len(value) + 4  # ": " and "\r\n"
            
            # Content length if available
            content_length = response.headers.get("content-length")
            if content_length:
                size += int(content_length)
            elif hasattr(response, 'body') and response.body:
                size += len(response.body)
            
            return size
            
        except Exception as e:
            logger.warning(f"Failed to estimate response size: {e}")
            return None


class ChatAnalyticsMiddleware:
    """
    Specialized middleware for chat endpoint analytics
    """
    
    def __init__(self, observability_service: ObservabilityService):
        self.observability = observability_service
    
    async def track_chat_request(
        self,
        request: Request,
        session_id: str,
        message_count: int,
        backend_used: str,
        features_used: Optional[list] = None,
        tokens_estimated: int = 0,
        research_query: bool = False
    ):
        """Track chat-specific metrics"""
        try:
            # Get response time from request state
            start_time = getattr(request.state, 'analytics_start_time', time.time())
            response_time = time.time() - start_time
            
            # Track chat session
            await self.observability.track_chat_session(
                session_id=session_id,
                message_count=message_count,
                backend_used=backend_used,
                response_time=response_time,
                tokens_estimated=tokens_estimated,
                features_used=features_used or [],
                error_occurred=False,
                research_query=research_query
            )
            
            # Set backend in request state for main middleware
            request.state.backend_used = backend_used
            
        except Exception as e:
            logger.error(f"Failed to track chat analytics: {e}")
    
    async def track_chat_error(
        self,
        request: Request,
        session_id: str,
        backend_used: str,
        error: str
    ):
        """Track chat error"""
        try:
            start_time = getattr(request.state, 'analytics_start_time', time.time())
            response_time = time.time() - start_time
            
            await self.observability.track_chat_session(
                session_id=session_id,
                message_count=0,
                backend_used=backend_used,
                response_time=response_time,
                error_occurred=True
            )
            
            request.state.backend_used = backend_used
            
        except Exception as e:
            logger.error(f"Failed to track chat error: {e}")


class ResearchAnalyticsMiddleware:
    """
    Specialized middleware for research endpoint analytics
    """
    
    def __init__(self, observability_service: ObservabilityService):
        self.observability = observability_service
    
    async def track_research_request(
        self,
        request: Request,
        session_id: Optional[str],
        query: str,
        sources_found: int,
        research_time: float,
        confidence_score: float,
        providers_used: list
    ):
        """Track research-specific metrics"""
        try:
            # Track as chat session with research flag
            if session_id:
                await self.observability.track_chat_session(
                    session_id=session_id,
                    message_count=1,  # Research counts as one interaction
                    backend_used="web_research",
                    response_time=research_time,
                    features_used=["web_research"] + providers_used,
                    research_query=True
                )
            
            # Set backend in request state
            request.state.backend_used = "web_research"
            
            # Add research-specific metadata
            request.state.research_metadata = {
                "query": query,
                "sources_found": sources_found,
                "confidence_score": confidence_score,
                "providers_used": providers_used
            }
            
        except Exception as e:
            logger.error(f"Failed to track research analytics: {e}")


# Utility functions for manual tracking
async def track_backend_usage(request: Request, backend: str):
    """Manually track backend usage for a request"""
    if hasattr(request.state, 'backend_used'):
        # If multiple backends used, combine them
        existing = request.state.backend_used
        if existing and existing != backend:
            request.state.backend_used = f"{existing}+{backend}"
        else:
            request.state.backend_used = backend
    else:
        request.state.backend_used = backend


async def track_feature_usage(request: Request, features: list):
    """Manually track feature usage for a request"""
    if not hasattr(request.state, 'features_used'):
        request.state.features_used = []
    
    for feature in features:
        if feature not in request.state.features_used:
            request.state.features_used.append(feature)


async def track_tokens_estimated(request: Request, tokens: int):
    """Manually track estimated token usage"""
    if hasattr(request.state, 'tokens_estimated'):
        request.state.tokens_estimated += tokens
    else:
        request.state.tokens_estimated = tokens

