"""
Comprehensive End-to-End Test Automation
Tests complete user workflows across the entire Sophia AI system
"""

import pytest
import asyncio
import json
import time
import uuid
import aiohttp
import websockets
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pathlib import Path

# Test configuration and utilities
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

@dataclass
class TestEnvironment:
    """Test environment configuration"""
    unified_mcp_url: str = "${SOPHIA_API_ENDPOINT}"
    artemis_url: str = "http://localhost:8081"
    bi_server_url: str = "http://localhost:8082"
    mem0_url: str = "http://localhost:8083"
    base_mcp_url: str = "http://localhost:8084"
    websocket_url: str = "ws://localhost:8080/ws"
    timeout: int = 30
    retry_attempts: int = 3

@dataclass
class TestUser:
    """Test user configuration"""
    user_id: str
    api_key: str
    role: str
    permissions: List[str]

@dataclass
class WorkflowResult:
    """Workflow execution result"""
    workflow_id: str
    status: str
    execution_time: float
    steps_completed: int
    errors: List[str]
    metrics: Dict[str, Any]

class E2ETestFixture:
    """End-to-end test fixture with setup and teardown"""

    def __init__(self, test_env: TestEnvironment):
        self.env = test_env
        self.session = None
        self.test_data = {}
        self.cleanup_tasks = []

    async def setup(self):
        """Set up test environment"""
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.env.timeout))

        # Wait for all servers to be ready
        await self.wait_for_servers()

        # Initialize test data
        await self.setup_test_data()

    async def teardown(self):
        """Clean up test environment"""
        # Execute cleanup tasks
        for cleanup_task in self.cleanup_tasks:
            try:
                await cleanup_task()
            except Exception as e:
                print(f"Cleanup error: {e}")

        if self.session:
            await self.session.close()

    async def wait_for_servers(self):
        """Wait for all servers to be ready"""
        servers = [
            ("Unified MCP", self.env.unified_mcp_url),
            ("Artemis", self.env.artemis_url),
            ("BI Server", self.env.bi_server_url),
            ("Mem0", self.env.mem0_url),
            ("Base MCP", self.env.base_mcp_url)
        ]

        for name, url in servers:
            await self.wait_for_server(name, f"{url}/health")

    async def wait_for_server(self, name: str, health_url: str):
        """Wait for a specific server to be ready"""
        for attempt in range(self.env.retry_attempts):
            try:
                async with self.session.get(health_url) as response:
                    if response.status == 200:
                        print(f"✓ {name} server is ready")
                        return
            except Exception as e:
                if attempt == self.env.retry_attempts - 1:
                    raise Exception(f"❌ {name} server not ready after {self.env.retry_attempts} attempts: {e}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

    async def setup_test_data(self):
        """Set up test data for E2E tests"""
        self.test_data = {
            "customers": [
                {
                    "id": "customer_001",
                    "name": "TechCorp Industries",
                    "industry": "Technology",
                    "employees": 500,
                    "revenue": 10000000
                },
                {
                    "id": "customer_002", 
                    "name": "StartupXYZ",
                    "industry": "SaaS",
                    "employees": 50,
                    "revenue": 1000000
                }
            ],
            "users": [
                TestUser("admin_001", "admin_api_key_123", "admin", ["read", "write", "admin"]),
                TestUser("analyst_001", "analyst_api_key_456", "analyst", ["read", "write"]),
                TestUser("viewer_001", "viewer_api_key_789", "viewer", ["read"])
            ],
            "workflows": [],
            "memories": []
        }

class TestCompleteUserWorkflows:
    """Test complete user workflows end-to-end"""

    @pytest.fixture
    async def e2e_fixture(self):
        """Set up E2E test environment"""
        test_env = TestEnvironment()
        fixture = E2ETestFixture(test_env)
        await fixture.setup()

        yield fixture

        await fixture.teardown()

    @pytest.mark.asyncio
    async def test_customer_onboarding_workflow(self, e2e_fixture):
        """Test complete customer onboarding workflow"""
        fixture = e2e_fixture
        customer_data = fixture.test_data["customers"][0]
        admin_user = fixture.test_data["users"][0]

        workflow_start = time.time()

        # Step 1: Create customer profile in BI system
        print("🚀 Step 1: Creating customer profile...")

        customer_profile_payload = {
            "customer_id": customer_data["id"],
            "name": customer_data["name"],
            "industry": customer_data["industry"],
            "metadata": {
                "employees": customer_data["employees"],
                "revenue": customer_data["revenue"],
                "onboarding_date": datetime.now().isoformat()
            }
        }

        headers = {"Authorization": f"Bearer {admin_user.api_key}"}

        async with fixture.session.post(
            f"{fixture.env.bi_server_url}/customers",
            json=customer_profile_payload,
            headers=headers
        ) as response:
            assert response.status == 201
            profile_result = await response.json()
            assert profile_result["customer_id"] == customer_data["id"]

        # Step 2: Store customer context in memory system
        print("🧠 Step 2: Storing customer context in memory...")

        memory_payload = {
            "content": {
                "type": "customer_onboarding",
                "customer_data": customer_data,
                "onboarding_stage": "profile_created",
                "timestamp": datetime.now().isoformat()
            },
            "memory_type": "episodic",
            "tags": ["customer", "onboarding", customer_data["industry"]]
        }

        async with fixture.session.post(
            f"{fixture.env.mem0_url}/memories",
            json=memory_payload,
            headers=headers
        ) as response:
            assert response.status == 201
            memory_result = await response.json()
            memory_id = memory_result["memory_id"]
            fixture.cleanup_tasks.append(
                lambda: fixture.session.delete(f"{fixture.env.mem0_url}/memories/{memory_id}", headers=headers)
            )

        # Step 3: Create onboarding workflow in Artemis
        print("⚡ Step 3: Creating onboarding workflow...")

        workflow_payload = {
            "workflow_type": "customer_onboarding",
            "customer_id": customer_data["id"],
            "context_memory_id": memory_id,
            "tasks": [
                {
                    "agent": "plannr",
                    "task": "create_onboarding_plan",
                    "input": {"customer_profile": customer_data}
                },
                {
                    "agent": "coder",
                    "task": "setup_customer_environment",
                    "dependencies": ["create_onboarding_plan"]
                },
                {
                    "agent": "tester",
                    "task": "validate_setup",
                    "dependencies": ["setup_customer_environment"]
                },
                {
                    "agent": "deployer",
                    "task": "deploy_customer_instance",
                    "dependencies": ["validate_setup"]
                }
            ],
            "priority": "high",
            "estimated_duration": "2 hours"
        }

        async with fixture.session.post(
            f"{fixture.env.artemis_url}/workflows",
            json=workflow_payload,
            headers=headers
        ) as response:
            assert response.status == 202  # Accepted for processing
            workflow_result = await response.json()
            workflow_id = workflow_result["workflow_id"]
            fixture.cleanup_tasks.append(
                lambda: fixture.session.delete(f"{fixture.env.artemis_url}/workflows/{workflow_id}", headers=headers)
            )

        # Step 4: Monitor workflow execution via Unified MCP
        print("📊 Step 4: Monitoring workflow execution...")

        workflow_completed = False
        max_wait_time = 60  # 60 seconds max wait
        poll_interval = 2   # Poll every 2 seconds
        waited_time = 0

        while not workflow_completed and waited_time < max_wait_time:
            async with fixture.session.get(
                f"{fixture.env.unified_mcp_url}/workflows/{workflow_id}/status",
                headers=headers
            ) as response:
                assert response.status == 200
                status_result = await response.json()

                if status_result["status"] in ["completed", "failed"]:
                    workflow_completed = True
                    assert status_result["status"] == "completed"
                    break

                await asyncio.sleep(poll_interval)
                waited_time += poll_interval

        assert workflow_completed, "Workflow did not complete within timeout"

        # Step 5: Verify workflow results
        print("✅ Step 5: Verifying workflow results...")

        async with fixture.session.get(
            f"{fixture.env.artemis_url}/workflows/{workflow_id}/results",
            headers=headers
        ) as response:
            assert response.status == 200
            results = await response.json()

            assert results["workflow_id"] == workflow_id
            assert results["status"] == "completed"
            assert len(results["task_results"]) == 4  # All tasks completed

            # Verify each task completed successfully
            for task_result in results["task_results"]:
                assert task_result["status"] == "completed"
                assert "result" in task_result

        # Step 6: Query memory system for onboarding history
        print("🔍 Step 6: Querying onboarding history...")

        async with fixture.session.get(
            f"{fixture.env.mem0_url}/memories/search",
            params={
                "query": f"customer onboarding {customer_data['name']}",
                "limit": 10
            },
            headers=headers
        ) as response:
            assert response.status == 200
            search_results = await response.json()

            assert len(search_results["memories"]) >= 1
            # Should find the original onboarding memory
            onboarding_memories = [
                m for m in search_results["memories"]
                if "onboarding" in m["content"].get("type", "").lower()
            ]
            assert len(onboarding_memories) >= 1

        total_workflow_time = time.time() - workflow_start
        print(f"🎉 Customer onboarding workflow completed in {total_workflow_time:.2f} seconds")

        # Return workflow result for further analysis
        return WorkflowResult(
            workflow_id=workflow_id,
            status="completed",
            execution_time=total_workflow_time,
            steps_completed=6,
            errors=[],
            metrics={
                "customer_id": customer_data["id"],
                "memory_id": memory_id,
                "tasks_completed": 4,
                "total_time": total_workflow_time
            }
        )

    @pytest.mark.asyncio
    async def test_business_intelligence_analysis_workflow(self, e2e_fixture):
        """Test complete BI analysis workflow with real-time insights"""
        fixture = e2e_fixture
        analyst_user = fixture.test_data["users"][1]  # Analyst role

        workflow_start = time.time()

        # Step 1: Request business analysis through Unified MCP
        print("📈 Step 1: Requesting business analysis...")

        analysis_request = {
            "analysis_type": "customer_segment_analysis",
            "parameters": {
                "industry": "Technology",
                "revenue_range": [1000000, 50000000],
                "employee_range": [100, 1000],
                "time_period": "last_quarter"
            },
            "output_format": "comprehensive_report",
            "priority": "normal"
        }

        headers = {"Authorization": f"Bearer {analyst_user.api_key}"}

        async with fixture.session.post(
            f"{fixture.env.unified_mcp_url}/analysis/request",
            json=analysis_request,
            headers=headers
        ) as response:
            assert response.status == 202
            request_result = await response.json()
            analysis_id = request_result["analysis_id"]
            fixture.cleanup_tasks.append(
                lambda: fixture.session.delete(f"{fixture.env.unified_mcp_url}/analysis/{analysis_id}", headers=headers)
            )

        # Step 2: Unified MCP routes to BI server and coordinates data collection
        print("🔄 Step 2: Coordinating multi-source data collection...")

        # Monitor routing and data collection
        routing_complete = False
        max_wait = 30
        waited = 0

        while not routing_complete and waited < max_wait:
            async with fixture.session.get(
                f"{fixture.env.unified_mcp_url}/analysis/{analysis_id}/routing",
                headers=headers
            ) as response:
                if response.status == 200:
                    routing_status = await response.json()
                    if routing_status.get("data_collection_status") == "in_progress":
                        routing_complete = True
                        break

                await asyncio.sleep(1)
                waited += 1

        assert routing_complete, "Data collection routing did not start"

        # Step 3: BI server processes data from multiple integrations
        print("🔗 Step 3: Processing multi-integration data...")

        # Simulate data from different BI integrations
        integration_data = {
            "apollo": {
                "companies_found": 45,
                "avg_employee_count": 342,
                "industries": ["SaaS", "Enterprise Software", "AI/ML"]
            },
            "hubspot": {
                "deals_in_segment": 23,
                "avg_deal_value": 125000,
                "conversion_rate": 0.34
            },
            "gong": {
                "calls_analyzed": 156,
                "sentiment_score": 0.72,
                "top_pain_points": ["scalability", "integration", "security"]
            }
        }

        # Wait for BI processing to complete
        bi_processing_complete = False
        max_wait_bi = 45
        waited_bi = 0

        while not bi_processing_complete and waited_bi < max_wait_bi:
            async with fixture.session.get(
                f"{fixture.env.bi_server_url}/analysis/{analysis_id}/status",
                headers=headers
            ) as response:
                if response.status == 200:
                    bi_status = await response.json()
                    if bi_status.get("processing_status") == "completed":
                        bi_processing_complete = True
                        break
                elif response.status == 404:
                    # BI server might still be processing the request
                    pass

                await asyncio.sleep(2)
                waited_bi += 2

        # Step 4: Memory system stores analysis context and learns patterns
        print("🧠 Step 4: Storing analysis patterns in memory...")

        analysis_context = {
            "analysis_type": analysis_request["analysis_type"],
            "parameters": analysis_request["parameters"],
            "integration_data": integration_data,
            "analyst_user": analyst_user.user_id,
            "timestamp": datetime.now().isoformat()
        }

        memory_payload = {
            "content": analysis_context,
            "memory_type": "semantic",
            "tags": ["analysis", "business_intelligence", "technology_segment"],
            "importance_score": 0.8
        }

        async with fixture.session.post(
            f"{fixture.env.mem0_url}/memories",
            json=memory_payload,
            headers=headers
        ) as response:
            assert response.status == 201
            memory_result = await response.json()
            analysis_memory_id = memory_result["memory_id"]

        # Step 5: Artemis creates insight generation workflow
        print("💡 Step 5: Generating actionable insights...")

        insight_workflow = {
            "workflow_type": "insight_generation",
            "analysis_id": analysis_id,
            "context_memory_id": analysis_memory_id,
            "tasks": [
                {
                    "agent": "plannr",
                    "task": "analyze_market_trends",
                    "input": {"integration_data": integration_data}
                },
                {
                    "agent": "evolver",
                    "task": "generate_recommendations",
                    "dependencies": ["analyze_market_trends"]
                }
            ]
        }

        async with fixture.session.post(
            f"{fixture.env.artemis_url}/workflows",
            json=insight_workflow,
            headers=headers
        ) as response:
            assert response.status == 202
            workflow_result = await response.json()
            insight_workflow_id = workflow_result["workflow_id"]

        # Step 6: Get comprehensive analysis results
        print("📊 Step 6: Retrieving comprehensive results...")

        # Wait for complete analysis
        analysis_complete = False
        max_wait_final = 60
        waited_final = 0

        while not analysis_complete and waited_final < max_wait_final:
            async with fixture.session.get(
                f"{fixture.env.unified_mcp_url}/analysis/{analysis_id}/results",
                headers=headers
            ) as response:
                if response.status == 200:
                    analysis_results = await response.json()
                    if analysis_results.get("status") == "completed":
                        analysis_complete = True

                        # Verify comprehensive results
                        assert "executive_summary" in analysis_results
                        assert "detailed_insights" in analysis_results
                        assert "recommendations" in analysis_results
                        assert "data_sources" in analysis_results

                        # Verify data quality
                        assert analysis_results["confidence_score"] > 0.7
                        assert len(analysis_results["recommendations"]) >= 3
                        break

                await asyncio.sleep(2)
                waited_final += 2

        assert analysis_complete, "Analysis did not complete within timeout"

        total_analysis_time = time.time() - workflow_start
        print(f"🎯 BI analysis workflow completed in {total_analysis_time:.2f} seconds")

        return WorkflowResult(
            workflow_id=insight_workflow_id,
            status="completed",
            execution_time=total_analysis_time,
            steps_completed=6,
            errors=[],
            metrics={
                "analysis_id": analysis_id,
                "memory_id": analysis_memory_id,
                "confidence_score": analysis_results["confidence_score"],
                "recommendations_count": len(analysis_results["recommendations"])
            }
        )

    @pytest.mark.asyncio 
    async def test_real_time_collaboration_workflow(self, e2e_fixture):
        """Test real-time collaboration between user and AI agents"""
        fixture = e2e_fixture
        admin_user = fixture.test_data["users"][0]

        workflow_start = time.time()

        # Step 1: Establish WebSocket connection for real-time interaction
        print("🔄 Step 1: Establishing real-time connection...")

        websocket_uri = f"{fixture.env.websocket_url}?token={admin_user.api_key}"

        async with websockets.connect(websocket_uri) as websocket:
            # Send connection handshake
            handshake = {
                "type": "connection",
                "user_id": admin_user.user_id,
                "session_id": str(uuid.uuid4())
            }

            await websocket.send(json.dumps(handshake))

            # Receive connection confirmation
            response = await websocket.recv()
            connection_result = json.loads(response)
            assert connection_result["type"] == "connection_confirmed"
            session_id = connection_result["session_id"]

            # Step 2: Start collaborative problem-solving session
            print("🤝 Step 2: Starting collaborative session...")

            problem_description = {
                "type": "collaborative_session_start",
                "session_id": session_id,
                "problem": {
                    "title": "Optimize customer conversion pipeline",
                    "description": "Our conversion rate dropped 15% last month. Need to identify bottlenecks and implement solutions.",
                    "urgency": "high",
                    "stakeholders": ["sales", "marketing", "product"]
                }
            }

            await websocket.send(json.dumps(problem_description))

            # Step 3: Receive AI agent assignments and initial analysis
            print("🤖 Step 3: Receiving agent assignments...")

            agent_assignments = []
            analysis_results = []

            # Collect responses from different agents
            for _ in range(3):  # Expect responses from 3 different agents
                response = await asyncio.wait_for(websocket.recv(), timeout=15)
                result = json.loads(response)

                if result["type"] == "agent_assignment":
                    agent_assignments.append(result)
                elif result["type"] == "analysis_result":
                    analysis_results.append(result)

            assert len(agent_assignments) >= 2  # At least 2 agents assigned

            # Step 4: Interactive refinement - user provides feedback
            print("💬 Step 4: Providing interactive feedback...")

            user_feedback = {
                "type": "user_feedback",
                "session_id": session_id,
                "feedback": {
                    "focus_areas": ["landing_page_optimization", "email_nurture_sequence"],
                    "constraints": ["budget_under_50k", "implementation_within_30_days"],
                    "additional_context": "We recently changed our pricing model which might be affecting conversions"
                }
            }

            await websocket.send(json.dumps(user_feedback))

            # Step 5: Receive refined recommendations
            print("🎯 Step 5: Receiving refined recommendations...")

            refined_recommendations = []
            implementation_plans = []

            # Wait for refined analysis
            timeout_count = 0
            max_timeout = 10

            while len(refined_recommendations) < 2 and timeout_count < max_timeout:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=3)
                    result = json.loads(response)

                    if result["type"] == "refined_recommendation":
                        refined_recommendations.append(result)
                    elif result["type"] == "implementation_plan":
                        implementation_plans.append(result)

                except asyncio.TimeoutError:
                    timeout_count += 1

            assert len(refined_recommendations) >= 1

            # Step 6: Approve and execute implementation
            print("✅ Step 6: Approving implementation plan...")

            if implementation_plans:
                approval = {
                    "type": "implementation_approval",
                    "session_id": session_id,
                    "approved_plans": [plan["plan_id"] for plan in implementation_plans],
                    "execution_priority": "high"
                }

                await websocket.send(json.dumps(approval))

                # Wait for execution confirmation
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                execution_result = json.loads(response)

                assert execution_result["type"] == "execution_started"
                assert "workflow_ids" in execution_result

            # Step 7: Monitor execution progress
            print("📈 Step 7: Monitoring execution progress...")

            progress_updates = []
            execution_complete = False

            # Monitor for up to 30 seconds
            start_monitor = time.time()
            while time.time() - start_monitor < 30 and not execution_complete:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    result = json.loads(response)

                    if result["type"] == "progress_update":
                        progress_updates.append(result)
                    elif result["type"] == "execution_completed":
                        execution_complete = True
                        final_results = result
                        break

                except asyncio.TimeoutError:
                    break

            # Step 8: Session summary and knowledge storage
            print("📚 Step 8: Storing session knowledge...")

            session_summary = {
                "type": "session_summary_request",
                "session_id": session_id
            }

            await websocket.send(json.dumps(session_summary))

            response = await asyncio.wait_for(websocket.recv(), timeout=10)
            summary_result = json.loads(response)

            assert summary_result["type"] == "session_summary"
            assert "key_insights" in summary_result
            assert "decisions_made" in summary_result
            assert "memory_stored" in summary_result

        total_collaboration_time = time.time() - workflow_start
        print(f"🌟 Real-time collaboration completed in {total_collaboration_time:.2f} seconds")

        return WorkflowResult(
            workflow_id=session_id,
            status="completed",
            execution_time=total_collaboration_time,
            steps_completed=8,
            errors=[],
            metrics={
                "agents_involved": len(agent_assignments),
                "recommendations_refined": len(refined_recommendations),
                "progress_updates": len(progress_updates),
                "session_duration": total_collaboration_time
            }
        )

    @pytest.mark.asyncio
    async def test_system_failure_recovery_workflow(self, e2e_fixture):
        """Test system resilience and failure recovery"""
        fixture = e2e_fixture
        admin_user = fixture.test_data["users"][0]

        workflow_start = time.time()

        print("⚠️  Starting failure recovery test...")

        # Step 1: Create a workflow that will encounter failures
        print("🚀 Step 1: Creating failure-prone workflow...")

        failure_test_payload = {
            "workflow_type": "failure_recovery_test",
            "test_scenarios": [
                {"type": "server_timeout", "target": "bi_server"},
                {"type": "memory_overflow", "target": "mem0"},
                {"type": "agent_failure", "target": "coder_agent"}
            ],
            "recovery_enabled": True,
            "max_retries": 3
        }

        headers = {"Authorization": f"Bearer {admin_user.api_key}"}

        async with fixture.session.post(
            f"{fixture.env.artemis_url}/workflows/failure-test",
            json=failure_test_payload,
            headers=headers
        ) as response:
            assert response.status == 202
            workflow_result = await response.json()
            test_workflow_id = workflow_result["workflow_id"]

        # Step 2: Monitor failure detection and recovery
        print("🔍 Step 2: Monitoring failure detection...")

        failure_events = []
        recovery_actions = []

        # Monitor for failures and recoveries
        monitoring_duration = 45  # 45 seconds
        start_monitoring = time.time()

        while time.time() - start_monitoring < monitoring_duration:
            # Check for failure events
            async with fixture.session.get(
                f"{fixture.env.unified_mcp_url}/system/events",
                params={"type": "failure", "since": start_monitoring},
                headers=headers
            ) as response:
                if response.status == 200:
                    events = await response.json()
                    failure_events.extend(events.get("failure_events", []))

            # Check for recovery actions
            async with fixture.session.get(
                f"{fixture.env.unified_mcp_url}/system/events",
                params={"type": "recovery", "since": start_monitoring},
                headers=headers
            ) as response:
                if response.status == 200:
                    events = await response.json()
                    recovery_actions.extend(events.get("recovery_events", []))

            await asyncio.sleep(3)

        # Step 3: Verify failure detection
        print("✅ Step 3: Verifying failure detection...")

        assert len(failure_events) >= 1, "No failure events detected"

        # Verify different types of failures were detected
        failure_types = {event["failure_type"] for event in failure_events}
        assert len(failure_types) >= 1

        # Step 4: Verify recovery mechanisms
        print("🔧 Step 4: Verifying recovery mechanisms...")

        assert len(recovery_actions) >= len(failure_events), "Not all failures had recovery actions"

        # Verify recovery action types
        recovery_types = {action["recovery_type"] for action in recovery_actions}
        expected_recovery_types = {"retry", "failover", "circuit_breaker"}
        assert len(recovery_types.intersection(expected_recovery_types)) >= 1

        # Step 5: Verify system stability after recovery
        print("📊 Step 5: Verifying system stability...")

        # Test system responsiveness after failures
        stability_tests = [
            ("Unified MCP", f"{fixture.env.unified_mcp_url}/health"),
            ("Artemis", f"{fixture.env.artemis_url}/health"),
            ("Memory System", f"{fixture.env.mem0_url}/health")
        ]

        for service_name, health_url in stability_tests:
            async with fixture.session.get(health_url, headers=headers) as response:
                assert response.status == 200, f"{service_name} not stable after recovery"
                health_data = await response.json()
                assert health_data.get("status") == "healthy"

        # Step 6: Verify workflow completion despite failures
        print("🎯 Step 6: Verifying workflow resilience...")

        final_workflow_status = None
        max_wait_recovery = 30
        waited_recovery = 0

        while waited_recovery < max_wait_recovery:
            async with fixture.session.get(
                f"{fixture.env.artemis_url}/workflows/{test_workflow_id}/status",
                headers=headers
            ) as response:
                if response.status == 200:
                    status_data = await response.json()
                    if status_data["status"] in ["completed", "failed"]:
                        final_workflow_status = status_data["status"]
                        break

            await asyncio.sleep(2)
            waited_recovery += 2

        # Workflow should either complete successfully or fail gracefully
        assert final_workflow_status is not None

        # If workflow failed, verify it was a graceful failure with proper error handling
        if final_workflow_status == "failed":
            async with fixture.session.get(
                f"{fixture.env.artemis_url}/workflows/{test_workflow_id}/error-details",
                headers=headers
            ) as response:
                assert response.status == 200
                error_details = await response.json()
                assert "error_message" in error_details
                assert "recovery_attempted" in error_details
                assert error_details["recovery_attempted"] is True

        total_recovery_test_time = time.time() - workflow_start
        print(f"🛡️ Failure recovery test completed in {total_recovery_test_time:.2f} seconds")

        return WorkflowResult(
            workflow_id=test_workflow_id,
            status=final_workflow_status,
            execution_time=total_recovery_test_time,
            steps_completed=6,
            errors=[event["error_message"] for event in failure_events],
            metrics={
                "failures_detected": len(failure_events),
                "recoveries_executed": len(recovery_actions),
                "system_stability": "verified",
                "failure_types": list(failure_types),
                "recovery_types": list(recovery_types)
            }
        )

