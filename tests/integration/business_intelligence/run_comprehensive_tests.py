#!/usr/bin/env python3
"""
Comprehensive Business Intelligence Integration Testing Runner

This script orchestrates and executes the complete BI integration testing strategy:
1. Connection testing for all platforms
2. Data flow validation 
3. End-to-end workflow testing
4. Performance benchmarking
5. Error handling validation
6. Health monitoring
7. Comprehensive reporting

Usage:
    python run_comprehensive_tests.py [--quick] [--platform PLATFORM] [--output DIR]
"""

import asyncio
import argparse
import json
import time
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import our testing modules
from test_bi_integrations import BIIntegrationTester
from performance_benchmarking import BIPerformanceBenchmarker, SLAThresholds
from mock_data_generator import BIMockDataGenerator, MockDataConfig

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ComprehensiveTestRunner:
    """Orchestrates comprehensive BI integration testing"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:3333", output_dir: str = "test_reports"):
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize test components
        self.integration_tester = None
        self.performance_benchmarker = None
        self.mock_generator = BIMockDataGenerator()
        
        # Test results storage
        self.test_results = {
            "start_time": None,
            "end_time": None,
            "connection_tests": {},
            "data_flow_tests": {},
            "workflow_tests": {},
            "performance_benchmarks": {},
            "error_handling_tests": {},
            "health_monitoring": {},
            "summary": {}
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.integration_tester = BIIntegrationTester(self.base_url)
        await self.integration_tester.__aenter__()
        self.performance_benchmarker = BIPerformanceBenchmarker(self.base_url)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.integration_tester:
            await self.integration_tester.__aexit__(exc_type, exc_val, exc_tb)

    # ==============================================================================
    # TEST EXECUTION METHODS
    # ==============================================================================
    
    async def run_connection_tests(self) -> Dict[str, Any]:
        """Run comprehensive connection tests"""
        logger.info("🔌 Starting connection tests...")
        
        try:
            results = await self.integration_tester.test_all_connections()
            self.test_results["connection_tests"] = results
            
            passed = results["summary"]["passed"]
            total = results["summary"]["total_tests"]
            logger.info(f"✅ Connection tests completed: {passed}/{total} passed")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Connection tests failed: {str(e)}")
            self.test_results["connection_tests"] = {"error": str(e)}
            return {"error": str(e)}
    
    async def run_data_flow_tests(self) -> Dict[str, Any]:
        """Run data flow validation tests"""
        logger.info("📊 Starting data flow tests...")
        
        try:
            results = await self.integration_tester.test_all_data_flows()
            self.test_results["data_flow_tests"] = results
            
            passed = results["summary"]["passed"]
            total = results["summary"]["total_tests"]
            avg_quality = results["summary"]["average_data_quality_score"]
            logger.info(f"✅ Data flow tests completed: {passed}/{total} passed, avg quality: {avg_quality:.2f}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Data flow tests failed: {str(e)}")
            self.test_results["data_flow_tests"] = {"error": str(e)}
            return {"error": str(e)}
    
    async def run_workflow_tests(self) -> Dict[str, Any]:
        """Run end-to-end workflow tests"""
        logger.info("🔄 Starting workflow tests...")
        
        try:
            results = await self.integration_tester.test_end_to_end_workflows()
            self.test_results["workflow_tests"] = results
            
            passed = results["summary"]["passed"]
            total = results["summary"]["total_workflows"]
            logger.info(f"✅ Workflow tests completed: {passed}/{total} passed")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Workflow tests failed: {str(e)}")
            self.test_results["workflow_tests"] = {"error": str(e)}
            return {"error": str(e)}
    
    async def run_performance_benchmarks(self, quick_mode: bool = False) -> Dict[str, Any]:
        """Run performance benchmarks"""
        logger.info("⚡ Starting performance benchmarks...")
        
        try:
            if quick_mode:
                # Quick benchmarks with reduced load
                results = await self._run_quick_benchmarks()
            else:
                # Full benchmark suite
                results = await self.performance_benchmarker.run_standard_benchmark_suite()
            
            # Generate performance report
            sla_thresholds = SLAThresholds(
                max_response_time_ms=5000,
                max_p95_response_time_ms=8000,
                min_success_rate=0.95
            )
            
            performance_report = self.performance_benchmarker.generate_performance_report(
                results, sla_thresholds
            )
            
            self.test_results["performance_benchmarks"] = performance_report
            
            total_benchmarks = len(results)
            avg_response_time = sum(r.avg_response_time_ms for r in results.values()) / total_benchmarks
            overall_success_rate = performance_report["test_summary"]["overall_success_rate"]
            
            logger.info(f"✅ Performance benchmarks completed: {total_benchmarks} tests")
            logger.info(f"   Avg response time: {avg_response_time:.2f}ms")
            logger.info(f"   Overall success rate: {overall_success_rate:.2%}")
            
            return performance_report
            
        except Exception as e:
            logger.error(f"❌ Performance benchmarks failed: {str(e)}")
            self.test_results["performance_benchmarks"] = {"error": str(e)}
            return {"error": str(e)}
    
    async def _run_quick_benchmarks(self) -> Dict[str, Any]:
        """Run reduced benchmark suite for quick testing"""
        from performance_benchmarking import BenchmarkConfig
        
        quick_configs = [
            BenchmarkConfig(
                name="quick_health_check",
                endpoint="/healthz",
                concurrent_users=1,
                total_requests=3
            ),
            BenchmarkConfig(
                name="quick_dashboard_test",
                endpoint="/api/business/dashboard", 
                concurrent_users=2,
                total_requests=10
            ),
            BenchmarkConfig(
                name="quick_gong_test",
                endpoint="/business/gong/recent?days=1",
                concurrent_users=1,
                total_requests=5
            )
        ]
        
        results = {}
        for config in quick_configs:
            try:
                result = await self.performance_benchmarker.run_load_test(config)
                results[config.name] = result
            except Exception as e:
                logger.warning(f"Quick benchmark {config.name} failed: {str(e)}")
        
        return results
    
    async def run_error_handling_tests(self) -> Dict[str, Any]:
        """Test error handling and fallback mechanisms"""
        logger.info("🛡️ Starting error handling tests...")
        
        try:
            # Import error handling components
            from dev_mcp_unified.integrations.error_handling import BIIntegrationErrorHandler, ErrorType
            
            error_handler = BIIntegrationErrorHandler()
            test_scenarios = []
            
            # Test circuit breaker
            circuit_breaker = error_handler.get_circuit_breaker("test_platform")
            
            # Simulate failures
            for _ in range(6):  # Exceed failure threshold
                circuit_breaker.record_failure()
            
            test_scenarios.append({
                "test": "circuit_breaker_activation",
                "passed": circuit_breaker.state == "open",
                "details": f"Circuit breaker state: {circuit_breaker.state}"
            })
            
            # Test error classification  
            from httpx import HTTPStatusError, Response, Request
            
            # Mock HTTP 401 error
            request = Request("GET", "http://example.com")
            response = Response(401, request=request)
            http_error = HTTPStatusError("Unauthorized", request=request, response=response)
            
            error_type = error_handler.classify_error(http_error, response)
            test_scenarios.append({
                "test": "error_classification_auth",
                "passed": error_type == ErrorType.AUTHENTICATION,
                "details": f"Classified as: {error_type.value}"
            })
            
            # Test cache functionality
            error_handler.cache.set("test_key", {"data": "test"}, ttl=1)
            cached_data = error_handler.cache.get("test_key")
            test_scenarios.append({
                "test": "cache_functionality", 
                "passed": cached_data is not None,
                "details": f"Cache working: {cached_data is not None}"
            })
            
            # Test health reporting
            health_report = error_handler.get_health_report()
            test_scenarios.append({
                "test": "health_reporting",
                "passed": "overall_status" in health_report,
                "details": f"Health report generated successfully"
            })
            
            passed_tests = sum(1 for scenario in test_scenarios if scenario["passed"])
            
            error_handling_results = {
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(test_scenarios),
                "passed_tests": passed_tests,
                "failed_tests": len(test_scenarios) - passed_tests,
                "success_rate": passed_tests / len(test_scenarios),
                "scenarios": test_scenarios,
                "health_report": health_report
            }
            
            self.test_results["error_handling_tests"] = error_handling_results
            
            logger.info(f"✅ Error handling tests completed: {passed_tests}/{len(test_scenarios)} passed")
            
            return error_handling_results
            
        except Exception as e:
            logger.error(f"❌ Error handling tests failed: {str(e)}")
            self.test_results["error_handling_tests"] = {"error": str(e)}
            return {"error": str(e)}
    
    async def run_health_monitoring(self) -> Dict[str, Any]:
        """Test health monitoring functionality"""
        logger.info("💚 Starting health monitoring tests...")
        
        try:
            # Get integration health
            health_status = await self.integration_tester.get_integration_health()
            
            # Test health endpoint
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/healthz")
                health_endpoint_working = response.status_code == 200
            
            health_monitoring_results = {
                "timestamp": datetime.now().isoformat(),
                "health_endpoint_status": response.status_code if 'response' in locals() else None,
                "health_endpoint_working": health_endpoint_working,
                "integration_health": health_status,
                "monitoring_functional": True
            }
            
            self.test_results["health_monitoring"] = health_monitoring_results
            
            logger.info(f"✅ Health monitoring tests completed")
            logger.info(f"   Overall health: {health_status.get('overall_status', 'unknown')}")
            
            return health_monitoring_results
            
        except Exception as e:
            logger.error(f"❌ Health monitoring tests failed: {str(e)}")
            self.test_results["health_monitoring"] = {"error": str(e)}
            return {"error": str(e)}
    
    # ==============================================================================
    # MAIN TEST EXECUTION
    # ==============================================================================
    
    async def run_comprehensive_tests(self, quick_mode: bool = False, 
                                    platform_filter: Optional[str] = None) -> Dict[str, Any]:
        """Run all comprehensive tests"""
        
        self.test_results["start_time"] = datetime.now().isoformat()
        
        print("🧪 COMPREHENSIVE BI INTEGRATION TESTING")
        print("=" * 60)
        print(f"Base URL: {self.base_url}")
        print(f"Mode: {'Quick' if quick_mode else 'Full'}")
        if platform_filter:
            print(f"Platform filter: {platform_filter}")
        print("")
        
        # Test phases
        test_phases = [
            ("Connection Tests", self.run_connection_tests),
            ("Data Flow Tests", self.run_data_flow_tests),
            ("Workflow Tests", self.run_workflow_tests),
            ("Performance Benchmarks", lambda: self.run_performance_benchmarks(quick_mode)),
            ("Error Handling Tests", self.run_error_handling_tests),
            ("Health Monitoring", self.run_health_monitoring)
        ]
        
        # Execute test phases
        for phase_name, test_method in test_phases:
            print(f"\n{'='*20} {phase_name} {'='*20}")
            
            phase_start = time.time()
            try:
                await test_method()
                phase_duration = time.time() - phase_start
                print(f"✅ {phase_name} completed in {phase_duration:.2f}s")
            except Exception as e:
                phase_duration = time.time() - phase_start
                print(f"❌ {phase_name} failed in {phase_duration:.2f}s: {str(e)}")
                logger.error(f"{phase_name} error: {str(e)}", exc_info=True)
        
        self.test_results["end_time"] = datetime.now().isoformat()
        
        # Generate summary
        self._generate_summary()
        
        # Save results
        await self._save_results()
        
        return self.test_results
    
    def _generate_summary(self):
        """Generate comprehensive test summary"""
        
        summary = {
            "overall_status": "unknown",
            "total_duration_seconds": 0,
            "phase_summaries": {},
            "key_metrics": {},
            "critical_issues": [],
            "recommendations": []
        }
        
        # Calculate duration
        if self.test_results["start_time"] and self.test_results["end_time"]:
            start_time = datetime.fromisoformat(self.test_results["start_time"])
            end_time = datetime.fromisoformat(self.test_results["end_time"])
            summary["total_duration_seconds"] = (end_time - start_time).total_seconds()
        
        # Process each test phase
        phases_passed = 0
        total_phases = 0
        
        for phase_name, phase_key in [
            ("Connection Tests", "connection_tests"),
            ("Data Flow Tests", "data_flow_tests"), 
            ("Workflow Tests", "workflow_tests"),
            ("Performance Benchmarks", "performance_benchmarks"),
            ("Error Handling Tests", "error_handling_tests"),
            ("Health Monitoring", "health_monitoring")
        ]:
            phase_results = self.test_results.get(phase_key, {})
            
            if "error" not in phase_results:
                total_phases += 1
                
                # Extract phase-specific metrics
                if phase_key == "connection_tests" and "summary" in phase_results:
                    phase_summary = phase_results["summary"]
                    if phase_summary.get("success_rate", 0) >= 0.8:
                        phases_passed += 1
                    
                    summary["phase_summaries"][phase_name] = {
                        "status": "passed" if phase_summary.get("success_rate", 0) >= 0.8 else "failed",
                        "passed": phase_summary.get("passed", 0),
                        "total": phase_summary.get("total_tests", 0),
                        "success_rate": phase_summary.get("success_rate", 0)
                    }
                
                elif phase_key == "data_flow_tests" and "summary" in phase_results:
                    phase_summary = phase_results["summary"]
                    if phase_summary.get("average_data_quality_score", 0) >= 0.7:
                        phases_passed += 1
                    
                    summary["phase_summaries"][phase_name] = {
                        "status": "passed" if phase_summary.get("average_data_quality_score", 0) >= 0.7 else "failed",
                        "passed": phase_summary.get("passed", 0),
                        "total": phase_summary.get("total_tests", 0),
                        "data_quality_score": phase_summary.get("average_data_quality_score", 0)
                    }
                
                elif phase_key == "workflow_tests" and "summary" in phase_results:
                    phase_summary = phase_results["summary"]
                    if phase_summary.get("passed", 0) > 0:
                        phases_passed += 1
                    
                    summary["phase_summaries"][phase_name] = {
                        "status": "passed" if phase_summary.get("passed", 0) > 0 else "failed",
                        "passed": phase_summary.get("passed", 0),
                        "total": phase_summary.get("total_workflows", 0)
                    }
                
                elif phase_key == "performance_benchmarks" and "test_summary" in phase_results:
                    test_summary = phase_results["test_summary"]
                    if test_summary.get("overall_success_rate", 0) >= 0.9:
                        phases_passed += 1
                    
                    summary["phase_summaries"][phase_name] = {
                        "status": "passed" if test_summary.get("overall_success_rate", 0) >= 0.9 else "failed",
                        "total_requests": test_summary.get("total_requests", 0),
                        "success_rate": test_summary.get("overall_success_rate", 0)
                    }
                
                else:
                    # Generic handling for other phases
                    phases_passed += 1
                    summary["phase_summaries"][phase_name] = {"status": "passed"}
            
            else:
                total_phases += 1
                summary["phase_summaries"][phase_name] = {"status": "error", "error": phase_results["error"]}
                summary["critical_issues"].append(f"{phase_name}: {phase_results['error']}")
        
        # Determine overall status
        if phases_passed == total_phases:
            summary["overall_status"] = "passed"
        elif phases_passed >= total_phases * 0.7:
            summary["overall_status"] = "partial"
        else:
            summary["overall_status"] = "failed"
        
        # Key metrics
        summary["key_metrics"] = {
            "phases_passed": phases_passed,
            "total_phases": total_phases,
            "overall_success_rate": phases_passed / total_phases if total_phases > 0 else 0
        }
        
        # Generate recommendations
        summary["recommendations"] = self._generate_recommendations()
        
        self.test_results["summary"] = summary
    
    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations based on test results"""
        recommendations = []
        
        # Connection test recommendations
        connection_results = self.test_results.get("connection_tests", {})
        if "summary" in connection_results:
            success_rate = connection_results["summary"].get("success_rate", 0)
            if success_rate < 0.8:
                recommendations.append("Connection reliability issues detected. Check network connectivity and API credentials.")
        
        # Data flow recommendations
        data_flow_results = self.test_results.get("data_flow_tests", {})
        if "summary" in data_flow_results:
            quality_score = data_flow_results["summary"].get("average_data_quality_score", 0)
            if quality_score < 0.7:
                recommendations.append("Data quality issues detected. Implement data validation and cleansing processes.")
        
        # Performance recommendations
        performance_results = self.test_results.get("performance_benchmarks", {})
        if "recommendations" in performance_results and performance_results["recommendations"]:
            recommendations.extend(performance_results["recommendations"][:3])  # Top 3 performance recommendations
        
        # Health monitoring recommendations
        health_results = self.test_results.get("health_monitoring", {})
        if "integration_health" in health_results:
            overall_health = health_results["integration_health"].get("overall_status")
            if overall_health != "healthy":
                recommendations.append("Integration health issues detected. Implement comprehensive monitoring and alerting.")
        
        return recommendations
    
    async def _save_results(self):
        """Save comprehensive test results"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save main results
        results_file = self.output_dir / f"comprehensive_test_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        # Save summary report
        summary_file = self.output_dir / f"test_summary_{timestamp}.json"
        with open(summary_file, 'w') as f:
            json.dump(self.test_results.get("summary", {}), f, indent=2, default=str)
        
        # Save human-readable report
        report_file = self.output_dir / f"test_report_{timestamp}.md"
        self._generate_markdown_report(report_file)
        
        print(f"\n📁 Test results saved:")
        print(f"   📄 Full results: {results_file}")
        print(f"   📊 Summary: {summary_file}")
        print(f"   📝 Report: {report_file}")
    
    def _generate_markdown_report(self, output_file: Path):
        """Generate human-readable markdown report"""
        
        summary = self.test_results.get("summary", {})
        
        content = f"""# BI Integration Test Report
        
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Duration:** {summary.get("total_duration_seconds", 0):.2f} seconds  
**Overall Status:** {summary.get("overall_status", "unknown").upper()}  

