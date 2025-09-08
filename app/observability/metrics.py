"""
Sophia AI Metrics Collection - Memray Leak Detection & Performance Monitoring
Advanced Python performance monitoring with memory leak detection

This module provides comprehensive performance monitoring:
- Memray integration for memory leak detection (May '25 updates)
- Custom metrics for cache performance and system resources
- Automatic performance profiling and optimization suggestions
- Memory usage tracking with leak detection algorithms
- Zero performance debt monitoring

Author: Manus AI - Hellfire Architecture Division
Date: August 8, 2025
Version: 1.0.0 - Performance Inferno
"""

import asyncio
import gc
import logging
import os
import psutil
import resource
import sys
import threading
import time
import tracemalloc
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Callable
from pathlib import Path

import memray
import numpy as np
from prometheus_client import Counter, Histogram, Gauge, Info, Summary

logger = logging.getLogger(__name__)

@dataclass
class MemorySnapshot:
    """Memory usage snapshot for leak detection"""
    timestamp: float
    rss_mb: float
    vms_mb: float
    heap_mb: float
    python_objects: int
    gc_collections: Tuple[int, int, int]
    tracemalloc_peak_mb: float
    component: str = "system"

@dataclass
class PerformanceProfile:
    """Performance profile for optimization analysis"""
    operation: str
    duration_ms: float
    memory_delta_mb: float
    cpu_percent: float
    io_operations: int
    cache_hits: int
    cache_misses: int
    timestamp: float
    component: str

