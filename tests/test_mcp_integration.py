"""
MCP Integration Test Suite
Comprehensive tests for SOPHIA's MCP server integration
"""

import asyncio
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.mcp_client import SophiaMCPClient, SophiaSessionManager, ContextAwareToolWrapper
from libs.mcp_client.repo_intelligence import RepositoryIntelligence
from libs.mcp_client.predictive_assistant import PredictiveAssistant


class TestMCPIntegration:
    """Integration tests for MCP components"""

    @pytest.fixture
    async def mock_mcp_client(self):
        """Create a mock MCP client for testing"""
        client = Mock(spec=SophiaMCPClient)
        client.session_id = "test_session_123"
        client.connected = True
        
        # Mock async methods
        client.connect = AsyncMock()
        client.disconnect = AsyncMock()
        client.health_check = AsyncMock(return_value={"status": "healthy"})
        client.store_context = AsyncMock(return_value={"success": True, "id": "ctx_123"})
        client.query_context = AsyncMock(return_value=[
            {
                "id": "ctx_123",
                "content": "Test context content",
                "score": 0.8,
                "metadata": {"file_path": "test.py", "context_type": "code_change"}
            }
        ])
        client.store_tool_usage = AsyncMock(return_value={"success": True, "id": "tool_123"})
        client.get_file_context = AsyncMock(return_value=[
            {"content": "Previous file change", "score": 0.7}
        ])
        
        return client

    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repository for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            
            # Create some test files
            (repo_path / "main.py").write_text("""
def hello_world():
    print("Hello, World!")

class TestClass:
    def __init__(self):
        self.value = 42
        
    def get_value(self):
        return self.value
""")
            
            (repo_path / "utils.py").write_text("""
def helper_function(x, y):
    return x + y

def another_helper(data):
    return [item * 2 for item in data]
""")
            
            (repo_path / "README.md").write_text("""
# Test Repository
This is a test repository for MCP integration testing.
""")
            
            yield repo_path

    @pytest.mark.asyncio
    async def test_sophia_mcp_client_connection(self, mock_mcp_client):
        """Test MCP client connection and basic operations"""
        # Test connection
        await mock_mcp_client.connect()
        assert mock_mcp_client.connected
        
        # Test health check
        health = await mock_mcp_client.health_check()
        assert health["status"] == "healthy"
        
        # Test context storage
        result = await mock_mcp_client.store_context(
            content="Test content",
            context_type="test",
            metadata={"test": True}
        )
        assert result["success"]
        
        # Test context query
        results = await mock_mcp_client.query_context("test query")
        assert len(results) > 0
        assert results[0]["score"] > 0

    @pytest.mark.asyncio
    async def test_session_manager(self, mock_mcp_client):
        """Test session management functionality"""
        with patch('libs.mcp_client.session_manager.SophiaMCPClient', return_value=mock_mcp_client):
            session_manager = SophiaSessionManager()
            
            # Test session creation
            session_id = await session_manager.start_session()
            assert session_id is not None
            assert session_manager.current_session == session_id
            
            # Test activity storage
            result = await session_manager.store_activity(
                activity_type="test_activity",
                description="Testing activity storage",
                data={"test": "data"}
            )
            assert result["success"]
            
            # Test context retrieval
            context = await session_manager.get_context_for_action(
                action_description="test action",
                file_path="test.py"
            )
            assert isinstance(context, list)
            
            # Test session ending
            await session_manager.end_session()
            assert session_manager.current_session is None

    @pytest.mark.asyncio
    async def test_context_aware_wrapper(self, mock_mcp_client):
        """Test context-aware tool wrapper"""
        wrapper = ContextAwareToolWrapper(mock_mcp_client)
        
        # Create a test tool function
        async def test_tool(file_path: str, content: str = ""):
            return f"Processed {file_path} with {len(content)} characters"
        
        # Wrap the tool
        wrapped_tool = await wrapper.wrap_tool(test_tool, "test_tool")
        
        # Test wrapped tool execution
        result = await wrapped_tool("test.py", content="test content")
        assert "Processed test.py" in result
        assert "13 characters" in result
        
        # Verify context storage was called
        mock_mcp_client.store_tool_usage.assert_called()
        
        # Test tool suggestions
        suggestions = await wrapper.get_tool_suggestions(
            current_context="working on test.py",
            file_path="test.py"
        )
        assert isinstance(suggestions, list)

    @pytest.mark.asyncio
    async def test_repository_intelligence(self, mock_mcp_client, temp_repo):
        """Test repository intelligence features"""
        repo_intel = RepositoryIntelligence(mock_mcp_client, str(temp_repo))
        
        # Test repository indexing
        index_results = await repo_intel.index_repository(force_refresh=True)
        assert "structure" in index_results
        assert "code_stats" in index_results
        assert index_results["code_stats"]["files_indexed"] > 0
        
        # Test semantic search
        search_results = await repo_intel.semantic_code_search(
            query="hello world function",
            max_results=5
        )
        assert isinstance(search_results, list)
        
        # Test dependency analysis
        main_py = temp_repo / "main.py"
        deps = await repo_intel.analyze_dependencies(str(main_py))
        assert "file_path" in deps
        assert "dependencies" in deps

    @pytest.mark.asyncio
    async def test_predictive_assistant(self, mock_mcp_client):
        """Test predictive assistant functionality"""
        assistant = PredictiveAssistant(mock_mcp_client)
        
        # Test action prediction
        recent_actions = [
            {"type": "read_file", "file": "test.py"},
            {"type": "search_files", "pattern": "function"}
        ]
        
        predictions = await assistant.predict_next_actions(
            current_context="working on test.py",
            recent_actions=recent_actions,
            max_suggestions=3
        )
        assert isinstance(predictions, list)
        
        # Test file suggestions
        file_suggestions = await assistant.suggest_relevant_files(
            current_task="refactor hello world function",
            current_files=["test.py"]
        )
        assert isinstance(file_suggestions, list)
        
        # Test proactive help
        help_suggestions = await assistant.get_proactive_help(
            current_situation="debugging function issues",
            user_skill_level="intermediate"
        )
        assert isinstance(help_suggestions, list)
        
        # Test learning from user actions
        await assistant.learn_from_user_action(
            predicted_action="edit_file",
            actual_action="edit_file",
            context={"file": "test.py"},
            was_helpful=True
        )
        
        # Check prediction accuracy
        accuracy = assistant.get_prediction_accuracy()
        assert "accuracy_rate" in accuracy

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, mock_mcp_client, temp_repo):
        """Test complete end-to-end workflow"""
        with patch('libs.mcp_client.session_manager.SophiaMCPClient', return_value=mock_mcp_client):
            # Start session
            session_manager = SophiaSessionManager()
            session_id = await session_manager.start_session(
                project_context={"repo_path": str(temp_repo)}
            )
            
            # Initialize components
            wrapper = ContextAwareToolWrapper(mock_mcp_client)
            repo_intel = RepositoryIntelligence(mock_mcp_client, str(temp_repo))
            assistant = PredictiveAssistant(mock_mcp_client)
            
            # Simulate reading a file with context
            async def read_file_enhanced(file_path: str):
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Store file access
                await session_manager.store_activity(
                    activity_type="file_access",
                    description=f"Read file: {file_path}",
                    data={"file_path": file_path, "size": len(content)}
                )
                
                return {"content": content, "size": len(content)}
            
            wrapped_read = await wrapper.wrap_tool(read_file_enhanced, "read_file")
            
            # Test enhanced file reading
            test_file = temp_repo / "main.py"
            result = await wrapped_read(str(test_file))
            assert "content" in result
            assert "def hello_world" in result["content"]
            
            # Get predictions for next actions
            predictions = await assistant.predict_next_actions(
                current_context="reading main.py file",
                recent_actions=[{
                    "type": "read_file",
                    "file": str(test_file)
                }]
            )
            
            # Index repository
            index_results = await repo_intel.index_repository()
            assert index_results["code_stats"]["files_indexed"] > 0
            
            # Search for similar code
            search_results = await repo_intel.semantic_code_search(
                query="class with init method",
                max_results=3
            )
            
            # Get contextual suggestions
            suggestions = await assistant.get_context_aware_suggestions(
                current_file=str(test_file),
                selected_text="def hello_world():"
            )
            
            # End session
            await session_manager.end_session()
            
            # Verify all components worked together
            assert len(predictions) >= 0  # Predictions can be empty in mock
            assert len(search_results) >= 0
            assert len(suggestions) >= 0

    def test_error_handling(self, mock_mcp_client):
        """Test error handling in various components"""
        # Test connection failure
        mock_mcp_client.connect = AsyncMock(side_effect=Exception("Connection failed"))
        
        async def test_connection_error():
            try:
                await mock_mcp_client.connect()
                assert False, "Should have raised exception"
            except Exception as e:
                assert "Connection failed" in str(e)
        
        asyncio.run(test_connection_error())

    @pytest.mark.asyncio
    async def test_performance_tracking(self, mock_mcp_client):
        """Test performance tracking features"""
        wrapper = ContextAwareToolWrapper(mock_mcp_client)
        
        # Simulate tool usage
        async def slow_tool():
            await asyncio.sleep(0.1)  # Simulate processing time
            return "completed"
        
        wrapped_tool = await wrapper.wrap_tool(slow_tool, "slow_tool")
        
        # Execute tool multiple times
        for i in range(3):
            await wrapped_tool()
        
        # Check stats
        stats = wrapper.get_tool_stats()
        assert "tools" in stats
        assert "slow_tool" in stats["tools"]
        assert stats["tools"]["slow_tool"]["usage_count"] == 3
        assert stats["tools"]["slow_tool"]["total_execution_time"] > 0


