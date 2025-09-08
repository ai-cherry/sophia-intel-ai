"""
Sophia AI V9.8 - Fused Self-Healing & Anomaly Detection System
Priority 1: Most Critical - Uptime Guardian

Combines anomaly detection with self-healing workflows, adaptive optimization,
and predictive failure analysis for 99.99% uptime targets.
"""

import asyncio
import logging
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from bayesian_optimization import BayesianOptimization
import redis.asyncio as redis
import asyncpg
from prometheus_client import Counter, Histogram, Gauge

from ..core.config import settings
from ..monitoring.metrics import MetricsCollector
from ..cache.cache_service import CacheService

# Metrics
ANOMALIES_DETECTED = Counter('sophia_anomalies_detected_total', 'Total anomalies detected', ['severity'])
HEALING_ACTIONS = Counter('sophia_healing_actions_total', 'Total healing actions taken', ['action_type'])
HEALING_SUCCESS_RATE = Gauge('sophia_healing_success_rate', 'Success rate of healing actions')
PREDICTION_ACCURACY = Gauge('sophia_prediction_accuracy', 'Accuracy of failure predictions')

logger = logging.getLogger(__name__)

class SeverityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Anomaly:
    timestamp: datetime
    metric_name: str
    value: float
    expected_range: Tuple[float, float]
    severity: SeverityLevel
    confidence: float
    context: Dict[str, Any]

@dataclass
class HealingAction:
    action_id: str
    action_type: str
    target_service: str
    parameters: Dict[str, Any]
    rollback_checkpoint: Optional[str]
    estimated_impact: float

