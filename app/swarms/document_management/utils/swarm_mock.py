#!/usr/bin/env python3
"""
Mock Swarm Module for Document Management Testing

This provides a lightweight mock of the swarm.Agent class for testing
the document management system without requiring the full swarm framework.
"""

from typing import Dict, Any, Optional, List


class Agent:
    """Mock Agent class that mimics the behavior of swarm.Agent"""
    
    def __init__(self, name: str = "MockAgent", instructions: str = ""):
        self.name = name
        self.instructions = instructions
        self.context = {}
        self.tools = []
    
    def __repr__(self):
        return f"Agent(name='{self.name}')"
    
    def add_tool(self, tool):
        """Add a tool to the agent"""
        self.tools.append(tool)
    
    def set_context(self, context: Dict[str, Any]):
        """Set agent context"""
        self.context.update(context)
    
    def get_instructions(self) -> str:
        """Get agent instructions"""
        return self.instructions
    
    async def execute_task(self, task: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Mock task execution"""
        if context:
            self.set_context(context)
        
        # Simple mock response based on agent name
        if "Discovery" in self.name:
            return f"Mock discovery result for: {task}"
        elif "Classification" in self.name:
            return f"Mock classification result for: {task}"
        elif "Cleanup" in self.name:
            return f"Mock cleanup result for: {task}"
        else:
            return f"Mock result from {self.name}: {task}"


# For backwards compatibility, create a swarm-like module structure
class MockSwarmModule:
    Agent = Agent


# This will be imported as 'swarm' in the document management modules
__all__ = ['Agent']