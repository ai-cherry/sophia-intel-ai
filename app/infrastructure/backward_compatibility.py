"""
Backward Compatibility Layer for API Migration
Ensures smooth transition from V1 to V2 API
"""

import json
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import logging
from functools import wraps

from app.api.contracts import (
    ChatRequestV1, ChatRequestV2,
    ChatResponseV1, ChatResponseV2,
    WebSocketMessage
)

logger = logging.getLogger(__name__)

# ==================== Version Mapping ====================

class APIVersionMapper:
    """
    Maps between different API versions for backward compatibility
    """
    
    @staticmethod
    def v1_request_to_v2(v1_request: ChatRequestV1) -> ChatRequestV2:
        """Convert V1 request to V2 format"""
        return ChatRequestV2(
            message=v1_request.message,
            session_id=v1_request.session_id,
            optimization_mode="balanced",  # Default for V1 clients
            swarm_type=None,  # Not available in V1
            use_memory=False,  # Default for V1
            user_context=v1_request.user_context or {}
        )
    
    @staticmethod
    def v2_response_to_v1(v2_response: ChatResponseV2) -> ChatResponseV1:
        """Convert V2 response to V1 format"""
        return ChatResponseV1(
            response=v2_response.response,
            session_id=v2_response.session_id,
            success=v2_response.success,
            metadata=v2_response.metadata
        )
    
    @staticmethod
    def detect_request_version(request_data: Dict[str, Any]) -> str:
        """Detect API version from request data"""
        # Explicit version
        if "api_version" in request_data:
            return request_data["api_version"]
        
        # V2 specific fields
        v2_fields = {"optimization_mode", "swarm_type", "use_memory"}
        if any(field in request_data for field in v2_fields):
            return "v2"
        
        # V1 format detection
        if "message" in request_data and "session_id" in request_data:
            # Check for V1-only field patterns
            if "text" in request_data:  # Old V1 field name
                return "v1"
            
            # Default to V2 for new clients
            return "v2"
        
        # Legacy format
        if "text" in request_data or "sessionId" in request_data:
            return "v1"
        
        # Default to latest version
        return "v2"

# ==================== Compatibility Middleware ====================

class BackwardCompatibilityMiddleware:
    """
    Middleware to handle backward compatibility
    """
    
    def __init__(self):
        self.version_mapper = APIVersionMapper()
        self.deprecation_warnings: Dict[str, datetime] = {}
    
    async def process_request(
        self,
        request_data: Dict[str, Any],
        handler: Callable
    ) -> Dict[str, Any]:
        """
        Process request with backward compatibility
        """
        # Detect version
        version = self.version_mapper.detect_request_version(request_data)
        
        # Log version usage
        logger.info(f"Processing {version} API request")
        
        # Transform request if needed
        if version == "v1":
            # Log deprecation warning
            self._log_deprecation_warning(
                "v1_api",
                "API v1 is deprecated. Please migrate to v2."
            )
            
            # Transform V1 to V2
            v1_request = self._parse_v1_request(request_data)
            v2_request = self.version_mapper.v1_request_to_v2(v1_request)
            
            # Process with V2 handler
            v2_response = await handler(v2_request)
            
            # Transform response back to V1
            v1_response = self.version_mapper.v2_response_to_v1(v2_response)
            
            return v1_response.dict()
        else:
            # Process V2 request directly
            v2_request = ChatRequestV2(**request_data)
            v2_response = await handler(v2_request)
            return v2_response.dict()
    
    def _parse_v1_request(self, data: Dict[str, Any]) -> ChatRequestV1:
        """Parse V1 request with field name mapping"""
        # Handle old field names
        if "text" in data:
            data["message"] = data.pop("text")
        if "sessionId" in data:
            data["session_id"] = data.pop("sessionId")
        if "userContext" in data:
            data["user_context"] = data.pop("userContext")
        
        return ChatRequestV1(**data)
    
    def _log_deprecation_warning(self, feature: str, message: str):
        """Log deprecation warning with rate limiting"""
        now = datetime.utcnow()
        
        # Rate limit warnings to once per hour
        if feature in self.deprecation_warnings:
            last_warning = self.deprecation_warnings[feature]
            if (now - last_warning).total_seconds() < 3600:
                return
        
        logger.warning(f"DEPRECATION: {message}")
        self.deprecation_warnings[feature] = now

# ==================== WebSocket Compatibility ====================

