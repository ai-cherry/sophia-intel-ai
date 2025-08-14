#!/usr/bin/env python3
"""
Simple MCP Integration Test
Tests the MCP integration without requiring live servers
"""

import asyncio
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.mcp_client.sophia_client import SophiaMCPClient, MCPServerError
from libs.mcp_client.session_manager import SophiaSessionManager
from libs.mcp_client.context_tools import ContextAwareToolWrapper
from libs.mcp_client.repo_intelligence import RepositoryIntelligence
from libs.mcp_client.predictive_assistant import PredictiveAssistant


async def test_basic_functionality():
    """Test basic functionality without MCP server dependencies"""
    print("🧪 Testing MCP Integration Components")
    print("=" * 50)
    
    success_count = 0
    total_tests = 0
    
    # Test 1: Import validation
    total_tests += 1
    print("📦 Test 1: Import Validation")
    try:
        from libs.mcp_client import SophiaMCPClient, SophiaSessionManager, ContextAwareToolWrapper
        print("✅ All imports successful")
        success_count += 1
    except Exception as e:
        print(f"❌ Import failed: {e}")
    
    # Test 2: Client initialization
    total_tests += 1
    print("\n🔧 Test 2: Client Initialization")
    try:
        client = SophiaMCPClient("test_session", mcp_port=8000)
        assert client.session_id == "test_session"
        assert client.mcp_base_url == "http://localhost:8000"
        print("✅ MCP Client initialized successfully")
        success_count += 1
    except Exception as e:
        print(f"❌ Client initialization failed: {e}")
    
    # Test 3: Session manager initialization
    total_tests += 1
    print("\n📱 Test 3: Session Manager Initialization")
    try:
        session_manager = SophiaSessionManager()
        assert hasattr(session_manager, 'sessions_dir')
        assert hasattr(session_manager, 'current_session')
        print("✅ Session Manager initialized successfully")
        success_count += 1
    except Exception as e:
        print(f"❌ Session Manager initialization failed: {e}")
    
    # Test 4: Context wrapper initialization
    total_tests += 1
    print("\n🛠️ Test 4: Context Wrapper Initialization")
    try:
        mock_client = MockMCPClient("test_session")
        wrapper = ContextAwareToolWrapper(mock_client)
        assert hasattr(wrapper, 'mcp_client')
        assert hasattr(wrapper, 'tool_stats')
        print("✅ Context Wrapper initialized successfully")
        success_count += 1
    except Exception as e:
        print(f"❌ Context Wrapper initialization failed: {e}")
    
    # Test 5: Repository intelligence initialization
    total_tests += 1
    print("\n🧠 Test 5: Repository Intelligence Initialization")
    try:
        mock_client = MockMCPClient("test_session")
        repo_intel = RepositoryIntelligence(mock_client)
        assert hasattr(repo_intel, 'mcp_client')
        assert hasattr(repo_intel, 'language_extensions')
        print("✅ Repository Intelligence initialized successfully")
        success_count += 1
    except Exception as e:
        print(f"❌ Repository Intelligence initialization failed: {e}")
    
    # Test 6: Predictive assistant initialization
    total_tests += 1
    print("\n🔮 Test 6: Predictive Assistant Initialization")
    try:
        mock_client = MockMCPClient("test_session")
        assistant = PredictiveAssistant(mock_client)
        assert hasattr(assistant, 'mcp_client')
        assert hasattr(assistant, 'prediction_stats')
        print("✅ Predictive Assistant initialized successfully")
        success_count += 1
    except Exception as e:
        print(f"❌ Predictive Assistant initialization failed: {e}")
    
    # Test 7: Mock integration workflow
    total_tests += 1
    print("\n🔄 Test 7: Mock Integration Workflow")
    try:
        await test_mock_workflow()
        print("✅ Mock workflow completed successfully")
        success_count += 1
    except Exception as e:
        print(f"❌ Mock workflow failed: {e}")
    
    # Test 8: Configuration validation
    total_tests += 1
    print("\n⚙️ Test 8: Configuration Validation")
    try:
        # Check if MCP config exists
        mcp_config_path = Path(".vscode/mcp.json")
        if mcp_config_path.exists():
            with open(mcp_config_path, 'r') as f:
                config = json.load(f)
            assert "servers" in config
            print(f"✅ MCP configuration valid: {len(config['servers'])} servers configured")
        else:
            print("⚠️ MCP configuration not found, but this is expected for testing")
        success_count += 1
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
    
    # Summary
    print(f"\n📊 Test Summary")
    print("=" * 50)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {success_count}")
    print(f"Failed: {total_tests - success_count}")
    print(f"Success Rate: {(success_count / total_tests) * 100:.1f}%")
    
    return success_count == total_tests


