#!/usr/bin/env python3
"""Test WebSocket MCP connection"""

import asyncio
import json
from datetime import datetime

import websockets


async def test_mcp_websocket():
    uri = "ws://localhost:8000/ws/mcp"

    try:
        async with websockets.connect(uri) as websocket:
            print(f"✅ Connected to MCP WebSocket: {uri}")

            # Listen for welcome message
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            print(f"📨 Welcome message: {welcome_data}")

            # Test memory store
            memory_message = {
                "type": "memory_store",
                "content": "WebSocket test from Claude Code - MCP Integration verification successful",
                "metadata": {
                    "source": "claude-code",
                    "test": "websocket_verification",
                    "timestamp": datetime.now().isoformat()
                },
                "source": "claude-websocket"
            }

            await websocket.send(json.dumps(memory_message))
            print("📤 Sent memory store message")

            # Wait for confirmation
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"📨 Memory store response: {response_data}")

            # Test memory search
            search_message = {
                "type": "memory_search",
                "query": "WebSocket test"
            }

            await websocket.send(json.dumps(search_message))
            print("📤 Sent search message")

            # Wait for search results
            search_response = await websocket.recv()
            search_data = json.loads(search_response)
            print(f"📨 Search response: {search_data}")

            # Test workspace sync
            workspace_message = {
                "type": "workspace_sync",
                "context": {
                    "current_project": "sophia-intel-ai-mcp-verified",
                    "active_files": ["mcp_verification_server.py", "test_websocket.py"],
                    "recent_changes": ["MCP WebSocket verification completed"]
                }
            }

            await websocket.send(json.dumps(workspace_message))
            print("📤 Sent workspace sync message")

            # Wait for sync confirmation
            sync_response = await websocket.recv()
            sync_data = json.loads(sync_response)
            print(f"📨 Workspace sync response: {sync_data}")

            print("\n🎉 MCP WebSocket verification completed successfully!")
            return True

    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_mcp_websocket())
    exit(0 if result else 1)
