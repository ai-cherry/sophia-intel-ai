"""
Advanced Usage Aggregator with Time-Series Cost Tracking
Real-time cost monitoring and usage analytics for OpenRouter models
"""
import asyncio
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib

from app.core.redis_manager import redis_manager, RedisNamespaces
from app.core.ai_logger import logger


class TimeWindow(Enum):
    """Time window options for aggregation"""
    HOUR = "hour"
    DAY = "day" 
    WEEK = "week"
    MONTH = "month"


@dataclass
class UsageEvent:
    """Individual usage event"""
    timestamp: float
    model_id: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    request_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    endpoint: Optional[str] = None
    latency_ms: Optional[float] = None


@dataclass
class UsageMetrics:
    """Aggregated usage metrics"""
    total_requests: int
    total_tokens: int
    total_cost_usd: float
    average_tokens_per_request: float
    average_cost_per_request: float
    average_latency_ms: float
    unique_models: int
    unique_users: int
    top_models: List[Tuple[str, int]]  # (model_id, request_count)
    cost_by_model: Dict[str, float]
    cost_by_provider: Dict[str, float]
    hourly_distribution: Dict[str, float]  # hour -> cost


@dataclass
class CostAlert:
    """Cost monitoring alert"""
    id: str
    alert_type: str  # "threshold", "spike", "anomaly"
    severity: str    # "info", "warning", "critical"
    message: str
    current_value: float
    threshold: float
    timestamp: str
    model_id: Optional[str] = None
    provider: Optional[str] = None