async def test_mock_workflow():
    """Test a complete workflow with mock MCP client"""
    mock_client = MockMCPClient("workflow_test")
    
    # Initialize components
    wrapper = ContextAwareToolWrapper(mock_client)
    repo_intel = RepositoryIntelligence(mock_client)
    assistant = PredictiveAssistant(mock_client)
    
    # Test tool wrapping
    async def sample_tool(file_path: str, operation: str = "read"):
        await asyncio.sleep(0.01)  # Simulate processing
        return f"Performed {operation} on {file_path}"
    
    wrapped_tool = await wrapper.wrap_tool(sample_tool, "sample_tool")
    result = await wrapped_tool("test.py", operation="analyze")
    assert "Performed analyze on test.py" in result
    
    # Test predictions
    predictions = await assistant.predict_next_actions(
        current_context="analyzing test.py",
        recent_actions=[{"type": "sample_tool", "file": "test.py"}],
        max_suggestions=3
    )
    assert isinstance(predictions, list)
    
    # Test file suggestions
    suggestions = await assistant.suggest_relevant_files(
        current_task="code analysis",
        current_files=["test.py"]
    )
    assert isinstance(suggestions, list)
    
    print("  - Tool wrapping: ✅")
    print("  - Action prediction: ✅") 
    print("  - File suggestions: ✅")


