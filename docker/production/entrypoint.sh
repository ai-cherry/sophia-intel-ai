#!/bin/bash
set -e

# Default to code service if MCP_ROLE not set
MCP_ROLE=${MCP_ROLE:-code}

echo "Starting Sophia MCP service: $MCP_ROLE"

# Route to appropriate MCP server based on role
case "$MCP_ROLE" in
    "code")
        echo "Starting Code MCP Server..."
        cd /app && python -m mcp_servers.app --service=code
        ;;
    "context")
        echo "Starting Context MCP Server..."
        cd /app && python -m mcp_servers.app --service=context
        ;;
    "memory")
        echo "Starting Memory MCP Server..."
        cd /app && python -m mcp_servers.app --service=memory
        ;;
    "research")
        echo "Starting Research MCP Server..."
        cd /app && python -m mcp_servers.app --service=research
        ;;
    "business")
        echo "Starting Business MCP Server..."
        cd /app && python -m mcp_servers.app --service=business
        ;;
    *)
        echo "Unknown MCP_ROLE: $MCP_ROLE"
        echo "Valid roles: code, context, memory, research, business"
        exit 1
        ;;
esac

