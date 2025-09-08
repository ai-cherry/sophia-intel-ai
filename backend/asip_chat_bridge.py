"""
ASIP Chat Bridge - Natural Language Interface for Sophia AI
Bridges Open WebUI and other chat interfaces with the ASIP Orchestrator
"""

import hashlib
import json

# Import existing ASIP components
import sys
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from collections.abc import AsyncGenerator

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.append("/workspace")
from asip.orchestrator import UltimateAdaptiveOrchestrator


class ChatRequest(BaseModel):
    """Chat request model"""

    message: str
    context: Dict[str, Any] = {}
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model"""

    response: str
    metadata: Dict[str, Any] = {}
    execution_mode: Optional[str] = None
    gpu_instance: Optional[str] = None
    processing_time: Optional[float] = None


class IntentType(Enum):
    """Intent types for routing"""

    CODE_GENERATION = "code_generation"
    ANALYSIS = "analysis"
    RESEARCH = "research"
    BUSINESS = "business"
    GENERAL = "general"
    SYSTEM = "system"


class NaturalLanguageProcessor:
    """Process natural language and extract intents"""

    def __init__(self):
        self.intent_patterns = {
            IntentType.CODE_GENERATION: [
                "write",
                "create",
                "generate",
                "build",
                "code",
                "implement",
                "develop",
            ],
            IntentType.ANALYSIS: [
                "analyze",
                "review",
                "check",
                "audit",
                "examine",
                "inspect",
                "evaluate",
            ],
            IntentType.RESEARCH: [
                "research",
                "find",
                "search",
                "lookup",
                "investigate",
                "explore",
                "discover",
            ],
            IntentType.BUSINESS: [
                "revenue",
                "sales",
                "metrics",
                "kpi",
                "profit",
                "customer",
                "market",
            ],
            IntentType.SYSTEM: ["status", "health", "performance", "monitor", "debug", "log"],
            IntentType.GENERAL: ["help", "what", "how", "why", "when", "who", "tell"],
        }

    async def extract_intent(self, message: str) -> Dict[str, Any]:
        """Extract intent from natural language message"""
        message_lower = message.lower()

        # Score each intent type
        intent_scores = {}
        for intent_type, keywords in self.intent_patterns.items():
            score = sum(1 for keyword in keywords if keyword in message_lower)
            if score > 0:
                intent_scores[intent_type] = score

        # Get primary intent
        primary_intent = (
            max(intent_scores, key=intent_scores.get) if intent_scores else IntentType.GENERAL
        )

        return {
            "primary_intent": primary_intent.value,
            "intent_scores": {k.value: v for k, v in intent_scores.items()},
            "original_message": message,
            "timestamp": datetime.now().isoformat(),
        }


class ContextManager:
    """Manage conversation context and memory"""

    def __init__(self):
        self.conversation_history = {}
        self.user_profiles = {}
        self.session_contexts = {}

    async def enrich(self, intent: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich intent with contextual information"""
        enriched = {**intent, **context, "enrichment_timestamp": datetime.now().isoformat()}

        # Add session context if available
        session_id = context.get("session_id")
        if session_id and session_id in self.session_contexts:
            enriched["session_context"] = self.session_contexts[session_id]

        # Add user profile if available
        user_id = context.get("user_id")
        if user_id and user_id in self.user_profiles:
            enriched["user_profile"] = self.user_profiles[user_id]

        # Add conversation history summary
        if session_id and session_id in self.conversation_history:
            history = self.conversation_history[session_id]
            enriched["conversation_summary"] = {
                "message_count": len(history),
                "last_messages": history[-3:] if len(history) >= 3 else history,
            }

        return enriched

    async def update_history(self, session_id: str, message: str, response: str):
        """Update conversation history"""
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []

        self.conversation_history[session_id].append(
            {"message": message, "response": response, "timestamp": datetime.now().isoformat()}
        )

        # Keep only last 20 messages per session
        if len(self.conversation_history[session_id]) > 20:
            self.conversation_history[session_id] = self.conversation_history[session_id][-20:]


class ResponseFormatter:
    """Format responses for different chat interfaces"""

    def format_for_chat(self, response: Dict[str, Any]) -> str:
        """Format response for chat interface"""
        if isinstance(response, str):
            return response

        # Extract main content
        content = response.get("content", response.get("response", ""))

        # Add metadata if available
        if "metadata" in response:
            metadata = response["metadata"]
            if metadata.get("sources"):
                content += "\n\n**Sources:**\n"
                for source in metadata["sources"]:
                    content += f"- {source}\n"

        return content

    def format_for_streaming(self, chunk: str) -> str:
        """Format chunk for streaming response"""
        return json.dumps({"chunk": chunk, "timestamp": datetime.now().isoformat()})


class GPUAwareRouter:
    """Route requests to appropriate Lambda Labs GPU instances"""

    def __init__(self):
        self.gpu_instances = {
            "inference": {"ip": "192.222.58.232", "name": "GH200", "memory": "141GB"},
            "ml_pipeline": {"ip": "104.171.202.134", "name": "A100", "memory": "80GB"},
            "api_services": {"ip": "104.171.202.103", "name": "RTX6000", "memory": "24GB"},
            "mcp_hub": {"ip": "104.171.202.117", "name": "A6000", "memory": "48GB"},
            "development": {"ip": "155.248.194.183", "name": "A10", "memory": "24GB"},
        }
        self.current_loads = {key: 0 for key in self.gpu_instances}

    async def route_to_gpu(self, task_type: str, complexity: float) -> Dict[str, str]:
        """Route task to appropriate GPU based on type and complexity"""
        if complexity > 0.7:
            # High complexity - use most powerful GPU
            selected = "inference"
        elif task_type in ["ml_training", "batch_processing"]:
            selected = "ml_pipeline"
        elif task_type in ["api_request", "web_service"]:
            selected = "api_services"
        elif task_type in ["mcp_operation", "agent_coordination"]:
            selected = "mcp_hub"
        else:
            selected = "development"

        # Update load tracking
        self.current_loads[selected] += 1

        return {"instance": selected, **self.gpu_instances[selected]}

    async def get_best_gpu(self) -> str:
        """Get GPU with lowest current load"""
        return min(self.current_loads, key=self.current_loads.get)


