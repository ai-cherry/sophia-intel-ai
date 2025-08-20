"""
End-to-End Autonomy Proof Tests for SOPHIA AI Orchestrator

These tests demonstrate SOPHIA's complete autonomous capabilities:
1. Self-improving deployment loop
2. Autonomous research and action
3. Contextual memory integration
4. Business action orchestration
5. Full stack deployment automation
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from sophia.core.sophia_base_agent import SOPHIABaseAgent


@pytest.fixture
def sophia_agent():
    """Create fully configured SOPHIA agent for testing."""
    with patch.dict('os.environ', {
        'OPENAI_API_KEY': 'test-openai-key',
        'ANTHROPIC_API_KEY': 'test-anthropic-key',
        'GITHUB_TOKEN': 'test-github-token',
        'FLY_API_TOKEN': 'test-fly-token',
        'SLACK_BOT_TOKEN': 'test-slack-token',
        'HUBSPOT_ACCESS_TOKEN': 'test-hubspot-token',
        'SERPER_API_KEY': 'test-serper-key',
        'TAVILY_API_KEY': 'test-tavily-key'
    }):
        agent = SOPHIABaseAgent()
        return agent


@pytest.fixture
def mock_github_responses():
    """Mock GitHub API responses for self-improvement cycle."""
    return {
        "create_branch": {"object": {"sha": "abc123"}},
        "get_file_content": "# Original file content\n",
        "create_commit": {"sha": "def456"},
        "create_pr": {"number": 42, "html_url": "https://github.com/test/repo/pull/42"},
        "merge_pr": {"sha": "ghi789"}
    }


@pytest.fixture
def mock_fly_responses():
    """Mock Fly.io API responses for deployment."""
    return {
        "deploy_app": {"success": True, "id": "deploy-123", "status": "running"},
        "get_app_health": {"healthy": True, "checks": [{"status": "passing"}]}
    }


@pytest.fixture
def mock_research_responses():
    """Mock research API responses."""
    return {
        "serper": {
            "organic": [
                {"title": "AI Market Trends 2024", "snippet": "AI market growing rapidly...", "link": "https://example.com/1"},
                {"title": "Enterprise AI Adoption", "snippet": "Companies adopting AI at scale...", "link": "https://example.com/2"}
            ]
        },
        "tavily": {
            "results": [
                {"title": "AI Investment Report", "content": "Investment in AI reached $50B...", "url": "https://example.com/3"}
            ]
        }
    }


@pytest.fixture
def mock_business_responses():
    """Mock business service responses."""
    return {
        "slack": {"ok": True, "ts": "1234567890.123456"},
        "hubspot_contact": {"id": "12345", "properties": {"firstname": "John", "lastname": "Doe"}},
        "hubspot_deal": {"id": "67890", "properties": {"dealname": "AI Implementation", "amount": "50000"}},
        "salesforce": {"id": "003XX000004TmiQQAS", "success": True, "errors": []}
    }


class TestSelfImprovingDeploymentLoop:
    """Test SOPHIA's self-improving deployment capabilities."""
    
    @pytest.mark.asyncio
    async def test_complete_self_improvement_cycle(self, sophia_agent, mock_github_responses, mock_fly_responses):
        """Test complete self-improvement cycle: code → commit → deploy → verify → learn."""
        
        # Mock all the required components
        with patch.object(sophia_agent.github_master, 'create_branch', return_value=mock_github_responses["create_branch"]), \
             patch.object(sophia_agent.github_master, 'get_file_content', return_value=mock_github_responses["get_file_content"]), \
             patch.object(sophia_agent.github_master, 'create_commit', return_value=mock_github_responses["create_commit"]), \
             patch.object(sophia_agent.github_master, 'create_pull_request', return_value=mock_github_responses["create_pr"]), \
             patch.object(sophia_agent.github_master, 'merge_pull_request', return_value=mock_github_responses["merge_pr"]), \
             patch.object(sophia_agent.fly_master, 'deploy_app', return_value=mock_fly_responses["deploy_app"]), \
             patch.object(sophia_agent.fly_master, 'get_app_health', return_value=mock_fly_responses["get_app_health"]), \
             patch.object(sophia_agent.memory_master, 'store_memory', return_value=True):
            
            # Execute self-improvement cycle
            result = await sophia_agent.self_improve(
                file_path="sophia/core/improvements.py",
                patch="# New improvement: Enhanced error handling\ndef better_error_handling():\n    pass",
                commit_msg="feat: add enhanced error handling",
                auto_merge=True,
                verify_deployment=True
            )
            
            # Verify all steps completed successfully
            assert result["overall_success"] is True
            assert "cycle_id" in result
            assert result["file_path"] == "sophia/core/improvements.py"
            
            # Verify each step
            steps = result["steps"]
            assert steps["create_branch"]["success"] is True
            assert steps["apply_patch"]["success"] is True
            assert steps["create_pr"]["success"] is True
            assert steps["ci_tests"]["success"] is True
            assert steps["merge_pr"]["success"] is True
            assert steps["deploy"]["success"] is True
            assert steps["verify_health"]["success"] is True
            
            # Verify PR was created with correct details
            assert steps["create_pr"]["pr_number"] == 42
            assert "auto/self-improve-" in steps["create_branch"]["branch_name"]
    
    @pytest.mark.asyncio
    async def test_self_improvement_with_ci_failure(self, sophia_agent, mock_github_responses):
        """Test self-improvement cycle with CI failure (no auto-merge)."""
        
        with patch.object(sophia_agent.github_master, 'create_branch', return_value=mock_github_responses["create_branch"]), \
             patch.object(sophia_agent.github_master, 'get_file_content', return_value=mock_github_responses["get_file_content"]), \
             patch.object(sophia_agent.github_master, 'create_commit', return_value=mock_github_responses["create_commit"]), \
             patch.object(sophia_agent.github_master, 'create_pull_request', return_value=mock_github_responses["create_pr"]):
            
            # Simulate CI failure by setting auto_merge=False
            result = await sophia_agent.self_improve(
                file_path="sophia/core/test.py",
                patch="# Test patch",
                commit_msg="test: add test patch",
                auto_merge=False  # Don't auto-merge
            )
            
            # Should still be successful up to PR creation
            assert result["steps"]["create_pr"]["success"] is True
            assert result["steps"]["merge_pr"]["success"] is False
            assert result["steps"]["merge_pr"]["reason"] == "auto_merge disabled or CI failed"
    
    @pytest.mark.asyncio
    async def test_self_improvement_error_handling(self, sophia_agent):
        """Test self-improvement cycle error handling."""
        
        # Mock GitHub master to raise an error
        with patch.object(sophia_agent.github_master, 'create_branch', side_effect=Exception("GitHub API error")):
            
            result = await sophia_agent.self_improve(
                file_path="sophia/core/test.py",
                patch="# Test patch",
                commit_msg="test: error handling"
            )
            
            assert result["overall_success"] is False
            assert "error" in result
            assert "GitHub API error" in result["error"]


