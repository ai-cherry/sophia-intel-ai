#!/usr/bin/env python3
"""System verification and deployment readiness check."""

import asyncio
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import aiohttp


class SystemVerifier:
    """Comprehensive system verification for local deployment."""

    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "components": {},
            "files": {},
            "api": {},
            "git": {},
            "deployment_ready": False
        }

    def check_files(self) -> dict[str, Any]:
        """Verify all critical files exist."""
        print("\n📂 Checking Critical Files...")

        critical_files = {
            "Core API": [
                "app/api/unified_server.py",
                "app/api/base_endpoints.py",
                "app/api/streaming_handlers.py"
            ],
            "Swarm Components": [
                "app/swarms/improved_swarm.py",
                "app/swarms/unified_enhanced_orchestrator.py",
                "app/swarms/coding/team.py",
                "app/swarms/coding/agents.py",
                "app/swarms/coding/pools.py"
            ],
            "Configuration": [
                "swarm_config.json",
                "app/config/local_dev_config.py"
            ],
            "Tools": [
                "app/tools/live_tools.py",
                "app/tools/code_search.py"
            ],
            "MCP Servers": [
                "app/memory/supermemory_mcp.py",
                "app/memory/enhanced_mcp_server.py"
            ],
            "Documentation": [
                "docs/mcp-ui/inventory.md",
                "README.md"
            ]
        }

        results = {}
        all_present = True

        for category, files in critical_files.items():
            category_results = []
            for file in files:
                path = Path(file)
                exists = path.exists()
                category_results.append({
                    "file": file,
                    "exists": exists,
                    "size": path.stat().st_size if exists else 0
                })

                if not exists:
                    all_present = False
                    print(f"  ❌ Missing: {file}")

            results[category] = {
                "files": category_results,
                "complete": all([f["exists"] for f in category_results])
            }

            if results[category]["complete"]:
                print(f"  ✅ {category}: All files present")
            else:
                missing = [f["file"] for f in category_results if not f["exists"]]
                print(f"  ❌ {category}: Missing {len(missing)} files")

        self.results["files"] = results
        return {"all_present": all_present, "results": results}

    async def check_api(self) -> dict[str, Any]:
        """Verify API server functionality."""
        print("\n🌐 Checking API Server...")

        base_url = "http://localhost:8003"
        endpoints = {
            "health": "/healthz",
            "teams": "/teams",
            "workflows": "/workflows",
            "stats": "/stats"
        }

        results = {}
        all_working = True

        async with aiohttp.ClientSession() as session:
            # Check if server is running
            try:
                async with session.get(f"{base_url}/healthz") as resp:
                    if resp.status != 200:
                        print("  ❌ Server not responding")
                        return {"running": False, "results": {}}
            except:
                print("  ❌ Cannot connect to server on port 8003")
                return {"running": False, "results": {}}

            # Test each endpoint
            for name, endpoint in endpoints.items():
                try:
                    async with session.get(f"{base_url}{endpoint}") as resp:
                        status = resp.status
                        results[name] = {
                            "status": status,
                            "working": status == 200
                        }

                        if status == 200:
                            data = await resp.json()
                            if name == "teams":
                                results[name]["teams"] = [t["id"] for t in data]
                            elif name == "workflows":
                                results[name]["workflows"] = [w["id"] for w in data]

                        if status != 200:
                            all_working = False

                except Exception as e:
                    results[name] = {"status": "error", "error": str(e)}
                    all_working = False

        if all_working:
            print("  ✅ All endpoints responding")
        else:
            failed = [k for k, v in results.items() if not v.get("working", False)]
            print(f"  ⚠️  {len(failed)} endpoints not working: {', '.join(failed)}")

        self.results["api"] = results
        return {"running": True, "all_working": all_working, "results": results}

    def check_git(self) -> dict[str, Any]:
        """Check Git repository status."""
        print("\n📦 Checking Git Status...")

        try:
            # Get current branch
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True
            )
            current_branch = branch_result.stdout.strip()

            # Get uncommitted changes
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True
            )
            changes = status_result.stdout.strip().split('\n') if status_result.stdout.strip() else []

            # Get latest commit
            log_result = subprocess.run(
                ["git", "log", "-1", "--oneline"],
                capture_output=True,
                text=True
            )
            latest_commit = log_result.stdout.strip()

            results = {
                "branch": current_branch,
                "uncommitted_files": len(changes),
                "latest_commit": latest_commit,
                "clean": len(changes) == 0
            }

            if results["clean"]:
                print(f"  ✅ Clean repository on branch: {current_branch}")
            else:
                print(f"  ⚠️  {len(changes)} uncommitted changes on branch: {current_branch}")

            self.results["git"] = results
            return results

        except Exception as e:
            print(f"  ❌ Git error: {e}")
            self.results["git"] = {"error": str(e)}
            return {"error": str(e)}

    def analyze_swarms(self) -> dict[str, Any]:
        """Analyze swarm implementations."""
        print("\n🐝 Analyzing Swarm Implementations...")

        swarm_analysis = {
            "patterns_implemented": [],
            "swarm_types": [],
            "enhancements": []
        }

        # Check improved swarm patterns
        improved_path = Path("app/swarms/improved_swarm.py")
        if improved_path.exists():
            content = improved_path.read_text()

            patterns = {
                "Adversarial Debate": "adversarial_debate",
                "Quality Gates": "quality_gates",
                "Strategy Archive": "strategy_archive",
                "Safety Boundaries": "safety_boundaries",
                "Dynamic Roles": "dynamic_role_assignment",
                "Consensus": "consensus_mechanism",
                "Adaptive Parameters": "adaptive_parameters",
                "Knowledge Transfer": "knowledge_transfer"
            }

            for name, code in patterns.items():
                if code in content:
                    swarm_analysis["patterns_implemented"].append(name)

            print(f"  ✅ {len(swarm_analysis['patterns_implemented'])}/8 enhancement patterns implemented")

        # Check swarm types
        swarm_files = {
            "Coding Team": "app/swarms/coding/team.py",
            "Coding Swarm": "app/swarms/coding/agents.py",
            "Unified Orchestrator": "app/swarms/unified_enhanced_orchestrator.py"
        }

        for name, file in swarm_files.items():
            if Path(file).exists():
                swarm_analysis["swarm_types"].append(name)

        print(f"  ✅ {len(swarm_analysis['swarm_types'])} swarm types available")

        self.results["components"]["swarms"] = swarm_analysis
        return swarm_analysis

    def generate_report(self) -> bool:
        """Generate final verification report."""
        print("\n" + "="*60)
        print("📊 SYSTEM VERIFICATION REPORT")
        print("="*60)

        # Calculate overall readiness
        checks = {
            "Files": all(v.get("complete", False) for v in self.results["files"].values()),
            "API": self.results["api"].get("health", {}).get("working", False),
            "Git": self.results["git"].get("clean", False),
            "Swarms": len(self.results["components"].get("swarms", {}).get("patterns_implemented", [])) >= 6
        }

        all_ready = all(checks.values())
        self.results["deployment_ready"] = all_ready

        print("\n✅ Deployment Checklist:")
        for check, status in checks.items():
            icon = "✅" if status else "❌"
            print(f"  {icon} {check}")

        if all_ready:
            print("\n🎉 SYSTEM IS READY FOR DEPLOYMENT")
            print("\nAll components verified and operational:")
            print("  • All critical files present")
            print("  • API server running and responsive")
            print("  • Git repository clean")
            print("  • Swarm enhancements implemented")
            print("\n✨ Ready to push to GitHub!")
        else:
            print("\n⚠️  SYSTEM NOT READY FOR DEPLOYMENT")
            print("\nIssues to resolve:")

            if not checks["Files"]:
                print("  • Some critical files are missing")
            if not checks["API"]:
                print("  • API server not fully operational")
            if not checks["Git"]:
                print("  • Uncommitted changes in repository")
            if not checks["Swarms"]:
                print("  • Swarm enhancements incomplete")

        # Save report
        report_path = Path("verification_report.json")
        with open(report_path, "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"\n📁 Full report saved to: {report_path}")

        return all_ready

    async def run_verification(self) -> bool:
        """Run complete system verification."""
        print("\n" + "="*60)
        print("🔍 COMPREHENSIVE SYSTEM VERIFICATION")
        print("="*60)

        # Run all checks
        self.check_files()
        await self.check_api()
        self.check_git()
        self.analyze_swarms()

        # Generate report
        ready = self.generate_report()

        return ready


async def main():
    """Main verification runner."""
    verifier = SystemVerifier()
    ready = await verifier.run_verification()

    if ready:
        print("\n🚀 System verified and ready for deployment!")
        return 0
    else:
        print("\n⚠️  System verification failed. Please address issues above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
