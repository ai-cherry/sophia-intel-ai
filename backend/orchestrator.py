"""
SOPHIA Intel Enhanced Orchestrator
Multi-agent system with latest OpenRouter models
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import httpx
from dataclasses import asdict

from models.openrouter_models import model_selector, ModelTier, ModelConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SOPHIAOrchestrator:
    """
    Enhanced SOPHIA Intel orchestrator with latest AI models
    """
    
    def __init__(self):
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.openrouter_api_key:
            logger.warning("OPENROUTER_API_KEY not found in environment variables")
        
        self.base_url = "https://openrouter.ai/api/v1"
        self.session_history: Dict[str, List[Dict]] = {}
        self.task_history: Dict[str, List[Dict]] = {}
        
        # Agent configurations
        self.agents = {
            "coding": {
                "name": "SOPHIA Coding Agent",
                "description": "Expert in code generation, debugging, and technical analysis",
                "preferred_models": ["claude-4-sonnet", "deepseek-v3", "qwen3-coder"],
                "system_prompt": """You are SOPHIA's coding specialist. You excel at:
- Writing clean, efficient, production-ready code
- Debugging complex issues and providing solutions
- Code review and optimization suggestions
- Technical architecture and design patterns
- Multiple programming languages and frameworks

Always provide working code with proper documentation and error handling."""
            },
            
            "research": {
                "name": "SOPHIA Research Agent", 
                "description": "Specialized in research, analysis, and information synthesis",
                "preferred_models": ["gemini-2.5-pro", "claude-4-sonnet", "kimi-k2"],
                "system_prompt": """You are SOPHIA's research specialist. You excel at:
- Comprehensive research and analysis
- Information synthesis from multiple sources
- Trend analysis and insights
- Academic and technical research
- Data interpretation and visualization

Provide thorough, well-sourced analysis with clear conclusions."""
            },
            
            "general": {
                "name": "SOPHIA General Agent",
                "description": "Versatile assistant for general tasks and conversations",
                "preferred_models": ["claude-4-sonnet", "gpt-5", "gpt-4.1"],
                "system_prompt": """You are SOPHIA's general assistant. You excel at:
- Natural conversation and communication
- Problem-solving and creative thinking
- Task planning and organization
- Writing and content creation
- General knowledge and reasoning

