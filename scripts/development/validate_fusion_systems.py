#!/usr/bin/env python3
"""
Fusion Systems Validation Script
Validates all 4 fusion systems are properly implemented and integrated
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "swarms"))
sys.path.append(str(project_root / "monitoring"))
sys.path.append(str(project_root / "devops"))
sys.path.append(str(project_root / "pipelines"))
sys.path.append(str(project_root / "backend"))


class FusionSystemsValidator:
    """Validates all fusion systems implementation"""

    def __init__(self):
        self.project_root = project_root
        self.validation_results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "unknown",
            "systems": {},
            "integration": {},
            "errors": [],
        }

    async def validate_all_systems(self) -> Dict[str, Any]:
        """Validate all fusion systems"""
        print("🔍 Starting Fusion Systems Validation...")
        print("=" * 60)

        # Validate individual systems
        await self.validate_redis_optimization()
        await self.validate_edge_rag()
        await self.validate_hybrid_routing()
        await self.validate_cross_db_analytics()

        # Validate integration components
        await self.validate_backend_api()
        await self.validate_frontend_dashboard()
        await self.validate_github_actions()

        # Calculate overall status
        self.calculate_overall_status()

        # Generate report
        self.generate_validation_report()

        return self.validation_results

    async def validate_redis_optimization(self):
        """Validate Redis optimization system"""
        print("🔧 Validating Redis Optimization System...")

        system_name = "redis_optimization"
        result = {
            "status": "unknown",
            "files_present": False,
            "imports_valid": False,
            "tests_present": False,
            "errors": [],
        }

        try:
            # Check if main file exists
            main_file = self.project_root / "swarms" / "mem0_agno_self_pruning.py"
            sophia_file = (
                self.project_root / "swarms" / "sophia_mem0_agno_self_pruning.py"
            )

            result["files_present"] = main_file.exists()
            result["tests_present"] = sophia_file.exists()

            if result["files_present"]:
                try:
                    from mem0_agno_self_pruning import (
                        MemoryOptimizationSwarm,
                        RedisPruningAgent,
                    )

                    result["imports_valid"] = True
                    print("  ✅ Redis optimization module imports successfully")
                except ImportError as e:
                    result["errors"].append(f"Import error: {e}")
                    print(f"  ❌ Import error: {e}")
            else:
                result["errors"].append("Main file not found")
                print("  ❌ Main file not found")

            # Determine status
            if (
                result["files_present"]
                and result["imports_valid"]
                and result["tests_present"]
            ):
                result["status"] = "valid"
                print("  ✅ Redis optimization system validation passed")
            else:
                result["status"] = "invalid"
                print("  ❌ Redis optimization system validation failed")

        except Exception as e:
            result["status"] = "error"
            result["errors"].append(str(e))
            print(f"  ❌ Validation error: {e}")

        self.validation_results["systems"][system_name] = result

    async def validate_edge_rag(self):
        """Validate Edge RAG system"""
        print("🧠 Validating Edge RAG System...")

        system_name = "edge_rag"
        result = {
            "status": "unknown",
            "files_present": False,
            "imports_valid": False,
            "errors": [],
        }

        try:
            # Check if main file exists
            main_file = self.project_root / "monitoring" / "qdrant_edge_rag.py"
            result["files_present"] = main_file.exists()

            if result["files_present"]:
                try:
                    from qdrant_edge_rag import EdgeRAGOrchestrator, QdrantEdgeRAG

                    result["imports_valid"] = True
                    print("  ✅ Edge RAG module imports successfully")
                except ImportError as e:
                    result["errors"].append(f"Import error: {e}")
                    print(f"  ❌ Import error: {e}")
            else:
                result["errors"].append("Main file not found")
                print("  ❌ Main file not found")

            # Determine status
            if result["files_present"] and result["imports_valid"]:
                result["status"] = "valid"
                print("  ✅ Edge RAG system validation passed")
            else:
                result["status"] = "invalid"
                print("  ❌ Edge RAG system validation failed")

        except Exception as e:
            result["status"] = "error"
            result["errors"].append(str(e))
            print(f"  ❌ Validation error: {e}")

        self.validation_results["systems"][system_name] = result

    async def validate_hybrid_routing(self):
        """Validate Hybrid Routing system"""
        print("🔀 Validating Hybrid Routing System...")

        system_name = "hybrid_routing"
        result = {
            "status": "unknown",
            "files_present": False,
            "imports_valid": False,
            "errors": [],
        }

        try:
            # Check if main file exists
            main_file = self.project_root / "devops" / "portkey_openrouter_hybrid.py"
            result["files_present"] = main_file.exists()

            if result["files_present"]:
                try:
                    from portkey_openrouter_hybrid import HybridModelRouter

                    result["imports_valid"] = True
                    print("  ✅ Hybrid routing module imports successfully")
                except ImportError as e:
                    result["errors"].append(f"Import error: {e}")
                    print(f"  ❌ Import error: {e}")
            else:
                result["errors"].append("Main file not found")
                print("  ❌ Main file not found")

            # Determine status
            if result["files_present"] and result["imports_valid"]:
                result["status"] = "valid"
                print("  ✅ Hybrid routing system validation passed")
            else:
                result["status"] = "invalid"
                print("  ❌ Hybrid routing system validation failed")

        except Exception as e:
            result["status"] = "error"
            result["errors"].append(str(e))
            print(f"  ❌ Validation error: {e}")

        self.validation_results["systems"][system_name] = result

    async def validate_cross_db_analytics(self):
        """Validate Cross-DB Analytics system"""
        print("📊 Validating Cross-DB Analytics System...")

        system_name = "cross_db_analytics"
        result = {
            "status": "unknown",
            "files_present": False,
            "imports_valid": False,
            "errors": [],
        }

        try:
            # Check if main file exists
            main_file = self.project_root / "pipelines" / "neon_qdrant_analytics.py"
            result["files_present"] = main_file.exists()

            if result["files_present"]:
                try:
                    from neon_qdrant_analytics import CrossDatabaseAnalyticsMCP

                    result["imports_valid"] = True
                    print("  ✅ Cross-DB analytics module imports successfully")
                except ImportError as e:
                    result["errors"].append(f"Import error: {e}")
                    print(f"  ❌ Import error: {e}")
            else:
                result["errors"].append("Main file not found")
                print("  ❌ Main file not found")

            # Determine status
            if result["files_present"] and result["imports_valid"]:
                result["status"] = "valid"
                print("  ✅ Cross-DB analytics system validation passed")
            else:
                result["status"] = "invalid"
                print("  ❌ Cross-DB analytics system validation failed")

        except Exception as e:
            result["status"] = "error"
            result["errors"].append(str(e))
            print(f"  ❌ Validation error: {e}")

        self.validation_results["systems"][system_name] = result

    async def validate_backend_api(self):
        """Validate backend API integration"""
        print("🔌 Validating Backend API Integration...")

        result = {
            "status": "unknown",
            "router_file_present": False,
            "router_imported": False,
            "main_updated": False,
            "errors": [],
        }

        try:
            # Check if router file exists
            router_file = (
                self.project_root / "backend" / "routers" / "fusion_metrics.py"
            )
            sophia_file = self.project_root / "backend" / "sophia_fusion_metrics_api.py"
            main_file = self.project_root / "backend" / "main.py"

            result["router_file_present"] = router_file.exists()

            if main_file.exists():
                main_content = main_file.read_text()
                result["router_imported"] = "fusion_metrics" in main_content
                result["main_updated"] = (
                    "app.include_router(fusion_metrics.router)" in main_content
                )

            if result["router_file_present"]:
                try:
                    from routers.fusion_metrics import router

                    print("  ✅ Fusion metrics router imports successfully")
                except ImportError as e:
                    result["errors"].append(f"Router import error: {e}")
                    print(f"  ❌ Router import error: {e}")

            # Determine status
            if (
                result["router_file_present"]
                and result["router_imported"]
                and result["main_updated"]
            ):
                result["status"] = "valid"
                print("  ✅ Backend API integration validation passed")
            else:
                result["status"] = "invalid"
                print("  ❌ Backend API integration validation failed")

        except Exception as e:
            result["status"] = "error"
            result["errors"].append(str(e))
            print(f"  ❌ Validation error: {e}")

        self.validation_results["integration"]["backend_api"] = result

    async def validate_frontend_dashboard(self):
        """Validate frontend dashboard integration"""
        print("🎨 Validating Frontend Dashboard Integration...")

        result = {
            "status": "unknown",
            "dashboard_file_present": False,
            "component_valid": False,
            "errors": [],
        }

        try:
            # Check if dashboard file exists
            dashboard_file = (
                self.project_root
                / "frontend"
                / "src"
                / "components"
                / "FusionMonitoringDashboard.tsx"
            )
            result["dashboard_file_present"] = dashboard_file.exists()

            if result["dashboard_file_present"]:
                # Check if component has required structure
                dashboard_content = dashboard_file.read_text()
                required_elements = [
                    "FusionMonitoringDashboard",
                    "redis_optimization",
                    "edge_rag",
                    "hybrid_routing",
                    "cross_db_analytics",
                    "/api/fusion/metrics",
                ]

                result["component_valid"] = all(
                    element in dashboard_content for element in required_elements
                )

                if result["component_valid"]:
                    print("  ✅ Dashboard component structure is valid")
                else:
                    result["errors"].append(
                        "Dashboard component missing required elements"
                    )
                    print("  ❌ Dashboard component missing required elements")
            else:
                result["errors"].append("Dashboard file not found")
                print("  ❌ Dashboard file not found")

            # Determine status
            if result["dashboard_file_present"] and result["component_valid"]:
                result["status"] = "valid"
                print("  ✅ Frontend dashboard integration validation passed")
            else:
                result["status"] = "invalid"
                print("  ❌ Frontend dashboard integration validation failed")

        except Exception as e:
            result["status"] = "error"
            result["errors"].append(str(e))
            print(f"  ❌ Validation error: {e}")

        self.validation_results["integration"]["frontend_dashboard"] = result

    async def validate_github_actions(self):
        """Validate GitHub Actions integration"""
        print("🔄 Validating GitHub Actions Integration...")

        result = {
            "status": "unknown",
            "workflow_file_present": False,
            "sophia_files_present": False,
            "workflow_valid": False,
            "errors": [],
        }

        try:
            # Check if workflow file exists
            workflow_file = (
                self.project_root / ".github" / "workflows" / "fusion-systems-test.yml"
            )
            result["workflow_file_present"] = workflow_file.exists()

            # Check if test files exist
            sophia_files = [
                self.project_root
                / "tests"
                / "integration"
                / "sophia_fusion_systems.py",
                self.project_root / "swarms" / "sophia_mem0_agno_self_pruning.py",
                self.project_root / "backend" / "sophia_fusion_metrics_api.py",
            ]

            result["sophia_files_present"] = all(f.exists() for f in sophia_files)

            if result["workflow_file_present"]:
                # Check if workflow has required structure
                workflow_content = workflow_file.read_text()
                required_elements = [
                    "fusion-unit-tests",
                    "fusion-integration-tests",
                    "frontend-fusion-tests",
                    "security-scan",
                    "sophia_fusion_systems.py",
                ]

                result["workflow_valid"] = all(
                    element in workflow_content for element in required_elements
                )

                if result["workflow_valid"]:
                    print("  ✅ GitHub Actions workflow structure is valid")
                else:
                    result["errors"].append("Workflow missing required elements")
                    print("  ❌ Workflow missing required elements")
            else:
                result["errors"].append("Workflow file not found")
                print("  ❌ Workflow file not found")

            # Determine status
            if (
                result["workflow_file_present"]
                and result["sophia_files_present"]
                and result["workflow_valid"]
            ):
                result["status"] = "valid"
                print("  ✅ GitHub Actions integration validation passed")
            else:
                result["status"] = "invalid"
                print("  ❌ GitHub Actions integration validation failed")

        except Exception as e:
            result["status"] = "error"
            result["errors"].append(str(e))
            print(f"  ❌ Validation error: {e}")

        self.validation_results["integration"]["github_actions"] = result

    def calculate_overall_status(self):
        """Calculate overall validation status"""
        all_systems_valid = all(
            system["status"] == "valid"
            for system in self.validation_results["systems"].values()
        )

        all_integrations_valid = all(
            integration["status"] == "valid"
            for integration in self.validation_results["integration"].values()
        )

        if all_systems_valid and all_integrations_valid:
            self.validation_results["overall_status"] = "valid"
        elif any(
            system["status"] == "error"
            for system in self.validation_results["systems"].values()
        ) or any(
            integration["status"] == "error"
            for integration in self.validation_results["integration"].values()
        ):
            self.validation_results["overall_status"] = "error"
        else:
            self.validation_results["overall_status"] = "invalid"

    def generate_validation_report(self):
        """Generate validation report"""
        print("\n" + "=" * 60)
        print("📋 FUSION SYSTEMS VALIDATION REPORT")
        print("=" * 60)

        # Overall status
        status_emoji = {"valid": "✅", "invalid": "❌", "error": "💥", "unknown": "❓"}

        overall_status = self.validation_results["overall_status"]
        print(
            f"Overall Status: {status_emoji[overall_status]} {overall_status.upper()}"
        )
        print()

        # Systems status
        print("🔧 FUSION SYSTEMS:")
        for system_name, system_result in self.validation_results["systems"].items():
            status = system_result["status"]
            print(f"  {status_emoji[status]} {system_name}: {status}")
            if system_result["errors"]:
                for error in system_result["errors"]:
                    print(f"    ⚠️  {error}")
        print()

        # Integration status
        print("🔌 INTEGRATION COMPONENTS:")
        for integration_name, integration_result in self.validation_results[
            "integration"
        ].items():
            status = integration_result["status"]
            print(f"  {status_emoji[status]} {integration_name}: {status}")
            if integration_result["errors"]:
                for error in integration_result["errors"]:
                    print(f"    ⚠️  {error}")
        print()

        # Summary
        total_systems = len(self.validation_results["systems"])
        valid_systems = sum(
            1
            for system in self.validation_results["systems"].values()
            if system["status"] == "valid"
        )

        total_integrations = len(self.validation_results["integration"])
        valid_integrations = sum(
            1
            for integration in self.validation_results["integration"].values()
            if integration["status"] == "valid"
        )

        print("📊 SUMMARY:")
        print(f"  Systems: {valid_systems}/{total_systems} valid")
        print(f"  Integrations: {valid_integrations}/{total_integrations} valid")
        print(f"  Timestamp: {self.validation_results['timestamp']}")

        # Save report to file
        report_file = self.project_root / "FUSION_VALIDATION_REPORT.json"
        with open(report_file, "w") as f:
            json.dump(self.validation_results, f, indent=2)

        print(f"\n📄 Full report saved to: {report_file}")


async def main():
    """Main validation function"""
    validator = FusionSystemsValidator()
    results = await validator.validate_all_systems()

    # Exit with appropriate code
    if results["overall_status"] == "valid":
        print("\n🎉 All fusion systems validation passed!")
        sys.exit(0)
    else:
        print("\n💥 Fusion systems validation failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
