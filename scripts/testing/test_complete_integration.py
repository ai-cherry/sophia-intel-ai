#!/usr/bin/env python3
"""
Comprehensive Integration Test Script
Tests Portkey LLM routing and Vector Database connections
"""

import json
import os
import sys
from datetime import datetime
from typing import Any, Dict

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging

from app.core.portkey_config import AgentRole, ModelProvider, portkey_manager
from app.core.vector_db_config import VectorDBType, vector_db_manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def test_portkey_providers():
    """Test Portkey provider connections"""
    print_header("TESTING PORTKEY PROVIDERS")

    results = {}
    test_providers = [
        (ModelProvider.OPENAI, "gpt-3.5-turbo"),
        (ModelProvider.ANTHROPIC, "claude-3-haiku-20240307"),
        (ModelProvider.DEEPSEEK, "deepseek-chat"),
        (ModelProvider.MISTRAL, "mistral-medium"),
        (ModelProvider.GROQ, "mixtral-8x7b-32768"),
    ]

    for provider, model in test_providers:
        print(f"\nTesting {provider.value} with {model}...", end=" ")
        try:
            client = portkey_manager.get_client_for_provider(provider, model=model)
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": "Say 'connected' in one word"}], max_tokens=10
            )
            if response and response.choices:
                print(f"✓ Success - Response: {response.choices[0].message.content}")
                results[provider.value] = {"status": "success", "model": model}
            else:
                print("✗ Failed - No response")
                results[provider.value] = {"status": "failed", "error": "No response"}
        except Exception as e:
            print(f"✗ Failed - {str(e)[:50]}")
            results[provider.value] = {"status": "failed", "error": str(e)[:100]}

    return results


def test_vector_databases():
    """Test vector database connections"""
    print_header("TESTING VECTOR DATABASES")

    results = vector_db_manager.test_all_connections()

    for db, connected in results.items():
        status = "✓ Connected" if connected else "✗ Not Connected"
        print(f"\n{db.upper()}: {status}")

    return results


def test_vector_operations():
    """Test vector database operations"""
    print_header("TESTING VECTOR DB OPERATIONS")

    test_vector = [0.1] * 1536  # OpenAI embedding dimension
    test_metadata = {
        "content": "Test content for vector database",
        "timestamp": datetime.now().isoformat(),
        "source": "integration_test",
    }

    results = {}

    # Test Qdrant operations
    print("\n[Qdrant Operations]")
    try:
        # Create collection if needed
        vector_db_manager.create_collection(VectorDBType.QDRANT, "test_collection")
        print("  ✓ Collection created/exists")

        # Store vector
        success = vector_db_manager.store_vector(
            VectorDBType.QDRANT, test_vector, test_metadata, "test_collection"
        )
        if success:
            print("  ✓ Vector stored")

            # Search vectors
            search_results = vector_db_manager.search_vectors(
                VectorDBType.QDRANT, test_vector, top_k=1, collection_name="test_collection"
            )
            if search_results:
                print(f"  ✓ Vector search successful (found {len(search_results)} results)")
            else:
                print("  ✗ Vector search failed")
        else:
            print("  ✗ Failed to store vector")

        results["qdrant"] = {"status": "success" if success else "failed"}
    except Exception as e:
        print(f"  ✗ Error: {str(e)[:100]}")
        results["qdrant"] = {"status": "failed", "error": str(e)[:100]}

    # Test Redis operations
    print("\n[Redis Operations]")
    try:
        client = vector_db_manager.get_client(VectorDBType.REDIS)
        if client:
            # Store test data
            client.set("test:key", "test_value")
            value = client.get("test:key")
            if value == "test_value":
                print("  ✓ Redis read/write successful")
                results["redis"] = {"status": "success"}
            else:
                print("  ✗ Redis read/write failed")
                results["redis"] = {"status": "failed"}
        else:
            print("  ✗ Redis client not available")
            results["redis"] = {"status": "unavailable"}
    except Exception as e:
        print(f"  ✗ Error: {str(e)[:100]}")
        results["redis"] = {"status": "failed", "error": str(e)[:100]}

    return results


def test_agent_role_routing():
    """Test agent role-based routing"""
    print_header("TESTING AGENT ROLE ROUTING")

    results = {}
    test_cases = [
        (AgentRole.CREATIVE, "Generate a creative name for an AI assistant"),
        (AgentRole.CODING, "Write a Python function to calculate factorial"),
        (AgentRole.ANALYTICAL, "Analyze the pros and cons of microservices"),
    ]

    for role, prompt in test_cases:
        print(f"\nTesting {role.value} role...", end=" ")
        try:
            client = portkey_manager.get_client_for_role(role, temperature=0.7)
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}], max_tokens=100
            )
            if response and response.choices:
                print("✓ Success")
                results[role.value] = {
                    "status": "success",
                    "response_preview": response.choices[0].message.content[:50] + "...",
                }
            else:
                print("✗ No response")
                results[role.value] = {"status": "failed", "error": "No response"}
        except Exception as e:
            print(f"✗ Failed - {str(e)[:50]}")
            results[role.value] = {"status": "failed", "error": str(e)[:100]}

    return results