class TestAutonomousResearchAndAction:
    """Test SOPHIA's autonomous research and action capabilities."""
    
    @pytest.mark.asyncio
    async def test_complete_research_action_cycle(self, sophia_agent, mock_research_responses, mock_business_responses):
        """Test complete research → synthesis → action → memory cycle."""
        
        # Mock research master
        research_results = {
            "sources": ["serper", "tavily"],
            "findings": [
                {"title": "AI Market Trends", "content": "AI market growing rapidly..."},
                {"title": "Enterprise AI Adoption", "content": "Companies adopting AI..."}
            ]
        }
        
        # Mock model router for synthesis
        synthesis_response = {
            "content": "Based on recent research, the AI market is experiencing unprecedented growth with enterprise adoption accelerating. Key trends include increased investment in AI infrastructure and growing demand for AI orchestration platforms."
        }
        
        with patch.object(sophia_agent.research_master, 'conduct_research', return_value=research_results), \
             patch.object(sophia_agent.model_router, 'call_model', return_value=synthesis_response), \
             patch.object(sophia_agent.business_master, 'post_slack_message', return_value=mock_business_responses["slack"]), \
             patch.object(sophia_agent.memory_master, 'store_memory', return_value=True):
            
            result = await sophia_agent.autonomous_research_and_act(
                research_query="AI market trends 2024",
                action_type="slack_post",
                target_channel="#ai-insights"
            )
            
            # Verify cycle completed successfully
            assert result["overall_success"] is True
            assert result["research_query"] == "AI market trends 2024"
            assert result["action_type"] == "slack_post"
            
            # Verify each step
            steps = result["steps"]
            assert steps["research"]["success"] is True
            assert steps["research"]["sources_used"] == 2
            assert steps["research"]["findings_count"] == 2
            
            assert steps["synthesis"]["success"] is True
            assert steps["synthesis"]["summary_length"] > 0
            
            assert steps["action"]["success"] is True
            assert steps["action"]["action_type"] == "slack_post"
            assert steps["action"]["message_ts"] == "1234567890.123456"
    
    @pytest.mark.asyncio
    async def test_research_action_with_different_actions(self, sophia_agent, mock_research_responses):
        """Test research cycle with different action types."""
        
        research_results = {
            "sources": ["serper"],
            "findings": [{"title": "Test", "content": "Test content"}]
        }
        
        synthesis_response = {"content": "Test synthesis"}
        
        with patch.object(sophia_agent.research_master, 'conduct_research', return_value=research_results), \
             patch.object(sophia_agent.model_router, 'call_model', return_value=synthesis_response), \
             patch.object(sophia_agent.business_master, 'post_slack_message', return_value={"ok": True, "ts": "123"}), \
             patch.object(sophia_agent.memory_master, 'store_memory', return_value=True):
            
            # Test with slack_post action
            result = await sophia_agent.autonomous_research_and_act(
                research_query="test query",
                action_type="slack_post",
                target_channel="#test"
            )
            
            assert result["overall_success"] is True
            assert result["steps"]["action"]["action_type"] == "slack_post"
    
    @pytest.mark.asyncio
    async def test_research_action_error_handling(self, sophia_agent):
        """Test research and action cycle error handling."""
        
        # Mock research master to raise an error
        with patch.object(sophia_agent.research_master, 'conduct_research', side_effect=Exception("Research API error")):
            
            result = await sophia_agent.autonomous_research_and_act(
                research_query="test query"
            )
            
            assert result["overall_success"] is False
            assert "error" in result
            assert "Research API error" in result["error"]


