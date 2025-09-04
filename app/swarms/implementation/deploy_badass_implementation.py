#!/usr/bin/env python3
"""
🔥 BADASS IMPLEMENTATION SWARM DEPLOYER
=====================================
Deploy ultra-sophisticated implementation swarm to CRUSH complex challenges
Using premium OpenRouter models with advanced collaboration patterns
"""

import asyncio
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add app to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.swarms.implementation.badass_implementation_swarm import (
    BadassImplementationSwarm, 
    ImplementationPhase,
    ImplementationReport
)
from app.swarms.implementation.badass_implementation_config import (
    IMPLEMENTATION_FORMATIONS,
    BADASS_IMPLEMENTATION_AGENTS
)

class ImplementationSwarmDeployer:
    """
    🚀 Deploy badass implementation swarm with premium AI agents
    
    Features:
    - Interactive formation selection
    - Real-time progress tracking
    - Results visualization
    - JSON export for analysis
    """
    
    def __init__(self):
        self.results_dir = Path(__file__).parent / "results"
        self.results_dir.mkdir(exist_ok=True)
        
    async def deploy_interactive(self) -> ImplementationReport:
        """Interactive deployment with formation selection"""
        
        print("🔥 BADASS IMPLEMENTATION SWARM DEPLOYMENT")
        print("=" * 50)
        print()
        
        # Show available formations
        print("📋 Available Implementation Formations:")
        print()
        
        formations = list(IMPLEMENTATION_FORMATIONS.keys())
        for i, formation_key in enumerate(formations, 1):
            formation = IMPLEMENTATION_FORMATIONS[formation_key]
            print(f"{i}. {formation['name']}")
            print(f"   Duration: {formation['duration_estimate']}")
            print(f"   Use Case: {formation['use_case']}")
            print()
            
        # Get user selection
        while True:
            try:
                choice = input(f"Select formation (1-{len(formations)}): ")
                formation_index = int(choice) - 1
                if 0 <= formation_index < len(formations):
                    selected_formation = formations[formation_index]
                    break
                else:
                    print("❌ Invalid selection. Please try again.")
            except (ValueError, KeyboardInterrupt):
                print("❌ Invalid input. Please try again.")
                
        print(f"✅ Selected: {IMPLEMENTATION_FORMATIONS[selected_formation]['name']}")
        print()
        
        # Get problem description
        print("🎯 Problem Description:")
        problem = input("Describe the implementation challenge: ")
        print()
        
        # Get target files
        print("📁 Target Files (optional, comma-separated):")
        files_input = input("Target files: ").strip()
        target_files = [f.strip() for f in files_input.split(",")] if files_input else []
        
        print()
        print("🚀 Deploying Implementation Swarm...")
        print("-" * 40)
        
        # Deploy swarm
        return await self.deploy_swarm(selected_formation, problem, target_files)
        
    async def deploy_swarm(self, formation: str, problem: str, 
                         target_files: list = None) -> ImplementationReport:
        """Deploy implementation swarm with specified parameters"""
        
        start_time = time.time()
        
        # Initialize swarm
        swarm = BadassImplementationSwarm(formation=formation, memory_enabled=True)
        
        print(f"🤖 Initializing {formation} formation...")
        formation_config = IMPLEMENTATION_FORMATIONS[formation]
        
        # Show agent lineup
        print(f"👥 Agent Lineup:")
        all_agents = set()
        for role_agents in formation_config.values():
            if isinstance(role_agents, list):
                all_agents.update(role_agents)
                
        for agent in sorted(all_agents):
            if agent in BADASS_IMPLEMENTATION_AGENTS:
                agent_config = BADASS_IMPLEMENTATION_AGENTS[agent]
                model = agent_config.get("model", "unknown")
                role = agent_config.get("role", "Unknown")
                print(f"   • {agent}: {role} ({model})")
                
        print()
        
        # Execute implementation
        try:
            print("⚡ Starting implementation execution...")
            report = await swarm.execute_implementation(
                problem_description=problem,
                target_files=target_files or []
            )
            
            execution_time = time.time() - start_time
            
            # Display results
            print()
            print("🎉 IMPLEMENTATION COMPLETE!")
            print("=" * 40)
            print(f"⏱️  Total Time: {execution_time/60:.1f} minutes")
            print(f"📊 Overall Confidence: {report.overall_confidence:.1%}")
            print(f"🎯 Implementation Score: {report.implementation_score:.1f}/10")
            print(f"🚀 Deployment Ready: {'✅ YES' if report.deployment_ready else '❌ NO'}")
            print()
            
            # Show key results
            if report.tasks_completed:
                print("✅ Tasks Completed:")
                for task in report.tasks_completed:
                    status_icon = "✅" if task.status == "completed" else "⚠️"
                    print(f"   {status_icon} {task.task_id} ({task.confidence:.1%} confidence)")
                print()
                
            if report.code_files_modified:
                print("📝 Files Modified:")
                for file in report.code_files_modified:
                    print(f"   • {file}")
                print()
                
            if report.next_steps:
                print("🚀 Next Steps:")
                for step in report.next_steps:
                    print(f"   • {step}")
                print()
                
            # Save results
            result_file = self.results_dir / f"implementation_{int(time.time())}.json"
            with open(result_file, 'w') as f:
                # Convert report to dict for JSON serialization
                report_dict = {
                    "swarm_id": report.swarm_id,
                    "timestamp": report.timestamp.isoformat(),
                    "formation_type": report.formation_type,
                    "total_execution_time": report.total_execution_time,
                    "problem_summary": report.problem_summary,
                    "overall_confidence": report.overall_confidence,
                    "implementation_score": report.implementation_score,
                    "deployment_ready": report.deployment_ready,
                    "code_files_modified": report.code_files_modified,
                    "next_steps": report.next_steps,
                    "task_summaries": [
                        {
                            "task_id": task.task_id,
                            "status": task.status,
                            "confidence": task.confidence,
                            "execution_time": task.execution_time
                        } for task in report.tasks_completed
                    ]
                }
                json.dump(report_dict, f, indent=2)
                
            print(f"💾 Results saved to: {result_file}")
            
            return report
            
        except Exception as e:
            print(f"❌ Implementation failed: {str(e)}")
            raise
            
    async def deploy_direct(self, formation: str, problem: str, 
                          target_files: str = "") -> ImplementationReport:
        """Direct deployment for programmatic use"""
        
        file_list = [f.strip() for f in target_files.split(",")] if target_files else []
        return await self.deploy_swarm(formation, problem, file_list)

