#!/usr/bin/env python3
"""
Tests for Pulumi IDP Governance
Validates policy enforcement and component registration
"""

import unittest
from unittest.mock import MagicMock, patch

from orchestration.infrastructure.pulumi_governance import (
    GovernanceManager,
    pulumi_idp_governance,
    register_reusable_component,
)
from pulumi_policy import PolicyPack


class TestPulumiGovernance(unittest.TestCase):
    """Test cases for Pulumi IDP Governance"""

    def setUp(self):
        """Set up test environment"""
        self.config = {
            "policy_name": "test-governance",
            "environment": "test",
            "enforcement_level": "advisory",
        }

    def test_pulumi_idp_governance_creation(self):
        """Test creation of policy pack"""
        policy_pack = pulumi_idp_governance(self.config)
        self.assertIsInstance(policy_pack, PolicyPack)
        self.assertEqual(policy_pack.name, "test-governance")

    @patch("pulumi.registry.RegistryClient")
    def test_register_reusable_component(self, mock_registry_client):
        """Test component registration"""
        # Mock the registry client
        mock_client_instance = MagicMock()
        mock_registry_client.return_value = mock_client_instance

        # Create a test component factory
        def test_component():
            return {"test": "component"}

        # Register the component
        result = register_reusable_component("test-component", test_component)

        # Verify the component was registered
        self.assertEqual(result, test_component)
        mock_client_instance.publish_package.assert_called_once()

    def test_governance_manager_initialization(self):
        """Test GovernanceManager initialization"""
        manager = GovernanceManager(self.config)
        self.assertEqual(manager.config, self.config)
        self.assertIsNone(manager.policy_pack)

        # Initialize the manager
        manager.initialize()
        self.assertIsNotNone(manager.policy_pack)

    @patch("orchestration.infrastructure.pulumi_governance.register_reusable_component")
    def test_governance_manager_register_component(self, mock_register):
        """Test GovernanceManager component registration"""
        # Mock the registration function
        mock_register.return_value = "registered-component"

        # Create the manager
        manager = GovernanceManager(self.config)

        # Define a test component
        def test_component():
            return {"test": "component"}

        # Register the component
        result = manager.register_component("test-component", test_component)

        # Verify the registration
        self.assertEqual(result, "registered-component")
        self.assertEqual(manager.registered_components["test-component"], "registered-component")
        mock_register.assert_called_once_with("test-component", test_component, None)


class TestPulumiPolicies(unittest.TestCase):
    """Test specific policy enforcement"""

    def setUp(self):
        """Set up test environment"""
        self.config = {"policy_name": "test-policies", "environment": "test"}
        self.policy_pack = pulumi_idp_governance(self.config)

    def test_web_access_security_policy_lambda(self):
        """Test web access security policy for Lambda"""
        # Create a mock validation context for a Lambda function
        resource_args = MagicMock()
        resource_args.resource_type = "aws:lambda/function:Function"
        resource_args.props = {"environment": {"variables": {"ALLOW_WEB_ACCESS": "true"}}}

        report_violation = MagicMock()

        # Find the web access security policy
        for policy in self.policy_pack.policies:
            if policy.name == "web-access-security":
                # Execute the policy validation
                policy.validate(resource_args, report_violation)
                break

        # Verify violations were reported
        self.assertEqual(report_violation.call_count, 2)

    def test_cost_optimization_policy(self):
        """Test cost optimization policy"""
        # Create a mock validation context for a Lambda function
        resource_args = MagicMock()
        resource_args.resource_type = "aws:lambda/function:Function"
        resource_args.resource_name = "standard-function"
        resource_args.props = {
            "memory_size": 10240,  # Excessive memory
            "timeout": 1000,  # Excessive timeout
        }

        report_violation = MagicMock()

        # Find the cost optimization policy
        for policy in self.policy_pack.policies:
            if policy.name == "cost-optimization":
                # Execute the policy validation
                policy.validate(resource_args, report_violation)
                break

        # Verify violations were reported (one for memory, one for timeout)
        self.assertEqual(report_violation.call_count, 2)

    def test_security_compliance_policy_s3(self):
        """Test security compliance policy for S3"""
        # Create a mock validation context for an S3 bucket
        resource_args = MagicMock()
        resource_args.resource_type = "aws:s3/bucket:Bucket"
        resource_args.props = {"acl": "public-read"}  # Insecure ACL

        report_violation = MagicMock()

        # Find the security compliance policy
        for policy in self.policy_pack.policies:
            if policy.name == "security-compliance":
                # Execute the policy validation
                policy.validate(resource_args, report_violation)
                break

        # Verify violations were reported (one for encryption, one for public access)
        self.assertEqual(report_violation.call_count, 2)


class TestIntegrationWithSwarm(unittest.TestCase):
    """Integration tests with swarm architecture"""

    @patch("pulumi.export")
    def test_integration_with_hybrid_cloud(self, mock_export):
        """Test integration with hybrid cloud manager"""
        from orchestration.infrastructure.hybrid_cloud import HybridCloudManager

        # Create governance manager
        governance_config = {"policy_name": "swarm-governance", "environment": "production"}
        governance = GovernanceManager(governance_config)
        governance.initialize()

        # Create hybrid cloud manager
        cloud_config = {
            "primary_region": "us-west-2",
            "fallback_region": "eastus",
            "env_prefix": "test-swarm",
        }
        cloud_manager = HybridCloudManager(cloud_config)

        # Register a custom component
        def create_secure_lambda(name, memory=1024, timeout=60):
            # Implementation would use the cloud manager
            return {
                "name": name,
                "memory": memory,
                "timeout": timeout,
                "security": {"development environment_enabled": True},
            }

        # Register the component with governance
        secure_lambda_factory = governance.register_component(
            "secure-lambda",
            create_secure_lambda,
            {"version": "1.0.0", "description": "Secure Lambda function with guardrails"},
        )

        # Verify component registration
        self.assertIsNotNone(secure_lambda_factory)
        self.assertIn("secure-lambda", governance.registered_components)


if __name__ == "__main__":
    unittest.main()