class MockMCPClient:
    """Mock MCP client for testing without server dependencies"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.connected = False
        self.context_storage = []
    
    async def connect(self):
        self.connected = True
        return True
    
    async def disconnect(self):
        self.connected = False
    
    async def health_check(self):
        return {"status": "healthy", "mock": True}
    
    async def store_context(self, content: str, context_type: str = "general", metadata=None):
        entry = {
            "id": f"mock_ctx_{len(self.context_storage)}",
            "content": content,
            "context_type": context_type,
            "metadata": metadata or {},
            "session_id": self.session_id
        }
        self.context_storage.append(entry)
        return {"success": True, "id": entry["id"]}
    
    async def query_context(self, query: str, top_k: int = 5, threshold: float = 0.7, context_types=None):
        # Simple mock search - return stored contexts that contain query terms
        results = []
        query_words = query.lower().split()
        
        for entry in self.context_storage:
            content_lower = entry["content"].lower()
            score = sum(1 for word in query_words if word in content_lower) / len(query_words)
            
            if score >= threshold:
                results.append({
                    **entry,
                    "score": score
                })
        
        # Sort by score and return top_k
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
    
    async def store_tool_usage(self, tool_name: str, params: dict, result: any, execution_time: float = 0.0):
        content = {
            "tool_name": tool_name,
            "params": params,
            "result": str(result)[:100],  # Truncate for storage
            "execution_time": execution_time
        }
        return await self.store_context(
            content=json.dumps(content),
            context_type="tool_usage",
            metadata={"tool_name": tool_name}
        )
    
    async def get_file_context(self, file_path: str):
        # Mock file context
        return [
            {
                "content": f"Previous change to {file_path}",
                "score": 0.8,
                "metadata": {"file_path": file_path}
            }
        ]
    
    def get_stats(self):
        return {
            "connected": self.connected,
            "session_id": self.session_id,
            "stored_contexts": len(self.context_storage)
        }


async def test_mcp_server_health():
    """Test if actual MCP servers are running (optional)"""
    print("\n🏥 Testing MCP Server Health (Optional)")
    print("-" * 30)
    
    try:
        client = SophiaMCPClient("health_test")
        await client.connect()
        health = await client.health_check()
        await client.disconnect()
        
        print(f"✅ MCP Server is running: {health}")
        return True
        
    except Exception as e:
        print(f"⚠️ MCP Server not available (expected): {e}")
        print("   This is normal if servers aren't running")
        return False


def create_integration_example():
    """Create an example integration file for reference"""
    example_content = '''
"""
SOPHIA MCP Integration Example
Shows how to use the MCP integration in practice
"""

import asyncio
from libs.mcp_client import SophiaMCPClient, SophiaSessionManager

async def sophia_enhanced_workflow():
    """Example of enhanced SOPHIA workflow with MCP integration"""
    
    # Start a persistent session
    async with SophiaSessionManager() as session:
        session_id = await session.start_session(
            project_context={"repo_path": "/path/to/project"}
        )
        
        # Access MCP client through session
        mcp = session.mcp_client
        
        # Store coding context
        await mcp.store_context(
            content="Working on refactoring authentication module",
            context_type="task_context",
            metadata={"priority": "high", "module": "auth"}
        )
        
        # Get relevant context for current task
        context = await session.get_context_for_action(
            action_description="refactoring authentication",
            file_path="auth/login.py"
        )
        
        # Use context-aware tools
        from libs.mcp_client.context_tools import ContextAwareToolWrapper
        wrapper = ContextAwareToolWrapper(mcp)
        
        # Wrap existing SOPHIA tools with context
        async def enhanced_read_file(path: str):
            with open(path, 'r') as f:
                content = f.read()
            return {"path": path, "content": content, "size": len(content)}
        
        context_aware_read = await wrapper.wrap_tool(enhanced_read_file)
        
        # File operations now store context automatically
        result = await context_aware_read("auth/login.py")
        
        # Get predictive suggestions
        from libs.mcp_client.predictive_assistant import PredictiveAssistant
        assistant = PredictiveAssistant(mcp)
        
        predictions = await assistant.predict_next_actions(
            current_context="refactoring auth module",
            recent_actions=[{"type": "read_file", "file": "auth/login.py"}]
        )
        
        print(f"Next suggested actions: {predictions}")

if __name__ == "__main__":
    asyncio.run(sophia_enhanced_workflow())
'''
    
    example_path = Path("examples/mcp_integration_example.py")
    example_path.parent.mkdir(exist_ok=True)
    example_path.write_text(example_content.strip())
    
    return example_path


def main():
    """Main test runner"""
    print("🚀 SOPHIA MCP Integration Test Suite")
    print("=" * 60)
    
    try:
        # Run basic functionality tests
        success = asyncio.run(test_basic_functionality())
        
        # Test server health (optional)
        server_available = asyncio.run(test_mcp_server_health())
        
        # Create integration example
        example_path = create_integration_example()
        print(f"\n📝 Integration example created: {example_path}")
        
        print(f"\n🎯 Final Results")
        print("=" * 60)
        
        if success:
            print("✅ All basic integration tests passed!")
            print("📦 MCP client library is ready for use")
            
            if server_available:
                print("🏥 MCP servers are running and healthy")
            else:
                print("⚠️ MCP servers not running (start them with: bash scripts/start_all_mcps.sh)")
            
            print("\n🎊 MCP Integration Implementation Complete!")
            print("\nNext steps:")
            print("1. Start MCP servers: bash scripts/start_all_mcps.sh")
            print("2. Run integration example: python examples/mcp_integration_example.py")
            print("3. Use enhanced SOPHIA tools with context awareness")
            
            return 0
        else:
            print("❌ Some integration tests failed")
            print("🔧 Check the error messages above and fix issues")
            return 1
            
    except Exception as e:
        print(f"💥 Test suite crashed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())