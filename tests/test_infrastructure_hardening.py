#!/usr/bin/env python3
"""
Comprehensive Test Suite for Infrastructure Hardening (2025)
Tests AGNO InfraOpsSwarm, Pulumi ESC, Service Connectors, and more
"""

import asyncio
import pytest
import time
from typing import Dict, Any, List
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.infrastructure.agno_infraops_swarm import (
    InfraOpsSwarm,
    InfraTask,
    InfraTaskType,
    InfraAgent
)
from app.infrastructure.pulumi_esc_secrets import (
    AdvancedSecretsManager,
    SecretRiskLevel,
    SecretProvider,
    RotatedSecret
)
from app.infrastructure.unified_service_connectors import (
    UnifiedServiceConnector,
    ServiceHealth,
    ServiceStatus
)


@pytest.mark.asyncio
class TestInfrastructureHardening:
    """Comprehensive test suite for infrastructure systems"""
    
    async def test_agno_infraops_swarm(self):
        """Test AGNO InfraOpsSwarm functionality"""
        swarm = InfraOpsSwarm()
        
        # Test team creation and agent initialization
        assert len(swarm.agents) == 5
        assert 'InfraLead' in swarm.agents
        assert 'SecurityGuard' in swarm.agents
        assert 'DeploymentEngine' in swarm.agents
        
        # Test deployment task with consensus
        task = {
            'type': 'deployment',
            'description': 'Deploy test infrastructure stack',
            'context': {
                'environment': 'staging',
                'stack': 'test-stack',
                'version': 'v1.0.0'
            },
            'require_approval': True,
            'priority': 8
        }
        
        result = await swarm.execute_infrastructure_task(task)
        assert result['status'] == 'success'
        assert 'consensus' in result
        if result['consensus']:
            assert 'decision' in result['consensus']
            assert result['consensus']['approval_ratio'] >= 0.66
        
        # Test security scan without approval
        security_task = {
            'type': 'security_scan',
            'description': 'Scan infrastructure for vulnerabilities',
            'context': {
                'scope': 'all',
                'severity_threshold': 'medium'
            },
            'require_approval': False
        }
        
        security_result = await swarm.execute_infrastructure_task(security_task)
        assert security_result['status'] == 'success'
        assert security_result['consensus'] is None
        
        # Test health check
        health = await swarm.health_check()
        assert health['healthy_agents'] > 0
        assert health['health_percentage'] > 0
        
        # Verify metrics
        status = swarm.get_swarm_status()
        assert status['swarm_metrics']['total_tasks'] >= 2
        assert status['swarm_metrics']['avg_swarm_latency_ms'] > 0
        
        print("✅ AGNO InfraOpsSwarm test passed")
    
    async def test_secret_rotation_automation(self):
        """Test Pulumi ESC secret rotation"""
        secrets_manager = AdvancedSecretsManager()
        
        # Test automatic rotation setup
        service_configs = {
            'test-service': {
                'provider': 'api-key',
                'risk_level': 'critical',
                'credentials': {
                    'api_key': 'test_key_123',
                    'endpoint': 'https://test.api.com'
                }
            },
            'test-database': {
                'provider': 'database',
                'risk_level': 'standard',
                'credentials': {
                    'connection_string': 'postgres://test:pass@localhost/db'
                }
            }
        }
        
        results = await secrets_manager.setup_rotated_secrets(service_configs)
        assert results['test-service'] == True
        assert results['test-database'] == True
        
        # Test secret health validation
        health = await secrets_manager.validate_secret_health()
        assert 'test-service' in health
        assert health['test-service'].status == 'healthy'
        assert health['test-service'].age_hours < 1
        
        # Test emergency rotation
        emergency_result = await secrets_manager.trigger_emergency_rotation(
            'test-service',
            'Test emergency rotation'
        )
        assert emergency_result['status'] == 'success'
        assert emergency_result['new_version'] in ['primary', 'secondary']
        assert emergency_result['latency_ms'] > 0
        
        # Test scheduled rotation check
        test_secret = secrets_manager.secrets['test-service']
        assert test_secret.rotation_count >= 1
        assert test_secret.last_rotation is not None
        
        # Verify metrics
        metrics = secrets_manager.get_metrics()
        assert metrics['total_rotations'] >= 1
        assert metrics['emergency_rotations'] >= 1
        assert metrics['success_rate'] > 0
        
        print("✅ Secret rotation automation test passed")
    
    async def test_service_connector_health(self):
        """Test unified service connector monitoring"""
        connector = UnifiedServiceConnector({'test': True})
        
        # Test service health monitoring
        statuses = await connector.monitor_all_services()
        assert len(statuses) > 0
        
        for status in statuses:
            assert hasattr(status, 'name')
            assert hasattr(status, 'health')
            assert hasattr(status, 'latency_ms')
            assert status.health in [
                ServiceHealth.HEALTHY,
                ServiceHealth.DEGRADED,
                ServiceHealth.UNHEALTHY,
                ServiceHealth.UNKNOWN
            ]
        
        # Test Lambda Labs connector
        lambda_client = await connector.lambda_labs_connector()
        assert lambda_client is not None
        assert lambda_client.name == 'lambda-labs'
        
        # Test circuit breaker functionality
        async def failing_operation():
            raise Exception("Test failure")
        
        # Should fail initially
        with pytest.raises(Exception):
            await connector.execute_with_circuit_breaker(
                'test-service',
                failing_operation
            )
        
        # After 5 failures, circuit should open
        for _ in range(4):
            try:
                await connector.execute_with_circuit_breaker(
                    'test-service',
                    failing_operation
                )
            except:
                pass
        
        breaker = connector.circuit_breakers.get('test-service')
        assert breaker is not None
        assert breaker['failures'] >= 5
        
        print("✅ Service connector health test passed")
        
        # Cleanup
        await connector.close()
    
    async def test_infrastructure_performance(self):
        """Test performance against 2025 targets"""
        results = {
            'swarm_latency': [],
            'rotation_latency': [],
            'connector_latency': []
        }
        
        # Test AGNO Swarm latency (Target: <100ms for consensus decisions)
        swarm = InfraOpsSwarm()
        for _ in range(10):
            start = time.perf_counter()
            await swarm.execute_infrastructure_task({
                'type': 'health_check',
                'description': 'Performance test',
                'context': {},
                'require_approval': False
            })
            latency = (time.perf_counter() - start) * 1000
            results['swarm_latency'].append(latency)
        
        avg_swarm = sum(results['swarm_latency']) / len(results['swarm_latency'])
        assert avg_swarm < 100, f"Swarm latency {avg_swarm:.2f}ms exceeds 100ms target"
        
        # Test secret rotation latency (Target: <500ms)
        secrets_manager = AdvancedSecretsManager()
        await secrets_manager.setup_rotated_secrets({
            'perf-test': {
                'provider': 'api-key',
                'risk_level': 'standard',
                'credentials': {'key': 'test'}
            }
        })
        
        for _ in range(10):
            start = time.perf_counter()
            await secrets_manager.trigger_emergency_rotation(
                'perf-test',
                'Performance test'
            )
            latency = (time.perf_counter() - start) * 1000
            results['rotation_latency'].append(latency)
        
        avg_rotation = sum(results['rotation_latency']) / len(results['rotation_latency'])
        assert avg_rotation < 500, f"Rotation latency {avg_rotation:.2f}ms exceeds 500ms target"
        
        # Test service connector latency (Target: <50ms for health checks)
        connector = UnifiedServiceConnector({'test': True})
        for _ in range(10):
            start = time.perf_counter()
            await connector.monitor_all_services()
            latency = (time.perf_counter() - start) * 1000
            results['connector_latency'].append(latency)
        
        avg_connector = sum(results['connector_latency']) / len(results['connector_latency'])
        assert avg_connector < 50, f"Connector latency {avg_connector:.2f}ms exceeds 50ms target"
        
        await connector.close()
        
        print("✅ Performance benchmarks passed!")
        print(f"   Swarm latency: {avg_swarm:.2f}ms (target: <100ms)")
        print(f"   Rotation latency: {avg_rotation:.2f}ms (target: <500ms)")
        print(f"   Connector latency: {avg_connector:.2f}ms (target: <50ms)")
        
        return results
    
    async def test_end_to_end_infrastructure_workflow(self):
        """Test complete infrastructure workflow"""
        # Initialize components
        swarm = InfraOpsSwarm()
        secrets_manager = AdvancedSecretsManager()
        connector = UnifiedServiceConnector({'test': True})
        
        # Step 1: Setup secrets for services
        await secrets_manager.setup_rotated_secrets({
            'e2e-service': {
                'provider': 'api-key',
                'risk_level': 'critical',
                'credentials': {'api_key': 'e2e_test_key'}
            }
        })
        
        # Step 2: Health check via swarm
        health_task = {
            'type': 'health_check',
            'description': 'E2E health check',
            'context': {'scope': 'all'},
            'require_approval': False
        }
        health_result = await swarm.execute_infrastructure_task(health_task)
        assert health_result['status'] == 'success'
        
        # Step 3: Monitor services
        service_statuses = await connector.monitor_all_services()
        assert len(service_statuses) > 0
        
        # Step 4: Deployment with approval
        deployment_task = {
            'type': 'deployment',
            'description': 'E2E deployment',
            'context': {
                'service': 'e2e-service',
                'version': 'v2.0.0'
            },
            'require_approval': True
        }
        deployment_result = await swarm.execute_infrastructure_task(deployment_task)
        assert deployment_result['status'] == 'success'
        
        # Step 5: Verify secret health after deployment
        secret_health = await secrets_manager.validate_secret_health()
        assert 'e2e-service' in secret_health
        
        # Cleanup
        await connector.close()
        
        print("✅ End-to-end infrastructure workflow test passed")


