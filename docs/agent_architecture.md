# Agent Architecture

This document outlines the agent architecture for the Sophia Intel platform, including how to write and register agents using LangGraph and the Enhanced MCP Server.

## Overview

The Sophia Intel platform uses a modern agent architecture built on:

- **LangGraph** - For agent workflow orchestration
- **Enhanced MCP Server** - For unified model context protocol
- **AI Router** - For intelligent model selection
- **BaseAgent** - For standardized agent interfaces

## Architecture Components

### 1. Enhanced MCP Server

The Enhanced MCP Server (`mcp_servers/enhanced_unified_server.py`) provides:

- **Unified API** - Single endpoint for all AI operations
- **Context Management** - Session-based context storage and retrieval
- **Model Routing** - Automatic selection of optimal AI models
- **Memory Services** - Persistent memory across conversations
- **Streaming Support** - Real-time response streaming

### 2. AI Router

The AI Router (`mcp_servers/ai_router.py`) handles:

- **Model Selection** - Chooses optimal models based on task type
- **Cost Optimization** - Balances cost vs. performance
- **Quality Assurance** - Ensures appropriate quality levels
- **Fallback Strategies** - Handles model failures gracefully

### 3. Base Agent Framework

All agents inherit from `BaseAgent` (`agents/base_agent.py`) which provides:

- **Standardized Interface** - Consistent agent API
- **Task Processing** - Abstract task processing methods
- **Error Handling** - Built-in error management
- **Logging** - Comprehensive logging support

## Creating Agents

### 1. Basic Agent Structure

```python
from agents.base_agent import BaseAgent
from typing import Dict, Any, Optional
from loguru import logger

class MyCustomAgent(BaseAgent):
    """Custom agent for specific tasks"""
    
    def __init__(self, name: str = "MyCustomAgent"):
        super().__init__(name)
        self.capabilities = ["task1", "task2", "task3"]
    
    async def _process_task_impl(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implement the core task processing logic
        
        Args:
            task: Task dictionary with 'type', 'data', and optional metadata
            
        Returns:
            Result dictionary with 'success', 'data', and optional metadata
        """
        task_type = task.get("type")
        task_data = task.get("data", {})
        
        try:
            if task_type == "task1":
                result = await self._handle_task1(task_data)
            elif task_type == "task2":
                result = await self._handle_task2(task_data)
            else:
                raise ValueError(f"Unsupported task type: {task_type}")
            
            return {
                "success": True,
                "data": result,
                "agent": self.name
            }
            
        except Exception as e:
            logger.error(f"Task processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": self.name
            }
    
    async def _handle_task1(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle task type 1"""
        # Implement task-specific logic
        return {"result": "task1_completed"}
    
    async def _handle_task2(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle task type 2"""
        # Implement task-specific logic
        return {"result": "task2_completed"}
```

### 2. LangGraph Integration

For complex workflows, integrate with LangGraph:

```python
from langgraph import StateGraph, END
from typing import TypedDict, Annotated
import operator

class AgentState(TypedDict):
    """State shared across agent workflow"""
    messages: Annotated[list, operator.add]
    current_task: str
    context: Dict[str, Any]
    result: Optional[Dict[str, Any]]

class LangGraphAgent(BaseAgent):
    """Agent using LangGraph for workflow orchestration"""
    
    def __init__(self, name: str = "LangGraphAgent"):
        super().__init__(name)
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("analyze", self._analyze_task)
        workflow.add_node("process", self._process_task)
        workflow.add_node("validate", self._validate_result)
        
        # Add edges
        workflow.add_edge("analyze", "process")
        workflow.add_edge("process", "validate")
        workflow.add_edge("validate", END)
        
        # Set entry point
        workflow.set_entry_point("analyze")
        
        return workflow.compile()
    
    async def _process_task_impl(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process task using LangGraph workflow"""
        initial_state = AgentState(
            messages=[],
            current_task=task.get("type", "unknown"),
            context=task.get("data", {}),
            result=None
        )
        
        final_state = await self.workflow.ainvoke(initial_state)
        return final_state["result"]
    
    async def _analyze_task(self, state: AgentState) -> AgentState:
        """Analyze the incoming task"""
        # Add analysis logic
        state["messages"].append("Task analyzed")
        return state
    
    async def _process_task(self, state: AgentState) -> AgentState:
        """Process the task"""
        # Add processing logic
        state["messages"].append("Task processed")
        return state
    
    async def _validate_result(self, state: AgentState) -> AgentState:
        """Validate the result"""
        # Add validation logic
        state["result"] = {
            "success": True,
            "data": {"processed": True},
            "messages": state["messages"]
        }
        return state
```

