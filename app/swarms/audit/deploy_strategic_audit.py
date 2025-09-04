#!/usr/bin/env python3
"""
Deploy Strategic Planning Enhanced Audit Swarm
Advanced deployment with OODA loop methodology and strategic planning integration
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

from app.swarms.audit.audit_execution_plan import BadassAuditOrchestrator
from app.swarms.audit.badass_audit_config import (
    BADASS_AGENTS, AUDIT_FORMATIONS, get_formation_config
)
from app.swarms.audit.premium_research_config import API_CONFIGURATIONS

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StrategicAuditDeployer:
    """Deployment manager for strategic planning enhanced audit swarm"""
    
    def __init__(self, codebase_path: str = "/Users/lynnmusil/sophia-intel-ai"):
        self.codebase_path = Path(codebase_path)
        self.results_dir = self.codebase_path / "strategic_audit_results"
        self.results_dir.mkdir(exist_ok=True)
        
    def display_strategic_formations(self):
        """Display available strategic planning enhanced audit formations"""
        print("\n" + "="*90)
        print("🎯 STRATEGIC PLANNING ENHANCED AUDIT SWARM - FORMATION SELECTOR")
        print("="*90)
        
        print(f"\n📊 Total Agents: {len(BADASS_AGENTS)} premium specialists")
        print(f"🔗 API Providers: {len(API_CONFIGURATIONS)} connected")
        print(f"🧠 Strategic Capabilities: OODA Loop, Predictive Modeling, Scenario Forecasting")
        
        print(f"\n🎯 STRATEGIC AUDIT FORMATIONS:")
        print("-" * 70)
        
        # Show strategic formations first
        strategic_formations = {
            k: v for k, v in AUDIT_FORMATIONS.items() 
            if v.get("strategic_planning", False) or "strategic" in k
        }
        
        # Show all available formations
        all_formations = dict(strategic_formations, **{
            k: v for k, v in AUDIT_FORMATIONS.items() 
            if k not in strategic_formations
        })
        
        for i, (formation_name, config) in enumerate(all_formations.items(), 1):
            agents_count = len(config["agents"])
            duration = config["expected_duration"]
            description = config["description"]
            
            # Mark strategic formations
            strategic_marker = "🎯 STRATEGIC" if config.get("strategic_planning", False) else "🔍 STANDARD"
            ooda_marker = " + OODA LOOP" if config.get("ooda_enabled", False) else ""
            
            print(f"{i}. {formation_name.upper()}")
            print(f"   {strategic_marker}{ooda_marker}")
            print(f"   📋 {description}")
            print(f"   🤖 Agents: {agents_count} | ⏱️  Duration: {duration}")
            print(f"   📚 Phases: {', '.join(config.get('phases', [])[:3])}...")
            print()
    
    async def execute_strategic_formation(self, formation: str) -> Dict[str, Any]:
        """Execute strategic planning enhanced audit formation"""
        
        if formation not in AUDIT_FORMATIONS:
            raise ValueError(f"Unknown formation: {formation}")
            
        config = get_formation_config(formation)
        
        print(f"\n🎯 LAUNCHING {formation.upper()} STRATEGIC AUDIT")
        print("=" * 80)
        print(f"📊 Agents: {len(config['agents'])}")
        print(f"⏱️  Duration: {config['expected_duration']}")
        print(f"🧠 Strategic Planning: {'Enabled' if config.get('strategic_planning') else 'Standard'}")
        print(f"🔄 OODA Loop: {'Enabled' if config.get('ooda_enabled') else 'Disabled'}")
        print(f"📚 Phases: {len(config.get('phases', []))}")
        print(f"🎯 Target: {self.codebase_path}")
        print("=" * 80)
        
        # Initialize orchestrator with strategic planning enabled
        enable_strategic = config.get("strategic_planning", False)
        orchestrator = BadassAuditOrchestrator(
            formation=formation,
            codebase_path=str(self.codebase_path),
            enable_strategic_planning=enable_strategic
        )
        
        # Execute strategic audit
        start_time = time.time()
        try:
            result = await orchestrator.execute_badass_audit()
            execution_time = time.time() - start_time
            
            # Save results
            result_file = self.results_dir / f"strategic_audit_{formation}_{int(start_time)}.json"
            
            # Prepare result summary
            result_summary = {
                "formation": formation,
                "execution_time": execution_time,
                "timestamp": int(start_time),
                "codebase_path": str(self.codebase_path),
                "strategic_planning_enabled": enable_strategic,
                "ooda_enabled": config.get("ooda_enabled", False),
                "result": result
            }
            
            with open(result_file, 'w') as f:
                json.dump(result_summary, f, indent=2, default=str)
            
            # Display results
            self.display_strategic_results(result, execution_time, formation)
            
            print(f"\n💾 Results saved to: {result_file}")
            
            return result_summary
            
        except Exception as e:
            logger.error(f"Strategic audit execution failed: {e}")
            raise
    
    def display_strategic_results(self, result: Dict[str, Any], execution_time: float, formation: str):
        """Display comprehensive strategic audit results"""
        
        print(f"\n✅ {formation.upper()} STRATEGIC AUDIT COMPLETED")
        print("=" * 100)
        print(f"⏱️  Execution Time: {execution_time/60:.1f} minutes")
        print(f"🎯 Strategic Planning: {'Enabled' if result.get('strategic_planning_enabled') else 'Standard'}")
        print(f"🤖 Agents Used: {result.get('agents_used', 'N/A')}")
        print(f"✅ Tasks Completed: {result.get('tasks_completed', 'N/A')}")
        print(f"⚔️  Debates Conducted: {result.get('debates_conducted', 0)}")
        print(f"🤝 Consensus Sessions: {result.get('consensus_sessions', 0)}")
        print(f"🔍 Total Findings: {result.get('total_findings', 'N/A')}")
        
        # Strategic Insights
        if result.get('strategic_insights'):
            insights = result['strategic_insights']
            print(f"\n🎯 STRATEGIC INSIGHTS:")
            print("-" * 40)
            print(f"💡 Insights Generated: {insights.get('insights_count', 0)}")
            print(f"🔮 Scenarios Analyzed: {insights.get('scenarios_analyzed', 0)}")
            print(f"📈 Strategic Recommendations: {insights.get('strategic_recommendations', 0)}")
            
            # Show OODA phases if available
            if insights.get('ooda_phases_completed'):
                print(f"🔄 OODA Phases: {', '.join(insights['ooda_phases_completed'])}")
        
        # Quality Assessment
        if result.get('deployment_readiness'):
            print(f"\n🚀 DEPLOYMENT ASSESSMENT:")
            print("-" * 50)
            print(f"📊 Overall Score: {result.get('overall_score', 'N/A')}")
            print(f"🎯 Deployment Status: {result['deployment_readiness']}")
            
            # Critical findings
            critical_count = result.get('critical_findings', 0)
            if critical_count > 0:
                print(f"⚠️  Critical Issues: {critical_count}")
            else:
                print(f"✅ No Critical Issues Found")
        
        # Strategic Recommendations
        if result.get('recommendations'):
            print(f"\n🎯 STRATEGIC RECOMMENDATIONS:")
            print("-" * 50)
            for i, rec in enumerate(result['recommendations'][:8], 1):
                print(f"{i:2d}. {rec}")
        
        # Executive Summary
        if result.get('executive_summary'):
            print(f"\n📋 EXECUTIVE SUMMARY:")
            print("-" * 50)
            print(f"   {result['executive_summary']}")
    
    async def run_interactive_strategic_mode(self):
        """Run interactive strategic audit selection"""
        
        while True:
            self.display_strategic_formations()
            
            try:
                choice = input("\n🎯 Select strategic formation (1-6) or 'q' to quit: ").strip()
                
                if choice.lower() == 'q':
                    print("👋 Goodbye!")
                    break
                
                formation_names = list(AUDIT_FORMATIONS.keys())
                formation_idx = int(choice) - 1
                
                if 0 <= formation_idx < len(formation_names):
                    formation = formation_names[formation_idx]
                    
                    # Show formation details
                    config = get_formation_config(formation)
                    strategic_enabled = config.get("strategic_planning", False)
                    
                    print(f"\n📋 Formation: {formation.upper()}")
                    print(f"🎯 Strategic Planning: {'Enabled' if strategic_enabled else 'Standard Audit'}")
                    print(f"⏱️  Duration: {config['expected_duration']}")
                    
                    confirm = input(f"\n🚀 Execute {formation.upper()} audit? (y/N): ").strip()
                    if confirm.lower() == 'y':
                        print(f"\n⚡ Starting {formation} strategic audit...")
                        await self.execute_strategic_formation(formation)
                        
                        another = input(f"\n🔄 Run another strategic audit? (y/N): ").strip()
                        if another.lower() != 'y':
                            break
                else:
                    print("❌ Invalid selection. Please try again.")
                    
            except (ValueError, KeyboardInterrupt):
                print("\n👋 Exiting...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    async def test_strategic_connections(self):
        """Test strategic audit system connections"""
        
        print("🎯 TESTING STRATEGIC AUDIT SYSTEM")
        print("=" * 50)
        
        import requests
        
        # Test key APIs
        test_results = {}
        
        # Test OpenRouter (primary)
        try:
            headers = {'Authorization': f"Bearer {API_CONFIGURATIONS['openrouter']['api_key']}"}
            response = requests.get('https://openrouter.ai/api/v1/models', headers=headers, timeout=10)
            test_results['openrouter'] = response.status_code == 200
            print(f"✅ OpenRouter: {'Connected' if test_results['openrouter'] else 'Failed'}")
        except:
            test_results['openrouter'] = False
            print("❌ OpenRouter: Failed")
        
        # Test strategic planning components
        try:
            from app.swarms.audit.strategic_planning_enhancement import StrategicPlanningEngine
            orchestrator = StrategicPlanningEngine("test", ".")
            test_results['strategic_planner'] = True
            print("✅ Strategic Planner: Initialized")
        except Exception as e:
            test_results['strategic_planner'] = False
            print(f"❌ Strategic Planner: Failed - {e}")
        
        # Test audit orchestrator
        try:
            orchestrator = BadassAuditOrchestrator("full_spectrum", ".", True)
            test_results['audit_orchestrator'] = True
            print("✅ Audit Orchestrator: Initialized")
        except Exception as e:
            test_results['audit_orchestrator'] = False
            print(f"❌ Audit Orchestrator: Failed - {e}")
        
        total_connected = sum(test_results.values())
        total_systems = len(test_results)
        
        print(f"\n🔗 System Status: {total_connected}/{total_systems} systems ready")
        
        if total_connected >= 2:
            print("✅ Strategic audit system ready for deployment")
            return True
        else:
            print("❌ System not ready - check configurations")
            return False

async def main():
    """Main deployment function for strategic audit"""
    
    print("🎯 STRATEGIC PLANNING ENHANCED AUDIT DEPLOYMENT")
    print("="*70)
    
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
    
    deployer = StrategicAuditDeployer(codebase_path)
    
    # Test systems first
    systems_ok = await deployer.test_strategic_connections()
    if not systems_ok:
        proceed = input("\n⚠️  Some systems failed checks. Continue anyway? (y/N): ").strip()
        if proceed.lower() != 'y':
            print("Deployment cancelled")
            return
    
    if formation:
        # Direct execution
        print(f"🎯 Direct execution mode: {formation}")
        await deployer.execute_strategic_formation(formation)
    else:
        # Interactive mode
        print("🎮 Interactive strategic mode")
        await deployer.run_interactive_strategic_mode()

def run_strategic_audit_demo():
    """Demo function for strategic audit testing"""
    
    print("🎯 STRATEGIC AUDIT SWARM - DEMO MODE")
    print("="*60)
    
    async def demo():
        deployer = StrategicAuditDeployer()
        
        print("🚀 Running STRATEGIC PLANNING ENHANCED audit for demo...")
        result = await deployer.execute_strategic_formation("strategic_planning_enhanced")
        
        print(f"\n🎉 Strategic audit demo completed!")
        print(f"📊 Demo took {result['execution_time']/60:.1f} minutes")
        print(f"🎯 Strategic insights: {result['result'].get('strategic_insights', {}).get('insights_count', 0)}")
        
        return result
    
    return asyncio.run(demo())

if __name__ == "__main__":
    # Command line usage:
    # python deploy_strategic_audit.py                                    # Interactive mode
    # python deploy_strategic_audit.py /path/to/codebase                  # Interactive with custom path  
    # python deploy_strategic_audit.py /path/to/codebase strategic_planning_enhanced  # Direct execution
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Strategic audit deployment interrupted")
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        sys.exit(1)