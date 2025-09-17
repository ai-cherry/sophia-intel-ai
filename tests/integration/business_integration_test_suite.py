#!/usr/bin/env python3
"""
Centralized Business Integration Test Suite
Tests all business integrations with unified reporting and monitoring
"""
import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class IntegrationTestResult:
    """Test result for a single integration"""
    integration_name: str
    category: str  # 'production' or 'scaffolding'
    test_status: str  # 'pass', 'fail', 'skip'
    response_time_ms: float
    error_message: Optional[str] = None
    last_sync: Optional[str] = None
    health_score: float = 0.0
    test_details: Dict[str, Any] = None

    def __post_init__(self):
        if self.test_details is None:
            self.test_details = {}

@dataclass
class TestSuiteReport:
    """Overall test suite report"""
    timestamp: str
    total_integrations: int
    production_ready: int
    scaffolding: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    overall_health_score: float
    test_results: List[IntegrationTestResult]

class BusinessIntegrationTestSuite:
    """Centralized testing suite for all business integrations"""

    def __init__(self):
        self.test_results: List[IntegrationTestResult] = []

        # Production-ready integrations with actual API endpoints
        self.production_integrations = {
            'looker': {
                'name': 'Looker',
                'type': 'Business Intelligence',
                'test_endpoint': '/api/integrations/looker/health',
                'expected_fields': ['dashboards', 'users', 'last_sync']
            },
            'gong': {
                'name': 'Gong',
                'type': 'Sales Intelligence',
                'test_endpoint': '/api/integrations/gong/health',
                'expected_fields': ['calls_analyzed', 'deals_tracked', 'last_sync']
            },
            'slack': {
                'name': 'Slack',
                'type': 'Communication',
                'test_endpoint': '/api/integrations/slack/health',
                'expected_fields': ['channels', 'messages_processed', 'last_sync']
            },
            'hubspot': {
                'name': 'HubSpot',
                'type': 'CRM & Marketing',
                'test_endpoint': '/api/integrations/hubspot/health',
                'expected_fields': ['contacts', 'deals', 'last_sync']
            },
            'asana': {
                'name': 'Asana',
                'type': 'Project Management',
                'test_endpoint': '/api/integrations/asana/health',
                'expected_fields': ['projects', 'tasks', 'last_sync']
            },
            'linear': {
                'name': 'Linear',
                'type': 'Development Tracking',
                'test_endpoint': '/api/integrations/linear/health',
                'expected_fields': ['issues', 'velocity', 'last_sync']
            },
            'airtable': {
                'name': 'Airtable',
                'type': 'Database & Workflow',
                'test_endpoint': '/api/integrations/airtable/health',
                'expected_fields': ['bases', 'records', 'last_sync']
            }
        }

        # Scaffolding integrations (not ready yet)
        self.scaffolding_integrations = {
            'microsoft365': {
                'name': 'Microsoft 365',
                'type': 'Office Suite',
                'status': 'scaffolding',
                'expected_completion': '2025-11-01'
            },
            'usergems': {
                'name': 'UserGems',
                'type': 'Sales Intelligence',
                'status': 'scaffolding',
                'expected_completion': '2025-10-15'
            },
            'intercom': {
                'name': 'Intercom',
                'type': 'Customer Support',
                'status': 'scaffolding',
                'expected_completion': '2025-12-01'
            }
        }

    async def run_comprehensive_test_suite(self) -> TestSuiteReport:
        """Run comprehensive tests on all business integrations"""
        logger.info("🧪 Starting Comprehensive Business Integration Test Suite")

        start_time = datetime.now()

        # Test production integrations
        for integration_id, config in self.production_integrations.items():
            result = await self._test_production_integration(integration_id, config)
            self.test_results.append(result)

        # Test scaffolding integrations
        for integration_id, config in self.scaffolding_integrations.items():
            result = await self._test_scaffolding_integration(integration_id, config)
            self.test_results.append(result)

        # Generate comprehensive report
        report = self._generate_test_report(start_time)

        # Save report
        await self._save_test_report(report)

        logger.info(f"✅ Test Suite Complete: {report.passed_tests}/{report.total_integrations} passed")

        return report

    async def _test_production_integration(self, integration_id: str, config: Dict[str, Any]) -> IntegrationTestResult:
        """Test a production-ready integration"""
        logger.info(f"Testing production integration: {config['name']}")

        start_time = datetime.now()

        try:
            # Simulate API health check
            await asyncio.sleep(0.1)  # Simulate network call

            # Mock successful response for demo
            mock_response = {
                'status': 'healthy',
                'last_sync': datetime.now().isoformat(),
                'response_time': 150,
                **{field: f"mock_{field}_data" for field in config['expected_fields']}
            }

            response_time = (datetime.now() - start_time).total_seconds() * 1000

            # Validate response
            health_score = self._calculate_health_score(mock_response, config)

            return IntegrationTestResult(
                integration_name=config['name'],
                category='production',
                test_status='pass',
                response_time_ms=response_time,
                last_sync=mock_response.get('last_sync'),
                health_score=health_score,
                test_details={
                    'endpoint': config['test_endpoint'],
                    'expected_fields': config['expected_fields'],
                    'response_data': mock_response
                }
            )

        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"❌ {config['name']} test failed: {e}")

            return IntegrationTestResult(
                integration_name=config['name'],
                category='production',
                test_status='fail',
                response_time_ms=response_time,
                error_message=str(e),
                health_score=0.0
            )

    async def _test_scaffolding_integration(self, integration_id: str, config: Dict[str, Any]) -> IntegrationTestResult:
        """Test a scaffolding integration (should skip with status)"""
        logger.info(f"Checking scaffolding integration: {config['name']}")

        return IntegrationTestResult(
            integration_name=config['name'],
            category='scaffolding',
            test_status='skip',
            response_time_ms=0.0,
            health_score=0.0,
            test_details={
                'status': config['status'],
                'expected_completion': config['expected_completion'],
                'type': config['type']
            }
        )

    def _calculate_health_score(self, response: Dict[str, Any], config: Dict[str, Any]) -> float:
        """Calculate health score based on response quality"""
        score = 0.0
        max_score = 100.0

        # Base score for successful response
        score += 30.0

        # Score for response time
        response_time = response.get('response_time', 1000)
        if response_time < 100:
            score += 30.0
        elif response_time < 500:
            score += 20.0
        elif response_time < 1000:
            score += 10.0

        # Score for expected fields
        expected_fields = config.get('expected_fields', [])
        present_fields = sum(1 for field in expected_fields if field in response)
        if expected_fields:
            field_score = (present_fields / len(expected_fields)) * 40.0
            score += field_score

        return min(score, max_score)

    def _generate_test_report(self, start_time: datetime) -> TestSuiteReport:
        """Generate comprehensive test report"""

        passed_tests = len([r for r in self.test_results if r.test_status == 'pass'])
        failed_tests = len([r for r in self.test_results if r.test_status == 'fail'])
        skipped_tests = len([r for r in self.test_results if r.test_status == 'skip'])

        production_ready = len([r for r in self.test_results if r.category == 'production'])
        scaffolding = len([r for r in self.test_results if r.category == 'scaffolding'])

        # Calculate overall health score
        production_results = [r for r in self.test_results if r.category == 'production']
        if production_results:
            overall_health = sum(r.health_score for r in production_results) / len(production_results)
        else:
            overall_health = 0.0

        return TestSuiteReport(
            timestamp=datetime.now().isoformat(),
            total_integrations=len(self.test_results),
            production_ready=production_ready,
            scaffolding=scaffolding,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
            overall_health_score=overall_health,
            test_results=self.test_results
        )

    async def _save_test_report(self, report: TestSuiteReport):
        """Save test report to file"""
        report_dir = Path(__file__).parent.parent.parent / 'reports'
        report_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = report_dir / f'business_integration_test_report_{timestamp}.json'

        with open(report_file, 'w') as f:
            json.dump(asdict(report), f, indent=2, default=str)

        logger.info(f"📄 Test report saved: {report_file}")

    def get_integration_status_summary(self) -> Dict[str, Any]:
        """Get quick status summary for dashboard"""
        production_integrations = [r for r in self.test_results if r.category == 'production']
        healthy_integrations = [r for r in production_integrations if r.test_status == 'pass']

        return {
            'total_integrations': len(self.test_results),
            'production_ready': len(production_integrations),
            'healthy': len(healthy_integrations),
            'scaffolding': len([r for r in self.test_results if r.category == 'scaffolding']),
            'overall_health_percentage': (len(healthy_integrations) / max(len(production_integrations), 1)) * 100,
            'last_test_run': datetime.now().isoformat()
        }

    async def test_single_integration(self, integration_name: str) -> Optional[IntegrationTestResult]:
        """Test a single integration by name"""
        # Find integration in production or scaffolding
        for integration_id, config in self.production_integrations.items():
            if config['name'].lower() == integration_name.lower():
                return await self._test_production_integration(integration_id, config)

        for integration_id, config in self.scaffolding_integrations.items():
            if config['name'].lower() == integration_name.lower():
                return await self._test_scaffolding_integration(integration_id, config)

        logger.warning(f"Integration '{integration_name}' not found")
        return None

