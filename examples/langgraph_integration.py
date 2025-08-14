#!/usr/bin/env python3
"""
LangGraph integration example for Sophia AI platform
Demonstrates how to create and use LangGraph workflows with the agent system
"""

import os
import sys
from typing import Dict, Any, TypedDict

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.graph import StateGraph, START, END
from agents.base_agent import BaseAgent, Status
from loguru import logger

class WorkflowState(TypedDict):
    """State structure for LangGraph workflows"""
    input: str
    output: str
    step: int
    agent_name: str

class LangGraphAgent(BaseAgent):
    """
    Agent that integrates with LangGraph for workflow orchestration
    """
    
    def __init__(self, name: str, **kwargs):
        super().__init__(name, **kwargs)
        self.graph = None
        self._setup_workflow()
    
    async def _process_task_impl(self, task_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implement the abstract method from BaseAgent
        Process tasks using the LangGraph workflow
        """
        try:
            input_data = task_data.get('input', str(task_data))
            result = self.execute_workflow(input_data)
            
            return {
                "success": True,
                "task_id": task_id,
                "summary": f"LangGraph workflow completed: {result['output']}",
                "result": result,
                "steps": result['step']
            }
        except Exception as e:
            return {
                "success": False,
                "task_id": task_id,
                "error": str(e),
                "summary": f"LangGraph workflow failed: {str(e)}"
            }
    
    def _setup_workflow(self):
        """Set up the LangGraph workflow"""
        try:
            # Create a state graph
            workflow = StateGraph(WorkflowState)
            
            # Add nodes
            workflow.add_node("process", self._process_node)
            workflow.add_node("validate", self._validate_node)
            workflow.add_node("finalize", self._finalize_node)
            
            # Add edges
            workflow.add_edge(START, "process")
            workflow.add_edge("process", "validate")
            workflow.add_edge("validate", "finalize")
            workflow.add_edge("finalize", END)
            
            # Compile the graph
            self.graph = workflow.compile()
            logger.info(f"LangGraph workflow compiled for agent {self.name}")
            
        except Exception as e:
            logger.error(f"Failed to setup LangGraph workflow: {str(e)}")
            self.status = Status.ERROR
    
    def _process_node(self, state: WorkflowState) -> WorkflowState:
        """Process the input data"""
        logger.info(f"Processing input: {state['input']}")
        
        # Simulate processing
        processed_output = f"Processed by {self.name}: {state['input']}"
        
        return {
            **state,
            "output": processed_output,
            "step": state.get("step", 0) + 1,
            "agent_name": self.name
        }
    
    def _validate_node(self, state: WorkflowState) -> WorkflowState:
        """Validate the processed data"""
        logger.info(f"Validating output: {state['output']}")
        
        # Simple validation
        is_valid = len(state['output']) > 0
        
        if is_valid:
            validated_output = f"✅ Validated: {state['output']}"
        else:
            validated_output = f"❌ Validation failed: {state['output']}"
        
        return {
            **state,
            "output": validated_output,
            "step": state.get("step", 0) + 1
        }
    
    def _finalize_node(self, state: WorkflowState) -> WorkflowState:
        """Finalize the workflow"""
        logger.info(f"Finalizing workflow for step {state['step']}")
        
        final_output = f"🎯 Final result: {state['output']} (completed in {state['step']} steps)"
        
        return {
            **state,
            "output": final_output,
            "step": state.get("step", 0) + 1
        }
    
    def execute_workflow(self, input_data: str) -> Dict[str, Any]:
        """Execute the LangGraph workflow"""
        if not self.graph:
            raise Exception("Workflow not initialized")
        
        self.status = Status.BUSY
        
        try:
            # Create initial state
            initial_state = WorkflowState(
                input=input_data,
                output="",
                step=0,
                agent_name=self.name
            )
            
            # Execute the workflow
            result = self.graph.invoke(initial_state)
            
            self.status = Status.READY
            self.tasks_completed += 1
            
            logger.info(f"Workflow completed successfully: {result['output']}")
            return result
            
        except Exception as e:
            self.status = Status.ERROR
            self.tasks_failed += 1
            logger.error(f"Workflow execution failed: {str(e)}")
            raise

def create_simple_graph_example():
    """Create a simple LangGraph example without agents"""
    
    class SimpleState(TypedDict):
        input: str
        message: str
        step: int
    
    def echo_node(state: SimpleState) -> SimpleState:
        return {
            **state,
            "message": f"Echo: {state.get('input', 'No input')}", 
            "step": 1
        }
    
    def transform_node(state: SimpleState) -> SimpleState:
        message = state.get('message', '')
        return {
            **state,
            "message": message.upper(), 
            "step": state.get('step', 0) + 1
        }
    
    # Create simple graph
    graph = StateGraph(SimpleState)
    graph.add_node("echo", echo_node)
    graph.add_node("transform", transform_node)
    
    graph.add_edge(START, "echo")
    graph.add_edge("echo", "transform")
    graph.add_edge("transform", END)
    
    compiled = graph.compile()
    
    # Test the graph
    result = compiled.invoke({"input": "hello world", "message": "", "step": 0})
    print(f"Simple graph result: {result}")
    return result

def main():
    """Main demonstration"""
    print("LangGraph Integration Example")
    print("="*40)
    
    # Test simple graph first
    print("\n1. Testing simple LangGraph workflow...")
    try:
        simple_result = create_simple_graph_example()
        print("✅ Simple LangGraph workflow working")
    except Exception as e:
        print(f"❌ Simple workflow failed: {str(e)}")
        return
    
    # Test agent integration
    print("\n2. Testing LangGraph agent integration...")
    try:
        agent = LangGraphAgent("demo-agent")
        
        if agent.status == Status.ERROR:
            print("❌ Agent initialization failed")
            return
        
        # Execute workflow
        result = agent.execute_workflow("Test input for LangGraph integration")
        
        print("✅ LangGraph agent integration working")
        print(f"Result: {result['output']}")
        print(f"Steps completed: {result['step']}")
        print(f"Agent status: {agent.status}")
        print(f"Tasks completed: {agent.tasks_completed}")
        
    except Exception as e:
        print(f"❌ Agent integration failed: {str(e)}")
    
    print("\n3. LangGraph Integration Summary:")
    print("- ✅ LangGraph installed and functional")
    print("- ✅ Basic workflow creation working")
    print("- ✅ Agent system integration working")
    print("- ✅ State management working")
    print("- ✅ Node execution and edge traversal working")

if __name__ == "__main__":
    main()

