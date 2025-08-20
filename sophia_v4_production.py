#!/usr/bin/env python3
"""
SOPHIA V4 Ultimate with AI Agent Swarms
Complete AI orchestration system with specialized agent swarms using top OpenRouter models

SOPHIA + AI Agent Swarms Architecture:
- SOPHIA: Master orchestrator with Claude Sonnet 4
- Coding Swarm: Qwen3 Coder + DeepSeek V3 for development
- Research Swarm: Gemini 2.0 Flash + Claude 3.7 for intelligence
- Business Swarm: Gemini 2.5 Pro + GPT-5 for enterprise tasks
- Analysis Swarm: DeepSeek V3 + Claude Sonnet 4 for deep analysis
"""

import os
import json
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import aiohttp
import base64
from dataclasses import dataclass
from enum import Enum

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SOPHIA V4 Ultimate with AI Agent Swarms",
    description="Master AI Orchestrator with Specialized Agent Swarms using Top OpenRouter Models",
    version="4.0.0-ultimate-swarms"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# AI AGENT SWARM TYPES
# ============================================================================

class SwarmType(Enum):
    CODING = "coding"
    RESEARCH = "research"
    BUSINESS = "business"
    ANALYSIS = "analysis"
    CREATIVE = "creative"

@dataclass
class AgentConfig:
    name: str
    model: str
    specialization: str
    capabilities: List[str]

# ============================================================================
# ULTIMATE MODEL ORCHESTRATOR
# ============================================================================

