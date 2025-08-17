"""
Streaming chat handler for real-time responses
"""

import asyncio
import json
from typing import AsyncGenerator, Dict, Any, Optional
from datetime import datetime

from backend.config.settings import Settings


class StreamingChatHandler:
    """Handles streaming chat responses"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
    
    async def stream_response(
        self, 
        response_generator: AsyncGenerator[str, None],
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat response with metadata"""
        try:
            chunk_count = 0
            total_content = ""
            
            async for chunk in response_generator:
                chunk_count += 1
                total_content += chunk
                
                yield {
                    "type": "chunk",
                    "content": chunk,
                    "session_id": session_id,
                    "chunk_number": chunk_count,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Small delay to prevent overwhelming the client
                await asyncio.sleep(0.01)
            
            # Send completion message
            yield {
                "type": "complete",
                "session_id": session_id,
                "total_chunks": chunk_count,
                "total_length": len(total_content),
                "metadata": metadata or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            yield {
                "type": "error",
                "error": str(e),
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def format_sse_message(self, data: Dict[str, Any]) -> str:
        """Format message for Server-Sent Events"""
        try:
            json_data = json.dumps(data)
            return f"data: {json_data}\n\n"
        except Exception:
            error_data = {
                "type": "error",
                "error": "Failed to format message",
                "timestamp": datetime.utcnow().isoformat()
            }
            return f"data: {json.dumps(error_data)}\n\n"
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for streaming handler"""
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        }

