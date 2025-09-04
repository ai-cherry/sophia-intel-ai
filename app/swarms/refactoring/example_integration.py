"""
Complete Integration Example for Code Refactoring Swarm
Demonstrates how to use the swarm in various scenarios
"""

import asyncio
import logging
from pathlib import Path

from app.swarms.refactoring.code_refactoring_swarm import (
    CodeRefactoringSwarm, RefactoringType, RefactoringRisk
)
from app.swarms.refactoring.refactoring_swarm_config import (
    RefactoringSwarmConfiguration, DeploymentEnvironment
)
from app.swarms.refactoring.deployment_utils import (
    SwarmDeploymentManager, SwarmOperations, 
    deploy_development_swarm, deploy_production_swarm
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_1_quick_development_deployment():
    """Example 1: Quick development deployment and testing"""
    print("\n🚀 Example 1: Quick Development Deployment")
    print("=" * 50)
    
    try:
        # Deploy swarm in development environment
        manager = await deploy_development_swarm()
        
        # Check deployment status
        status = manager.get_status()
        print(f"✅ Swarm deployed: {status['deployed']}")
        print(f"✅ Environment: {status['environment']}")
        print(f"✅ Agents configured: {status['configuration']['agents_configured']}")
        
        # Run health check
        health = await manager.health_check()
        print(f"✅ Health status: {'HEALTHY' if health['healthy'] else 'UNHEALTHY'}")
        
        # Execute test session
        test_result = await manager.execute_test_session()
        print(f"✅ Test session: {'PASSED' if test_result['success'] else 'FAILED'}")
        print(f"   Opportunities found: {test_result['opportunities_found']}")
        
        # Shutdown
        await manager.shutdown()
        print("✅ Swarm shutdown complete")
        
        return True
        
    except Exception as e:
        logger.error(f"Example 1 failed: {e}")
        return False


async def example_2_custom_configuration():
    """Example 2: Custom configuration and targeted refactoring"""
    print("\n🎯 Example 2: Custom Configuration")
    print("=" * 50)
    
    try:
        # Create custom configuration
        config = RefactoringSwarmConfiguration(
            environment=DeploymentEnvironment.STAGING,
            enabled_refactoring_types=[RefactoringType.PERFORMANCE, RefactoringType.SECURITY],
            default_risk_tolerance=RefactoringRisk.LOW,
            dry_run_default=True
        )
        
        # Custom safety settings
        config.safety.max_files_per_session = 25
        config.safety.require_tests = True
        config.safety.forbidden_paths.extend(["/production/", "/live/"])
        
        # Custom agent settings
        config.agent_model_overrides = {
            "security_auditor": "claude-3-5-sonnet-20241022",
            "performance_profiler": "gpt-4o"
        }
        
        # Deploy with custom configuration
        manager = SwarmDeploymentManager(config)
        success = await manager.deploy()
        
        if not success:
            print("❌ Custom deployment failed")
            return False
        
        print("✅ Custom configuration deployed successfully")
        
        # Execute refactoring with specific types
        swarm = manager.swarm
        result = await swarm.execute_refactoring_session(
            codebase_path=str(Path.cwd()),
            refactoring_types=[RefactoringType.SECURITY, RefactoringType.PERFORMANCE],
            risk_tolerance=RefactoringRisk.LOW,
            dry_run=True
        )
        
        print(f"✅ Custom refactoring session completed")
        print(f"   Success: {result.success}")
        print(f"   Execution time: {result.execution_time:.2f}s")
        print(f"   Quality metrics: {result.quality_metrics}")
        
        # Cleanup
        await manager.shutdown()
        return True
        
    except Exception as e:
        logger.error(f"Example 2 failed: {e}")
        return False


async def example_3_production_deployment():
    """Example 3: Production deployment with full validation"""
    print("\n🏭 Example 3: Production Deployment")
    print("=" * 50)
    
    try:
        # Get production configuration
        config = RefactoringSwarmConfiguration.for_environment(DeploymentEnvironment.PRODUCTION)
        
        # Run production readiness checklist
        checklist = await SwarmOperations.production_deployment_checklist(config)
        
        print("📋 Production Readiness Checklist:")
        for check in checklist:
            status_emoji = "✅" if check["status"] == "PASS" else "⚠️" if check["status"] == "WARN" else "❌"
            print(f"   {status_emoji} {check['category']}: {check['check']}")
        
        # Check for failed items
        failed_checks = [c for c in checklist if c["status"] == "FAIL"]
        if failed_checks:
            print(f"❌ Production deployment blocked by {len(failed_checks)} failed checks")
            return False
        
        # Deploy (this will run comprehensive tests)
        print("🚀 Starting production deployment...")
        manager = await deploy_production_swarm()
        
        print("✅ Production deployment successful!")
        
        # Run comprehensive tests
        test_results = await SwarmOperations.run_comprehensive_test(manager)
        
        print(f"📊 Test Results: {test_results['overall_status']}")
        print(f"   Tests passed: {test_results.get('passed_count', 0)}")
        print(f"   Tests failed: {test_results.get('failed_count', 0)}")
        
        # Create production backup
        backup_path = await manager.create_backup()
        print(f"💾 Production backup created: {backup_path}")
        
        # Cleanup
        await manager.shutdown()
        return True
        
    except Exception as e:
        logger.error(f"Example 3 failed: {e}")
        return False


async def example_4_session_management():
    """Example 4: Session management and rollback capabilities"""
    print("\n🔄 Example 4: Session Management & Rollback")
    print("=" * 50)
    
    try:
        # Deploy development swarm
        manager = await deploy_development_swarm()
        swarm = manager.swarm
        
        # Execute multiple refactoring sessions
        sessions = []
        
        for i in range(3):
            print(f"🔄 Running refactoring session {i+1}/3...")
            
            result = await swarm.execute_refactoring_session(
                codebase_path=str(Path.cwd()),
                refactoring_types=[RefactoringType.QUALITY, RefactoringType.MAINTAINABILITY],
                risk_tolerance=RefactoringRisk.MEDIUM,
                dry_run=True
            )
            
            sessions.append(result)
            print(f"   Session {result.plan_id}: {'✅ SUCCESS' if result.success else '❌ FAILED'}")
        
        # Get session history
        history = swarm.get_session_history()
        print(f"📊 Total sessions in history: {len(history)}")
        
        # Demonstrate rollback capability
        for session in sessions:
            if session.rollback_available:
                print(f"🔄 Rolling back session {session.plan_id}")
                rollback_success = await swarm.rollback_changes(session.plan_id)
                print(f"   Rollback: {'✅ SUCCESS' if rollback_success else '❌ FAILED'}")
        
        # Create backup of current state
        backup_path = await manager.create_backup()
        print(f"💾 Session backup created: {backup_path}")
        
        # Test backup restoration
        restore_success = await manager.restore_from_backup(backup_path)
        print(f"🔄 Backup restoration: {'✅ SUCCESS' if restore_success else '❌ FAILED'}")
        
        # Cleanup
        await manager.shutdown()
        return True
        
    except Exception as e:
        logger.error(f"Example 4 failed: {e}")
        return False


async def example_5_monitoring_and_metrics():
    """Example 5: Monitoring, metrics, and observability"""
    print("\n📊 Example 5: Monitoring & Metrics")
    print("=" * 50)
    
    try:
        # Create configuration with comprehensive monitoring
        config = RefactoringSwarmConfiguration.for_environment(DeploymentEnvironment.STAGING)
        config.monitoring.level = config.monitoring.level.COMPREHENSIVE
        config.monitoring.export_prometheus = True
        
        # Deploy with monitoring
        manager = SwarmDeploymentManager(config)
        success = await manager.deploy()
        
        if not success:
            print("❌ Monitoring deployment failed")
            return False
        
        print("✅ Swarm deployed with comprehensive monitoring")
        
        # Run multiple operations to generate metrics
        swarm = manager.swarm
        
        operations = [
            (RefactoringType.PERFORMANCE, RefactoringRisk.LOW),
            (RefactoringType.SECURITY, RefactoringRisk.MEDIUM),
            (RefactoringType.MAINTAINABILITY, RefactoringRisk.LOW)
        ]
        
        metrics_summary = {
            "total_sessions": 0,
            "successful_sessions": 0,
            "total_opportunities": 0,
            "total_execution_time": 0
        }
        
        for refactor_type, risk_level in operations:
            print(f"🔄 Running {refactor_type.value} refactoring at {risk_level.value} risk")
            
            result = await swarm.execute_refactoring_session(
                codebase_path=str(Path.cwd()),
                refactoring_types=[refactor_type],
                risk_tolerance=risk_level,
                dry_run=True
            )
            
            # Collect metrics
            metrics_summary["total_sessions"] += 1
            if result.success:
                metrics_summary["successful_sessions"] += 1
            metrics_summary["total_opportunities"] += len(result.executed_opportunities)
            metrics_summary["total_execution_time"] += result.execution_time
        
        # Run comprehensive health check
        health_status = await manager.health_check()
        print(f"🏥 Final health status: {'HEALTHY' if health_status['healthy'] else 'UNHEALTHY'}")
        
        # Print metrics summary
        print("\n📊 Session Metrics Summary:")
        print(f"   Total sessions: {metrics_summary['total_sessions']}")
        print(f"   Success rate: {metrics_summary['successful_sessions']/metrics_summary['total_sessions']*100:.1f}%")
        print(f"   Total opportunities: {metrics_summary['total_opportunities']}")
        print(f"   Average execution time: {metrics_summary['total_execution_time']/metrics_summary['total_sessions']:.2f}s")
        
        # Print health check details
        if health_status.get('warnings'):
            print("\n⚠️  Health Warnings:")
            for warning in health_status['warnings']:
                print(f"   - {warning}")
        
        if health_status.get('checks'):
            print(f"\n✅ System Resources:")
            checks = health_status['checks']
            print(f"   Memory: {checks.get('memory_available_mb', 'N/A')}MB available")
            print(f"   CPU cores: {checks.get('cpu_cores', 'N/A')}")
            print(f"   Agents: {checks.get('agents_initialized', 'N/A')}")
        
        # Cleanup
        await manager.shutdown()
        return True
        
    except Exception as e:
        logger.error(f"Example 5 failed: {e}")
        return False


async def run_all_examples():
    """Run all integration examples"""
    print("🎯 Code Refactoring Swarm - Complete Integration Examples")
    print("=" * 60)
    
    examples = [
        ("Quick Development Deployment", example_1_quick_development_deployment),
        ("Custom Configuration", example_2_custom_configuration),
        ("Production Deployment", example_3_production_deployment),
        ("Session Management & Rollback", example_4_session_management),
        ("Monitoring & Metrics", example_5_monitoring_and_metrics)
    ]
    
    results = {}
    
    for name, example_func in examples:
        try:
            print(f"\n{'='*60}")
            print(f"Running: {name}")
            
            success = await example_func()
            results[name] = "✅ PASSED" if success else "❌ FAILED"
            
        except Exception as e:
            logger.error(f"Example '{name}' crashed: {e}")
            results[name] = f"💥 CRASHED: {str(e)[:50]}"
    
    # Print final summary
    print(f"\n{'='*60}")
    print("🎯 INTEGRATION EXAMPLES SUMMARY")
    print(f"{'='*60}")
    
    passed = 0
    total = len(results)
    
    for example_name, status in results.items():
        print(f"{status} {example_name}")
        if status.startswith("✅"):
            passed += 1
    
    print(f"\n📊 Results: {passed}/{total} examples passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All integration examples completed successfully!")
    else:
        print("⚠️  Some examples failed - check logs for details")
    
    return passed == total


# CLI interface for running examples individually
async def main():
    """Main function for running examples"""
    import sys
    
    if len(sys.argv) > 1:
        example_num = sys.argv[1]
        
        examples = {
            "1": example_1_quick_development_deployment,
            "2": example_2_custom_configuration, 
            "3": example_3_production_deployment,
            "4": example_4_session_management,
            "5": example_5_monitoring_and_metrics,
            "all": run_all_examples
        }
        
        if example_num in examples:
            success = await examples[example_num]()
            sys.exit(0 if success else 1)
        else:
            print(f"Invalid example number: {example_num}")
            print("Available examples: 1, 2, 3, 4, 5, all")
            sys.exit(1)
    else:
        # Run all examples by default
        success = await run_all_examples()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())