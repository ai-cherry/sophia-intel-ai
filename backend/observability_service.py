"""
Comprehensive Observability Service for SOPHIA Intel
Advanced tracking, metrics, monitoring, and alerting system
with Sentry integration, Prometheus metrics, and custom analytics
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from collections import defaultdict, deque

import httpx
from loguru import logger
from pydantic import BaseModel

from config.config import settings


class RequestMetrics(BaseModel):
    """Request metrics model"""
    request_id: str
    session_id: Optional[str]
    endpoint: str
    method: str
    backend_used: Optional[str]
    start_time: float
    end_time: Optional[float]
    duration: Optional[float]
    status_code: Optional[int]
    error: Optional[str]
    user_agent: Optional[str]
    ip_address: Optional[str]
    request_size: Optional[int]
    response_size: Optional[int]
    metadata: Dict[str, Any] = {}


class ChatMetrics(BaseModel):
    """Chat-specific metrics"""
    session_id: str
    message_count: int
    backend_usage: Dict[str, int]
    research_queries: int
    error_count: int
    avg_response_time: float
    total_tokens_estimated: int
    features_used: List[str]
    conversation_duration: float
    last_activity: datetime


class SystemMetrics(BaseModel):
    """System-wide metrics"""
    timestamp: datetime
    active_sessions: int
    total_requests: int
    avg_response_time: float
    error_rate: float
    backend_distribution: Dict[str, int]
    memory_usage: Dict[str, Any]
    cache_hit_rate: float
    research_requests: int
    lambda_server_status: Dict[str, str]


class ObservabilityService:
    """
    Comprehensive observability service providing:
    - Request/response tracking with detailed metrics
    - Performance monitoring and alerting
    - User interaction analytics
    - System health monitoring
    - Sentry integration for error tracking
    - Prometheus metrics export
    - Custom dashboard data
    """
    
    def __init__(self):
        # Configuration
        self.sentry_dsn = getattr(settings, "SENTRY_DSN", "")
        self.sentry_pat = getattr(settings, "SENTRY_PAT", "")
        self.prometheus_enabled = getattr(settings, "PROMETHEUS_ENABLED", False)
        
        # Metrics storage (in-memory for now, would use Redis/DB in production)
        self.request_metrics = deque(maxlen=10000)  # Last 10k requests
        self.chat_sessions = {}  # Active chat sessions
        self.system_metrics_history = deque(maxlen=1440)  # 24 hours of minute-by-minute data
        
        # Performance tracking
        self.response_times = deque(maxlen=1000)  # Last 1000 response times
        self.error_counts = defaultdict(int)
        self.backend_usage = defaultdict(int)
        
        # Alerting thresholds
        self.alert_thresholds = {
            "response_time_p95": 5.0,  # 5 seconds
            "error_rate": 0.05,  # 5%
            "memory_usage": 0.85,  # 85%
            "lambda_server_down": True
        }
        
        # Sentry client (would initialize properly in production)
        self.sentry_initialized = False
        
        # Background tasks
        self.metrics_collection_task = None
        self.start_background_tasks()
    
    def start_background_tasks(self):
        """Start background metrics collection tasks"""
        if not self.metrics_collection_task:
            self.metrics_collection_task = asyncio.create_task(self._metrics_collection_loop())
    
    async def track_request_start(
        self,
        request_id: str,
        endpoint: str,
        method: str,
        session_id: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        request_size: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> RequestMetrics:
        """Track the start of a request"""
        try:
            metrics = RequestMetrics(
                request_id=request_id,
                session_id=session_id,
                endpoint=endpoint,
                method=method,
                backend_used=None,
                start_time=time.time(),
                end_time=None,
                duration=None,
                status_code=None,
                error=None,
                user_agent=user_agent,
                ip_address=ip_address,
                request_size=request_size,
                response_size=None,
                metadata=metadata or {}
            )
            
            # Store metrics
            self.request_metrics.append(metrics)
            
            logger.debug(f"Request tracking started: {request_id} - {endpoint}")
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to track request start: {e}")
            # Return minimal metrics on error
            return RequestMetrics(
                request_id=request_id,
                session_id=session_id,
                endpoint=endpoint,
                method=method,
                backend_used=None,
                start_time=time.time()
            )
    
    async def track_request_end(
        self,
        request_id: str,
        status_code: int,
        backend_used: Optional[str] = None,
        response_size: Optional[int] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Track the end of a request"""
        try:
            # Find the request metrics
            request_metrics = None
            for metrics in reversed(self.request_metrics):
                if metrics.request_id == request_id:
                    request_metrics = metrics
                    break
            
            if not request_metrics:
                logger.warning(f"Request metrics not found for ID: {request_id}")
                return
            
            # Update metrics
            end_time = time.time()
            duration = end_time - request_metrics.start_time
            
            request_metrics.end_time = end_time
            request_metrics.duration = duration
            request_metrics.status_code = status_code
            request_metrics.backend_used = backend_used
            request_metrics.response_size = response_size
            request_metrics.error = error
            
            if metadata:
                request_metrics.metadata.update(metadata)
            
            # Update performance tracking
            self.response_times.append(duration)
            if backend_used:
                self.backend_usage[backend_used] += 1
            
            # Track errors
            if status_code >= 400 or error:
                self.error_counts[f"{status_code}_{error or 'unknown'}"] += 1
                
                # Send to Sentry if configured
                if self.sentry_dsn and error:
                    await self._send_to_sentry(request_metrics, error)
            
            logger.debug(f"Request tracking completed: {request_id} - {duration:.3f}s - {status_code}")
            
        except Exception as e:
            logger.error(f"Failed to track request end: {e}")
    
    async def track_chat_session(
        self,
        session_id: str,
        message_count: int,
        backend_used: str,
        response_time: float,
        tokens_estimated: int = 0,
        features_used: Optional[List[str]] = None,
        error_occurred: bool = False,
        research_query: bool = False
    ):
        """Track chat session metrics"""
        try:
            current_time = datetime.now()
            
            if session_id not in self.chat_sessions:
                self.chat_sessions[session_id] = ChatMetrics(
                    session_id=session_id,
                    message_count=0,
                    backend_usage={},
                    research_queries=0,
                    error_count=0,
                    avg_response_time=0.0,
                    total_tokens_estimated=0,
                    features_used=[],
                    conversation_duration=0.0,
                    last_activity=current_time
                )
            
            session_metrics = self.chat_sessions[session_id]
            
            # Update metrics
            session_metrics.message_count = message_count
            session_metrics.backend_usage[backend_used] = session_metrics.backend_usage.get(backend_used, 0) + 1
            
            if research_query:
                session_metrics.research_queries += 1
            
            if error_occurred:
                session_metrics.error_count += 1
            
            # Update average response time
            total_responses = sum(session_metrics.backend_usage.values())
            if total_responses > 0:
                current_avg = session_metrics.avg_response_time
                session_metrics.avg_response_time = (
                    (current_avg * (total_responses - 1) + response_time) / total_responses
                )
            
            session_metrics.total_tokens_estimated += tokens_estimated
            
            if features_used:
                for feature in features_used:
                    if feature not in session_metrics.features_used:
                        session_metrics.features_used.append(feature)
            
            # Update conversation duration
            if hasattr(session_metrics, 'first_activity'):
                session_metrics.conversation_duration = (
                    current_time - session_metrics.first_activity
                ).total_seconds()
            else:
                session_metrics.first_activity = current_time
                session_metrics.conversation_duration = 0.0
            
            session_metrics.last_activity = current_time
            
            logger.debug(f"Chat session tracked: {session_id} - {message_count} messages")
            
        except Exception as e:
            logger.error(f"Failed to track chat session: {e}")
    
    async def get_system_metrics(self) -> SystemMetrics:
        """Get current system metrics"""
        try:
            current_time = datetime.now()
            
            # Calculate metrics from recent data
            recent_requests = [
                req for req in self.request_metrics
                if req.end_time and (time.time() - req.end_time) < 3600  # Last hour
            ]
            
            # Response time metrics
            recent_response_times = [req.duration for req in recent_requests if req.duration]
            avg_response_time = sum(recent_response_times) / len(recent_response_times) if recent_response_times else 0.0
            
            # Error rate
            error_requests = [req for req in recent_requests if req.status_code and req.status_code >= 400]
            error_rate = len(error_requests) / len(recent_requests) if recent_requests else 0.0
            
            # Backend distribution
            backend_dist = defaultdict(int)
            for req in recent_requests:
                if req.backend_used:
                    backend_dist[req.backend_used] += 1
            
            # Cache hit rate (placeholder - would calculate from actual cache metrics)
            cache_hit_rate = 0.75  # Placeholder
            
            # Lambda server status (would check actual servers)
            lambda_status = {
                "primary": "healthy",
                "secondary": "healthy"
            }
            
            # Memory usage (placeholder - would get from system)
            memory_usage = {
                "used_mb": 512,
                "total_mb": 2048,
                "percentage": 0.25
            }
            
            metrics = SystemMetrics(
                timestamp=current_time,
                active_sessions=len(self.chat_sessions),
                total_requests=len(recent_requests),
                avg_response_time=avg_response_time,
                error_rate=error_rate,
                backend_distribution=dict(backend_dist),
                memory_usage=memory_usage,
                cache_hit_rate=cache_hit_rate,
                research_requests=sum(1 for session in self.chat_sessions.values() if session.research_queries > 0),
                lambda_server_status=lambda_status
            )
            
            # Store in history
            self.system_metrics_history.append(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return SystemMetrics(
                timestamp=datetime.now(),
                active_sessions=0,
                total_requests=0,
                avg_response_time=0.0,
                error_rate=0.0,
                backend_distribution={},
                memory_usage={},
                cache_hit_rate=0.0,
                research_requests=0,
                lambda_server_status={}
            )
    
    async def get_analytics_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive analytics data for dashboard"""
        try:
            system_metrics = await self.get_system_metrics()
            
            # Request analytics
            recent_requests = [
                req for req in self.request_metrics
                if req.end_time and (time.time() - req.end_time) < 86400  # Last 24 hours
            ]
            
            # Response time percentiles
            response_times = [req.duration for req in recent_requests if req.duration]
            response_times.sort()
            
            percentiles = {}
            if response_times:
                percentiles = {
                    "p50": response_times[int(len(response_times) * 0.5)],
                    "p90": response_times[int(len(response_times) * 0.9)],
                    "p95": response_times[int(len(response_times) * 0.95)],
                    "p99": response_times[int(len(response_times) * 0.99)]
                }
            
            # Endpoint analytics
            endpoint_stats = defaultdict(lambda: {"count": 0, "avg_time": 0.0, "errors": 0})
            for req in recent_requests:
                endpoint = req.endpoint
                endpoint_stats[endpoint]["count"] += 1
                if req.duration:
                    current_avg = endpoint_stats[endpoint]["avg_time"]
                    count = endpoint_stats[endpoint]["count"]
                    endpoint_stats[endpoint]["avg_time"] = (
                        (current_avg * (count - 1) + req.duration) / count
                    )
                if req.status_code and req.status_code >= 400:
                    endpoint_stats[endpoint]["errors"] += 1
            
            # Chat session analytics
            session_analytics = {
                "total_sessions": len(self.chat_sessions),
                "avg_messages_per_session": sum(s.message_count for s in self.chat_sessions.values()) / len(self.chat_sessions) if self.chat_sessions else 0,
                "avg_conversation_duration": sum(s.conversation_duration for s in self.chat_sessions.values()) / len(self.chat_sessions) if self.chat_sessions else 0,
                "total_research_queries": sum(s.research_queries for s in self.chat_sessions.values()),
                "backend_preference": dict(system_metrics.backend_distribution)
            }
            
            # Feature usage analytics
            all_features = []
            for session in self.chat_sessions.values():
                all_features.extend(session.features_used)
            
            feature_usage = defaultdict(int)
            for feature in all_features:
                feature_usage[feature] += 1
            
            # Time series data (last 24 hours)
            time_series = []
            for metrics in list(self.system_metrics_history)[-1440:]:  # Last 24 hours
                time_series.append({
                    "timestamp": metrics.timestamp.isoformat(),
                    "requests": metrics.total_requests,
                    "response_time": metrics.avg_response_time,
                    "error_rate": metrics.error_rate,
                    "active_sessions": metrics.active_sessions
                })
            
            return {
                "system_metrics": system_metrics.dict(),
                "request_analytics": {
                    "total_requests_24h": len(recent_requests),
                    "response_time_percentiles": percentiles,
                    "endpoint_stats": dict(endpoint_stats),
                    "error_breakdown": dict(self.error_counts)
                },
                "session_analytics": session_analytics,
                "feature_usage": dict(feature_usage),
                "time_series": time_series,
                "alerts": await self._check_alerts(),
                "health_status": await self._get_health_status()
            }
            
        except Exception as e:
            logger.error(f"Failed to get analytics dashboard data: {e}")
            return {"error": str(e)}
    
    async def _check_alerts(self) -> List[Dict[str, Any]]:
        """Check for system alerts"""
        alerts = []
        
        try:
            system_metrics = await self.get_system_metrics()
            
            # Response time alert
            if system_metrics.avg_response_time > self.alert_thresholds["response_time_p95"]:
                alerts.append({
                    "type": "performance",
                    "severity": "warning",
                    "message": f"High response time: {system_metrics.avg_response_time:.2f}s",
                    "threshold": self.alert_thresholds["response_time_p95"],
                    "current_value": system_metrics.avg_response_time
                })
            
            # Error rate alert
            if system_metrics.error_rate > self.alert_thresholds["error_rate"]:
                alerts.append({
                    "type": "error_rate",
                    "severity": "critical",
                    "message": f"High error rate: {system_metrics.error_rate:.1%}",
                    "threshold": self.alert_thresholds["error_rate"],
                    "current_value": system_metrics.error_rate
                })
            
            # Memory usage alert
            memory_pct = system_metrics.memory_usage.get("percentage", 0)
            if memory_pct > self.alert_thresholds["memory_usage"]:
                alerts.append({
                    "type": "memory",
                    "severity": "warning",
                    "message": f"High memory usage: {memory_pct:.1%}",
                    "threshold": self.alert_thresholds["memory_usage"],
                    "current_value": memory_pct
                })
            
            # Lambda server alerts
            for server, status in system_metrics.lambda_server_status.items():
                if status != "healthy":
                    alerts.append({
                        "type": "lambda_server",
                        "severity": "critical",
                        "message": f"Lambda server {server} is {status}",
                        "server": server,
                        "status": status
                    })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to check alerts: {e}")
            return [{"type": "system", "severity": "error", "message": f"Alert check failed: {str(e)}"}]
    
    async def _get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status"""
        try:
            alerts = await self._check_alerts()
            
            # Determine overall health
            critical_alerts = [a for a in alerts if a.get("severity") == "critical"]
            warning_alerts = [a for a in alerts if a.get("severity") == "warning"]
            
            if critical_alerts:
                status = "critical"
            elif warning_alerts:
                status = "warning"
            else:
                status = "healthy"
            
            return {
                "status": status,
                "critical_alerts": len(critical_alerts),
                "warning_alerts": len(warning_alerts),
                "total_alerts": len(alerts),
                "last_check": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get health status: {e}")
            return {
                "status": "unknown",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
    
    async def _send_to_sentry(self, request_metrics: RequestMetrics, error: str):
        """Send error to Sentry"""
        try:
            if not self.sentry_dsn:
                return
            
            # This would integrate with Sentry SDK in production
            logger.info(f"Would send to Sentry: {error} for request {request_metrics.request_id}")
            
        except Exception as e:
            logger.error(f"Failed to send to Sentry: {e}")
    
    async def _metrics_collection_loop(self):
        """Background task for metrics collection"""
        while True:
            try:
                await asyncio.sleep(60)  # Collect metrics every minute
                
                # Collect system metrics
                await self.get_system_metrics()
                
                # Clean up old sessions (inactive for > 1 hour)
                current_time = datetime.now()
                inactive_sessions = []
                
                for session_id, session_metrics in self.chat_sessions.items():
                    if (current_time - session_metrics.last_activity).total_seconds() > 3600:
                        inactive_sessions.append(session_id)
                
                for session_id in inactive_sessions:
                    del self.chat_sessions[session_id]
                
                if inactive_sessions:
                    logger.info(f"Cleaned up {len(inactive_sessions)} inactive sessions")
                
            except Exception as e:
                logger.error(f"Metrics collection loop error: {e}")
    
    async def export_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format"""
        try:
            system_metrics = await self.get_system_metrics()
            
            metrics_lines = []
            
            # System metrics
            metrics_lines.append(f"sophia_active_sessions {system_metrics.active_sessions}")
            metrics_lines.append(f"sophia_total_requests {system_metrics.total_requests}")
            metrics_lines.append(f"sophia_avg_response_time {system_metrics.avg_response_time}")
            metrics_lines.append(f"sophia_error_rate {system_metrics.error_rate}")
            metrics_lines.append(f"sophia_cache_hit_rate {system_metrics.cache_hit_rate}")
            metrics_lines.append(f"sophia_research_requests {system_metrics.research_requests}")
            
            # Backend distribution
            for backend, count in system_metrics.backend_distribution.items():
                metrics_lines.append(f'sophia_backend_requests{{backend="{backend}"}} {count}')
            
            # Memory metrics
            memory_used = system_metrics.memory_usage.get("used_mb", 0)
            memory_total = system_metrics.memory_usage.get("total_mb", 1)
            metrics_lines.append(f"sophia_memory_used_bytes {memory_used * 1024 * 1024}")
            metrics_lines.append(f"sophia_memory_total_bytes {memory_total * 1024 * 1024}")
            
            # Lambda server status
            for server, status in system_metrics.lambda_server_status.items():
                status_value = 1 if status == "healthy" else 0
                metrics_lines.append(f'sophia_lambda_server_healthy{{server="{server}"}} {status_value}')
            
            return "\n".join(metrics_lines)
            
        except Exception as e:
            logger.error(f"Failed to export Prometheus metrics: {e}")
            return f"# Error exporting metrics: {str(e)}"
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for observability service"""
        try:
            health_status = await self._get_health_status()
            
            return {
                "status": "healthy",
                "observability_service": health_status,
                "metrics_collected": {
                    "request_metrics": len(self.request_metrics),
                    "chat_sessions": len(self.chat_sessions),
                    "system_metrics_history": len(self.system_metrics_history)
                },
                "integrations": {
                    "sentry": "configured" if self.sentry_dsn else "not_configured",
                    "prometheus": "enabled" if self.prometheus_enabled else "disabled"
                },
                "background_tasks": {
                    "metrics_collection": "running" if self.metrics_collection_task and not self.metrics_collection_task.done() else "stopped"
                }
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

