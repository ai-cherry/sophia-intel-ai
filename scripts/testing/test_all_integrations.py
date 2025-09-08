#!/usr/bin/env python3
"""
🧪 Sophia AI Fortress - Complete Integration Testing Suite
Tests all enterprise API integrations and services
"""

import asyncio
import json
import logging
import os
import sys
from typing import Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class IntegrationTester:
    """Comprehensive integration testing for all Sophia AI services"""

    def __init__(self):
        self.results = {}
        self.api_keys = {
            "GHCR_PAT": os.getenv("GHCR_PAT"),
            "LAMBDA_LABS_API_KEY": os.getenv("LAMBDA_LABS_API_KEY"),
            "HUGGINGFACE_API_TOKEN": os.getenv("HUGGINGFACE_API_TOKEN"),
            "PULUMI_API_TOKEN": os.getenv("PULUMI_API_TOKEN"),
            "PORTKEY_API_KEY": os.getenv("PORTKEY_API_KEY"),
            "NEON_API_TOKEN": os.getenv("NEON_API_TOKEN"),
            "VERCEL_API_TOKEN": os.getenv("VERCEL_API_TOKEN"),
            "MEM0_API_TOKEN": os.getenv("MEM0_API_TOKEN"),
            "N8N_API_TOKEN": os.getenv("N8N_API_TOKEN"),
            "ESTUARY_API_TOKEN": os.getenv("ESTUARY_API_TOKEN"),
            "QDRANT_API_KEY": os.getenv("QDRANT_API_KEY"),
            "OPENROUTER_API_KEY": os.getenv("OPENROUTER_API_KEY"),
            "REDIS_API_KEY": os.getenv("REDIS_API_KEY"),
            "LANGGRAPH_API_KEY": os.getenv("LANGGRAPH_API_KEY"),
            "AGNO_API_KEY": os.getenv("AGNO_API_KEY"),
            "DOCKER_ACCESS_TOKEN": os.getenv("DOCKER_ACCESS_TOKEN"),
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
            "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        }

    async def test_lambda_labs(self) -> Dict:
        """Test Lambda Labs GPU API connectivity"""
        try:
            import httpx

            if not self.api_keys["LAMBDA_LABS_API_KEY"]:
                return {"status": "skipped", "reason": "API key not set"}

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://cloud.lambdalabs.com/api/v1/instances",
                    auth=(self.api_keys["LAMBDA_LABS_API_KEY"], ""),
                )
                if response.status_code == 200:
                    instances = response.json()
                    return {
                        "status": "success",
                        "instances_count": len(instances.get("data", [])),
                        "message": "Lambda Labs API accessible",
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"HTTP {response.status_code}",
                    }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def test_qdrant(self) -> Dict:
        """Test Qdrant vector database connectivity"""
        try:
            from qdrant_client import QdrantClient

            if not self.api_keys["QDRANT_API_KEY"]:
                return {"status": "skipped", "reason": "API key not set"}

            client = QdrantClient(
                url="https://your-cluster.qdrant.io",  # Replace with actual URL
                api_key=self.api_keys["QDRANT_API_KEY"],
            )
            collections = client.get_collections()
            return {
                "status": "success",
                "collections_count": len(collections.collections),
                "message": "Qdrant API accessible",
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def test_portkey(self) -> Dict:
        """Test Portkey multi-model routing"""
        try:
            import httpx

            if not self.api_keys["PORTKEY_API_KEY"]:
                return {"status": "skipped", "reason": "API key not set"}

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.portkey.ai/v1/models",
                    headers={
                        "Authorization": f'Bearer {self.api_keys["PORTKEY_API_KEY"]}'
                    },
                )
                if response.status_code == 200:
                    models = response.json()
                    return {
                        "status": "success",
                        "models_count": len(models.get("data", [])),
                        "message": "Portkey API accessible",
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"HTTP {response.status_code}",
                    }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def test_openrouter(self) -> Dict:
        """Test OpenRouter API connectivity"""
        try:
            import httpx

            if not self.api_keys["OPENROUTER_API_KEY"]:
                return {"status": "skipped", "reason": "API key not set"}

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers={
                        "Authorization": f'Bearer {self.api_keys["OPENROUTER_API_KEY"]}'
                    },
                )
                if response.status_code == 200:
                    models = response.json()
                    return {
                        "status": "success",
                        "models_count": len(models.get("data", [])),
                        "message": "OpenRouter API accessible",
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"HTTP {response.status_code}",
                    }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def test_huggingface(self) -> Dict:
        """Test HuggingFace Hub connectivity"""
        try:
            from huggingface_hub import HfApi

            if not self.api_keys["HUGGINGFACE_API_TOKEN"]:
                return {"status": "skipped", "reason": "API key not set"}

            api = HfApi(token=self.api_keys["HUGGINGFACE_API_TOKEN"])
            user_info = api.whoami()
            return {
                "status": "success",
                "user": user_info.get("name", "Unknown"),
                "message": "HuggingFace Hub accessible",
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def test_redis_connection(self) -> Dict:
        """Test Redis connectivity"""
        try:
            import redis

            redis_url = os.getenv("REDIS_URL", "${REDIS_URL}")
            r = redis.from_url(redis_url)
            r.ping()
            return {"status": "success", "message": "Redis connection successful"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def test_postgres_connection(self) -> Dict:
        """Test PostgreSQL connectivity"""
        try:
            import psycopg2

            db_url = os.getenv("DATABASE_URL", "${DATABASE_URL}:5432/sophia")
            conn = psycopg2.connect(db_url)
            conn.close()
            return {"status": "success", "message": "PostgreSQL connection successful"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def test_docker_connectivity(self) -> Dict:
        """Test Docker daemon connectivity"""
        try:
            import docker

            client = docker.from_env()
            info = client.info()
            return {
                "status": "success",
                "docker_version": info.get("ServerVersion", "Unknown"),
                "containers_running": info.get("ContainersRunning", 0),
                "message": "Docker daemon accessible",
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def test_api_keys_presence(self) -> Dict:
        """Test which API keys are present"""
        present_keys = []
        missing_keys = []

        for key, value in self.api_keys.items():
            if value and value.strip():
                present_keys.append(key)
            else:
                missing_keys.append(key)

        return {
            "status": "info",
            "present_keys": present_keys,
            "missing_keys": missing_keys,
            "present_count": len(present_keys),
            "total_count": len(self.api_keys),
        }

    async def run_all_tests(self) -> Dict:
        """Run comprehensive integration tests"""
        print("🧪 Sophia AI Fortress - Integration Testing Suite")
        print("=" * 50)

        # Test API keys presence
        print("\n🔑 Testing API Keys Presence...")
        self.results["api_keys"] = self.test_api_keys_presence()
        print(
            f"✅ {self.results['api_keys']['present_count']}/{self.results['api_keys']['total_count']} API keys present"
        )

        # Test core services
        tests = [
            ("lambda_labs", self.test_lambda_labs),
            ("qdrant", self.test_qdrant),
            ("portkey", self.test_portkey),
            ("openrouter", self.test_openrouter),
            ("huggingface", self.test_huggingface),
            ("redis", self.test_redis_connection),
            ("postgres", self.test_postgres_connection),
            ("docker", self.test_docker_connectivity),
        ]

        for test_name, test_func in tests:
            print(f"\n🔍 Testing {test_name.replace('_', ' ').title()}...")
            try:
                result = await test_func()
                self.results[test_name] = result

                if result["status"] == "success":
                    print(f"✅ {result['message']}")
                elif result["status"] == "skipped":
                    print(f"⏭️ Skipped: {result['reason']}")
                else:
                    print(f"❌ Failed: {result['message']}")
            except Exception as e:
                self.results[test_name] = {"status": "error", "message": str(e)}
                print(f"❌ Error: {str(e)}")

        return self.results

    def generate_report(self) -> str:
        """Generate comprehensive test report"""
        successful_tests = sum(
            1 for r in self.results.values() if r.get("status") == "success"
        )
        total_tests = len(self.results) - 1  # Exclude api_keys from count

        report = f"""
🏰 Sophia AI Fortress - Integration Test Report
============================================

📊 SUMMARY:
- Tests Passed: {successful_tests}/{total_tests}
- API Keys Present: {self.results['api_keys']['present_count']}/{self.results['api_keys']['total_count']}
- Overall Status: {'🎉 EXCELLENT' if successful_tests >= total_tests * 0.8 else '⚠️ NEEDS ATTENTION'}

🔑 API KEYS STATUS:
Present: {', '.join(self.results['api_keys']['present_keys'])}
Missing: {', '.join(self.results['api_keys']['missing_keys']) if self.results['api_keys']['missing_keys'] else 'None'}

📋 DETAILED RESULTS:
"""

        for test_name, result in self.results.items():
            if test_name == "api_keys":
                continue

            status_icon = {"success": "✅", "error": "❌", "skipped": "⏭️"}.get(
                result["status"], "❓"
            )

            report += f"{status_icon} {test_name.replace('_', ' ').title()}: {result['message']}\n"

        report += """
💡 RECOMMENDATIONS:
- Set missing API keys in GitHub Codespaces secrets
- Ensure all services are properly configured
- Check network connectivity for failed tests
- Review logs for detailed error information

🚀 NEXT STEPS:
- Fix any failed integrations
- Test MCP servers: python scripts/validate_mcp_servers.py
- Start backend: python backend/main.py
- Launch frontend: cd frontend && npm run dev
"""

        return report


async def main():
    """Main test execution"""
    tester = IntegrationTester()
    results = await tester.run_all_tests()

    # Generate and save report
    report = tester.generate_report()
    print(report)

    # Save results to file
    with open("logs/integration_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    with open("logs/integration_test_report.md", "w") as f:
        f.write(report)

    print("\n📄 Detailed results saved to:")
    print("   - logs/integration_test_results.json")
    print("   - logs/integration_test_report.md")

    # Exit with appropriate code
    successful_tests = sum(1 for r in results.values() if r.get("status") == "success")
    total_tests = len(results) - 1  # Exclude api_keys

    if successful_tests >= total_tests * 0.8:
        print(
            f"\n🎉 Integration testing PASSED! ({successful_tests}/{total_tests} tests successful)"
        )
        sys.exit(0)
    else:
        print(
            f"\n⚠️ Integration testing needs attention. ({successful_tests}/{total_tests} tests successful)"
        )
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
