"""
Real-time Cost Monitoring and API Usage Tracking System
Prevents unexpected bills by tracking all LLM API calls in real-time
"""

import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import redis.asyncio as redis

from app.core.ai_logger import logger
from app.core.circuit_breaker import with_circuit_breaker

logger = logging.getLogger(__name__)

@dataclass
class CostRequest:
    """Represents a single LLM API request for cost tracking."""
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    user_id: str
    swarm_id: str
    request_id: str = field(default_factory=lambda: f"req_{int(time.time()*1000)}")
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class CostMetrics:
    """Cost metrics for a single request."""
    cost: float
    hourly_spend: float
    daily_spend: float
    monthly_spend: float
    request_count: int

class AlertSystem:
    """Handles cost alerts and notifications."""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.alert_thresholds = {
            'hourly': 500.0,    # $500/hour
            'daily': 5000.0,    # $5000/day
            'monthly': 50000.0  # $50000/month
        }

    async def send_alert(self, alert_type: str, data: dict[str, Any]) -> None:
        """Send cost alert via multiple channels."""
        alert_message = {
            'type': alert_type,
            'timestamp': datetime.now().isoformat(),
            'data': data,
            'severity': self._calculate_severity(data.get('amount', 0))
        }

        # Store alert in Redis for dashboard
        await self.redis.lpush('cost_alerts', json.dumps(alert_message))
        await self.redis.ltrim('cost_alerts', 0, 99)  # Keep last 100 alerts

        # Log alert
        logger.warning(f"COST ALERT: {alert_type} - ${data.get('amount', 0):.2f}")

        # TODO: Add Slack/Email notifications
        # await self._send_slack_alert(alert_message)
        # await self._send_email_alert(alert_message)

    def _calculate_severity(self, amount: float) -> str:
        """Calculate alert severity based on amount."""
        if amount >= 1000:
            return 'critical'
        elif amount >= 500:
            return 'high'
        elif amount >= 100:
            return 'medium'
        else:
            return 'low'

