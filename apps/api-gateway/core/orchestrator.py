"""Core orchestrator - Routes requests to appropriate services"""
import uuid
import logging
from typing import Dict, Any
from core.adapters.mcp_code import CodeAdapter
from core.adapters.memory import MemoryAdapter
from core.adapters.research import ResearchAdapter
from core.env_schema import validate_environment

logger = logging.getLogger(__name__)
config = validate_environment()

class Orchestrator:
    """Central orchestrator for all AI requests"""
    
    def __init__(self):
        self.code_adapter = CodeAdapter()
        self.memory_adapter = MemoryAdapter()
        self.research_adapter = ResearchAdapter()
    
    async def handle_request(self, request_type: str, payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Route request to appropriate handler"""
        request_id = str(uuid.uuid4())
        
        logger.info(f"Handling {request_type} request {request_id}")
        
        try:
            if request_type == "chat":
                return await self._handle_chat(payload, context, request_id)
            elif request_type == "code":
                return await self.code_adapter.handle_request(payload, context, request_id)
            elif request_type == "memory":
                return await self.memory_adapter.handle_request(payload, context, request_id)
            elif request_type == "research":
                return await self.research_adapter.handle_request(payload, context, request_id)
            else:
                raise ValueError(f"Unknown request type: {request_type}")
                
        except Exception as e:
            logger.error(f"Request {request_id} failed: {e}")
            return {
                "request_id": request_id,
                "error": str(e),
                "status": "failed"
            }
    
    async def _handle_chat(self, payload: Dict[str, Any], context: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """Handle chat requests"""
        message = payload.get("message", "")
        
        # For now, return mock response
        # TODO: Integrate with OpenRouter and current models
        return {
            "request_id": request_id,
            "response": f"SOPHIA: I received your message '{message}'. This is a mock response from the orchestrator.",
            "model_used": "openai/gpt-oss-20b",
            "cost_estimate": 0.0,
            "status": "success"
        }

# Global orchestrator instance
orchestrator = Orchestrator()