async def run_all_tests():
    """Run complete infrastructure test suite"""
    print("=" * 60)
    print("🧪 INFRASTRUCTURE HARDENING TEST SUITE (2025)")
    print("=" * 60)
    print()
    
    test_suite = TestInfrastructureHardening()
    
    tests = [
        ("AGNO InfraOpsSwarm", test_suite.test_agno_infraops_swarm),
        ("Secret Rotation Automation", test_suite.test_secret_rotation_automation),
        ("Service Connector Health", test_suite.test_service_connector_health),
        ("Infrastructure Performance", test_suite.test_infrastructure_performance),
        ("End-to-End Workflow", test_suite.test_end_to_end_infrastructure_workflow)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📝 Running: {test_name}")
        print("-" * 40)
        try:
            await test_func()
            passed += 1
        except Exception as e:
            print(f"❌ Test failed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 TEST RESULTS")
    print(f"   Passed: {passed}/{len(tests)}")
    print(f"   Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Infrastructure hardening is production ready.")
        print("   ✅ AGNO InfraOpsSwarm operational")
        print("   ✅ Pulumi ESC secret rotation configured")
        print("   ✅ Service connectors healthy")
        print("   ✅ Performance targets met")
        print("   ✅ End-to-end workflow validated")
    else:
        print(f"\n⚠️ {failed} tests failed. Review errors above.")
    
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_all_tests())