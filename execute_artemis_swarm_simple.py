#!/usr/bin/env python3
"""
Artemis Swarm Execution - Direct Factory Usage
Uses the Artemis unified factory directly to execute comprehensive audit
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, "/Users/lynnmusil/sophia-intel-ai")

from app.artemis.unified_factory import artemis_unified_factory

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ArtemisDirectExecutor:
    """Direct execution using Artemis factory"""

    def __init__(self):
        self.factory = artemis_unified_factory
        self.results = {}
        self.start_time = datetime.now()

    async def execute_audit_mission(self):
        """Execute comprehensive audit using military units"""
        logger.info("🚀 ARTEMIS FACTORY - DIRECT MISSION EXECUTION")
        logger.info("=" * 60)

        try:
            # Execute Operation Clean Sweep mission
            logger.info("\n🎯 Launching Operation Clean Sweep")

            mission_result = await self.factory.execute_mission(
                mission_type="operation_clean_sweep",
                target="/Users/lynnmusil/sophia-intel-ai",
                parameters={
                    "scan_depth": "comprehensive",
                    "include_patterns": [
                        "app/**/*.py",
                        "agent_ui/**/*.tsx",
                        "agent_catalog/**/*.json",
                    ],
                    "analysis_focus": [
                        "duplicate_detection",
                        "architecture_patterns",
                        "integration_gaps",
                        "swarm_configurations",
                    ],
                    "enhancement_targets": [
                        "llm_routing",
                        "memory_architecture",
                        "ui_consolidation",
                        "micro_swarm_design",
                    ],
                },
            )

            self.results["clean_sweep"] = mission_result

            # Create specialized swarms for different domains
            logger.info("\n🔧 Creating Domain-Specific Swarms")

            # Marketing Swarm
            marketing_swarm = await self.factory.create_specialized_swarm(
                swarm_type="domain_team",
                swarm_config={
                    "domain": "marketing",
                    "capabilities": [
                        "paid_ads_management",
                        "brand_design",
                        "proposal_generation",
                        "market_intelligence",
                    ],
                    "integrations": ["google_ads", "linkedin", "hubspot"],
                    "reporting_to": "sophia",
                },
            )
            self.results["marketing_swarm"] = marketing_swarm

            # Sales Swarm
            sales_swarm = await self.factory.create_specialized_swarm(
                swarm_type="domain_team",
                swarm_config={
                    "domain": "sales",
                    "capabilities": [
                        "persona_building",
                        "outreach_planning",
                        "creative_messaging",
                        "follow_up_scheduling",
                    ],
                    "integrations": ["gong", "salesforce", "twilio"],
                    "reporting_to": "sophia",
                },
            )
            self.results["sales_swarm"] = sales_swarm

            # Technical Refactoring Swarm
            refactor_swarm = await self.factory.create_specialized_swarm(
                swarm_type="refactoring_swarm",
                swarm_config={
                    "targets": ["unified_server.py", "agent_factories", "dashboard_components"],
                    "quality_gates": True,
                    "test_coverage_target": 85.0,
                },
            )
            self.results["refactor_swarm"] = refactor_swarm

            # Create technical teams
            logger.info("\n👨‍💻 Creating Technical Teams")

            architecture_team = await self.factory.create_technical_team(
                {
                    "type": "architecture_review",
                    "name": "Elite Architecture Squad",
                    "focus": "micro_swarm_architecture",
                }
            )
            self.results["architecture_team"] = architecture_team

            security_team = await self.factory.create_technical_team(
                {
                    "type": "security_audit",
                    "name": "Security Strike Force",
                    "focus": "vulnerability_assessment",
                }
            )
            self.results["security_team"] = security_team

            # Generate comprehensive report
            report = self._generate_report()

            return report

        except Exception as e:
            logger.error(f"❌ Mission execution failed: {e}")
            return {"status": "failed", "error": str(e), "partial_results": self.results}

    def _generate_report(self):
        """Generate comprehensive execution report"""
        duration = (datetime.now() - self.start_time).total_seconds()

        # Get factory metrics
        metrics = self.factory.get_factory_metrics()

        # Extract mission results
        clean_sweep = self.results.get("clean_sweep", {})

        report = {
            "execution": "ARTEMIS FACTORY DIRECT EXECUTION",
            "status": "SUCCESS" if clean_sweep.get("success") else "PARTIAL",
            "duration_seconds": duration,
            "timestamp": datetime.now().isoformat(),
            "mission_results": {
                "operation_clean_sweep": clean_sweep,
                "phases_completed": clean_sweep.get("phases_completed", []),
                "findings": clean_sweep.get("results", {}),
            },
            "swarms_created": {
                "marketing": self.results.get("marketing_swarm"),
                "sales": self.results.get("sales_swarm"),
                "refactoring": self.results.get("refactor_swarm"),
            },
            "teams_deployed": {
                "architecture": self.results.get("architecture_team"),
                "security": self.results.get("security_team"),
            },
            "factory_metrics": metrics,
            "recommendations": self._generate_recommendations(),
            "implementation_plan": self._generate_implementation_plan(),
        }

        # Save report
        report_path = Path(
            f"artemis_factory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"\n📄 Report saved to: {report_path}")

        return report

    def _generate_recommendations(self):
        """Generate actionable recommendations"""
        return [
            {
                "priority": "CRITICAL",
                "category": "Architecture",
                "recommendations": [
                    "Implement domain-specific orchestrators immediately",
                    "Deploy Portkey as primary LLM gateway",
                    "Consolidate duplicate agent factories",
                ],
            },
            {
                "priority": "HIGH",
                "category": "Marketing & Sales",
                "recommendations": [
                    "Activate marketing micro-swarms for campaign management",
                    "Deploy persona builder with Gong/LinkedIn integration",
                    "Implement SMS vs Email decision engine",
                ],
            },
            {
                "priority": "HIGH",
                "category": "Technical",
                "recommendations": [
                    "Unify vector store on Milvus/Qdrant",
                    "Implement deduplication in data ingestion",
                    "Consolidate UI dashboards to one per orchestrator",
                ],
            },
            {
                "priority": "MEDIUM",
                "category": "Governance",
                "recommendations": [
                    "Create CEO console for permission management",
                    "Implement cost tracking per model",
                    "Set up monitoring dashboards",
                ],
            },
        ]

    def _generate_implementation_plan(self):
        """Generate step-by-step implementation plan"""
        return {
            "phase_1": {
                "name": "Foundation (Week 1)",
                "tasks": [
                    "Consolidate agent factories",
                    "Implement Portkey integration",
                    "Set up unified vector store",
                ],
            },
            "phase_2": {
                "name": "Micro-Swarms (Week 2)",
                "tasks": [
                    "Deploy marketing swarms",
                    "Deploy sales swarms",
                    "Implement swarm patterns (debate, consensus)",
                ],
            },
            "phase_3": {
                "name": "Integration (Week 3)",
                "tasks": [
                    "Connect HubSpot, Gong, Salesforce",
                    "Implement data ingestion pipeline",
                    "Deploy CEO console",
                ],
            },
            "phase_4": {
                "name": "Optimization (Week 4)",
                "tasks": ["Performance tuning", "Security hardening", "Documentation and training"],
            },
        }


async def main():
    """Main execution"""
    print("\n" + "=" * 80)
    print("⚔️  ARTEMIS UNIFIED FACTORY - DIRECT EXECUTION")
    print("=" * 80)
    print()
    print("🎯 Mission: Comprehensive Repository Audit & Enhancement")
    print("📦 Repository: sophia-intel-ai")
    print("🚀 Strategy: Military swarms with specialized teams")
    print()

    executor = ArtemisDirectExecutor()

    try:
        # Execute the mission
        report = await executor.execute_audit_mission()

        # Display results
        print("\n" + "=" * 80)
        print("✅ MISSION EXECUTION COMPLETE")
        print("=" * 80)
        print()

        if report.get("status") == "SUCCESS":
            print("🎆 Status: SUCCESS")
        else:
            print("⚠️  Status: PARTIAL SUCCESS")

        print(f"⏱️  Duration: {report.get('duration_seconds', 0):.2f} seconds")

        # Display metrics
        metrics = report.get("factory_metrics", {})
        if metrics:
            print("\n📈 Factory Metrics:")
            print(f"  - Active Agents: {metrics.get('active_agents', 0)}")
            print(f"  - Active Swarms: {metrics.get('active_swarms', 0)}")
            print(
                f"  - Missions Completed: {metrics.get('technical_metrics', {}).get('missions_completed', 0)}"
            )
            print(
                f"  - Task Utilization: {metrics.get('task_status', {}).get('utilization', 0)*100:.1f}%"
            )

        # Display recommendations
        print("\n💡 Top Recommendations:")
        for rec in report.get("recommendations", [])[:2]:
            print(f"  [{rec['priority']}] {rec['category']}:")
            for item in rec["recommendations"][:2]:
                print(f"    - {item}")

        # Display implementation phases
        print("\n📅 Implementation Plan:")
        plan = report.get("implementation_plan", {})
        for phase_key, phase in list(plan.items())[:2]:
            print(f"  {phase['name']}:")
            for task in phase["tasks"][:2]:
                print(f"    • {task}")

        print("\n📄 Full report: artemis_factory_report_*.json")
        print("\n🎯 Next Steps: Review report and begin Phase 1 implementation")

        return 0

    except Exception as e:
        print(f"\n❌ Execution failed: {e}")
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    # Run the async main
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