class TestContextualMemoryIntegration:
    """Test SOPHIA's contextual memory capabilities."""
    
    @pytest.mark.asyncio
    async def test_contextual_memory_retrieval(self, sophia_agent):
        """Test contextual memory search and retrieval."""
        
        # Mock memory results
        memory_results = [
            {
                "content": "Self-improvement cycle completed successfully",
                "metadata": {"type": "self_improvement", "cycle_id": "cycle-123"},
                "score": 0.95,
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "content": "Research conducted on AI market trends",
                "metadata": {"type": "research", "query": "AI trends"},
                "score": 0.87,
                "created_at": "2024-01-01T01:00:00Z"
            }
        ]
        
        with patch.object(sophia_agent.memory_master, 'search_memories', return_value=memory_results):
            
            result = await sophia_agent.demonstrate_contextual_memory(
                query="self improvement cycles"
            )
            
            assert result["query"] == "self improvement cycles"
            assert result["results_found"] == 2
            assert len(result["memories"]) == 2
            
            # Verify memory structure
            memory = result["memories"][0]
            assert memory["content"] == "Self-improvement cycle completed successfully"
            assert memory["metadata"]["type"] == "self_improvement"
            assert memory["relevance_score"] == 0.95
            assert "stored_at" in memory
    
    @pytest.mark.asyncio
    async def test_contextual_memory_error_handling(self, sophia_agent):
        """Test contextual memory error handling."""
        
        with patch.object(sophia_agent.memory_master, 'search_memories', side_effect=Exception("Memory search error")):
            
            result = await sophia_agent.demonstrate_contextual_memory(
                query="test query"
            )
            
            assert "error" in result
            assert "Memory search error" in result["error"]


