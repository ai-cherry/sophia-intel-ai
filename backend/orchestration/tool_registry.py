"\nTool Registry for Sophia AI Orchestration\nManages MCP servers and other tool integrations\n"

import asyncio
import logging
import os
from abc import abstractmethod
from datetime import datetime
from typing import Any, Protocol

import httpx

logger = logging.getLogger(__name__)


class Tool(Protocol):
    """Protocol for all tools"""

    name: str
    description: str

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]: ...


class MCPToolAdapter:
    """Adapter for MCP servers"""

    def __init__(self, name: str, host: str, port: int, description: str = ""):
        self.name = name
        self.host = host
        self.port = port
        self.description = description or f"MCP server: {name}"
        self.base_url = f"http://{host}:{port}"
        self.client = httpx.AsyncClient(timeout=30.0)

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool on the MCP server"""
        tool_name = params.get("tool", params.get("action", "default"))
        tool_params = params.get("params", params)
        try:
            response = await self.client.post(
                f"{self.base_url}/call_tool",
                json={"tool": tool_name, "params": tool_params},
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"MCP server error for {self.name}: {e}")
            return {"error": str(e), "status": "failed", "server": self.name}
        except Exception as e:
            logger.error(f"Unexpected error calling {self.name}: {e}")
            return {"error": str(e), "status": "failed", "server": self.name}

    async def health_check(self) -> bool:
        """Check if MCP server is healthy"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except:
            return False

    async def list_tools(self) -> list[dict[str, Any]]:
        """List available tools on the MCP server"""
        try:
            response = await self.client.post(
                f"{self.base_url}/call_tool", json={"tool": "list_tools", "params": {}}
            )
            response.raise_for_status()
            return response.json().get("tools", [])
        except Exception as e:
            logger.error(f"Failed to list tools for {self.name}: {e}")
            return []


class DirectAPITool:
    """Base class for direct API integrations"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute the tool"""


