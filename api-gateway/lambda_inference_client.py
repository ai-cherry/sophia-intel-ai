"""
Lambda Inference API Client for SOPHIA Intel

Provides access to Lambda's state-of-the-art models including:
- Llama 4 variants (Maverick, Scout)
- DeepSeek R1 (671B, 0528)
- Hermes 3 (405B, 70B, 8B)
- Qwen 2.5 Coder
- And more...
"""

import os
import base64
from typing import List, Dict, Any, Optional, Union
from openai import OpenAI
import asyncio
from functools import wraps


class LambdaInferenceClient:
    """Client for Lambda Inference API with OpenAI-compatible interface"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("LAMBDA_API_KEY")
        if not self.api_key:
            raise ValueError("Lambda API key is required. Set LAMBDA_API_KEY environment variable.")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.lambda.ai/v1"
        )
        
        # Available models from Lambda Inference API
        self.available_models = [
            "llama-4-maverick-17b-128e-instruct-fp8",
            "llama-4-scout-17b-16e-instruct", 
            "deepseek-r1-671b",
            "deepseek-r1-0528",
            "deepseek-v3-0324",
            "deepseek-llama3.3-70b",
            "hermes3-405b",
            "hermes3-70b", 
            "hermes3-8b",
            "llama3.1-405b-instruct-fp8",
            "llama3.1-70b-instruct-fp8",
            "llama3.1-8b-instruct",
            "llama3.1-nemotron-70b-instruct-fp8",
            "llama3.2-11b-vision-instruct",
            "llama3.2-3b-instruct",
            "llama3.3-70b-instruct-fp8",
            "qwen25-coder-32b-instruct",
            "qwen3-32b-fp8",
            "lfm-40b",
            "lfm-7b"
        ]
        
        # Model recommendations for different tasks
        self.model_recommendations = {
            "reasoning": "deepseek-r1-671b",  # Best for complex reasoning
            "coding": "qwen25-coder-32b-instruct",  # Best for code generation
            "general": "llama-4-maverick-17b-128e-instruct-fp8",  # Best general purpose
            "vision": "llama3.2-11b-vision-instruct",  # Best for image analysis
            "large_context": "llama-4-maverick-17b-128e-instruct-fp8",  # 128k context
            "fast": "hermes3-8b",  # Fastest responses
            "powerful": "hermes3-405b"  # Most capable
        }

    def get_recommended_model(self, task_type: str = "general") -> str:
        """Get recommended model for specific task type"""
        return self.model_recommendations.get(task_type, self.model_recommendations["general"])

    def list_models(self) -> List[Dict[str, Any]]:
        """List all available models"""
        try:
            models = self.client.models.list()
            return [{"id": model.id, "created": model.created, "owned_by": model.owned_by} 
                   for model in models.data]
        except Exception as e:
            print(f"Error listing models: {e}")
            return []

    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[Dict[str, Any], Any]:
        """
        Create chat completion using Lambda Inference API
        
        Args:
            messages: List of message objects with 'role' and 'content'
            model: Model to use (defaults to recommended general model)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional parameters
        """
        if not model:
            model = self.get_recommended_model("general")
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
                **kwargs
            )
            
            if stream:
                return response  # Return generator for streaming
            else:
                return {
                    "id": response.id,
                    "model": response.model,
                    "content": response.choices[0].message.content,
                    "finish_reason": response.choices[0].finish_reason,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                }
        except Exception as e:
            print(f"Error in chat completion: {e}")
            return {"error": str(e)}

    def text_completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create text completion using Lambda Inference API
        
        Args:
            prompt: Input text prompt
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        """
        if not model:
            model = self.get_recommended_model("general")
        
        try:
            response = self.client.completions.create(
                model=model,
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            return {
                "id": response.id,
                "model": response.model,
                "text": response.choices[0].text,
                "finish_reason": response.choices[0].finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
        except Exception as e:
            print(f"Error in text completion: {e}")
            return {"error": str(e)}

    def vision_completion(
        self,
        text: str,
        image_data: Union[str, bytes],
        model: Optional[str] = None,
        is_url: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create vision completion with image input
        
        Args:
            text: Text prompt
            image_data: Image data (base64 string, bytes, or URL)
            model: Model to use (defaults to vision model)
            is_url: Whether image_data is a URL
        """
        if not model:
            model = self.get_recommended_model("vision")
        
        # Prepare image content
        if is_url:
            image_content = {"type": "image_url", "image_url": {"url": image_data}}
        else:
            # Handle base64 encoding
            if isinstance(image_data, bytes):
                encoded = base64.b64encode(image_data).decode("utf-8")
                data_uri = f"data:image/jpeg;base64,{encoded}"
            elif image_data.startswith("data:"):
                data_uri = image_data
            else:
                # Assume it's already base64 encoded
                data_uri = f"data:image/jpeg;base64,{image_data}"
            
            image_content = {"type": "image_url", "image_url": {"url": data_uri}}
        
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": text},
                image_content
            ]
        }]
        
        return self.chat_completion(messages, model=model, **kwargs)

    def reasoning_completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Use DeepSeek R1 for complex reasoning tasks
        """
        if not model:
            model = self.get_recommended_model("reasoning")
        
        messages = [{
            "role": "system",
            "content": "You are an expert reasoning assistant. Think step by step and provide detailed analysis."
        }, {
            "role": "user", 
            "content": prompt
        }]
        
        return self.chat_completion(messages, model=model, **kwargs)

    def code_completion(
        self,
        prompt: str,
        language: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Use Qwen 2.5 Coder for code generation tasks
        """
        if not model:
            model = self.get_recommended_model("coding")
        
        system_prompt = "You are an expert programmer. Provide clean, efficient, and well-documented code."
        if language:
            system_prompt += f" Focus on {language} programming."
        
        messages = [{
            "role": "system",
            "content": system_prompt
        }, {
            "role": "user",
            "content": prompt
        }]
        
        return self.chat_completion(messages, model=model, **kwargs)

    async def async_chat_completion(self, *args, **kwargs):
        """Async wrapper for chat completion"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.chat_completion, *args, **kwargs)

    def stream_chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        **kwargs
    ):
        """
        Stream chat completion responses
        
        Yields:
            Dict with incremental response data
        """
        if not model:
            model = self.get_recommended_model("general")
        
        try:
            stream = self.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                **kwargs
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield {
                        "id": chunk.id,
                        "model": chunk.model,
                        "content": chunk.choices[0].delta.content,
                        "finish_reason": chunk.choices[0].finish_reason
                    }
        except Exception as e:
            yield {"error": str(e)}

    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """Get information about a specific model"""
        model_info = {
            "llama-4-maverick-17b-128e-instruct-fp8": {
                "name": "Llama 4 Maverick",
                "size": "17B",
                "context": "128k",
                "strengths": ["General purpose", "Long context", "Instruction following"],
                "best_for": "General conversations and complex tasks"
            },
            "deepseek-r1-671b": {
                "name": "DeepSeek R1",
                "size": "671B", 
                "context": "64k",
                "strengths": ["Reasoning", "Problem solving", "Analysis"],
                "best_for": "Complex reasoning and analytical tasks"
            },
            "qwen25-coder-32b-instruct": {
                "name": "Qwen 2.5 Coder",
                "size": "32B",
                "context": "32k", 
                "strengths": ["Code generation", "Programming", "Technical tasks"],
                "best_for": "Software development and coding tasks"
            },
            "hermes3-405b": {
                "name": "Hermes 3",
                "size": "405B",
                "context": "128k",
                "strengths": ["Capability", "Knowledge", "Reasoning"],
                "best_for": "Most demanding tasks requiring maximum capability"
            }
        }
        
        return model_info.get(model_id, {
            "name": model_id,
            "size": "Unknown",
            "context": "Unknown", 
            "strengths": ["General purpose"],
            "best_for": "General tasks"
        })


# Convenience functions for easy integration
def create_lambda_client(api_key: Optional[str] = None) -> LambdaInferenceClient:
    """Create a Lambda Inference API client"""
    return LambdaInferenceClient(api_key)


def quick_chat(prompt: str, model: Optional[str] = None, api_key: Optional[str] = None) -> str:
    """Quick chat completion - returns just the text response"""
    client = create_lambda_client(api_key)
    messages = [{"role": "user", "content": prompt}]
    response = client.chat_completion(messages, model=model)
    return response.get("content", "Error: " + str(response.get("error", "Unknown error")))


def quick_reasoning(prompt: str, api_key: Optional[str] = None) -> str:
    """Quick reasoning with DeepSeek R1"""
    client = create_lambda_client(api_key)
    response = client.reasoning_completion(prompt)
    return response.get("content", "Error: " + str(response.get("error", "Unknown error")))


def quick_code(prompt: str, language: Optional[str] = None, api_key: Optional[str] = None) -> str:
    """Quick code generation with Qwen 2.5 Coder"""
    client = create_lambda_client(api_key)
    response = client.code_completion(prompt, language=language)
    return response.get("content", "Error: " + str(response.get("error", "Unknown error")))


if __name__ == "__main__":
    # Test the client
    client = create_lambda_client()
    
    # List available models
    print("Available models:")
    models = client.list_models()
    for model in models[:5]:  # Show first 5
        print(f"- {model['id']}")
    
    # Test chat completion
    print("\nTesting chat completion:")
    response = client.chat_completion([
        {"role": "user", "content": "What is SOPHIA Intel?"}
    ])
    print(f"Response: {response.get('content', 'Error')}")
    
    # Test reasoning
    print("\nTesting reasoning:")
    reasoning_response = client.reasoning_completion(
        "Explain the benefits of using Lambda Inference API for AI applications."
    )
    print(f"Reasoning: {reasoning_response.get('content', 'Error')}")