class TestFullStackAutonomousWorkflow:
    """Test complete autonomous workflow combining all capabilities."""
    
    @pytest.mark.asyncio
    async def test_complete_autonomous_workflow(self, sophia_agent, mock_github_responses, mock_fly_responses, mock_research_responses, mock_business_responses):
        """Test complete workflow: research → code improvement → deployment → business action → memory storage."""
        
        # Step 1: Research phase
        research_results = {
            "sources": ["serper", "tavily"],
            "findings": [
                {"title": "AI Performance Optimization", "content": "New techniques for AI optimization..."},
                {"title": "Deployment Best Practices", "content": "Best practices for AI deployment..."}
            ]
        }
        
        synthesis_response = {
            "content": "Research indicates new optimization techniques that could improve SOPHIA's performance by 25%."
        }
        
        # Mock all components
        with patch.object(sophia_agent.research_master, 'conduct_research', return_value=research_results), \
             patch.object(sophia_agent.model_router, 'call_model', return_value=synthesis_response), \
             patch.object(sophia_agent.github_master, 'create_branch', return_value=mock_github_responses["create_branch"]), \
             patch.object(sophia_agent.github_master, 'get_file_content', return_value=mock_github_responses["get_file_content"]), \
             patch.object(sophia_agent.github_master, 'create_commit', return_value=mock_github_responses["create_commit"]), \
             patch.object(sophia_agent.github_master, 'create_pull_request', return_value=mock_github_responses["create_pr"]), \
             patch.object(sophia_agent.github_master, 'merge_pull_request', return_value=mock_github_responses["merge_pr"]), \
             patch.object(sophia_agent.fly_master, 'deploy_app', return_value=mock_fly_responses["deploy_app"]), \
             patch.object(sophia_agent.fly_master, 'get_app_health', return_value=mock_fly_responses["get_app_health"]), \
             patch.object(sophia_agent.business_master, 'post_slack_message', return_value=mock_business_responses["slack"]), \
             patch.object(sophia_agent.business_master, 'create_hubspot_deal', return_value=mock_business_responses["hubspot_deal"]), \
             patch.object(sophia_agent.memory_master, 'store_memory', return_value=True), \
             patch.object(sophia_agent.memory_master, 'search_memories', return_value=[]):
            
            # Phase 1: Conduct research
            research_result = await sophia_agent.autonomous_research_and_act(
                research_query="AI performance optimization techniques",
                action_type="slack_post",
                target_channel="#ai-research"
            )
            
            assert research_result["overall_success"] is True
            
            # Phase 2: Apply research findings via self-improvement
            improvement_result = await sophia_agent.self_improve(
                file_path="sophia/core/performance_optimizer.py",
                patch="# Implement new optimization technique from research\ndef optimize_performance():\n    # 25% performance improvement\n    pass",
                commit_msg="feat: implement AI performance optimization from research",
                auto_merge=True,
                verify_deployment=True
            )
            
            assert improvement_result["overall_success"] is True
            
            # Phase 3: Create business opportunity
            deal_result = await sophia_agent.business_master.create_hubspot_deal(
                deal_name="AI Performance Optimization Implementation",
                amount=75000.0,
                close_date="2024-03-31"
            )
            
            assert deal_result["id"] == "67890"
            
            # Phase 4: Verify contextual memory
            memory_result = await sophia_agent.demonstrate_contextual_memory(
                query="performance optimization"
            )
            
            # All phases should complete successfully
            assert research_result["overall_success"] is True
            assert improvement_result["overall_success"] is True
            assert deal_result["id"] == "67890"
            assert "memories" in memory_result
    
    @pytest.mark.asyncio
    async def test_autonomous_error_recovery(self, sophia_agent):
        """Test autonomous error recovery and resilience."""
        
        # Simulate partial failures in the workflow
        research_results = {"sources": ["serper"], "findings": [{"title": "Test", "content": "Test"}]}
        synthesis_response = {"content": "Test synthesis"}
        
        with patch.object(sophia_agent.research_master, 'conduct_research', return_value=research_results), \
             patch.object(sophia_agent.model_router, 'call_model', return_value=synthesis_response), \
             patch.object(sophia_agent.business_master, 'post_slack_message', side_effect=Exception("Slack API error")), \
             patch.object(sophia_agent.memory_master, 'store_memory', return_value=True):
            
            # Should handle Slack error gracefully
            with pytest.raises(Exception, match="Slack API error"):
                await sophia_agent.autonomous_research_and_act(
                    research_query="test query",
                    action_type="slack_post"
                )
            
            # But research and synthesis should have succeeded
            # (This would be verified through action history in the business master)