class CodeSearchTool(DirectAPITool):
    """Direct code search implementation"""

    def __init__(self):
        super().__init__(
            name="code_search_direct",
            description="Search codebase using direct file system access",
        )

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute code search"""
        params.get("query", "")
        params.get("target_directories", [])
        return {
            "status": "success",
            "results": [],
            "message": "Direct code search not yet implemented",
        }


class GitTool(DirectAPITool):
    """Git operations tool"""

    def __init__(self):
        super().__init__(name="git", description="Execute git operations")

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute git command"""
        command = params.get("command", "")
        args = params.get("args", [])
        allowed_commands = ["status", "diff", "log", "branch", "show"]
        if command not in allowed_commands:
            return {"status": "error", "error": f"Command '{command}' not allowed"}
        import subprocess

        try:
            result = subprocess.run(
                ["git", command] + args, capture_output=True, text=True, timeout=10
            )
            return {
                "status": "success",
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None,
                "return_code": result.returncode,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


class ToolRegistry:
    """Central registry for all tools"""

    def __init__(self):
        self.tools: dict[str, Tool] = {}
        self.execution_history: list[dict[str, Any]] = []
        self._initialized = False

    async def initialize(self):
        """Initialize and register all tools"""
        if self._initialized:
            return
        mcp_servers = [
            (
                "code_search",
                os.getenv("MCP_HOST", "mcp-server"),
                9001,
                "Search and analyze codebase",
            ),
            (
                "ai_memory",
                os.getenv("MCP_HOST", "mcp-server"),
                9002,
                "AI memory and context storage",
            ),
            ("github", os.getenv("MCP_HOST", "mcp-server"), 9003, "GitHub operations"),
            (
                "linear",
                os.getenv("MCP_HOST", "mcp-server"),
                9004,
                "Linear project management",
            ),
            (
                "notion",
                os.getenv("MCP_HOST", "mcp-server"),
                9005,
                "Notion documentation",
            ),
            ("slack", os.getenv("MCP_HOST", "mcp-server"), 9006, "Slack communication"),
            (
                "asana",
                os.getenv("MCP_HOST", "mcp-server"),
                9007,
                "Asana task management",
            ),
            ("hubspot", os.getenv("MCP_HOST", "mcp-server"), 9008, "HubSpot CRM"),
            ("openrouter", "mcp-server", 9013, "LLM routing and optimization"),
        ]
        for name, host, port, desc in mcp_servers:
            adapter = MCPToolAdapter(name, host, port, desc)
            self.register_tool(adapter)
        self.register_tool(CodeSearchTool())
        self.register_tool(GitTool())
        await self._health_check_all()
        self._initialized = True
        logger.info(f"Tool registry initialized with {len(self.tools)} tools")

    def register_tool(self, tool: Tool):
        """Register a tool"""
        self.tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")

    async def execute_tool(self, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool and track usage"""
        if tool_name not in self.tools:
            return {
                "status": "error",
                "error": f"Tool '{tool_name}' not found",
                "available_tools": list(self.tools.keys()),
            }
        tool = self.tools[tool_name]
        start_time = datetime.now()
        try:
            result = await tool.execute(params)
            execution_record = {
                "tool": tool_name,
                "params": params,
                "result": result,
                "duration_ms": (datetime.now() - start_time).total_seconds() * 1000,
                "timestamp": start_time.isoformat(),
                "success": result.get("status") != "error",
            }
            self.execution_history.append(execution_record)
            logger.info(f"Executed tool '{tool_name}' in {execution_record['duration_ms']:.2f}ms")
            return result
        except Exception as e:
            logger.error(f"Tool execution failed for '{tool_name}': {e}")
            error_result = {"status": "error", "error": str(e), "tool": tool_name}
            self.execution_history.append(
                {
                    "tool": tool_name,
                    "params": params,
                    "result": error_result,
                    "duration_ms": (datetime.now() - start_time).total_seconds() * 1000,
                    "timestamp": start_time.isoformat(),
                    "success": False,
                }
            )
            return error_result

    async def execute_parallel(self, executions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Execute multiple tools in parallel"""
        tasks = [self.execute_tool(exec["tool"], exec.get("params", {})) for exec in executions]
        return await asyncio.gather(*tasks)

    async def _health_check_all(self):
        """Health check all MCP servers"""
        health_results = {}
        for name, tool in self.tools.items():
            if isinstance(tool, MCPToolAdapter):
                health_results[name] = await tool.health_check()
        healthy = sum(1 for h in health_results.values() if h)
        total = len(health_results)
        logger.info(f"MCP server health: {healthy}/{total} servers healthy")
        if healthy < total:
            unhealthy = [name for name, health in health_results.items() if not health]
            logger.warning(f"Unhealthy MCP servers: {unhealthy}")

    def get_tool_info(self, tool_name: str) -> dict[str, Any] | None:
        """Get information about a tool"""
        if tool_name not in self.tools:
            return None
        tool = self.tools[tool_name]
        return {
            "name": tool.name,
            "description": tool.description,
            "type": type(tool).__name__,
            "available": True,
        }

    def list_tools(self) -> list[dict[str, Any]]:
        """List all available tools"""
        return [
            info
            for info in (self.get_tool_info(name) for name in self.tools.keys())
            if info is not None
        ]

    def get_execution_stats(self) -> dict[str, Any]:
        """Get execution statistics"""
        if not self.execution_history:
            return {
                "total_executions": 0,
                "success_rate": 0,
                "average_duration_ms": 0,
                "by_tool": {},
            }
        total = len(self.execution_history)
        successful = sum(1 for e in self.execution_history if e["success"])
        by_tool = {}
        for exec in self.execution_history:
            tool = exec["tool"]
            if tool not in by_tool:
                by_tool[tool] = {"count": 0, "success": 0, "total_duration_ms": 0}
            by_tool[tool]["count"] += 1
            if exec["success"]:
                by_tool[tool]["success"] += 1
            by_tool[tool]["total_duration_ms"] += exec["duration_ms"]
        for tool_stats in by_tool.values():
            tool_stats["success_rate"] = tool_stats["success"] / tool_stats["count"]
            tool_stats["average_duration_ms"] = (
                tool_stats["total_duration_ms"] / tool_stats["count"]
            )
        return {
            "total_executions": total,
            "success_rate": successful / total if total > 0 else 0,
            "average_duration_ms": (
                sum(e["duration_ms"] for e in self.execution_history) / total if total > 0 else 0
            ),
            "by_tool": by_tool,
        }
