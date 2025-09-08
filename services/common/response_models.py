"""
Standardized response models for AI-agent friendly deterministic outputs
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
import uuid
import time

class ResponseStatus(Enum):
    """Standard response status codes"""
    SUCCESS = "success"
    PARTIAL = "partial"
    ERROR = "error"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"

@dataclass
class ServiceResponse:
    """Standard response wrapper for all Sophia AI services"""

    # Core response data
    success: bool
    status: ResponseStatus
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    # Metadata for observability
    request_id: str = None
    timestamp: datetime = None
    duration_ms: float = 0.0
    service_name: str = ""
    version: str = "1.0.0"

    # AI-agent friendly fields
    confidence: float = 1.0  # 0.0 to 1.0
    sources: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Initialize default values"""
        if self.request_id is None:
            self.request_id = str(uuid.uuid4())
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.sources is None:
            self.sources = []
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Deterministic serialization for agent chaining"""
        return {
            "success": self.success,
            "status": self.status.value,
            "data": self.data,
            "error": self.error,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
            "service_name": self.service_name,
            "version": self.version,
            "confidence": self.confidence,
            "sources": self.sources,
            "metadata": self.metadata
        }

    @classmethod
    def success_response(
        cls,
        data: Dict[str, Any],
        service_name: str,
        confidence: float = 1.0,
        sources: List[str] = None,
        duration_ms: float = 0.0
    ) -> "ServiceResponse":
        """Create a successful response"""
        return cls(
            success=True,
            status=ResponseStatus.SUCCESS,
            data=data,
            service_name=service_name,
            confidence=confidence,
            sources=sources or [],
            duration_ms=duration_ms
        )

    @classmethod
    def error_response(
        cls,
        error: str,
        service_name: str,
        status: ResponseStatus = ResponseStatus.ERROR,
        duration_ms: float = 0.0
    ) -> "ServiceResponse":
        """Create an error response"""
        return cls(
            success=False,
            status=status,
            error=error,
            service_name=service_name,
            confidence=0.0,
            duration_ms=duration_ms
        )

    @classmethod
    def partial_response(
        cls,
        data: Dict[str, Any],
        service_name: str,
        confidence: float,
        sources: List[str] = None,
        duration_ms: float = 0.0,
        error: str = None
    ) -> "ServiceResponse":
        """Create a partial success response"""
        return cls(
            success=True,
            status=ResponseStatus.PARTIAL,
            data=data,
            error=error,
            service_name=service_name,
            confidence=confidence,
            sources=sources or [],
            duration_ms=duration_ms
        )

@dataclass
class SearchResponse(ServiceResponse):
    """Specialized response for search operations"""

    query: str = ""
    results_count: int = 0
    apis_used: List[str] = None
    fusion_strategy: str = "weighted_confidence"

    def __post_init__(self):
        super().__post_init__()
        if self.apis_used is None:
            self.apis_used = []

    def to_dict(self) -> Dict[str, Any]:
        """Extended serialization for search responses"""
        base_dict = super().to_dict()
        base_dict.update({
            "query": self.query,
            "results_count": self.results_count,
            "apis_used": self.apis_used,
            "fusion_strategy": self.fusion_strategy
        })
        return base_dict

@dataclass
class NeuralResponse(ServiceResponse):
    """Specialized response for neural inference operations"""

    prompt: str = ""
    model: str = ""
    tokens_generated: int = 0
    inference_time_ms: float = 0.0
    gpu_memory_used_mb: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Extended serialization for neural responses"""
        base_dict = super().to_dict()
        base_dict.update({
            "prompt": self.prompt[:100] + "..." if len(self.prompt) > 100 else self.prompt,
            "model": self.model,
            "tokens_generated": self.tokens_generated,
            "inference_time_ms": self.inference_time_ms,
            "gpu_memory_used_mb": self.gpu_memory_used_mb
        })
        return base_dict

@dataclass
class HealthResponse(ServiceResponse):
    """Specialized response for health check operations"""

    service_status: str = "healthy"
    dependencies: Dict[str, str] = None
    resource_usage: Dict[str, float] = None
    uptime_seconds: float = 0.0

    def __post_init__(self):
        super().__post_init__()
        if self.dependencies is None:
            self.dependencies = {}
        if self.resource_usage is None:
            self.resource_usage = {}

    def to_dict(self) -> Dict[str, Any]:
        """Extended serialization for health responses"""
        base_dict = super().to_dict()
        base_dict.update({
            "service_status": self.service_status,
            "dependencies": self.dependencies,
            "resource_usage": self.resource_usage,
            "uptime_seconds": self.uptime_seconds
        })
        return base_dict

# Response factory for easy creation
class ResponseFactory:
    """Factory for creating standardized responses"""

    @staticmethod
    def create_search_response(
        query: str,
        results: List[Dict[str, Any]],
        apis_used: List[str],
        confidence: float,
        duration_ms: float
    ) -> SearchResponse:
        """Create a search response with proper metadata"""
        return SearchResponse(
            success=True,
            status=ResponseStatus.SUCCESS,
            data={"results": results},
            service_name="enhanced-search",
            confidence=confidence,
            sources=apis_used,
            duration_ms=duration_ms,
            query=query,
            results_count=len(results),
            apis_used=apis_used
        )

    @staticmethod
    def create_neural_response(
        prompt: str,
        response_text: str,
        model: str,
        tokens_generated: int,
        inference_time_ms: float,
        confidence: float = 1.0
    ) -> NeuralResponse:
        """Create a neural inference response with proper metadata"""
        return NeuralResponse(
            success=True,
            status=ResponseStatus.SUCCESS,
            data={"response": response_text},
            service_name="neural-engine",
            confidence=confidence,
            duration_ms=inference_time_ms,
            prompt=prompt,
            model=model,
            tokens_generated=tokens_generated,
            inference_time_ms=inference_time_ms
        )

    @staticmethod
    def create_health_response(
        service_name: str,
        status: str,
        dependencies: Dict[str, str],
        resource_usage: Dict[str, float],
        uptime_seconds: float
    ) -> HealthResponse:
        """Create a health check response with proper metadata"""
        return HealthResponse(
            success=status == "healthy",
            status=ResponseStatus.SUCCESS if status == "healthy" else ResponseStatus.PARTIAL,
            data={"status": status},
            service_name=service_name,
            confidence=1.0 if status == "healthy" else 0.5,
            service_status=status,
            dependencies=dependencies,
            resource_usage=resource_usage,
            uptime_seconds=uptime_seconds
        )