class TestPerformanceValidation:
    """Test system performance under various conditions"""

    @pytest.mark.asyncio
    async def test_concurrent_user_load(self, e2e_fixture):
        """Test system performance under concurrent user load"""
        fixture = e2e_fixture

        print("🚀 Starting concurrent load test...")

        # Create multiple concurrent user sessions
        concurrent_users = 10
        requests_per_user = 5

        async def user_session(user_id: int):
            """Simulate a user session with multiple requests"""
            user_api_key = f"load_test_user_{user_id:03d}"
            headers = {"Authorization": f"Bearer {user_api_key}"}

            session_requests = []
            session_start = time.time()

            for req_num in range(requests_per_user):
                request_start = time.time()

                # Mix different types of requests
                request_types = ["memory_query", "workflow_creation", "bi_analysis", "health_check"]
                request_type = request_types[req_num % len(request_types)]

                try:
                    if request_type == "memory_query":
                        async with fixture.session.get(
                            f"{fixture.env.mem0_url}/memories/search",
                            params={"query": f"test query {user_id}_{req_num}", "limit": 5},
                            headers=headers
                        ) as response:
                            status = response.status

                    elif request_type == "workflow_creation":
                        payload = {
                            "workflow_type": "load_test",
                            "user_id": user_id,
                            "request_num": req_num
                        }
                        async with fixture.session.post(
                            f"{fixture.env.artemis_url}/workflows/quick-test",
                            json=payload,
                            headers=headers
                        ) as response:
                            status = response.status

                    elif request_type == "bi_analysis":
                        async with fixture.session.get(
                            f"{fixture.env.bi_server_url}/analytics/quick-stats",
                            headers=headers
                        ) as response:
                            status = response.status

                    else:  # health_check
                        async with fixture.session.get(
                            f"{fixture.env.unified_mcp_url}/health",
                            headers=headers
                        ) as response:
                            status = response.status

                    request_time = time.time() - request_start
                    session_requests.append({
                        "type": request_type,
                        "status": status,
                        "response_time": request_time,
                        "success": status < 400
                    })

                except Exception as e:
                    request_time = time.time() - request_start
                    session_requests.append({
                        "type": request_type,
                        "status": 0,
                        "response_time": request_time,
                        "success": False,
                        "error": str(e)
                    })

            session_time = time.time() - session_start
            return {
                "user_id": user_id,
                "requests": session_requests,
                "session_time": session_time,
                "success_rate": sum(1 for r in session_requests if r["success"]) / len(session_requests)
            }

        # Execute concurrent user sessions
        load_test_start = time.time()

        user_results = await asyncio.gather(
            *[user_session(user_id) for user_id in range(concurrent_users)]
        )

        total_load_test_time = time.time() - load_test_start

        # Analyze performance results
        total_requests = sum(len(result["requests"]) for result in user_results)
        successful_requests = sum(
            sum(1 for req in result["requests"] if req["success"])
            for result in user_results
        )

        all_response_times = [
            req["response_time"]
            for result in user_results
            for req in result["requests"]
            if req["success"]
        ]

        if all_response_times:
            avg_response_time = sum(all_response_times) / len(all_response_times)
            max_response_time = max(all_response_times)
            min_response_time = min(all_response_times)
        else:
            avg_response_time = max_response_time = min_response_time = 0

        overall_success_rate = successful_requests / total_requests if total_requests > 0 else 0
        requests_per_second = total_requests / total_load_test_time

        print(f"📊 Load Test Results:")
        print(f"   Concurrent Users: {concurrent_users}")
        print(f"   Total Requests: {total_requests}")
        print(f"   Success Rate: {overall_success_rate:.2%}")
        print(f"   Requests/Second: {requests_per_second:.1f}")
        print(f"   Avg Response Time: {avg_response_time:.3f}s")
        print(f"   Max Response Time: {max_response_time:.3f}s")
        print(f"   Total Test Time: {total_load_test_time:.2f}s")

        # Performance assertions
        assert overall_success_rate >= 0.95, f"Success rate {overall_success_rate:.2%} below 95% threshold"
        assert avg_response_time <= 2.0, f"Average response time {avg_response_time:.3f}s above 2.0s threshold"
        assert requests_per_second >= 10, f"Throughput {requests_per_second:.1f} RPS below 10 RPS threshold"

        return {
            "test_type": "concurrent_load",
            "metrics": {
                "concurrent_users": concurrent_users,
                "total_requests": total_requests,
                "success_rate": overall_success_rate,
                "requests_per_second": requests_per_second,
                "avg_response_time": avg_response_time,
                "max_response_time": max_response_time,
                "test_duration": total_load_test_time
            },
            "passed": True
        }

    @pytest.mark.asyncio
    async def test_memory_performance_scaling(self, e2e_fixture):
        """Test memory system performance with increasing data volume"""
        fixture = e2e_fixture
        admin_user = fixture.test_data["users"][0]
        headers = {"Authorization": f"Bearer {admin_user.api_key}"}

        print("🧠 Testing memory system scaling...")

        # Test different data volumes
        data_volumes = [100, 500, 1000, 2000]  # Number of memories to store/query
        performance_results = []

        for volume in data_volumes:
            print(f"   Testing with {volume} memories...")

            volume_start = time.time()

            # 1. Bulk memory storage
            storage_start = time.time()

            memory_batch = []
            for i in range(volume):
                memory_batch.append({
                    "content": f"Performance test memory {i} - " + "data " * 10,  # ~60 chars
                    "memory_type": "semantic",
                    "tags": [f"batch_{volume}", f"item_{i}", "performance_test"],
                    "importance_score": 0.5 + (i % 100) / 200  # Vary importance
                })

            # Store memories in batches of 50
            batch_size = 50
            storage_times = []

            for batch_start in range(0, len(memory_batch), batch_size):
                batch = memory_batch[batch_start:batch_start + batch_size]
                batch_storage_start = time.time()

                async with fixture.session.post(
                    f"{fixture.env.mem0_url}/memories/batch",
                    json={"memories": batch},
                    headers=headers
                ) as response:
                    assert response.status in [201, 207]  # Created or multi-status

                batch_storage_time = time.time() - batch_storage_start
                storage_times.append(batch_storage_time)

            total_storage_time = time.time() - storage_start

            # 2. Memory querying performance
            query_start = time.time()

            query_types = [
                {"query": f"performance test batch_{volume}", "limit": 20},
                {"query": "data memory", "limit": 50},
                {"query": f"item_{volume//2}", "limit": 10}  # Specific item query
            ]

            query_times = []
            for query in query_types:
                query_request_start = time.time()

                async with fixture.session.get(
                    f"{fixture.env.mem0_url}/memories/search",
                    params=query,
                    headers=headers
                ) as response:
                    assert response.status == 200
                    results = await response.json()
                    assert len(results.get("memories", [])) > 0

                query_times.append(time.time() - query_request_start)

            total_query_time = time.time() - query_start

            # 3. Memory correlation performance
            correlation_start = time.time()

            # Test correlation for a subset of memories
            correlation_test_size = min(50, volume // 4)
            async with fixture.session.post(
                f"{fixture.env.mem0_url}/memories/correlate",
                json={
                    "memory_count": correlation_test_size,
                    "correlation_threshold": 0.7
                },
                headers=headers
            ) as response:
                if response.status == 200:
                    correlation_results = await response.json()
                    correlation_time = time.time() - correlation_start
                else:
                    correlation_time = 0  # Service might not support this endpoint

            total_volume_time = time.time() - volume_start

            # Calculate performance metrics
            avg_storage_time_per_memory = total_storage_time / volume
            avg_query_time = sum(query_times) / len(query_times)
            throughput_memories_per_second = volume / total_storage_time

            volume_results = {
                "data_volume": volume,
                "storage_time": total_storage_time,
                "query_time": total_query_time,
                "correlation_time": correlation_time,
                "total_time": total_volume_time,
                "avg_storage_per_memory": avg_storage_time_per_memory,
                "avg_query_time": avg_query_time,
                "throughput_mps": throughput_memories_per_second
            }

            performance_results.append(volume_results)

            print(f"     Storage: {total_storage_time:.2f}s ({throughput_memories_per_second:.1f} memories/s)")
            print(f"     Query: {avg_query_time:.3f}s avg")
            print(f"     Total: {total_volume_time:.2f}s")

        # Analyze scaling characteristics
        print("\n📈 Memory Performance Scaling Analysis:")

        for i, result in enumerate(performance_results):
            print(f"   {result['data_volume']:4d} memories: "
                  f"{result['throughput_mps']:6.1f} storage/s, "
                  f"{result['avg_query_time']:6.3f}s query")

        # Verify acceptable performance degradation
        baseline_result = performance_results[0]
        largest_result = performance_results[-1]

        # Storage throughput shouldn't degrade more than 50%
        throughput_degradation = 1 - (largest_result['throughput_mps'] / baseline_result['throughput_mps'])
        assert throughput_degradation <= 0.5, f"Storage throughput degraded by {throughput_degradation:.1%}"

        # Query time shouldn't increase more than 200%
        query_time_increase = largest_result['avg_query_time'] / baseline_result['avg_query_time']
        assert query_time_increase <= 3.0, f"Query time increased by {query_time_increase:.1f}x"

        return {
            "test_type": "memory_scaling",
            "results": performance_results,
            "scaling_analysis": {
                "throughput_degradation": throughput_degradation,
                "query_time_increase": query_time_increase,
                "max_volume_tested": max(r['data_volume'] for r in performance_results)
            },
            "passed": True
        }

if __name__ == "__main__":
    # Run E2E tests with detailed output
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--asyncio-mode=auto",
        "-s",  # Don't capture output, show real-time progress
        "--durations=10"  # Show 10 slowest tests
    ])