class UsageAggregator:
    """Advanced usage tracking and cost aggregation"""
    
    # Redis key patterns
    USAGE_STREAM = "usage_events"
    HOURLY_METRICS = "usage:hourly"
    DAILY_METRICS = "usage:daily"
    MODEL_STATS = "usage:models"
    PROVIDER_STATS = "usage:providers"
    ALERTS_KEY = "usage:alerts"
    BUDGET_KEY = "usage:budgets"
    
    # Default cost thresholds (USD)
    DEFAULT_HOURLY_THRESHOLD = 5.0
    DEFAULT_DAILY_THRESHOLD = 50.0
    DEFAULT_MONTHLY_THRESHOLD = 1000.0
    
    def __init__(self):
        self._alert_handlers = []
        self._initialized = False
    
    async def initialize(self):
        """Initialize the usage aggregator"""
        if self._initialized:
            return
            
        try:
            # Create Redis streams and consumer groups
            await redis_manager.stream_create_group(
                self.USAGE_STREAM, 
                "aggregator_group", 
                mkstream=True
            )
            
            # Set up default budgets if not exist
            if not await redis_manager.exists(self.BUDGET_KEY):
                default_budgets = {
                    "hourly_limit": self.DEFAULT_HOURLY_THRESHOLD,
                    "daily_limit": self.DEFAULT_DAILY_THRESHOLD,
                    "monthly_limit": self.DEFAULT_MONTHLY_THRESHOLD
                }
                await redis_manager.set_with_ttl(
                    self.BUDGET_KEY,
                    json.dumps(default_budgets),
                    ttl=86400 * 30  # 30 days
                )
            
            self._initialized = True
            logger.info("Usage aggregator initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize usage aggregator: {e}")
            raise
    
    async def track_usage(self, usage_event: UsageEvent):
        """Track a single usage event"""
        await self.initialize()
        
        try:
            # Add to stream for real-time processing
            event_data = asdict(usage_event)
            await redis_manager.stream_add(
                self.USAGE_STREAM,
                event_data,
                maxlen=10000  # Keep last 10k events
            )
            
            # Update real-time metrics
            await self._update_realtime_metrics(usage_event)
            
            # Check for cost alerts
            await self._check_cost_alerts(usage_event)
            
            logger.debug(f"Tracked usage event: {usage_event.model_id}, ${usage_event.cost_usd:.4f}")
            
        except Exception as e:
            logger.error(f"Failed to track usage event: {e}")
            raise
    
    async def _update_realtime_metrics(self, event: UsageEvent):
        """Update real-time aggregated metrics"""
        now = datetime.fromtimestamp(event.timestamp, tz=timezone.utc)
        hour_key = now.strftime("%Y-%m-%d-%H")
        day_key = now.strftime("%Y-%m-%d")
        
        # Update hourly metrics
        await self._increment_metric(f"{self.HOURLY_METRICS}:{hour_key}", {
            "requests": 1,
            "tokens": event.total_tokens,
            "cost": event.cost_usd,
            "latency_sum": event.latency_ms or 0
        })
        
        # Update daily metrics
        await self._increment_metric(f"{self.DAILY_METRICS}:{day_key}", {
            "requests": 1,
            "tokens": event.total_tokens,
            "cost": event.cost_usd,
            "latency_sum": event.latency_ms or 0
        })
        
        # Update model-specific stats
        await self._increment_metric(f"{self.MODEL_STATS}:{event.model_id}", {
            "requests": 1,
            "tokens": event.total_tokens,
            "cost": event.cost_usd,
            "last_used": event.timestamp
        })
        
        # Update provider stats
        await self._increment_metric(f"{self.PROVIDER_STATS}:{event.provider}", {
            "requests": 1,
            "tokens": event.total_tokens,
            "cost": event.cost_usd
        })
    
    async def _increment_metric(self, key: str, values: Dict[str, float]):
        """Increment multiple metric values atomically"""
        async with redis_manager.pipeline() as pipe:
            for field, value in values.items():
                pipe.hincrby(key, field, int(value * 10000) if field == "cost" else int(value))
            pipe.expire(key, 86400 * 31)  # 31 days retention
            await pipe.execute()
    
    async def _check_cost_alerts(self, event: UsageEvent):
        """Check for cost threshold violations"""
        budgets = await self._get_budgets()
        now = datetime.fromtimestamp(event.timestamp, tz=timezone.utc)
        
        # Check hourly spend
        hourly_spend = await self.get_cost_for_period(TimeWindow.HOUR)
        if hourly_spend > budgets.get("hourly_limit", self.DEFAULT_HOURLY_THRESHOLD):
            await self._create_alert(
                "threshold",
                "warning",
                f"Hourly cost limit exceeded: ${hourly_spend:.2f}",
                hourly_spend,
                budgets["hourly_limit"]
            )
        
        # Check daily spend
        daily_spend = await self.get_cost_for_period(TimeWindow.DAY)
        if daily_spend > budgets.get("daily_limit", self.DEFAULT_DAILY_THRESHOLD):
            await self._create_alert(
                "threshold", 
                "critical",
                f"Daily cost limit exceeded: ${daily_spend:.2f}",
                daily_spend,
                budgets["daily_limit"]
            )
        
        # Check for cost spikes (>50% increase from average)
        recent_avg = await self._get_recent_average_cost()
        if event.cost_usd > recent_avg * 1.5:
            await self._create_alert(
                "spike",
                "warning", 
                f"Cost spike detected: ${event.cost_usd:.4f} vs avg ${recent_avg:.4f}",
                event.cost_usd,
                recent_avg,
                model_id=event.model_id
            )
    
    async def _create_alert(self, alert_type: str, severity: str, message: str, 
                          current_value: float, threshold: float, 
                          model_id: Optional[str] = None, provider: Optional[str] = None):
        """Create and store a cost alert"""
        alert = CostAlert(
            id=hashlib.md5(f"{alert_type}_{message}_{int(time.time())}".encode()).hexdigest()[:8],
            alert_type=alert_type,
            severity=severity,
            message=message,
            current_value=current_value,
            threshold=threshold,
            timestamp=datetime.utcnow().isoformat(),
            model_id=model_id,
            provider=provider
        )
        
        # Store alert with TTL
        await redis_manager.set_with_ttl(
            f"{self.ALERTS_KEY}:{alert.id}",
            json.dumps(asdict(alert)),
            ttl=86400 * 7  # 7 days
        )
        
        # Notify alert handlers
        for handler in self._alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")
        
        logger.warning(f"Cost alert [{severity}]: {message}")
    
    async def get_usage_metrics(self, window: TimeWindow, 
                              start_time: Optional[datetime] = None) -> UsageMetrics:
        """Get aggregated usage metrics for a time window"""
        if start_time is None:
            start_time = datetime.utcnow()
        
        # Determine time range
        if window == TimeWindow.HOUR:
            start_key = start_time.strftime("%Y-%m-%d-%H")
            keys = [f"{self.HOURLY_METRICS}:{start_key}"]
        elif window == TimeWindow.DAY:
            start_key = start_time.strftime("%Y-%m-%d")
            keys = [f"{self.DAILY_METRICS}:{start_key}"]
        elif window == TimeWindow.WEEK:
            keys = []
            for i in range(7):
                day = start_time - timedelta(days=i)
                day_key = day.strftime("%Y-%m-%d")
                keys.append(f"{self.DAILY_METRICS}:{day_key}")
        else:  # MONTH
            keys = []
            for i in range(30):
                day = start_time - timedelta(days=i)
                day_key = day.strftime("%Y-%m-%d")
                keys.append(f"{self.DAILY_METRICS}:{day_key}")
        
        # Aggregate metrics from Redis
        total_requests = 0
        total_tokens = 0
        total_cost = 0.0
        total_latency = 0.0
        
        for key in keys:
            metrics = await redis_manager.redis.hgetall(key)
            if metrics:
                total_requests += int(metrics.get(b'requests', 0))
                total_tokens += int(metrics.get(b'tokens', 0))
                total_cost += int(metrics.get(b'cost', 0)) / 10000  # Convert back from storage format
                total_latency += int(metrics.get(b'latency_sum', 0))
        
        # Calculate averages
        avg_tokens = total_tokens / total_requests if total_requests > 0 else 0
        avg_cost = total_cost / total_requests if total_requests > 0 else 0
        avg_latency = total_latency / total_requests if total_requests > 0 else 0
        
        # Get model and provider stats
        model_stats = await self._get_top_models(limit=10)
        cost_by_model = await self._get_cost_by_model()
        cost_by_provider = await self._get_cost_by_provider()
        hourly_dist = await self._get_hourly_distribution()
        
        return UsageMetrics(
            total_requests=total_requests,
            total_tokens=total_tokens,
            total_cost_usd=total_cost,
            average_tokens_per_request=avg_tokens,
            average_cost_per_request=avg_cost,
            average_latency_ms=avg_latency,
            unique_models=len(model_stats),
            unique_users=0,  # TODO: Calculate from events
            top_models=model_stats,
            cost_by_model=cost_by_model,
            cost_by_provider=cost_by_provider,
            hourly_distribution=hourly_dist
        )
    
    async def get_cost_for_period(self, window: TimeWindow) -> float:
        """Get total cost for a specific time period"""
        metrics = await self.get_usage_metrics(window)
        return metrics.total_cost_usd
    
    async def _get_top_models(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get top models by request count"""
        model_keys = await redis_manager.redis.keys(f"{self.MODEL_STATS}:*")
        model_stats = []
        
        for key in model_keys[:limit]:
            model_id = key.decode().split(':')[-1]
            stats = await redis_manager.redis.hgetall(key)
            if stats:
                requests = int(stats.get(b'requests', 0))
                model_stats.append((model_id, requests))
        
        return sorted(model_stats, key=lambda x: x[1], reverse=True)[:limit]
    
    async def _get_cost_by_model(self) -> Dict[str, float]:
        """Get cost breakdown by model"""
        model_keys = await redis_manager.redis.keys(f"{self.MODEL_STATS}:*")
        cost_by_model = {}
        
        for key in model_keys:
            model_id = key.decode().split(':')[-1]
            stats = await redis_manager.redis.hgetall(key)
            if stats:
                cost = int(stats.get(b'cost', 0)) / 10000
                if cost > 0:
                    cost_by_model[model_id] = cost
        
        return cost_by_model
    
    async def _get_cost_by_provider(self) -> Dict[str, float]:
        """Get cost breakdown by provider"""
        provider_keys = await redis_manager.redis.keys(f"{self.PROVIDER_STATS}:*")
        cost_by_provider = {}
        
        for key in provider_keys:
            provider = key.decode().split(':')[-1]
            stats = await redis_manager.redis.hgetall(key)
            if stats:
                cost = int(stats.get(b'cost', 0)) / 10000
                if cost > 0:
                    cost_by_provider[provider] = cost
        
        return cost_by_provider
    
    async def _get_hourly_distribution(self) -> Dict[str, float]:
        """Get cost distribution by hour of day"""
        hourly_dist = {}
        now = datetime.utcnow()
        
        # Look at last 24 hours
        for i in range(24):
            hour_time = now - timedelta(hours=i)
            hour_key = hour_time.strftime("%Y-%m-%d-%H")
            stats = await redis_manager.redis.hgetall(f"{self.HOURLY_METRICS}:{hour_key}")
            hour_label = hour_time.strftime("%H:00")
            
            if stats:
                cost = int(stats.get(b'cost', 0)) / 10000
                hourly_dist[hour_label] = cost
            else:
                hourly_dist[hour_label] = 0.0
        
        return hourly_dist
    
    async def _get_budgets(self) -> Dict[str, float]:
        """Get current budget settings"""
        try:
            budgets_json = await redis_manager.get(self.BUDGET_KEY)
            if budgets_json:
                return json.loads(budgets_json)
        except Exception as e:
            logger.error(f"Failed to get budgets: {e}")
        
        # Return defaults
        return {
            "hourly_limit": self.DEFAULT_HOURLY_THRESHOLD,
            "daily_limit": self.DEFAULT_DAILY_THRESHOLD,
            "monthly_limit": self.DEFAULT_MONTHLY_THRESHOLD
        }
    
    async def _get_recent_average_cost(self) -> float:
        """Get average cost per request from recent events"""
        try:
            # Get last 100 events from stream
            events = await redis_manager.stream_read(
                {self.USAGE_STREAM: "0-0"},
                count=100
            )
            
            if not events:
                return 0.0
            
            total_cost = 0.0
            count = 0
            
            for stream_name, messages in events:
                for message_id, fields in messages:
                    cost = float(fields.get(b'cost_usd', 0))
                    total_cost += cost
                    count += 1
            
            return total_cost / count if count > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Failed to get recent average cost: {e}")
            return 0.0
    
    async def set_budgets(self, hourly: float = None, daily: float = None, 
                         monthly: float = None):
        """Update budget thresholds"""
        current_budgets = await self._get_budgets()
        
        if hourly is not None:
            current_budgets["hourly_limit"] = hourly
        if daily is not None:
            current_budgets["daily_limit"] = daily
        if monthly is not None:
            current_budgets["monthly_limit"] = monthly
        
        await redis_manager.set_with_ttl(
            self.BUDGET_KEY,
            json.dumps(current_budgets),
            ttl=86400 * 30  # 30 days
        )
        
        logger.info(f"Updated budgets: {current_budgets}")
    
    async def get_alerts(self, severity: Optional[str] = None, 
                        limit: int = 50) -> List[CostAlert]:
        """Get recent cost alerts"""
        alert_keys = await redis_manager.redis.keys(f"{self.ALERTS_KEY}:*")
        alerts = []
        
        for key in alert_keys[:limit]:
            alert_json = await redis_manager.redis.get(key)
            if alert_json:
                alert_data = json.loads(alert_json)
                alert = CostAlert(**alert_data)
                
                if severity is None or alert.severity == severity:
                    alerts.append(alert)
        
        # Sort by timestamp (newest first)
        alerts.sort(key=lambda x: x.timestamp, reverse=True)
        return alerts[:limit]
    
    def add_alert_handler(self, handler):
        """Add a custom alert handler function"""
        self._alert_handlers.append(handler)
    
    async def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old usage data"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Clean up daily metrics
        for i in range(days_to_keep, days_to_keep + 30):  # Clean extra 30 days
            old_date = cutoff_date - timedelta(days=i)
            old_key = f"{self.DAILY_METRICS}:{old_date.strftime('%Y-%m-%d')}"
            await redis_manager.delete(old_key)
        
        # Clean up hourly metrics (keep last 7 days)
        for i in range(7 * 24, 14 * 24):  # Clean 7-14 days ago
            old_time = cutoff_date - timedelta(hours=i)
            old_key = f"{self.HOURLY_METRICS}:{old_time.strftime('%Y-%m-%d-%H')}"
            await redis_manager.delete(old_key)
        
        logger.info(f"Cleaned up usage data older than {days_to_keep} days")


# Global instance
_usage_aggregator = None

async def get_usage_aggregator() -> UsageAggregator:
    """Get global usage aggregator instance"""
    global _usage_aggregator
    if not _usage_aggregator:
        _usage_aggregator = UsageAggregator()
        await _usage_aggregator.initialize()
    return _usage_aggregator