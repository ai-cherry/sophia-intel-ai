#!/usr/bin/env python3
"""
Test script for MCP improvements including:
- Enhanced MCP Server with connection pooling
- Integrated Tool Manager with shared context
- Enhanced Tools with error handling
- Observability System
- Elite Portkey configuration
"""

import asyncio
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.elite_portkey_config import EliteAgentConfig, ElitePortkeyGateway
from app.memory.enhanced_mcp_server import EnhancedMCPServer, MCPServerConfig
from app.observability.metrics_collector import ObservabilitySystem
from app.tools.enhanced_tools import EnhancedCodeSearch, EnhancedGitOps, EnhancedReadFile
from app.tools.integrated_manager import IntegratedToolManager


async def test_enhanced_mcp_server():
    """Test enhanced MCP server with connection pooling."""
    print("\n🧪 Testing Enhanced MCP Server...")
    print("=" * 60)

    config = MCPServerConfig(
        connection_pool_size=5,
        retry_attempts=3,
        enable_metrics=True
    )

    server = EnhancedMCPServer(config)

    try:
        # Initialize pool
        await server.initialize_pool()
        print("✅ Connection pool initialized")

        # Health check
        health = await server.health_check()
        print(f"✅ Health check: {health}")

        # Get metrics
        metrics = await server.get_metrics()
        print(f"✅ Metrics: Available connections = {metrics['available_connections']}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        await server.close()

async def test_integrated_tool_manager():
    """Test integrated tool manager with shared context."""
    print("\n🧪 Testing Integrated Tool Manager...")
    print("=" * 60)

    manager = IntegratedToolManager()

    try:
        # Create context
        context = await manager.create_context(
            "test_session",
            "Test task for validation"
        )
        print(f"✅ Context created: {context.session_id}")

        # Execute a tool
        result = await manager.execute_tool(
            "test_session",
            "git_status"
        )
        print(f"✅ Tool executed: {result.tool_name} - Success: {result.success}")

        # Get context summary
        summary = await manager.get_context_summary("test_session")
        print(f"✅ Context summary: {summary['execution_count']} executions")

        # Get metrics
        metrics = manager.get_metrics()
        print(f"✅ Manager metrics: {metrics['executions']} total executions")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_enhanced_tools():
    """Test enhanced tools with error handling."""
    print("\n🧪 Testing Enhanced Tools...")
    print("=" * 60)

    try:
        # Test EnhancedReadFile
        reader = EnhancedReadFile()
        content = await reader.run("README.md")
        print(f"✅ EnhancedReadFile: Read {len(content)} characters")

        # Test EnhancedCodeSearch
        searcher = EnhancedCodeSearch()
        results = await searcher.run(
            query="async def",
            file_type="py",
            context_lines=1
        )
        print(f"✅ EnhancedCodeSearch: Found {len(results)} matches")

        # Test EnhancedGitOps
        git = EnhancedGitOps()
        status = await git.run("status")
        print(f"✅ EnhancedGitOps: Branch = {status.get('branch', 'unknown')}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_observability_system():
    """Test observability system."""
    print("\n🧪 Testing Observability System...")
    print("=" * 60)

    observability = ObservabilitySystem()

    try:
        # Start observability
        await observability.start()
        print("✅ Observability system started")

        # Simulate tool execution with monitoring
        with observability.tool_execution_context("test_tool") as ctx:
            await asyncio.sleep(0.1)  # Simulate work

        print("✅ Tool execution monitored")

        # Record some metrics
        observability.metrics.record("test_metric", 42.0)
        observability.metrics.increment("test_counter", 1.0)
        print("✅ Metrics recorded")

        # Get dashboard data
        dashboard = observability.get_dashboard_data()
        print(f"✅ Dashboard: {len(dashboard['metrics'])} metrics tracked")

        # Export metrics
        prometheus_export = observability.export_metrics("prometheus")
        print(f"✅ Prometheus export: {len(prometheus_export.splitlines())} lines")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        await observability.stop()

async def test_elite_portkey():
    """Test elite Portkey configuration."""
    print("\n🧪 Testing Elite Portkey Configuration...")
    print("=" * 60)

    try:
        # Show configured models
        print("📋 Elite Models Configured:")
        for role, model in EliteAgentConfig.MODELS.items():
            print(f"  {role:20} -> {model}")

        # Create gateway
        gateway = ElitePortkeyGateway()
        print("✅ Elite gateway initialized")

        # Test model selection
        from app.elite_portkey_config import EliteOptimizations
        opt = EliteOptimizations()

        tier = opt.get_model_tier('openai/gpt-5')
        print(f"✅ Model tier detection: GPT-5 = {tier}")

        # Test routing strategy
        from app.elite_portkey_config import EliteRoutingStrategy
        routing = EliteRoutingStrategy()

        route = routing.get_optimal_route('complex_task', 0.9)
        print(f"✅ Routing strategy: Complex task -> {route['primary']}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def main():
    """Run all tests."""
    print("🚀 MCP IMPROVEMENTS TEST SUITE")
    print("=" * 60)

    tests = [
        ("Enhanced MCP Server", test_enhanced_mcp_server),
        ("Integrated Tool Manager", test_integrated_tool_manager),
        ("Enhanced Tools", test_enhanced_tools),
        ("Observability System", test_observability_system),
        ("Elite Portkey Config", test_elite_portkey)
    ]

    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} failed with exception: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS:")
    print("=" * 60)

    passed = 0
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name:30} {status}")
        if result:
            passed += 1

    print("=" * 60)
    print(f"🎯 Total: {passed}/{len(tests)} tests passed")

    if passed == len(tests):
        print("🎉 ALL TESTS PASSED! MCP improvements are working!")
        return 0
    else:
        print("⚠️ Some tests failed. Review the errors above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
