"""
Scalable SOPHIA Orchestrator with Agno + LangGraph
Production-ready multi-agent orchestration with CQRS, memory management, and monitoring
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict

import redis.asyncio as redis
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from mem0 import Memory
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import aiohttp
from loguru import logger

from config.config import settings
from services.lambda_inference_client import LambdaInferenceClient, run_lambda_inference
from services.openrouter_client import OpenRouterClient


# Simple circuit breaker implementation
class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def __enter__(self):
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = 'HALF_OPEN'
            else:
                raise Exception("Circuit breaker is OPEN")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = 'OPEN'
        else:
            self.failure_count = 0
            self.state = 'CLOSED'


# Metrics
REQUEST_COUNT = Counter('sophia_requests_total', 'Total requests', ['endpoint', 'method'])
REQUEST_DURATION = Histogram('sophia_request_duration_seconds', 'Request duration')
ACTIVE_SESSIONS = Gauge('sophia_active_sessions', 'Active user sessions')
AGENT_EXECUTIONS = Counter('sophia_agent_executions_total', 'Agent executions', ['agent_type'])
MEMORY_OPERATIONS = Counter('sophia_memory_operations_total', 'Memory operations', ['operation'])


class SessionState(TypedDict):
    """State for user session in LangGraph"""
    user_id: str
    session_id: str
    messages: List[Dict[str, Any]]
    context: Dict[str, Any]
    current_agent: Optional[str]
    task_queue: List[Dict[str, Any]]
    memory_context: Dict[str, Any]


class ScalableOrchestrator:
    """Production-ready orchestrator with CQRS, memory management, and monitoring"""
    
    def __init__(self):
        self.redis_client = None
        self.memory = None
        self.graph = None
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=30)
        self.active_sessions = {}
        
        # Initialize components
        asyncio.create_task(self._initialize())
    
    async def _initialize(self):
        """Initialize Redis, Memory, and LangGraph"""
        try:
            # Redis for queuing and session management
            self.redis_client = redis.Redis(
                host=getattr(settings, 'REDIS_HOST', 'localhost'),
                port=getattr(settings, 'REDIS_PORT', 6379),
                decode_responses=True
            )
            
            # Mem0 for unified memory management
            self.memory = Memory(
                config={
                    "vector_store": {
                        "provider": "qdrant",
                        "config": {
                            "host": getattr(settings, 'QDRANT_HOST', 'localhost'),
                            "port": getattr(settings, 'QDRANT_PORT', 6333),
                            "collection_name": "sophia_memory"
                        }
                    }
                }
            )
            
            # Build LangGraph workflow
            self._build_workflow()
            
            # Start metrics server
            start_http_server(8090)
            
            logger.info("Scalable orchestrator initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            raise
    
    def _build_workflow(self):
        """Build LangGraph workflow for agent orchestration"""
        
        # Define the workflow graph
        workflow = StateGraph(SessionState)
        
        # Add nodes for different agents
        workflow.add_node("planner", self._planner_agent)
        workflow.add_node("coder", self._coder_agent)
        workflow.add_node("researcher", self._researcher_agent)
        workflow.add_node("memory_manager", self._memory_manager)
        workflow.add_node("response_generator", self._response_generator)
        
        # Define edges and flow
        workflow.set_entry_point("planner")
        workflow.add_edge("planner", "memory_manager")
        workflow.add_conditional_edges(
            "memory_manager",
            self._route_to_agent,
            {
                "code": "coder",
                "research": "researcher", 
                "response": "response_generator"
            }
        )
        workflow.add_edge("coder", "response_generator")
        workflow.add_edge("researcher", "response_generator")
        workflow.add_edge("response_generator", END)
        
        # Compile with checkpointer for persistence
        checkpointer = MemorySaver()
        self.graph = workflow.compile(checkpointer=checkpointer)
    
    async def _planner_agent(self, state: SessionState) -> SessionState:
        """Planning agent - analyzes user request and determines workflow"""
        AGENT_EXECUTIONS.labels(agent_type='planner').inc()
        
        try:
            latest_message = state["messages"][-1] if state["messages"] else {}
            user_input = latest_message.get("content", "")
            
            # Analyze request type using circuit breaker
            with self.circuit_breaker:
                analysis = await self._analyze_request(user_input)
            
            state["context"]["plan"] = analysis
            state["current_agent"] = "planner"
            
            logger.info(f"Planner analyzed request: {analysis.get('task_type', 'unknown')}")
            return state
            
        except Exception as e:
            logger.error(f"Planner agent error: {e}")
            state["context"]["error"] = str(e)
            return state
    
    async def _memory_manager(self, state: SessionState) -> SessionState:
        """Memory management agent - handles context and personalization"""
        AGENT_EXECUTIONS.labels(agent_type='memory').inc()
        MEMORY_OPERATIONS.labels(operation='retrieve').inc()
        
        try:
            user_id = state["user_id"]
            session_id = state["session_id"]
            
            # Retrieve relevant memories
            memories = await self._get_user_memories(user_id, state["messages"][-1]["content"])
            
            # Store current interaction
            await self._store_interaction(user_id, session_id, state["messages"][-1])
            
            state["memory_context"] = {
                "relevant_memories": memories,
                "user_preferences": await self._get_user_preferences(user_id)
            }
            
            logger.info(f"Memory manager processed context for user {user_id}")
            return state
            
        except Exception as e:
            logger.error(f"Memory manager error: {e}")
            state["context"]["memory_error"] = str(e)
            return state
    
    async def _coder_agent(self, state: SessionState) -> SessionState:
        """Coding agent - handles code generation and review"""
        AGENT_EXECUTIONS.labels(agent_type='coder').inc()
        
        try:
            plan = state["context"].get("plan", {})
            user_input = state["messages"][-1]["content"]
            memory_context = state.get("memory_context", {})
            
            # Generate code with context
            code_response = await self._generate_code(user_input, memory_context)
            
            state["context"]["code_result"] = code_response
            state["current_agent"] = "coder"
            
            logger.info("Coder agent completed code generation")
            return state
            
        except Exception as e:
            logger.error(f"Coder agent error: {e}")
            state["context"]["code_error"] = str(e)
            return state
    
    async def _researcher_agent(self, state: SessionState) -> SessionState:
        """Research agent - handles web research and analysis"""
        AGENT_EXECUTIONS.labels(agent_type='researcher').inc()
        
        try:
            user_input = state["messages"][-1]["content"]
            memory_context = state.get("memory_context", {})
            
            # Perform research with context
            research_result = await self._perform_research(user_input, memory_context)
            
            state["context"]["research_result"] = research_result
            state["current_agent"] = "researcher"
            
            logger.info("Researcher agent completed research")
            return state
            
        except Exception as e:
            logger.error(f"Researcher agent error: {e}")
            state["context"]["research_error"] = str(e)
            return state
    
    async def _response_generator(self, state: SessionState) -> SessionState:
        """Response generation agent - synthesizes final response"""
        AGENT_EXECUTIONS.labels(agent_type='response').inc()
        
        try:
            context = state["context"]
            memory_context = state.get("memory_context", {})
            
            # Generate personalized response
            response = await self._generate_response(context, memory_context)
            
            # Add response to messages
            state["messages"].append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().isoformat(),
                "agent": "response_generator"
            })
            
            logger.info("Response generator completed")
            return state
            
        except Exception as e:
            logger.error(f"Response generator error: {e}")
            state["messages"].append({
                "role": "assistant", 
                "content": f"I encountered an error: {str(e)}",
                "timestamp": datetime.now().isoformat(),
                "error": True
            })
            return state
    
    def _route_to_agent(self, state: SessionState) -> str:
        """Route to appropriate agent based on plan"""
        plan = state["context"].get("plan", {})
        task_type = plan.get("task_type", "response")
        
        if "code" in task_type.lower():
            return "code"
        elif "research" in task_type.lower() or "search" in task_type.lower():
            return "research"
        else:
            return "response"
    
    async def process_message(self, user_id: str, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Process user message through the orchestrator"""
        REQUEST_COUNT.labels(endpoint='process_message', method='POST').inc()
        
        with REQUEST_DURATION.time():
            try:
                if not session_id:
                    session_id = str(uuid.uuid4())
                
                # Track active session
                ACTIVE_SESSIONS.inc()
                self.active_sessions[session_id] = time.time()
                
                # Initialize state
                initial_state = SessionState(
                    user_id=user_id,
                    session_id=session_id,
                    messages=[{
                        "role": "user",
                        "content": message,
                        "timestamp": datetime.now().isoformat()
                    }],
                    context={},
                    current_agent=None,
                    task_queue=[],
                    memory_context={}
                )
                
                # Execute workflow
                config = {"configurable": {"thread_id": session_id}}
                result = await self.graph.ainvoke(initial_state, config)
                
                # Clean up session tracking
                if session_id in self.active_sessions:
                    del self.active_sessions[session_id]
                    ACTIVE_SESSIONS.dec()
                
                return {
                    "success": True,
                    "session_id": session_id,
                    "response": result["messages"][-1]["content"],
                    "context": result["context"],
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Message processing error: {e}")
                if session_id in self.active_sessions:
                    del self.active_sessions[session_id]
                    ACTIVE_SESSIONS.dec()
                
                return {
                    "success": False,
                    "error": str(e),
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                }
    
    async def _analyze_request(self, user_input: str) -> Dict[str, Any]:
        """Analyze user request to determine task type"""
        # Simple keyword-based analysis (can be enhanced with ML)
        user_input_lower = user_input.lower()
        
        if any(keyword in user_input_lower for keyword in ["code", "program", "function", "script"]):
            return {"task_type": "code_generation", "complexity": "medium"}
        elif any(keyword in user_input_lower for keyword in ["search", "research", "find", "lookup"]):
            return {"task_type": "research", "complexity": "low"}
        else:
            return {"task_type": "general_chat", "complexity": "low"}
    
    async def _get_user_memories(self, user_id: str, query: str) -> List[Dict[str, Any]]:
        """Retrieve relevant memories for user"""
        try:
            MEMORY_OPERATIONS.labels(operation='search').inc()
            memories = self.memory.search(query, user_id=user_id, limit=5)
            return memories if memories else []
        except Exception as e:
            logger.error(f"Memory retrieval error: {e}")
            return []
    
    async def _store_interaction(self, user_id: str, session_id: str, message: Dict[str, Any]):
        """Store user interaction in memory"""
        try:
            MEMORY_OPERATIONS.labels(operation='store').inc()
            self.memory.add(
                message["content"],
                user_id=user_id,
                metadata={
                    "session_id": session_id,
                    "timestamp": message.get("timestamp"),
                    "role": message.get("role")
                }
            )
        except Exception as e:
            logger.error(f"Memory storage error: {e}")
    
    async def _get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences from Redis cache"""
        try:
            prefs = await self.redis_client.hgetall(f"user_prefs:{user_id}")
            return prefs if prefs else {"temperature": 0.7, "max_tokens": 2000}
        except Exception as e:
            logger.error(f"Preferences retrieval error: {e}")
            return {"temperature": 0.7, "max_tokens": 2000}
    
    async def _generate_code(self, user_input: str, memory_context: Dict[str, Any]) -> str:
        """Generate code using Lambda Labs GH200 servers with OpenRouter fallback"""
        try:
            # Build prompt with context
            prompt = self._build_code_prompt(user_input, memory_context)
            
            # Try Lambda Labs inference first with circuit breaker
            try:
                with self.circuit_breaker:
                    result = await run_lambda_inference(
                        prompt=prompt,
                        max_tokens=1024,
                        temperature=0.1  # Lower temperature for code generation
                    )
                    logger.info(f"Code generated using Lambda Labs server: {result.get('server')}")
                    return result.get('response', '')
                    
            except Exception as lambda_error:
                logger.warning(f"Lambda Labs inference failed: {lambda_error}")
                
                # Fallback to OpenRouter
                async with OpenRouterClient() as client:
                    messages = [{"role": "user", "content": prompt}]
                    result = await client.chat_completion(
                        messages=messages,
                        model="anthropic/claude-3.5-sonnet",  # Good for code generation
                        max_tokens=1024,
                        temperature=0.1
                    )
                    logger.info("Code generated using OpenRouter fallback")
                    return result.get('content', '')
                    
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            return f"# Error generating code: {str(e)}\n# Please try again or provide more specific requirements."
    
    def _build_code_prompt(self, user_input: str, memory_context: Dict[str, Any]) -> str:
        """Build optimized prompt for code generation"""
        context_info = ""
        if memory_context:
            context_info = f"\nRelevant context from previous conversations:\n{json.dumps(memory_context, indent=2)}\n"
        
        return f"""You are SOPHIA Intel, an expert software engineer. Generate high-quality, production-ready code based on the user's request.

User Request: {user_input}
{context_info}
Requirements:
- Write clean, well-documented code
- Include error handling where appropriate
- Follow best practices for the language/framework
- Provide brief explanations for complex logic
- Make the code production-ready

Generate the code:"""
    
    async def _perform_research(self, user_input: str, memory_context: Dict[str, Any]) -> str:
        """Perform web research with Lambda Labs GH200 servers and OpenRouter fallback"""
        try:
            # Build research prompt with context
            prompt = self._build_research_prompt(user_input, memory_context)
            
            # Try Lambda Labs inference first with circuit breaker
            try:
                with self.circuit_breaker:
                    result = await run_lambda_inference(
                        prompt=prompt,
                        max_tokens=1024,
                        temperature=0.3  # Moderate temperature for research
                    )
                    logger.info(f"Research completed using Lambda Labs server: {result.get('server')}")
                    return result.get('response', '')
                    
            except Exception as lambda_error:
                logger.warning(f"Lambda Labs research failed: {lambda_error}")
                
                # Fallback to OpenRouter
                async with OpenRouterClient() as client:
                    messages = [{"role": "user", "content": prompt}]
                    result = await client.chat_completion(
                        messages=messages,
                        model="google/gemini-2.0-flash-exp",  # Good for research and analysis
                        max_tokens=1024,
                        temperature=0.3
                    )
                    logger.info("Research completed using OpenRouter fallback")
                    return result.get('content', '')
                    
        except Exception as e:
            logger.error(f"Research failed: {e}")
            return f"Research Error: {str(e)}\nPlease try rephrasing your research query."
    
    def _build_research_prompt(self, user_input: str, memory_context: Dict[str, Any]) -> str:
        """Build optimized prompt for research tasks"""
        context_info = ""
        if memory_context:
            context_info = f"\nRelevant context from previous conversations:\n{json.dumps(memory_context, indent=2)}\n"
        
        return f"""You are SOPHIA Intel, an expert researcher and analyst. Provide comprehensive, accurate research and analysis based on the user's request.

User Request: {user_input}
{context_info}
Requirements:
- Provide accurate, up-to-date information
- Include multiple perspectives when relevant
- Cite sources or indicate when information should be verified
- Structure the response clearly with key findings
- Focus on actionable insights

Research and analyze:"""
    
    async def _generate_response(self, context: Dict[str, Any], memory_context: Dict[str, Any]) -> str:
        """Generate final response with full context"""
        # Synthesize response from all available context
        if "code_result" in context:
            return f"Here's the code I generated:\n\n{context['code_result']}"
        elif "research_result" in context:
            return f"Based on my research:\n\n{context['research_result']}"
        else:
            return "I'm here to help! What would you like me to do?"
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check endpoint"""
        try:
            # Check Redis connection
            await self.redis_client.ping()
            redis_status = "healthy"
        except:
            redis_status = "unhealthy"
        
        return {
            "status": "healthy" if redis_status == "healthy" else "degraded",
            "components": {
                "redis": redis_status,
                "memory": "healthy" if self.memory else "unhealthy",
                "graph": "healthy" if self.graph else "unhealthy"
            },
            "active_sessions": len(self.active_sessions),
            "timestamp": datetime.now().isoformat()
        }


# Global orchestrator instance
orchestrator = ScalableOrchestrator()

