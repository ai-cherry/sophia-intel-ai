#!/usr/bin/env python3
"""
Test script for Mem0 Bridge and Memory MCP
Tests the functionality of the enhanced memory system
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("memory_test")

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from memory.mem0_bridge import Mem0Bridge
except ImportError:
    logger.error(
        "Error: Could not import Mem0Bridge. Make sure memory/mem0_bridge.py exists."
    )
    sys.exit(1)


async def test_memory_bridge():
    """Test the Mem0Bridge functionality"""
    logger.info("Testing memory bridge...")

    # Initialize the memory bridge
    try:
        bridge = Mem0Bridge()
        logger.info("✅ Memory bridge initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize memory bridge: {str(e)}")
        return False

    # Test adding memories with different relevance scores
    memories = [
        {
            "agent_id": "artemis_test",
            "content": "Fixed a critical bug in the authentication system related to token expiration.",
            "relevance": 0.95,
            "metadata": {"type": "bugfix", "priority": "high"},
        },
        {
            "agent_id": "artemis_test",
            "content": "Added documentation for the memory system explaining how to configure Mem0 and LangChain integration.",
            "relevance": 0.85,
            "metadata": {"type": "documentation", "priority": "medium"},
        },
        {
            "agent_id": "artemis_test",
            "content": "Team meeting discussed project timeline and next sprint priorities.",
            "relevance": 0.65,
            "metadata": {"type": "meeting", "priority": "low"},
        },
    ]

    for memory in memories:
        try:
            success = await bridge.add(
                agent_id=memory["agent_id"],
                content=memory["content"],
                relevance=memory["relevance"],
                metadata=memory["metadata"],
            )
            if success:
                logger.info(f"✅ Added memory with relevance {memory['relevance']}")
            else:
                logger.error(
                    f"❌ Failed to add memory with relevance {memory['relevance']}"
                )
                return False
        except Exception as e:
            logger.error(f"❌ Error adding memory: {str(e)}")
            return False

    # Test retrieving memories with different queries
    queries = ["authentication bug", "memory system documentation", "meeting"]

    for query in queries:
        try:
            results = await bridge.retrieve(
                agent_id="artemis_test", query=query, limit=5, include_entities=True
            )

            logger.info(
                f"✅ Retrieved {len(results['merged_results'])} memories for query: {query}"
            )
            for i, result in enumerate(results["merged_results"]):
                logger.info(f"  {i+1}. Relevance: {result.get('relevance', 0):.2f}")
                logger.info(f"     Content: {result.get('content', '')[:50]}...")

            if results.get("related_entities"):
                logger.info(
                    f"✅ Found related entities: {', '.join(results['related_entities'])}"
                )

        except Exception as e:
            logger.error(f"❌ Error retrieving memories for query '{query}': {str(e)}")
            return False

    # Test offline summary
    try:
        contents = [m["content"] for m in memories]
        summary = await bridge.offline_summary(contents, "project status")
        logger.info(f"✅ Generated offline summary: {summary[:100]}...")
    except Exception as e:
        logger.error(f"❌ Error generating offline summary: {str(e)}")

    # Test memory stats
    try:
        stats = await bridge.get_stats("artemis_test")
        logger.info(f"✅ Memory stats: {json.dumps(stats, indent=2)}")
    except Exception as e:
        logger.error(f"❌ Error getting memory stats: {str(e)}")

    # Test pruning memories
    try:
        pruned = await bridge.prune("artemis_test", max_relevance=0.7)
        logger.info(f"✅ Pruned {pruned} memories with relevance < 0.7")
    except Exception as e:
        logger.error(f"❌ Error pruning memories: {str(e)}")

    # Cleanup - clear test memories
    try:
        success = await bridge.clear("artemis_test")
        if success:
            logger.info("✅ Cleared test memories")
        else:
            logger.error("❌ Failed to clear test memories")
    except Exception as e:
        logger.error(f"❌ Error clearing test memories: {str(e)}")

    return True


async def test_http_client():
    """Test the Memory MCP server using HTTP client"""
    import httpx

    logger.info("Testing Memory MCP server...")

    base_url = "http://localhost:8000"

    async with httpx.AsyncClient() as client:
        # Test health endpoint
        try:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                logger.info(f"✅ Health check: {response.json()}")
            else:
                logger.error(
                    f"❌ Health check failed: {response.status_code} {response.text}"
                )
                return False
        except Exception as e:
            logger.error(f"❌ Error connecting to MCP server: {str(e)}")
            logger.info(
                "   Is the server running? Start it with: python -m mcp_servers.memory_mcp"
            )
            return False

        # Test adding memory
        try:
            memory = {
                "agent_id": "http_test",
                "content": "Testing the Memory MCP server via HTTP",
                "relevance": 0.9,
                "metadata": {"type": "test", "timestamp": datetime.now().isoformat()},
            }

            response = await client.post(f"{base_url}/add", json=memory)
            if response.status_code == 200:
                logger.info(f"✅ Added memory via HTTP: {response.json()}")
            else:
                logger.error(
                    f"❌ Failed to add memory via HTTP: {response.status_code} {response.text}"
                )
                return False
        except Exception as e:
            logger.error(f"❌ Error adding memory via HTTP: {str(e)}")
            return False

        # Test retrieving memory
        try:
            query = {
                "agent_id": "http_test",
                "query": "test server",
                "limit": 5,
                "include_entities": True,
            }

            response = await client.post(f"{base_url}/retrieve", json=query)
            if response.status_code == 200:
                results = response.json()
                logger.info(
                    f"✅ Retrieved {len(results.get('merged_results', []))} memories via HTTP"
                )
            else:
                logger.error(
                    f"❌ Failed to retrieve memories via HTTP: {response.status_code} {response.text}"
                )
                return False
        except Exception as e:
            logger.error(f"❌ Error retrieving memories via HTTP: {str(e)}")
            return False

        # Test Continue.dev integration
        try:
            response = await client.get(
                f"{base_url}/continue/search?query=test&agent_id=http_test"
            )
            if response.status_code == 200:
                logger.info(f"✅ Continue.dev integration: {response.json()}")
            else:
                logger.error(
                    f"❌ Failed Continue.dev integration: {response.status_code} {response.text}"
                )
        except Exception as e:
            logger.error(f"❌ Error testing Continue.dev integration: {str(e)}")

        # Cleanup - clear test memories
        try:
            clear_request = {"agent_id": "http_test"}

            response = await client.post(f"{base_url}/clear", json=clear_request)
            if response.status_code == 200:
                logger.info(f"✅ Cleared test memories via HTTP: {response.json()}")
            else:
                logger.error(
                    f"❌ Failed to clear test memories via HTTP: {response.status_code} {response.text}"
                )
        except Exception as e:
            logger.error(f"❌ Error clearing test memories via HTTP: {str(e)}")

    return True


async def main():
    """Main test function"""
    logger.info("Starting memory system tests...")

    # Test Mem0 Bridge
    bridge_result = await test_memory_bridge()
    if bridge_result:
        logger.info("✅ Memory bridge tests completed successfully")
    else:
        logger.error("❌ Memory bridge tests failed")

    # Prompt to start MCP server if needed
    if input("\nDo you want to test the Memory MCP server? (y/n): ").lower() == "y":
        logger.info("Starting Memory MCP server test...")
        logger.info(
            "Note: Make sure the server is running with: python -m mcp_servers.memory_mcp"
        )

        if input("Is the Memory MCP server running? (y/n): ").lower() == "y":
            # Test HTTP client
            http_result = await test_http_client()
            if http_result:
                logger.info("✅ Memory MCP server tests completed successfully")
            else:
                logger.error("❌ Memory MCP server tests failed")
        else:
            logger.info("Skipping Memory MCP server tests")

    logger.info("Memory system tests completed")


if __name__ == "__main__":
    asyncio.run(main())