### 3. MCP Server Integration

Integrate with the Enhanced MCP Server:

```python
import aiohttp
from config.config import settings

class MCPIntegratedAgent(BaseAgent):
    """Agent that integrates with MCP Server"""
    
    def __init__(self, name: str = "MCPIntegratedAgent"):
        super().__init__(name)
        self.mcp_url = f"http://{settings.HOST}:{settings.MCP_PORT}"
    
    async def _process_task_impl(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process task using MCP Server"""
        try:
            # Use MCP Server for AI operations
            ai_response = await self._call_mcp_server(task)
            
            # Process the AI response
            result = await self._process_ai_response(ai_response)
            
            return {
                "success": True,
                "data": result,
                "agent": self.name
            }
            
        except Exception as e:
            logger.error(f"MCP integration failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": self.name
            }
    
    async def _call_mcp_server(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Call the MCP Server for AI processing"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "prompt": task.get("prompt", ""),
                "task_type": task.get("type", "GENERAL_CHAT"),
                "session_id": task.get("session_id"),
                "use_context": True
            }
            
            async with session.post(
                f"{self.mcp_url}/ai/chat",
                json=payload
            ) as response:
                return await response.json()
    
    async def _process_ai_response(self, ai_response: Dict[str, Any]) -> Dict[str, Any]:
        """Process the AI response"""
        # Add custom processing logic
        return {
            "ai_response": ai_response,
            "processed_at": "timestamp",
            "agent_processing": "completed"
        }
```

## Agent Registration

### 1. Register with Enhanced MCP Server

Add your agent to the MCP Server:

```python
# In mcp_servers/enhanced_unified_server.py
from agents.my_custom_agent import MyCustomAgent

# Initialize agent
custom_agent = MyCustomAgent()

# Add endpoint for agent
@app.post("/agents/custom")
async def custom_agent_endpoint(request: AgentRequest):
    """Custom agent endpoint"""
    task = {
        "type": request.task_type,
        "data": request.data,
        "session_id": request.session_id
    }
    
    result = await custom_agent.process_task(task)
    return result
```

### 2. Register with Orchestrator

Add your agent to the orchestrator:

```python
# In services/orchestrator.py
from agents.my_custom_agent import MyCustomAgent

class Orchestrator:
    def __init__(self):
        self.agents = {
            "custom": MyCustomAgent(),
            # ... other agents
        }
    
    async def route_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Route task to appropriate agent"""
        agent_type = task.get("agent_type", "default")
        agent = self.agents.get(agent_type)
        
        if agent:
            return await agent.process_task(task)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
```

## Best Practices

### 1. Error Handling

```python
async def _process_task_impl(self, task: Dict[str, Any]) -> Dict[str, Any]:
    """Process task with proper error handling"""
    try:
        # Validate input
        self._validate_task(task)
        
        # Process task
        result = await self._execute_task(task)
        
        # Validate output
        self._validate_result(result)
        
        return {
            "success": True,
            "data": result,
            "agent": self.name
        }
        
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        return {"success": False, "error": f"Validation failed: {e}"}
        
    except ProcessingError as e:
        logger.error(f"Processing error: {e}")
        return {"success": False, "error": f"Processing failed: {e}"}
        
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return {"success": False, "error": f"Unexpected error: {e}"}
```

### 2. Logging

