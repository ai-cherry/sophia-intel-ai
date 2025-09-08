#!/usr/bin/env python3
"""Fixed MCP Server Validator"""

import importlib.util
from pathlib import Path


def find_mcp_servers():
    """Find all MCP servers with correct paths"""
    servers = []
    mcp_dir = Path("mcp_servers")

    # Look for directories with server.py
    for item in mcp_dir.iterdir():
        if item.is_dir():
            server_file = item / "server.py"
            if server_file.exists():
                servers.append(
                    {"name": item.name, "path": str(item), "server_file": str(server_file)}
                )

    # Also check for loose server files
    for item in mcp_dir.glob("*_server.py"):
        if item.is_file():
            servers.append(
                {
                    "name": item.stem.replace("_server", ""),
                    "path": str(mcp_dir),
                    "server_file": str(item),
                    "needs_restructure": True,
                }
            )

    return servers


def validate_server(server):
    """Validate a single server"""
    print(f"  Validating {server['name']}...", end=" ")

    try:
        spec = importlib.util.spec_from_file_location(
            f"mcp_{server['name']}", server["server_file"]
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Check for required attributes
        if hasattr(module, "app"):
            print("✅")
            return True
        else:
            print("❌ No 'app' object")
            return False
    except Exception as e:
        print(f"❌ {str(e)[:50]}")
        return False


if __name__ == "__main__":
    servers = find_mcp_servers()
    print(f"Found {len(servers)} servers")

    working = 0
    for server in servers:
        if "needs_restructure" in server:
            print(f"  {server['name']}: Needs restructuring")
        else:
            if validate_server(server):
                working += 1

    print(f"\nResult: {working}/{len(servers)} servers working")