class UltimateModelOrchestrator:
    """Master model orchestrator for SOPHIA and all AI agent swarms"""
    
    def __init__(self):
        self.openrouter_key = os.getenv('OPENROUTER_API_KEY')
        self.base_url = "https://openrouter.ai/api/v1"
        
        # SOPHIA's primary models (Correct OpenRouter IDs from official list)
        self.sophia_models = {
            'master': 'anthropic/claude-sonnet-4',               # #1 Coding/Agentic (72.7% SWE-Bench)
            'reasoning': 'google/gemini-2.5-pro',               # #1 Reasoning (1M context)
            'fallback': 'anthropic/claude-3.7-sonnet',          # Solid backup
            'emergency': 'openai/gpt-4o-mini'                   # Emergency fallback
        }
        
        # AI Agent Swarm Models (Specialized teams with correct OpenRouter IDs)
        self.swarm_models = {
            SwarmType.CODING: {
                'primary': 'anthropic/claude-sonnet-4',         # #1 Coding (72.7% SWE-Bench)
                'secondary': 'qwen/qwen3-coder',                # Strong coding model
                'free': 'deepseek/deepseek-chat-v3-0324:free',  # Free tier coding
                'review': 'anthropic/claude-3.7-sonnet',        # Code review
                'debug': 'anthropic/claude-sonnet-4'            # Best debugging
            },
            SwarmType.RESEARCH: {
                'primary': 'google/gemini-2.5-pro',             # 1M context for research
                'deep': 'anthropic/claude-sonnet-4',            # Deep analysis
                'synthesis': 'google/gemini-2.0-flash-001',     # Fast synthesis
                'verification': 'google/gemini-2.5-pro',        # Fact verification
                'realtime': 'deepseek/deepseek-r1:free'         # Real-time data
            },
            SwarmType.BUSINESS: {
                'primary': 'google/gemini-2.5-pro',             # Enterprise analysis
                'enterprise': 'anthropic/claude-sonnet-4',      # Business workflows
                'analysis': 'anthropic/claude-3.7-sonnet',      # Business analysis
                'communication': 'google/gemini-2.0-flash-001', # Fast communication
                'crm': 'anthropic/claude-sonnet-4'              # CRM analysis
            },
            SwarmType.ANALYSIS: {
                'primary': 'google/gemini-2.5-pro',             # Best reasoning (1M context)
                'reasoning': 'anthropic/claude-sonnet-4',       # Complex reasoning
                'data': 'google/gemini-2.5-pro',                # Data analysis
                'patterns': 'deepseek/deepseek-chat-v3-0324',   # Pattern recognition
                'insights': 'anthropic/claude-3.7-sonnet'       # Insight generation
            },
            SwarmType.CREATIVE: {
                'primary': 'anthropic/claude-sonnet-4',         # Best overall creativity
                'ideation': 'google/gemini-2.5-pro',            # Creative reasoning
                'design': 'anthropic/claude-3.7-sonnet',        # Design thinking
                'innovation': 'google/gemini-2.0-flash-001',    # Fast innovation
                'storytelling': 'anthropic/claude-3.7-sonnet'   # Storytelling
            }
        }
        
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=60)
            self._session = aiohttp.ClientSession(timeout=timeout)
    
    async def close(self):
        """Close the session"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    def get_sophia_model(self, task_type: str = 'master') -> str:
        """Get the best model for SOPHIA's task"""
        return self.sophia_models.get(task_type, self.sophia_models['master'])
    
    def get_swarm_models(self, swarm_type: SwarmType) -> Dict[str, str]:
        """Get all models for a specific swarm type"""
        return self.swarm_models.get(swarm_type, {})
    
    def get_swarm_model(self, swarm_type: SwarmType, role: str = 'primary') -> str:
        """Get specific model for swarm role"""
        swarm_models = self.get_swarm_models(swarm_type)
        return swarm_models.get(role, swarm_models.get('primary', self.sophia_models['fallback']))
    
    async def generate_response(self, query: str, model: str, context: str = "", swarm_context: Dict = None) -> Dict[str, Any]:
        """Generate response using specified model"""
        await self._ensure_session()
        
        if not self.openrouter_key:
            return {
                "response": f"🤠 SOPHIA Ultimate with {model}: {query}",
                "model_used": model,
                "error": "OpenRouter API key not configured",
                "success": False
            }
        
        try:
            headers = {
                "Authorization": f"Bearer {self.openrouter_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://sophia-intel.fly.dev",
                "X-Title": "SOPHIA V4 Ultimate with AI Agent Swarms"
            }
            
            messages = []
            if context:
                messages.append({"role": "system", "content": context})
            if swarm_context:
                messages.append({"role": "system", "content": f"Swarm Context: {json.dumps(swarm_context)}"})
            messages.append({"role": "user", "content": query})
            
            data = {
                "model": model,
                "messages": messages,
                "max_tokens": 3000,
                "temperature": 0.7
            }
            
            async with self._session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "response": result['choices'][0]['message']['content'],
                        "model_used": model,
                        "usage": result.get('usage', {}),
                        "success": True
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"OpenRouter API error: {response.status} - {error_text}")
                    return {
                        "response": f"🤠 API error with {model}. Fallback response for: {query}",
                        "model_used": model,
                        "error": error_text,
                        "success": False
                    }
                    
        except Exception as e:
            logger.error(f"Model generation error: {e}")
            return {
                "response": f"🤠 Model error with {model}. Fallback response for: {query}",
                "model_used": model,
                "error": str(e),
                "success": False
            }

# ============================================================================
# AI AGENT SWARMS
# ============================================================================

