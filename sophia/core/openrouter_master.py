"""
SOPHIA OpenRouter Master - Multi-Model Intelligence Orchestration
Implements dynamic model selection and cost optimization
"""
import os
import httpx
import json
from typing import Dict, Any, Optional
from datetime import datetime

class OpenRouterMaster:
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.base_url = "https://openrouter.ai/api/v1"
        self.model_costs = {
            # Premium Tier - High-value tasks
            "anthropic/claude-3.5-sonnet": {"input": 0.003, "output": 0.015, "tier": "premium"},
            "openai/gpt-4-turbo": {"input": 0.01, "output": 0.03, "tier": "premium"},
            "openai/gpt-4o": {"input": 0.005, "output": 0.015, "tier": "premium"},
            
            # Balanced Tier - General business intelligence
            "anthropic/claude-3-opus": {"input": 0.015, "output": 0.075, "tier": "balanced"},
            "openai/gpt-4": {"input": 0.03, "output": 0.06, "tier": "balanced"},
            "google/gemini-pro": {"input": 0.0005, "output": 0.0015, "tier": "balanced"},
            
            # Efficient Tier - High-volume tasks
            "anthropic/claude-3-haiku": {"input": 0.00025, "output": 0.00125, "tier": "efficient"},
            "openai/gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015, "tier": "efficient"},
            "meta-llama/llama-2-70b-chat": {"input": 0.0007, "output": 0.0009, "tier": "efficient"}
        }
    
    def select_optimal_model(self, task_type: str, complexity: str = "medium", budget_tier: str = "balanced") -> str:
        """Select the optimal model based on task requirements"""
        
        # Task-specific model selection
        if task_type == "research_synthesis" and complexity == "high":
            return "anthropic/claude-3.5-sonnet"
        elif task_type == "code_generation" and budget_tier == "premium":
            return "openai/gpt-4-turbo"
        elif task_type == "quick_analysis" and budget_tier == "standard":
            return "anthropic/claude-3-haiku"
        elif task_type == "creative_content":
            return "openai/gpt-4o"
        elif task_type == "market_intelligence":
            return "anthropic/claude-3.5-sonnet"
        elif task_type == "sales_analysis":
            return "openai/gpt-4-turbo"
        elif task_type == "operational_insights":
            return "anthropic/claude-3-opus"
        else:
            # Default balanced option
            return "anthropic/claude-3-opus"
    
    async def generate_response(self, prompt: str, task_type: str = "general", 
                              complexity: str = "medium", budget_tier: str = "balanced") -> Dict[str, Any]:
        """Generate response using optimal model selection"""
        
        model = self.select_optimal_model(task_type, complexity, budget_tier)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "max_tokens": 2000
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "content": result["choices"][0]["message"]["content"],
                        "model_used": model,
                        "cost_tier": self.model_costs[model]["tier"],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"API error: {response.status_code}",
                        "model_attempted": model
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model_attempted": model
            }
    
    def get_model_recommendations(self, business_scenario: str) -> Dict[str, str]:
        """Get model recommendations for specific business scenarios"""
        
        scenarios = {
            "quarterly_review": {
                "primary": "anthropic/claude-3.5-sonnet",
                "reasoning": "Superior at synthesizing multiple data sources into coherent business narrative"
            },
            "market_research": {
                "primary": "openai/gpt-4-turbo", 
                "reasoning": "Excellent at processing complex market data and strategic implications"
            },
            "crisis_management": {
                "primary": "anthropic/claude-3.5-sonnet",
                "reasoning": "Best deep reasoning for critical business decisions"
            },
            "daily_summary": {
                "primary": "anthropic/claude-3-haiku",
                "reasoning": "Fast and cost-effective for routine analysis"
            },
            "client_communication": {
                "primary": "openai/gpt-4o",
                "reasoning": "Superior creative and communication capabilities"
            }
        }
        
        return scenarios.get(business_scenario, {
            "primary": "anthropic/claude-3-opus",
            "reasoning": "Balanced performance for general business intelligence"
        })

# Global instance for SOPHIA system
openrouter_master = OpenRouterMaster()
