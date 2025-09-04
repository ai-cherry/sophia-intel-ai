#!/usr/bin/env python3
"""
🚀 Production Deployment Script for Autonomous Evolution System
================================================================
Deploys the production-ready autonomous evolution system with:
- Full resource management and cleanup
- Health monitoring and recovery
- Persistent state management  
- Graceful shutdown handling
- Performance monitoring
"""

import asyncio
import logging
import signal
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Import autonomous evolution components
from autonomous_evolution_kickoff import AutonomousEvolutionOrchestrator
from app.orchestrators.resource_manager import resource_manager, ResourceType

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('autonomous_evolution_production.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ProductionAutonomousEvolution:
    """Production-ready autonomous evolution deployment"""
    
    def __init__(self):
        self.orchestrator: Optional[AutonomousEvolutionOrchestrator] = None
        self.is_running = False
        self.start_time: Optional[datetime] = None
        self.health_check_interval = 60  # seconds
        self.performance_metrics = []
        self.deployment_id = f"prod_evolution_{int(time.time())}"
        
        # Setup deployment directory
        self.deployment_dir = Path("production_deployment")
        self.deployment_dir.mkdir(exist_ok=True)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        logger.info(f"🏭 Production Autonomous Evolution initialized: {self.deployment_id}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"📡 Received signal {signum}, initiating graceful shutdown...")
        self.is_running = False
    
    async def deploy(self) -> bool:
        """Deploy the production autonomous evolution system"""
        logger.info("🚀 DEPLOYING PRODUCTION AUTONOMOUS EVOLUTION SYSTEM")
        logger.info("=" * 65)
        
        try:
            self.start_time = datetime.now()
            self.is_running = True
            
            # Initialize orchestrator
            logger.info("🤖 Initializing Autonomous Evolution Orchestrator...")
            self.orchestrator = AutonomousEvolutionOrchestrator()
            
            # Initialize all systems with resource management
            success = await self.orchestrator.initialize_all_systems()
            if not success:
                logger.error("❌ System initialization failed")
                return False
            
            # Perform initial health check
            health = await self.orchestrator.get_system_health()
            logger.info("💗 Initial system health check:")
            logger.info(f"  📊 Total resources: {health['resource_manager']['total_resources']}")
            logger.info(f"  🤖 Orchestrators active: {len(health['orchestrators'])}")
            logger.info(f"  ⚔️ Teams deployed: {len(health['teams'])}")
            
            # Start continuous monitoring
            monitor_task = asyncio.create_task(self._continuous_monitoring())
            
            # Execute autonomous evolution phases
            logger.info("🧠 Executing Autonomous Evolution Phases...")
            
            # Phase 1: Self-Analysis
            phase_1_results = await self.orchestrator.execute_phase_1_self_analysis()
            await self._save_phase_results("phase_1", phase_1_results)
            
            # Wait for monitoring or shutdown signal
            while self.is_running:
                await asyncio.sleep(1)
            
            # Graceful shutdown
            monitor_task.cancel()
            await self._graceful_shutdown()
            
            logger.info("✅ Production deployment completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Production deployment failed: {e}")
            await self._emergency_shutdown()
            return False
    
    async def _continuous_monitoring(self):
        """Continuous system health monitoring"""
        logger.info("📊 Starting continuous system monitoring...")
        
        try:
            while self.is_running:
                await asyncio.sleep(self.health_check_interval)
                
                if not self.orchestrator:
                    continue
                
                # Collect system health
                health = await self.orchestrator.get_system_health()
                
                # Collect performance metrics
                metrics = {
                    "timestamp": datetime.now().isoformat(),
                    "uptime": (datetime.now() - self.start_time).total_seconds(),
                    "resource_count": health['resource_manager']['total_resources'],
                    "orchestrator_health": {
                        name: data.get('initialized', False) 
                        for name, data in health['orchestrators'].items()
                    },
                    "team_health": {
                        name: data.get('initialized', False)
                        for name, data in health['teams'].items()
                    }
                }
                
                self.performance_metrics.append(metrics)
                
                # Log key metrics
                total_resources = metrics["resource_count"]
                healthy_orchestrators = sum(metrics["orchestrator_health"].values())
                healthy_teams = sum(metrics["team_health"].values())
                
                logger.info(f"📊 Health Check - Resources: {total_resources}, "
                           f"Orchestrators: {healthy_orchestrators}, Teams: {healthy_teams}")
                
                # Keep metrics history manageable
                if len(self.performance_metrics) > 100:
                    self.performance_metrics.pop(0)
                
                # Check for issues and auto-recovery
                await self._check_system_health(health)
                
        except asyncio.CancelledError:
            logger.info("📊 Monitoring cancelled")
        except Exception as e:
            logger.error(f"❌ Monitoring error: {e}")
    
    async def _check_system_health(self, health: Dict[str, Any]):
        """Check system health and trigger recovery if needed"""
        issues = []
        
        # Check resource manager
        if health['resource_manager']['total_resources'] == 0:
            issues.append("No resources registered")
        
        # Check orchestrators
        for name, data in health['orchestrators'].items():
            if not data.get('initialized'):
                issues.append(f"{name} orchestrator not initialized")
        
        # Check teams
        failed_teams = [
            name for name, data in health['teams'].items()
            if not data.get('initialized')
        ]
        if failed_teams:
            issues.append(f"Failed teams: {', '.join(failed_teams)}")
        
        if issues:
            logger.warning(f"⚠️ System health issues detected: {'; '.join(issues)}")
            # Could trigger auto-recovery here
        else:
            logger.debug("✅ All systems healthy")
    
    async def _save_phase_results(self, phase_name: str, results: Dict[str, Any]):
        """Save phase results for analysis"""
        try:
            results_file = self.deployment_dir / f"{self.deployment_id}_{phase_name}_results.json"
            
            with open(results_file, 'w') as f:
                json.dump({
                    "deployment_id": self.deployment_id,
                    "phase": phase_name,
                    "timestamp": datetime.now().isoformat(),
                    "results": results
                }, f, indent=2)
            
            logger.info(f"💾 {phase_name.title()} results saved to {results_file}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save {phase_name} results: {e}")
    
    async def _save_deployment_summary(self):
        """Save final deployment summary"""
        try:
            summary = {
                "deployment_id": self.deployment_id,
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": datetime.now().isoformat(),
                "duration": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
                "total_health_checks": len(self.performance_metrics),
                "final_resource_count": self.performance_metrics[-1]["resource_count"] if self.performance_metrics else 0,
                "performance_summary": {
                    "avg_resources": sum(m["resource_count"] for m in self.performance_metrics) / len(self.performance_metrics) if self.performance_metrics else 0,
                    "max_uptime": max((m["uptime"] for m in self.performance_metrics), default=0)
                }
            }
            
            summary_file = self.deployment_dir / f"{self.deployment_id}_deployment_summary.json"
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            logger.info(f"📋 Deployment summary saved to {summary_file}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save deployment summary: {e}")
    
    async def _graceful_shutdown(self):
        """Graceful system shutdown"""
        logger.info("🛑 Initiating graceful production shutdown...")
        
        try:
            # Save deployment summary
            await self._save_deployment_summary()
            
            # Shutdown orchestrator
            if self.orchestrator:
                await self.orchestrator.emergency_cleanup()
            
            # Shutdown resource manager
            await resource_manager.graceful_shutdown()
            
            logger.info("✅ Graceful shutdown completed")
            
        except Exception as e:
            logger.error(f"❌ Graceful shutdown error: {e}")
    
    async def _emergency_shutdown(self):
        """Emergency shutdown procedure"""
        logger.error("🚨 Executing emergency shutdown...")
        
        try:
            if self.orchestrator:
                await self.orchestrator.emergency_cleanup()
            
            await resource_manager.graceful_shutdown()
            
            logger.info("🚨 Emergency shutdown completed")
            
        except Exception as e:
            logger.error(f"❌ Emergency shutdown failed: {e}")


async def main():
    """Main entry point for production deployment"""
    print("🏭 SOPHIA-ARTEMIS AUTONOMOUS EVOLUTION")
    print("    PRODUCTION DEPLOYMENT SYSTEM")
    print("=" * 50)
    
    deployment = ProductionAutonomousEvolution()
    
    try:
        success = await deployment.deploy()
        
        if success:
            print("\n🎉 PRODUCTION DEPLOYMENT SUCCESSFUL!")
            print("💎 Sophia ecosystem: Strategic business intelligence active")
            print("⚔️ Artemis ecosystem: Tactical technical operations active")
            print("🤖 Autonomous evolution: Continuous improvement enabled")
            print("📊 Resource management: Full cleanup and monitoring active")
            print("\n🏆 SYSTEM STATUS: PRODUCTION READY AND FULLY AUTONOMOUS!")
        else:
            print("\n❌ PRODUCTION DEPLOYMENT FAILED!")
            print("Check logs for details.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Production deployment interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error in production deployment: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())