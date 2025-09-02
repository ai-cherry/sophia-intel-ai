"""
Production MCP Bridge for Swarm Integration
Connects AI agent swarms to MCP server for code review and quality checks
"""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

import httpx

logger = logging.getLogger(__name__)

class ReviewType(Enum):
    CODE_REVIEW = "code-review"
    QUALITY_CHECK = "quality-check"
    SECURITY_SCAN = "security-scan"

@dataclass
class MCPConfig:
    """MCP Server Configuration"""
    host: str = "localhost"
    port: int = 8003
    timeout: int = 30
    retry_count: int = 3

    @property
    def base_url(self):
        return f"http://{self.host}:{self.port}"

class ProductionMCPBridge:
    """Bridge between AI Swarm and MCP Server"""

    def __init__(self, config: MCPConfig | None = None):
        self.config = config or MCPConfig()
        self.client = httpx.AsyncClient(
            timeout=self.config.timeout,
            limits=httpx.Limits(max_keepalive_connections=10)
        )

    async def health_check(self) -> bool:
        """Check if MCP server is healthy"""
        try:
            response = await self.client.get(f"{self.config.base_url}/health")
            data = response.json()
            return data.get("status") == "healthy"
        except Exception as e:
            logger.error(f"MCP health check failed: {e}")
            return False

    async def code_review(self, code: str, language: str = "python") -> dict[str, Any]:
        """Send code for review to MCP server"""
        try:
            response = await self.client.post(
                f"{self.config.base_url}/code-review",
                json={
                    "code": code,
                    "language": language,
                    "model": "x-ai/grok-code-fast-1"  # Use approved model
                }
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Code review failed: {response.status_code}")
                return {"error": f"Review failed: {response.status_code}"}

        except Exception as e:
            logger.error(f"Code review error: {e}")
            return {"error": str(e)}

    async def quality_check(self, code: str, metrics: list[str] = None) -> dict[str, Any]:
        """Perform quality check on code"""
        metrics = metrics or ["complexity", "maintainability", "testability"]

        try:
            response = await self.client.post(
                f"{self.config.base_url}/quality-check",
                json={
                    "code": code,
                    "metrics": metrics,
                    "model": "qwen/qwen3-30b-a3b"  # Use approved model
                }
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Quality check failed: {response.status_code}"}

        except Exception as e:
            logger.error(f"Quality check error: {e}")
            return {"error": str(e)}

    async def swarm_request(self, task: str, agents: list[str], context: dict[str, Any]) -> dict[str, Any]:
        """Send task to swarm through MCP"""
        try:
            response = await self.client.post(
                f"{self.config.base_url}/swarm/execute",
                json={
                    "task": task,
                    "agents": agents,
                    "context": context,
                    "model": "openai/gpt-5"  # Use approved premium model
                }
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Swarm execution failed: {response.status_code}"}

        except Exception as e:
            logger.error(f"Swarm request error: {e}")
            return {"error": str(e)}

    async def get_swarm_status(self) -> dict[str, Any]:
        """Get current swarm status"""
        try:
            response = await self.client.get(f"{self.config.base_url}/swarm/status")
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get swarm status: {e}")
            return {"error": str(e), "active_agents": 0}

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

# Singleton instance for global use
_bridge_instance: ProductionMCPBridge | None = None

def get_mcp_bridge(config: MCPConfig | None = None) -> ProductionMCPBridge:
    """Get or create MCP bridge instance"""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = ProductionMCPBridge(config)
    return _bridge_instance

async def test_bridge():
    """Test MCP bridge connectivity"""
    bridge = get_mcp_bridge()

    # Test health check
    is_healthy = await bridge.health_check()
    print(f"MCP Server Health: {'✅ Healthy' if is_healthy else '❌ Unhealthy'}")

    if is_healthy:
        # Test code review
        test_code = """
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
"""

        review_result = await bridge.code_review(test_code, "python")
        print(f"Code Review Result: {review_result}")

        # Test swarm status
        status = await bridge.get_swarm_status()
        print(f"Swarm Status: {status}")

    await bridge.close()

if __name__ == "__main__":
    asyncio.run(test_bridge())