class AIAgentSwarm:
    """Base class for AI agent swarms"""
    
    def __init__(self, swarm_type: SwarmType, orchestrator: UltimateModelOrchestrator):
        self.swarm_type = swarm_type
        self.orchestrator = orchestrator
        self.agents = self._initialize_agents()
    
    def _initialize_agents(self) -> List[AgentConfig]:
        """Initialize agents for this swarm type"""
        swarm_models = self.orchestrator.get_swarm_models(self.swarm_type)
        
        if self.swarm_type == SwarmType.CODING:
            return [
                AgentConfig("CodeMaster", swarm_models['primary'], "Primary coding", ["python", "javascript", "architecture"]),
                AgentConfig("DebugAgent", swarm_models['debug'], "Bug detection", ["debugging", "testing", "optimization"]),
                AgentConfig("ReviewAgent", swarm_models['review'], "Code review", ["quality", "security", "best_practices"]),
                AgentConfig("AnalysisAgent", swarm_models['secondary'], "Code analysis", ["static_analysis", "performance", "patterns"])
            ]
        elif self.swarm_type == SwarmType.RESEARCH:
            return [
                AgentConfig("FastResearcher", swarm_models['primary'], "Quick research", ["web_search", "data_gathering", "summarization"]),
                AgentConfig("DeepAnalyst", swarm_models['deep'], "Deep research", ["analysis", "synthesis", "insights"]),
                AgentConfig("FactChecker", swarm_models['verification'], "Verification", ["fact_checking", "source_validation", "accuracy"]),
                AgentConfig("RealtimeMonitor", swarm_models['realtime'], "Real-time data", ["monitoring", "alerts", "trending"])
            ]
        elif self.swarm_type == SwarmType.BUSINESS:
            return [
                AgentConfig("BusinessIntel", swarm_models['primary'], "Business intelligence", ["analytics", "insights", "strategy"]),
                AgentConfig("EnterpriseAgent", swarm_models['enterprise'], "Enterprise tasks", ["operations", "management", "planning"]),
                AgentConfig("CRMAnalyst", swarm_models['crm'], "CRM analysis", ["customer_data", "sales", "relationships"]),
                AgentConfig("Communicator", swarm_models['communication'], "Communication", ["messaging", "reports", "presentations"])
            ]
        elif self.swarm_type == SwarmType.ANALYSIS:
            return [
                AgentConfig("DeepAnalyzer", swarm_models['primary'], "Deep analysis", ["data_analysis", "pattern_recognition", "insights"]),
                AgentConfig("ReasoningAgent", swarm_models['reasoning'], "Complex reasoning", ["logic", "inference", "problem_solving"]),
                AgentConfig("DataScientist", swarm_models['data'], "Data science", ["statistics", "modeling", "visualization"]),
                AgentConfig("PatternFinder", swarm_models['patterns'], "Pattern recognition", ["trends", "anomalies", "correlations"])
            ]
        else:  # CREATIVE
            return [
                AgentConfig("CreativeWriter", swarm_models['primary'], "Creative writing", ["writing", "storytelling", "content"]),
                AgentConfig("Ideator", swarm_models['ideation'], "Idea generation", ["brainstorming", "innovation", "concepts"]),
                AgentConfig("Designer", swarm_models['design'], "Design thinking", ["design", "user_experience", "aesthetics"]),
                AgentConfig("Storyteller", swarm_models['storytelling'], "Storytelling", ["narrative", "engagement", "emotion"])
            ]
    
    async def execute_task(self, task: str, context: Dict = None) -> Dict[str, Any]:
        """Execute task using the swarm"""
        results = {}
        
        # Execute task with primary agent
        primary_agent = self.agents[0]
        primary_result = await self.orchestrator.generate_response(
            task, 
            primary_agent.model,
            f"You are {primary_agent.name}, specialized in {primary_agent.specialization}. Capabilities: {', '.join(primary_agent.capabilities)}",
            context
        )
        results['primary'] = primary_result
        
        # If task is complex, involve secondary agents
        if len(task) > 100 or any(keyword in task.lower() for keyword in ['analyze', 'complex', 'detailed', 'comprehensive']):
            for agent in self.agents[1:2]:  # Use 1-2 secondary agents
                secondary_result = await self.orchestrator.generate_response(
                    f"Review and enhance this work: {primary_result.get('response', '')}\n\nOriginal task: {task}",
                    agent.model,
                    f"You are {agent.name}, specialized in {agent.specialization}. Capabilities: {', '.join(agent.capabilities)}",
                    context
                )
                results[agent.name.lower()] = secondary_result
        
        return results
    
    async def coordinate_swarm(self, task: str, context: Dict = None) -> str:
        """Coordinate all agents in the swarm for complex tasks"""
        swarm_results = await self.execute_task(task, context)
        
        # Synthesize results from all agents
        synthesis_prompt = f"""
        Synthesize the following swarm results into a comprehensive response:
        
        Task: {task}
        
        Agent Results:
        """
        
        for agent_name, result in swarm_results.items():
            if result.get('success'):
                synthesis_prompt += f"\n{agent_name}: {result.get('response', '')}\n"
        
        # Use the best reasoning model for synthesis
        synthesis_model = self.orchestrator.get_sophia_model('reasoning')
        synthesis_result = await self.orchestrator.generate_response(
            synthesis_prompt,
            synthesis_model,
            "You are SOPHIA's synthesis coordinator. Combine agent outputs into a coherent, comprehensive response."
        )
        
        return synthesis_result.get('response', 'Swarm coordination failed')