async def main():
    """Main deployment interface"""
    
    deployer = ImplementationSwarmDeployer()
    
    if len(sys.argv) > 1:
        # Direct execution mode
        if len(sys.argv) < 3:
            print("Usage: python deploy_badass_implementation.py <formation> <problem> [target_files]")
            print()
            print("Available formations:")
            for key, config in IMPLEMENTATION_FORMATIONS.items():
                print(f"  • {key}: {config['name']}")
            sys.exit(1)
            
        formation = sys.argv[1]
        problem = sys.argv[2]
        target_files = sys.argv[3] if len(sys.argv) > 3 else ""
        
        if formation not in IMPLEMENTATION_FORMATIONS:
            print(f"❌ Unknown formation: {formation}")
            print("Available formations:", list(IMPLEMENTATION_FORMATIONS.keys()))
            sys.exit(1)
            
        await deployer.deploy_direct(formation, problem, target_files)
        
    else:
        # Interactive mode
        await deployer.deploy_interactive()

if __name__ == "__main__":
    print("🔥 BADASS IMPLEMENTATION SWARM DEPLOYER")
    print("Ready to CRUSH complex implementation challenges!")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚡ Deployment interrupted by user")
    except Exception as e:
        print(f"💥 Deployment error: {str(e)}")
        sys.exit(1)