#!/usr/bin/env python3
"""
OpenRouter Squad Service - Third Option for Multi-Model Access
Provides access to 200+ models with automatic routing and competitive pricing
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional, AsyncIterator
from datetime import datetime
from pathlib import Path
import httpx
from pydantic import BaseModel, Field
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
OPENROUTER_BASE_URL = 'https://openrouter.ai/api/v1'


class OpenRouterModels:
    """OpenRouter model definitions with pricing and capabilities"""
    
    # Premium Models ($10-30/M tokens)
    PREMIUM = {
        'anthropic/claude-3-opus': {
            'name': 'Claude 3 Opus',
            'context': 200000,
            'price_per_million': 15.00,
            'capabilities': ['reasoning', 'coding', 'analysis', 'creative'],
            'speed': 'slow',
            'quality': 'excellent'
        },
        'openai/gpt-4-turbo': {
            'name': 'GPT-4 Turbo',
            'context': 128000,
            'price_per_million': 10.00,
            'capabilities': ['general', 'coding', 'reasoning'],
            'speed': 'medium',
            'quality': 'excellent'
        },
        'google/gemini-pro-1.5': {
            'name': 'Gemini Pro 1.5',
            'context': 1000000,  # 1M context!
            'price_per_million': 7.00,
            'capabilities': ['long_context', 'multimodal', 'analysis'],
            'speed': 'medium',
            'quality': 'excellent'
        }
    }
    
    # Standard Models ($1-10/M tokens)
    STANDARD = {
        'anthropic/claude-3-sonnet': {
            'name': 'Claude 3 Sonnet',
            'context': 200000,
            'price_per_million': 3.00,
            'capabilities': ['coding', 'analysis', 'general'],
            'speed': 'fast',
            'quality': 'very_good'
        },
        'anthropic/claude-3-haiku': {
            'name': 'Claude 3 Haiku',
            'context': 200000,
            'price_per_million': 0.25,
            'capabilities': ['quick_tasks', 'classification', 'extraction'],
            'speed': 'very_fast',
            'quality': 'good'
        },
        'mistral/mistral-large': {
            'name': 'Mistral Large',
            'context': 32000,
            'price_per_million': 2.00,
            'capabilities': ['coding', 'reasoning', 'multilingual'],
            'speed': 'fast',
            'quality': 'very_good'
        },
        'meta-llama/llama-3-70b-instruct': {
            'name': 'Llama 3 70B',
            'context': 8000,
            'price_per_million': 0.70,
            'capabilities': ['general', 'coding', 'chat'],
            'speed': 'fast',
            'quality': 'good'
        },
        'deepseek/deepseek-chat': {
            'name': 'DeepSeek Chat',
            'context': 32000,
            'price_per_million': 0.14,
            'capabilities': ['coding', 'reasoning', 'math'],
            'speed': 'fast',
            'quality': 'good'
        }
    }
    
    # Economy Models (<$1/M tokens)
    ECONOMY = {
        'openai/gpt-3.5-turbo': {
            'name': 'GPT-3.5 Turbo',
            'context': 16385,
            'price_per_million': 0.50,
            'capabilities': ['general', 'quick_tasks'],
            'speed': 'very_fast',
            'quality': 'decent'
        },
        'google/gemini-flash': {
            'name': 'Gemini Flash',
            'context': 32000,
            'price_per_million': 0.075,  # Super cheap!
            'capabilities': ['quick_tasks', 'extraction', 'summary'],
            'speed': 'instant',
            'quality': 'decent'
        },
        'mistral/mistral-7b-instruct': {
            'name': 'Mistral 7B',
            'context': 32000,
            'price_per_million': 0.07,
            'capabilities': ['basic_tasks', 'chat'],
            'speed': 'instant',
            'quality': 'basic'
        }
    }
    
    # Specialized Models
    SPECIALIZED = {
        'openai/o1-preview': {
            'name': 'OpenAI o1 Preview',
            'context': 128000,
            'price_per_million': 15.00,
            'capabilities': ['deep_reasoning', 'math', 'science', 'coding'],
            'speed': 'very_slow',
            'quality': 'exceptional'
        },
        'perplexity/llama-3-sonar-large-32k-online': {
            'name': 'Perplexity Sonar',
            'context': 32000,
            'price_per_million': 1.00,
            'capabilities': ['web_search', 'current_events', 'research'],
            'speed': 'medium',
            'quality': 'very_good'
        },
        'nvidia/nemotron-4-340b-instruct': {
            'name': 'Nemotron 340B',
            'context': 4096,
            'price_per_million': 4.20,
            'capabilities': ['synthetic_data', 'roleplay', 'creative'],
            'speed': 'slow',
            'quality': 'excellent'
        },
        'cohere/command-r-plus': {
            'name': 'Command R+',
            'context': 128000,
            'price_per_million': 3.00,
            'capabilities': ['rag', 'retrieval', 'grounded_generation'],
            'speed': 'medium',
            'quality': 'very_good'
        }
    }
    
    # Free Models (with rate limits)
    FREE = {
        'google/gemma-7b-it:free': {
            'name': 'Gemma 7B (Free)',
            'context': 8192,
            'price_per_million': 0,
            'capabilities': ['basic_tasks'],
            'speed': 'fast',
            'quality': 'basic',
            'rate_limit': '10 requests/minute'
        },
        'meta-llama/llama-3-8b-instruct:free': {
            'name': 'Llama 3 8B (Free)',
            'context': 8000,
            'price_per_million': 0,
            'capabilities': ['general', 'chat'],
            'speed': 'fast',
            'quality': 'decent',
            'rate_limit': '10 requests/minute'
        }
    }


class OpenRouterRequest(BaseModel):
    """Request model for OpenRouter API"""
    model: str
    messages: List[Dict[str, str]]
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream: bool = False
    route: Optional[str] = None  # "fallback" for auto-routing
    transforms: List[str] = Field(default_factory=list)  # ["middle-out"] for compression
    provider: Optional[Dict] = None  # Provider preferences


class OpenRouterSquadService:
    """OpenRouter integration for Sophia Squad"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or OPENROUTER_API_KEY
        self.base_url = OPENROUTER_BASE_URL
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'HTTP-Referer': 'https://sophia-intel-ai.com',
                'X-Title': 'Sophia Intel AI Squad'
            },
            timeout=120.0
        )
        self.models = self._merge_models()
        
    def _merge_models(self) -> Dict[str, Any]:
        """Merge all model categories"""
        all_models = {}
        for category in [
            OpenRouterModels.PREMIUM,
            OpenRouterModels.STANDARD,
            OpenRouterModels.ECONOMY,
            OpenRouterModels.SPECIALIZED,
            OpenRouterModels.FREE
        ]:
            all_models.update(category)
        return all_models
    
    async def get_available_models(self) -> List[Dict]:
        """Get list of available models from OpenRouter"""
        try:
            response = await self.client.get('/models')
            if response.status_code == 200:
                return response.json()['data']
            return []
        except Exception as e:
            logger.error(f"Failed to get models: {e}")
            return []
    
    async def get_model_pricing(self) -> Dict[str, float]:
        """Get current model pricing"""
        models = await self.get_available_models()
        pricing = {}
        for model in models:
            model_id = model['id']
            # Convert from per-token to per-million tokens
            if 'pricing' in model:
                prompt_price = float(model['pricing'].get('prompt', 0)) * 1_000_000
                completion_price = float(model['pricing'].get('completion', 0)) * 1_000_000
                # Average for simplicity
                pricing[model_id] = (prompt_price + completion_price) / 2
        return pricing
    
    def select_model_for_task(
        self,
        task_type: str,
        max_cost: float = None,
        min_quality: str = None,
        required_capabilities: List[str] = None
    ) -> str:
        """Intelligently select model based on requirements"""
        
        # Task type to model mapping
        task_models = {
            'architecture': ['anthropic/claude-3-opus', 'openai/gpt-4-turbo'],
            'coding': ['anthropic/claude-3-sonnet', 'deepseek/deepseek-chat'],
            'reasoning': ['openai/o1-preview', 'anthropic/claude-3-opus'],
            'research': ['perplexity/llama-3-sonar-large-32k-online'],
            'quick_task': ['google/gemini-flash', 'anthropic/claude-3-haiku'],
            'documentation': ['openai/gpt-3.5-turbo', 'mistral/mistral-7b-instruct'],
            'creative': ['nvidia/nemotron-4-340b-instruct', 'anthropic/claude-3-opus'],
            'long_context': ['google/gemini-pro-1.5', 'anthropic/claude-3-opus']
        }
        
        candidates = task_models.get(task_type, ['anthropic/claude-3-haiku'])
        
        # Filter by cost if specified
        if max_cost:
            candidates = [
                m for m in candidates
                if m in self.models and self.models[m]['price_per_million'] <= max_cost * 1000
            ]
        
        # Filter by quality if specified
        if min_quality:
            quality_levels = ['basic', 'decent', 'good', 'very_good', 'excellent', 'exceptional']
            min_level = quality_levels.index(min_quality)
            candidates = [
                m for m in candidates
                if m in self.models and quality_levels.index(self.models[m]['quality']) >= min_level
            ]
        
        # Filter by required capabilities
        if required_capabilities:
            candidates = [
                m for m in candidates
                if m in self.models and all(
                    cap in self.models[m]['capabilities'] for cap in required_capabilities
                )
            ]
        
        # Return best candidate or default
        return candidates[0] if candidates else 'anthropic/claude-3-haiku'
    
    async def completion(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = None,
        stream: bool = False,
        auto_route: bool = True
    ) -> Dict[str, Any]:
        """Send completion request to OpenRouter"""
        
        # Auto-select model if not specified
        if not model:
            # Analyze message complexity
            total_length = sum(len(m['content']) for m in messages)
            if total_length < 500:
                model = 'google/gemini-flash'  # Cheap and fast
            elif total_length < 2000:
                model = 'anthropic/claude-3-haiku'  # Good balance
            else:
                model = 'anthropic/claude-3-sonnet'  # Better for complex
        
        # Build request
        request = OpenRouterRequest(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
            route="fallback" if auto_route else None
        )
        
        try:
            if stream:
                return await self._stream_completion(request)
            else:
                response = await self.client.post(
                    '/chat/completions',
                    json=request.dict(exclude_none=True)
                )
                response.raise_for_status()
                result = response.json()
                
                # Add cost information
                if model in self.models:
                    tokens = result.get('usage', {}).get('total_tokens', 0)
                    cost = (tokens / 1_000_000) * self.models[model]['price_per_million']
                    result['estimated_cost'] = cost
                    result['model_info'] = self.models[model]
                
                return result
                
        except httpx.HTTPError as e:
            logger.error(f"OpenRouter request failed: {e}")
            raise
    
    async def _stream_completion(self, request: OpenRouterRequest) -> AsyncIterator[str]:
        """Stream completion from OpenRouter"""
        request.stream = True
        
        async with self.client.stream(
            'POST',
            '/chat/completions',
            json=request.dict(exclude_none=True)
        ) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if line.startswith('data: '):
                    data = line[6:]
                    if data == '[DONE]':
                        break
                    
                    try:
                        chunk = json.loads(data)
                        if 'choices' in chunk and chunk['choices']:
                            delta = chunk['choices'][0].get('delta', {})
                            if 'content' in delta:
                                yield delta['content']
                    except json.JSONDecodeError:
                        continue
    
    async def get_generation_stats(self, generation_id: str) -> Dict:
        """Get stats for a specific generation"""
        response = await self.client.get(f'/generations/{generation_id}')
        if response.status_code == 200:
            return response.json()
        return {}
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