```python
from loguru import logger

class LoggingAgent(BaseAgent):
    """Agent with comprehensive logging"""
    
    async def _process_task_impl(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process task with logging"""
        task_id = task.get("id", "unknown")
        
        logger.info(f"Starting task {task_id} for agent {self.name}")
        
        try:
            result = await self._execute_task(task)
            
            logger.info(f"Task {task_id} completed successfully")
            logger.debug(f"Task {task_id} result: {result}")
            
            return {"success": True, "data": result}
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            raise
```

### 3. Testing

```python
import pytest
from agents.my_custom_agent import MyCustomAgent

@pytest.fixture
async def agent():
    """Create agent for testing"""
    return MyCustomAgent()

@pytest.mark.asyncio
async def test_agent_task_processing(agent):
    """Test agent task processing"""
    task = {
        "type": "task1",
        "data": {"input": "test_data"}
    }
    
    result = await agent.process_task(task)
    
    assert result["success"] is True
    assert "data" in result
    assert result["agent"] == "MyCustomAgent"

@pytest.mark.asyncio
async def test_agent_error_handling(agent):
    """Test agent error handling"""
    task = {
        "type": "invalid_task",
        "data": {}
    }
    
    result = await agent.process_task(task)
    
    assert result["success"] is False
    assert "error" in result
```

## Example: Complete Agent Implementation

```python
from agents.base_agent import BaseAgent
from mcp_servers.ai_router import AIRouter, TaskRequest, TaskType
from typing import Dict, Any, Optional
from loguru import logger
import aiohttp

class DataAnalysisAgent(BaseAgent):
    """Agent specialized in data analysis tasks"""
    
    def __init__(self, name: str = "DataAnalysisAgent"):
        super().__init__(name)
        self.ai_router = AIRouter()
        self.capabilities = [
            "data_analysis",
            "statistical_analysis", 
            "data_visualization",
            "report_generation"
        ]
    
    async def _process_task_impl(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process data analysis tasks"""
        task_type = task.get("type")
        
        if task_type not in self.capabilities:
            return {
                "success": False,
                "error": f"Unsupported task type: {task_type}"
            }
        
        try:
            # Route to appropriate handler
            if task_type == "data_analysis":
                result = await self._analyze_data(task.get("data", {}))
            elif task_type == "statistical_analysis":
                result = await self._statistical_analysis(task.get("data", {}))
            elif task_type == "data_visualization":
                result = await self._create_visualization(task.get("data", {}))
            elif task_type == "report_generation":
                result = await self._generate_report(task.get("data", {}))
            
            return {
                "success": True,
                "data": result,
                "agent": self.name,
                "task_type": task_type
            }
            
        except Exception as e:
            logger.error(f"Data analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": self.name
            }
    
    async def _analyze_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform data analysis using AI Router"""
        # Create AI request for data analysis
        ai_request = TaskRequest(
            prompt=f"Analyze this data: {data}",
            task_type=TaskType.ANALYSIS,
            quality_requirement="high"
        )
        
        # Route to optimal model
        decision = await self.ai_router.route_request(ai_request)
        response = await self.ai_router.execute_task(ai_request, decision)
        
        return {
            "analysis": response.get("content", ""),
            "model_used": decision.selected_model,
            "confidence": decision.confidence_score
        }
    
    async def _statistical_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform statistical analysis"""
        # Implementation for statistical analysis
        return {"statistics": "computed"}
    
    async def _create_visualization(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create data visualization"""
        # Implementation for visualization
        return {"visualization": "created"}
    
    async def _generate_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate analysis report"""
        # Implementation for report generation
        return {"report": "generated"}
```

## Summary

The Sophia Intel agent architecture provides:

1. **Standardized Interface** - All agents inherit from BaseAgent
2. **LangGraph Integration** - Complex workflows using state graphs
3. **MCP Server Integration** - Unified AI operations
4. **AI Router Integration** - Optimal model selection
5. **Error Handling** - Comprehensive error management
6. **Logging** - Detailed operation logging
7. **Testing** - Built-in testing support

This architecture enables rapid development of specialized agents while maintaining consistency and reliability across the platform.