class MemoryLeakDetector:
    """
    Advanced memory leak detection using multiple algorithms
    Integrates with Memray for deep memory analysis
    """
    
    def __init__(self, window_size: int = 100, leak_threshold_mb: float = 50.0):
        self.window_size = window_size
        self.leak_threshold_mb = leak_threshold_mb
        self.snapshots = deque(maxlen=window_size)
        self.leak_alerts = []
        self.monitoring_active = False
        self.memray_tracker = None
        
        # Enable tracemalloc for detailed tracking
        if not tracemalloc.is_tracing():
            tracemalloc.start(25)  # Keep 25 frames
        
        logger.info("🔥 Memory leak detector initialized")
    
    def start_memray_tracking(self, output_file: str = "sophia_memory_profile.bin"):
        """Start Memray tracking for detailed memory analysis"""
        try:
            self.memray_tracker = memray.Tracker(output_file)
            self.memray_tracker.__enter__()
            logger.info(f"✅ Memray tracking started: {output_file}")
        except Exception as e:
            logger.error(f"Failed to start Memray tracking: {e}")
    
    def stop_memray_tracking(self):
        """Stop Memray tracking and generate report"""
        if self.memray_tracker:
            try:
                self.memray_tracker.__exit__(None, None, None)
                logger.info("✅ Memray tracking stopped")
            except Exception as e:
                logger.error(f"Failed to stop Memray tracking: {e}")
            finally:
                self.memray_tracker = None
    
    def take_snapshot(self, component: str = "system") -> MemorySnapshot:
        """Take a memory usage snapshot"""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        # Get tracemalloc statistics
        tracemalloc_current, tracemalloc_peak = tracemalloc.get_traced_memory()
        
        # Get GC statistics
        gc_stats = gc.get_stats()
        gc_collections = tuple(stat['collections'] for stat in gc_stats)
        
        snapshot = MemorySnapshot(
            timestamp=time.time(),
            rss_mb=memory_info.rss / 1024 / 1024,
            vms_mb=memory_info.vms / 1024 / 1024,
            heap_mb=tracemalloc_current / 1024 / 1024,
            python_objects=len(gc.get_objects()),
            gc_collections=gc_collections,
            tracemalloc_peak_mb=tracemalloc_peak / 1024 / 1024,
            component=component
        )
        
        self.snapshots.append(snapshot)
        return snapshot
    
    def detect_leaks(self) -> List[Dict[str, Any]]:
        """
        Detect memory leaks using multiple algorithms
        """
        if len(self.snapshots) < 10:
            return []
        
        leaks = []
        
        # Algorithm 1: Linear trend analysis
        leak = self._detect_linear_trend()
        if leak:
            leaks.append(leak)
        
        # Algorithm 2: Exponential growth detection
        leak = self._detect_exponential_growth()
        if leak:
            leaks.append(leak)
        
        # Algorithm 3: GC inefficiency detection
        leak = self._detect_gc_inefficiency()
        if leak:
            leaks.append(leak)
        
        # Algorithm 4: Object count explosion
        leak = self._detect_object_explosion()
        if leak:
            leaks.append(leak)
        
        return leaks
    
    def _detect_linear_trend(self) -> Optional[Dict[str, Any]]:
        """Detect linear memory growth trend"""
        if len(self.snapshots) < 20:
            return None
        
        # Get recent memory usage
        recent_snapshots = list(self.snapshots)[-20:]
        timestamps = [s.timestamp for s in recent_snapshots]
        rss_values = [s.rss_mb for s in recent_snapshots]
        
        # Calculate linear regression
        n = len(timestamps)
        sum_x = sum(timestamps)
        sum_y = sum(rss_values)
        sum_xy = sum(t * r for t, r in zip(timestamps, rss_values))
        sum_x2 = sum(t * t for t in timestamps)
        
        # Slope calculation
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        # Convert slope to MB/hour
        slope_mb_per_hour = slope * 3600
        
        if slope_mb_per_hour > 10.0:  # Growing > 10MB/hour
            return {
                "type": "linear_trend",
                "severity": "high" if slope_mb_per_hour > 50 else "medium",
                "growth_rate_mb_per_hour": slope_mb_per_hour,
                "description": f"Linear memory growth detected: {slope_mb_per_hour:.1f} MB/hour",
                "recommendation": "Check for unclosed resources or growing caches"
            }
        
        return None
    
    def _detect_exponential_growth(self) -> Optional[Dict[str, Any]]:
        """Detect exponential memory growth"""
        if len(self.snapshots) < 15:
            return None
        
        recent_snapshots = list(self.snapshots)[-15:]
        
        # Check for doubling pattern
        growth_ratios = []
        for i in range(1, len(recent_snapshots)):
            prev_rss = recent_snapshots[i-1].rss_mb
            curr_rss = recent_snapshots[i].rss_mb
            if prev_rss > 0:
                ratio = curr_rss / prev_rss
                growth_ratios.append(ratio)
        
        # Average growth ratio
        if growth_ratios:
            avg_ratio = sum(growth_ratios) / len(growth_ratios)
            if avg_ratio > 1.05:  # Growing > 5% per snapshot
                return {
                    "type": "exponential_growth",
                    "severity": "critical",
                    "growth_ratio": avg_ratio,
                    "description": f"Exponential memory growth detected: {avg_ratio:.3f}x per measurement",
                    "recommendation": "Immediate investigation required - possible memory bomb"
                }
        
        return None
    
    def _detect_gc_inefficiency(self) -> Optional[Dict[str, Any]]:
        """Detect garbage collection inefficiency"""
        if len(self.snapshots) < 10:
            return None
        
        recent_snapshots = list(self.snapshots)[-10:]
        
        # Check GC collection frequency vs memory growth
        gc_increases = 0
        memory_increases = 0
        
        for i in range(1, len(recent_snapshots)):
            prev = recent_snapshots[i-1]
            curr = recent_snapshots[i]
            
            # Check if GC collections increased
            if sum(curr.gc_collections) > sum(prev.gc_collections):
                gc_increases += 1
            
            # Check if memory increased
            if curr.rss_mb > prev.rss_mb:
                memory_increases += 1
        
        # If memory keeps growing despite frequent GC
        if gc_increases > 5 and memory_increases > 7:
            return {
                "type": "gc_inefficiency",
                "severity": "medium",
                "gc_frequency": gc_increases,
                "memory_growth_frequency": memory_increases,
                "description": "Garbage collection inefficiency detected",
                "recommendation": "Check for circular references or C extension leaks"
            }
        
        return None
    
    def _detect_object_explosion(self) -> Optional[Dict[str, Any]]:
        """Detect Python object count explosion"""
        if len(self.snapshots) < 5:
            return None
        
        recent_snapshots = list(self.snapshots)[-5:]
        
        # Check object count growth
        first_count = recent_snapshots[0].python_objects
        last_count = recent_snapshots[-1].python_objects
        
        if first_count > 0:
            growth_ratio = last_count / first_count
            if growth_ratio > 2.0:  # Object count doubled
                return {
                    "type": "object_explosion",
                    "severity": "high",
                    "object_growth_ratio": growth_ratio,
                    "object_count": last_count,
                    "description": f"Python object explosion: {growth_ratio:.1f}x growth",
                    "recommendation": "Check for object creation without cleanup"
                }
        
        return None
    
    def get_memory_report(self) -> Dict[str, Any]:
        """Get comprehensive memory usage report"""
        if not self.snapshots:
            return {"error": "No snapshots available"}
        
        latest = self.snapshots[-1]
        
        # Calculate trends if we have enough data
        trends = {}
        if len(self.snapshots) >= 5:
            first = self.snapshots[-5]
            trends = {
                "rss_trend_mb": latest.rss_mb - first.rss_mb,
                "heap_trend_mb": latest.heap_mb - first.heap_mb,
                "object_trend": latest.python_objects - first.python_objects,
                "time_window_minutes": (latest.timestamp - first.timestamp) / 60
            }
        
        # Detect leaks
        leaks = self.detect_leaks()
        
        return {
            "current_usage": {
                "rss_mb": latest.rss_mb,
                "vms_mb": latest.vms_mb,
                "heap_mb": latest.heap_mb,
                "python_objects": latest.python_objects,
                "tracemalloc_peak_mb": latest.tracemalloc_peak_mb
            },
            "trends": trends,
            "leaks_detected": leaks,
            "leak_count": len(leaks),
            "severity": "critical" if any(l.get("severity") == "critical" for l in leaks) else
                       "high" if any(l.get("severity") == "high" for l in leaks) else
                       "medium" if any(l.get("severity") == "medium" for l in leaks) else "low",
            "recommendations": [leak.get("recommendation", "") for leak in leaks],
            "snapshot_count": len(self.snapshots),
            "monitoring_duration_hours": (latest.timestamp - self.snapshots[0].timestamp) / 3600 if len(self.snapshots) > 1 else 0
        }