class OpenRouterSquadOrchestrator:
    """Orchestrator for OpenRouter-based squad agents"""
    
    def __init__(self, api_key: str = None):
        self.service = OpenRouterSquadService(api_key)
        self.agents = self._initialize_agents()
        
    def _initialize_agents(self) -> Dict[str, Dict]:
        """Initialize squad agents with OpenRouter models"""
        return {
            'architect': {
                'name': 'OpenRouter Architect',
                'models': ['anthropic/claude-3-opus', 'openai/gpt-4-turbo'],
                'capabilities': ['system_design', 'architecture', 'planning'],
                'max_cost': 15.00
            },
            'coder': {
                'name': 'OpenRouter Coder',
                'models': ['anthropic/claude-3-sonnet', 'deepseek/deepseek-chat'],
                'capabilities': ['implementation', 'refactoring', 'debugging'],
                'max_cost': 3.00
            },
            'researcher': {
                'name': 'OpenRouter Researcher',
                'models': ['perplexity/llama-3-sonar-large-32k-online'],
                'capabilities': ['web_search', 'current_events', 'fact_checking'],
                'max_cost': 1.00
            },
            'reasoner': {
                'name': 'OpenRouter Reasoner',
                'models': ['openai/o1-preview', 'anthropic/claude-3-opus'],
                'capabilities': ['deep_reasoning', 'math', 'logic'],
                'max_cost': 15.00
            },
            'speed_coder': {
                'name': 'OpenRouter Speed Coder',
                'models': ['google/gemini-flash', 'anthropic/claude-3-haiku'],
                'capabilities': ['quick_fixes', 'simple_tasks', 'formatting'],
                'max_cost': 0.25
            },
            'creative': {
                'name': 'OpenRouter Creative',
                'models': ['nvidia/nemotron-4-340b-instruct'],
                'capabilities': ['creative_writing', 'synthetic_data', 'roleplay'],
                'max_cost': 5.00
            }
        }
    
    async def assign_task(
        self,
        task: str,
        task_type: str = None,
        context: Dict = None
    ) -> Dict:
        """Assign task to appropriate agent with model selection"""
        
        # Determine task type if not specified
        if not task_type:
            if any(word in task.lower() for word in ['design', 'architecture', 'system']):
                task_type = 'architecture'
            elif any(word in task.lower() for word in ['implement', 'code', 'fix', 'bug']):
                task_type = 'coding'
            elif any(word in task.lower() for word in ['research', 'find', 'search']):
                task_type = 'research'
            elif any(word in task.lower() for word in ['reason', 'analyze', 'solve']):
                task_type = 'reasoning'
            else:
                task_type = 'general'
        
        # Select agent and model
        agent_map = {
            'architecture': 'architect',
            'coding': 'coder',
            'research': 'researcher',
            'reasoning': 'reasoner',
            'quick': 'speed_coder',
            'creative': 'creative'
        }
        
        agent_role = agent_map.get(task_type, 'coder')
        agent = self.agents[agent_role]
        
        # Select best model for task
        model = self.service.select_model_for_task(
            task_type=task_type,
            max_cost=agent['max_cost'] / 1000,  # Convert to per-token
            min_quality='good' if task_type in ['architecture', 'reasoning'] else 'decent',
            required_capabilities=agent['capabilities']
        )
        
        # Build messages
        messages = [
            {
                "role": "system",
                "content": f"You are {agent['name']}, specialized in {', '.join(agent['capabilities'])}."
            },
            {
                "role": "user",
                "content": task
            }
        ]
        
        # Add context if provided
        if context:
            messages.insert(1, {
                "role": "system",
                "content": f"Context: {json.dumps(context)}"
            })
        
        # Execute task
        result = await self.service.completion(
            messages=messages,
            model=model,
            temperature=0.3 if task_type == 'coding' else 0.7
        )
        
        return {
            'agent': agent['name'],
            'model': model,
            'response': result.get('choices', [{}])[0].get('message', {}).get('content'),
            'cost': result.get('estimated_cost', 0),
            'tokens': result.get('usage', {})
        }
    
    async def close(self):
        """Cleanup"""
        await self.service.close()


# Export main classes
__all__ = ['OpenRouterSquadService', 'OpenRouterSquadOrchestrator', 'OpenRouterModels']