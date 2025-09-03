"""
Experimental Evolution Monitoring Dashboard - ADR-002
Provides comprehensive monitoring, reporting, and visualization for experimental evolution.

⚠️ EXPERIMENTAL MONITORING ⚠️

This dashboard monitors experimental evolution systems with real-time metrics,
safety alerts, and performance tracking.
"""

import asyncio
import logging
import statistics
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Optional, Union

from app.swarms.memory_integration import SwarmMemoryClient

from .experimental_evolution_engine import ExperimentalEvolutionEngine, SwarmChromosome
from .integration_adapter import ExperimentalSwarmEvolutionAdapter

logger = logging.getLogger(__name__)


@dataclass
class EvolutionAlert:
    """Alert for evolution system monitoring."""
    alert_id: str
    alert_type: str  # "safety", "performance", "configuration", "experimental"
    severity: str  # "low", "medium", "high", "critical"
    swarm_type: str
    message: str
    timestamp: datetime
    resolved: bool = False
    resolution_timestamp: Optional[datetime] = None
    experimental_context: dict[str, Any] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "swarm_type": self.swarm_type,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved,
            "resolution_timestamp": self.resolution_timestamp.isoformat() if self.resolution_timestamp else None,
            "experimental_context": self.experimental_context or {}
        }


