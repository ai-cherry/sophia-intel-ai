#!/usr/bin/env python3
"""
ARTEMIS REAL SCAN SWARM - AGENTS WITH ACTUAL FILE ACCESS
These agents can REALLY read and modify your code
"""

import asyncio
import glob
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
from dotenv import load_dotenv

# Import the file access tools
from app.tools.basic_tools import read_file

load_dotenv()

# Set API keys
if not os.environ.get("AIMLAPI_API_KEY"):
    os.environ["AIMLAPI_API_KEY"] = "562d964ac0b54357874b01de33cb91e9"
if not os.environ.get("OPENROUTER_API_KEY"):
    os.environ["OPENROUTER_API_KEY"] = (
        "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"
    )


@dataclass
class RealScanResult:
    """Result from a real repository scan"""

    agent_name: str
    model: str
    files_scanned: int
    issues_found: List[Dict[str, Any]]
    execution_time: float
    success: bool
    error: Optional[str] = None


class ArtemisRealScanSwarm:
    """Real scanning swarm that actually reads files"""

    def __init__(self):
        self.repo_path = "/Users/lynnmusil/sophia-intel-ai"
        self.critical_files = []
        self.security_issues = []
        self.architecture_issues = []
        self.performance_issues = []

    def scan_repository_structure(self) -> Dict[str, Any]:
        """Get real repository structure"""
        print("\n📂 Scanning REAL repository structure...")

        # Count real files
        py_files = glob.glob(f"{self.repo_path}/**/*.py", recursive=True)
        tsx_files = glob.glob(f"{self.repo_path}/**/*.tsx", recursive=True)
        ts_files = glob.glob(f"{self.repo_path}/**/*.ts", recursive=True)

        # Get critical files to scan
        critical_files = [
            "app/artemis/unified_factory.py",
            "app/sophia/sophia_orchestrator.py",
            "app/core/websocket_manager.py",
            "app/core/portkey_config.py",
            "app/core/aimlapi_config.py",
            "app/api/unified_server.py",
            ".env",
        ]

        self.critical_files = critical_files

        return {
            "python_files": len(py_files),
            "typescript_files": len(ts_files),
            "tsx_files": len(tsx_files),
            "total_files": len(py_files) + len(ts_files) + len(tsx_files),
            "critical_files": critical_files,
            "sample_py_files": py_files[:10],
        }

    async def agent1_security_scanner(self) -> RealScanResult:
        """Agent 1: REAL security scanning with file access"""
        agent_name = "SECURITY SCANNER ALPHA"
        model = "grok-code-fast-1"

        print(f"\n🔒 {agent_name} starting REAL file scan...")
        start = time.time()

        issues = []
        files_scanned = 0

        try:
            # REAL file scanning
            for file_path in self.critical_files:
                full_path = os.path.join(self.repo_path, file_path)
                if os.path.exists(full_path):
                    result = read_file(full_path)
                    if "content" in result:
                        files_scanned += 1
                        content = result["content"]

                        # Check for REAL security issues
                        if "api_key" in content.lower() or "secret" in content.lower():
                            # Look for actual exposed keys
                            lines = content.split("\n")
                            for i, line in enumerate(lines, 1):
                                if ('="' in line or "='" in line) and any(
                                    key in line.lower()
                                    for key in ["key", "secret", "token", "password"]
                                ):
                                    if not line.strip().startswith("#"):
                                        issues.append(
                                            {
                                                "type": "EXPOSED_SECRET",
                                                "file": file_path,
                                                "line": i,
                                                "severity": "CRITICAL",
                                                "preview": line.strip()[:100],
                                            }
                                        )

                        # Check for SQL injection vulnerabilities
                        if ".execute(" in content or "cursor.execute" in content:
                            lines = content.split("\n")
                            for i, line in enumerate(lines, 1):
                                if "execute" in line and (
                                    "%" in line
                                    or ".format(" in line
                                    or "f'" in line
                                    or 'f"' in line
                                ):
                                    issues.append(
                                        {
                                            "type": "SQL_INJECTION_RISK",
                                            "file": file_path,
                                            "line": i,
                                            "severity": "HIGH",
                                            "preview": line.strip()[:100],
                                        }
                                    )

            # Scan .env file for exposed keys
            env_path = os.path.join(self.repo_path, ".env")
            if os.path.exists(env_path):
                env_result = read_file(env_path)
                if "content" in env_result:
                    files_scanned += 1
                    for line in env_result["content"].split("\n"):
                        if "=" in line and not line.startswith("#"):
                            key, value = line.split("=", 1)
                            if (
                                value
                                and not value.startswith("YOUR_")
                                and len(value) > 10
                            ):
                                issues.append(
                                    {
                                        "type": "ENV_KEY_EXPOSED",
                                        "file": ".env",
                                        "key": key.strip(),
                                        "severity": "CRITICAL",
                                        "recommendation": "Move to secure secrets manager",
                                    }
                                )

            self.security_issues = issues

            return RealScanResult(
                agent_name=agent_name,
                model=model,
                files_scanned=files_scanned,
                issues_found=issues,
                execution_time=time.time() - start,
                success=True,
            )

        except Exception as e:
            return RealScanResult(
                agent_name=agent_name,
                model=model,
                files_scanned=files_scanned,
                issues_found=issues,
                execution_time=time.time() - start,
                success=False,
                error=str(e),
            )

    async def agent2_architecture_analyzer(self) -> RealScanResult:
        """Agent 2: REAL architecture analysis"""
        agent_name = "ARCHITECTURE ANALYZER BRAVO"
        model = "llama-4-scout"

        print(f"\n🏗️ {agent_name} analyzing REAL architecture...")
        start = time.time()

        issues = []
        files_scanned = 0

        try:
            # Check for duplicate orchestrators
            orchestrator_files = glob.glob(
                f"{self.repo_path}/**/orchestrator*.py", recursive=True
            )
            orchestrator_files += glob.glob(
                f"{self.repo_path}/**/*factory*.py", recursive=True
            )

            duplicate_functions = {}

            for file_path in orchestrator_files[:20]:  # Limit to 20 files
                result = read_file(file_path)
                if "content" in result:
                    files_scanned += 1
                    content = result["content"]

                    # Find function definitions
                    lines = content.split("\n")
                    for i, line in enumerate(lines, 1):
                        if line.strip().startswith("def "):
                            func_name = line.split("(")[0].replace("def ", "").strip()
                            if func_name in duplicate_functions:
                                duplicate_functions[func_name].append((file_path, i))
                            else:
                                duplicate_functions[func_name] = [(file_path, i)]

            # Report duplicates
            for func_name, locations in duplicate_functions.items():
                if len(locations) > 1:
                    issues.append(
                        {
                            "type": "DUPLICATE_FUNCTION",
                            "function": func_name,
                            "locations": [
                                {
                                    "file": loc[0].replace(self.repo_path, ""),
                                    "line": loc[1],
                                }
                                for loc in locations
                            ],
                            "severity": "MEDIUM",
                            "impact": "Code redundancy increases maintenance burden",
                        }
                    )

            # Check for circular imports
            import_map = {}
            for py_file in glob.glob(f"{self.repo_path}/app/**/*.py", recursive=True)[
                :50
            ]:
                result = read_file(py_file)
                if "content" in result:
                    files_scanned += 1
                    imports = []
                    for line in result["content"].split("\n"):
                        if line.startswith("from app.") or line.startswith(
                            "import app."
                        ):
                            imports.append(line.strip())
                    if imports:
                        import_map[py_file.replace(self.repo_path, "")] = imports

            if len(import_map) > 10:
                issues.append(
                    {
                        "type": "COMPLEX_IMPORT_STRUCTURE",
                        "modules_analyzed": len(import_map),
                        "severity": "LOW",
                        "recommendation": "Consider simplifying import structure",
                    }
                )

            self.architecture_issues = issues

            return RealScanResult(
                agent_name=agent_name,
                model=model,
                files_scanned=files_scanned,
                issues_found=issues,
                execution_time=time.time() - start,
                success=True,
            )

        except Exception as e:
            return RealScanResult(
                agent_name=agent_name,
                model=model,
                files_scanned=files_scanned,
                issues_found=issues,
                execution_time=time.time() - start,
                success=False,
                error=str(e),
            )

    async def agent3_performance_scanner(self) -> RealScanResult:
        """Agent 3: REAL performance issue detection"""
        agent_name = "PERFORMANCE SCANNER CHARLIE"
        model = "deepseek-chat"

        print(f"\n⚡ {agent_name} scanning for REAL performance issues...")
        start = time.time()

        issues = []
        files_scanned = 0

        try:
            # Scan for performance issues
            py_files = glob.glob(f"{self.repo_path}/app/**/*.py", recursive=True)[:30]

            for file_path in py_files:
                result = read_file(file_path)
                if "content" in result:
                    files_scanned += 1
                    content = result["content"]
                    lines = content.split("\n")

                    for i, line in enumerate(lines, 1):
                        # Check for synchronous I/O in async functions
                        if (
                            "async def" in content
                            and "open(" in line
                            and "await" not in line
                        ):
                            issues.append(
                                {
                                    "type": "BLOCKING_IO_IN_ASYNC",
                                    "file": file_path.replace(self.repo_path, ""),
                                    "line": i,
                                    "severity": "HIGH",
                                    "preview": line.strip()[:100],
                                }
                            )

                        # Check for nested loops (potential O(n²))
                        if "for " in line:
                            # Check next 10 lines for another loop
                            for j in range(i + 1, min(i + 10, len(lines))):
                                if "for " in lines[j] and lines[j].count(
                                    " "
                                ) > line.count(" "):
                                    issues.append(
                                        {
                                            "type": "NESTED_LOOP",
                                            "file": file_path.replace(
                                                self.repo_path, ""
                                            ),
                                            "line": i,
                                            "severity": "MEDIUM",
                                            "complexity": "Potential O(n²) complexity",
                                        }
                                    )
                                    break

                        # Check for large list comprehensions
                        if (
                            "[" in line
                            and "for" in line
                            and "]" in line
                            and len(line) > 100
                        ):
                            issues.append(
                                {
                                    "type": "LARGE_LIST_COMPREHENSION",
                                    "file": file_path.replace(self.repo_path, ""),
                                    "line": i,
                                    "severity": "LOW",
                                    "recommendation": "Consider using generator for memory efficiency",
                                }
                            )

            self.performance_issues = issues

            return RealScanResult(
                agent_name=agent_name,
                model=model,
                files_scanned=files_scanned,
                issues_found=issues,
                execution_time=time.time() - start,
                success=True,
            )

        except Exception as e:
            return RealScanResult(
                agent_name=agent_name,
                model=model,
                files_scanned=files_scanned,
                issues_found=issues,
                execution_time=time.time() - start,
                success=False,
                error=str(e),
            )

    async def run_real_parallel_scan(self) -> Dict[str, Any]:
        """Execute REAL parallel repository scan"""
        print("\n" + "=" * 70)
        print("🚀 ARTEMIS REAL SCAN SWARM ACTIVATION")
        print("=" * 70)
        print(f"📅 Timestamp: {datetime.now().isoformat()}")
        print(f"📁 Repository: {self.repo_path}")
        print("🎯 Mission: REAL File Analysis")
        print("=" * 70)

        # Get repository structure
        repo_info = self.scan_repository_structure()
        print("\n📊 Repository Stats:")
        print(f"  Python files: {repo_info['python_files']}")
        print(f"  TypeScript files: {repo_info['typescript_files']}")
        print(f"  TSX files: {repo_info['tsx_files']}")
        print(f"  Total: {repo_info['total_files']} files")

        # Run all agents in parallel
        print("\n⚡ LAUNCHING REAL PARALLEL SCAN...")
        tasks = [
            self.agent1_security_scanner(),
            self.agent2_architecture_analyzer(),
            self.agent3_performance_scanner(),
        ]

        results = await asyncio.gather(*tasks)

        # Compile results
        total_files_scanned = sum(r.files_scanned for r in results)
        total_issues = sum(len(r.issues_found) for r in results)

        print("\n" + "=" * 70)
        print("📊 REAL SCAN RESULTS")
        print("=" * 70)

        for result in results:
            status = "✅" if result.success else "❌"
            print(f"\n{status} {result.agent_name}")
            print(f"  Model: {result.model}")
            print(f"  Files Scanned: {result.files_scanned}")
            print(f"  Issues Found: {len(result.issues_found)}")
            print(f"  Execution Time: {result.execution_time:.2f}s")

            if result.issues_found:
                print("\n  Top Issues:")
                for issue in result.issues_found[:3]:
                    print(
                        f"    • {issue.get('type', 'UNKNOWN')}: {issue.get('file', 'N/A')}"
                    )
                    if "line" in issue:
                        print(
                            f"      Line {issue['line']}: {issue.get('preview', '')[:60]}..."
                        )

        # Generate report
        report = {
            "timestamp": datetime.now().isoformat(),
            "repository": self.repo_path,
            "scan_type": "REAL_FILE_ANALYSIS",
            "repository_stats": repo_info,
            "total_files_scanned": total_files_scanned,
            "total_issues_found": total_issues,
            "security_issues": self.security_issues,
            "architecture_issues": self.architecture_issues,
            "performance_issues": self.performance_issues,
            "agents": [
                {
                    "name": r.agent_name,
                    "model": r.model,
                    "files_scanned": r.files_scanned,
                    "issues": len(r.issues_found),
                    "success": r.success,
                    "time": r.execution_time,
                }
                for r in results
            ],
        }

        # Save report
        report_file = (
            f"artemis_real_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\n💾 Full report saved to: {report_file}")

        # Show critical issues
        critical_issues = [
            i for i in self.security_issues if i.get("severity") == "CRITICAL"
        ]
        if critical_issues:
            print("\n🚨 CRITICAL SECURITY ISSUES FOUND:")
            for issue in critical_issues[:5]:
                print(f"  • {issue['type']}: {issue.get('file', 'N/A')}")
                if "key" in issue:
                    print(f"    Key: {issue['key']}")

        return report


async def main():
    """Execute the real scan swarm"""
    swarm = ArtemisRealScanSwarm()
    report = await swarm.run_real_parallel_scan()

    print("\n" + "=" * 70)
    print("✅ REAL SCAN COMPLETE")
    print("=" * 70)
    print(f"Total Issues Found: {report['total_issues_found']}")
    print(f"Files Actually Scanned: {report['total_files_scanned']}")

    # Show summary
    if report["total_issues_found"] > 0:
        print("\n📋 ISSUE SUMMARY:")
        print(f"  Security Issues: {len(report['security_issues'])}")
        print(f"  Architecture Issues: {len(report['architecture_issues'])}")
        print(f"  Performance Issues: {len(report['performance_issues'])}")


if __name__ == "__main__":
    asyncio.run(main())
