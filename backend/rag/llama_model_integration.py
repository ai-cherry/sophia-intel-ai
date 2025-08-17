"""
LLAMA Model Integration for SOPHIA Intel
Advanced business intelligence analysis using LLAMA models
"""

import os
import asyncio
import json
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

@dataclass
class LlamaModelConfig:
    """Configuration for LLAMA model integration"""
    api_key: str
    base_url: str = "https://api.llama-api.com/chat/completions"
    model: str = "llama-3.1-70b-versatile"
    temperature: float = 0.1
    max_tokens: int = 2000
    timeout: int = 30

class LlamaModelIntegration:
    """LLAMA model integration for advanced business analysis"""
    
    def __init__(self):
        self.setup_llama_config()
        self.setup_business_prompts()
        self.metrics = {
            "queries_processed": 0,
            "avg_response_time": 0.0,
            "successful_requests": 0,
            "failed_requests": 0
        }
    
    def setup_llama_config(self):
        """Setup LLAMA model configuration"""
        api_key = os.getenv("LLAMA_API_KEY")
        
        if api_key:
            self.config = LlamaModelConfig(api_key=api_key)
            self.available = True
            print("✅ LLAMA model integration configured")
        else:
            self.config = None
            self.available = False
            print("⚠️  LLAMA_API_KEY not found, LLAMA integration disabled")
    
    def setup_business_prompts(self):
        """Setup business intelligence prompt templates"""
        self.prompt_templates = {
            "financial_analysis": """
You are SOPHIA, Pay Ready's AI business intelligence expert specializing in fintech and payment processing.

Analyze the following financial query with deep business context:

Company: Pay Ready (Fintech/Payment Processing)
Query: {query}
Available Data: {data_context}
User Role: {user_role}

Provide a comprehensive financial analysis that includes:
1. Key financial insights and trends
2. Business implications and risks
3. Strategic recommendations
4. Actionable next steps
5. Data quality assessment

Focus on fintech-specific metrics like payment volume, merchant acquisition, churn rates, and regulatory compliance.
""",
            
            "customer_analysis": """
You are SOPHIA, Pay Ready's AI business intelligence expert with deep expertise in customer lifecycle management.

Analyze the following customer-related query:

Company: Pay Ready (Fintech/Payment Processing)
Query: {query}
Available Data: {data_context}
User Role: {user_role}

Provide a detailed customer analysis covering:
1. Customer behavior patterns and insights
2. Acquisition, retention, and churn analysis
3. Segment-specific recommendations
4. Revenue impact assessment
5. Competitive positioning

Consider the unique aspects of fintech customer relationships, including onboarding complexity, compliance requirements, and payment behavior.
""",
            
            "operational_analysis": """
You are SOPHIA, Pay Ready's AI business intelligence expert focused on operational excellence.

Analyze the following operational query:

Company: Pay Ready (Fintech/Payment Processing)
Query: {query}
Available Data: {data_context}
User Role: {user_role}

Provide comprehensive operational insights including:
1. Process efficiency analysis
2. Resource utilization assessment
3. Bottleneck identification
4. Automation opportunities
5. Compliance and risk considerations

Focus on payment processing operations, merchant onboarding, KYC processes, and regulatory compliance workflows.
""",
            
            "strategic_analysis": """
You are SOPHIA, Pay Ready's AI business intelligence expert providing C-level strategic insights.

Analyze the following strategic query:

Company: Pay Ready (Fintech/Payment Processing)
Query: {query}
Available Data: {data_context}
User Role: {user_role}

Provide executive-level strategic analysis covering:
1. Market positioning and competitive landscape
2. Growth opportunities and threats
3. Resource allocation recommendations
4. Long-term strategic implications
5. Key performance indicators to monitor

Consider fintech industry trends, regulatory changes, and competitive dynamics in the payment processing space.
""",
            
            "general_business": """
You are SOPHIA, Pay Ready's AI business intelligence assistant with comprehensive knowledge of fintech operations.

Address the following business query:

Company: Pay Ready (Fintech/Payment Processing)
Query: {query}
Available Data: {data_context}
User Role: {user_role}

Provide a thorough business intelligence response that:
1. Addresses the specific question with relevant data
2. Provides business context and implications
3. Identifies related opportunities or concerns
4. Suggests follow-up analyses or actions
5. Maintains focus on Pay Ready's business objectives

Ensure the response is appropriate for the user's role and demonstrates deep understanding of fintech business operations.
"""
        }
    
    async def process_business_query(
        self,
        query: str,
        context_data: Dict[str, Any],
        user_role: str = "Business User",
        analysis_type: str = "auto"
    ) -> Dict[str, Any]:
        """Process business query using LLAMA model"""
        
        if not self.available:
            return self.create_unavailable_response(query)
        
        start_time = datetime.utcnow()
        
        try:
            # Determine analysis type if auto
            if analysis_type == "auto":
                analysis_type = self.determine_analysis_type(query)
            
            # Select appropriate prompt template
            prompt_template = self.prompt_templates.get(analysis_type, self.prompt_templates["general_business"])
            
            # Create formatted prompt
            formatted_prompt = prompt_template.format(
                query=query,
                data_context=self.format_data_context(context_data),
                user_role=user_role
            )
            
            # Make API request to LLAMA
            response = await self.make_llama_request(formatted_prompt)
            
            # Process response
            response_time = (datetime.utcnow() - start_time).total_seconds()
            self.update_metrics(response_time, success=True)
            
            return {
                "response": response.get("content", ""),
                "system_used": "llama_model",
                "model": self.config.model,
                "analysis_type": analysis_type,
                "confidence_score": self.calculate_confidence_score(response, context_data),
                "response_time": response_time,
                "token_usage": response.get("usage", {}),
                "business_context_applied": True,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            response_time = (datetime.utcnow() - start_time).total_seconds()
            self.update_metrics(response_time, success=False)
            
            print(f"❌ LLAMA processing error: {e}")
            return self.create_error_response(query, str(e))
    
    def determine_analysis_type(self, query: str) -> str:
        """Determine the type of analysis based on query content"""
        query_lower = query.lower()
        
        # Financial analysis keywords
        if any(term in query_lower for term in [
            "revenue", "profit", "cost", "margin", "financial", "budget", 
            "pricing", "payment volume", "transaction", "fees"
        ]):
            return "financial_analysis"
        
        # Customer analysis keywords
        if any(term in query_lower for term in [
            "customer", "client", "merchant", "user", "churn", "retention",
            "acquisition", "onboarding", "satisfaction", "segment"
        ]):
            return "customer_analysis"
        
        # Operational analysis keywords
        if any(term in query_lower for term in [
            "process", "operation", "workflow", "efficiency", "automation",
            "compliance", "kyc", "risk", "fraud", "processing time"
        ]):
            return "operational_analysis"
        
        # Strategic analysis keywords
        if any(term in query_lower for term in [
            "strategy", "market", "competition", "growth", "expansion",
            "partnership", "investment", "roadmap", "vision", "goals"
        ]):
            return "strategic_analysis"
        
        return "general_business"
    
    def format_data_context(self, context_data: Dict[str, Any]) -> str:
        """Format data context for LLAMA prompt"""
        context_parts = []
        
        # Format entities
        if context_data.get("entities"):
            entities_info = []
            for entity in context_data["entities"][:10]:  # Limit to top 10
                entities_info.append(
                    f"- {entity['name']} ({entity['type']}): {entity.get('description', 'No description')}"
                )
            context_parts.append("Business Entities:\n" + "\n".join(entities_info))
        
        # Format data sources
        if context_data.get("data_source_coverage"):
            context_parts.append(f"Data Sources: {', '.join(context_data['data_source_coverage'])}")
        
        # Format business insights
        if context_data.get("business_insights"):
            insights_info = []
            for insight in context_data["business_insights"]:
                insights_info.append(f"- {insight.get('insight', '')}")
            context_parts.append("Business Insights:\n" + "\n".join(insights_info))
        
        # Format relationships
        if context_data.get("relationships"):
            context_parts.append(f"Business Relationships: {len(context_data['relationships'])} identified")
        
        return "\n\n".join(context_parts) if context_parts else "Limited data context available"
    
    async def make_llama_request(self, prompt: str) -> Dict[str, Any]:
        """Make API request to LLAMA model"""
        
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.config.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "stream": False
        }
        
        try:
            # Make async request
            response = await asyncio.to_thread(
                requests.post,
                self.config.base_url,
                headers=headers,
                json=payload,
                timeout=self.config.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Extract content from response
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                return {
                    "content": content,
                    "usage": result.get("usage", {}),
                    "model": result.get("model", self.config.model)
                }
            else:
                raise ValueError("Invalid response format from LLAMA API")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"LLAMA API request failed: {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response from LLAMA API: {e}")
        except Exception as e:
            raise Exception(f"LLAMA API error: {e}")
    
    def calculate_confidence_score(
        self,
        response: Dict[str, Any],
        context_data: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for LLAMA response"""
        
        score = 0.7  # Base score for LLAMA model
        
        # Increase score based on available context
        if context_data.get("entities"):
            score += min(0.15, len(context_data["entities"]) * 0.02)
        
        if context_data.get("business_insights"):
            score += min(0.1, len(context_data["business_insights"]) * 0.03)
        
        # Increase score based on response quality
        content = response.get("content", "")
        if len(content) > 500:
            score += 0.05
        
        if any(term in content.lower() for term in ["pay ready", "fintech", "payment", "business"]):
            score += 0.05
        
        # Check for structured response
        if any(marker in content for marker in ["1.", "2.", "3.", "•", "-"]):
            score += 0.03
        
        return min(0.95, score)
    
    def create_unavailable_response(self, query: str) -> Dict[str, Any]:
        """Create response when LLAMA is unavailable"""
        return {
            "response": f"I understand you're asking about: '{query}'. However, the LLAMA model integration is currently unavailable. Please ensure the LLAMA_API_KEY is properly configured for enhanced business intelligence analysis.",
            "system_used": "llama_unavailable",
            "model": "unavailable",
            "analysis_type": "unavailable",
            "confidence_score": 0.0,
            "error": "LLAMA model not available",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def create_error_response(self, query: str, error_message: str) -> Dict[str, Any]:
        """Create response when LLAMA processing fails"""
        return {
            "response": f"I encountered an error while processing your query: '{query}'. The LLAMA model analysis is temporarily unavailable. Error: {error_message}",
            "system_used": "llama_error",
            "model": self.config.model if self.config else "unknown",
            "analysis_type": "error",
            "confidence_score": 0.0,
            "error": error_message,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def update_metrics(self, response_time: float, success: bool):
        """Update processing metrics"""
        self.metrics["queries_processed"] += 1
        
        if success:
            self.metrics["successful_requests"] += 1
        else:
            self.metrics["failed_requests"] += 1
        
        # Update average response time
        current_avg = self.metrics["avg_response_time"]
        total_queries = self.metrics["queries_processed"]
        self.metrics["avg_response_time"] = (
            current_avg * (total_queries - 1) + response_time
        ) / total_queries
    
    async def analyze_business_trends(
        self,
        data_points: List[Dict[str, Any]],
        analysis_focus: str = "general"
    ) -> Dict[str, Any]:
        """Analyze business trends using LLAMA model"""
        
        if not self.available:
            return self.create_unavailable_response("business trends analysis")
        
        try:
            # Format data points for analysis
            data_summary = self.format_trend_data(data_points)
            
            trend_prompt = f"""
You are SOPHIA, Pay Ready's AI business intelligence expert specializing in trend analysis.

Analyze the following business data trends for Pay Ready (Fintech/Payment Processing):

Data Points: {data_summary}
Analysis Focus: {analysis_focus}

Provide a comprehensive trend analysis including:
1. Key patterns and trends identified
2. Statistical significance of changes
3. Business implications and drivers
4. Predictive insights for next quarter
5. Recommended actions based on trends
6. Risk factors and opportunities

Focus on fintech-specific trends like payment volume growth, merchant acquisition rates, customer behavior shifts, and market dynamics.
"""
            
            response = await self.make_llama_request(trend_prompt)
            
            return {
                "trend_analysis": response.get("content", ""),
                "system_used": "llama_trend_analysis",
                "data_points_analyzed": len(data_points),
                "analysis_focus": analysis_focus,
                "confidence_score": self.calculate_confidence_score(response, {"entities": data_points}),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Trend analysis error: {e}")
            return self.create_error_response("business trends analysis", str(e))
    
    def format_trend_data(self, data_points: List[Dict[str, Any]]) -> str:
        """Format data points for trend analysis"""
        if not data_points:
            return "No data points available for analysis"
        
        formatted_points = []
        for point in data_points[:20]:  # Limit to 20 points
            formatted_points.append(
                f"- {point.get('name', 'Unknown')}: {point.get('value', 'N/A')} "
                f"({point.get('period', 'Unknown period')})"
            )
        
        return "\n".join(formatted_points)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get LLAMA integration status"""
        return {
            "system_name": "LLAMA Model Integration",
            "available": self.available,
            "model": self.config.model if self.config else "unavailable",
            "api_configured": bool(self.config),
            "metrics": self.metrics,
            "prompt_templates": list(self.prompt_templates.keys()),
            "timestamp": datetime.utcnow().isoformat()
        }

# Global instance
_llama_integration_instance = None

def get_llama_integration() -> LlamaModelIntegration:
    """Get global LLAMA integration instance"""
    global _llama_integration_instance
    if _llama_integration_instance is None:
        _llama_integration_instance = LlamaModelIntegration()
    return _llama_integration_instance