class PerformanceProfiler:
    """
    Performance profiler with automatic optimization suggestions
    """
    
    def __init__(self, max_profiles: int = 1000):
        self.max_profiles = max_profiles
        self.profiles = deque(maxlen=max_profiles)
        self.operation_stats = defaultdict(list)
        
    def profile_operation(
        self,
        operation: str,
        component: str = "unknown"
    ):
        """Context manager for profiling operations"""
        
        class OperationProfiler:
            def __init__(self, profiler, operation, component):
                self.profiler = profiler
                self.operation = operation
                self.component = component
                self.start_time = None
                self.start_memory = None
                self.start_cpu_times = None
                
            def __enter__(self):
                self.start_time = time.perf_counter()
                
                # Get memory info
                process = psutil.Process()
                self.start_memory = process.memory_info().rss / 1024 / 1024
                self.start_cpu_times = process.cpu_times()
                
                return self
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                end_time = time.perf_counter()
                duration_ms = (end_time - self.start_time) * 1000
                
                # Calculate resource usage
                process = psutil.Process()
                end_memory = process.memory_info().rss / 1024 / 1024
                memory_delta_mb = end_memory - self.start_memory
                
                end_cpu_times = process.cpu_times()
                cpu_delta = (end_cpu_times.user - self.start_cpu_times.user) + \
                           (end_cpu_times.system - self.start_cpu_times.system)
                cpu_percent = (cpu_delta / (duration_ms / 1000)) * 100 if duration_ms > 0 else 0
                
                # Create profile
                profile = PerformanceProfile(
                    operation=self.operation,
                    duration_ms=duration_ms,
                    memory_delta_mb=memory_delta_mb,
                    cpu_percent=cpu_percent,
                    io_operations=0,  # Would need more detailed tracking
                    cache_hits=0,     # Would be set by cache operations
                    cache_misses=0,   # Would be set by cache operations
                    timestamp=time.time(),
                    component=self.component
                )
                
                self.profiler.add_profile(profile)
        
        return OperationProfiler(self, operation, component)
    
    def add_profile(self, profile: PerformanceProfile):
        """Add a performance profile"""
        self.profiles.append(profile)
        self.operation_stats[profile.operation].append(profile)
        
        # Keep operation stats bounded
        if len(self.operation_stats[profile.operation]) > 100:
            self.operation_stats[profile.operation] = \
                self.operation_stats[profile.operation][-50:]
    
    def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """Get optimization suggestions based on profiles"""
        suggestions = []
        
        for operation, profiles in self.operation_stats.items():
            if len(profiles) < 5:
                continue
            
            # Calculate statistics
            durations = [p.duration_ms for p in profiles[-20:]]  # Last 20
            memory_deltas = [p.memory_delta_mb for p in profiles[-20:]]
            
            avg_duration = sum(durations) / len(durations)
            avg_memory_delta = sum(memory_deltas) / len(memory_deltas)
            
            # Check for slow operations
            if avg_duration > 1000:  # > 1 second
                suggestions.append({
                    "type": "slow_operation",
                    "operation": operation,
                    "avg_duration_ms": avg_duration,
                    "severity": "high" if avg_duration > 5000 else "medium",
                    "suggestion": f"Operation '{operation}' is slow ({avg_duration:.1f}ms avg). Consider caching or optimization.",
                    "component": profiles[-1].component
                })
            
            # Check for memory-intensive operations
            if avg_memory_delta > 10:  # > 10MB average growth
                suggestions.append({
                    "type": "memory_intensive",
                    "operation": operation,
                    "avg_memory_delta_mb": avg_memory_delta,
                    "severity": "medium",
                    "suggestion": f"Operation '{operation}' uses significant memory ({avg_memory_delta:.1f}MB avg). Check for memory leaks.",
                    "component": profiles[-1].component
                })
            
            # Check for high variance (inconsistent performance)
            if len(durations) > 10:
                duration_std = np.std(durations)
                if duration_std > avg_duration * 0.5:  # High variance
                    suggestions.append({
                        "type": "inconsistent_performance",
                        "operation": operation,
                        "avg_duration_ms": avg_duration,
                        "std_deviation_ms": duration_std,
                        "severity": "low",
                        "suggestion": f"Operation '{operation}' has inconsistent performance. Consider investigating load-dependent factors.",
                        "component": profiles[-1].component
                    })
        
        return suggestions
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        if not self.profiles:
            return {"error": "No profiles available"}
        
        # Overall statistics
        all_durations = [p.duration_ms for p in self.profiles]
        all_memory_deltas = [p.memory_delta_mb for p in self.profiles]
        
        # Operation breakdown
        operation_summary = {}
        for operation, profiles in self.operation_stats.items():
            durations = [p.duration_ms for p in profiles]
            operation_summary[operation] = {
                "count": len(profiles),
                "avg_duration_ms": sum(durations) / len(durations),
                "min_duration_ms": min(durations),
                "max_duration_ms": max(durations),
                "total_duration_ms": sum(durations)
            }
        
        return {
            "total_operations": len(self.profiles),
            "avg_duration_ms": sum(all_durations) / len(all_durations),
            "total_memory_delta_mb": sum(all_memory_deltas),
            "operation_breakdown": operation_summary,
            "optimization_suggestions": self.get_optimization_suggestions(),
            "monitoring_period_hours": (self.profiles[-1].timestamp - self.profiles[0].timestamp) / 3600 if len(self.profiles) > 1 else 0
        }