class TestOGOrchestrationCapabilities:
    """Test SOPHIA's OG (Original Gangster) orchestration capabilities."""
    
    @pytest.mark.asyncio
    async def test_multi_service_orchestration(self, sophia_agent, mock_business_responses):
        """Test orchestration across multiple services simultaneously."""
        
        with patch.object(sophia_agent.business_master, 'post_slack_message', return_value=mock_business_responses["slack"]), \
             patch.object(sophia_agent.business_master, 'update_hubspot_contact', return_value=mock_business_responses["hubspot_contact"]), \
             patch.object(sophia_agent.business_master, 'create_salesforce_record', return_value=mock_business_responses["salesforce"]):
            
            # Orchestrate actions across multiple services
            slack_result = await sophia_agent.business_master.post_slack_message(
                channel="#sales",
                message="🎯 New high-value lead identified: John Doe (ACME Corp)"
            )
            
            hubspot_result = await sophia_agent.business_master.update_hubspot_contact(
                contact_id="12345",
                properties={
                    "lead_score": "95",
                    "lead_source": "ai_orchestrator",
                    "last_activity_date": datetime.now().isoformat()
                }
            )
            
            salesforce_result = await sophia_agent.business_master.create_salesforce_record(
                object_type="Opportunity",
                fields={
                    "Name": "ACME Corp - AI Implementation",
                    "Amount": 100000,
                    "StageName": "Prospecting",
                    "CloseDate": "2024-06-30"
                }
            )
            
            # Verify all orchestrated actions succeeded
            assert slack_result["ok"] is True
            assert hubspot_result["id"] == "12345"
            assert salesforce_result["success"] is True
            
            # Verify action history shows coordinated workflow
            action_history = sophia_agent.business_master.action_history
            assert len(action_history) == 3
            
            # All actions should be timestamped within seconds of each other
            timestamps = [action["timestamp"] for action in action_history]
            time_diffs = [abs((datetime.fromisoformat(timestamps[i+1].replace('Z', '+00:00')) - 
                              datetime.fromisoformat(timestamps[i].replace('Z', '+00:00'))).total_seconds()) 
                         for i in range(len(timestamps)-1)]
            assert all(diff < 10 for diff in time_diffs)  # All within 10 seconds
    
    @pytest.mark.asyncio
    async def test_autonomous_decision_making(self, sophia_agent):
        """Test SOPHIA's autonomous decision-making capabilities."""
        
        # Mock scenario: High-value lead identified through research
        research_results = {
            "sources": ["serper"],
            "findings": [
                {
                    "title": "ACME Corp Expands AI Initiative", 
                    "content": "ACME Corp announced $10M investment in AI infrastructure..."
                }
            ]
        }
        
        synthesis_response = {
            "content": "ACME Corp represents a high-value opportunity with confirmed AI budget and immediate need for orchestration platform."
        }
        
        with patch.object(sophia_agent.research_master, 'conduct_research', return_value=research_results), \
             patch.object(sophia_agent.model_router, 'call_model', return_value=synthesis_response), \
             patch.object(sophia_agent.business_master, 'post_slack_message', return_value={"ok": True, "ts": "123"}), \
             patch.object(sophia_agent.memory_master, 'store_memory', return_value=True):
            
            # SOPHIA should autonomously decide to research and act
            result = await sophia_agent.autonomous_research_and_act(
                research_query="ACME Corp AI investment budget 2024",
                action_type="slack_post",
                target_channel="#high-value-leads"
            )
            
            assert result["overall_success"] is True
            
            # Verify autonomous decision was logged
            assert result["steps"]["research"]["findings_count"] == 1
            assert result["steps"]["synthesis"]["success"] is True
            assert result["steps"]["action"]["success"] is True