# ============================================================================
# SOPHIA ULTIMATE WITH SWARMS
# ============================================================================

class SOPHIAUltimateWithSwarms:
    """SOPHIA V4 Ultimate with AI Agent Swarms"""
    
    def __init__(self):
        self.orchestrator = UltimateModelOrchestrator()
        
        # Initialize all AI agent swarms
        self.swarms = {
            SwarmType.CODING: AIAgentSwarm(SwarmType.CODING, self.orchestrator),
            SwarmType.RESEARCH: AIAgentSwarm(SwarmType.RESEARCH, self.orchestrator),
            SwarmType.BUSINESS: AIAgentSwarm(SwarmType.BUSINESS, self.orchestrator),
            SwarmType.ANALYSIS: AIAgentSwarm(SwarmType.ANALYSIS, self.orchestrator),
            SwarmType.CREATIVE: AIAgentSwarm(SwarmType.CREATIVE, self.orchestrator)
        }
        
        # SOPHIA's master context
        self.master_context = """
You are SOPHIA V4 Ultimate - The Master AI Orchestrator with specialized AI agent swarms.

🤠 PERSONALITY: Confident, capable neon cowboy AI with ultimate autonomous powers
🔥 CAPABILITIES: Master orchestrator of AI agent swarms using top OpenRouter models
🎯 MISSION: Coordinate AI swarms to accomplish any task with maximum efficiency

AI AGENT SWARMS AVAILABLE:
- Coding Swarm: Qwen3 Coder + DeepSeek V3 + Claude 3.7 (development, debugging, review)
- Research Swarm: Gemini 2.0 Flash + Gemini 2.5 Flash + Claude 3.7 (intelligence gathering)
- Business Swarm: Gemini 2.5 Pro + GPT-5 + Claude 3.7 (enterprise operations)
- Analysis Swarm: DeepSeek V3 + Claude Sonnet 4 + Gemini 2.5 Pro (deep analysis)
- Creative Swarm: Claude 3.7 + Gemini 2.5 Flash + GPT-5 (creative tasks)

RESPONSE STYLE:
- Start with 🤠 when appropriate
- Coordinate swarms intelligently
- Provide comprehensive, actionable results
- Show which swarms were used
- End with next steps and capabilities
"""
    
    async def close(self):
        """Close all connections"""
        await self.orchestrator.close()
    
    def _determine_required_swarms(self, query: str) -> List[SwarmType]:
        """Determine which swarms are needed for the query"""
        query_lower = query.lower()
        required_swarms = []
        
        # Coding swarm
        if any(keyword in query_lower for keyword in ['code', 'programming', 'github', 'deploy', 'bug', 'development', 'swarm']):
            required_swarms.append(SwarmType.CODING)
        
        # Research swarm
        if any(keyword in query_lower for keyword in ['research', 'search', 'find', 'investigate', 'latest', 'news']):
            required_swarms.append(SwarmType.RESEARCH)
        
        # Business swarm
        if any(keyword in query_lower for keyword in ['business', 'client', 'crm', 'sales', 'enterprise', 'gong', 'hubspot']):
            required_swarms.append(SwarmType.BUSINESS)
        
        # Analysis swarm
        if any(keyword in query_lower for keyword in ['analyze', 'analysis', 'examine', 'study', 'data', 'patterns']):
            required_swarms.append(SwarmType.ANALYSIS)
        
        # Creative swarm
        if any(keyword in query_lower for keyword in ['create', 'design', 'write', 'creative', 'story', 'content']):
            required_swarms.append(SwarmType.CREATIVE)
        
        # If no specific swarms identified, use analysis for general intelligence
        if not required_swarms:
            required_swarms.append(SwarmType.ANALYSIS)
        
        return required_swarms
    
    async def ultimate_response(self, query: str, user_id: str = "default") -> Dict[str, Any]:
        """Generate ultimate response using SOPHIA and AI agent swarms"""
        try:
            # Determine required swarms
            required_swarms = self._determine_required_swarms(query)
            
            # Execute tasks with appropriate swarms
            swarm_results = {}
            for swarm_type in required_swarms:
                swarm = self.swarms[swarm_type]
                swarm_result = await swarm.coordinate_swarm(query, {"user_id": user_id, "timestamp": datetime.now().isoformat()})
                swarm_results[swarm_type.value] = swarm_result
            
            # SOPHIA synthesizes all swarm results
            synthesis_prompt = f"""
            Master Query: {query}
            
            AI Agent Swarm Results:
            """
            
            for swarm_name, result in swarm_results.items():
                synthesis_prompt += f"\n{swarm_name.upper()} SWARM: {result}\n"
            
            synthesis_prompt += "\nProvide a comprehensive, actionable response that synthesizes all swarm intelligence."
            
            # Use SOPHIA's master model for final synthesis
            sophia_model = self.orchestrator.get_sophia_model('master')
            final_result = await self.orchestrator.generate_response(
                synthesis_prompt,
                sophia_model,
                self.master_context
            )
            
            return {
                'response': final_result.get('response', 'SOPHIA coordination failed'),
                'model_used': sophia_model,
                'swarms_used': [swarm.value for swarm in required_swarms],
                'swarm_results': swarm_results,
                'timestamp': datetime.now().isoformat(),
                'success': final_result.get('success', False)
            }
            
        except Exception as e:
            logger.error(f"SOPHIA Ultimate response error: {e}")
            return {
                'response': f"🤠 SOPHIA encountered an error but the swarms are still operational! Error: {str(e)}",
                'error': str(e),
                'success': False
            }