Be helpful, accurate, and engaging in all interactions."""
            }
        }
    
    async def detect_task_type(self, message: str) -> tuple[str, str]:
        """
        Detect task type and complexity from user message
        
        Returns:
            tuple: (task_type, complexity)
        """
        message_lower = message.lower()
        
        # Coding indicators
        coding_keywords = [
            "code", "function", "class", "debug", "error", "bug", "implement",
            "algorithm", "programming", "script", "api", "database", "sql",
            "python", "javascript", "react", "flask", "django", "git"
        ]
        
        # Research indicators
        research_keywords = [
            "research", "analyze", "study", "compare", "investigate", "trends",
            "market", "data", "statistics", "report", "findings", "insights",
            "academic", "paper", "publication", "survey"
        ]
        
        # Creative indicators
        creative_keywords = [
            "write", "create", "story", "article", "blog", "content", "creative",
            "brainstorm", "ideas", "design", "marketing", "copy", "narrative"
        ]
        
        # Determine task type
        task_type = "general"  # default
        
        if any(keyword in message_lower for keyword in coding_keywords):
            task_type = "coding"
        elif any(keyword in message_lower for keyword in research_keywords):
            task_type = "research"
        elif any(keyword in message_lower for keyword in creative_keywords):
            task_type = "creative"
        
        # Determine complexity
        complexity = "medium"  # default
        
        complex_indicators = [
            "complex", "advanced", "sophisticated", "comprehensive", "detailed",
            "enterprise", "production", "scalable", "architecture", "system"
        ]
        
        simple_indicators = [
            "simple", "basic", "quick", "easy", "straightforward", "minimal",
            "small", "brief", "short", "fast"
        ]
        
        if any(indicator in message_lower for indicator in complex_indicators):
            complexity = "complex"
        elif any(indicator in message_lower for indicator in simple_indicators):
            complexity = "simple"
        
        return task_type, complexity
    
    def select_optimal_model(self, task_type: str, complexity: str, budget: str = "premium") -> ModelConfig:
        """
        Select the optimal model for the task
        """
        return model_selector.select_model_for_task(task_type, complexity, budget)
    
    async def make_api_request(self, model: ModelConfig, messages: List[Dict], **kwargs) -> Dict:
        """
        Make API request to OpenRouter
        """
        if not self.openrouter_api_key:
            raise ValueError("OpenRouter API key not configured")
        
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://sophia-intel.ai",
            "X-Title": "SOPHIA Intel"
        }
        
        payload = {
            "model": model.name,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", model.max_tokens_default),
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 0.9),
            "frequency_penalty": kwargs.get("frequency_penalty", 0.0),
            "presence_penalty": kwargs.get("presence_penalty", 0.0),
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPError as e:
                logger.error(f"OpenRouter API error: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error in API request: {e}")
                raise
    
    async def process_message(self, 
                            message: str, 
                            session_id: str = "default",
                            agent_type: Optional[str] = None,
                            budget: str = "premium") -> Dict[str, Any]:
        """
        Process a message through the orchestrator
        
        Args:
            message: User message
            session_id: Session identifier for context
            agent_type: Specific agent to use (optional)
            budget: Budget constraint for model selection
        """
        try:
            # Detect task type and complexity if agent not specified
            if not agent_type:
                task_type, complexity = await self.detect_task_type(message)
                agent_type = task_type if task_type in self.agents else "general"
            else:
                task_type = agent_type
                complexity = "medium"
            
            # Select optimal model
            model = self.select_optimal_model(task_type, complexity, budget)
            
            # Get agent configuration
            agent_config = self.agents.get(agent_type, self.agents["general"])
            
            # Build conversation context
            if session_id not in self.session_history:
                self.session_history[session_id] = []
            
            # Prepare messages with system prompt
            messages = [
                {"role": "system", "content": agent_config["system_prompt"]}
            ]
            
            # Add recent conversation history (last 10 messages)
            recent_history = self.session_history[session_id][-10:]
            messages.extend(recent_history)
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Make API request
            start_time = datetime.now()
            response = await self.make_api_request(model, messages)
            end_time = datetime.now()
            
            # Extract response
            if "choices" in response and len(response["choices"]) > 0:
                assistant_message = response["choices"][0]["message"]["content"]
                
                # Update session history
                self.session_history[session_id].extend([
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": assistant_message}
                ])
                
                # Track task history
                if session_id not in self.task_history:
                    self.task_history[session_id] = []
                
                task_record = {
                    "timestamp": start_time.isoformat(),
                    "task_type": task_type,
                    "complexity": complexity,
                    "agent": agent_type,
                    "model": model.name,
                    "model_provider": model.provider,
                    "model_tier": model.tier.value,
                    "response_time": (end_time - start_time).total_seconds(),
                    "tokens_used": response.get("usage", {}).get("total_tokens", 0),
                    "cost_estimate": response.get("usage", {}).get("total_tokens", 0) * model.cost_per_1k_tokens / 1000
                }
                
                self.task_history[session_id].append(task_record)
                
                return {
                    "success": True,
                    "response": assistant_message,
                    "metadata": {
                        "agent": agent_config["name"],
                        "model": model.name,
                        "provider": model.provider,
                        "tier": model.tier.value,
                        "task_type": task_type,
                        "complexity": complexity,
                        "response_time": task_record["response_time"],
                        "tokens_used": task_record["tokens_used"],
                        "cost_estimate": task_record["cost_estimate"]
                    }
                }
            else:
                raise ValueError("Invalid response from OpenRouter API")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_response": "I apologize, but I encountered an error processing your request. Please try again or contact support if the issue persists."
            }
    
    async def get_session_status(self, session_id: str = "default") -> Dict[str, Any]:
        """
        Get session status and statistics
        """
        history = self.session_history.get(session_id, [])
        tasks = self.task_history.get(session_id, [])
        
        if not tasks:
            return {
                "session_id": session_id,
                "message_count": len(history),
                "task_count": 0,
                "models_used": [],
                "total_cost": 0.0,
                "avg_response_time": 0.0
            }
        
        # Calculate statistics
        models_used = list(set(task["model"] for task in tasks))
        total_cost = sum(task["cost_estimate"] for task in tasks)
        avg_response_time = sum(task["response_time"] for task in tasks) / len(tasks)
        
        # Task type distribution
        task_types = {}
        for task in tasks:
            task_type = task["task_type"]
            task_types[task_type] = task_types.get(task_type, 0) + 1
        
        return {
            "session_id": session_id,
            "message_count": len(history),
            "task_count": len(tasks),
            "models_used": models_used,
            "total_cost": round(total_cost, 4),
            "avg_response_time": round(avg_response_time, 2),
            "task_distribution": task_types,
            "last_activity": tasks[-1]["timestamp"] if tasks else None
        }
    
    async def reset_session(self, session_id: str = "default") -> Dict[str, str]:
        """
        Reset session history
        """
        if session_id in self.session_history:
            del self.session_history[session_id]
        if session_id in self.task_history:
            del self.task_history[session_id]
        
        return {
            "status": "success",
            "message": f"Session {session_id} has been reset"
        }
    
    def get_available_models(self) -> Dict[str, List[Dict]]:
        """
        Get information about available models
        """
        models_by_tier = {}
        
        for tier in ModelTier:
            tier_models = model_selector.list_models_by_tier(tier)
            models_by_tier[tier.value] = [
                {
                    "name": model.name,
                    "provider": model.provider,
                    "context_length": model.context_length,
                    "cost_per_1k_tokens": model.cost_per_1k_tokens,
                    "strengths": model.strengths,
                    "best_for": model.best_for
                }
                for model in tier_models
            ]
        
        return models_by_tier
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get orchestrator health status
        """
        return {
            "status": "healthy",
            "openrouter_configured": bool(self.openrouter_api_key),
            "available_agents": list(self.agents.keys()),
            "available_models": len(model_selector.models),
            "flagship_models": len(model_selector.get_flagship_models()),
            "free_models": len(model_selector.get_free_models()),
            "active_sessions": len(self.session_history),
            "total_tasks_processed": sum(len(tasks) for tasks in self.task_history.values()),
            "timestamp": datetime.now().isoformat()
        }

# Global orchestrator instance
orchestrator = SOPHIAOrchestrator()

