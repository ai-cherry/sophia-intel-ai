#!/usr/bin/env python3
"""
Test script for Portkey integration
Validates all virtual keys and provider connections
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
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
def test_provider_configuration():
    """Test provider configuration setup"""
    print("\n" + "=" * 60)
    print("TESTING PROVIDER CONFIGURATION")
    print("=" * 60)
    status = portkey_manager.get_provider_status()
    for provider, config in status.items():
        print(f"\n{provider.upper()}:")
        print(f"  Virtual Key: {config['virtual_key']}")
        print(
            f"  Models: {', '.join(config['models']) if config['models'] else 'None'}"
        )
        print(
            f"  Fallbacks: {', '.join(config['fallback_providers']) if config['fallback_providers'] else 'None'}"
        )
        print(f"  Configured: {'✓' if config['configured'] else '✗'}")
    return status
def test_individual_providers():
    """Test each provider connection individually"""
    print("\n" + "=" * 60)
    print("TESTING INDIVIDUAL PROVIDER CONNECTIONS")
    print("=" * 60)
    results = {}
    providers_to_test = [
        ModelProvider.OPENAI,
        ModelProvider.ANTHROPIC,
        ModelProvider.DEEPSEEK,
        ModelProvider.PERPLEXITY,
        ModelProvider.GROQ,
        ModelProvider.MISTRAL,
        ModelProvider.GEMINI,
        ModelProvider.TOGETHER,
        ModelProvider.OPENROUTER,
    ]
    for provider in providers_to_test:
        print(f"\nTesting {provider.value}...", end=" ")
        try:
            client = portkey_manager.get_client_for_provider(provider)
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": "Say 'hello' in one word"}],
                max_tokens=10,
            )
            if response and response.choices:
                print(f"✓ Success - Response: {response.choices[0].message.content}")
                results[provider.value] = {
                    "status": "success",
                    "response": response.choices[0].message.content,
                }
            else:
                print("✗ Failed - No response")
                results[provider.value] = {"status": "failed", "error": "No response"}
        except Exception as e:
            print(f"✗ Failed - Error: {str(e)[:100]}")
            results[provider.value] = {"status": "failed", "error": str(e)[:200]}
    return results
def test_role_based_routing():
    """Test role-based provider routing"""
    print("\n" + "=" * 60)
    print("TESTING ROLE-BASED ROUTING")
    print("=" * 60)
    results = {}
    test_roles = [
        (AgentRole.CREATIVE, "Write a creative tagline for a tech startup"),
        (AgentRole.ANALYTICAL, "Analyze the number 42"),
        (AgentRole.CODING, "Write a Python hello world function"),
        (AgentRole.RESEARCH, "What is the capital of France?"),
        (AgentRole.TACTICAL, "List 3 quick wins for productivity"),
    ]
    for role, prompt in test_roles:
        print(f"\nTesting {role.value} role...", end=" ")
        try:
            client = portkey_manager.get_client_for_role(role)
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}], max_tokens=50
            )
            if response and response.choices:
                print("✓ Success")
                results[role.value] = {
                    "status": "success",
                    "prompt": prompt,
                    "response": response.choices[0].message.content[:100],
                }
            else:
                print("✗ Failed - No response")
                results[role.value] = {"status": "failed", "error": "No response"}
        except Exception as e:
            print(f"✗ Failed - Error: {str(e)[:100]}")
            results[role.value] = {"status": "failed", "error": str(e)[:200]}
    return results
def test_fallback_mechanism():
    """Test fallback mechanism by simulating failures"""
    print("\n" + "=" * 60)
    print("TESTING FALLBACK MECHANISMS")
    print("=" * 60)
    # This test would require simulating provider failures
    # For now, we'll just test that fallback configurations are set up
    results = {}
    for provider in ModelProvider:
        config = portkey_manager.providers.get(provider)
        if config:
            fallback_count = len(config.fallback_providers)
            print(f"\n{provider.value}: {fallback_count} fallback(s) configured")
            results[provider.value] = {
                "fallback_count": fallback_count,
                "fallback_chain": [p.value for p in config.fallback_providers],
            }
    return results
def generate_test_report(all_results: Dict[str, Any]):
    """Generate a comprehensive test report"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "test_results": all_results,
        "summary": {
            "total_providers": len(all_results.get("provider_tests", {})),
            "successful_providers": sum(
                1
                for r in all_results.get("provider_tests", {}).values()
                if r.get("status") == "success"
            ),
            "total_roles_tested": len(all_results.get("role_tests", {})),
            "successful_roles": sum(
                1
                for r in all_results.get("role_tests", {}).values()
                if r.get("status") == "success"
            ),
        },
    }
    # Save report to file
    report_file = f"portkey_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n\nTest report saved to: {report_file}")
    return report
def main():
    """Main test execution"""
    print("\n" + "=" * 60)
    print(" PORTKEY INTEGRATION TEST SUITE")
    print("=" * 60)
    all_results = {}
    # Test 1: Provider Configuration
    print("\n[1/4] Testing Provider Configuration...")
    all_results["configuration"] = test_provider_configuration()
    # Test 2: Individual Provider Connections
    print("\n[2/4] Testing Individual Provider Connections...")
    all_results["provider_tests"] = test_individual_providers()
    # Test 3: Role-Based Routing
    print("\n[3/4] Testing Role-Based Routing...")
    all_results["role_tests"] = test_role_based_routing()
    # Test 4: Fallback Mechanisms
    print("\n[4/4] Testing Fallback Mechanisms...")
    all_results["fallback_tests"] = test_fallback_mechanism()
    # Generate Report
    report = generate_test_report(all_results)
    # Print Summary
    print("\n" + "=" * 60)
    print(" TEST SUMMARY")
    print("=" * 60)
    print(f"\nProviders Tested: {report['summary']['total_providers']}")
    print(f"Successful Providers: {report['summary']['successful_providers']}")
    print(f"Roles Tested: {report['summary']['total_roles_tested']}")
    print(f"Successful Roles: {report['summary']['successful_roles']}")
    # Return exit code based on success
    success_rate = report["summary"]["successful_providers"] / max(
        report["summary"]["total_providers"], 1
    )
    if success_rate >= 0.8:
        print("\n✓ Tests PASSED (80%+ success rate)")
        return 0
    elif success_rate >= 0.5:
        print("\n⚠ Tests PARTIALLY PASSED (50-80% success rate)")
        return 1
    else:
        print("\n✗ Tests FAILED (<50% success rate)")
        return 2
if __name__ == "__main__":
    exit(main())
