"""
Chat Domain - Unified chat functionality with intelligent routing
Consolidates chat_proxy, chat_router, and unified_chat_service
"""

from .service import ChatService
from .router import ChatRouter
from .models import ChatRequest, ChatResponse, ChatMessage
from .streaming import StreamingChatHandler

__all__ = [
    "ChatService",
    "ChatRouter", 
    "ChatRequest",
    "ChatResponse",
    "ChatMessage",
    "StreamingChatHandler"
]

