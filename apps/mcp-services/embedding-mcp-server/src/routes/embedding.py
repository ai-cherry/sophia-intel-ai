"""
SOPHIA Intel Embedding MCP Server Routes
Vendor-independent embedding generation with multiple providers
"""

from flask import Blueprint, request, jsonify
import os
import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union
import json

# Create blueprint
embedding_bp = Blueprint('embedding', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingMCP:
    """Vendor-independent embedding generation service"""
    
    def __init__(self):
        # Get API keys from environment variables (populated by Kubernetes secrets)
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.lambda_cloud_api_key = os.getenv("LAMBDA_CLOUD_API_KEY")
        
        # Load embedding models configuration
        self.models_config = self._load_models_config()
        
        logger.info("Embedding MCP initialized with vendor-independent architecture")
    
    def _load_models_config(self) -> Dict:
        """Load embedding models configuration"""
        return {
            "default": "nomic-ai/nomic-embed-text-v1.5",
            "models": {
                "nomic-ai/nomic-embed-text-v1.5": {
                    "provider": "openrouter",
                    "dimensions": 768,
                    "max_tokens": 8192,
                    "cost_per_1k": 0.00002,
                    "description": "High-quality embedding model optimized for text similarity"
                },
                "text-embedding-3-small": {
                    "provider": "openai",
                    "dimensions": 1536,
                    "max_tokens": 8191,
                    "cost_per_1k": 0.00002,
                    "description": "OpenAI's efficient embedding model"
                },
                "text-embedding-3-large": {
                    "provider": "openai",
                    "dimensions": 3072,
                    "max_tokens": 8191,
                    "cost_per_1k": 0.00013,
                    "description": "OpenAI's most capable embedding model"
                },
                "lambda-inference/text-embedding": {
                    "provider": "lambda_inference",
                    "dimensions": 768,
                    "max_tokens": 4096,
                    "cost_per_1k": 0.00001,
                    "description": "Lambda Labs inference API embedding"
                }
            }
        }
    
    def generate_embedding(self, text: str, model_id: str = None) -> Dict:
        """Generate embedding using specified model or default"""
        try:
            # Use default model if none specified
            if not model_id:
                model_id = self.models_config["default"]
            
            # Get model configuration
            model_config = self.models_config["models"].get(model_id)
            if not model_config:
                return {"error": f"Model {model_id} not found in configuration"}
            
            # Route to appropriate provider
            provider = model_config["provider"]
            
            if provider == "openrouter":
                return self._generate_openrouter_embedding(text, model_id, model_config)
            elif provider == "openai":
                return self._generate_openai_embedding(text, model_id, model_config)
            elif provider == "lambda_inference":
                return self._generate_lambda_embedding(text, model_id, model_config)
            else:
                return {"error": f"Provider {provider} not supported"}
                
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return {"error": str(e)}
    
    def _generate_openrouter_embedding(self, text: str, model_id: str, config: Dict) -> Dict:
        """Generate embedding using OpenRouter"""
        if not self.openrouter_api_key:
            return {"error": "OpenRouter API key not configured"}
        
        try:
            headers = {
                "Authorization": f"Bearer {self.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://sophia-intel.ai",
                "X-Title": "SOPHIA Intel Embedding Service"
            }
            
            payload = {
                "model": model_id,
                "input": text
            }
            
            response = requests.post(
                "https://openrouter.ai/api/v1/embeddings",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                embedding = data["data"][0]["embedding"]
                
                return {
                    "embedding": embedding,
                    "model": model_id,
                    "provider": "openrouter",
                    "dimensions": len(embedding),
                    "usage": data.get("usage", {}),
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {"error": f"OpenRouter API error: {response.status_code} - {response.text}"}
                
        except Exception as e:
            return {"error": f"OpenRouter request failed: {str(e)}"}
    
    def _generate_openai_embedding(self, text: str, model_id: str, config: Dict) -> Dict:
        """Generate embedding using OpenAI"""
        if not self.openai_api_key:
            return {"error": "OpenAI API key not configured"}
        
        try:
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model_id,
                "input": text
            }
            
            response = requests.post(
                "https://api.openai.com/v1/embeddings",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                embedding = data["data"][0]["embedding"]
                
                return {
                    "embedding": embedding,
                    "model": model_id,
                    "provider": "openai",
                    "dimensions": len(embedding),
                    "usage": data.get("usage", {}),
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {"error": f"OpenAI API error: {response.status_code} - {response.text}"}
                
        except Exception as e:
            return {"error": f"OpenAI request failed: {str(e)}"}
    
    def _generate_lambda_embedding(self, text: str, model_id: str, config: Dict) -> Dict:
        """Generate embedding using Lambda Inference API"""
        if not self.lambda_cloud_api_key:
            return {"error": "Lambda Cloud API key not configured"}
        
        try:
            # This would be implemented when Lambda Labs provides embedding endpoints
            # For now, fallback to OpenRouter
            logger.warning("Lambda Inference API not yet available, falling back to OpenRouter")
            return self._generate_openrouter_embedding(text, self.models_config["default"], 
                                                     self.models_config["models"][self.models_config["default"]])
                
        except Exception as e:
            return {"error": f"Lambda Inference request failed: {str(e)}"}
    
    def get_available_models(self) -> Dict:
        """Get list of available embedding models"""
        return {
            "default_model": self.models_config["default"],
            "models": self.models_config["models"],
            "providers": {
                "openrouter": {"configured": bool(self.openrouter_api_key)},
                "openai": {"configured": bool(self.openai_api_key)},
                "lambda_inference": {"configured": bool(self.lambda_cloud_api_key)}
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def batch_generate_embeddings(self, texts: List[str], model_id: str = None) -> Dict:
        """Generate embeddings for multiple texts"""
        try:
            results = []
            errors = []
            
            for i, text in enumerate(texts):
                result = self.generate_embedding(text, model_id)
                if "error" in result:
                    errors.append({"index": i, "text": text[:50] + "...", "error": result["error"]})
                else:
                    results.append({"index": i, "embedding": result["embedding"]})
            
            return {
                "results": results,
                "errors": errors,
                "total_processed": len(texts),
                "successful": len(results),
                "failed": len(errors),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"error": str(e)}

# Initialize embedding MCP
embedding_mcp = EmbeddingMCP()

@embedding_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "service": "embedding-mcp",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "architecture": "vendor-independent"
    })

@embedding_bp.route('/models', methods=['GET'])
def get_models():
    """Get available embedding models"""
    return jsonify(embedding_mcp.get_available_models())

@embedding_bp.route('/embed', methods=['POST'])
def generate_embedding():
    """Generate embedding for text"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "Missing 'text' field in request"}), 400
        
        text = data['text']
        model_id = data.get('model_id')
        
        result = embedding_mcp.generate_embedding(text, model_id)
        
        if "error" in result:
            return jsonify(result), 400
        else:
            return jsonify(result)
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@embedding_bp.route('/embed/batch', methods=['POST'])
def batch_generate_embeddings():
    """Generate embeddings for multiple texts"""
    try:
        data = request.get_json()
        if not data or 'texts' not in data:
            return jsonify({"error": "Missing 'texts' field in request"}), 400
        
        texts = data['texts']
        model_id = data.get('model_id')
        
        if not isinstance(texts, list):
            return jsonify({"error": "'texts' must be a list"}), 400
        
        result = embedding_mcp.batch_generate_embeddings(texts, model_id)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@embedding_bp.route('/test', methods=['GET'])
def test_embedding():
    """Test embedding generation with sample text"""
    sample_text = "SOPHIA Intel is an AI-powered command center with vendor-independent architecture."
    result = embedding_mcp.generate_embedding(sample_text)
    
    if "error" in result:
        return jsonify({"test_status": "failed", "error": result["error"]}), 500
    else:
        return jsonify({
            "test_status": "success",
            "sample_text": sample_text,
            "model_used": result["model"],
            "provider": result["provider"],
            "dimensions": result["dimensions"],
            "timestamp": result["timestamp"]
        })

