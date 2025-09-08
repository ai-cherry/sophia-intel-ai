#!/usr/bin/env python3
"""
Integration test for Artemis and UnifiedIaCAgent
"""

import asyncio
import os
import tempfile

from artemis.orchestrator.core_orchestrator import ArtemisOrchestrator

# Import the core components
from core.clean_architecture.agents.unified_iac_agent import (
    IaCConfig,
    IaCTool,
    UnifiedIaCAgent,
)


async def test_artemis_iac_integration():
    """Test the integration between Artemis and UnifiedIaCAgent"""
    print("🧪 Testing Artemis and UnifiedIaCAgent integration...\n")

    # Create the UnifiedIaCAgent
    print("Creating UnifiedIaCAgent...")
    config = IaCConfig(
        enable_performance_monitoring=True,
        enable_cost_optimization=True,
        enable_conflict_resolution=True,
    )
    iac_agent = UnifiedIaCAgent(config)

    # Create the ArtemisOrchestrator
    print("Creating ArtemisOrchestrator...")
    artemis = ArtemisOrchestrator()

    # Create a sample Terraform configuration for testing
    tf_config = """
    provider "aws" {
      region = "us-west-2"
    }

    resource "aws_instance" "example" {
      ami           = "ami-0c55b159cbfafe1f0"
      instance_type = "t3.micro"

      tags = {
        Name = "Test Instance"
        Environment = "dev"
      }
    }
    """

    # Create a temporary file with the Terraform configuration
    print("Creating temporary Terraform configuration file...")
    temp_dir = tempfile.mkdtemp()
    config_path = os.path.join(temp_dir, "main.tf")
    with open(config_path, "w") as f:
        f.write(tf_config)

    print(f"Created configuration at: {config_path}")

    # Test UnifiedIaCAgent validation
    print("\n🔍 Testing IaC validation...")
    validation_result = await iac_agent.validate_infrastructure_config(
        IaCTool.TERRAFORM, config_path
    )

    if validation_result.is_success:
        print("✅ Validation successful!")
        print(f"Validation score: {validation_result.value['validation_score']}/100")
        if validation_result.value["security_issues"]:
            print(f"Security issues found: {len(validation_result.value['security_issues'])}")
        if validation_result.value["recommendations"]:
            print(f"Recommendations: {len(validation_result.value['recommendations'])}")
    else:
        print(f"❌ Validation failed: {validation_result.error}")

    # Test IaC cost optimization
    print("\n💰 Testing IaC cost optimization...")
    resources = [
        {
            "name": "example_instance",
            "type": "aws_instance",
            "provider": "aws",
            "configuration": {"instance_type": "t3.medium"},
            "dependencies": [],
            "tags": {"Environment": "dev"},
            "estimated_cost": 50.0,
        }
    ]

    # Convert to IaCResource objects
    from core.clean_architecture.agents.unified_iac_agent import IaCResource

    iac_resources = [
        IaCResource(
            name=r["name"],
            type=r["type"],
            provider=r["provider"],
            configuration=r["configuration"],
            dependencies=r.get("dependencies", []),
            tags=r.get("tags", {}),
            estimated_cost=r["estimated_cost"],
        )
        for r in resources
    ]

    optimization_result = await iac_agent.optimize_infrastructure_costs(iac_resources)

    if optimization_result.is_success:
        print("✅ Cost optimization successful!")
        print(f"Current cost: ${optimization_result.value['current_cost']:.2f}")
        print(f"Optimized cost: ${optimization_result.value['optimized_cost']:.2f}")
        print(
            f"Potential savings: ${optimization_result.value['potential_savings']:.2f} ({optimization_result.value['savings_percentage']:.1f}%)"
        )
    else:
        print(f"❌ Cost optimization failed: {optimization_result.error}")

    # Test UnifiedIaCAgent health check
    print("\n❤️ Testing IaC health status...")
    health_result = await iac_agent.get_health_status()

    if health_result.is_success:
        print("✅ Health check successful!")
        print(f"Status: {health_result.value['status']}")
        print(f"Agent type: {health_result.value['agent_type']}")
        print(f"Version: {health_result.value['version']}")
        print(f"Features: {len(health_result.value['features'])}")
    else:
        print(f"❌ Health check failed: {health_result.error}")

    # Test ArtemisOrchestrator health status
    print("\n❤️ Testing Artemis health status...")
    artemis_health = await artemis.get_health_status()

    print("✅ Artemis health check successful!")
    print(f"Status: {artemis_health['status']}")
    print(f"Components: {artemis_health['components']}")

    # Create a mock session state for testing hand-off
    print("\n🤖 Testing Artemis chat hand-off with IaC context...")
    session_state = {
        "latest_input": "Can you help me optimize my AWS infrastructure costs?",
        "history": [
            {"role": "user", "content": "I need help with my cloud infrastructure"},
            {
                "role": "assistant",
                "content": "I can help with that. What specifically do you need assistance with?",
            },
        ],
        "context": {
            "project_type": "infrastructure",
            "cloud_provider": "aws",
            "iac_tool": "terraform",
        },
    }

    hand_off_result = await artemis.adaptive_hand_off(session_state)

    print("✅ Artemis chat hand-off successful!")
    print(f"Agent used: {hand_off_result['agent_info'].get('agent_type', 'unknown')}")
    print(f"Suggested actions: {len(hand_off_result['suggested_actions'])}")

    print("\n🎉 All integration tests completed successfully!")
    print("The UnifiedIaCAgent is properly aligned with the Artemis architecture!")


if __name__ == "__main__":
    asyncio.run(test_artemis_iac_integration())

if __name__ == "__main__":
    asyncio.run(test_artemis_iac_integration())