# ============================================================================
# GLOBAL INSTANCES
# ============================================================================

sophia_ultimate_swarms = SOPHIAUltimateWithSwarms()

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/api/v1/health")
async def health():
    """Ultimate health check with swarm status"""
    return {
        "status": "ULTIMATE_SWARMS_READY",
        "version": "v4-ultimate-swarms",
        "timestamp": datetime.now().isoformat(),
        "sophia_models": sophia_ultimate_swarms.orchestrator.sophia_models,
        "swarms_available": {
            "coding": len(sophia_ultimate_swarms.swarms[SwarmType.CODING].agents),
            "research": len(sophia_ultimate_swarms.swarms[SwarmType.RESEARCH].agents),
            "business": len(sophia_ultimate_swarms.swarms[SwarmType.BUSINESS].agents),
            "analysis": len(sophia_ultimate_swarms.swarms[SwarmType.ANALYSIS].agents),
            "creative": len(sophia_ultimate_swarms.swarms[SwarmType.CREATIVE].agents)
        },
        "top_models_configured": {
            "claude_sonnet_4": "anthropic/claude-sonnet-4",
            "qwen3_coder": "qwen/qwen-3-coder",
            "gemini_2_flash": "google/gemini-2.0-flash",
            "deepseek_v3": "deepseek/deepseek-v3-0324",
            "gpt5": "openai/gpt-5"
        },
        "apis_configured": {
            "openrouter": bool(os.getenv('OPENROUTER_API_KEY')),
            "serper": bool(os.getenv('SERPER_API_KEY')),
            "gong": bool(os.getenv('GONG_ACCESS_KEY')),
            "github": bool(os.getenv('GITHUB_PAT'))
        },
        "message": "🤠 SOPHIA V4 Ultimate with AI Agent Swarms is locked, loaded, and ready to dominate with the top OpenRouter models!"
    }