class ASIPChatBridge:
    """
    Main bridge between natural language chat interfaces and ASIP orchestrator
    """

    def __init__(self):
        self.orchestrator = UltimateAdaptiveOrchestrator()
        self.nlp_processor = NaturalLanguageProcessor()
        self.context_manager = ContextManager()
        self.response_formatter = ResponseFormatter()
        self.gpu_router = GPUAwareRouter()
        self.cache = {}

    async def process_chat_message(
        self, message: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Process natural language message through ASIP system
        """
        start_time = datetime.now()
        context = context or {}

        # Check cache
        cache_key = hashlib.md5(
            f"{message}{json.dumps(context, sort_keys=True)}".encode()
        ).hexdigest()
        if cache_key in self.cache:
            cached_response = self.cache[cache_key]
            cached_response["from_cache"] = True
            return cached_response

        # 1. Process natural language
        intent = await self.nlp_processor.extract_intent(message)

        # 2. Enrich with context
        enriched_context = await self.context_manager.enrich(intent, context)

        # 3. Prepare task for orchestrator
        task = {
            "id": f"chat_{datetime.now().timestamp()}",
            "type": intent["primary_intent"],
            "content": message,
            "context": enriched_context,
            "priority": context.get("priority", "normal"),
        }

        # 4. Process through orchestrator
        result = await self.orchestrator.process_task(task)

        # 5. Get execution details
        execution_mode = result.get("execution_mode", "unknown")
        complexity = result.get("complexity_score", 0)

        # 6. Route to GPU if needed
        gpu_info = await self.gpu_router.route_to_gpu(intent["primary_intent"], complexity)

        # 7. Format response
        formatted_response = self.response_formatter.format_for_chat(result)

        # 8. Update conversation history
        session_id = context.get("session_id")
        if session_id:
            await self.context_manager.update_history(session_id, message, formatted_response)

        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()

        response = {
            "response": formatted_response,
            "metadata": {
                "execution_mode": execution_mode,
                "complexity_score": complexity,
                "gpu_instance": gpu_info["name"],
                "gpu_ip": gpu_info["ip"],
                "processing_time": processing_time,
                "intent": intent["primary_intent"],
                "timestamp": datetime.now().isoformat(),
            },
        }

        # Cache the response
        self.cache[cache_key] = response

        # Limit cache size
        if len(self.cache) > 1000:
            # Remove oldest entries
            oldest_keys = list(self.cache.keys())[:100]
            for key in oldest_keys:
                del self.cache[key]

        return response

    async def process_streaming(
        self, message: str, context: Dict[str, Any] = None
    ) -> AsyncGenerator[str, None]:
        """
        Process message with streaming response
        """
        # For now, return the full response as a single chunk
        # In production, this would stream tokens as they're generated
        result = await self.process_chat_message(message, context)
        yield self.response_formatter.format_for_streaming(result["response"])


# FastAPI Application
app = FastAPI(title="ASIP Chat Bridge API", version="1.0.0")

# CORS middleware for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize bridge
bridge = ASIPChatBridge()


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ASIP Chat Bridge",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    """Main chat endpoint"""
    try:
        result = await bridge.process_chat_message(
            request.message,
            {**request.context, "user_id": request.user_id, "session_id": request.session_id},
        )

        return ChatResponse(
            response=result["response"],
            metadata=result["metadata"],
            execution_mode=result["metadata"].get("execution_mode"),
            gpu_instance=result["metadata"].get("gpu_instance"),
            processing_time=result["metadata"].get("processing_time"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/openai")
async def openai_compatible_chat(request: Dict[str, Any]):
    """OpenAI API compatible endpoint for Open WebUI"""
    try:
        # Extract message from OpenAI format
        messages = request.get("messages", [])
        if not messages:
            raise ValueError("No messages provided")

        last_message = messages[-1]
        user_message = last_message.get("content", "")

        # Process through bridge
        result = await bridge.process_chat_message(user_message)

        # Format as OpenAI response
        return {
            "id": f"chatcmpl-{datetime.now().timestamp()}",
            "object": "chat.completion",
            "created": int(datetime.now().timestamp()),
            "model": "sophia-asip",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": result["response"]},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": len(user_message.split()),
                "completion_tokens": len(result["response"].split()),
                "total_tokens": len(user_message.split()) + len(result["response"].split()),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for streaming chat"""
    await websocket.accept()

    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            message = data.get("message", "")
            context = data.get("context", {})

            # Stream response
            async for chunk in bridge.process_streaming(message, context):
                await websocket.send_text(chunk)

            # Send completion signal
            await websocket.send_json({"type": "complete"})

    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
    finally:
        await websocket.close()


@app.get("/metrics")
async def get_metrics():
    """Get chat bridge metrics"""
    return {
        "cache_size": len(bridge.cache),
        "gpu_loads": bridge.gpu_router.current_loads,
        "active_sessions": len(bridge.context_manager.conversation_history),
        "timestamp": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="${BIND_IP}", port=8100)