class RealTimeCostMonitor:
    """
    Real-time cost monitoring system with Redis-based tracking and alerts.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis: redis.Redis | None = None
        self.alert_system: AlertSystem | None = None
        self.initialized = False

        # Cost rates per token (as of 2025)
        self.cost_rates = {
            'openai': {
                'gpt-4o': {'input': 0.00003, 'output': 0.00006},
                'gpt-4o-mini': {'input': 0.0000015, 'output': 0.000006},
                'gpt-5': {'input': 0.00005, 'output': 0.00010}
            },
            'anthropic': {
                'claude-3-5-sonnet': {'input': 0.00003, 'output': 0.00015},
                'claude-3-haiku': {'input': 0.0000008, 'output': 0.000004},
                'claude-4': {'input': 0.00004, 'output': 0.00020}
            },
            'together': {
                'llama-3.2-90b': {'input': 0.0000009, 'output': 0.0000009},
                'mixtral-8x7b': {'input': 0.0000006, 'output': 0.0000006}
            },
            'groq': {
                'llama-3.2-90b': {'input': 0.00000005, 'output': 0.0000001},
                'mixtral-8x7b': {'input': 0.00000004, 'output': 0.00000008}
            }
        }

    async def initialize(self) -> None:
        """Initialize Redis connection and alert system."""
        if self.initialized:
            return

        try:
            self.redis = redis.Redis.from_url(self.redis_url, decode_responses=True)
            self.alert_system = AlertSystem(self.redis)

            # Test connection
            await self.redis.ping()
            self.initialized = True
            logger.info("✅ Cost monitor initialized successfully")

        except Exception as e:
            logger.error(f"❌ Failed to initialize cost monitor: {e}")
            raise

    async def track_request(self, request: CostRequest) -> CostMetrics:
        """
        Track a single LLM API request and return cost metrics.

        Args:
            request: CostRequest object with request details

        Returns:
            CostMetrics with current spending data
        """
        if not self.initialized:
            await self.initialize()

        start_time = time.time()

        # Calculate cost for this request
        cost = self._calculate_cost(request)

        # Store request data in Redis
        await self._store_request_data(request, cost)

        # Get current spending metrics
        metrics = await self._get_current_metrics()

        # Check for alerts
        await self._check_alerts(metrics)

        latency = time.time() - start_time
        logger.debug(f"Cost tracking completed in {latency:.4f}s")
        return CostMetrics(
            cost=cost,
            hourly_spend=metrics['hourly'],
            daily_spend=metrics['daily'],
            monthly_spend=metrics['monthly'],
            request_count=metrics['request_count']
        )

    def _calculate_cost(self, request: CostRequest) -> float:
        """Calculate cost for a single request."""
        try:
            rates = self.cost_rates[request.provider][request.model]
            input_cost = request.input_tokens * rates['input']
            output_cost = request.output_tokens * rates['output']
            return input_cost + output_cost
        except KeyError:
            # Fallback for unknown models
            logger.warning(f"Unknown model {request.provider}/{request.model}, using fallback rate")
            return (request.input_tokens + request.output_tokens) * 0.00001

    async def _store_request_data(self, request: CostRequest, cost: float) -> None:
        """Store request data in Redis with multiple time granularities."""
        timestamp = int(request.timestamp.timestamp())

        # Store individual request
        request_data = {
            'request_id': request.request_id,
            'provider': request.provider,
            'model': request.model,
            'input_tokens': request.input_tokens,
            'output_tokens': request.output_tokens,
            'cost': cost,
            'user_id': request.user_id,
            'swarm_id': request.swarm_id,
            'timestamp': timestamp
        }

        # Add to sorted sets for time-based queries
        await self.redis.zadd('costs:all', {json.dumps(request_data): timestamp})
        await self.redis.zadd(f'costs:user:{request.user_id}', {json.dumps(request_data): timestamp})
        await self.redis.zadd(f'costs:swarm:{request.swarm_id}', {json.dumps(request_data): timestamp})
        await self.redis.zadd(f'costs:provider:{request.provider}', {json.dumps(request_data): timestamp})

        # Update rolling counters
        await self._update_rolling_counters(cost, timestamp)

    async def _update_rolling_counters(self, cost: float, timestamp: int) -> None:
        """Update rolling cost counters for different time windows."""
        # Hourly counter (expires after 24 hours)
        hour_key = f"costs:hourly:{timestamp // 3600}"
        await self.redis.incrbyfloat(hour_key, cost)
        await self.redis.expire(hour_key, 86400)  # 24 hours

        # Daily counter (expires after 30 days)
        day_key = f"costs:daily:{timestamp // 86400}"
        await self.redis.incrbyfloat(day_key, cost)
        await self.redis.expire(day_key, 2592000)  # 30 days

        # Monthly counter (expires after 365 days)
        month_key = f"costs:monthly:{timestamp // (86400 * 30)}"
        await self.redis.incrbyfloat(month_key, cost)
        await self.redis.expire(month_key, 31536000)  # 365 days

        # Request counter
        await self.redis.incr('request_count')

    @with_circuit_breaker("redis")
    async def _get_current_metrics(self) -> dict[str, float]:
        """Get current spending metrics."""
        int(time.time())

        # Get hourly spend (last hour)
        hourly_keys = await self.redis.keys('costs:hourly:*')
        hourly_spend = 0.0
        for key in hourly_keys:
            try:
                hourly_spend += float(await self.redis.get(key) or 0)
            except:
                pass

        # Get daily spend (last 24 hours)
        daily_keys = await self.redis.keys('costs:daily:*')
        daily_spend = 0.0
        for key in daily_keys:
            try:
                daily_spend += float(await self.redis.get(key) or 0)
            except:
                pass

        # Get monthly spend (last 30 days)
        monthly_keys = await self.redis.keys('costs:monthly:*')
        monthly_spend = 0.0
        for key in monthly_keys:
            try:
                monthly_spend += float(await self.redis.get(key) or 0)
            except:
                pass

        # Get request count
        request_count = int(await self.redis.get('request_count') or 0)

        return {
            'hourly': hourly_spend,
            'daily': daily_spend,
            'monthly': monthly_spend,
            'request_count': request_count
        }

    async def _check_alerts(self, metrics: dict[str, float]) -> None:
        """Check if any alert thresholds have been exceeded."""
        if not self.alert_system:
            return

        # Hourly alert
        if metrics['hourly'] >= 500:
            await self.alert_system.send_alert('HOURLY_COST_ALERT', {
                'amount': metrics['hourly'],
                'threshold': 500,
                'period': 'hourly'
            })

        # Daily alert
        if metrics['daily'] >= 5000:
            await self.alert_system.send_alert('DAILY_COST_ALERT', {
                'amount': metrics['daily'],
                'threshold': 5000,
                'period': 'daily'
            })

        # Monthly alert
        if metrics['monthly'] >= 50000:
            await self.alert_system.send_alert('MONTHLY_COST_ALERT', {
                'amount': metrics['monthly'],
                'threshold': 50000,
                'period': 'monthly'
            })

    async def get_cost_report(self, time_window: str = 'daily') -> dict[str, Any]:
        """Get detailed cost report for specified time window."""
        if not self.initialized:
            await self.initialize()

        metrics = await self._get_current_metrics()

        # Get top spenders
        top_users = await self._get_top_spenders('user', time_window)
        top_swarms = await self._get_top_spenders('swarm', time_window)
        top_providers = await self._get_top_spenders('provider', time_window)

        # Get recent alerts
        recent_alerts = await self.redis.lrange('cost_alerts', 0, 9)
        alerts = [json.loads(alert) for alert in recent_alerts]

        return {
            'current_metrics': metrics,
            'top_users': top_users,
            'top_swarms': top_swarms,
            'top_providers': top_providers,
            'recent_alerts': alerts,
            'time_window': time_window
        }

    async def _get_top_spenders(self, entity_type: str, time_window: str) -> list[dict[str, Any]]:
        """Get top spenders for given entity type and time window."""
        # This is a simplified implementation
        # In production, you'd want more sophisticated aggregation
        keys = await self.redis.keys(f'costs:{entity_type}:*')

        spenders = []
        for key in keys:
            try:
                # Get all requests for this entity
                requests = await self.redis.zrange(key, 0, -1, withscores=True)
                total_cost = 0.0

                for request_json, _ in requests:
                    request_data = json.loads(request_json)
                    total_cost += request_data.get('cost', 0)

                entity_id = key.split(':')[-1]
                spenders.append({
                    'id': entity_id,
                    'total_cost': total_cost,
                    'request_count': len(requests)
                })
            except Exception as e:
                logger.warning(f"Error processing {key}: {e}")

        # Sort by total cost and return top 10
        spenders.sort(key=lambda x: x['total_cost'], reverse=True)
        return spenders[:10]

    @with_circuit_breaker("redis")
    async def cleanup_old_data(self, days_to_keep: int = 90) -> None:
        """Clean up old cost data to prevent Redis bloat."""
        cutoff_timestamp = int((datetime.now() - timedelta(days=days_to_keep)).timestamp())

        # Remove old entries from sorted sets
        await self.redis.zremrangebyscore('costs:all', 0, cutoff_timestamp)

        # Remove old hourly/daily keys
        old_hourly_keys = await self.redis.keys('costs:hourly:*')
        old_daily_keys = await self.redis.keys('costs:daily:*')

        for key in old_hourly_keys + old_daily_keys:
            try:
                key_timestamp = int(key.split(':')[-1])
                if key_timestamp < (cutoff_timestamp // 3600):
                    await self.redis.delete(key)
            except:
                pass

        logger.info(f"Cleaned up cost data older than {days_to_keep} days")

# Global singleton instance
_cost_monitor: RealTimeCostMonitor | None = None

async def get_cost_monitor() -> RealTimeCostMonitor:
    """Get the global cost monitor instance."""
    global _cost_monitor
    if _cost_monitor is None:
        _cost_monitor = RealTimeCostMonitor()
        await _cost_monitor.initialize()
    return _cost_monitor

@asynccontextmanager
async def cost_tracking(request: CostRequest):
    """Context manager for automatic cost tracking."""
    monitor = await get_cost_monitor()
    try:
        yield await monitor.track_request(request)
    except Exception as e:
        logger.error(f"Cost tracking failed: {e}")
        # Don't raise exception to avoid breaking the main flow
        yield CostMetrics(cost=0, hourly_spend=0, daily_spend=0, monthly_spend=0, request_count=0)

# Example usage
async def example_usage():
    """Example of how to use the cost monitor."""
    monitor = await get_cost_monitor()

    # Track a sample request
    request = CostRequest(
        provider='openai',
        model='gpt-4o',
        input_tokens=1000,
        output_tokens=500,
        user_id='user_123',
        swarm_id='swarm_alpha'
    )

    metrics = await monitor.track_request(request)
    logger.info(f"Request cost: ${metrics.cost:.4f}")
    logger.info(f"Hourly spend: ${metrics.hourly_spend:.2f}")
    logger.info(f"Daily spend: ${metrics.daily_spend:.2f}")

    # Get cost report
    report = await monitor.get_cost_report('daily')
    logger.info(f"Total daily spend: ${report['current_metrics']['daily']:.2f}")

if __name__ == "__main__":
    asyncio.run(example_usage())
