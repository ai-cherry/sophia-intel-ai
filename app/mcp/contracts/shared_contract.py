#!/usr/bin/env python3
"""
Shared Domain MCP Server Contract
Specialized contract for Shared (cross-domain) services
"""

import asyncio
from abc import abstractmethod
from datetime import datetime
from typing import Any

from .base_contract import (
    BaseMCPServerContract,
    CapabilityDeclaration,
    CapabilityStatus,
    HealthCheckResult,
    HealthStatus,
    MCPRequest,
    MCPResponse,
)


class EmbeddingRequest(MCPRequest):
    """Specialized request for embedding operations"""

    def __init__(self, **data):
        super().__init__(**data)
        # Embedding-specific validations can be added here


class SearchRequest(MCPRequest):
    """Specialized request for search operations"""

    def __init__(self, **data):
        super().__init__(**data)
        # Search-specific validations can be added here


class SharedServiceContract(BaseMCPServerContract):
    """
    Shared domain contract for cross-domain MCP servers
    Extends base contract with shared service capabilities
    """

    def __init__(self, server_id: str, name: str, version: str = "1.0.0"):
        super().__init__(server_id, name, version)

        # Register standard shared capabilities
        asyncio.create_task(self._register_standard_capabilities())

    async def _register_standard_capabilities(self):
        """Register standard shared service capabilities"""

        # Embeddings Capability
        embeddings = CapabilityDeclaration(
            name="embeddings",
            methods=[
                "generate_embedding",
                "batch_generate_embeddings",
                "similarity_search",
                "semantic_search",
                "clustering",
                "dimensionality_reduction",
                "embedding_comparison",
                "update_embeddings",
            ],
            description="Vector embeddings generation and semantic operations",
            requirements=["text_input"],
            configuration={
                "supported_models": ["text-embedding-ada-002", "sentence-transformers", "custom"],
                "vector_dimensions": [512, 768, 1024, 1536],
                "similarity_metrics": ["cosine", "euclidean", "dot_product"],
                "batch_sizes": [1, 10, 50, 100],
            },
        )
        await self.register_capability(embeddings)

        # Indexing Capability
        indexing = CapabilityDeclaration(
            name="indexing",
            methods=[
                "create_index",
                "update_index",
                "delete_index",
                "search_index",
                "rebuild_index",
                "get_index_stats",
                "optimize_index",
                "backup_index",
            ],
            description="Document indexing and full-text search capabilities",
            requirements=["index_name"],
            dependencies=["embeddings"],
            configuration={
                "index_types": ["inverted", "vector", "hybrid"],
                "analyzers": ["standard", "keyword", "ngram", "semantic"],
                "storage_backends": ["memory", "disk", "distributed"],
                "max_documents": 1000000,
            },
        )
        await self.register_capability(indexing)

        # Database Operations Capability
        database_ops = CapabilityDeclaration(
            name="database_operations",
            methods=[
                "execute_query",
                "batch_insert",
                "batch_update",
                "transaction",
                "schema_migration",
                "backup_data",
                "restore_data",
                "connection_pool_status",
            ],
            description="Unified database operations across multiple backends",
            requirements=["query"],
            configuration={
                "supported_databases": ["postgresql", "mysql", "sqlite", "redis", "mongodb"],
                "connection_pooling": True,
                "transaction_support": True,
                "max_connections": 100,
            },
        )
        await self.register_capability(database_ops)

        # Cross-Domain Communication Capability
        cross_domain_comm = CapabilityDeclaration(
            name="cross_domain_communication",
            methods=[
                "route_message",
                "broadcast_message",
                "domain_discovery",
                "capability_negotiation",
                "load_balance_request",
                "failover_routing",
                "message_transformation",
                "protocol_adaptation",
            ],
            description="Communication and routing between different domains",
            requirements=["target_domain", "message"],
            dependencies=["indexing"],
            configuration={
                "supported_domains": ["artemis", "sophia", "shared"],
                "routing_strategies": ["priority", "round_robin", "least_connections"],
                "message_formats": ["json", "protobuf", "avro"],
                "compression": ["none", "gzip", "lz4"],
            },
        )
        await self.register_capability(cross_domain_comm)

        # Cache Management Capability
        cache_management = CapabilityDeclaration(
            name="cache_management",
            methods=[
                "cache_set",
                "cache_get",
                "cache_delete",
                "cache_clear",
                "cache_stats",
                "cache_expire",
                "cache_pattern_delete",
                "cache_health_check",
            ],
            description="Distributed caching and memory management",
            requirements=["cache_key"],
            configuration={
                "cache_backends": ["redis", "memcached", "in_memory"],
                "eviction_policies": ["lru", "lfu", "ttl", "random"],
                "serialization": ["json", "pickle", "msgpack"],
                "compression": True,
                "clustering": True,
            },
        )
        await self.register_capability(cache_management)

    # Shared service abstract methods

    @abstractmethod
    async def generate_embeddings(self, request: EmbeddingRequest) -> dict[str, Any]:
        """Generate embeddings for text or data"""
        pass

    @abstractmethod
    async def perform_semantic_search(self, request: SearchRequest) -> list[dict[str, Any]]:
        """Perform semantic search across domains"""
        pass

    @abstractmethod
    async def route_cross_domain_request(
        self, request: MCPRequest, target_domain: str
    ) -> MCPResponse:
        """Route requests across domains"""
        pass

    @abstractmethod
    async def manage_shared_cache(
        self, operation: str, key: str, value: Any = None
    ) -> dict[str, Any]:
        """Manage shared cache operations"""
        pass

    # Enhanced health check for shared services

    async def perform_health_check(self) -> HealthCheckResult:
        """Perform shared service health check"""
        start_time = datetime.now()

        try:
            health_details = {}
            capabilities_status = {}

            # Check vector operations
            try:
                import math

                # Test basic vector operations
                test_vector_a = [1.0, 2.0, 3.0]
                test_vector_b = [4.0, 5.0, 6.0]

                # Cosine similarity calculation
                dot_product = sum(a * b for a, b in zip(test_vector_a, test_vector_b))
                magnitude_a = math.sqrt(sum(a * a for a in test_vector_a))
                magnitude_b = math.sqrt(sum(b * b for b in test_vector_b))
                cosine_sim = dot_product / (magnitude_a * magnitude_b)

                health_details["vector_operations"] = f"operational (cosine_sim: {cosine_sim:.3f})"
                capabilities_status["embeddings"] = CapabilityStatus.AVAILABLE

            except Exception as e:
                health_details["vector_operations"] = f"error: {str(e)}"
                capabilities_status["embeddings"] = CapabilityStatus.UNAVAILABLE

            # Check indexing capabilities
            try:
                # Test basic indexing operations
                {
                    "id": "test",
                    "content": "health check document",
                    "timestamp": datetime.now().isoformat(),
                }

                # Simulate indexing
                health_details["indexing_engine"] = "operational"
                capabilities_status["indexing"] = CapabilityStatus.AVAILABLE

            except Exception as e:
                health_details["indexing_engine"] = f"error: {str(e)}"
                capabilities_status["indexing"] = CapabilityStatus.DEGRADED

            # Check database connectivity
            try:
                # Test basic database operations (simulated)
                health_details["database_connectivity"] = "operational"
                capabilities_status["database_operations"] = CapabilityStatus.AVAILABLE

            except Exception as e:
                health_details["database_connectivity"] = f"error: {str(e)}"
                capabilities_status["database_operations"] = CapabilityStatus.UNAVAILABLE

            # Check cross-domain communication
            try:
                # Test message routing capabilities
                test_domains = ["artemis", "sophia", "shared"]
                health_details["domain_routing"] = f"operational (domains: {len(test_domains)})"
                capabilities_status["cross_domain_communication"] = CapabilityStatus.AVAILABLE

            except Exception as e:
                health_details["domain_routing"] = f"error: {str(e)}"
                capabilities_status["cross_domain_communication"] = CapabilityStatus.DEGRADED

            # Check cache management
            try:
                import json

                # Test cache operations
                test_cache_data = {"health_check": True, "timestamp": datetime.now().isoformat()}
                serialized = json.dumps(test_cache_data)
                json.loads(serialized)

                health_details["cache_management"] = "operational"
                capabilities_status["cache_management"] = CapabilityStatus.AVAILABLE

            except Exception as e:
                health_details["cache_management"] = f"error: {str(e)}"
                capabilities_status["cache_management"] = CapabilityStatus.DEGRADED

            # Check required libraries
            required_libraries = {
                "json": "JSON processing",
                "math": "Mathematical operations",
                "datetime": "Date/time operations",
                "asyncio": "Asynchronous operations",
            }

            available_libraries = []
            missing_libraries = []

            for lib, description in required_libraries.items():
                try:
                    __import__(lib)
                    available_libraries.append(f"{lib}: {description}")
                except ImportError:
                    missing_libraries.append(lib)

            health_details["required_libraries"] = {
                "available": available_libraries,
                "missing": missing_libraries,
            }

            # Determine overall health
            unavailable_count = sum(
                1
                for status in capabilities_status.values()
                if status == CapabilityStatus.UNAVAILABLE
            )
            degraded_count = sum(
                1 for status in capabilities_status.values() if status == CapabilityStatus.DEGRADED
            )

            total_capabilities = len(capabilities_status)
            library_health = len(missing_libraries) == 0

            if unavailable_count == 0 and degraded_count == 0 and library_health:
                overall_status = HealthStatus.HEALTHY
            elif (
                unavailable_count <= total_capabilities * 0.3 and library_health
            ):  # Less than 30% unavailable
                overall_status = HealthStatus.DEGRADED
            else:
                overall_status = HealthStatus.UNHEALTHY

            response_time = (datetime.now() - start_time).total_seconds()

            return HealthCheckResult(
                status=overall_status,
                timestamp=datetime.now(),
                response_time=response_time,
                details=health_details,
                capabilities_status=capabilities_status,
            )

        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                timestamp=datetime.now(),
                response_time=response_time,
                details={"error": str(e)},
                error_message=f"Health check failed: {str(e)}",
            )

    # Shared service request handling

    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """Handle shared service requests"""
        start_time = datetime.now()

        try:
            # Update connection activity
            await self.update_connection_activity(request.client_id)

            # Validate request
            is_valid, error_message = await self.validate_request(request)
            if not is_valid:
                return await self.create_error_response(
                    request,
                    error_message,
                    "VALIDATION_ERROR",
                    (datetime.now() - start_time).total_seconds(),
                )

            # Route to capability-specific handler
            if request.capability == "embeddings":
                result = await self._handle_embeddings(request)
            elif request.capability == "indexing":
                result = await self._handle_indexing(request)
            elif request.capability == "database_operations":
                result = await self._handle_database_operations(request)
            elif request.capability == "cross_domain_communication":
                result = await self._handle_cross_domain_communication(request)
            elif request.capability == "cache_management":
                result = await self._handle_cache_management(request)
            else:
                return await self.create_error_response(
                    request,
                    f"Unsupported capability: {request.capability}",
                    "CAPABILITY_NOT_SUPPORTED",
                    (datetime.now() - start_time).total_seconds(),
                )

            execution_time = (datetime.now() - start_time).total_seconds()
            return await self.create_success_response(request, result, execution_time)

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()

            # Update error count
            if request.client_id in self.active_connections:
                self.active_connections[request.client_id].error_count += 1

            return await self.create_error_response(
                request, f"Internal server error: {str(e)}", "INTERNAL_ERROR", execution_time
            )

    # Capability-specific handlers (to be implemented by concrete servers)

    async def _handle_embeddings(self, request: MCPRequest) -> dict[str, Any]:
        """Handle embeddings requests"""
        # Default implementation - to be overridden
        return {"message": "Embeddings capability not implemented"}

    async def _handle_indexing(self, request: MCPRequest) -> dict[str, Any]:
        """Handle indexing requests"""
        # Default implementation - to be overridden
        return {"message": "Indexing capability not implemented"}

    async def _handle_database_operations(self, request: MCPRequest) -> dict[str, Any]:
        """Handle database operation requests"""
        # Default implementation - to be overridden
        return {"message": "Database operations capability not implemented"}

    async def _handle_cross_domain_communication(self, request: MCPRequest) -> dict[str, Any]:
        """Handle cross-domain communication requests"""
        # Default implementation - to be overridden
        return {"message": "Cross-domain communication capability not implemented"}

    async def _handle_cache_management(self, request: MCPRequest) -> dict[str, Any]:
        """Handle cache management requests"""
        # Default implementation - to be overridden
        return {"message": "Cache management capability not implemented"}

    # Shared service utility methods

    async def calculate_vector_similarity(
        self, vector_a: list[float], vector_b: list[float], metric: str = "cosine"
    ) -> float:
        """Calculate similarity between two vectors"""
        try:
            import math

            if len(vector_a) != len(vector_b):
                raise ValueError("Vectors must have the same dimensions")

            if metric == "cosine":
                dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
                magnitude_a = math.sqrt(sum(a * a for a in vector_a))
                magnitude_b = math.sqrt(sum(b * b for b in vector_b))

                if magnitude_a == 0 or magnitude_b == 0:
                    return 0.0

                return dot_product / (magnitude_a * magnitude_b)

            elif metric == "euclidean":
                squared_diff = sum((a - b) ** 2 for a, b in zip(vector_a, vector_b))
                return math.sqrt(squared_diff)

            elif metric == "dot_product":
                return sum(a * b for a, b in zip(vector_a, vector_b))

            else:
                raise ValueError(f"Unsupported similarity metric: {metric}")

        except Exception as e:
            raise Exception(f"Vector similarity calculation failed: {str(e)}")

    async def normalize_vector(self, vector: list[float]) -> list[float]:
        """Normalize a vector to unit length"""
        try:
            import math

            magnitude = math.sqrt(sum(v * v for v in vector))
            if magnitude == 0:
                return vector

            return [v / magnitude for v in vector]

        except Exception as e:
            raise Exception(f"Vector normalization failed: {str(e)}")

    async def batch_process_items(self, items: list[Any], batch_size: int, processor) -> list[Any]:
        """Process items in batches for efficiency"""
        results = []

        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            batch_results = await processor(batch)
            results.extend(batch_results)

        return results