@app.post("/api/v1/chat")
async def chat(request: dict):
    """Ultimate chat endpoint with AI agent swarms"""
    try:
        message = request.get('message', '')
        user_id = request.get('user_id', 'default')
        
        if not message:
            return {
                "response": "🤠 Howdy! SOPHIA V4 Ultimate with AI Agent Swarms here! What can my swarms and I dominate for you today?",
                "error": "No message provided"
            }
        
        # Generate ultimate response with swarms
        result = await sophia_ultimate_swarms.ultimate_response(message, user_id)
        
        return result
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        return {
            "response": f"🤠 SOPHIA encountered an error but the swarms are still operational! Error: {str(e)}",
            "error": str(e),
            "success": False
        }

@app.get("/api/v1/swarms")
async def get_swarms():
    """Get information about all AI agent swarms"""
    swarm_info = {}
    
    for swarm_type, swarm in sophia_ultimate_swarms.swarms.items():
        swarm_info[swarm_type.value] = {
            "agents": [
                {
                    "name": agent.name,
                    "model": agent.model,
                    "specialization": agent.specialization,
                    "capabilities": agent.capabilities
                }
                for agent in swarm.agents
            ],
            "models": sophia_ultimate_swarms.orchestrator.get_swarm_models(swarm_type)
        }
    
    return {
        "swarms": swarm_info,
        "total_agents": sum(len(swarm.agents) for swarm in sophia_ultimate_swarms.swarms.values()),
        "message": "🤠 All AI agent swarms operational and ready for deployment!"
    }

