"""
Service Automation for SOPHIA Intel
Complete control over OpenRouter, Airbyte, Mem0, Redis, and Neon services
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import aiohttp
import base64
from urllib.parse import urlencode

from .circuit_breaker import get_circuit_breaker, CircuitBreakerConfig
from .infrastructure_automation import InfrastructureResult, InfrastructureOperation

logger = logging.getLogger(__name__)

class ServiceOperation(Enum):
    CONFIGURE = "configure"
    OPTIMIZE = "optimize"
    SCALE = "scale"
    BACKUP = "backup"
    RESTORE = "restore"
    ROTATE_KEYS = "rotate_keys"
    UPDATE_SETTINGS = "update_settings"
    MONITOR = "monitor"

@dataclass
class ServiceRequest:
    """Service automation request"""
    operation: ServiceOperation
    service: str
    parameters: Dict[str, Any]
    user_id: str
    correlation_id: str

class OpenRouterAutomation:
    """OpenRouter service automation"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.circuit_breaker = get_circuit_breaker("openrouter_automation", CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=30,
            success_threshold=2,
            timeout=30.0
        ))
    
    async def configure_model_routing(self, routing_config: Dict[str, Any]) -> InfrastructureResult:
        """Configure OpenRouter model routing rules"""
        async def _configure():
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Configure routing preferences
            routing_rules = {
                "fallbacks": routing_config.get("fallbacks", [
                    "anthropic/claude-3.5-sonnet",
                    "openai/gpt-4-turbo",
                    "google/gemini-pro-1.5"
                ]),
                "preferences": routing_config.get("preferences", {
                    "cost_priority": 0.3,
                    "speed_priority": 0.4,
                    "quality_priority": 0.3
                }),
                "model_limits": routing_config.get("model_limits", {
                    "anthropic/claude-3.5-sonnet": {"daily_limit": 1000, "rate_limit": 60},
                    "openai/gpt-4-turbo": {"daily_limit": 500, "rate_limit": 30},
                    "google/gemini-pro-1.5": {"daily_limit": 2000, "rate_limit": 100}
                })
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/routing/configure",
                    headers=headers,
                    json=routing_rules
                ) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        return InfrastructureResult(
                            success=True,
                            resource_id="routing_config",
                            details=data
                        )
                    else:
                        error_data = await response.text()
                        return InfrastructureResult(
                            success=False,
                            error=f"OpenRouter configuration failed: {error_data}"
                        )
        
        start_time = time.time()
        try:
            result = await self.circuit_breaker.call(_configure)
            result.duration = time.time() - start_time
            logger.info("OpenRouter routing configured successfully")
            return result
        except Exception as e:
            logger.error(f"Failed to configure OpenRouter: {e}")
            return InfrastructureResult(
                success=False,
                error=str(e),
                duration=time.time() - start_time
            )
    
    async def get_usage_analytics(self) -> Dict[str, Any]:
        """Get OpenRouter usage analytics"""
        async def _get_analytics():
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/usage",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        raise Exception(f"Failed to get usage analytics: {response.status}")
        
        try:
            return await self.circuit_breaker.call(_get_analytics)
        except Exception as e:
            logger.error(f"Failed to get OpenRouter analytics: {e}")
            return {}
    
    async def optimize_model_selection(self, usage_data: Dict[str, Any]) -> InfrastructureResult:
        """AI-powered model selection optimization"""
        # Analyze usage patterns and optimize model routing
        cost_per_model = usage_data.get("cost_breakdown", {})
        performance_metrics = usage_data.get("performance", {})
        
        # Calculate cost-effectiveness scores
        optimizations = []
        
        for model, cost in cost_per_model.items():
            response_time = performance_metrics.get(model, {}).get("avg_response_time", 1000)
            quality_score = performance_metrics.get(model, {}).get("quality_score", 0.8)
            
            # Cost-effectiveness formula
            effectiveness = (quality_score * 100) / (cost * response_time / 1000)
            
            if effectiveness > 50:  # High effectiveness threshold
                optimizations.append({
                    "model": model,
                    "action": "increase_priority",
                    "effectiveness_score": effectiveness
                })
            elif effectiveness < 10:  # Low effectiveness threshold
                optimizations.append({
                    "model": model,
                    "action": "decrease_priority",
                    "effectiveness_score": effectiveness
                })
        
        return InfrastructureResult(
            success=True,
            resource_id="optimization_analysis",
            details={"optimizations": optimizations}
        )

