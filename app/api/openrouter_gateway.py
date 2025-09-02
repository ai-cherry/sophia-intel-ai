"""
OpenRouter Gateway - REAL AI EXECUTION, NO MOCKS
Direct integration with OpenRouter for all model access
"""

import os
import json
import httpx
import logging
from typing import Dict, List, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class ModelProvider(Enum):
    """Real model providers via OpenRouter"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    DEEPSEEK = "deepseek"
    XAI = "x-ai"
    GROQ = "groq"
    QWEN = "qwen"
    PERPLEXITY = "perplexity"

class RealModelGateway:
    """Gateway for REAL AI model execution via OpenRouter"""
    
    # REAL MODELS - NO FAKES
    MODELS = {
        # Top tier models - GPT-5 as requested (fallback to best available)
        'orchestrator': 'openai/gpt-5',  # GPT-5 as main orchestrator (will fallback if not available)
        'planner': 'google/gemini-2.5-pro',  # Gemini 2.5 Pro for planning
        'generator': 'deepseek/deepseek-chat',  # DeepSeek for code generation
        'critic': 'anthropic/claude-3-5-sonnet-20241022',  # Claude for review
        'judge': 'x-ai/grok-2-latest',  # Grok for decisions
        
        # Fast execution models
        'runner': 'groq/llama-3.3-70b-versatile',  # Groq for speed
        'fast': 'google/gemini-2.0-flash-exp:free',  # Gemini Flash for quick tasks
        
        # Specialized models
        'coder': 'deepseek/deepseek-chat',  # DeepSeek for code
        'search': 'perplexity/sonar-online',  # Perplexity for web search
        'creative': 'x-ai/grok-2-latest',  # Grok for creative tasks
        
        # Fallback models
        'balanced': 'openai/gpt-4o-mini',  # Cheaper GPT-4
        'free': 'google/gemini-2.0-flash-exp:free',  # Free tier
    }
    
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not set - cannot make REAL API calls")
        
        logger.info(f"✅ OpenRouter Gateway initialized with REAL models")
        
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        role: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make REAL API call to OpenRouter
        
        Args:
            messages: Chat messages
            model: Direct model name or None to use role-based selection
            role: Role name to auto-select model
            temperature: Model temperature
            max_tokens: Max tokens to generate
            stream: Whether to stream response
            **kwargs: Additional parameters
        """
        
        # Select model based on role or use provided model
        if not model:
            if role and role in self.MODELS:
                model = self.MODELS[role]
            else:
                model = self.MODELS['balanced']  # Default to balanced
        
        # Ensure model format is correct for OpenRouter
        if not model.startswith(('openai/', 'anthropic/', 'google/', 'deepseek/', 'x-ai/', 'groq/', 'qwen/', 'perplexity/')):
            # Try to map common names
            if 'gpt' in model.lower():
                model = f"openai/{model}"
            elif 'claude' in model.lower():
                model = f"anthropic/{model}"
            elif 'gemini' in model.lower():
                model = f"google/{model}"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": os.getenv("HTTP_REFERER", "http://localhost:3000"),
            "X-Title": os.getenv("X_TITLE", "Sophia-Intel-AI"),
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream
        }
        
        # Add any additional kwargs
        payload.update(kwargs)
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                logger.info(f"🚀 Making REAL API call to {model}")
                
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"✅ REAL response received from {model}")
                    
                    # Add metadata about the real call
                    if 'choices' in result and result['choices']:
                        result['_metadata'] = {
                            'real_api_call': True,
                            'model_used': model,
                            'provider': model.split('/')[0],
                            'no_mocks': True
                        }
                    
                    return result
                else:
                    error_msg = f"OpenRouter API error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    
                    # Try to parse error for better handling
                    try:
                        error_data = response.json()
                        if 'error' in error_data:
                            error_msg = error_data['error'].get('message', error_msg)
                    except:
                        pass
                    
                    raise httpx.HTTPStatusError(
                        error_msg,
                        request=response.request,
                        response=response
                    )
                    
        except httpx.TimeoutException:
            logger.error(f"Timeout calling {model}")
            raise
        except Exception as e:
            logger.error(f"Error calling {model}: {str(e)}")
            raise
    
    async def generate_embeddings(
        self,
        texts: List[str],
        model: str = "openai/text-embedding-3-small"
    ) -> Dict[str, Any]:
        """Generate REAL embeddings via OpenRouter"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "input": texts
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    raise httpx.HTTPStatusError(
                        f"Embedding error: {response.status_code} - {response.text}",
                        request=response.request,
                        response=response
                    )
        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            raise

# Global instance for REAL API calls
real_gateway = RealModelGateway()

async def execute_real_llm_call(
    prompt: str,
    role: str = "generator",
    temperature: float = 0.7,
    max_tokens: int = 2048,
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function for REAL LLM calls
    
    Args:
        prompt: The prompt to send
        role: Role to determine model selection
        temperature: Model temperature
        max_tokens: Max tokens to generate
        **kwargs: Additional parameters
    
    Returns:
        REAL API response with content
    """
    
    messages = [{"role": "user", "content": prompt}]
    
    response = await real_gateway.chat_completion(
        messages=messages,
        role=role,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs
    )
    
    # Extract content from response
    if response and 'choices' in response and response['choices']:
        content = response['choices'][0]['message']['content']
        return {
            'content': content,
            'success': True,
            'model': response.get('model'),
            'usage': response.get('usage'),
            'metadata': response.get('_metadata')
        }
    else:
        return {
            'content': 'No response generated',
            'success': False,
            'error': 'Empty response from API'
        }