class SophiaMetricsCollector:
    """
    Comprehensive metrics collector for Sophia AI
    Integrates memory leak detection and performance profiling
    """
    
    def __init__(self):
        self.leak_detector = MemoryLeakDetector()
        self.profiler = PerformanceProfiler()
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # Prometheus metrics
        self.memory_usage_gauge = Gauge(
            'sophia_memory_usage_mb',
            'Memory usage by component and type',
            ['component', 'memory_type']
        )
        
        self.performance_histogram = Histogram(
            'sophia_operation_duration_seconds',
            'Operation duration by component and operation',
            ['component', 'operation'],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        )
        
        self.leak_detection_gauge = Gauge(
            'sophia_memory_leaks_detected',
            'Number of memory leaks detected by severity',
            ['severity']
        )
        
        self.system_resources_gauge = Gauge(
            'sophia_system_resources',
            'System resource utilization',
            ['resource_type']
        )
        
        logger.info("🔥 Sophia metrics collector initialized")
    
    def start_monitoring(self, interval_seconds: int = 30):
        """Start background monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self.monitoring_thread.start()
        
        logger.info(f"✅ Background monitoring started (interval: {interval_seconds}s)")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        logger.info("✅ Background monitoring stopped")
    
    def _monitoring_loop(self, interval_seconds: int):
        """Background monitoring loop"""
        while self.monitoring_active:
            try:
                # Take memory snapshot
                snapshot = self.leak_detector.take_snapshot("background_monitor")
                
                # Update Prometheus metrics
                self.memory_usage_gauge.labels(
                    component="system",
                    memory_type="rss"
                ).set(snapshot.rss_mb)
                
                self.memory_usage_gauge.labels(
                    component="system", 
                    memory_type="heap"
                ).set(snapshot.heap_mb)
                
                # Update system resource metrics
                self._update_system_metrics()
                
                # Check for leaks
                leaks = self.leak_detector.detect_leaks()
                leak_counts = defaultdict(int)
                for leak in leaks:
                    leak_counts[leak.get("severity", "unknown")] += 1
                
                for severity in ["low", "medium", "high", "critical"]:
                    self.leak_detection_gauge.labels(severity=severity).set(
                        leak_counts[severity]
                    )
                
                # Log critical leaks
                critical_leaks = [l for l in leaks if l.get("severity") == "critical"]
                if critical_leaks:
                    logger.error(f"🚨 CRITICAL MEMORY LEAKS DETECTED: {len(critical_leaks)}")
                    for leak in critical_leaks:
                        logger.error(f"  - {leak['description']}")
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
            
            time.sleep(interval_seconds)
    
    def _update_system_metrics(self):
        """Update system resource metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.system_resources_gauge.labels(resource_type="cpu_percent").set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.system_resources_gauge.labels(resource_type="memory_percent").set(memory.percent)
            self.system_resources_gauge.labels(resource_type="memory_available_gb").set(memory.available / 1024**3)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.system_resources_gauge.labels(resource_type="disk_percent").set(disk.percent)
            
            # Network I/O
            network = psutil.net_io_counters()
            self.system_resources_gauge.labels(resource_type="network_bytes_sent").set(network.bytes_sent)
            self.system_resources_gauge.labels(resource_type="network_bytes_recv").set(network.bytes_recv)
            
        except Exception as e:
            logger.error(f"Failed to update system metrics: {e}")
    
    def profile_operation(self, operation: str, component: str = "unknown"):
        """Profile an operation with automatic metrics recording"""
        
        class MetricsOperationProfiler:
            def __init__(self, collector, operation, component):
                self.collector = collector
                self.operation = operation
                self.component = component
                self.profiler_context = None
                
            def __enter__(self):
                self.profiler_context = self.collector.profiler.profile_operation(
                    self.operation, self.component
                ).__enter__()
                return self
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.profiler_context:
                    self.profiler_context.__exit__(exc_type, exc_val, exc_tb)
                
                # Record in Prometheus histogram
                if hasattr(self.profiler_context, 'start_time'):
                    duration = time.perf_counter() - self.profiler_context.start_time
                    self.collector.performance_histogram.labels(
                        component=self.component,
                        operation=self.operation
                    ).observe(duration)
        
        return MetricsOperationProfiler(self, operation, component)
    
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Get comprehensive performance and memory report"""
        memory_report = self.leak_detector.get_memory_report()
        performance_report = self.profiler.get_performance_summary()
        
        return {
            "timestamp": time.time(),
            "memory_analysis": memory_report,
            "performance_analysis": performance_report,
            "monitoring_status": {
                "active": self.monitoring_active,
                "memray_active": self.leak_detector.memray_tracker is not None
            },
            "system_health": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent
            },
            "recommendations": self._generate_recommendations(memory_report, performance_report),
            "status": "🔥 METRICS INFERNO ACTIVE"
        }
    
    def _generate_recommendations(self, memory_report: Dict, performance_report: Dict) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        # Memory recommendations
        if memory_report.get("leak_count", 0) > 0:
            recommendations.append("🚨 Memory leaks detected - investigate immediately")
        
        current_usage = memory_report.get("current_usage", {})
        if current_usage.get("rss_mb", 0) > 1000:  # > 1GB
            recommendations.append("💾 High memory usage detected - consider optimization")
        
        # Performance recommendations
        if "optimization_suggestions" in performance_report:
            for suggestion in performance_report["optimization_suggestions"]:
                recommendations.append(f"⚡ {suggestion.get('suggestion', '')}")
        
        # System recommendations
        try:
            if psutil.cpu_percent() > 80:
                recommendations.append("🔥 High CPU usage - check for CPU-intensive operations")
            
            if psutil.virtual_memory().percent > 85:
                recommendations.append("💾 High system memory usage - consider scaling")
        except:
        
        return recommendations
    
    def start_memray_session(self, output_file: str = None):
        """Start Memray profiling session"""
        if not output_file:
            output_file = f"sophia_memory_profile_{int(time.time())}.bin"
        
        self.leak_detector.start_memray_tracking(output_file)
        return output_file
    
    def stop_memray_session(self):
        """Stop Memray profiling session"""
        self.leak_detector.stop_memray_tracking()

# Global metrics collector instance
metrics_collector = SophiaMetricsCollector()

# Export key functions and classes
__all__ = [
    "SophiaMetricsCollector",
    "MemoryLeakDetector", 
    "PerformanceProfiler",
    "MemorySnapshot",
    "PerformanceProfile",
    "metrics_collector"
]

