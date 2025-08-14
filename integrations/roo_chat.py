"""
Roo Chat Integration for Swarm
Provides a simple interface to integrate Swarm with Roo or other chat systems
"""

from typing import Dict, Any, Optional
from swarm.chat_interface import chat_with_swarm


def process_roo_message(message: str) -> Dict[str, Any]:
    """
    Process a message from Roo and return a response from the Swarm system

    Args:
        message: The message from Roo

    Returns:
        A formatted response suitable for returning to Roo
    """
    # Process the message with the Swarm chat interface
    response = chat_with_swarm(message)

    # Return the response in a format suitable for Roo
    return {
        "response": response["text"],
        "metadata": {
            "swarm_summary": response["swarm_summary"],
            "success": response["success"]
        }
    }


def reset_conversation() -> Dict[str, Any]:
    """Reset the Swarm conversation history"""
    from swarm.chat_interface import swarm_chat
    swarm_chat.reset_conversation()
    return {
        "status": "success",
        "message": "Conversation history has been reset"
    }