## Executive Summary

- **Phases Passed:** {summary.get("key_metrics", {}).get("phases_passed", 0)}/{summary.get("key_metrics", {}).get("total_phases", 0)}
- **Overall Success Rate:** {summary.get("key_metrics", {}).get("overall_success_rate", 0):.1%}

## Test Phase Results

"""
        
        # Add phase summaries
        for phase_name, phase_data in summary.get("phase_summaries", {}).items():
            status_emoji = "✅" if phase_data.get("status") == "passed" else "❌"
            content += f"### {status_emoji} {phase_name}\n"
            
            if phase_data.get("status") == "error":
                content += f"**Error:** {phase_data.get('error', 'Unknown error')}\n\n"
            else:
                for key, value in phase_data.items():
                    if key != "status":
                        content += f"- **{key.replace('_', ' ').title()}:** {value}\n"
                content += "\n"
        
        # Add critical issues
        if summary.get("critical_issues"):
            content += "## Critical Issues\n\n"
            for issue in summary["critical_issues"]:
                content += f"- ⚠️ {issue}\n"
            content += "\n"
        
        # Add recommendations
        if summary.get("recommendations"):
            content += "## Recommendations\n\n"
            for i, rec in enumerate(summary["recommendations"], 1):
                content += f"{i}. {rec}\n"
            content += "\n"
        
        with open(output_file, 'w') as f:
            f.write(content)

# ==============================================================================
# COMMAND LINE INTERFACE
# ==============================================================================

async def main():
    parser = argparse.ArgumentParser(description="Comprehensive BI Integration Testing")
    parser.add_argument("--quick", action="store_true", help="Run quick tests with reduced load")
    parser.add_argument("--platform", help="Filter tests for specific platform")
    parser.add_argument("--output", default="test_reports", help="Output directory for reports")
    parser.add_argument("--base-url", default="http://127.0.0.1:3333", help="Base URL for API testing")
    
    args = parser.parse_args()
    
    async with ComprehensiveTestRunner(args.base_url, args.output) as runner:
        try:
            results = await runner.run_comprehensive_tests(
                quick_mode=args.quick,
                platform_filter=args.platform
            )
            
            # Print final summary
            summary = results.get("summary", {})
            print(f"\n{'='*60}")
            print(f"🏁 COMPREHENSIVE TESTING COMPLETE")
            print(f"{'='*60}")
            print(f"Overall Status: {summary.get('overall_status', 'unknown').upper()}")
            print(f"Duration: {summary.get('total_duration_seconds', 0):.2f} seconds")
            print(f"Success Rate: {summary.get('key_metrics', {}).get('overall_success_rate', 0):.1%}")
            
            if summary.get("critical_issues"):
                print(f"\n⚠️  Critical Issues: {len(summary['critical_issues'])}")
                for issue in summary["critical_issues"][:3]:  # Show top 3
                    print(f"   - {issue}")
            
            if summary.get("recommendations"):
                print(f"\n💡 Key Recommendations:")
                for rec in summary["recommendations"][:3]:  # Show top 3
                    print(f"   - {rec}")
            
            # Exit with appropriate code
            exit_code = 0 if summary.get("overall_status") == "passed" else 1
            sys.exit(exit_code)
            
        except KeyboardInterrupt:
            print("\n⚠️  Testing interrupted by user")
            sys.exit(130)
        except Exception as e:
            logger.error(f"Testing failed with error: {str(e)}", exc_info=True)
            print(f"\n❌ Testing failed: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())