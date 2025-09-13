"""
LiteLLM Coding Excellence Router
Optimized for software architecture, implementation, and debugging
"""
import os
import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum
import hashlib

import litellm
from litellm import Router, completion
from pydantic import BaseModel, Field
import redis.asyncio as aioredis

# Configure LiteLLM
litellm.set_verbose = False
litellm.telemetry = False

class TaskComplexity(Enum):
    """Task complexity levels for routing"""
    TRIVIAL = "trivial"      # < $0.01 - formatting, simple docs
    SIMPLE = "simple"        # < $0.10 - basic implementation
    MODERATE = "moderate"    # < $0.50 - standard features
    COMPLEX = "complex"      # < $2.00 - architecture, debugging
    CRITICAL = "critical"    # < $5.00 - system design

class CodingTaskType(Enum):
    """Types of coding tasks"""
    ARCHITECTURE = "architecture"
    IMPLEMENTATION = "implementation"
    DEBUGGING = "debugging"
    OPTIMIZATION = "optimization"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    CODE_REVIEW = "code_review"
    REFACTORING = "refactoring"

class CodingTask(BaseModel):
    """Coding task request"""
    request: str
    type: Optional[CodingTaskType] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    max_cost: float = Field(default=5.0)
    timeout: int = Field(default=60)
    require_tests: bool = Field(default=True)
    require_docs: bool = Field(default=True)

class ModelConfig(BaseModel):
    """Model configuration"""
    name: str
    model_id: str
    cost_per_1k_input: float
    cost_per_1k_output: float
    max_tokens: int
    temperature: float
    timeout: int
    best_for: List[str]

