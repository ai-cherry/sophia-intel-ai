"""
Chat Interface for Sophia Swarm System
Provides a direct integration between chat systems and the Swarm
"""
import os
import time
import json
from typing import Dict, Any, Optional, List, Union
from loguru import logger

# Import Swarm components
from swarm.graph import run as run_swarm
from swarm.nl_interface import process_natural_language


class SwarmChatInterface:
    """
    Chat interface for the Swarm system that allows for direct integration
    with chat services like Roo or other conversational agents.
    """

    def __init__(self):
        """Initialize the Swarm Chat Interface"""
        self.history = []
        self.active_session = False
        self.session_start_time = None

    def handle_message(
        self,
        message: str,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a chat message and generate a response using the Swarm system.

        Args:
            message: The chat message to process
            user_id: Optional user identifier for tracking conversations
            context: Optional context information

        Returns:
            The formatted response from the Swarm system
        """
        # Track session information
        if not self.active_session:
            self.active_session = True
            self.session_start_time = time.time()

        # Add message to history
        self.history.append({
            "role": "user",
            "content": message,
            "timestamp": time.time(),
            "user_id": user_id
        })

        # Process the message with the Swarm system
        try:
            swarm_results = process_natural_language(message)

            # Format the response
            response = self._format_response(message, swarm_results, context)

            # Add response to history
            self.history.append({
                "role": "assistant",
                "content": response["text"],
                "timestamp": time.time(),
                "swarm_results": swarm_results
            })

            return response

        except Exception as e:
            logger.error(f"Error processing message with Swarm: {e}")
            error_response = {
                "text": f"I encountered an error while processing your request: {str(e)}",
                "success": False,
                "error": str(e)
            }

            # Add error response to history
            self.history.append({
                "role": "assistant",
                "content": error_response["text"],
                "timestamp": time.time(),
                "error": str(e)
            })

            return error_response

    def _format_response(
        self,
        message: str,
        swarm_results: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Format the Swarm results into a chat-friendly response"""
        # Extract outputs from each agent
        architect_output = swarm_results.get("architect", "")
        builder_output = swarm_results.get("builder", "")
        tester_output = swarm_results.get("tester", "")
        operator_output = swarm_results.get("operator", "")

        # Determine which agents were active
        active_agents = []
        if architect_output:
            active_agents.append("architect")
        if builder_output:
            active_agents.append("builder")
        if tester_output:
            active_agents.append("tester")
        if operator_output:
            active_agents.append("operator")

        # Create response text
        if not active_agents:
            response_text = "I processed your request but none of the Swarm agents were activated."
        else:
            response_text = f"I processed your request with the Swarm system using {len(active_agents)} agents: {', '.join(active_agents)}.\n\n"

            # Include summaries based on active agents
            if "architect" in active_agents:
                arch_summary = architect_output[:200] + "..." if len(
                    architect_output) > 200 else architect_output
                response_text += f"**Architecture Analysis:**\n{arch_summary}\n\n"

            if "builder" in active_agents:
                build_summary = builder_output[:200] + "..." if len(
                    builder_output) > 200 else builder_output
                response_text += f"**Implementation:**\n{build_summary}\n\n"

            if "tester" in active_agents:
                test_summary = tester_output[:200] + \
                    "..." if len(tester_output) > 200 else tester_output
                response_text += f"**Testing Results:**\n{test_summary}\n\n"

            if "operator" in active_agents:
                op_summary = operator_output[:200] + "..." if len(
                    operator_output) > 200 else operator_output
                response_text += f"**Operational Notes:**\n{op_summary}\n\n"

        # Create structured response
        response = {
            "text": response_text,
            "success": True,
            "swarm_summary": {
                "active_agents": active_agents,
                "architect_length": len(architect_output),
                "builder_length": len(builder_output),
                "tester_length": len(tester_output),
                "operator_length": len(operator_output)
            },
            "full_results": swarm_results
        }

        return response

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the conversation history"""
        return self.history

    def reset_conversation(self) -> None:
        """Reset the conversation history"""
        self.history = []
        self.active_session = False
        self.session_start_time = None


# Create a global instance for easy import
swarm_chat = SwarmChatInterface()

# Convenience function for direct integration


def chat_with_swarm(
    message: str,
    user_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convenience function to chat directly with the Swarm system

    Args:
        message: The chat message to process
        user_id: Optional user identifier
        context: Optional context information

    Returns:
        The formatted response from the Swarm system
    """
    global swarm_chat
    return swarm_chat.handle_message(message, user_id, context)