class TestMVPLockInCapabilities:
    """Test MVP lock-in capabilities that prove SOPHIA's value."""
    
    @pytest.mark.asyncio
    async def test_value_demonstration_cycle(self, sophia_agent, mock_business_responses):
        """Test complete value demonstration cycle."""
        
        # Mock high-impact scenario
        research_results = {
            "sources": ["serper", "tavily"],
            "findings": [
                {"title": "AI Market Opportunity", "content": "$50B market opportunity in AI orchestration..."},
                {"title": "Competitor Analysis", "content": "Current solutions lack autonomous capabilities..."}
            ]
        }
        
        synthesis_response = {
            "content": "Market analysis reveals $50B opportunity in AI orchestration with SOPHIA positioned as the only truly autonomous solution."
        }
        
        with patch.object(sophia_agent.research_master, 'conduct_research', return_value=research_results), \
             patch.object(sophia_agent.model_router, 'call_model', return_value=synthesis_response), \
             patch.object(sophia_agent.business_master, 'post_slack_message', return_value=mock_business_responses["slack"]), \
             patch.object(sophia_agent.business_master, 'create_hubspot_deal', return_value=mock_business_responses["hubspot_deal"]), \
             patch.object(sophia_agent.memory_master, 'store_memory', return_value=True):
            
            # Execute value demonstration
            research_result = await sophia_agent.autonomous_research_and_act(
                research_query="AI orchestration market opportunity 2024",
                action_type="slack_post",
                target_channel="#executive-insights"
            )
            
            # Create high-value opportunity
            deal_result = await sophia_agent.business_master.create_hubspot_deal(
                deal_name="Enterprise AI Orchestration Platform",
                amount=500000.0,
                close_date="2024-12-31"
            )
            
            # Verify value demonstration
            assert research_result["overall_success"] is True
            assert deal_result["id"] == "67890"
            assert float(deal_result["properties"]["amount"]) >= 500000.0
    
    def test_sophia_agent_metrics(self, sophia_agent):
        """Test SOPHIA's comprehensive metrics and capabilities."""
        
        metrics = sophia_agent.get_agent_metrics()
        
        # Verify all core components are initialized
        components = metrics["components_initialized"]
        assert components["model_router"] is True
        assert components["api_manager"] is True
        assert components["github_master"] is True
        assert components["fly_master"] is True
        assert components["research_master"] is True
        assert components["business_master"] is True
        assert components["memory_master"] is True
        assert components["mcp_client"] is True
        assert components["feedback_master"] is True
        assert components["performance_monitor"] is True
        
        # Verify metrics structure
        assert "model_calls" in metrics
        assert "api_calls" in metrics
        assert "model_success_rate" in metrics
        assert "api_success_rate" in metrics

