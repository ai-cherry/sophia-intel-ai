#!/usr/bin/env python3
"""
Deploy Research-Enhanced Audit Swarm
Premium deployment with multiple API providers and research capabilities
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

from app.swarms.audit.research_enhanced_orchestrator import ResearchEnhancedOrchestrator
from app.swarms.audit.premium_research_config import (
    PREMIUM_RESEARCH_AGENTS, RESEARCH_ENHANCED_FORMATIONS, API_CONFIGURATIONS,
    get_research_formation_config
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ResearchAuditDeployer:
    """Deployment manager for research-enhanced audit swarm"""
    
    def __init__(self, codebase_path: str = "/Users/lynnmusil/sophia-intel-ai"):
        self.codebase_path = Path(codebase_path)
        self.results_dir = self.codebase_path / "research_audit_results"
        self.results_dir.mkdir(exist_ok=True)
        
    def display_research_formations(self):
        """Display available research-enhanced audit formations"""
        print("\n" + "="*90)
        print("🔬 RESEARCH-ENHANCED AUDIT SWARM - PREMIUM FORMATION SELECTOR")
        print("="*90)
        
        print(f"\n📊 Research Agents: {len(PREMIUM_RESEARCH_AGENTS)} premium specialists")
        print(f"🔗 API Providers: {len(API_CONFIGURATIONS)} connected")
        print(f"🧠 Research Capabilities: Literature Review, Trend Analysis, Best Practices")
        
        print(f"\n🎯 RESEARCH FORMATIONS:")
        print("-" * 70)
        
        for i, (formation_name, config) in enumerate(RESEARCH_ENHANCED_FORMATIONS.items(), 1):
            agents_count = len(config["agents"])
            duration = config["expected_duration"]
            description = config["description"]
            research_depth = config.get("research_depth", "comprehensive")
            
            print(f"{i}. {formation_name.upper()}")
            print(f"   📋 {description}")
            print(f"   🤖 Agents: {agents_count} | ⏱️  Duration: {duration}")
            print(f"   🔬 Research Depth: {research_depth.title()}")
            print(f"   📚 Phases: {', '.join(config.get('research_phases', [])[:3])}...")
            print()
    
    async def execute_research_formation(self, formation: str) -> Dict[str, Any]:
        """Execute specific research-enhanced audit formation"""
        
        if formation not in RESEARCH_ENHANCED_FORMATIONS:
            raise ValueError(f"Unknown formation: {formation}")
            
        config = get_research_formation_config(formation)
        
        print(f"\n🔬 LAUNCHING {formation.upper()} RESEARCH FORMATION")
        print("=" * 80)
        print(f"📊 Research Agents: {len(config['agents'])}")
        print(f"⏱️  Expected Duration: {config['expected_duration']}")
        print(f"🔬 Research Depth: {config.get('research_depth', 'comprehensive').title()}")
        print(f"📚 Research Phases: {len(config.get('research_phases', []))}")
        print(f"🎯 Target: {self.codebase_path}")
        print("=" * 80)
        
        # Initialize orchestrator
        orchestrator = ResearchEnhancedOrchestrator(formation, str(self.codebase_path))
        
        # Execute research-enhanced audit
        start_time = time.time()
        try:
            result = await orchestrator.execute_research_enhanced_audit()
            execution_time = time.time() - start_time
            
            # Save results
            result_file = self.results_dir / f"research_audit_{formation}_{int(start_time)}.json"
            
            # Prepare result summary
            result_summary = {
                "formation": formation,
                "execution_time": execution_time,
                "timestamp": int(start_time),
                "codebase_path": str(self.codebase_path),
                "research_enhanced": True,
                "result": result
            }
            
            with open(result_file, 'w') as f:
                json.dump(result_summary, f, indent=2, default=str)
            
            # Display results
            self.display_research_results(result, execution_time, formation)
            
            print(f"\n💾 Results saved to: {result_file}")
            
            return result_summary
            
        except Exception as e:
            logger.error(f"Research audit execution failed: {e}")
            raise
    
    def display_research_results(self, result: Dict[str, Any], execution_time: float, formation: str):
        """Display comprehensive research audit results"""
        
        print(f"\n✅ {formation.upper()} RESEARCH AUDIT COMPLETED")
        print("=" * 100)
        print(f"⏱️  Execution Time: {execution_time/60:.1f} minutes")
        print(f"🔬 Research Findings: {result.get('research_findings_count', 'N/A')}")
        print(f"📚 Sources Reviewed: {result.get('research_metrics', {}).get('total_sources_reviewed', 'N/A')}")
        print(f"📖 Citations Generated: {result.get('research_metrics', {}).get('citations_generated', 'N/A')}")
        print(f"✅ Quality Validation: {result.get('research_quality_validation', {})}")
        
        # Research Quality Metrics
        if result.get('research_metrics'):
            metrics = result['research_metrics']
            print(f"\n🔬 RESEARCH QUALITY METRICS:")
            print("-" * 40)
            print(f"📊 Research Depth: {metrics.get('research_depth_achieved', 'N/A')}")
            print(f"🎯 Validation Rounds: {metrics.get('validation_rounds_completed', 'N/A')}")
            print(f"🤝 Cross-Validation Agreements: {metrics.get('cross_validation_agreements', 'N/A')}")
            print(f"📏 Methodology Rigor: {metrics.get('methodology_rigor_score', 'N/A')}")
        
        # Quality Gates
        if result.get('research_quality_validation'):
            print(f"\n🎯 RESEARCH QUALITY GATES:")
            print("-" * 50)
            gates = result['research_quality_validation']
            passed = sum(1 for v in gates.values() if v)
            total = len(gates)
            print(f"✅ Passed: {passed}/{total} quality gates")
            
            for gate, passed in gates.items():
                status = "✅" if passed else "❌"
                gate_name = gate.replace('_', ' ').title()
                print(f"   {status} {gate_name}")
        
        # Research Recommendations
        if result.get('recommendations'):
            print(f"\n🎯 RESEARCH-BASED RECOMMENDATIONS:")
            print("-" * 50)
            for i, rec in enumerate(result['recommendations'][:6], 1):
                print(f"{i:2d}. {rec}")
        
        # Executive Summary
        if result.get('executive_summary'):
            print(f"\n📋 EXECUTIVE SUMMARY:")
            print("-" * 50)
            print(f"   {result['executive_summary']}")
    
    async def run_interactive_research_mode(self):
        """Run interactive research audit selection"""
        
        while True:
            self.display_research_formations()
            
            try:
                choice = input("\n🔬 Select research formation (1-5) or 'q' to quit: ").strip()
                
                if choice.lower() == 'q':
                    print("👋 Goodbye!")
                    break
                
                formation_names = list(RESEARCH_ENHANCED_FORMATIONS.keys())
                formation_idx = int(choice) - 1
                
                if 0 <= formation_idx < len(formation_names):
                    formation = formation_names[formation_idx]
                    
                    confirm = input(f"\n🔬 Execute {formation.upper()} research audit? (y/N): ").strip()
                    if confirm.lower() == 'y':
                        print(f"\n⚡ Starting {formation} research audit...")
                        await self.execute_research_formation(formation)
                        
                        another = input(f"\n🔄 Run another research audit? (y/N): ").strip()
                        if another.lower() != 'y':
                            break
                else:
                    print("❌ Invalid selection. Please try again.")
                    
            except (ValueError, KeyboardInterrupt):
                print("\n👋 Exiting...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    async def test_research_connections(self):
        """Test all research API connections"""
        
        print("🔬 TESTING RESEARCH API CONNECTIONS")
        print("=" * 50)
        
        import requests
        
        # Test key research APIs
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
        
        # Test HuggingFace (research models)
        try:
            headers = {'Authorization': f"Bearer {API_CONFIGURATIONS['huggingface']['api_key']}"}
            response = requests.get('https://huggingface.co/api/models', headers=headers, timeout=10)
            test_results['huggingface'] = response.status_code == 200
            print(f"✅ HuggingFace: {'Connected' if test_results['huggingface'] else 'Failed'}")
        except:
            test_results['huggingface'] = False
            print("❌ HuggingFace: Failed")
        
        # Test DeepSeek (code analysis)
        try:
            headers = {'Authorization': f"Bearer {API_CONFIGURATIONS['deepseek']['api_key']}"}
            response = requests.get('https://api.deepseek.com/models', headers=headers, timeout=10)
            test_results['deepseek'] = response.status_code == 200
            print(f"✅ DeepSeek: {'Connected' if test_results['deepseek'] else 'Failed'}")
        except:
            test_results['deepseek'] = False
            print("❌ DeepSeek: Failed")
        
        # Test Groq (fast analysis)
        try:
            headers = {'Authorization': f"Bearer {API_CONFIGURATIONS['groq']['api_key']}"}
            response = requests.get('https://api.groq.com/openai/v1/models', headers=headers, timeout=10)
            test_results['groq'] = response.status_code == 200
            print(f"✅ Groq: {'Connected' if test_results['groq'] else 'Failed'}")
        except:
            test_results['groq'] = False
            print("❌ Groq: Failed")
        
        total_connected = sum(test_results.values())
        total_apis = len(test_results)
        
        print(f"\n🔗 API Connection Status: {total_connected}/{total_apis} connected")
        
        if total_connected >= 2:
            print("✅ Sufficient API connectivity for research operations")
            return True
        else:
            print("❌ Insufficient API connectivity - check credentials")
            return False

async def main():
    """Main deployment function for research-enhanced audit"""
    
    print("🔬 RESEARCH-ENHANCED AUDIT SWARM DEPLOYMENT")
    print("="*70)
    
    # Check if codebase path provided
    if len(sys.argv) > 1:
        codebase_path = sys.argv[1]
    else:
        codebase_path = "/Users/lynnmusil/sophia-intel-ai"
    
    # Check if formation specified
    if len(sys.argv) > 2:
        formation = sys.argv[2]
        if formation not in RESEARCH_ENHANCED_FORMATIONS:
            print(f"❌ Unknown formation: {formation}")
            print(f"Available: {', '.join(RESEARCH_ENHANCED_FORMATIONS.keys())}")
            return
    else:
        formation = None
    
    deployer = ResearchAuditDeployer(codebase_path)
    
    # Test connections first
    connections_ok = await deployer.test_research_connections()
    if not connections_ok:
        proceed = input("\n⚠️  Some API connections failed. Continue anyway? (y/N): ").strip()
        if proceed.lower() != 'y':
            print("Deployment cancelled")
            return
    
    if formation:
        # Direct execution
        print(f"🎯 Direct execution mode: {formation}")
        await deployer.execute_research_formation(formation)
    else:
        # Interactive mode
        print("🎮 Interactive research mode")
        await deployer.run_interactive_research_mode()

def run_research_audit_demo():
    """Demo function for quick research testing"""
    
    print("🔬 RESEARCH-ENHANCED AUDIT SWARM - DEMO MODE")
    print("="*60)
    
    async def demo():
        deployer = ResearchAuditDeployer()
        
        print("🚀 Running RAPID RESEARCH AUDIT formation for demo...")
        result = await deployer.execute_research_formation("rapid_research_audit")
        
        print(f"\n🎉 Research demo completed successfully!")
        print(f"📊 Demo took {result['execution_time']/60:.1f} minutes")
        print(f"🔬 Research findings: {result['result'].get('research_findings_count', 0)}")
        
        return result
    
    return asyncio.run(demo())

if __name__ == "__main__":
    # Command line usage:
    # python deploy_research_audit.py                                    # Interactive mode
    # python deploy_research_audit.py /path/to/codebase                  # Interactive with custom path  
    # python deploy_research_audit.py /path/to/codebase full_research_spectrum  # Direct execution
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Research audit deployment interrupted")
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        sys.exit(1)