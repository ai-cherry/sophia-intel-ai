from typing import Dict, List, Optional, Any
import asyncio
import logging
from app.llm.real_executor import RealExecutor
from app.memory.unified_memory import store_memory, search_memory
from app.swarms.communication.message_bus import MessageBus, MessageType, SwarmMessage
from app.swarms.core.swarm_base import SwarmBase
from app.agents.simple_orchestrator import SimpleAgentOrchestrator

logger = logging.getLogger(__name__)

class CodeReviewEngine:
    """Backend analysis engine for AI-powered code review system"""
    
    def __init__(
        self,
        message_bus: MessageBus,
        executor: RealExecutor,
        swarm: SwarmBase
    ):
        self.message_bus = message_bus
        self.executor = executor
        self.swarm = swarm
        self.last_analysis_id = 0
    
    async def analyze_code(self, code: str, file_path: str = "unknown") -> Dict[str, Any]:
        """Analyze code using LLM and store results in memory"""
        self.last_analysis_id += 1
        analysis_id = f"analysis:{self.last_analysis_id}"
        
        # Step 1: Get LLM analysis
        analysis_response = await self.executor.execute_analysis(
            code=code,
            context={
                "file_path": file_path,
                "analysis_id": analysis_id
            }
        )
        
        # Step 2: Store in memory
        await store_memory(
            content=analysis_response["result"],
            metadata={
                "analysis_id": analysis_id,
                "file_path": file_path,
                "analysis_type": "code_review",
                "timestamp": asyncio.get_event_loop().time()
            }
        )
        
        # Step 3: Notify swarm about new analysis
        await self._notify_analytic_swarm(analysis_id, analysis_response)
        
        # Return detailed results
        return {
            "analysis_id": analysis_id,
            "file_path": file_path,
            "results": analysis_response,
            "memory_storage": f"memory://{analysis_id}"
        }
    
    async def _notify_analytic_swarm(self, analysis_id: str, analysis_results: Dict[str, Any]):
        """Notify the swarm of new code analysis results"""
        try:
            # Create message for swarm
            message = SwarmMessage(
                sender_agent_id="code_review_engine",
                receiver_agent_id="analytic_swarm",
                message_type=MessageType.RESULT,
                content={
                    "analysis_id": analysis_id,
                    "results": analysis_results,
                    "context": {
                        "type": "code_review",
                        "timestamp": asyncio.get_event_loop().time()
                    }
                },
                priority=7
            )
            
            # Publish message
            await self.message_bus.publish(message)
            
            logger.info(f"Notification sent to analytic swarm for {analysis_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to notify swarm: {str(e)}")
            return False
    
    async def get_analysis_history(self, file_path: str, limit: int = 5) -> List[Dict]:
        """Retrieve analysis history for a file from memory"""
        results = await search_memory(
            query=file_path,
            filters={
                "analysis_type": "code_review",
                "file_path": file_path
            },
            top_k=limit
        )
        
        return [{
            "analysis_id": r["metadata"].get("analysis_id", "unknown"),
            "timestamp": r["metadata"].get("timestamp", "unknown"),
            "summary": r["content"][:200] + "..." if len(r["content"]) > 200 else r["content"]
        } for r in results]
    
    async def get_code_review_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive dashboard of code review system status"""
        # Get recent analyses
        recent_analyses = await self.get_analysis_history(
            file_path="all",
            limit=20
        )
        
        # Get system metrics (simulated for now)
        metrics = {
            "total_analyses": len(recent_analyses),
            "average_analysis_time": 2.3,
            "success_rate": 0.97,
            "memory_usage": "15.6% of 512MB"
        }
        
        return {
            "dashboard": {
                "recent_analyses": recent_analyses[:5],
                "system_metrics": metrics
            }
        }

# Example usage
if __name__ == "__main__":
    async def demo():
        # Initialize dependencies
        message_bus = MessageBus()
        await message_bus.initialize()
        executor = RealExecutor()
        swarm = SimpleAgentOrchestrator()  # Or actual swarm instance
        
        engine = CodeReviewEngine(message_bus, executor, swarm)
        
        # Analyze sample code
        sample_code = """
        def add(a, b):
            return a + b
        """
        result = await engine.analyze_code(
            code=sample_code,
            file_path="example.py"
        )
        
        print(f"Code reviewed and stored as {result['analysis_id']}")
        print("Dashboard:", await engine.get_code_review_dashboard())
        
        # Clean up
        await message_bus.close()
    
    asyncio.run(demo())
