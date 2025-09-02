import logging
from abc import ABC, abstractmethod
from typing import Any
from uuid import uuid4

from app.swarms.communication.message_bus import MessageBus, MessageType, SwarmMessage

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for all swarm agents"""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id

    @abstractmethod
    async def execute(self, problem: dict[str, Any]) -> dict[str, Any]:
        """Execute the agent's task on a problem"""
        pass

class CommunicativeAgent(BaseAgent):
    """Agent that supports inter-agent communication through the message bus"""

    def __init__(self, agent_id: str, bus: MessageBus):
        super().__init__(agent_id)
        self.bus = bus

    async def send_query(self, target_agent_id: str, query: str) -> str:
        """Send a query to another agent and wait for a response"""
        # Generate a thread ID for the query response
        thread_id = f"query:{self.agent_id}:{target_agent_id}:{uuid4().hex}"

        # Create a query message
        message = SwarmMessage(
            sender_agent_id=self.agent_id,
            receiver_agent_id=target_agent_id,
            message_type=MessageType.QUERY,
            content={"query": query, "thread_id": thread_id},
            priority=7
        )

        # Publish the message
        await self.bus.publish(message)

        # Wait for a response on this thread
        async for response in self.bus.subscribe(
            self.agent_id,
            [MessageType.RESPONSE]
        ):
            if response.thread_id == thread_id:
                return response.content.get("response", "No response")

        return "No response received"

    async def broadcast_proposal(self, proposal: dict[str, Any]) -> list[dict]:
        """Broadcast a proposal to all agents and collect responses"""
        # We'll create a thread for the broadcast
        thread_id = f"proposal:{self.agent_id}:{proposal.get('id', 'unknown')}"

        # Create and publish the proposal message
        message = SwarmMessage(
            sender_agent_id=self.agent_id,
            receiver_agent_id=None,  # Broadcast
            message_type=MessageType.PROPOSAL,
            content={"proposal": proposal, "thread_id": thread_id},
            priority=5
        )
        await self.bus.publish(message)

        # Collect responses from the bus
        responses = []
        async for response in self.bus.subscribe(
            self.agent_id,
            [MessageType.RESPONSE]
        ):
            if response.thread_id == thread_id:
                responses.append(response.content)

        return responses

    async def vote_on_proposal(self, proposal_id: str, vote: str) -> None:
        """Vote on a proposal (which must be on a thread)"""
        # Create a vote message
        message = SwarmMessage(
            sender_agent_id=self.agent_id,
            receiver_agent_id=None,  # Broadcast vote to proposal thread
            message_type=MessageType.VOTE,
            content={"proposal_id": proposal_id, "vote": vote},
            priority=6
        )
        await self.bus.publish(message)

    async def request_expertise(self, domain: str, question: str) -> str:
        """Request expertise from a domain expert agent"""
        # In reality, we'd use the registry to find an expert agent
        # For now, we'll use a fixed pattern for expert agents
        expert_agent_id = f"expert_agent_{domain.replace(' ', '_').lower()}"
        return await self.send_query(expert_agent_id, f"Expertise question: {domain} - {question}")

    # Message handlers - to be implemented by subclasses
    async def on_query_received(self, message: SwarmMessage) -> dict:
        """Handle a query message"""
        return {"response": "Query handled", "context": message.content}

    async def on_proposal_received(self, message: SwarmMessage) -> dict:
        """Handle a proposal message"""
        return {"response": "Proposal handled", "context": message.content}

    async def on_vote_request(self, message: SwarmMessage) -> dict:
        """Handle a vote request (e.g., for a proposal)"""
        return {"response": "Vote handled", "context": message.content}

# Example usage
if __name__ == "__main__":
    async def demo():
        # Initialize message bus and agent
        bus = MessageBus()
        await bus.initialize()
        agent = CommunicativeAgent("agent_1", bus)

        # Test query
        response = await agent.send_query("agent_2", "What is 2+2?")
        print(f"Query result: {response}")

        # Test proposal broadcast
        proposal = {"title": "Test Proposal", "content": "Testing message bus"}
        responses = await agent.broadcast_proposal(proposal)
        print(f"Proposal responses: {responses}")

        await bus.close()

    import asyncio
    asyncio.run(demo())