@dataclass
class EvolutionMetrics:
    """Comprehensive evolution metrics."""
    timestamp: datetime
    swarm_type: str

    # Population metrics
    population_size: int
    generation: int
    experimental_variants: int

    # Performance metrics
    average_fitness: float
    best_fitness: float
    fitness_std_dev: float
    performance_trend: float

    # Evolution metrics
    mutation_rate_actual: float
    crossover_rate_actual: float
    selection_pressure_actual: float

    # Safety metrics
    safety_violations_count: int
    rollback_count: int
    risk_score: float

    # Experimental metrics
    breakthrough_events: int
    pattern_discoveries: int
    experimental_mutations: int

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary."""
        return asdict(self)


class ExperimentalEvolutionMonitor:
    """
    Comprehensive monitoring system for experimental evolution engines.
    
    Provides:
    - Real-time performance tracking
    - Safety violation detection
    - Alert management
    - Trend analysis
    - Dashboard data aggregation
    """

    def __init__(self, memory_client: Optional[SwarmMemoryClient] = None):
        """Initialize evolution monitor."""
        self.memory_client = memory_client

        # Monitoring data
        self.tracked_engines: dict[str, ExperimentalEvolutionEngine] = {}
        self.tracked_adapters: dict[str, ExperimentalSwarmEvolutionAdapter] = {}
        self.metrics_history: dict[str, list[EvolutionMetrics]] = {}
        self.active_alerts: dict[str, EvolutionAlert] = {}
        self.resolved_alerts: list[EvolutionAlert] = []

        # Monitoring configuration
        self.monitoring_active = False
        self.monitoring_interval = timedelta(minutes=5)
        self.alert_thresholds = {
            'performance_degradation': 0.15,
            'safety_violation_rate': 0.1,
            'experimental_risk_score': 0.8,
            'fitness_stagnation_generations': 5
        }

        # Statistics
        self.monitoring_stats = {
            'total_alerts': 0,
            'critical_alerts': 0,
            'safety_interventions': 0,
            'monitoring_cycles': 0,
            'last_monitoring_cycle': None
        }

        logger.info("🧪📊 Experimental evolution monitor initialized")

    def register_engine(self, swarm_type: str, engine: ExperimentalEvolutionEngine):
        """Register an evolution engine for monitoring."""
        self.tracked_engines[swarm_type] = engine
        self.metrics_history[swarm_type] = []
        logger.info(f"🧪📊 Registered evolution engine for monitoring: {swarm_type}")

    def register_adapter(self, swarm_type: str, adapter: ExperimentalSwarmEvolutionAdapter):
        """Register an evolution adapter for monitoring."""
        self.tracked_adapters[swarm_type] = adapter
        if swarm_type not in self.metrics_history:
            self.metrics_history[swarm_type] = []
        logger.info(f"🧪📊 Registered evolution adapter for monitoring: {swarm_type}")

    async def start_monitoring(self):
        """Start continuous monitoring."""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        logger.info("🧪📊 Starting experimental evolution monitoring")

        # Start monitoring loop
        asyncio.create_task(self._monitoring_loop())

    async def stop_monitoring(self):
        """Stop monitoring."""
        self.monitoring_active = False
        logger.info("🧪📊 Stopped experimental evolution monitoring")

    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                await self._perform_monitoring_cycle()
                self.monitoring_stats['monitoring_cycles'] += 1
                self.monitoring_stats['last_monitoring_cycle'] = datetime.now().isoformat()

                await asyncio.sleep(self.monitoring_interval.total_seconds())

            except Exception as e:
                logger.error(f"🧪📊 Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def _perform_monitoring_cycle(self):
        """Perform one monitoring cycle."""
        logger.debug("🧪📊 Performing monitoring cycle")

        # Monitor engines
        for swarm_type, engine in self.tracked_engines.items():
            await self._monitor_engine(swarm_type, engine)

        # Monitor adapters
        for swarm_type, adapter in self.tracked_adapters.items():
            await self._monitor_adapter(swarm_type, adapter)

        # Check for alerts
        await self._evaluate_alerts()

        # Store monitoring data
        if self.memory_client:
            await self._store_monitoring_data()

    async def _monitor_engine(self, swarm_type: str, engine: ExperimentalEvolutionEngine):
        """Monitor an evolution engine."""
        try:
            # Get engine status
            status = engine.get_experimental_status(swarm_type)
            if not status or not status.get('evolution_active', False):
                return

            # Get population data
            population = engine.populations.get(swarm_type, [])
            if not population:
                return

            # Calculate metrics
            metrics = await self._calculate_engine_metrics(swarm_type, engine, population)

            # Store metrics
            self.metrics_history[swarm_type].append(metrics)

            # Keep only recent metrics
            max_history = 288  # 24 hours at 5-minute intervals
            if len(self.metrics_history[swarm_type]) > max_history:
                self.metrics_history[swarm_type] = self.metrics_history[swarm_type][-max_history:]

            # Check for issues
            await self._check_engine_issues(swarm_type, engine, metrics)

        except Exception as e:
            logger.error(f"🧪📊 Error monitoring engine {swarm_type}: {e}")

    async def _monitor_adapter(self, swarm_type: str, adapter: ExperimentalSwarmEvolutionAdapter):
        """Monitor an evolution adapter."""
        try:
            # Get adapter status
            status = adapter.get_evolution_status()
            if not status.get('evolution_active', False):
                return

            # Get performance summary
            performance = adapter.get_performance_summary()
            if performance.get('status') == 'no_data':
                return

            # Calculate adapter-specific metrics
            metrics = await self._calculate_adapter_metrics(swarm_type, adapter, status, performance)

            # Store metrics
            if swarm_type not in self.metrics_history:
                self.metrics_history[swarm_type] = []
            self.metrics_history[swarm_type].append(metrics)

            # Check for adapter issues
            await self._check_adapter_issues(swarm_type, adapter, metrics)

        except Exception as e:
            logger.error(f"🧪📊 Error monitoring adapter {swarm_type}: {e}")

    async def _calculate_engine_metrics(self, swarm_type: str, engine: ExperimentalEvolutionEngine,
                                      population: list[SwarmChromosome]) -> EvolutionMetrics:
        """Calculate metrics for an evolution engine."""
        # Population metrics
        population_size = len(population)
        generation = engine.generation_counter.get(swarm_type, 1)
        experimental_variants = sum(1 for c in population if c.experimental_variant)

        # Fitness metrics
        fitness_scores = [c.fitness_score for c in population]
        average_fitness = statistics.mean(fitness_scores) if fitness_scores else 0.0
        best_fitness = max(fitness_scores) if fitness_scores else 0.0
        fitness_std_dev = statistics.stdev(fitness_scores) if len(fitness_scores) > 1 else 0.0

        # Performance trend
        history = self.metrics_history.get(swarm_type, [])
        if len(history) >= 2:
            recent_avg = statistics.mean([m.average_fitness for m in history[-5:]])
            older_avg = statistics.mean([m.average_fitness for m in history[-10:-5]]) if len(history) >= 10 else recent_avg
            performance_trend = recent_avg - older_avg
        else:
            performance_trend = 0.0

        # Evolution rates (actual vs configured)
        config = engine.config
        mutation_rate_actual = config.mutation_rate
        crossover_rate_actual = config.crossover_rate
        selection_pressure_actual = config.selection_pressure

        # Safety metrics
        safety_violations = len(engine.safety_violations)
        rollback_count = engine.evolution_stats.get('rollbacks', 0)
        avg_risk = statistics.mean([c.risk_tolerance for c in population]) if population else 0.0

        # Experimental metrics
        breakthrough_events = len(engine.breakthrough_events)
        pattern_discoveries = engine.evolution_stats.get('patterns_discovered', 0)
        experimental_mutations = sum(c.experimental_mutations_count for c in population)

        return EvolutionMetrics(
            timestamp=datetime.now(),
            swarm_type=swarm_type,
            population_size=population_size,
            generation=generation,
            experimental_variants=experimental_variants,
            average_fitness=average_fitness,
            best_fitness=best_fitness,
            fitness_std_dev=fitness_std_dev,
            performance_trend=performance_trend,
            mutation_rate_actual=mutation_rate_actual,
            crossover_rate_actual=crossover_rate_actual,
            selection_pressure_actual=selection_pressure_actual,
            safety_violations_count=safety_violations,
            rollback_count=rollback_count,
            risk_score=avg_risk,
            breakthrough_events=breakthrough_events,
            pattern_discoveries=pattern_discoveries,
            experimental_mutations=experimental_mutations
        )

    async def _calculate_adapter_metrics(self, swarm_type: str, adapter: ExperimentalSwarmEvolutionAdapter,
                                       status: dict[str, Any], performance: dict[str, Any]) -> EvolutionMetrics:
        """Calculate metrics for an evolution adapter."""
        # Get chromosome if available
        chromosome = adapter.current_best_chromosome

        return EvolutionMetrics(
            timestamp=datetime.now(),
            swarm_type=swarm_type,
            population_size=1,  # Adapter tracks single best
            generation=chromosome.generation if chromosome else 1,
            experimental_variants=1 if chromosome and chromosome.experimental_variant else 0,
            average_fitness=chromosome.fitness_score if chromosome else 0.0,
            best_fitness=chromosome.fitness_score if chromosome else 0.0,
            fitness_std_dev=0.0,  # Single chromosome
            performance_trend=performance.get('improvement_from_baseline', 0.0),
            mutation_rate_actual=adapter.config.experimental_mode.value == 'experimental' and 0.15 or 0.1,
            crossover_rate_actual=0.7,  # Default
            selection_pressure_actual=0.3,  # Default
            safety_violations_count=len(adapter.safety_violations),
            rollback_count=len([v for v in adapter.safety_violations if v.get('type') == 'evolution_rollback']),
            risk_score=chromosome.risk_tolerance if chromosome else 0.0,
            breakthrough_events=0,  # Adapter doesn't track breakthroughs directly
            pattern_discoveries=0,  # Adapter doesn't track patterns directly
            experimental_mutations=chromosome.experimental_mutations_count if chromosome else 0
        )

    async def _check_engine_issues(self, swarm_type: str, engine: ExperimentalEvolutionEngine,
                                 metrics: EvolutionMetrics):
        """Check for issues in evolution engine."""
        # Performance degradation alert
        if metrics.performance_trend < -self.alert_thresholds['performance_degradation']:
            await self._create_alert(
                alert_type="performance",
                severity="high",
                swarm_type=swarm_type,
                message=f"Performance degradation detected: {metrics.performance_trend:.3f}",
                experimental_context={"metrics": metrics.to_dict()}
            )

        # Safety violation alert
        recent_violations = [v for v in engine.safety_violations
                           if (datetime.now() - datetime.fromisoformat(v['timestamp'])).total_seconds() < 3600]
        if len(recent_violations) > self.alert_thresholds['safety_violation_rate'] * 10:
            await self._create_alert(
                alert_type="safety",
                severity="critical",
                swarm_type=swarm_type,
                message=f"High safety violation rate: {len(recent_violations)} violations in last hour",
                experimental_context={"recent_violations": recent_violations}
            )

        # High experimental risk alert
        if metrics.risk_score > self.alert_thresholds['experimental_risk_score']:
            await self._create_alert(
                alert_type="experimental",
                severity="medium",
                swarm_type=swarm_type,
                message=f"High experimental risk score: {metrics.risk_score:.3f}",
                experimental_context={"risk_details": {"population_risk": metrics.risk_score}}
            )

        # Fitness stagnation alert
        history = self.metrics_history.get(swarm_type, [])
        if len(history) >= self.alert_thresholds['fitness_stagnation_generations']:
            recent_fitness = [m.best_fitness for m in history[-self.alert_thresholds['fitness_stagnation_generations']:]]
            if max(recent_fitness) - min(recent_fitness) < 0.01:  # Very little improvement
                await self._create_alert(
                    alert_type="performance",
                    severity="medium",
                    swarm_type=swarm_type,
                    message=f"Fitness stagnation detected over {self.alert_thresholds['fitness_stagnation_generations']} generations",
                    experimental_context={"fitness_trend": recent_fitness}
                )

    async def _check_adapter_issues(self, swarm_type: str, adapter: ExperimentalSwarmEvolutionAdapter,
                                  metrics: EvolutionMetrics):
        """Check for issues in evolution adapter."""
        # Similar checks as engine but adapted for adapter context
        if metrics.performance_trend < -self.alert_thresholds['performance_degradation']:
            await self._create_alert(
                alert_type="performance",
                severity="high",
                swarm_type=swarm_type,
                message=f"Adapter performance degradation: {metrics.performance_trend:.3f}",
                experimental_context={"adapter_metrics": metrics.to_dict()}
            )

    async def _create_alert(self, alert_type: str, severity: str, swarm_type: str,
                          message: str, experimental_context: dict[str, Any] = None):
        """Create a new alert."""
        alert_id = f"{alert_type}_{swarm_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Check if similar alert already exists
        existing_similar = [a for a in self.active_alerts.values()
                          if a.alert_type == alert_type and a.swarm_type == swarm_type and not a.resolved]

        if existing_similar:
            # Update existing alert instead of creating duplicate
            existing_similar[0].message += f" | {message}"
            existing_similar[0].timestamp = datetime.now()
            return

        alert = EvolutionAlert(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            swarm_type=swarm_type,
            message=message,
            timestamp=datetime.now(),
            experimental_context=experimental_context
        )

        self.active_alerts[alert_id] = alert
        self.monitoring_stats['total_alerts'] += 1

        if severity == 'critical':
            self.monitoring_stats['critical_alerts'] += 1
            logger.error(f"🧪📊🚨 CRITICAL EXPERIMENTAL EVOLUTION ALERT [{swarm_type}]: {message}")
        else:
            logger.warning(f"🧪📊⚠️ Experimental evolution alert [{swarm_type}] ({severity}): {message}")

        # Store alert in memory if available
        if self.memory_client:
            try:
                await self.memory_client.store_learning(
                    learning_type="experimental_evolution_alert",
                    content=f"Alert: {alert_type} - {message}",
                    confidence=0.9 if severity in ['high', 'critical'] else 0.7,
                    context={
                        'alert_data': alert.to_dict(),
                        'experimental_monitoring': True
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to store alert in memory: {e}")

    async def resolve_alert(self, alert_id: str, resolution_note: str = ""):
        """Resolve an active alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolution_timestamp = datetime.now()

            # Move to resolved alerts
            self.resolved_alerts.append(alert)
            del self.active_alerts[alert_id]

            logger.info(f"🧪📊✅ Resolved experimental evolution alert {alert_id}: {resolution_note}")

    async def _evaluate_alerts(self):
        """Evaluate and potentially auto-resolve alerts."""
        # Auto-resolve old alerts that might be stale
        current_time = datetime.now()
        stale_alerts = []

        for alert_id, alert in self.active_alerts.items():
            # Auto-resolve alerts older than 1 hour for non-critical issues
            if (alert.severity != 'critical' and
                (current_time - alert.timestamp).total_seconds() > 3600):
                stale_alerts.append(alert_id)

        for alert_id in stale_alerts:
            await self.resolve_alert(alert_id, "Auto-resolved: stale alert")

    async def _store_monitoring_data(self):
        """Store monitoring data in memory."""
        try:
            summary = self.get_monitoring_summary()

            await self.memory_client.store_learning(
                learning_type="experimental_evolution_monitoring",
                content=f"Monitoring cycle: {summary['total_tracked_systems']} systems, {summary['active_alerts']} alerts",
                confidence=1.0,
                context={
                    'monitoring_summary': summary,
                    'experimental_monitoring': True,
                    'timestamp': datetime.now().isoformat()
                }
            )
        except Exception as e:
            logger.warning(f"Failed to store monitoring data: {e}")

    def get_monitoring_summary(self) -> dict[str, Any]:
        """Get comprehensive monitoring summary."""
        # Calculate aggregate metrics
        all_metrics = []
        for swarm_metrics in self.metrics_history.values():
            if swarm_metrics:
                all_metrics.extend(swarm_metrics[-10:])  # Recent metrics only

        if all_metrics:
            avg_fitness = statistics.mean([m.average_fitness for m in all_metrics])
            avg_risk = statistics.mean([m.risk_score for m in all_metrics])
            total_violations = sum([m.safety_violations_count for m in all_metrics])
            total_breakthroughs = sum([m.breakthrough_events for m in all_metrics])
        else:
            avg_fitness = avg_risk = total_violations = total_breakthroughs = 0

        return {
            'monitoring_active': self.monitoring_active,
            'monitoring_stats': self.monitoring_stats,
            'total_tracked_systems': len(self.tracked_engines) + len(self.tracked_adapters),
            'tracked_engines': len(self.tracked_engines),
            'tracked_adapters': len(self.tracked_adapters),
            'active_alerts': len(self.active_alerts),
            'resolved_alerts': len(self.resolved_alerts),
            'alert_breakdown': self._get_alert_breakdown(),
            'aggregate_metrics': {
                'average_fitness_across_swarms': avg_fitness,
                'average_risk_score': avg_risk,
                'total_safety_violations': total_violations,
                'total_breakthrough_events': total_breakthroughs
            },
            'system_health': self._calculate_system_health(),
            'experimental_status': 'active' if any(
                any(m.experimental_variants > 0 for m in metrics)
                for metrics in self.metrics_history.values() if metrics
            ) else 'inactive'
        }

    def _get_alert_breakdown(self) -> dict[str, int]:
        """Get breakdown of alerts by type and severity."""
        breakdown = defaultdict(int)

        for alert in list(self.active_alerts.values()) + self.resolved_alerts:
            breakdown[f"{alert.alert_type}_{alert.severity}"] += 1
            breakdown[f"total_{alert.severity}"] += 1
            breakdown[f"total_{alert.alert_type}"] += 1

        return dict(breakdown)

    def _calculate_system_health(self) -> str:
        """Calculate overall system health status."""
        active_critical = len([a for a in self.active_alerts.values() if a.severity == 'critical'])
        active_high = len([a for a in self.active_alerts.values() if a.severity == 'high'])

        if active_critical > 0:
            return 'critical'
        elif active_high > 2:
            return 'degraded'
        elif active_high > 0 or len(self.active_alerts) > 5:
            return 'warning'
        else:
            return 'healthy'

    def get_dashboard_data(self) -> dict[str, Any]:
        """Get formatted data for dashboard display."""
        summary = self.get_monitoring_summary()

        # Recent metrics for charts
        dashboard_metrics = {}
        for swarm_type, metrics in self.metrics_history.items():
            recent_metrics = metrics[-24:] if metrics else []  # Last 24 data points (2 hours)
            dashboard_metrics[swarm_type] = {
                'fitness_trend': [m.average_fitness for m in recent_metrics],
                'risk_trend': [m.risk_score for m in recent_metrics],
                'generation_progress': [m.generation for m in recent_metrics],
                'experimental_activity': [m.experimental_variants for m in recent_metrics],
                'timestamps': [m.timestamp.isoformat() for m in recent_metrics]
            }

        # Active alerts for dashboard
        dashboard_alerts = [alert.to_dict() for alert in self.active_alerts.values()]

        return {
            'summary': summary,
            'metrics': dashboard_metrics,
            'alerts': dashboard_alerts,
            'system_status': {
                'health': summary['system_health'],
                'monitoring_active': summary['monitoring_active'],
                'last_cycle': summary['monitoring_stats']['last_monitoring_cycle'],
                'experimental_active': summary['experimental_status'] == 'active'
            }
        }

    async def generate_report(self, time_range_hours: int = 24) -> dict[str, Any]:
        """Generate comprehensive monitoring report."""
        cutoff_time = datetime.now() - timedelta(hours=time_range_hours)

        # Filter metrics by time range
        report_metrics = {}
        for swarm_type, metrics in self.metrics_history.items():
            filtered_metrics = [m for m in metrics if m.timestamp >= cutoff_time]
            report_metrics[swarm_type] = filtered_metrics

        # Calculate report statistics
        report_stats = {}
        for swarm_type, metrics in report_metrics.items():
            if not metrics:
                continue

            report_stats[swarm_type] = {
                'total_data_points': len(metrics),
                'avg_fitness': statistics.mean([m.average_fitness for m in metrics]),
                'max_fitness': max([m.best_fitness for m in metrics]),
                'avg_risk': statistics.mean([m.risk_score for m in metrics]),
                'total_safety_violations': sum([m.safety_violations_count for m in metrics]),
                'total_rollbacks': sum([m.rollback_count for m in metrics]),
                'experimental_activity': sum([m.experimental_variants for m in metrics]),
                'breakthrough_events': sum([m.breakthrough_events for m in metrics]),
                'generation_progress': max([m.generation for m in metrics]) - min([m.generation for m in metrics])
            }

        # Report alerts in time range
        report_alerts = [
            alert.to_dict() for alert in (list(self.active_alerts.values()) + self.resolved_alerts)
            if alert.timestamp >= cutoff_time
        ]

        return {
            'report_generated': datetime.now().isoformat(),
            'time_range_hours': time_range_hours,
            'summary': self.get_monitoring_summary(),
            'swarm_statistics': report_stats,
            'alerts_in_period': report_alerts,
            'alert_summary': {
                'total_alerts': len(report_alerts),
                'critical_alerts': len([a for a in report_alerts if a['severity'] == 'critical']),
                'resolved_alerts': len([a for a in report_alerts if a['resolved']])
            },
            'recommendations': self._generate_recommendations(report_stats, report_alerts)
        }

    def _generate_recommendations(self, stats: dict[str, Any], alerts: list[dict[str, Any]]) -> list[str]:
        """Generate recommendations based on monitoring data."""
        recommendations = []

        # Check for consistent high risk
        high_risk_swarms = [
            swarm for swarm, data in stats.items()
            if data.get('avg_risk', 0) > 0.7
        ]
        if high_risk_swarms:
            recommendations.append(
                f"🧪⚠️ Consider reducing risk tolerance for high-risk swarms: {', '.join(high_risk_swarms)}"
            )

        # Check for frequent safety violations
        high_violation_swarms = [
            swarm for swarm, data in stats.items()
            if data.get('total_safety_violations', 0) > 5
        ]
        if high_violation_swarms:
            recommendations.append(
                f"🛡️ Review safety configuration for swarms with frequent violations: {', '.join(high_violation_swarms)}"
            )

        # Check for stagnant evolution
        stagnant_swarms = [
            swarm for swarm, data in stats.items()
            if data.get('generation_progress', 0) < 2 and data.get('total_data_points', 0) > 10
        ]
        if stagnant_swarms:
            recommendations.append(
                f"🔄 Consider increasing mutation rate or selection pressure for stagnant swarms: {', '.join(stagnant_swarms)}"
            )

        # Critical alert patterns
        critical_alerts = [a for a in alerts if a['severity'] == 'critical']
        if len(critical_alerts) > 3:
            recommendations.append(
                f"🚨 High critical alert frequency ({len(critical_alerts)}) - review experimental evolution configuration"
            )

        # Experimental activity recommendations
        total_experimental = sum(data.get('experimental_activity', 0) for data in stats.values())
        if total_experimental == 0:
            recommendations.append(
                "🧪 No experimental variants detected - consider enabling experimental features for exploration"
            )
        elif total_experimental > 100:
            recommendations.append(
                "🧪 High experimental activity detected - ensure adequate monitoring and safety measures"
            )

        if not recommendations:
            recommendations.append("✅ No specific recommendations - system appears to be operating within normal parameters")

        return recommendations


# Global monitor instance
_global_monitor: Optional[ExperimentalEvolutionMonitor] = None

def get_global_monitor() -> ExperimentalEvolutionMonitor:
    """Get the global evolution monitor instance."""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = ExperimentalEvolutionMonitor()
    return _global_monitor

def create_monitor_with_memory(memory_client: SwarmMemoryClient) -> ExperimentalEvolutionMonitor:
    """Create a new monitor with memory integration."""
    return ExperimentalEvolutionMonitor(memory_client)