def test_factory_integration():
    """Test factory integration with Portkey"""
    print_header("TESTING FACTORY INTEGRATION")

    try:
        from app.artemis.unified_factory import artemis_unified_factory

        # Get factory status
        status = artemis_unified_factory.get_status()
        print("\nArtemis Factory Status:")
        print(f"  Domain: {status.get('domain', 'Unknown')}")
        print(f"  Active Tasks: {status.get('active_tasks', 0)}")
        print(f"  Max Concurrent: {status.get('max_concurrent_tasks', 0)}")
        print(f"  Agents Available: {len(status.get('agent_templates', {}))}")

        # Test agent creation with Portkey
        agent = artemis_unified_factory.create_agent(
            role="code_reviewer", personality="tactical_precise"
        )

        if agent:
            print("\n✓ Agent created successfully:")
            print(f"  ID: {agent.id}")
            print(f"  Role: {agent.role}")
            print(f"  Virtual Key: {agent.virtual_key[:20]}...")
            return {"status": "success", "agent_id": agent.id}
        else:
            print("\n✗ Failed to create agent")
            return {"status": "failed"}

    except Exception as e:
        print(f"\n✗ Factory integration error: {str(e)[:100]}")
        return {"status": "failed", "error": str(e)[:100]}


def generate_integration_report(all_results: Dict[str, Any]):
    """Generate comprehensive integration report"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "test_results": all_results,
        "summary": {
            "portkey_providers": sum(
                1
                for r in all_results.get("portkey_providers", {}).values()
                if r.get("status") == "success"
            ),
            "vector_databases": sum(
                1 for connected in all_results.get("vector_databases", {}).values() if connected
            ),
            "vector_operations": sum(
                1
                for r in all_results.get("vector_operations", {}).values()
                if r.get("status") == "success"
            ),
            "agent_roles": sum(
                1
                for r in all_results.get("agent_roles", {}).values()
                if r.get("status") == "success"
            ),
            "factory_integration": (
                "✓"
                if all_results.get("factory_integration", {}).get("status") == "success"
                else "✗"
            ),
        },
    }

    # Save report
    report_file = f"integration_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n\nReport saved to: {report_file}")
    return report


def main():
    """Main test execution"""
    print_header("COMPREHENSIVE INTEGRATION TEST SUITE")
    print("\nThis will test all Portkey and Vector Database integrations")

    all_results = {}

    # Test 1: Portkey Providers
    print("\n[1/5] Testing Portkey Providers...")
    all_results["portkey_providers"] = test_portkey_providers()

    # Test 2: Vector Databases
    print("\n[2/5] Testing Vector Database Connections...")
    all_results["vector_databases"] = test_vector_databases()

    # Test 3: Vector Operations
    print("\n[3/5] Testing Vector Database Operations...")
    all_results["vector_operations"] = test_vector_operations()

    # Test 4: Agent Role Routing
    print("\n[4/5] Testing Agent Role Routing...")
    all_results["agent_roles"] = test_agent_role_routing()

    # Test 5: Factory Integration
    print("\n[5/5] Testing Factory Integration...")
    all_results["factory_integration"] = test_factory_integration()

    # Generate Report
    report = generate_integration_report(all_results)

    # Print Summary
    print_header("TEST SUMMARY")
    summary = report["summary"]
    print(f"\nPortkey Providers: {summary['portkey_providers']}/5 working")
    print(f"Vector Databases: {summary['vector_databases']}/4 connected")
    print(f"Vector Operations: {summary['vector_operations']}/2 successful")
    print(f"Agent Roles: {summary['agent_roles']}/3 working")
    print(f"Factory Integration: {summary['factory_integration']}")

    # Overall assessment
    total_tests = 5 + 4 + 2 + 3 + 1
    total_passed = (
        summary["portkey_providers"]
        + summary["vector_databases"]
        + summary["vector_operations"]
        + summary["agent_roles"]
        + (1 if summary["factory_integration"] == "✓" else 0)
    )

    success_rate = (total_passed / total_tests) * 100

    print(f"\n{'='*60}")
    print(f"Overall Success Rate: {success_rate:.1f}% ({total_passed}/{total_tests} tests passed)")

    if success_rate >= 80:
        print("✓ Integration tests PASSED")
        return 0
    elif success_rate >= 60:
        print("⚠ Integration tests PARTIALLY PASSED")
        return 1
    else:
        print("✗ Integration tests FAILED")
        return 2


if __name__ == "__main__":
    exit(main())
