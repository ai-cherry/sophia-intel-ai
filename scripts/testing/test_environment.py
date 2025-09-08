#!/usr/bin/env python3
"""
Comprehensive environment and API key testing script.
Tests all API keys, Portkey virtual keys, and tech stack versions.
"""

import asyncio
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.ai_logger import logger

# Import our environment loader


class TechStackAnalyzer:
    """Analyze tech stack versions and compatibility."""

    def __init__(self):
        self.config = get_env_config()
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "versions": {},
            "api_keys": {},
            "gaps": [],
            "recommendations": [],
        }

    def check_python_packages(self) -> dict[str, Any]:
        """Check installed Python package versions."""
        logger.info("\n📦 Checking Python Package Versions...")

        packages = {
            "agno": "1.8.1",  # Latest as of Aug 30, 2025
            "weaviate-client": "4.16.9",  # Latest
            "weaviate-agents": "0.13.0",  # Latest
            "pulumi": "3.192.0",  # Latest CLI
            "fastapi": "0.116.1",
            "openai": "1.75.0",
            "portkey-ai": None,  # Check if installed
            "psycopg2-binary": None,
            "sqlalchemy": None,
            "airbyte-cdk": None,
        }

        installed = {}
        for pkg, latest in packages.items():
            try:
                result = subprocess.run(
                    ["pip3", "show", pkg], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    for line in result.stdout.split("\n"):
                        if line.startswith("Version:"):
                            current = line.split(":")[1].strip()
                            installed[pkg] = {
                                "current": current,
                                "latest": latest,
                                "status": "✅" if not latest or current == latest else "⚠️",
                            }
                            break
                else:
                    installed[pkg] = {"current": None, "latest": latest, "status": "❌"}
            except Exception:installed[pkg] = {"current": None, "latest": latest, "status": "❌"}

        self.results["versions"]["python_packages"] = installed

        # Print results
        for pkg, info in installed.items():
            status = info["status"]
            current = info["current"] or "Not installed"
            latest = info["latest"] or "N/A"

            if status == "✅":
                logger.info(f"  {status} {pkg}: {current}")
            elif status == "⚠️":
                logger.info(f"  {status} {pkg}: {current} (latest: {latest})")
            else:
                logger.info(f"  {status} {pkg}: Not installed")

        return installed

    def check_system_tools(self) -> dict[str, Any]:
        """Check system tool versions."""
        logger.info("\n🛠️ Checking System Tool Versions...")

        tools = {
            "pulumi": {"command": ["pulumi", "version"], "latest": "v3.192.0"},
            "esc": {"command": ["esc", "version"], "latest": "v0.17.0"},
            "docker": {"command": ["docker", "--version"], "latest": None},
            "node": {"command": ["node", "--version"], "latest": None},
            "postgresql": {"command": ["psql", "--version"], "latest": "17.5"},
        }

        installed = {}
        for tool, info in tools.items():
            try:
                result = subprocess.run(info["command"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    version_str = result.stdout.strip()
                    installed[tool] = {
                        "current": version_str,
                        "latest": info["latest"],
                        "status": "✅",
                    }
                    logger.info(f"  ✅ {tool}: {version_str}")
                else:
                    installed[tool] = {"current": None, "latest": info["latest"], "status": "❌"}
                    logger.info(f"  ❌ {tool}: Not installed")
            except Exception:installed[tool] = {"current": None, "latest": info["latest"], "status": "❌"}
                logger.info(f"  ❌ {tool}: Not found")

        self.results["versions"]["system_tools"] = installed
        return installed

    async def test_api_keys(self) -> dict[str, Any]:
        """Test all API keys and Portkey virtual keys."""
        logger.info("\n🔑 Testing API Keys...")

        key_tests = {
            "portkey": {
                "key": self.config.portkey_api_key,
                "test_url": "https://api.portkey.ai/v1/models",
                "headers": {"Authorization": f"Bearer {self.config.portkey_api_key}"},
            },
            "openrouter": {
                "key": self.config.openrouter_api_key,
                "test_url": "https://openrouter.ai/api/v1/models",
                "headers": {"Authorization": f"Bearer {self.config.openrouter_api_key}"},
            },
            "anthropic": {
                "key": self.config.anthropic_api_key,
                "test_url": "https://api.anthropic.com/v1/messages",
                "headers": {
                    "x-api-key": self.config.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                },
            },
            "openai": {
                "key": self.config.openai_native_api_key,
                "test_url": "https://api.openai.com/v1/models",
                "headers": {"Authorization": f"Bearer {self.config.openai_native_api_key}"},
            },
            "groq": {
                "key": self.config.groq_api_key,
                "test_url": "https://api.groq.com/openai/v1/models",
                "headers": {"Authorization": f"Bearer {self.config.groq_api_key}"},
            },
            "together": {
                "key": self.config.together_api_key,
                "test_url": "https://api.together.xyz/v1/models",
                "headers": {"Authorization": f"Bearer {self.config.together_api_key}"},
            },
        }

        results = {}
        async with httpx.AsyncClient(timeout=10.0) as client:
            for provider, info in key_tests.items():
                if not info["key"] or info["key"].startswith("YOUR_"):
                    results[provider] = {"status": "❌", "error": "Not configured"}
                    logger.info(f"  ❌ {provider}: Not configured")
                else:
                    try:
                        response = await client.get(info["test_url"], headers=info["headers"])
                        if response.status_code in [200, 201]:
                            results[provider] = {"status": "✅", "valid": True}
                            logger.info(f"  ✅ {provider}: Valid")
                        elif response.status_code == 401:
                            results[provider] = {"status": "❌", "error": "Invalid key"}
                            logger.info(f"  ❌ {provider}: Invalid key")
                        else:
                            results[provider] = {
                                "status": "⚠️",
                                "error": f"Status {response.status_code}",
                            }
                            logger.info(f"  ⚠️ {provider}: Status {response.status_code}")
                    except Exception as e:
                        results[provider] = {"status": "❌", "error": str(e)}
                        logger.info(f"  ❌ {provider}: {e}")

        self.results["api_keys"] = results
        return results

    async def test_portkey_virtual_keys(self) -> dict[str, Any]:
        """Test Portkey virtual keys specifically."""
        logger.info("\n🔐 Testing Portkey Virtual Keys...")

        if not self.config.portkey_api_key or self.config.portkey_api_key.startswith("YOUR_"):
            logger.info("  ❌ Portkey not configured")
            return {"status": "not_configured"}

        # Test with Portkey gateway
        virtual_key_tests = [
            {
                "name": "openrouter_vk",
                "model": "openrouter/qwen/qwen-2.5-coder-32b-instruct",
                "provider": "openrouter",
            },
            {
                "name": "together_vk",
                "model": "togethercomputer/m2-bert-80M-8k-retrieval",
                "provider": "together",
            },
            {"name": "anthropic_vk", "model": "claude-3-haiku-20240307", "provider": "anthropic"},
        ]

        results = {}
        async with httpx.AsyncClient(timeout=10.0) as client:
            for vk_test in virtual_key_tests:
                try:
                    # Test completion with minimal tokens
                    response = await client.post(
                        "https://api.portkey.ai/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.config.portkey_api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": vk_test["model"],
                            "messages": [{"role": "user", "content": "Hi"}],
                            "max_tokens": 5,
                        },
                    )

                    if response.status_code == 200:
                        results[vk_test["name"]] = {"status": "✅", "provider": vk_test["provider"]}
                        logger.info(f"  ✅ {vk_test['name']}: Working")
                    else:
                        results[vk_test["name"]] = {
                            "status": "❌",
                            "error": f"Status {response.status_code}",
                        }
                        logger.info(f"  ❌ {vk_test['name']}: Failed ({response.status_code})")
                except Exception as e:
                    results[vk_test["name"]] = {"status": "❌", "error": str(e)}
                    logger.info(f"  ❌ {vk_test['name']}: {e}")

        self.results["portkey_virtual_keys"] = results
        return results

    def check_weaviate(self) -> dict[str, Any]:
        """Check Weaviate connection and version."""
        logger.info("\n🔍 Checking Weaviate...")

        try:
            import weaviate

            client = weaviate.Client(
                url=self.config.weaviate_url or "http://localhost:8080",
                auth_client_secret=(
                    weaviate.AuthApiKey(api_key=self.config.weaviate_api_key)
                    if self.config.weaviate_api_key
                    else None
                ),
            )

            # Get server version
            meta = client.get_meta()
            server_version = meta.get("version", "Unknown")

            result = {
                "status": "✅",
                "server_version": server_version,
                "latest_version": "1.32.0",
                "client_version": (
                    weaviate.__version__ if hasattr(weaviate, "__version__") else "Unknown"
                ),
            }

            logger.info(f"  ✅ Server: {server_version} (latest: 1.32.0)")
            logger.info(f"  ✅ Client: {result['client_version']}")

        except Exception as e:
            result = {"status": "❌", "error": str(e)}
            logger.info(f"  ❌ Weaviate: {e}")

        self.results["versions"]["weaviate"] = result
        return result

    def analyze_gaps(self) -> list[dict[str, Any]]:
        """Analyze gaps and create recommendations."""
        logger.info("\n📊 Gap Analysis...")

        gaps = []

        # Check Python packages
        for pkg, info in self.results["versions"].get("python_packages", {}).items():
            if info["status"] == "❌":
                gaps.append(
                    {
                        "type": "missing_package",
                        "package": pkg,
                        "severity": "high" if pkg in ["agno", "weaviate-client"] else "medium",
                        "action": f"pip install {pkg}",
                    }
                )
            elif info["status"] == "⚠️":
                gaps.append(
                    {
                        "type": "outdated_package",
                        "package": pkg,
                        "current": info["current"],
                        "latest": info["latest"],
                        "severity": "medium",
                        "action": f"pip install -U {pkg}=={info['latest']}",
                    }
                )

        # Check API keys
        for provider, info in self.results.get("api_keys", {}).items():
            if info["status"] == "❌":
                gaps.append(
                    {
                        "type": "missing_api_key",
                        "provider": provider,
                        "severity": "high" if provider in ["portkey", "openai"] else "medium",
                        "action": f"Configure {provider.upper()}_API_KEY in .env",
                    }
                )

        # Check Weaviate
        weaviate_info = self.results["versions"].get("weaviate", {})
        if weaviate_info.get("status") == "❌":
            gaps.append(
                {
                    "type": "service_down",
                    "service": "weaviate",
                    "severity": "high",
                    "action": "Start Weaviate with docker-compose",
                }
            )
        elif weaviate_info.get("server_version"):
            current = weaviate_info["server_version"]
            latest = "1.32.0"
            if current < latest:
                gaps.append(
                    {
                        "type": "outdated_service",
                        "service": "weaviate",
                        "current": current,
                        "latest": latest,
                        "severity": "medium",
                        "action": "Update Weaviate docker image to 1.32.0",
                    }
                )

        self.results["gaps"] = gaps

        # Print gaps
        if gaps:
            logger.info(f"\n  Found {len(gaps)} gaps:")

            high_severity = [g for g in gaps if g.get("severity") == "high"]
            medium_severity = [g for g in gaps if g.get("severity") == "medium"]

            if high_severity:
                logger.info(f"\n  🔴 High Severity ({len(high_severity)}):")
                for gap in high_severity:
                    logger.info(
                        f"    • {gap['type']}: {gap.get('package') or gap.get('provider') or gap.get('service')}"
                    )
                    logger.info(f"      Action: {gap['action']}")

            if medium_severity:
                logger.info(f"\n  🟡 Medium Severity ({len(medium_severity)}):")
                for gap in medium_severity:
                    logger.info(
                        f"    • {gap['type']}: {gap.get('package') or gap.get('provider') or gap.get('service')}"
                    )
                    if gap.get("current"):
                        logger.info(
                            f"      Current: {gap['current']} → Latest: {gap.get('latest')}"
                        )
                    logger.info(f"      Action: {gap['action']}")
        else:
            logger.info("  ✅ No critical gaps found!")

        return gaps

    def generate_recommendations(self) -> list[str]:
        """Generate upgrade recommendations."""
        logger.info("\n💡 Recommendations...")

        recommendations = []

        # Based on latest versions (Aug 30, 2025)
        tech_updates = {
            "PostgreSQL": {
                "current": None,  # Check if using Neon
                "latest": "17.5",
                "benefit": "Performance improvements, native JSON operations",
            },
            "Weaviate": {
                "current": self.results["versions"].get("weaviate", {}).get("server_version"),
                "latest": "1.32.0",
                "benefit": "Collection aliases, RQ, compressed HNSW",
            },
            "Pulumi": {
                "current": self.results["versions"]
                .get("system_tools", {})
                .get("pulumi", {})
                .get("current"),
                "latest": "v3.192.0",
                "benefit": "Vigilant mode, better secrets management",
            },
            "Lambda Stack": {
                "current": None,
                "latest": "CUDA 12.8, PyTorch 2.7.0",
                "benefit": "GPU acceleration for AI workloads",
            },
            "Airbyte": {
                "current": None,
                "latest": "v1.8",
                "benefit": "Iceberg support, AI sync diagnosis",
            },
        }

        for tech, info in tech_updates.items():
            if not info["current"] or (info["current"] and info["current"] < info["latest"]):
                recommendations.append(f"Upgrade {tech} to {info['latest']}: {info['benefit']}")

        # Specific recommendations for our stack
        if not self.config.portkey_api_key or self.config.portkey_api_key.startswith("YOUR_"):
            recommendations.append(
                "Configure Portkey for unified LLM gateway - reduces complexity and adds failover"
            )

        if self.results.get("api_keys", {}).get("openrouter", {}).get("status") != "✅":
            recommendations.append("Set up OpenRouter for access to 100+ models with single API")

        # Infrastructure recommendations
        recommendations.extend(
            [
                "Consider Neon PostgreSQL for serverless database with autoscaling",
                "Implement Pulumi ESC for centralized secrets management",
                "Add Airbyte for data pipeline automation if needed",
                "Enable Weaviate's new RQ feature for 3x memory efficiency",
            ]
        )

        self.results["recommendations"] = recommendations

        # Print recommendations
        for i, rec in enumerate(recommendations[:5], 1):  # Top 5
            logger.info(f"  {i}. {rec}")

        return recommendations

    async def run_full_analysis(self):
        """Run complete environment analysis."""
        logger.info("\n" + "=" * 60)
        logger.info("🔬 COMPREHENSIVE ENVIRONMENT ANALYSIS")
        logger.info("=" * 60)

        # Check versions
        self.check_python_packages()
        self.check_system_tools()
        self.check_weaviate()

        # Test API keys
        await self.test_api_keys()
        await self.test_portkey_virtual_keys()

        # Analyze gaps
        self.analyze_gaps()
        self.generate_recommendations()

        # Generate report
        self.generate_report()

    def generate_report(self):
        """Generate comprehensive report."""
        logger.info("\n" + "=" * 60)
        logger.info("📋 ENVIRONMENT REPORT SUMMARY")
        logger.info("=" * 60)

        # Count statuses
        packages = self.results["versions"].get("python_packages", {})
        pkg_ok = len([p for p in packages.values() if p["status"] == "✅"])
        pkg_warn = len([p for p in packages.values() if p["status"] == "⚠️"])
        pkg_miss = len([p for p in packages.values() if p["status"] == "❌"])

        keys = self.results.get("api_keys", {})
        keys_ok = len([k for k in keys.values() if k["status"] == "✅"])
        keys_miss = len([k for k in keys.values() if k["status"] == "❌"])

        logger.info("\n📦 Python Packages:")
        logger.info(f"  ✅ Up to date: {pkg_ok}")
        logger.info(f"  ⚠️  Outdated: {pkg_warn}")
        logger.info(f"  ❌ Missing: {pkg_miss}")

        logger.info("\n🔑 API Keys:")
        logger.info(f"  ✅ Valid: {keys_ok}")
        logger.info(f"  ❌ Missing/Invalid: {keys_miss}")

        gaps = self.results.get("gaps", [])
        if gaps:
            logger.info(f"\n⚠️  Total Gaps: {len(gaps)}")
            logger.info(
                f"  🔴 High severity: {len([g for g in gaps if g.get('severity') == 'high'])}"
            )
            logger.info(
                f"  🟡 Medium severity: {len([g for g in gaps if g.get('severity') == 'medium'])}"
            )
        else:
            logger.info("\n✅ No critical gaps!")

        # Save detailed report
        report_path = Path("environment_analysis.json")
        with open(report_path, "w") as f:
            json.dump(self.results, f, indent=2)

        logger.info(f"\n📁 Detailed report saved to: {report_path}")

        # Overall status
        if pkg_miss == 0 and keys_miss <= 2:
            logger.info("\n🎉 Environment is mostly ready!")
        else:
            logger.info("\n⚠️  Environment needs configuration")
            logger.info("Run the recommended actions above to complete setup")


async def main():
    """Main analysis runner."""
    analyzer = TechStackAnalyzer()
    await analyzer.run_full_analysis()

    return 0 if len(analyzer.results.get("gaps", [])) == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