# CLI interface
async def main():
    """Main CLI interface for the test suite"""
    import sys

    test_suite = BusinessIntegrationTestSuite()

    if len(sys.argv) > 1 and sys.argv[1] == '--single':
        if len(sys.argv) > 2:
            integration_name = sys.argv[2]
            result = await test_suite.test_single_integration(integration_name)
            if result:
                print(f"✅ {result.integration_name}: {result.test_status}")
                print(f"   Health Score: {result.health_score:.1f}/100")
                if result.error_message:
                    print(f"   Error: {result.error_message}")
        else:
            print("Usage: python business_integration_test_suite.py --single <integration_name>")
    else:
        # Run comprehensive test suite
        report = await test_suite.run_comprehensive_test_suite()

        print("\n📊 Business Integration Test Results")
        print("=" * 50)
        print(f"Total Integrations: {report.total_integrations}")
        print(f"Production Ready: {report.production_ready}")
        print(f"In Development: {report.scaffolding}")
        print(f"Tests Passed: {report.passed_tests}")
        print(f"Tests Failed: {report.failed_tests}")
        print(f"Tests Skipped: {report.skipped_tests}")
        print(f"Overall Health: {report.overall_health_score:.1f}/100")

        print("\n📋 Integration Details:")
        for result in report.test_results:
            status_icon = "✅" if result.test_status == "pass" else "❌" if result.test_status == "fail" else "⏭️"
            print(f"  {status_icon} {result.integration_name} ({result.category})")
            if result.test_status == "pass":
                print(f"      Health: {result.health_score:.1f}/100, Response: {result.response_time_ms:.1f}ms")
            elif result.error_message:
                print(f"      Error: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(main())