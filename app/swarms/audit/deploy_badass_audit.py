#!/usr/bin/env python3
"""
Deploy and Execute Badass Audit Swarm
Complete deployment script with formation selection and execution monitoring
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

from app.swarms.audit.comprehensive_audit_swarm import ComprehensiveAuditSwarm
from app.swarms.audit.audit_execution_plan import BadassAuditOrchestrator
from app.swarms.audit.badass_audit_config import (
    AUDIT_FORMATIONS, BADASS_AGENTS, get_formation_config, get_model_distribution
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AuditSwarmDeployer:
    """Deployment manager for badass audit swarm"""
    
    def __init__(self, codebase_path: str = "/Users/lynnmusil/sophia-intel-ai"):
        self.codebase_path = Path(codebase_path)
        self.results_dir = self.codebase_path / "audit_results"
        self.results_dir.mkdir(exist_ok=True)
        
    def display_formation_options(self):
        """Display available audit formations"""
        print("\n" + "="*80)
        print("🚀 BADASS AUDIT SWARM - FORMATION SELECTOR")
        print("="*80)
        
        print(f"\n📊 Available Models: {sum(get_model_distribution().values())} premium models")
        print(f"🤖 Total Specialized Agents: {len(BADASS_AGENTS)}")
        
        print(f"\n🎯 AVAILABLE FORMATIONS:")
        print("-" * 50)
        
        for i, (formation_name, config) in enumerate(AUDIT_FORMATIONS.items(), 1):
            agents_count = len(config["agents"])
            duration = config["expected_duration"]
            description = config["description"]
            
            print(f"{i}. {formation_name.upper()}")
            print(f"   📋 {description}")
            print(f"   🤖 Agents: {agents_count} | ⏱️  Duration: {duration}")
            print(f"   🔧 Phases: {', '.join(config['phases'])}")
            print()
    
    async def execute_formation(self, formation: str) -> Dict[str, Any]:
        """Execute specific audit formation"""
        
        if formation not in AUDIT_FORMATIONS:
            raise ValueError(f"Unknown formation: {formation}")
            
        config = get_formation_config(formation)
        
        print(f"\n🚀 LAUNCHING {formation.upper()} FORMATION")
        print("=" * 60)
        print(f"📊 Agents: {len(config['agents'])}")
        print(f"⏱️  Expected Duration: {config['expected_duration']}")
        print(f"🎯 Target: {self.codebase_path}")
        print("=" * 60)
        
        # Initialize orchestrator
        orchestrator = BadassAuditOrchestrator(formation, str(self.codebase_path))
        
        # Execute audit
        start_time = time.time()
        try:
            result = await orchestrator.execute_badass_audit()
            execution_time = time.time() - start_time
            
            # Save results
            result_file = self.results_dir / f"audit_{formation}_{int(start_time)}.json"
            
            # Prepare result summary
            result_summary = {
                "formation": formation,
                "execution_time": execution_time,
                "timestamp": int(start_time),
                "codebase_path": str(self.codebase_path),
                "result": result
            }
            
            with open(result_file, 'w') as f:
                json.dump(result_summary, f, indent=2, default=str)
            
            # Display results
            self.display_results(result, execution_time, formation)
            
            print(f"\n💾 Results saved to: {result_file}")
            
            return result_summary
            
        except Exception as e:
            logger.error(f"Audit execution failed: {e}")
            raise
    
    def display_results(self, result: Dict[str, Any], execution_time: float, formation: str):
        """Display comprehensive audit results"""
        
        print(f"\n✅ {formation.upper()} AUDIT COMPLETED")
        print("=" * 80)
        print(f"⏱️  Execution Time: {execution_time/60:.1f} minutes")
        print(f"🤖 Agents Used: {result.get('agents_used', 'N/A')}")
        print(f"📋 Tasks Completed: {result.get('tasks_completed', 'N/A')}")
        print(f"⚔️  Debates Conducted: {result.get('debates_conducted', 0)}")
        print(f"🤝 Consensus Sessions: {result.get('consensus_sessions', 0)}")
        print(f"🔍 Total Findings: {result.get('total_findings', 0)}")
        print(f"⚠️  Critical Findings: {result.get('critical_findings', 0)}")
        print(f"📊 Overall Score: {result.get('overall_score', 'N/A')}")
        print(f"🚀 Deployment Status: {result.get('deployment_readiness', 'N/A')}")
        
        # Quality Gates
        if result.get('quality_gates_passed'):
            print(f"\n🎯 QUALITY GATES:")
            print("-" * 30)
            gates = result['quality_gates_passed']
            passed = sum(1 for v in gates.values() if v)
            total = len(gates)
            print(f"✅ Passed: {passed}/{total} quality gates")
            
            for gate, passed in gates.items():
                status = "✅" if passed else "❌"
                print(f"   {status} {gate.replace('_', ' ').title()}")
        
        # Recommendations
        if result.get('recommendations'):
            print(f"\n🎯 TOP RECOMMENDATIONS:")
            print("-" * 40)
            for i, rec in enumerate(result['recommendations'][:8], 1):
                print(f"{i:2d}. {rec}")
        
        # Executive Summary
        if result.get('executive_summary'):
            print(f"\n📋 EXECUTIVE SUMMARY:")
            print("-" * 40)
            print(f"   {result['executive_summary']}")
    
    async def run_interactive_mode(self):
        """Run interactive audit selection"""
        
        while True:
            self.display_formation_options()
            
            try:
                choice = input("\n🎯 Select formation (1-5) or 'q' to quit: ").strip()
                
                if choice.lower() == 'q':
                    print("👋 Goodbye!")
                    break
                
                formation_names = list(AUDIT_FORMATIONS.keys())
                formation_idx = int(choice) - 1
                
                if 0 <= formation_idx < len(formation_names):
                    formation = formation_names[formation_idx]
                    
                    confirm = input(f"\n🚀 Execute {formation.upper()} audit? (y/N): ").strip()
                    if confirm.lower() == 'y':
                        print(f"\n⚡ Starting {formation} audit...")
                        await self.execute_formation(formation)
                        
                        another = input(f"\n🔄 Run another audit? (y/N): ").strip()
                        if another.lower() != 'y':
                            break
                else:
                    print("❌ Invalid selection. Please try again.")
                    
            except (ValueError, KeyboardInterrupt):
                print("\n👋 Exiting...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

async def main():
    """Main deployment function"""
    
    print("🔥 BADASS AUDIT SWARM DEPLOYMENT SYSTEM")
    print("="*60)
    
    # Check if codebase path provided
    if len(sys.argv) > 1:
        codebase_path = sys.argv[1]
    else:
        codebase_path = "/Users/lynnmusil/sophia-intel-ai"
    
    # Check if formation specified
    if len(sys.argv) > 2:
        formation = sys.argv[2]
        if formation not in AUDIT_FORMATIONS:
            print(f"❌ Unknown formation: {formation}")
            print(f"Available: {', '.join(AUDIT_FORMATIONS.keys())}")
            return
    else:
        formation = None
    
    deployer = AuditSwarmDeployer(codebase_path)
    
    if formation:
        # Direct execution
        print(f"🎯 Direct execution mode: {formation}")
        await deployer.execute_formation(formation)
    else:
        # Interactive mode
        print("🎮 Interactive mode")
        await deployer.run_interactive_mode()

def run_badass_audit_demo():
    """Demo function for quick testing"""
    
    print("🔥 BADASS AUDIT SWARM - DEMO MODE")
    print("="*50)
    
    async def demo():
        deployer = AuditSwarmDeployer()
        
        print("🚀 Running RAPID ASSESSMENT formation for demo...")
        result = await deployer.execute_formation("rapid_assessment")
        
        print(f"\n🎉 Demo completed successfully!")
        print(f"📊 Demo took {result['execution_time']/60:.1f} minutes")
        
        return result
    
    return asyncio.run(demo())

if __name__ == "__main__":
    # Command line usage:
    # python deploy_badass_audit.py                           # Interactive mode
    # python deploy_badass_audit.py /path/to/codebase         # Interactive with custom path  
    # python deploy_badass_audit.py /path/to/codebase full_spectrum  # Direct execution
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Audit deployment interrupted")
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        sys.exit(1)