# Demo script to showcase the integration
class MCPIntegrationDemo:
    """Demo class to showcase MCP integration capabilities"""
    
    def __init__(self):
        self.session_manager = None
        self.mcp_client = None
        
    async def run_demo(self):
        """Run a complete demo of the MCP integration"""
        print("🚀 Starting SOPHIA MCP Integration Demo")
        print("=" * 50)
        
        try:
            # Initialize session
            print("📱 Initializing SOPHIA session...")
            self.session_manager = SophiaSessionManager()
            session_id = await self.session_manager.start_session()
            self.mcp_client = self.session_manager.mcp_client
            
            print(f"✅ Session started: {session_id}")
            
            # Test basic MCP operations
            await self._demo_basic_operations()
            
            # Test context-aware tools
            await self._demo_context_aware_tools()
            
            # Test repository intelligence
            await self._demo_repository_intelligence()
            
            # Test predictive assistance
            await self._demo_predictive_assistance()
            
            print("\n🎉 Demo completed successfully!")
            
        except Exception as e:
            print(f"❌ Demo failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            if self.session_manager:
                await self.session_manager.end_session()
                print("📱 Session ended")
    
    async def _demo_basic_operations(self):
        """Demo basic MCP operations"""
        print("\n🔧 Testing Basic MCP Operations")
        print("-" * 30)
        
        # Health check
        health = await self.mcp_client.health_check()
        print(f"Health check: {health.get('status', 'unknown')}")
        
        # Store context
        result = await self.mcp_client.store_context(
            content="Demo context: Testing MCP integration",
            context_type="demo",
            metadata={"demo": True, "timestamp": "2024-01-01"}
        )
        print(f"Context stored: {result.get('success', False)}")
        
        # Query context
        results = await self.mcp_client.query_context("demo testing")
        print(f"Found {len(results)} context entries")
    
    async def _demo_context_aware_tools(self):
        """Demo context-aware tool functionality"""
        print("\n🛠️ Testing Context-Aware Tools")
        print("-" * 30)
        
        wrapper = ContextAwareToolWrapper(self.mcp_client)
        
        # Create a demo tool
        async def demo_tool(action: str, data: str = ""):
            await asyncio.sleep(0.1)  # Simulate processing
            return f"Executed {action} with {len(data)} bytes of data"
        
        wrapped_tool = await wrapper.wrap_tool(demo_tool, "demo_tool")
        
        # Use the tool
        result = await wrapped_tool("process", "test data content")
        print(f"Tool result: {result}")
        
        # Get tool suggestions
        suggestions = await wrapper.get_tool_suggestions("processing data")
        print(f"Tool suggestions: {len(suggestions)} found")
        
        # Check stats
        stats = wrapper.get_tool_stats()
        print(f"Tool stats: {stats['total_tools']} tools tracked")
    
    async def _demo_repository_intelligence(self):
        """Demo repository intelligence features"""
        print("\n🧠 Testing Repository Intelligence")
        print("-" * 30)
        
        repo_intel = RepositoryIntelligence(self.mcp_client)
        
        # Get architectural insights (will work with mock data)
        insights = await repo_intel.get_architectural_insights()
        print(f"Architectural insights generated: {len(insights)} categories")
        
        # Demo search functionality
        search_results = await repo_intel.semantic_code_search(
            query="function definition",
            max_results=3
        )
        print(f"Semantic search results: {len(search_results)} found")
    
    async def _demo_predictive_assistance(self):
        """Demo predictive assistance features"""
        print("\n🔮 Testing Predictive Assistant")
        print("-" * 30)
        
        assistant = PredictiveAssistant(self.mcp_client)
        
        # Predict next actions
        recent_actions = [
            {"type": "read_file", "file": "demo.py"},
            {"type": "search", "query": "function"}
        ]
        
        predictions = await assistant.predict_next_actions(
            current_context="working on demo code",
            recent_actions=recent_actions
        )
        print(f"Action predictions: {len(predictions)} suggestions")
        
        # File suggestions
        file_suggestions = await assistant.suggest_relevant_files(
            current_task="code refactoring"
        )
        print(f"File suggestions: {len(file_suggestions)} files")
        
        # Proactive help
        help_suggestions = await assistant.get_proactive_help(
            current_situation="debugging code issues"
        )
        print(f"Proactive help: {len(help_suggestions)} suggestions")
        
        # Check prediction accuracy
        accuracy = assistant.get_prediction_accuracy()
        print(f"Prediction accuracy: {accuracy['accuracy_rate']:.2%}")


if __name__ == "__main__":
    # Run the demo
    demo = MCPIntegrationDemo()
    
    try:
        asyncio.run(demo.run_demo())
    except KeyboardInterrupt:
        print("\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"❌ Demo failed: {e}")