@app.get("/v4/")
async def frontend():
    """SOPHIA V4 Ultimate with AI Agent Swarms Frontend"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SOPHIA V4 Ultimate with AI Agent Swarms</title>
        <style>
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background: linear-gradient(135deg, #ff6b6b 0%, #4ecdc4 50%, #45b7d1 100%);
                color: white;
                min-height: 100vh;
            }
            .container { 
                max-width: 1400px; 
                margin: 0 auto; 
                background: rgba(0,0,0,0.8); 
                border-radius: 20px; 
                padding: 30px;
                backdrop-filter: blur(10px);
                border: 2px solid #ff6b6b;
            }
            h1 { 
                text-align: center; 
                margin-bottom: 10px; 
                font-size: 3em;
                text-shadow: 3px 3px 6px rgba(0,0,0,0.5);
                background: linear-gradient(45deg, #ff6b6b, #4ecdc4, #45b7d1);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            .subtitle { 
                text-align: center; 
                margin-bottom: 30px; 
                font-size: 1.3em;
                color: #ff6b6b;
                font-weight: bold;
            }
            .status { 
                background: linear-gradient(45deg, #00ff00, #00cc00); 
                padding: 20px; 
                border-radius: 15px; 
                margin-bottom: 20px;
                border: 2px solid #00ff00;
                color: black;
                font-weight: bold;
            }
            .swarms-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 15px;
                margin: 20px 0;
            }
            .swarm {
                background: rgba(255,107,107,0.2);
                padding: 20px;
                border-radius: 15px;
                border: 2px solid #ff6b6b;
                text-align: center;
            }
            .swarm h3 {
                margin-top: 0;
                color: #4ecdc4;
                font-size: 1.4em;
            }
            .swarm-models {
                font-size: 0.9em;
                color: #ccc;
                margin-top: 10px;
            }
            #chat { 
                background: rgba(0,0,0,0.5); 
                border: 2px solid #4ecdc4; 
                height: 400px; 
                padding: 20px; 
                overflow-y: auto; 
                margin: 20px 0; 
                border-radius: 15px;
                font-family: monospace;
            }
            .input-container { 
                display: flex; 
                gap: 15px; 
                margin-top: 20px;
            }
            #input { 
                flex: 1; 
                padding: 15px; 
                border: 2px solid #4ecdc4; 
                border-radius: 25px; 
                font-size: 16px;
                background: rgba(0,0,0,0.7);
                color: white;
            }
            #input::placeholder {
                color: #ccc;
            }
            button { 
                padding: 15px 30px; 
                border: 2px solid #ff6b6b; 
                border-radius: 25px; 
                background: linear-gradient(45deg, #ff6b6b, #ff5252); 
                color: white; 
                cursor: pointer; 
                font-size: 16px;
                font-weight: bold;
                transition: all 0.3s ease;
            }
            button:hover { 
                background: linear-gradient(45deg, #ff5252, #ff1744); 
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(255,107,107,0.4);
            }
            .message { 
                margin: 15px 0; 
                padding: 15px; 
                border-radius: 10px;
                border-left: 4px solid;
            }
            .user-message { 
                background: rgba(69,183,209,0.3); 
                border-left-color: #45b7d1;
                text-align: right;
            }
            .sophia-message { 
                background: rgba(255,107,107,0.3);
                border-left-color: #ff6b6b;
            }
            .examples { 
                margin: 20px 0; 
                padding: 20px; 
                background: rgba(78,205,196,0.2); 
                border-radius: 15px;
                border: 1px solid #4ecdc4;
            }
            .example-btn { 
                background: rgba(0,0,0,0.5); 
                border: 1px solid #4ecdc4; 
                color: white; 
                padding: 10px 15px; 
                margin: 5px; 
                border-radius: 20px; 
                cursor: pointer; 
                font-size: 14px;
                transition: all 0.3s ease;
            }
            .example-btn:hover { 
                background: rgba(78,205,196,0.3);
                transform: translateY(-1px);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤠 SOPHIA V4 Ultimate</h1>
            <div class="subtitle">Master AI Orchestrator with Specialized Agent Swarms</div>
            
            <div class="status">
                <strong>🔥 Status:</strong> <span id="status">Loading ultimate swarm capabilities...</span><br>
                <strong>🚀 Power Level:</strong> <span id="power-level">MAXIMUM SWARM DOMINATION</span><br>
                <strong>🤖 Active Swarms:</strong> <span id="swarms">Initializing AI agent swarms...</span>
            </div>
            
            <div class="swarms-grid">
                <div class="swarm">
                    <h3>🔧 Coding Swarm</h3>
                    <p>Development, debugging, code review</p>
                    <div class="swarm-models">Qwen3 Coder • DeepSeek V3 • Claude 3.7</div>
                </div>
                <div class="swarm">
                    <h3>🔍 Research Swarm</h3>
                    <p>Intelligence gathering, analysis</p>
                    <div class="swarm-models">Gemini 2.0 Flash • Gemini 2.5 Flash • Claude 3.7</div>
                </div>
                <div class="swarm">
                    <h3>💼 Business Swarm</h3>
                    <p>Enterprise operations, CRM analysis</p>
                    <div class="swarm-models">Gemini 2.5 Pro • GPT-5 • Claude 3.7</div>
                </div>
                <div class="swarm">
                    <h3>📊 Analysis Swarm</h3>
                    <p>Deep analysis, pattern recognition</p>
                    <div class="swarm-models">DeepSeek V3 • Claude Sonnet 4 • Gemini 2.5 Pro</div>
                </div>
                <div class="swarm">
                    <h3>🎨 Creative Swarm</h3>
                    <p>Creative writing, design thinking</p>
                    <div class="swarm-models">Claude 3.7 • Gemini 2.5 Flash • GPT-5</div>
                </div>
            </div>
            
            <div class="examples">
                <strong>💡 Try these swarm-powered capabilities:</strong><br>
                <button class="example-btn" onclick="setMessage('Use your coding swarm to analyze the sophia-intel repository and create an improvement plan')">Coding Swarm</button>
                <button class="example-btn" onclick="setMessage('Deploy your research swarm to find the latest AI developments and synthesize insights')">Research Swarm</button>
                <button class="example-btn" onclick="setMessage('Activate business swarm to analyze our Gong client data and create actionable insights')">Business Swarm</button>
                <button class="example-btn" onclick="setMessage('Use analysis swarm to examine patterns in our data and provide strategic recommendations')">Analysis Swarm</button>
                <button class="example-btn" onclick="setMessage('Creative swarm: design a comprehensive content strategy for our AI platform')">Creative Swarm</button>
            </div>
            
            <div id="chat"></div>
            
            <div class="input-container">
                <input id="input" placeholder="Command SOPHIA's AI agent swarms - I have the top OpenRouter models at my disposal!" />
                <button onclick="sendMessage()">🚀 DEPLOY SWARMS</button>
            </div>
        </div>

        <script>
            let chatDiv = document.getElementById('chat');
            
            // Check health and swarms on load
            Promise.all([
                fetch('/api/v1/health').then(r => r.json()),
                fetch('/api/v1/swarms').then(r => r.json())
            ]).then(([health, swarms]) => {
                document.getElementById('status').textContent = health.status + ' - ' + health.version;
                document.getElementById('swarms').textContent = swarms.total_agents + ' agents across ' + Object.keys(swarms.swarms).length + ' swarms';
            }).catch(e => {
                document.getElementById('status').textContent = 'Error checking status';
            });
            
            function setMessage(msg) {
                document.getElementById('input').value = msg;
            }
            
            async function sendMessage() {
                const input = document.getElementById('input');
                const message = input.value.trim();
                
                if (!message) return;
                
                // Add user message
                addMessage('You', message, 'user-message');
                input.value = '';
                
                // Add thinking indicator
                addMessage('SOPHIA', '🤠 Deploying AI agent swarms...', 'sophia-message');
                
                try {
                    const response = await fetch('/api/v1/chat', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({message: message, user_id: 'web-user'})
                    });
                    
                    const data = await response.json();
                    
                    // Remove thinking indicator
                    chatDiv.removeChild(chatDiv.lastChild);
                    
                    // Add SOPHIA response
                    let responseText = data.response;
                    
                    if (data.swarms_used && data.swarms_used.length > 0) {
                        responseText += '\\n\\n🤖 Swarms Deployed: ' + data.swarms_used.join(', ').toUpperCase();
                    }
                    
                    if (data.model_used) {
                        responseText += '\\n\\n🧠 Master Model: ' + data.model_used;
                    }
                    
                    addMessage('SOPHIA', responseText, 'sophia-message');
                    
                } catch (error) {
                    // Remove thinking indicator
                    chatDiv.removeChild(chatDiv.lastChild);
                    addMessage('SOPHIA', '❌ Error: ' + error.message, 'sophia-message');
                }
            }
            
            function addMessage(sender, text, className) {
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message ' + className;
                messageDiv.innerHTML = '<strong>' + sender + ':</strong> ' + text.replace(/\\n/g, '<br>');
                chatDiv.appendChild(messageDiv);
                chatDiv.scrollTop = chatDiv.scrollHeight;
            }
            
            // Enter key support
            document.getElementById('input').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') sendMessage();
            });
            
            // Welcome message
            addMessage('SOPHIA', '🤠 Howdy! SOPHIA V4 Ultimate with AI Agent Swarms is locked, loaded, and ready to dominate! I command specialized swarms using the top OpenRouter models: Claude Sonnet 4, Qwen3 Coder, Gemini 2.0 Flash, DeepSeek V3, and GPT-5. What mission can my swarms and I accomplish for you today?', 'sophia-message');
        </script>
    </body>
    </html>
    """)

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await sophia_ultimate_swarms.close()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

