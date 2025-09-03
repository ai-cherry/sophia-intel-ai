#!/usr/bin/env python3
"""
Production Deployment Monitor
Tracks all systems and provides real-time health metrics
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any

from app.core.super_orchestrator import get_orchestrator
from app.core.orchestrator_enhancements import SystemStatus, SystemType

class DeploymentMonitor:
    """Monitor production deployment health"""
    
    def __init__(self):
        self.orchestrator = get_orchestrator()
        self.start_time = datetime.now()
        self.metrics_history = []
        
    async def initialize(self):
        """Initialize monitoring"""
        await self.orchestrator.initialize()
        print("✅ Monitoring system initialized")
        
    async def check_health(self) -> Dict[str, Any]:
        """Check system health"""
        health = self.orchestrator.registry.get_health_report()
        
        # Get detailed metrics
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "uptime": str(datetime.now() - self.start_time),
            "health_score": health["health_score"],
            "total_systems": health["total_systems"],
            "by_status": health["by_status"],
            "by_type": health["by_type"],
            "cost_per_hour": self.orchestrator._calculate_cost(),
            "memory_usage": await self._get_memory_usage(),
            "error_rate": self._calculate_error_rate()
        }
        
        self.metrics_history.append(metrics)
        return metrics
    
    async def _get_memory_usage(self) -> float:
        """Get memory usage in MB"""
        try:
            import psutil
            return psutil.Process().memory_info().rss / 1024 / 1024
        except:
            return 0.0
    
    def _calculate_error_rate(self) -> float:
        """Calculate error rate"""
        total = len(self.orchestrator.registry.systems)
        if total == 0:
            return 0.0
        
        errors = sum(1 for s in self.orchestrator.registry.systems.values() 
                    if s.status == SystemStatus.ERROR)
        return (errors / total) * 100
    
    async def monitor_loop(self, interval: int = 10):
        """Main monitoring loop"""
        print("\n" + "="*60)
        print("🚀 DEPLOYMENT MONITORING ACTIVE")
        print("="*60)
        
        while True:
            try:
                # Get current metrics
                metrics = await self.check_health()
                
                # Clear screen for clean display
                print("\033[2J\033[H")  # Clear screen and move to top
                
                # Display dashboard
                print("="*60)
                print(f"📊 PRODUCTION MONITORING - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("="*60)
                
                # Health Overview
                health_emoji = "🟢" if metrics["health_score"] > 90 else "🟡" if metrics["health_score"] > 70 else "🔴"
                print(f"\n{health_emoji} Health Score: {metrics['health_score']:.1f}%")
                print(f"⏱️  Uptime: {metrics['uptime']}")
                print(f"💰 Cost/hour: ${metrics['cost_per_hour']:.4f}")
                print(f"🧠 Memory: {metrics['memory_usage']:.1f} MB")
                print(f"⚠️  Error Rate: {metrics['error_rate']:.1f}%")
                
                # System Distribution
                print("\n📦 Active Systems:")
                for sys_type, count in metrics["by_type"].items():
                    if count > 0:
                        print(f"  • {sys_type}: {count}")
                
                # Status Distribution
                print("\n📈 Status Distribution:")
                for status, count in metrics["by_status"].items():
                    if count > 0:
                        emoji = "🟢" if status == "active" else "🔵" if status == "processing" else "🟡" if status == "idle" else "🔴"
                        print(f"  {emoji} {status}: {count}")
                
                # Personality Commentary
                if metrics["health_score"] < 80 or metrics["error_rate"] > 10:
                    response = self.orchestrator.personality.generate_response(
                        "analysis",
                        data={
                            "health_score": metrics["health_score"],
                            "active_systems": metrics["total_systems"],
                            "cost": metrics["cost_per_hour"] * 24
                        }
                    )
                    print(f"\n💭 Orchestrator: {response}")
                
                # Suggestions
                if metrics["total_systems"] > 0:
                    context = {
                        "error_count": sum(1 for s in self.orchestrator.registry.systems.values() 
                                         if s.status == SystemStatus.ERROR),
                        "cost_today": metrics["cost_per_hour"] * 24,
                        "idle_systems": metrics["by_status"].get("idle", 0),
                        "active_systems": metrics["by_status"].get("active", 0)
                    }
                    
                    suggestions = self.orchestrator.suggestions.get_contextual_suggestions(context)
                    if suggestions:
                        print("\n💡 Suggestions:")
                        for suggestion in suggestions[:3]:
                            print(f"  • {suggestion}")
                
                # Alert conditions
                alerts = []
                if metrics["health_score"] < 70:
                    alerts.append("🚨 Health score critically low!")
                if metrics["error_rate"] > 20:
                    alerts.append("🚨 High error rate detected!")
                if metrics["cost_per_hour"] > 1.0:
                    alerts.append("💸 High operational cost!")
                
                if alerts:
                    print("\n⚠️ ALERTS:")
                    for alert in alerts:
                        print(f"  {alert}")
                
                print("\n" + "-"*60)
                print("Press Ctrl+C to stop monitoring")
                
                # Wait for next interval
                await asyncio.sleep(interval)
                
            except KeyboardInterrupt:
                print("\n\n👋 Monitoring stopped by user")
                break
            except Exception as e:
                print(f"\n❌ Monitoring error: {e}")
                await asyncio.sleep(interval)
    
    async def generate_report(self):
        """Generate final monitoring report"""
        if not self.metrics_history:
            return
        
        # Calculate averages
        avg_health = sum(m["health_score"] for m in self.metrics_history) / len(self.metrics_history)
        avg_cost = sum(m["cost_per_hour"] for m in self.metrics_history) / len(self.metrics_history)
        avg_error = sum(m["error_rate"] for m in self.metrics_history) / len(self.metrics_history)
        
        report = {
            "monitoring_period": str(datetime.now() - self.start_time),
            "total_samples": len(self.metrics_history),
            "average_health": avg_health,
            "average_cost_per_hour": avg_cost,
            "average_error_rate": avg_error,
            "final_metrics": self.metrics_history[-1] if self.metrics_history else None
        }
        
        # Save report
        with open("deployment_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print("\n📊 MONITORING REPORT")
        print("="*60)
        print(f"Period: {report['monitoring_period']}")
        print(f"Samples: {report['total_samples']}")
        print(f"Avg Health: {report['average_health']:.1f}%")
        print(f"Avg Cost/hr: ${report['average_cost_per_hour']:.4f}")
        print(f"Avg Error Rate: {report['average_error_rate']:.1f}%")
        print("\n✅ Report saved to deployment_report.json")

async def main():
    """Main monitoring entry point"""
    monitor = DeploymentMonitor()
    await monitor.initialize()
    
    try:
        await monitor.monitor_loop(interval=5)  # Update every 5 seconds
    finally:
        await monitor.generate_report()
        await monitor.orchestrator.shutdown()

if __name__ == "__main__":
    asyncio.run(main())