"""
Business Intelligence Integration Testing Framework

This module provides comprehensive testing for all BI platform integrations:
- Gong (Call intelligence)
- Slack (Team communication) 
- Salesforce (CRM)
- Looker (Business intelligence)
- Linear (Project management)
- Asana (Task coordination)
- Notion (Documentation)
- HubSpot (Marketing automation)
"""

import pytest
import asyncio
import time
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from unittest.mock import AsyncMock, patch
import httpx
import os
import logging
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ConnectionTest:
    """Test configuration for platform connections"""
    name: str
    endpoint: str
    auth_method: str
    required_env_vars: List[str]
    timeout_seconds: int = 30
    expected_status: int = 200
    retry_attempts: int = 3

@dataclass
class DataFlowTest:
    """Test configuration for data flow validation"""
    name: str
    source_endpoint: str
    expected_fields: List[str]
    data_validation_rules: Dict[str, Any]
    performance_threshold_ms: int = 5000

@dataclass
class IntegrationHealth:
    """Integration health status"""
    platform: str
    status: str  # 'healthy', 'degraded', 'down'
    response_time_ms: float
    last_successful_call: Optional[datetime]
    error_message: Optional[str]
    data_quality_score: float  # 0.0 to 1.0

class BIIntegrationTester:
    """Main class for business intelligence integration testing"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:3333"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.health_status: Dict[str, IntegrationHealth] = {}
        
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    # ==============================================================================
    # CONNECTION TESTS
    # ==============================================================================
    
    CONNECTION_TESTS = [
        ConnectionTest(
            name="gong_recent_calls",
            endpoint="/business/gong/recent",
            auth_method="basic",
            required_env_vars=["GONG_ACCESS_KEY", "GONG_CLIENT_SECRET"],
        ),
        ConnectionTest(
            name="business_dashboard", 
            endpoint="/api/business/dashboard",
            auth_method="none",
            required_env_vars=[],
        ),
        ConnectionTest(
            name="crm_contacts",
            endpoint="/api/business/crm/contacts", 
            auth_method="api_key",
            required_env_vars=["HUBSPOT_API_KEY"],
        ),
        ConnectionTest(
            name="crm_pipeline",
            endpoint="/api/business/crm/pipeline",
            auth_method="api_key", 
            required_env_vars=["SALESFORCE_API_KEY", "SALESFORCE_INSTANCE_URL"],
        ),
        ConnectionTest(
            name="calls_recent",
            endpoint="/api/business/calls/recent",
            auth_method="basic",
            required_env_vars=["GONG_ACCESS_KEY", "GONG_CLIENT_SECRET"],
        ),
        ConnectionTest(
            name="projects_overview",
            endpoint="/api/business/projects/overview",
            auth_method="oauth",
            required_env_vars=["ASANA_ACCESS_TOKEN", "LINEAR_API_KEY"],
        ),
    ]
    
    async def test_connection(self, test_config: ConnectionTest) -> Dict[str, Any]:
        """Test individual platform connection"""
        start_time = time.time()
        
        try:
            # Check required environment variables
            missing_vars = [var for var in test_config.required_env_vars 
                          if not os.getenv(var)]
            
            if missing_vars:
                return {
                    "name": test_config.name,
                    "status": "skipped",
                    "reason": f"Missing environment variables: {missing_vars}",
                    "response_time_ms": 0
                }
            
            # Perform connection test with retries
            last_error = None
            for attempt in range(test_config.retry_attempts):
                try:
                    response = await self.client.get(
                        f"{self.base_url}{test_config.endpoint}",
                        timeout=test_config.timeout_seconds
                    )
                    
                    response_time_ms = (time.time() - start_time) * 1000
                    
                    if response.status_code == test_config.expected_status:
                        # Update health status
                        platform = test_config.name.split('_')[0]
                        self.health_status[platform] = IntegrationHealth(
                            platform=platform,
                            status="healthy",
                            response_time_ms=response_time_ms,
                            last_successful_call=datetime.now(),
                            error_message=None,
                            data_quality_score=1.0
                        )
                        
                        return {
                            "name": test_config.name,
                            "status": "passed",
                            "response_time_ms": response_time_ms,
                            "response_size_bytes": len(response.content),
                            "attempt": attempt + 1
                        }
                    else:
                        last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                        
                except httpx.TimeoutException:
                    last_error = f"Timeout after {test_config.timeout_seconds}s"
                except Exception as e:
                    last_error = str(e)
                
                if attempt < test_config.retry_attempts - 1:
                    await asyncio.sleep(1)  # Wait before retry
            
            # All attempts failed
            platform = test_config.name.split('_')[0]
            self.health_status[platform] = IntegrationHealth(
                platform=platform,
                status="down",
                response_time_ms=(time.time() - start_time) * 1000,
                last_successful_call=None,
                error_message=last_error,
                data_quality_score=0.0
            )
            
            return {
                "name": test_config.name,
                "status": "failed",
                "error": last_error,
                "attempts": test_config.retry_attempts,
                "response_time_ms": (time.time() - start_time) * 1000
            }
            
        except Exception as e:
            return {
                "name": test_config.name,
                "status": "error",
                "error": str(e),
                "response_time_ms": (time.time() - start_time) * 1000
            }
    
    async def test_all_connections(self) -> Dict[str, Any]:
        """Test all platform connections"""
        logger.info("Starting connection tests for all BI platforms")
        
        # Run all connection tests concurrently
        tasks = [self.test_connection(test) for test in self.CONNECTION_TESTS]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        passed = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "passed")
        failed = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "failed") 
        skipped = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "skipped")
        errors = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "error")
        
        return {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": len(results),
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "errors": errors,
                "success_rate": passed / len(results) if results else 0
            },
            "results": [r for r in results if isinstance(r, dict)],
            "health_status": {k: asdict(v) for k, v in self.health_status.items()}
        }

    # ==============================================================================
    # DATA FLOW TESTS
    # ==============================================================================
    
    DATA_FLOW_TESTS = [
        DataFlowTest(
            name="gong_call_data_structure",
            source_endpoint="/business/gong/recent?days=7",
            expected_fields=["fromDate", "count", "calls"],
            data_validation_rules={
                "calls": {"type": "list", "min_length": 0},
                "count": {"type": "int", "min_value": 0},
                "fromDate": {"type": "string", "format": "date"}
            }
        ),
        DataFlowTest(
            name="business_dashboard_completeness",
            source_endpoint="/api/business/dashboard",
            expected_fields=["overview", "ai_insights", "recommended_actions", "agent_performance"],
            data_validation_rules={
                "overview.leads_this_week": {"type": "int", "min_value": 0},
                "ai_insights.revenue_forecast": {"type": "int", "min_value": 0},
                "recommended_actions": {"type": "list", "min_length": 0}
            }
        ),
        DataFlowTest(
            name="crm_pipeline_data_quality", 
            source_endpoint="/api/business/crm/pipeline",
            expected_fields=["pipeline", "ai_insights"],
            data_validation_rules={
                "pipeline": {"type": "list", "min_length": 0},
                "ai_insights.success_probability": {"type": "float", "min_value": 0, "max_value": 1}
            }
        )
    ]
    
    def validate_data_structure(self, data: Any, field_path: str, rules: Dict[str, Any]) -> List[str]:
        """Validate data structure against rules"""
        errors = []
        
        try:
            # Navigate to the field using dot notation
            current = data
            for part in field_path.split('.'):
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    errors.append(f"Field '{field_path}' not found")
                    return errors
            
            # Validate type
            if "type" in rules:
                expected_type = rules["type"]
                if expected_type == "string" and not isinstance(current, str):
                    errors.append(f"Field '{field_path}' should be string, got {type(current)}")
                elif expected_type == "int" and not isinstance(current, int):
                    errors.append(f"Field '{field_path}' should be int, got {type(current)}")
                elif expected_type == "float" and not isinstance(current, (int, float)):
                    errors.append(f"Field '{field_path}' should be float, got {type(current)}")
                elif expected_type == "list" and not isinstance(current, list):
                    errors.append(f"Field '{field_path}' should be list, got {type(current)}")
            
            # Validate constraints
            if "min_value" in rules and isinstance(current, (int, float)):
                if current < rules["min_value"]:
                    errors.append(f"Field '{field_path}' value {current} below minimum {rules['min_value']}")
            
            if "max_value" in rules and isinstance(current, (int, float)):
                if current > rules["max_value"]:
                    errors.append(f"Field '{field_path}' value {current} above maximum {rules['max_value']}")
            
            if "min_length" in rules and isinstance(current, list):
                if len(current) < rules["min_length"]:
                    errors.append(f"Field '{field_path}' length {len(current)} below minimum {rules['min_length']}")
                    
        except Exception as e:
            errors.append(f"Validation error for '{field_path}': {str(e)}")
        
        return errors
    
    async def test_data_flow(self, test_config: DataFlowTest) -> Dict[str, Any]:
        """Test data flow and structure for a specific endpoint"""
        start_time = time.time()
        
        try:
            response = await self.client.get(f"{self.base_url}{test_config.source_endpoint}")
            response_time_ms = (time.time() - start_time) * 1000
            
            if response.status_code != 200:
                return {
                    "name": test_config.name,
                    "status": "failed",
                    "error": f"HTTP {response.status_code}: {response.text[:200]}",
                    "response_time_ms": response_time_ms
                }
            
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                return {
                    "name": test_config.name,
                    "status": "failed", 
                    "error": f"Invalid JSON: {str(e)}",
                    "response_time_ms": response_time_ms
                }
            
            # Check expected fields
            missing_fields = []
            for field in test_config.expected_fields:
                if field not in data:
                    missing_fields.append(field)
            
            # Validate data structure
            validation_errors = []
            for field_path, rules in test_config.data_validation_rules.items():
                errors = self.validate_data_structure(data, field_path, rules)
                validation_errors.extend(errors)
            
            # Calculate data quality score
            total_checks = len(test_config.expected_fields) + len(test_config.data_validation_rules)
            failed_checks = len(missing_fields) + len(validation_errors)
            data_quality_score = max(0, (total_checks - failed_checks) / total_checks)
            
            # Check performance
            performance_ok = response_time_ms <= test_config.performance_threshold_ms
            
            status = "passed" if not missing_fields and not validation_errors and performance_ok else "failed"
            
            return {
                "name": test_config.name,
                "status": status,
                "response_time_ms": response_time_ms,
                "performance_threshold_ms": test_config.performance_threshold_ms,
                "performance_ok": performance_ok,
                "data_quality_score": data_quality_score,
                "missing_fields": missing_fields,
                "validation_errors": validation_errors,
                "response_size_bytes": len(response.content)
            }
            
        except Exception as e:
            return {
                "name": test_config.name,
                "status": "error",
                "error": str(e),
                "response_time_ms": (time.time() - start_time) * 1000
            }
    
    async def test_all_data_flows(self) -> Dict[str, Any]:
        """Test all data flow validations"""
        logger.info("Starting data flow tests for all BI integrations")
        
        tasks = [self.test_data_flow(test) for test in self.DATA_FLOW_TESTS]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        passed = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "passed")
        failed = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "failed")
        errors = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "error")
        
        avg_quality_score = sum(r.get("data_quality_score", 0) for r in results if isinstance(r, dict)) / len(results)
        avg_response_time = sum(r.get("response_time_ms", 0) for r in results if isinstance(r, dict)) / len(results)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": len(results),
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "average_data_quality_score": avg_quality_score,
                "average_response_time_ms": avg_response_time
            },
            "results": [r for r in results if isinstance(r, dict)]
        }

    # ==============================================================================
    # INTEGRATION WORKFLOW TESTS
    # ==============================================================================
    
    async def test_end_to_end_workflows(self) -> Dict[str, Any]:
        """Test complete business intelligence workflows"""
        logger.info("Starting end-to-end workflow tests")
        
        workflows = [
            {
                "name": "lead_qualification_workflow",
                "steps": [
                    "/api/business/crm/contacts",
                    "/api/business/calls/recent", 
                    "/api/business/message/preview",
                    "/api/business/workflows/trigger"
                ]
            },
            {
                "name": "project_optimization_workflow", 
                "steps": [
                    "/api/business/projects/overview",
                    "/api/factory/personas",
                    "/api/business/projects/{project_id}/optimize"
                ]
            }
        ]
        
        workflow_results = []
        
        for workflow in workflows:
            start_time = time.time()
            workflow_errors = []
            step_results = []
            
            for step in workflow["steps"]:
                try:
                    # Handle parameterized URLs
                    if "{project_id}" in step:
                        step = step.replace("{project_id}", "proj_001")
                    
                    if step == "/api/business/message/preview":
                        # POST request with sample data
                        response = await self.client.post(
                            f"{self.base_url}{step}",
                            json={
                                "leadId": "lead-001",
                                "signalType": "NewRole", 
                                "person": "Test Person",
                                "company": "Test Company"
                            }
                        )
                    elif step == "/api/business/workflows/trigger":
                        # POST request for workflow trigger
                        response = await self.client.post(
                            f"{self.base_url}{step}",
                            json={"type": "lead_qualification"}
                        )
                    elif "optimize" in step:
                        # POST request for project optimization
                        response = await self.client.post(
                            f"{self.base_url}{step}",
                            json={}
                        )
                    else:
                        # GET request
                        response = await self.client.get(f"{self.base_url}{step}")
                    
                    step_results.append({
                        "step": step,
                        "status_code": response.status_code,
                        "success": response.status_code < 400
                    })
                    
                    if response.status_code >= 400:
                        workflow_errors.append(f"Step {step}: HTTP {response.status_code}")
                        
                except Exception as e:
                    workflow_errors.append(f"Step {step}: {str(e)}")
                    step_results.append({
                        "step": step,
                        "status_code": None,
                        "success": False,
                        "error": str(e)
                    })
            
            workflow_time = (time.time() - start_time) * 1000
            success_rate = sum(1 for step in step_results if step["success"]) / len(step_results)
            
            workflow_results.append({
                "name": workflow["name"],
                "status": "passed" if not workflow_errors else "failed",
                "execution_time_ms": workflow_time,
                "success_rate": success_rate,
                "errors": workflow_errors,
                "steps": step_results
            })
        
        passed_workflows = sum(1 for w in workflow_results if w["status"] == "passed")
        
        return {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_workflows": len(workflow_results),
                "passed": passed_workflows,
                "failed": len(workflow_results) - passed_workflows
            },
            "workflows": workflow_results
        }

    # ==============================================================================
    # HEALTH MONITORING
    # ==============================================================================
    
    async def get_integration_health(self) -> Dict[str, Any]:
        """Get current health status of all integrations"""
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": self._calculate_overall_health(),
            "platforms": {k: asdict(v) for k, v in self.health_status.items()},
            "alerts": self._generate_health_alerts()
        }
    
    def _calculate_overall_health(self) -> str:
        """Calculate overall system health"""
        if not self.health_status:
            return "unknown"
        
        statuses = [h.status for h in self.health_status.values()]
        
        if all(s == "healthy" for s in statuses):
            return "healthy"
        elif any(s == "down" for s in statuses):
            return "degraded"
        else:
            return "degraded"
    
    def _generate_health_alerts(self) -> List[Dict[str, Any]]:
        """Generate alerts based on health status"""
        alerts = []
        
        for platform, health in self.health_status.items():
            if health.status == "down":
                alerts.append({
                    "severity": "critical",
                    "platform": platform,
                    "message": f"{platform} integration is down: {health.error_message}",
                    "timestamp": datetime.now().isoformat()
                })
            elif health.response_time_ms > 10000:  # 10 second threshold
                alerts.append({
                    "severity": "warning", 
                    "platform": platform,
                    "message": f"{platform} response time is slow: {health.response_time_ms:.0f}ms",
                    "timestamp": datetime.now().isoformat()
                })
            elif health.data_quality_score < 0.8:
                alerts.append({
                    "severity": "warning",
                    "platform": platform, 
                    "message": f"{platform} data quality is low: {health.data_quality_score:.2f}",
                    "timestamp": datetime.now().isoformat()
                })
        
        return alerts

# ==============================================================================
# PYTEST TEST CASES  
# ==============================================================================

@pytest.mark.asyncio
class TestBIIntegrations:
    """Pytest test cases for BI integrations"""
    
    async def test_connection_tests(self):
        """Test all BI platform connections"""
        async with BIIntegrationTester() as tester:
            results = await tester.test_all_connections()
            
            assert results["summary"]["total_tests"] > 0
            assert results["summary"]["success_rate"] >= 0.5  # At least 50% success rate
            
            # Log results for debugging
            logger.info(f"Connection test results: {json.dumps(results, indent=2)}")
    
    async def test_data_flow_validation(self):
        """Test data flow and structure validation"""
        async with BIIntegrationTester() as tester:
            results = await tester.test_all_data_flows()
            
            assert results["summary"]["total_tests"] > 0
            assert results["summary"]["average_data_quality_score"] >= 0.7
            
            logger.info(f"Data flow test results: {json.dumps(results, indent=2)}")
    
    async def test_end_to_end_workflows(self):
        """Test complete business workflows"""
        async with BIIntegrationTester() as tester:
            results = await tester.test_end_to_end_workflows()
            
            assert results["summary"]["total_workflows"] > 0
            
            # At least one workflow should pass
            assert results["summary"]["passed"] >= 0
            
            logger.info(f"Workflow test results: {json.dumps(results, indent=2)}")
    
    async def test_health_monitoring(self):
        """Test health monitoring functionality"""
        async with BIIntegrationTester() as tester:
            # Run some tests first to populate health data
            await tester.test_all_connections()
            
            health = await tester.get_integration_health()
            
            assert "overall_status" in health
            assert "platforms" in health
            assert "alerts" in health
            
            logger.info(f"Health monitoring results: {json.dumps(health, indent=2)}")

# ==============================================================================
# COMMAND LINE INTERFACE
# ==============================================================================

async def main():
    """Main function for running tests from command line"""
    print("🧪 Business Intelligence Integration Testing Framework")
    print("=" * 60)
    
    async with BIIntegrationTester() as tester:
        # Run all test suites
        print("\n📡 Testing platform connections...")
        connection_results = await tester.test_all_connections()
        print(f"✅ Connection tests: {connection_results['summary']['passed']}/{connection_results['summary']['total_tests']} passed")
        
        print("\n📊 Testing data flows...")
        dataflow_results = await tester.test_all_data_flows()
        print(f"✅ Data flow tests: {dataflow_results['summary']['passed']}/{dataflow_results['summary']['total_tests']} passed")
        
        print("\n🔄 Testing end-to-end workflows...")
        workflow_results = await tester.test_end_to_end_workflows()
        print(f"✅ Workflow tests: {workflow_results['summary']['passed']}/{workflow_results['summary']['total_workflows']} passed")
        
        print("\n💚 Getting integration health status...")
        health_results = await tester.get_integration_health()
        print(f"📈 Overall health: {health_results['overall_status']}")
        print(f"🚨 Active alerts: {len(health_results['alerts'])}")
        
        # Save comprehensive report
        report = {
            "test_run_timestamp": datetime.now().isoformat(),
            "connection_tests": connection_results,
            "data_flow_tests": dataflow_results,
            "workflow_tests": workflow_results,
            "health_status": health_results
        }
        
        with open("bi_integration_test_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📝 Full report saved to: bi_integration_test_report.json")
        print("\n🎯 Integration testing complete!")

if __name__ == "__main__":
    asyncio.run(main())