class WebSocketCompatibilityAdapter:
    """
    Adapter for WebSocket message compatibility
    """
    
    @staticmethod
    def adapt_v1_message(message: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt V1 WebSocket message to V2 format"""
        # Handle old message types
        if message.get("type") == "message":  # Old V1 type
            message["type"] = "chat"
        
        # Handle old field names in data
        if "data" in message:
            data = message["data"]
            if "text" in data:
                data["message"] = data.pop("text")
            if "sessionId" in data:
                data["session_id"] = data.pop("sessionId")
        
        return message
    
    @staticmethod
    def adapt_v2_response(response: Dict[str, Any], client_version: str) -> Dict[str, Any]:
        """Adapt V2 response for V1 clients"""
        if client_version == "v1":
            # Remove V2-only fields
            v2_only_fields = [
                "execution_mode",
                "quality_score",
                "execution_time"
            ]
            for field in v2_only_fields:
                response.pop(field, None)
            
            # Rename fields for V1
            if "response" in response:
                response["text"] = response.pop("response")
            if "session_id" in response:
                response["sessionId"] = response.pop("session_id")
        
        return response

# ==================== Migration Helpers ====================

class MigrationHelper:
    """
    Helpers for migrating from V1 to V2
    """
    
    @staticmethod
    def generate_migration_report(
        v1_usage: Dict[str, int],
        v2_usage: Dict[str, int]
    ) -> Dict[str, Any]:
        """Generate migration status report"""
        total_v1 = sum(v1_usage.values())
        total_v2 = sum(v2_usage.values())
        total = total_v1 + total_v2
        
        if total == 0:
            migration_percentage = 0
        else:
            migration_percentage = (total_v2 / total) * 100
        
        return {
            "total_requests": total,
            "v1_requests": total_v1,
            "v2_requests": total_v2,
            "migration_percentage": migration_percentage,
            "v1_endpoints": list(v1_usage.keys()),
            "v2_endpoints": list(v2_usage.keys()),
            "recommendation": MigrationHelper._get_recommendation(migration_percentage)
        }
    
    @staticmethod
    def _get_recommendation(migration_percentage: float) -> str:
        """Get migration recommendation based on progress"""
        if migration_percentage < 25:
            return "Begin migration - most clients still on V1"
        elif migration_percentage < 50:
            return "Migration in progress - continue monitoring"
        elif migration_percentage < 75:
            return "Good progress - consider deprecation timeline"
        elif migration_percentage < 95:
            return "Nearly complete - reach out to remaining V1 clients"
        else:
            return "Ready to sunset V1 API"
    
    @staticmethod
    def validate_v1_to_v2_migration(
        v1_request: Dict[str, Any],
        v2_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate that V1 to V2 migration preserves data"""
        issues = []
        
        # Check required fields
        if v1_request.get("message") != v2_request.get("message"):
            issues.append("Message content mismatch")
        
        if v1_request.get("session_id") != v2_request.get("session_id"):
            issues.append("Session ID mismatch")
        
        # Check data loss
        v1_context = v1_request.get("user_context", {})
        v2_context = v2_request.get("user_context", {})
        if v1_context and v1_context != v2_context:
            issues.append("User context data loss")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }

# ==================== Compatibility Decorators ====================

def backward_compatible(version: str = "v2"):
    """
    Decorator to make endpoints backward compatible
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request data
            request = kwargs.get("request")
            if not request:
                return await func(*args, **kwargs)
            
            # Check if it's a dict (raw request data)
            if isinstance(request, dict):
                middleware = BackwardCompatibilityMiddleware()
                
                # Create handler for the original function
                async def handler(transformed_request):
                    kwargs["request"] = transformed_request
                    return await func(*args, **kwargs)
                
                # Process with compatibility layer
                return await middleware.process_request(request, handler)
            
            # Already transformed, proceed normally
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

def deprecated(message: str, sunset_date: Optional[str] = None):
    """
    Mark an endpoint or function as deprecated
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            warning = f"DEPRECATED: {message}"
            if sunset_date:
                warning += f" (Sunset date: {sunset_date})"
            logger.warning(warning)
            return func(*args, **kwargs)
        
        # Add deprecation metadata
        wrapper._deprecated = True
        wrapper._deprecation_message = message
        wrapper._sunset_date = sunset_date
        
        return wrapper
    return decorator

# ==================== Client Version Detection ====================

class ClientVersionDetector:
    """
    Detect client version from various sources
    """
    
    @staticmethod
    def detect_from_headers(headers: Dict[str, str]) -> Optional[str]:
        """Detect version from HTTP headers"""
        # Check API-Version header
        if "API-Version" in headers:
            return headers["API-Version"]
        
        # Check User-Agent for SDK version
        user_agent = headers.get("User-Agent", "")
        if "ai-orchestra-sdk/1." in user_agent:
            return "v1"
        elif "ai-orchestra-sdk/2." in user_agent:
            return "v2"
        
        return None
    
    @staticmethod
    def detect_from_path(path: str) -> Optional[str]:
        """Detect version from URL path"""
        if "/v1/" in path:
            return "v1"
        elif "/v2/" in path:
            return "v2"
        return None
    
    @staticmethod
    def detect_from_query(query_params: Dict[str, str]) -> Optional[str]:
        """Detect version from query parameters"""
        return query_params.get("api_version")

# ==================== Feature Parity Checker ====================

class FeatureParityChecker:
    """
    Check feature parity between API versions
    """
    
    @staticmethod
    def check_parity() -> Dict[str, Any]:
        """Check which features are available in each version"""
        v1_features = {
            "basic_chat": True,
            "session_management": True,
            "user_context": True,
            "metadata": True
        }
        
        v2_features = {
            "basic_chat": True,
            "session_management": True,
            "user_context": True,
            "metadata": True,
            "optimization_modes": True,
            "swarm_intelligence": True,
            "memory_integration": True,
            "quality_scoring": True,
            "execution_metrics": True,
            "websocket_streaming": True
        }
        
        v1_only = set(v1_features.keys()) - set(v2_features.keys())
        v2_only = set(v2_features.keys()) - set(v1_features.keys())
        common = set(v1_features.keys()) & set(v2_features.keys())
        
        return {
            "v1_features": v1_features,
            "v2_features": v2_features,
            "v1_only": list(v1_only),
            "v2_only": list(v2_only),
            "common": list(common),
            "v2_advantages": len(v2_only),
            "migration_required": len(v1_only) > 0
        }

# ==================== Export ====================

__all__ = [
    "APIVersionMapper",
    "BackwardCompatibilityMiddleware",
    "WebSocketCompatibilityAdapter",
    "MigrationHelper",
    "ClientVersionDetector",
    "FeatureParityChecker",
    "backward_compatible",
    "deprecated"
]