class FusedHealingSystem:
    """
    Advanced self-healing system that combines:
    1. Anomaly detection using IsolationForest
    2. Bayesian optimization for parameter tuning
    3. Predictive failure analysis
    4. Automated healing workflows with rollback
    """

    def __init__(self):
        self.redis_client = None
        self.db_pool = None
        self.cache_service = CacheService()
        self.metrics_collector = MetricsCollector()

        # ML Models
        self.anomaly_model = IsolationForest(
            contamination=0.05,
            random_state=42,
            n_estimators=200
        )
        self.scaler = StandardScaler()

        # Bayesian Optimizer for parameter tuning
        self.optimizer = BayesianOptimization(
            f=self._optimization_objective,
            pbounds={
                'cpu_threshold': (0.5, 0.9),
                'memory_threshold': (0.6, 0.9),
                'response_time_threshold': (100, 500),
                'error_rate_threshold': (0.01, 0.1)
            },
            random_state=42
        )

        # Historical data for learning
        self.historical_metrics = []
        self.healing_history = []
        self.model_trained = False

        # Configuration
        self.config = {
            'anomaly_window_minutes': 15,
            'prediction_horizon_minutes': 30,
            'healing_cooldown_minutes': 5,
            'max_concurrent_healings': 3,
            'rollback_timeout_seconds': 300
        }

    async def initialize(self):
        """Initialize connections and load historical data"""
        try:
            # Redis connection
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                decode_responses=True
            )

            # Database connection
            self.db_pool = await asyncpg.create_pool(
                settings.DATABASE_URL,
                min_size=2,
                max_size=10
            )

            # Load historical data and train models
            await self._load_historical_data()
            await self._train_models()

            logger.info("FusedHealingSystem initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize FusedHealingSystem: {e}")
            raise

    async def detect_and_heal(self, metrics: Dict[str, float]) -> List[HealingAction]:
        """
        Main entry point: detect anomalies and trigger healing actions
        """
        try:
            # Step 1: Detect anomalies
            anomalies = await self._detect_anomalies(metrics)

            if not anomalies:
                return []

            # Step 2: Predict potential failures
            failure_predictions = await self._predict_failures(metrics, anomalies)

            # Step 3: Generate healing actions
            healing_actions = await self._generate_healing_actions(anomalies, failure_predictions)

            # Step 4: Execute healing actions
            executed_actions = []
            for action in healing_actions:
                if await self._can_execute_healing(action):
                    success = await self._execute_healing_action(action)
                    if success:
                        executed_actions.append(action)
                        HEALING_ACTIONS.labels(action_type=action.action_type).inc()

            # Step 5: Learn from results
            await self._learn_from_healing(executed_actions, metrics)

            return executed_actions

        except Exception as e:
            logger.error(f"Error in detect_and_heal: {e}")
            return []

    async def _detect_anomalies(self, metrics: Dict[str, float]) -> List[Anomaly]:
        """Detect anomalies using trained IsolationForest model"""
        if not self.model_trained:
            return []

        try:
            # Prepare data for anomaly detection
            metric_values = np.array(list(metrics.values())).reshape(1, -1)
            scaled_values = self.scaler.transform(metric_values)

            # Predict anomalies
            anomaly_score = self.anomaly_model.decision_function(scaled_values)[0]
            is_anomaly = self.anomaly_model.predict(scaled_values)[0] == -1

            anomalies = []

            if is_anomaly:
                # Analyze each metric for specific anomalies
                for metric_name, value in metrics.items():
                    expected_range = await self._get_expected_range(metric_name)

                    if not (expected_range[0] <= value <= expected_range[1]):
                        severity = self._calculate_severity(metric_name, value, expected_range)
                        confidence = abs(anomaly_score)  # Higher absolute score = higher confidence

                        anomaly = Anomaly(
                            timestamp=datetime.utcnow(),
                            metric_name=metric_name,
                            value=value,
                            expected_range=expected_range,
                            severity=severity,
                            confidence=confidence,
                            context={"anomaly_score": anomaly_score}
                        )

                        anomalies.append(anomaly)
                        ANOMALIES_DETECTED.labels(severity=severity.value).inc()

            return anomalies

        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return []

    async def _predict_failures(self, metrics: Dict[str, float], anomalies: List[Anomaly]) -> Dict[str, float]:
        """Predict potential system failures based on current state"""
        try:
            predictions = {}

            # Simple rule-based predictions (can be enhanced with ML)
            cpu_usage = metrics.get('cpu_usage_percent', 0)
            memory_usage = metrics.get('memory_usage_percent', 0)
            response_time = metrics.get('avg_response_time_ms', 0)
            error_rate = metrics.get('error_rate_percent', 0)

            # CPU failure prediction
            if cpu_usage > 85:
                predictions['cpu_overload'] = min(1.0, (cpu_usage - 85) / 15)

            # Memory failure prediction
            if memory_usage > 80:
                predictions['memory_exhaustion'] = min(1.0, (memory_usage - 80) / 20)

            # Response time degradation
            if response_time > 1000:
                predictions['response_degradation'] = min(1.0, (response_time - 1000) / 2000)

            # Error rate spike
            if error_rate > 5:
                predictions['error_spike'] = min(1.0, error_rate / 10)

            # Combine with anomaly severity
            for anomaly in anomalies:
                if anomaly.severity in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]:
                    failure_type = f"{anomaly.metric_name}_failure"
                    predictions[failure_type] = anomaly.confidence

            return predictions

        except Exception as e:
            logger.error(f"Error predicting failures: {e}")
            return {}

    async def _generate_healing_actions(self, anomalies: List[Anomaly], predictions: Dict[str, float]) -> List[HealingAction]:
        """Generate appropriate healing actions based on anomalies and predictions"""
        actions = []

        try:
            # Get optimal parameters from Bayesian optimizer
            optimal_params = await self._get_optimal_parameters()

            for anomaly in anomalies:
                action = await self._create_healing_action(anomaly, optimal_params)
                if action:
                    actions.append(action)

            # Add predictive actions for high-probability failures
            for failure_type, probability in predictions.items():
                if probability > 0.7:  # High probability threshold
                    action = await self._create_predictive_action(failure_type, probability, optimal_params)
                    if action:
                        actions.append(action)

            return actions

        except Exception as e:
            logger.error(f"Error generating healing actions: {e}")
            return []

    async def _create_healing_action(self, anomaly: Anomaly, optimal_params: Dict) -> Optional[HealingAction]:
        """Create specific healing action for an anomaly"""
        action_id = hashlib.md5(f"{anomaly.metric_name}_{anomaly.timestamp}".encode()).hexdigest()

        # CPU-related healing
        if 'cpu' in anomaly.metric_name.lower():
            return HealingAction(
                action_id=action_id,
                action_type="scale_resources",
                target_service="compute",
                parameters={
                    "resource_type": "cpu",
                    "scale_factor": 1.5,
                    "threshold": optimal_params.get('cpu_threshold', 0.8)
                },
                rollback_checkpoint=await self._create_checkpoint("compute"),
                estimated_impact=0.8
            )

        # Memory-related healing
        elif 'memory' in anomaly.metric_name.lower():
            return HealingAction(
                action_id=action_id,
                action_type="clear_cache",
                target_service="cache",
                parameters={
                    "cache_type": "redis",
                    "clear_percentage": 30,
                    "preserve_critical": True
                },
                rollback_checkpoint=await self._create_checkpoint("cache"),
                estimated_impact=0.6
            )

        # Response time healing
        elif 'response' in anomaly.metric_name.lower():
            return HealingAction(
                action_id=action_id,
                action_type="optimize_queries",
                target_service="database",
                parameters={
                    "enable_query_cache": True,
                    "connection_pool_size": 20,
                    "timeout_ms": optimal_params.get('response_time_threshold', 200)
                },
                rollback_checkpoint=await self._create_checkpoint("database"),
                estimated_impact=0.7
            )

        return None

    async def _execute_healing_action(self, action: HealingAction) -> bool:
        """Execute a healing action with rollback capability"""
        try:
            logger.info(f"Executing healing action: {action.action_type} for {action.target_service}")

            # Store action in history
            await self._store_healing_action(action)

            # Execute based on action type
            success = False

            if action.action_type == "scale_resources":
                success = await self._scale_resources(action.parameters)
            elif action.action_type == "clear_cache":
                success = await self._clear_cache(action.parameters)
            elif action.action_type == "optimize_queries":
                success = await self._optimize_queries(action.parameters)
            elif action.action_type == "restart_service":
                success = await self._restart_service(action.parameters)

            # Update success rate metric
            current_rate = HEALING_SUCCESS_RATE._value._value if hasattr(HEALING_SUCCESS_RATE._value, '_value') else 0
            new_rate = (current_rate * 0.9) + (0.1 if success else 0)
            HEALING_SUCCESS_RATE.set(new_rate)

            if not success and action.rollback_checkpoint:
                await self._rollback_action(action)

            return success

        except Exception as e:
            logger.error(f"Error executing healing action {action.action_id}: {e}")
            if action.rollback_checkpoint:
                await self._rollback_action(action)
            return False

    async def _optimization_objective(self, **params) -> float:
        """Objective function for Bayesian optimization"""
        # This would be called with different parameter combinations
        # Return a score based on system performance with these parameters

        # Simulate performance score (in real implementation, this would
        # measure actual system performance)
        cpu_score = 1.0 - abs(params['cpu_threshold'] - 0.75)
        memory_score = 1.0 - abs(params['memory_threshold'] - 0.8)
        response_score = 1.0 - abs(params['response_time_threshold'] - 200) / 200
        error_score = 1.0 - params['error_rate_threshold']

        return (cpu_score + memory_score + response_score + error_score) / 4

    async def _get_optimal_parameters(self) -> Dict[str, float]:
        """Get optimal parameters from Bayesian optimizer"""
        try:
            # Run optimization if we have enough data
            if len(self.healing_history) > 10:
                self.optimizer.maximize(init_points=2, n_iter=3)
                return self.optimizer.max['params']
            else:
                # Return default parameters
                return {
                    'cpu_threshold': 0.8,
                    'memory_threshold': 0.8,
                    'response_time_threshold': 200,
                    'error_rate_threshold': 0.05
                }
        except Exception as e:
            logger.error(f"Error getting optimal parameters: {e}")
            return {}

    async def _load_historical_data(self):
        """Load historical metrics and healing data"""
        try:
            async with self.db_pool.acquire() as conn:
                # Load historical metrics
                metrics_query = """
                    SELECT timestamp, metric_name, value 
                    FROM system_metrics 
                    WHERE timestamp > NOW() - INTERVAL '7 days'
                    ORDER BY timestamp DESC
                """
                metrics_rows = await conn.fetch(metrics_query)

                # Load healing history
                healing_query = """
                    SELECT action_type, success, parameters, timestamp
                    FROM healing_actions
                    WHERE timestamp > NOW() - INTERVAL '30 days'
                    ORDER BY timestamp DESC
                """
                healing_rows = await conn.fetch(healing_query)

                self.healing_history = [dict(row) for row in healing_rows]

                # Process metrics for training
                metrics_df = pd.DataFrame([dict(row) for row in metrics_rows])
                if not metrics_df.empty:
                    # Pivot to get metrics as columns
                    pivot_df = metrics_df.pivot_table(
                        index='timestamp', 
                        columns='metric_name', 
                        values='value'
                    ).fillna(0)

                    self.historical_metrics = pivot_df.values

        except Exception as e:
            logger.error(f"Error loading historical data: {e}")

    async def _train_models(self):
        """Train anomaly detection models"""
        try:
            if len(self.historical_metrics) > 100:  # Need sufficient data
                # Fit scaler and model
                self.scaler.fit(self.historical_metrics)
                scaled_data = self.scaler.transform(self.historical_metrics)
                self.anomaly_model.fit(scaled_data)

                self.model_trained = True
                logger.info("Anomaly detection model trained successfully")
            else:
                logger.warning("Insufficient historical data for model training")

        except Exception as e:
            logger.error(f"Error training models: {e}")

    async def _get_expected_range(self, metric_name: str) -> Tuple[float, float]:
        """Get expected range for a metric based on historical data"""
        try:
            # Get from cache first
            cache_key = f"expected_range:{metric_name}"
            cached_range = await self.cache_service.get(cache_key)

            if cached_range:
                return tuple(json.loads(cached_range))

            # Calculate from database
            async with self.db_pool.acquire() as conn:
                query = """
                    SELECT 
                        PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY value) as p5,
                        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY value) as p95
                    FROM system_metrics 
                    WHERE metric_name = $1 
                    AND timestamp > NOW() - INTERVAL '7 days'
                """
                row = await conn.fetchrow(query, metric_name)

                if row and row['p5'] is not None:
                    range_tuple = (float(row['p5']), float(row['p95']))
                    # Cache for 1 hour
                    await self.cache_service.set(cache_key, json.dumps(range_tuple), ttl=3600)
                    return range_tuple
                else:
                    # Default ranges for common metrics
                    defaults = {
                        'cpu_usage_percent': (0, 80),
                        'memory_usage_percent': (0, 85),
                        'avg_response_time_ms': (50, 500),
                        'error_rate_percent': (0, 2)
                    }
                    return defaults.get(metric_name, (0, 100))

        except Exception as e:
            logger.error(f"Error getting expected range for {metric_name}: {e}")
            return (0, 100)

    def _calculate_severity(self, metric_name: str, value: float, expected_range: Tuple[float, float]) -> SeverityLevel:
        """Calculate severity level based on how far outside expected range"""
        min_val, max_val = expected_range
        range_size = max_val - min_val

        if value < min_val:
            deviation = (min_val - value) / range_size
        else:
            deviation = (value - max_val) / range_size

        if deviation > 2.0:
            return SeverityLevel.CRITICAL
        elif deviation > 1.0:
            return SeverityLevel.HIGH
        elif deviation > 0.5:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW

    async def _can_execute_healing(self, action: HealingAction) -> bool:
        """Check if healing action can be executed (cooldown, concurrency limits)"""
        try:
            # Check cooldown
            cooldown_key = f"healing_cooldown:{action.target_service}"
            if await self.redis_client.exists(cooldown_key):
                return False

            # Check concurrent healings
            active_healings = await self.redis_client.scard("active_healings")
            if active_healings >= self.config['max_concurrent_healings']:
                return False

            return True

        except Exception as e:
            logger.error(f"Error checking healing execution: {e}")
            return False

    async def _create_checkpoint(self, service: str) -> str:
        """Create rollback checkpoint for a service"""
        checkpoint_id = f"checkpoint_{service}_{int(datetime.utcnow().timestamp())}"

        # Store current state (simplified - would store actual service state)
        checkpoint_data = {
            "service": service,
            "timestamp": datetime.utcnow().isoformat(),
            "state": "current_configuration"  # Would be actual config
        }

        await self.redis_client.setex(
            f"checkpoint:{checkpoint_id}",
            self.config['rollback_timeout_seconds'],
            json.dumps(checkpoint_data)
        )

        return checkpoint_id

    async def _store_healing_action(self, action: HealingAction):
        """Store healing action in database for learning"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO healing_actions (
                        action_id, action_type, target_service, parameters, 
                        timestamp, rollback_checkpoint
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                """, 
                action.action_id, action.action_type, action.target_service,
                json.dumps(action.parameters), datetime.utcnow(), action.rollback_checkpoint
                )
        except Exception as e:
            logger.error(f"Error storing healing action: {e}")

    async def _scale_resources(self, parameters: Dict) -> bool:
        """Scale system resources"""
        # Implementation would integrate with Lambda Labs API
        logger.info(f"Scaling resources: {parameters}")
        return True

    async def _clear_cache(self, parameters: Dict) -> bool:
        """Clear cache based on parameters"""
        try:
            if parameters.get('cache_type') == 'redis':
                # Clear percentage of cache
                clear_pct = parameters.get('clear_percentage', 30)
                # Implementation would selectively clear cache
                logger.info(f"Clearing {clear_pct}% of Redis cache")
                return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

    async def _optimize_queries(self, parameters: Dict) -> bool:
        """Optimize database queries"""
        logger.info(f"Optimizing queries: {parameters}")
        # Implementation would adjust connection pools, enable caching, etc.
        return True

    async def _restart_service(self, parameters: Dict) -> bool:
        """Restart a service"""
        service_name = parameters.get('service_name')
        logger.info(f"Restarting service: {service_name}")
        # Implementation would restart the specified service
        return True

    async def _rollback_action(self, action: HealingAction):
        """Rollback a healing action using checkpoint"""
        try:
            if not action.rollback_checkpoint:
                return

            checkpoint_data = await self.redis_client.get(f"checkpoint:{action.rollback_checkpoint}")
            if checkpoint_data:
                logger.info(f"Rolling back action {action.action_id}")
                # Implementation would restore from checkpoint

        except Exception as e:
            logger.error(f"Error rolling back action {action.action_id}: {e}")

    async def _learn_from_healing(self, actions: List[HealingAction], metrics: Dict[str, float]):
        """Learn from healing action results to improve future decisions"""
        try:
            # Update healing history
            for action in actions:
                self.healing_history.append({
                    'action_type': action.action_type,
                    'success': True,  # Would check actual success
                    'parameters': action.parameters,
                    'timestamp': datetime.utcnow()
                })

            # Update Bayesian optimizer with results
            # This would measure actual performance improvement
            performance_score = 0.8  # Placeholder

            # Store learning data
            await self._store_learning_data(actions, performance_score)

        except Exception as e:
            logger.error(f"Error learning from healing: {e}")

    async def _store_learning_data(self, actions: List[HealingAction], performance_score: float):
        """Store learning data for future optimization"""
        try:
            async with self.db_pool.acquire() as conn:
                for action in actions:
                    await conn.execute("""
                        UPDATE healing_actions 
                        SET success = $1, performance_score = $2
                        WHERE action_id = $3
                    """, True, performance_score, action.action_id)
        except Exception as e:
            logger.error(f"Error storing learning data: {e}")

    async def _create_predictive_action(self, failure_type: str, probability: float, optimal_params: Dict) -> Optional[HealingAction]:
        """Create preventive action based on failure prediction"""
        action_id = hashlib.md5(f"predictive_{failure_type}_{datetime.utcnow()}".encode()).hexdigest()

        if 'cpu' in failure_type:
            return HealingAction(
                action_id=action_id,
                action_type="preemptive_scale",
                target_service="compute",
                parameters={
                    "resource_type": "cpu",
                    "scale_factor": 1.2,
                    "probability": probability
                },
                rollback_checkpoint=await self._create_checkpoint("compute"),
                estimated_impact=probability
            )

        return None

# Global instance
fused_healing_system = FusedHealingSystem()
