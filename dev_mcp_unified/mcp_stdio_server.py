"""
Minimal MCP JSON‑RPC stdio server wrapper (requires `pip install mcp`).
This exposes our tools so Claude Desktop can auto‑discover them.

Usage:
  python3 -m dev_mcp_unified.mcp_stdio_server
"""
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except Exception as e:
    raise SystemExit("Install mcp: pip install mcp")

import asyncio
from dev_mcp_unified.tools.semantic_search import semantic_search
from dev_mcp_unified.tools.symbol_lookup import symbol_lookup
from dev_mcp_unified.tools.test_runner import run_tests


app = Server("mcp-unified")


@app.list_tools()
async def _list_tools():
    return [
        Tool(name="search", description="Search repository text", inputSchema={"type":"object","properties":{"query":{"type":"string"}},"required":["query"]}),
        Tool(name="symbols", description="List symbols in file", inputSchema={"type":"object","properties":{"file":{"type":"string"}},"required":["file"]}),
        Tool(name="tests", description="Run pytest", inputSchema={"type":"object","properties":{"path":{"type":"string","default":"."}}}),
    ]


@app.call_tool()
async def _call_tool(name: str, arguments: dict | None):
    arguments = arguments or {}
    if name == "search":
        res = semantic_search(arguments.get("query",""))
        return [TextContent(type="text", text=str(res)[:8000])]
    if name == "symbols":
        res = symbol_lookup(arguments.get("file"))
        return [TextContent(type="text", text=str(res)[:8000])]
    if name == "tests":
        log = "\n".join(run_tests(arguments.get("path",".")))
        return [TextContent(type="text", text=log[:8000])]
    return [TextContent(type="text", text=f"unknown tool: {name}")]


async def main():
    async with stdio_server() as (r, w):
        await app.run(r, w, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())

