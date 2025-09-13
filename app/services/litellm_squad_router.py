"""
LiteLLM Squad Router - Intelligent Multi-Model Orchestration
Integrates Claude Squad, AIMLAPI, and Codex with cost-optimized routing
"""

import os
import json
import asyncio
import yaml
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from enum import Enum
import httpx
import redis
from pydantic import BaseModel, Field
import litellm
from litellm import Router, acompletion
from litellm.caching import Cache
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure LiteLLM
litellm.api_key = os.getenv('LITELLM_API_KEY', '09e30f5d9e3d57d5f3ae98435bda387b84d252d0c58cc10017706cb2d9b2d990')
litellm.set_verbose = True


class TaskComplexity(Enum):
    """Task complexity levels"""
    TRIVIAL = "trivial"      # < 100 tokens, simple operations
    SIMPLE = "simple"        # < 500 tokens, basic tasks
    MODERATE = "moderate"    # < 2000 tokens, standard development
    COMPLEX = "complex"      # < 10000 tokens, architecture/design
    CRITICAL = "critical"    # Any size, security/core systems


class SquadRole(Enum):
    """Squad member roles"""
    ARCHITECT = "architect"
    CODER = "coder"
    REVIEWER = "reviewer"
    DEBUGGER = "debugger"
    TESTER = "tester"
    DOCUMENTER = "documenter"
    ANALYST = "analyst"
    INNOVATOR = "innovator"


class TaskContext(BaseModel):
    """Context for task routing"""
    files: List[str] = Field(default_factory=list)
    language: Optional[str] = None
    framework: Optional[str] = None
    mcp_servers: List[str] = Field(default_factory=list)
    priority: str = Field(default="normal")
    squad_role: Optional[SquadRole] = None
    max_cost: Optional[float] = None
    requires_codex: bool = False
    asana_task_id: Optional[str] = None
    github_issue_id: Optional[str] = None