class CodingRouter:
    """Enhanced LiteLLM router for coding excellence"""
    
    # Model configurations optimized for coding
    MODELS = {
        # Premium tier - for complex tasks
        "architect": ModelConfig(
            name="Claude Opus Architect",
            model_id="claude-3-opus-20240229",
            cost_per_1k_input=15.0,
            cost_per_1k_output=75.0,
            max_tokens=8000,
            temperature=0.7,
            timeout=120,
            best_for=["architecture", "system_design", "api_design"]
        ),
        "reasoner": ModelConfig(
            name="OpenAI O1 Reasoner",
            model_id="openai/o1-preview",
            cost_per_1k_input=15.0,
            cost_per_1k_output=60.0,
            max_tokens=4000,
            temperature=0.1,
            timeout=120,
            best_for=["debugging", "optimization", "algorithm_design"]
        ),
        
        # Standard tier - for implementation
        "coder": ModelConfig(
            name="DeepSeek Coder",
            model_id="deepseek/deepseek-coder",
            cost_per_1k_input=0.14,
            cost_per_1k_output=0.28,
            max_tokens=4000,
            temperature=0.3,
            timeout=30,
            best_for=["implementation", "refactoring", "code_generation"]
        ),
        "reviewer": ModelConfig(
            name="Claude Sonnet Reviewer",
            model_id="claude-3-sonnet-20240229",
            cost_per_1k_input=3.0,
            cost_per_1k_output=15.0,
            max_tokens=4000,
            temperature=0.4,
            timeout=30,
            best_for=["code_review", "security_analysis", "best_practices"]
        ),
        
        # Economy tier - for simple tasks
        "assistant": ModelConfig(
            name="GPT-4 Turbo Assistant",
            model_id="gpt-4-turbo-preview",
            cost_per_1k_input=10.0,
            cost_per_1k_output=30.0,
            max_tokens=4000,
            temperature=0.5,
            timeout=30,
            best_for=["general", "explanation", "planning"]
        ),
        "documenter": ModelConfig(
            name="Gemini Flash Documenter (OpenRouter)",
            model_id="openrouter/google/gemini-1.5-flash",
            cost_per_1k_input=0.075,
            cost_per_1k_output=0.30,
            max_tokens=2000,
            temperature=0.5,
            timeout=15,
            best_for=["documentation", "comments", "readme"]
        )
    }
    
    # Task patterns for automatic classification
    TASK_PATTERNS = {
        CodingTaskType.ARCHITECTURE: {
            'keywords': ['design', 'architect', 'structure', 'pattern', 'scale', 'system'],
            'model': 'architect',
            'context_needed': ['repository_structure', 'tech_stack', 'requirements']
        },
        CodingTaskType.IMPLEMENTATION: {
            'keywords': ['implement', 'create', 'build', 'develop', 'add', 'feature'],
            'model': 'coder',
            'context_needed': ['relevant_files', 'dependencies', 'examples']
        },
        CodingTaskType.DEBUGGING: {
            'keywords': ['fix', 'debug', 'error', 'issue', 'bug', 'crash', 'failing'],
            'model': 'reasoner',
            'context_needed': ['error_traces', 'logs', 'recent_changes']
        },
        CodingTaskType.OPTIMIZATION: {
            'keywords': ['optimize', 'performance', 'speed', 'efficiency', 'improve'],
            'model': 'reasoner',
            'context_needed': ['performance_metrics', 'bottlenecks', 'profiling']
        },
        CodingTaskType.TESTING: {
            'keywords': ['test', 'validate', 'verify', 'coverage', 'unit', 'integration'],
            'model': 'coder',
            'context_needed': ['implementation_files', 'test_framework', 'coverage']
        },
        CodingTaskType.CODE_REVIEW: {
            'keywords': ['review', 'check', 'audit', 'security', 'quality'],
            'model': 'reviewer',
            'context_needed': ['changed_files', 'pr_description', 'standards']
        },
        CodingTaskType.DOCUMENTATION: {
            'keywords': ['document', 'explain', 'comment', 'readme', 'guide'],
            'model': 'documenter',
            'context_needed': ['code_structure', 'api_endpoints', 'examples']
        }
    }
    
    def __init__(self):
        """Initialize the coding router"""
        self.redis_client = None
        self.total_cost = 0.0
        self.request_count = 0
        self.cache_hits = 0
        
        # Initialize LiteLLM router with model configurations
        self.router = self._setup_router()
        
    def _setup_router(self) -> Router:
        """Setup LiteLLM router with all models"""
        model_list = []
        
        for key, config in self.MODELS.items():
            model_list.append({
                "model_name": config.name,
                "litellm_params": {
                    "model": config.model_id,
                    "api_key": self._get_api_key(config.model_id),
                    "temperature": config.temperature,
                    "max_tokens": config.max_tokens,
                    "timeout": config.timeout
                }
            })
        
        return Router(
            model_list=model_list,
            fallbacks=[
                {"gpt-4-turbo-preview": ["claude-3-sonnet-20240229"]},
                {"claude-3-opus-20240229": ["openai/o1-preview"]},
                {"deepseek/deepseek-coder": ["gpt-4-turbo-preview"]}
            ],
            retry_after=5,
            allowed_fails=2
        )
    
    def _get_api_key(self, model_id: str) -> str:
        """Get API key for model provider"""
        if "claude" in model_id:
            return os.getenv("ANTHROPIC_API_KEY", "")
        elif "openai" in model_id or "gpt" in model_id:
            return os.getenv("OPENAI_API_KEY", "")
        elif "gemini" in model_id:
            return os.getenv("GOOGLE_API_KEY", "")
        elif "deepseek" in model_id:
            return os.getenv("DEEPSEEK_API_KEY", "")
        else:
            return os.getenv("LITELLM_API_KEY", "")
    
    async def initialize(self):
        """Initialize Redis connection"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client = await aioredis.from_url(redis_url, decode_responses=True)
    
    def classify_task(self, request: str) -> Tuple[CodingTaskType, TaskComplexity]:
        """Classify task type and complexity"""
        request_lower = request.lower()
        
        # Determine task type
        task_type = CodingTaskType.IMPLEMENTATION  # default
        max_match = 0
        
        for t_type, pattern in self.TASK_PATTERNS.items():
            matches = sum(1 for keyword in pattern['keywords'] if keyword in request_lower)
            if matches > max_match:
                max_match = matches
                task_type = t_type
        
        # Determine complexity based on indicators
        complexity = TaskComplexity.SIMPLE  # default
        
        if any(word in request_lower for word in ['entire', 'system', 'architecture', 'redesign']):
            complexity = TaskComplexity.CRITICAL
        elif any(word in request_lower for word in ['complex', 'advanced', 'optimize', 'performance']):
            complexity = TaskComplexity.COMPLEX
        elif any(word in request_lower for word in ['implement', 'feature', 'integrate']):
            complexity = TaskComplexity.MODERATE
        elif any(word in request_lower for word in ['fix', 'simple', 'basic', 'add']):
            complexity = TaskComplexity.SIMPLE
        elif any(word in request_lower for word in ['typo', 'comment', 'rename']):
            complexity = TaskComplexity.TRIVIAL
        
        return task_type, complexity
    
    def select_model(self, task_type: CodingTaskType, complexity: TaskComplexity) -> ModelConfig:
        """Select optimal model based on task type and complexity"""
        # Get base model for task type
        pattern = self.TASK_PATTERNS.get(task_type)
        base_model_key = pattern['model'] if pattern else 'assistant'
        
        # Adjust based on complexity
        if complexity == TaskComplexity.CRITICAL:
            # Always use best model for critical tasks
            if task_type in [CodingTaskType.ARCHITECTURE, CodingTaskType.OPTIMIZATION]:
                return self.MODELS['architect']
            else:
                return self.MODELS['reasoner']
        elif complexity == TaskComplexity.TRIVIAL:
            # Always use cheapest model for trivial tasks
            return self.MODELS['documenter']
        else:
            # Use recommended model for task type
            return self.MODELS[base_model_key]
    
    async def get_cache_key(self, task: CodingTask) -> str:
        """Generate cache key for task"""
        content = f"{task.request}:{task.type}:{json.dumps(task.context, sort_keys=True)}"
        return f"litellm:cache:{hashlib.md5(content.encode()).hexdigest()}"
    
    async def get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached response if available"""
        if not self.redis_client:
            return None
        
        try:
            cached = await self.redis_client.get(cache_key)
            if cached:
                self.cache_hits += 1
                return json.loads(cached)
        except Exception:
            pass
        
        return None
    
    async def cache_response(self, cache_key: str, response: Dict[str, Any], ttl: int = 3600):
        """Cache response for future use"""
        if not self.redis_client:
            return
        
        try:
            await self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(response)
            )
        except Exception:
            pass
    
    def build_prompt(self, task: CodingTask, task_type: CodingTaskType) -> str:
        """Build optimized prompt for task"""
        pattern = self.TASK_PATTERNS.get(task_type, {})
        context_needed = pattern.get('context_needed', [])
        
        prompt_parts = [
            "You are an expert software engineer specializing in:",
            f"- {task_type.value.replace('_', ' ').title()}",
            "",
            "TASK:",
            task.request,
            ""
        ]
        
        # Add relevant context
        if task.context:
            prompt_parts.append("CONTEXT:")
            for key in context_needed:
                if key in task.context:
                    prompt_parts.append(f"- {key}: {task.context[key]}")
            prompt_parts.append("")
        
        # Add specific instructions based on task type
        if task_type == CodingTaskType.ARCHITECTURE:
            prompt_parts.extend([
                "REQUIREMENTS:",
                "- Provide clear architectural design",
                "- Include component diagrams if helpful",
                "- Specify interfaces and contracts",
                "- Consider scalability and maintainability",
                "- List technology choices with justification"
            ])
        elif task_type == CodingTaskType.IMPLEMENTATION:
            prompt_parts.extend([
                "REQUIREMENTS:",
                "- Write clean, production-ready code",
                "- Follow best practices and patterns",
                "- Include error handling",
                "- Add appropriate comments",
                "- Ensure code is testable"
            ])
        elif task_type == CodingTaskType.DEBUGGING:
            prompt_parts.extend([
                "REQUIREMENTS:",
                "- Identify root cause",
                "- Provide step-by-step diagnosis",
                "- Suggest multiple solutions if applicable",
                "- Include preventive measures",
                "- Consider edge cases"
            ])
        
        # Add test/doc requirements
        if task.require_tests:
            prompt_parts.append("- Include comprehensive tests")
        if task.require_docs:
            prompt_parts.append("- Include clear documentation")
        
        return "\n".join(prompt_parts)
    
    async def process_task(self, task: CodingTask) -> Dict[str, Any]:
        """Process a coding task with optimal routing"""
        self.request_count += 1
        
        # Check cache first
        cache_key = await self.get_cache_key(task)
        cached_response = await self.get_cached_response(cache_key)
        if cached_response:
            return cached_response
        
        # Classify task
        task_type, complexity = self.classify_task(task.request)
        if task.type:  # Override if explicitly set
            task_type = task.type
        
        # Select model
        model = self.select_model(task_type, complexity)
        
        # Check cost limit
        estimated_cost = (model.cost_per_1k_input * 2) + (model.cost_per_1k_output * 4)
        if estimated_cost > task.max_cost:
            # Downgrade to cheaper model
            model = self.MODELS['assistant']
        
        # Build prompt
        prompt = self.build_prompt(task, task_type)
        
        # Make completion request
        try:
            response = await self.router.acompletion(
                model=model.name,
                messages=[{"role": "user", "content": prompt}],
                temperature=model.temperature,
                max_tokens=model.max_tokens,
                timeout=min(task.timeout, model.timeout)
            )
            
            # Calculate actual cost
            usage = response.usage
            input_cost = (usage.prompt_tokens / 1000) * model.cost_per_1k_input
            output_cost = (usage.completion_tokens / 1000) * model.cost_per_1k_output
            total_cost = input_cost + output_cost
            self.total_cost += total_cost
            
            result = {
                "success": True,
                "task_type": task_type.value,
                "complexity": complexity.value,
                "model_used": model.name,
                "response": response.choices[0].message.content,
                "cost": {
                    "input": input_cost,
                    "output": output_cost,
                    "total": total_cost
                },
                "tokens": {
                    "input": usage.prompt_tokens,
                    "output": usage.completion_tokens,
                    "total": usage.total_tokens
                },
                "cached": False
            }
            
            # Cache successful response
            await self.cache_response(cache_key, result)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "task_type": task_type.value,
                "complexity": complexity.value,
                "model_attempted": model.name
            }
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get router statistics"""
        return {
            "total_requests": self.request_count,
            "total_cost": self.total_cost,
            "average_cost": self.total_cost / max(self.request_count, 1),
            "cache_hits": self.cache_hits,
            "cache_hit_rate": self.cache_hits / max(self.request_count, 1)
        }

# Singleton instance
_router = None

async def get_coding_router() -> CodingRouter:
    """Get or create coding router instance"""
    global _router
    if _router is None:
        _router = CodingRouter()
        await _router.initialize()
    return _router
