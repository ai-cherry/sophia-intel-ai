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