class IntelligentSquadRouter:
    """Main router for Claude Squad with LiteLLM integration"""
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.router = self._setup_router()
        self.redis_client = self._setup_redis()
        self.cache = self._setup_cache()
        self.cost_tracker = CostTracker(self.redis_client)
        self.task_analyzer = TaskAnalyzer()
        self.mcp_client = MCPIntegration()
        self.codex_client = CodexIntegration()
        
    def _load_config(self, config_path: str = None) -> Dict:
        """Load router configuration"""
        if not config_path:
            config_path = Path(__file__).parent.parent.parent / 'config' / 'litellm_squad_config.yaml'
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        # Substitute environment variables
        config_str = yaml.dump(config)
        for key, value in os.environ.items():
            config_str = config_str.replace(f'${{{key}}}', value)
        
        return yaml.safe_load(config_str)
    
    def _setup_router(self) -> Router:
        """Setup LiteLLM router"""
        return Router(
            model_list=self.config['model_list'],
            fallbacks=self._create_fallback_chains(),
            set_verbose=True,
            cache_responses=True,
            num_retries=3,
            timeout=120
        )
    
    def _setup_redis(self) -> redis.Redis:
        """Setup Redis connection"""
        return redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
    
    def _setup_cache(self) -> Cache:
        """Setup caching"""
        return Cache(
            type="redis",
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            ttl=3600
        )
    
    def _create_fallback_chains(self) -> List[Dict]:
        """Create fallback chains from config"""
        chains = []
        for tier, models in self.config['router_settings']['fallback_chains'].items():
            if len(models) > 1:
                for i in range(len(models) - 1):
                    chains.append({models[i]: [models[i + 1]]})
        return chains
    
    async def route_squad_request(
        self,
        messages: List[Dict],
        context: TaskContext,
        stream: bool = False
    ) -> Dict:
        """Route request to optimal model based on squad role and task analysis"""
        
        # Check daily budget
        if not await self.cost_tracker.check_budget():
            logger.warning("Daily budget exceeded, using economy tier")
            context.max_cost = 0.5
        
        # Determine model based on squad role or task analysis
        if context.squad_role:
            model_name = self._get_model_for_role(context.squad_role)
        else:
            complexity = await self.task_analyzer.analyze_complexity(messages, context)
            model_name = self._get_model_for_complexity(complexity)
        
        # Check if Codex is required
        if context.requires_codex:
            return await self.codex_client.execute_task(messages, context)
        
        # Apply cost constraints
        if context.max_cost:
            model_name = self._get_cheapest_capable_model(model_name, context.max_cost)
        
        # Add context from MCP servers if needed
        if context.mcp_servers:
            mcp_context = await self.mcp_client.gather_context(context.mcp_servers)
            messages = self._inject_mcp_context(messages, mcp_context)
        
        # Execute request
        try:
            logger.info(f"Routing to {model_name} (role: {context.squad_role}, cost limit: {context.max_cost})")
            
            response = await self.router.acompletion(
                model=model_name,
                messages=messages,
                stream=stream,
                metadata={
                    "squad_role": context.squad_role.value if context.squad_role else None,
                    "task_id": context.asana_task_id or context.github_issue_id,
                    "files": context.files
                }
            )
            
            # Track cost and usage
            if not stream and 'usage' in response:
                await self._track_usage(model_name, response['usage'], context)
            
            # Add routing metadata
            response['sophia_routing'] = {
                'model_used': model_name,
                'squad_role': context.squad_role.value if context.squad_role else None,
                'estimated_cost': await self._estimate_cost(model_name, response.get('usage', {}))
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error routing request: {e}")
            # Fallback to economy model
            return await self._fallback_request(messages, context)
    
    def _get_model_for_role(self, role: SquadRole) -> str:
        """Get primary model for squad role"""
        role_config = self.config['squad_roles'].get(role.value, {})
        return role_config.get('primary_model', 'gemini-assistant')
    
    def _get_model_for_complexity(self, complexity: TaskComplexity) -> str:
        """Get model based on task complexity"""
        complexity_models = {
            TaskComplexity.TRIVIAL: 'gemini-assistant',
            TaskComplexity.SIMPLE: 'gpt35-quick',
            TaskComplexity.MODERATE: 'deepseek-coder',
            TaskComplexity.COMPLEX: 'claude-architect',
            TaskComplexity.CRITICAL: 'openai-reasoner'
        }
        return complexity_models.get(complexity, 'gpt35-quick')
    
    def _get_cheapest_capable_model(self, preferred_model: str, max_cost: float) -> str:
        """Find cheapest model that meets requirements"""
        # Get model metadata
        model_configs = {m['model_name']: m for m in self.config['model_list']}
        
        if preferred_model in model_configs:
            preferred_cost = model_configs[preferred_model]['metadata']['cost_per_1k_tokens']
            if preferred_cost <= max_cost * 1000:
                return preferred_model
        
        # Find cheaper alternative
        suitable_models = [
            (m['model_name'], m['metadata']['cost_per_1k_tokens'])
            for m in self.config['model_list']
            if m['metadata']['cost_per_1k_tokens'] <= max_cost * 1000
        ]
        
        if suitable_models:
            suitable_models.sort(key=lambda x: x[1], reverse=True)  # Best model within budget
            return suitable_models[0][0]
        
        return 'gemini-assistant'  # Ultimate fallback
    
    def _inject_mcp_context(self, messages: List[Dict], mcp_context: Dict) -> List[Dict]:
        """Inject MCP context into messages"""
        context_message = {
            "role": "system",
            "content": f"Repository context from MCP servers:\n{json.dumps(mcp_context, indent=2)}"
        }
        
        # Insert after first system message or at beginning
        if messages and messages[0].get('role') == 'system':
            messages.insert(1, context_message)
        else:
            messages.insert(0, context_message)
        
        return messages
    
    async def _track_usage(self, model_name: str, usage: Dict, context: TaskContext):
        """Track usage and costs"""
        model_config = next(
            (m for m in self.config['model_list'] if m['model_name'] == model_name),
            None
        )
        
        if model_config:
            cost_per_token = model_config['metadata']['cost_per_1k_tokens'] / 1000
            total_tokens = usage.get('total_tokens', 0)
            cost = await self.cost_tracker.track_cost(model_name, total_tokens, cost_per_token)
            
            # Log to monitoring
            logger.info(f"Usage: {model_name} - {total_tokens} tokens - ${cost:.4f}")
            
            # Track by squad role
            if context.squad_role:
                role_key = f"squad:usage:{context.squad_role.value}:{datetime.now().strftime('%Y-%m-%d')}"
                self.redis_client.incrbyfloat(role_key, cost)
    
    async def _estimate_cost(self, model_name: str, usage: Dict) -> float:
        """Estimate cost for a request"""
        model_config = next(
            (m for m in self.config['model_list'] if m['model_name'] == model_name),
            None
        )
        
        if model_config and usage:
            cost_per_token = model_config['metadata']['cost_per_1k_tokens'] / 1000
            total_tokens = usage.get('total_tokens', 0)
            return total_tokens * cost_per_token
        
        return 0.0
    
    async def _fallback_request(self, messages: List[Dict], context: TaskContext) -> Dict:
        """Fallback to economy model"""
        logger.warning("Falling back to economy model")
        return await self.router.acompletion(
            model='gemini-assistant',
            messages=messages,
            metadata={"fallback": True}
        )


class TaskAnalyzer:
    """Analyzes tasks to determine complexity and optimal routing"""
    
    COMPLEXITY_PATTERNS = {
        TaskComplexity.CRITICAL: [
            r'security', r'vulnerability', r'authentication', r'authorization',
            r'encryption', r'production', r'critical', r'urgent'
        ],
        TaskComplexity.COMPLEX: [
            r'architecture', r'design', r'refactor', r'migrate', r'optimize',
            r'performance', r'scale', r'distributed', r'microservice'
        ],
        TaskComplexity.MODERATE: [
            r'implement', r'feature', r'api', r'endpoint', r'service',
            r'integrate', r'database', r'model', r'controller'
        ],
        TaskComplexity.SIMPLE: [
            r'fix', r'bug', r'update', r'modify', r'change',
            r'add', r'remove', r'adjust', r'correct'
        ],
        TaskComplexity.TRIVIAL: [
            r'format', r'rename', r'comment', r'document', r'typo',
            r'spacing', r'indent', r'style', r'cleanup'
        ]
    }
    
    async def analyze_complexity(
        self,
        messages: List[Dict],
        context: TaskContext
    ) -> TaskComplexity:
        """Analyze task complexity from messages and context"""
        
        # Combine all message content
        text = ' '.join([m.get('content', '') for m in messages]).lower()
        
        # Check for complexity indicators
        for complexity, patterns in self.COMPLEXITY_PATTERNS.items():
            for pattern in patterns:
                if pattern in text:
                    return complexity
        
        # Check file context
        if context.files:
            total_files = len(context.files)
            if total_files > 10:
                return TaskComplexity.COMPLEX
            elif total_files > 5:
                return TaskComplexity.MODERATE
            elif total_files > 1:
                return TaskComplexity.SIMPLE
        
        # Check message length
        total_length = sum(len(m.get('content', '')) for m in messages)
        if total_length > 5000:
            return TaskComplexity.COMPLEX
        elif total_length > 2000:
            return TaskComplexity.MODERATE
        elif total_length > 500:
            return TaskComplexity.SIMPLE
        
        return TaskComplexity.TRIVIAL


class CostTracker:
    """Tracks and manages API costs"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.daily_key_prefix = "litellm:costs:daily:"
        self.hourly_key_prefix = "litellm:costs:hourly:"
    
    async def track_cost(
        self,
        model: str,
        tokens: int,
        cost_per_token: float
    ) -> float:
        """Track cost for a request"""
        cost = tokens * cost_per_token
        
        # Track daily
        daily_key = f"{self.daily_key_prefix}{datetime.now().strftime('%Y-%m-%d')}"
        self.redis.incrbyfloat(daily_key, cost)
        self.redis.expire(daily_key, 86400 * 7)  # Keep for 7 days
        
        # Track hourly
        hourly_key = f"{self.hourly_key_prefix}{datetime.now().strftime('%Y-%m-%d-%H')}"
        self.redis.incrbyfloat(hourly_key, cost)
        self.redis.expire(hourly_key, 86400)  # Keep for 1 day
        
        # Track by model
        model_key = f"{daily_key}:model:{model}"
        self.redis.incrbyfloat(model_key, cost)
        
        return cost
    
    async def check_budget(self, limit: float = None) -> bool:
        """Check if within budget"""
        if limit is None:
            limit = float(os.getenv('LITELLM_DAILY_BUDGET', '100.0'))
        
        daily_key = f"{self.daily_key_prefix}{datetime.now().strftime('%Y-%m-%d')}"
        current = float(self.redis.get(daily_key) or 0)
        
        return current < limit
    
    async def get_usage_report(self) -> Dict:
        """Get usage report"""
        daily_key = f"{self.daily_key_prefix}{datetime.now().strftime('%Y-%m-%d')}"
        hourly_key = f"{self.hourly_key_prefix}{datetime.now().strftime('%Y-%m-%d-%H')}"
        
        # Get model breakdown
        model_costs = {}
        for key in self.redis.scan_iter(f"{daily_key}:model:*"):
            model_name = key.split(':')[-1]
            model_costs[model_name] = float(self.redis.get(key) or 0)
        
        return {
            'daily_total': float(self.redis.get(daily_key) or 0),
            'hourly_total': float(self.redis.get(hourly_key) or 0),
            'by_model': model_costs,
            'daily_limit': float(os.getenv('LITELLM_DAILY_BUDGET', '100.0'))
        }


class MCPIntegration:
    """Integration with MCP servers"""
    
    def __init__(self):
        self.servers = {
            'memory': 'http://localhost:8081',
            'filesystem': 'http://localhost:8082',
            'git': 'http://localhost:8084',
            'web': 'http://localhost:8083'
        }
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def gather_context(self, server_names: List[str]) -> Dict:
        """Gather context from specified MCP servers"""
        context = {}
        
        for server_name in server_names:
            if server_name in self.servers:
                try:
                    # Get appropriate context based on server type
                    if server_name == 'git':
                        response = await self.client.post(
                            f"{self.servers[server_name]}/git/status",
                            json={"repo": "sophia"}
                        )
                        context['git_status'] = response.json()
                    
                    elif server_name == 'filesystem':
                        response = await self.client.post(
                            f"{self.servers[server_name]}/repo/list",
                            json={"root": ".", "globs": ["*.py"], "limit": 10}
                        )
                        context['repository_files'] = response.json()
                    
                    elif server_name == 'memory':
                        response = await self.client.post(
                            f"{self.servers[server_name]}/memory/search",
                            json={"namespace": "default", "query": "context", "limit": 5}
                        )
                        context['memory_context'] = response.json()
                    
                except Exception as e:
                    logger.warning(f"Failed to get context from {server_name}: {e}")
        
        return context


class CodexIntegration:
    """Integration with OpenAI Codex"""
    
    def __init__(self):
        self.base_url = os.getenv('CODEX_BASE_URL', 'http://localhost:8090/v1')
        self.client = httpx.AsyncClient(timeout=120.0)
    
    async def execute_task(
        self,
        messages: List[Dict],
        context: TaskContext
    ) -> Dict:
        """Execute task using Codex with MCP support"""
        
        # Prepare Codex-specific request
        codex_request = {
            "messages": messages,
            "model": os.getenv('CODEX_MODEL', 'codex-1'),
            "max_tokens": 192000,
            "temperature": 0.4,
            "mcp_enabled": True,
            "mcp_servers": context.mcp_servers,
            "files": context.files
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=codex_request
            )
            
            result = response.json()
            result['codex_execution'] = True
            return result
            
        except Exception as e:
            logger.error(f"Codex execution failed: {e}")
            # Fallback to regular model
            return {"error": str(e), "fallback": True}


# Export main router class
__all__ = ['IntelligentSquadRouter', 'TaskContext', 'SquadRole', 'TaskComplexity']