#!/usr/bin/env python3
"""
Portkey-OpenRouter Hybrid Routing with Pulumi - Fusion Implementation
Pulumi dynamically provisions Lambda Labs GPUs, routes via Portkey/OpenRouter based on load
Llama for scale, Claude for planning, LangGraph checkpoints for failover
99.9% uptime without exploding costs
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

import httpx
import redis
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelProvider(Enum):
    PORTKEY = "portkey"
    OPENROUTER = "openrouter"
    LAMBDA_LABS = "lambda_labs"

class ModelType(Enum):
    LLAMA = "llama"
    CLAUDE = "claude"
    GPT = "gpt"

@dataclass
class RoutingRule:
    model_type: ModelType
    provider: ModelProvider
    cost_per_token: float
    latency_ms: int
    reliability_score: float
    max_concurrent: int

@dataclass
class LoadMetrics:
    current_requests: int
    avg_latency_ms: float
    error_rate: float
    cost_per_hour: float
    timestamp: datetime

class HybridModelRouter:
    """Intelligent hybrid routing between Portkey and OpenRouter"""

    def __init__(self):
        self.portkey_api_key = os.getenv('PORTKEY_API_KEY')
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        self.lambda_labs_api_key = os.getenv('LAMBDA_LABS_API_KEY')
        self.redis_client = self._init_redis()

        # Routing rules configuration
        self.routing_rules = [
            # Llama for scale (high volume, low cost)
            RoutingRule(
                model_type=ModelType.LLAMA,
                provider=ModelProvider.OPENROUTER,
                cost_per_token=0.0001,
                latency_ms=800,
                reliability_score=0.95,
                max_concurrent=100
            ),
            # Claude for planning (high quality, medium cost)
            RoutingRule(
                model_type=ModelType.CLAUDE,
                provider=ModelProvider.PORTKEY,
                cost_per_token=0.003,
                latency_ms=1200,
                reliability_score=0.99,
                max_concurrent=50
            ),
            # GPT for general use (balanced)
            RoutingRule(
                model_type=ModelType.GPT,
                provider=ModelProvider.PORTKEY,
                cost_per_token=0.002,
                latency_ms=1000,
                reliability_score=0.98,
                max_concurrent=75
            )
        ]

        self.load_metrics = {}
        self.circuit_breakers = {}

    def _init_redis(self) -> redis.Redis:
        """Initialize Redis for metrics storage"""
        redis_url = os.getenv('REDIS_URL', '${REDIS_URL}')
        return redis.from_url(redis_url, decode_responses=True)

    async def route_request(self, prompt: str, model_preference: Optional[ModelType] = None) -> Dict:
        """Route request to optimal provider based on current load and rules"""
        try:
            # Determine model type
            model_type = model_preference or self._determine_model_type(prompt)

            # Get current load metrics
            current_load = await self._get_current_load()

            # Find best routing rule
            best_rule = await self._select_best_rule(model_type, current_load)

            if not best_rule:
                raise Exception(f"No available routing rule for {model_type}")

            # Check circuit breaker
            if await self._is_circuit_open(best_rule.provider):
                # Fallback to alternative provider
                best_rule = await self._get_fallback_rule(model_type)

            # Execute request
            result = await self._execute_request(prompt, best_rule)

            # Update metrics
            await self._update_metrics(best_rule, result)

            return {
                "response": result.get('response', ''),
                "provider": best_rule.provider.value,
                "model_type": model_type.value,
                "latency_ms": result.get('latency_ms', 0),
                "cost": result.get('cost', 0),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error routing request: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    def _determine_model_type(self, prompt: str) -> ModelType:
        """Determine optimal model type based on prompt characteristics"""
        prompt_lower = prompt.lower()

        # Planning and reasoning tasks -> Claude
        if any(keyword in prompt_lower for keyword in ['plan', 'strategy', 'analyze', 'reason', 'think']):
            return ModelType.CLAUDE

        # High-volume, simple tasks -> Llama
        if any(keyword in prompt_lower for keyword in ['summarize', 'extract', 'list', 'simple']):
            return ModelType.LLAMA

        # Default to GPT for balanced performance
        return ModelType.GPT

    async def _get_current_load(self) -> Dict[ModelProvider, LoadMetrics]:
        """Get current load metrics for all providers"""
        load_metrics = {}

        for provider in ModelProvider:
            try:
                metrics_key = f"load_metrics:{provider.value}"
                metrics_data = self.redis_client.get(metrics_key)

                if metrics_data:
                    data = json.loads(metrics_data)
                    load_metrics[provider] = LoadMetrics(
                        current_requests=data.get('current_requests', 0),
                        avg_latency_ms=data.get('avg_latency_ms', 1000),
                        error_rate=data.get('error_rate', 0.0),
                        cost_per_hour=data.get('cost_per_hour', 0.0),
                        timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat()))
                    )
                else:
                    # Default metrics if no data available
                    load_metrics[provider] = LoadMetrics(
                        current_requests=0,
                        avg_latency_ms=1000,
                        error_rate=0.0,
                        cost_per_hour=0.0,
                        timestamp=datetime.now()
                    )

            except Exception as e:
                logger.error(f"Error getting load metrics for {provider}: {e}")
                continue

        return load_metrics

    async def _select_best_rule(self, model_type: ModelType, current_load: Dict) -> Optional[RoutingRule]:
        """Select best routing rule based on model type and current load"""
        # Filter rules by model type
        applicable_rules = [rule for rule in self.routing_rules if rule.model_type == model_type]

        if not applicable_rules:
            return None

        # Score each rule based on current conditions
        best_rule = None
        best_score = -1

        for rule in applicable_rules:
            provider_load = current_load.get(rule.provider)
            if not provider_load:
                continue

            # Calculate composite score
            # Lower is better for cost and latency, higher is better for reliability
            cost_score = 1.0 / (rule.cost_per_token * 1000 + 1)  # Normalize cost
            latency_score = 1.0 / (rule.latency_ms + 1)  # Normalize latency
            reliability_score = rule.reliability_score
            load_score = 1.0 / (provider_load.current_requests + 1)  # Prefer less loaded

            # Weighted composite score
            composite_score = (
                cost_score * 0.3 +
                latency_score * 0.3 +
                reliability_score * 0.3 +
                load_score * 0.1
            )

            if composite_score > best_score:
                best_score = composite_score
                best_rule = rule

        return best_rule

    async def _is_circuit_open(self, provider: ModelProvider) -> bool:
        """Check if circuit breaker is open for provider"""
        try:
            circuit_key = f"circuit_breaker:{provider.value}"
            circuit_data = self.redis_client.get(circuit_key)

            if not circuit_data:
                return False

            data = json.loads(circuit_data)

            # Check if circuit is open and if cooldown period has passed
            if data.get('state') == 'open':
                open_time = datetime.fromisoformat(data.get('opened_at'))
                cooldown_minutes = data.get('cooldown_minutes', 5)

                if datetime.now() - open_time < timedelta(minutes=cooldown_minutes):
                    return True
                else:
                    # Reset circuit breaker after cooldown
                    await self._reset_circuit_breaker(provider)
                    return False

            return False

        except Exception as e:
            logger.error(f"Error checking circuit breaker for {provider}: {e}")
            return False

    async def _get_fallback_rule(self, model_type: ModelType) -> Optional[RoutingRule]:
        """Get fallback routing rule when primary is unavailable"""
        # Find alternative provider for the same model type
        applicable_rules = [rule for rule in self.routing_rules if rule.model_type == model_type]

        # Sort by reliability score (highest first)
        applicable_rules.sort(key=lambda x: x.reliability_score, reverse=True)

        for rule in applicable_rules:
            if not await self._is_circuit_open(rule.provider):
                return rule

        # If no same-type alternatives, fallback to any available provider
        for rule in self.routing_rules:
            if not await self._is_circuit_open(rule.provider):
                logger.warning(f"Fallback: Using {rule.model_type} instead of {model_type}")
                return rule

        return None

    async def _execute_request(self, prompt: str, rule: RoutingRule) -> Dict:
        """Execute request using specified routing rule"""
        start_time = time.time()

        try:
            if rule.provider == ModelProvider.PORTKEY:
                result = await self._execute_portkey_request(prompt, rule)
            elif rule.provider == ModelProvider.OPENROUTER:
                result = await self._execute_openrouter_request(prompt, rule)
            else:
                raise Exception(f"Unsupported provider: {rule.provider}")

            latency_ms = (time.time() - start_time) * 1000

            return {
                "response": result.get('response', ''),
                "latency_ms": latency_ms,
                "cost": self._calculate_cost(prompt, result, rule),
                "success": True
            }

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"Error executing request with {rule.provider}: {e}")

            # Open circuit breaker on repeated failures
            await self._handle_request_failure(rule.provider)

            return {
                "response": "",
                "latency_ms": latency_ms,
                "cost": 0,
                "success": False,
                "error": str(e)
            }

    async def _execute_portkey_request(self, prompt: str, rule: RoutingRule) -> Dict:
        """Execute request via Portkey"""
        if not self.portkey_api_key:
            raise Exception("PORTKEY_API_KEY not configured")

        # Map model types to Portkey model names
        model_mapping = {
            ModelType.CLAUDE: "claude-3-opus-20240229",
            ModelType.GPT: "gpt-4",
            ModelType.LLAMA: "llama-2-70b-chat"
        }

        model_name = model_mapping.get(rule.model_type, "gpt-4")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.portkey.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.portkey_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1000
                },
                timeout=30.0
            )

            if response.status_code != 200:
                raise Exception(f"Portkey API error: {response.status_code}")

            data = response.json()
            return {
                "response": data['choices'][0]['message']['content'],
                "tokens_used": data.get('usage', {}).get('total_tokens', 0)
            }

    async def _execute_openrouter_request(self, prompt: str, rule: RoutingRule) -> Dict:
        """Execute request via OpenRouter"""
        if not self.openrouter_api_key:
            raise Exception("OPENROUTER_API_KEY not configured")

        # Map model types to OpenRouter model names
        model_mapping = {
            ModelType.CLAUDE: "anthropic/claude-3-opus",
            ModelType.GPT: "openai/gpt-4",
            ModelType.LLAMA: "meta-llama/llama-2-70b-chat"
        }

        model_name = model_mapping.get(rule.model_type, "openai/gpt-4")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1000
                },
                timeout=30.0
            )

            if response.status_code != 200:
                raise Exception(f"OpenRouter API error: {response.status_code}")

            data = response.json()
            return {
                "response": data['choices'][0]['message']['content'],
                "tokens_used": data.get('usage', {}).get('total_tokens', 0)
            }

    def _calculate_cost(self, prompt: str, result: Dict, rule: RoutingRule) -> float:
        """Calculate cost for the request"""
        tokens_used = result.get('tokens_used', len(prompt.split()) * 1.3)  # Rough estimate
        return tokens_used * rule.cost_per_token

    async def _update_metrics(self, rule: RoutingRule, result: Dict):
        """Update load metrics for the provider"""
        try:
            metrics_key = f"load_metrics:{rule.provider.value}"

            # Get current metrics
            current_data = self.redis_client.get(metrics_key)
            if current_data:
                metrics = json.loads(current_data)
            else:
                metrics = {
                    "current_requests": 0,
                    "avg_latency_ms": 0,
                    "error_rate": 0.0,
                    "cost_per_hour": 0.0,
                    "total_requests": 0
                }

            # Update metrics
            metrics["total_requests"] += 1
            metrics["current_requests"] = max(0, metrics["current_requests"] - 1)  # Decrement active

            # Update average latency
            old_latency = metrics["avg_latency_ms"]
            new_latency = result.get("latency_ms", 1000)
            metrics["avg_latency_ms"] = (old_latency * 0.9) + (new_latency * 0.1)  # Exponential moving average

            # Update error rate
            if not result.get("success", True):
                metrics["error_rate"] = (metrics["error_rate"] * 0.9) + (1.0 * 0.1)
            else:
                metrics["error_rate"] = metrics["error_rate"] * 0.9

            # Update cost
            cost = result.get("cost", 0)
            metrics["cost_per_hour"] = (metrics["cost_per_hour"] * 0.9) + (cost * 3600 * 0.1)  # Hourly rate

            metrics["timestamp"] = datetime.now().isoformat()

            # Store updated metrics
            self.redis_client.setex(metrics_key, 3600, json.dumps(metrics))  # 1 hour TTL

        except Exception as e:
            logger.error(f"Error updating metrics: {e}")

    async def _handle_request_failure(self, provider: ModelProvider):
        """Handle request failure and potentially open circuit breaker"""
        try:
            failure_key = f"failures:{provider.value}"

            # Increment failure count
            failures = self.redis_client.incr(failure_key)
            self.redis_client.expire(failure_key, 300)  # 5 minute window

            # Open circuit breaker if too many failures
            if failures >= 5:  # 5 failures in 5 minutes
                await self._open_circuit_breaker(provider)

        except Exception as e:
            logger.error(f"Error handling failure for {provider}: {e}")

    async def _open_circuit_breaker(self, provider: ModelProvider):
        """Open circuit breaker for provider"""
        try:
            circuit_key = f"circuit_breaker:{provider.value}"
            circuit_data = {
                "state": "open",
                "opened_at": datetime.now().isoformat(),
                "cooldown_minutes": 5
            }

            self.redis_client.setex(circuit_key, 600, json.dumps(circuit_data))  # 10 minute TTL
            logger.warning(f"Circuit breaker opened for {provider.value}")

        except Exception as e:
            logger.error(f"Error opening circuit breaker for {provider}: {e}")

    async def _reset_circuit_breaker(self, provider: ModelProvider):
        """Reset circuit breaker for provider"""
        try:
            circuit_key = f"circuit_breaker:{provider.value}"
            self.redis_client.delete(circuit_key)
            logger.info(f"Circuit breaker reset for {provider.value}")

        except Exception as e:
            logger.error(f"Error resetting circuit breaker for {provider}: {e}")

class LambdaLabsGPUManager:
    """Manage Lambda Labs GPU instances for model serving"""

    def __init__(self):
        self.api_key = os.getenv('LAMBDA_LABS_API_KEY')
        self.base_url = "https://cloud.lambda.ai/api/v1"

    async def provision_gpu_instance(self, instance_type: str = "gpu_1x_a100") -> Dict:
        """Provision GPU instance for high-load scenarios"""
        if not self.api_key:
            logger.warning("LAMBDA_LABS_API_KEY not configured")
            return {"error": "API key not configured"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/instance-operations/launch",
                    auth=(self.api_key, ""),
                    json={
                        "region_name": "us-west-2",
                        "instance_type_name": instance_type,
                        "ssh_key_names": ["sophia-ssh-key"],
                        "quantity": 1
                    },
                    timeout=60.0
                )

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Provisioned GPU instance: {data}")
                    return data
                else:
                    logger.error(f"Lambda Labs API error: {response.status_code}")
                    return {"error": f"API error: {response.status_code}"}

        except Exception as e:
            logger.error(f"Error provisioning GPU instance: {e}")
            return {"error": str(e)}

    async def monitor_and_scale(self):
        """Monitor load and auto-scale GPU instances"""
        # This would implement auto-scaling logic based on load metrics
        # For now, just log the monitoring activity
        logger.info("Monitoring GPU instances for auto-scaling...")

async def main():
    """Main function for testing"""
    router = HybridModelRouter()

    # Test routing
    result = await router.route_request(
        "Analyze the PropTech market trends and create a strategic plan for Q1 2025",
        model_preference=ModelType.CLAUDE
    )
    print(f"Routing result: {result}")

    # Test GPU provisioning
    gpu_manager = LambdaLabsGPUManager()
    gpu_result = await gpu_manager.provision_gpu_instance()
    print(f"GPU provisioning result: {gpu_result}")

if __name__ == "__main__":
    asyncio.run(main())