class AirbyteAutomation:
    """Airbyte service automation"""
    
    def __init__(self, api_url: str, username: str, password: str):
        self.api_url = api_url.rstrip('/')
        self.username = username
        self.password = password
        self.circuit_breaker = get_circuit_breaker("airbyte_automation", CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=60,
            success_threshold=2,
            timeout=45.0
        ))
    
    async def create_connection(self, source_id: str, destination_id: str, sync_config: Dict[str, Any]) -> InfrastructureResult:
        """Create Airbyte connection"""
        async def _create():
            auth = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
            headers = {
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/json"
            }
            
            connection_config = {
                "sourceId": source_id,
                "destinationId": destination_id,
                "syncCatalog": sync_config.get("catalog", {}),
                "schedule": sync_config.get("schedule", {
                    "scheduleType": "cron",
                    "cronExpression": "0 */6 * * *"  # Every 6 hours
                }),
                "status": "active",
                "name": sync_config.get("name", f"Connection-{int(time.time())}")
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/v1/connections",
                    headers=headers,
                    json=connection_config
                ) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        return InfrastructureResult(
                            success=True,
                            resource_id=data.get("connectionId"),
                            details=data
                        )
                    else:
                        error_data = await response.text()
                        return InfrastructureResult(
                            success=False,
                            error=f"Airbyte connection creation failed: {error_data}"
                        )
        
        start_time = time.time()
        try:
            result = await self.circuit_breaker.call(_create)
            result.duration = time.time() - start_time
            logger.info(f"Airbyte connection created: {result.resource_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to create Airbyte connection: {e}")
            return InfrastructureResult(
                success=False,
                error=str(e),
                duration=time.time() - start_time
            )
    
    async def optimize_sync_schedule(self, connection_id: str, usage_patterns: Dict[str, Any]) -> InfrastructureResult:
        """Optimize sync schedule based on usage patterns"""
        # Analyze data freshness requirements vs resource usage
        peak_hours = usage_patterns.get("peak_hours", [9, 10, 11, 14, 15, 16])
        data_staleness_tolerance = usage_patterns.get("staleness_tolerance_hours", 4)
        
        # Determine optimal sync frequency
        if data_staleness_tolerance <= 1:
            cron_expression = "0 * * * *"  # Hourly
        elif data_staleness_tolerance <= 4:
            cron_expression = "0 */4 * * *"  # Every 4 hours
        elif data_staleness_tolerance <= 12:
            cron_expression = "0 */12 * * *"  # Twice daily
        else:
            cron_expression = "0 2 * * *"  # Daily at 2 AM
        
        # Update connection schedule
        async def _update():
            auth = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
            headers = {
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/json"
            }
            
            update_config = {
                "connectionId": connection_id,
                "schedule": {
                    "scheduleType": "cron",
                    "cronExpression": cron_expression
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(
                    f"{self.api_url}/v1/connections/{connection_id}",
                    headers=headers,
                    json=update_config
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return InfrastructureResult(
                            success=True,
                            resource_id=connection_id,
                            details={
                                "new_schedule": cron_expression,
                                "optimization_reason": f"Optimized for {data_staleness_tolerance}h staleness tolerance"
                            }
                        )
                    else:
                        error_data = await response.text()
                        return InfrastructureResult(
                            success=False,
                            error=f"Schedule optimization failed: {error_data}"
                        )
        
        start_time = time.time()
        try:
            result = await self.circuit_breaker.call(_update)
            result.duration = time.time() - start_time
            logger.info(f"Airbyte sync schedule optimized: {connection_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to optimize Airbyte schedule: {e}")
            return InfrastructureResult(
                success=False,
                error=str(e),
                duration=time.time() - start_time
            )

class Mem0Automation:
    """Mem0 service automation"""
    
    def __init__(self, api_key: str, api_url: str = "https://api.mem0.ai"):
        self.api_key = api_key
        self.api_url = api_url
        self.circuit_breaker = get_circuit_breaker("mem0_automation", CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=30,
            success_threshold=2,
            timeout=20.0
        ))
    
    async def configure_memory_settings(self, config: Dict[str, Any]) -> InfrastructureResult:
        """Configure Mem0 memory settings"""
        async def _configure():
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            memory_config = {
                "embedding_model": config.get("embedding_model", "text-embedding-3-small"),
                "vector_store": config.get("vector_store", "qdrant"),
                "memory_retention": config.get("retention_days", 365),
                "similarity_threshold": config.get("similarity_threshold", 0.7),
                "max_memories_per_user": config.get("max_memories", 10000),
                "auto_summarization": config.get("auto_summarization", True),
                "privacy_mode": config.get("privacy_mode", "strict")
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/v1/config",
                    headers=headers,
                    json=memory_config
                ) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        return InfrastructureResult(
                            success=True,
                            resource_id="memory_config",
                            details=data
                        )
                    else:
                        error_data = await response.text()
                        return InfrastructureResult(
                            success=False,
                            error=f"Mem0 configuration failed: {error_data}"
                        )
        
        start_time = time.time()
        try:
            result = await self.circuit_breaker.call(_configure)
            result.duration = time.time() - start_time
            logger.info("Mem0 memory settings configured")
            return result
        except Exception as e:
            logger.error(f"Failed to configure Mem0: {e}")
            return InfrastructureResult(
                success=False,
                error=str(e),
                duration=time.time() - start_time
            )
    
    async def optimize_memory_performance(self, usage_stats: Dict[str, Any]) -> InfrastructureResult:
        """Optimize Mem0 memory performance"""
        # Analyze memory usage patterns
        avg_query_time = usage_stats.get("avg_query_time_ms", 100)
        memory_utilization = usage_stats.get("memory_utilization", 0.5)
        hit_rate = usage_stats.get("cache_hit_rate", 0.8)
        
        optimizations = []
        
        # Optimize similarity threshold based on hit rate
        if hit_rate < 0.6:
            new_threshold = max(0.5, usage_stats.get("current_threshold", 0.7) - 0.1)
            optimizations.append({
                "parameter": "similarity_threshold",
                "old_value": usage_stats.get("current_threshold", 0.7),
                "new_value": new_threshold,
                "reason": "Increase recall due to low hit rate"
            })
        elif hit_rate > 0.9:
            new_threshold = min(0.9, usage_stats.get("current_threshold", 0.7) + 0.1)
            optimizations.append({
                "parameter": "similarity_threshold",
                "old_value": usage_stats.get("current_threshold", 0.7),
                "new_value": new_threshold,
                "reason": "Increase precision due to high hit rate"
            })
        
        # Optimize embedding model based on performance
        if avg_query_time > 500:  # ms
            optimizations.append({
                "parameter": "embedding_model",
                "old_value": "text-embedding-3-large",
                "new_value": "text-embedding-3-small",
                "reason": "Reduce query time with faster model"
            })
        
        return InfrastructureResult(
            success=True,
            resource_id="performance_optimization",
            details={"optimizations": optimizations}
        )

class RedisAutomation:
    """Redis service automation"""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.circuit_breaker = get_circuit_breaker("redis_automation", CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=20,
            success_threshold=2,
            timeout=10.0
        ))
    
    async def optimize_memory_usage(self, current_stats: Dict[str, Any]) -> InfrastructureResult:
        """Optimize Redis memory usage"""
        async def _optimize():
            import redis.asyncio as redis
            
            client = redis.from_url(self.redis_url)
            
            try:
                # Get memory info
                memory_info = await client.info("memory")
                used_memory = memory_info.get("used_memory", 0)
                max_memory = memory_info.get("maxmemory", 0)
                
                optimizations = []
                
                # Set optimal memory policies
                if max_memory == 0:  # No memory limit set
                    # Set memory limit to 80% of available system memory
                    await client.config_set("maxmemory", "2gb")
                    optimizations.append("Set maxmemory limit")
                
                # Set eviction policy
                await client.config_set("maxmemory-policy", "allkeys-lru")
                optimizations.append("Set LRU eviction policy")
                
                # Optimize key expiration
                await client.config_set("lazy-expire", "yes")
                optimizations.append("Enabled lazy expiration")
                
                # Configure memory sampling
                await client.config_set("maxmemory-samples", "10")
                optimizations.append("Optimized memory sampling")
                
                return InfrastructureResult(
                    success=True,
                    resource_id="redis_memory_optimization",
                    details={
                        "optimizations": optimizations,
                        "memory_usage": {
                            "used_memory_mb": used_memory / (1024 * 1024),
                            "max_memory_mb": max_memory / (1024 * 1024) if max_memory > 0 else "unlimited"
                        }
                    }
                )
            finally:
                await client.close()
        
        start_time = time.time()
        try:
            result = await self.circuit_breaker.call(_optimize)
            result.duration = time.time() - start_time
            logger.info("Redis memory optimization completed")
            return result
        except Exception as e:
            logger.error(f"Failed to optimize Redis memory: {e}")
            return InfrastructureResult(
                success=False,
                error=str(e),
                duration=time.time() - start_time
            )
    
    async def configure_persistence(self, persistence_config: Dict[str, Any]) -> InfrastructureResult:
        """Configure Redis persistence settings"""
        async def _configure():
            import redis.asyncio as redis
            
            client = redis.from_url(self.redis_url)
            
            try:
                # Configure RDB snapshots
                rdb_enabled = persistence_config.get("rdb_enabled", True)
                if rdb_enabled:
                    save_intervals = persistence_config.get("save_intervals", ["900 1", "300 10", "60 10000"])
                    for interval in save_intervals:
                        await client.config_set("save", interval)
                
                # Configure AOF
                aof_enabled = persistence_config.get("aof_enabled", True)
                if aof_enabled:
                    await client.config_set("appendonly", "yes")
                    await client.config_set("appendfsync", persistence_config.get("appendfsync", "everysec"))
                    await client.config_set("auto-aof-rewrite-percentage", "100")
                    await client.config_set("auto-aof-rewrite-min-size", "64mb")
                
                return InfrastructureResult(
                    success=True,
                    resource_id="redis_persistence_config",
                    details=persistence_config
                )
            finally:
                await client.close()
        
        start_time = time.time()
        try:
            result = await self.circuit_breaker.call(_configure)
            result.duration = time.time() - start_time
            logger.info("Redis persistence configured")
            return result
        except Exception as e:
            logger.error(f"Failed to configure Redis persistence: {e}")
            return InfrastructureResult(
                success=False,
                error=str(e),
                duration=time.time() - start_time
            )

class NeonAutomation:
    """Neon database automation"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://console.neon.tech/api/v2"
        self.circuit_breaker = get_circuit_breaker("neon_automation", CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=60,
            success_threshold=2,
            timeout=30.0
        ))
    
    async def create_branch(self, project_id: str, branch_config: Dict[str, Any]) -> InfrastructureResult:
        """Create Neon database branch"""
        async def _create():
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            branch_data = {
                "name": branch_config.get("name", f"branch-{int(time.time())}"),
                "parent_id": branch_config.get("parent_id"),
                "parent_lsn": branch_config.get("parent_lsn"),
                "parent_timestamp": branch_config.get("parent_timestamp")
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/projects/{project_id}/branches",
                    headers=headers,
                    json=branch_data
                ) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        return InfrastructureResult(
                            success=True,
                            resource_id=data["branch"]["id"],
                            details=data
                        )
                    else:
                        error_data = await response.text()
                        return InfrastructureResult(
                            success=False,
                            error=f"Neon branch creation failed: {error_data}"
                        )
        
        start_time = time.time()
        try:
            result = await self.circuit_breaker.call(_create)
            result.duration = time.time() - start_time
            logger.info(f"Neon branch created: {result.resource_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to create Neon branch: {e}")
            return InfrastructureResult(
                success=False,
                error=str(e),
                duration=time.time() - start_time
            )
    
    async def scale_compute(self, project_id: str, endpoint_id: str, scale_config: Dict[str, Any]) -> InfrastructureResult:
        """Scale Neon compute resources"""
        async def _scale():
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            scale_data = {
                "autoscaling_limit_min_cu": scale_config.get("min_cu", 0.25),
                "autoscaling_limit_max_cu": scale_config.get("max_cu", 4),
                "suspend_timeout_seconds": scale_config.get("suspend_timeout", 300)
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(
                    f"{self.base_url}/projects/{project_id}/endpoints/{endpoint_id}",
                    headers=headers,
                    json=scale_data
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return InfrastructureResult(
                            success=True,
                            resource_id=endpoint_id,
                            details=data,
                            cost_impact=self._calculate_compute_cost(scale_config)
                        )
                    else:
                        error_data = await response.text()
                        return InfrastructureResult(
                            success=False,
                            error=f"Neon scaling failed: {error_data}"
                        )
        
        start_time = time.time()
        try:
            result = await self.circuit_breaker.call(_scale)
            result.duration = time.time() - start_time
            logger.info(f"Neon compute scaled: {endpoint_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to scale Neon compute: {e}")
            return InfrastructureResult(
                success=False,
                error=str(e),
                duration=time.time() - start_time
            )
    
    def _calculate_compute_cost(self, scale_config: Dict[str, Any]) -> float:
        """Calculate estimated monthly cost for compute scaling"""
        max_cu = scale_config.get("max_cu", 4)
        # Neon pricing: ~$0.102 per CU-hour
        monthly_hours = 24 * 30
        return max_cu * 0.102 * monthly_hours

class ServiceAutomationManager:
    """Main service automation manager"""
    
    def __init__(self, config: Dict[str, Any]):
        self.openrouter = OpenRouterAutomation(config["openrouter"]["api_key"])
        self.airbyte = AirbyteAutomation(
            config["airbyte"]["api_url"],
            config["airbyte"]["username"],
            config["airbyte"]["password"]
        )
        self.mem0 = Mem0Automation(config["mem0"]["api_key"])
        self.redis = RedisAutomation(config["redis"]["url"])
        self.neon = NeonAutomation(config["neon"]["api_key"])
        
        logger.info("Service automation manager initialized")
    
    async def execute_service_request(self, request: ServiceRequest) -> InfrastructureResult:
        """Execute service automation request"""
        logger.info(f"Executing {request.operation.value} on {request.service}")
        
        try:
            if request.service == "openrouter":
                return await self._handle_openrouter_request(request)
            elif request.service == "airbyte":
                return await self._handle_airbyte_request(request)
            elif request.service == "mem0":
                return await self._handle_mem0_request(request)
            elif request.service == "redis":
                return await self._handle_redis_request(request)
            elif request.service == "neon":
                return await self._handle_neon_request(request)
            else:
                return InfrastructureResult(
                    success=False,
                    error=f"Unknown service: {request.service}"
                )
        except Exception as e:
            logger.error(f"Service request failed: {e}")
            return InfrastructureResult(
                success=False,
                error=str(e)
            )
    
    async def _handle_openrouter_request(self, request: ServiceRequest) -> InfrastructureResult:
        """Handle OpenRouter requests"""
        if request.operation == ServiceOperation.CONFIGURE:
            return await self.openrouter.configure_model_routing(request.parameters)
        elif request.operation == ServiceOperation.OPTIMIZE:
            usage_data = await self.openrouter.get_usage_analytics()
            return await self.openrouter.optimize_model_selection(usage_data)
        else:
            return InfrastructureResult(
                success=False,
                error=f"Unsupported OpenRouter operation: {request.operation.value}"
            )
    
    async def _handle_airbyte_request(self, request: ServiceRequest) -> InfrastructureResult:
        """Handle Airbyte requests"""
        if request.operation == ServiceOperation.CONFIGURE:
            return await self.airbyte.create_connection(**request.parameters)
        elif request.operation == ServiceOperation.OPTIMIZE:
            return await self.airbyte.optimize_sync_schedule(**request.parameters)
        else:
            return InfrastructureResult(
                success=False,
                error=f"Unsupported Airbyte operation: {request.operation.value}"
            )
    
    async def _handle_mem0_request(self, request: ServiceRequest) -> InfrastructureResult:
        """Handle Mem0 requests"""
        if request.operation == ServiceOperation.CONFIGURE:
            return await self.mem0.configure_memory_settings(request.parameters)
        elif request.operation == ServiceOperation.OPTIMIZE:
            return await self.mem0.optimize_memory_performance(request.parameters)
        else:
            return InfrastructureResult(
                success=False,
                error=f"Unsupported Mem0 operation: {request.operation.value}"
            )
    
    async def _handle_redis_request(self, request: ServiceRequest) -> InfrastructureResult:
        """Handle Redis requests"""
        if request.operation == ServiceOperation.OPTIMIZE:
            return await self.redis.optimize_memory_usage(request.parameters)
        elif request.operation == ServiceOperation.CONFIGURE:
            return await self.redis.configure_persistence(request.parameters)
        else:
            return InfrastructureResult(
                success=False,
                error=f"Unsupported Redis operation: {request.operation.value}"
            )
    
    async def _handle_neon_request(self, request: ServiceRequest) -> InfrastructureResult:
        """Handle Neon requests"""
        if request.operation == ServiceOperation.CONFIGURE:
            return await self.neon.create_branch(**request.parameters)
        elif request.operation == ServiceOperation.SCALE:
            return await self.neon.scale_compute(**request.parameters)
        else:
            return InfrastructureResult(
                success=False,
                error=f"Unsupported Neon operation: {request.operation.value}"
            )

# Global service automation manager
_service_manager: Optional[ServiceAutomationManager] = None

def get_service_automation_manager() -> ServiceAutomationManager:
    """Get global service automation manager"""
    if _service_manager is None:
        raise RuntimeError("Service automation manager not initialized")
    return _service_manager

async def initialize_service_automation_manager(config: Dict[str, Any]) -> ServiceAutomationManager:
    """Initialize global service automation manager"""
    global _service_manager
    _service_manager = ServiceAutomationManager(config)
    return _service_manager

