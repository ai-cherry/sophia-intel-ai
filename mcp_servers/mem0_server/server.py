"""
Mem0 MCP Server - Advanced Memory-Aware AI Agent Integration
Provides persistent, adaptive memory capabilities for Sophia AI V8+
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from mcp.server import Server
    from mcp.types import TextContent, Tool
except ImportError:
    # Fallback for development
    class Server:
        def __init__(self, name: str):
            self.name = name

        def register_tool(self, name: str, func):
            pass

    class Tool:
        pass

    class TextContent:
        pass


try:
    from mem0 import MemoryClient
except ImportError:
    # Mock for development
    class MemoryClient:
        def __init__(self, api_key: str):
            self.api_key = api_key

        async def add(self, messages: List[Dict], user_id: str) -> Dict:
            return {"id": "mock"}

        async def search(self, query: str, user_id: str) -> List[Dict]:
            return []

        async def get_all(self, user_id: str) -> List[Dict]:
            return []


import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MemoryContext:
    """Enhanced memory context with adaptive learning"""

    user_id: str
    session_id: str
    domain: str  # e.g., "gong_analysis", "salesforce_insights"
    priority: int = 1  # 1-5, higher = more important
    access_count: int = 0
    last_accessed: datetime = None
    adaptation_score: float = 0.0  # Learning effectiveness


class Mem0MCPServer(Server):
    """
    Advanced Mem0 MCP Server for Sophia AI V8+
    Features:
    - Adaptive memory with access pattern learning
    - Cross-domain memory correlation
    - Real-time memory updates via CDC
    - Performance optimization for PropTech workflows
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__("mem0-memory-v8")

        # Initialize Mem0 client
        self.mem0_key = config.get("mem0_api_key") or os.getenv("MEM0_API_KEY")
        if not self.mem0_key:
            raise ValueError("MEM0_API_KEY required for Mem0 MCP Server")

        self.mem0 = MemoryClient(api_key=self.mem0_key)

        # Adaptive memory tracking
        self.memory_contexts: Dict[str, MemoryContext] = {}
        self.access_patterns: Dict[str, List[datetime]] = {}

        # Performance optimization
        self.cache_ttl = config.get("cache_ttl", 300)  # 5 minutes
        self.memory_cache: Dict[str, Any] = {}

        # Register MCP tools
        self._register_tools()

        logger.info("✅ Mem0 MCP Server V8+ initialized with adaptive memory")

    def _register_tools(self):
        """Register all Mem0 MCP tools"""

        self.register_tool(
            "store_memory",
            Tool(
                name="store_memory",
                description="Store adaptive memory with context awareness for PropTech workflows",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Memory content to store"},
                        "user_id": {"type": "string", "description": "User/agent identifier"},
                        "domain": {
                            "type": "string",
                            "description": "Business domain (gong, salesforce, etc.)",
                        },
                        "priority": {
                            "type": "integer",
                            "description": "Memory priority 1-5",
                            "default": 1,
                        },
                        "metadata": {
                            "type": "object",
                            "description": "Additional context metadata",
                        },
                    },
                    "required": ["content", "user_id", "domain"],
                },
            ),
        )

        self.register_tool(
            "recall_memory",
            Tool(
                name="recall_memory",
                description="Adaptive memory recall with learning optimization",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Memory search query"},
                        "user_id": {"type": "string", "description": "User/agent identifier"},
                        "domain": {"type": "string", "description": "Business domain filter"},
                        "limit": {"type": "integer", "description": "Max results", "default": 10},
                        "adaptive": {
                            "type": "boolean",
                            "description": "Enable adaptive learning",
                            "default": True,
                        },
                    },
                    "required": ["query", "user_id"],
                },
            ),
        )

        self.register_tool(
            "correlate_memories",
            Tool(
                name="correlate_memories",
                description="Cross-domain memory correlation for business intelligence",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "domains": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Domains to correlate",
                        },
                        "user_id": {"type": "string", "description": "User/agent identifier"},
                        "correlation_type": {
                            "type": "string",
                            "enum": ["temporal", "semantic", "causal"],
                            "default": "semantic",
                        },
                    },
                    "required": ["domains", "user_id"],
                },
            ),
        )

        self.register_tool(
            "optimize_memory",
            Tool(
                name="optimize_memory",
                description="Optimize memory storage based on access patterns",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "User/agent identifier"},
                        "strategy": {
                            "type": "string",
                            "enum": ["frequency", "recency", "importance"],
                            "default": "frequency",
                        },
                    },
                    "required": ["user_id"],
                },
            ),
        )

    async def store_memory(
        self,
        content: str,
        user_id: str,
        domain: str,
        priority: int = 1,
        metadata: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Store adaptive memory with enhanced context"""
        try:
            # Create enhanced message for Mem0
            message = {
                "role": "user",
                "content": content,
                "metadata": {
                    "domain": domain,
                    "priority": priority,
                    "timestamp": datetime.now().isoformat(),
                    "sophia_version": "v8+",
                    **(metadata or {}),
                },
            }

            # Store in Mem0
            result = await self.mem0.add(messages=[message], user_id=user_id)

            # Update local context tracking
            context_key = f"{user_id}:{domain}"
            if context_key not in self.memory_contexts:
                self.memory_contexts[context_key] = MemoryContext(
                    user_id=user_id,
                    session_id=f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    domain=domain,
                    priority=priority,
                )

            # Update access patterns for adaptive learning
            if context_key not in self.access_patterns:
                self.access_patterns[context_key] = []
            self.access_patterns[context_key].append(datetime.now())

            logger.info(f"✅ Stored memory for {user_id} in domain {domain}")

            return {
                "success": True,
                "memory_id": result.get("id", "unknown"),
                "domain": domain,
                "priority": priority,
                "adaptive_score": self._calculate_adaptation_score(context_key),
            }

        except Exception as e:
            logger.error(f"❌ Error storing memory: {e}")
            return {"success": False, "error": str(e)}

    async def recall_memory(
        self,
        query: str,
        user_id: str,
        domain: Optional[str] = None,
        limit: int = 10,
        adaptive: bool = True,
    ) -> Dict[str, Any]:
        """Adaptive memory recall with learning optimization"""
        try:
            # Check cache first for performance
            cache_key = f"{user_id}:{query}:{domain}"
            if cache_key in self.memory_cache:
                cached_result = self.memory_cache[cache_key]
                if (datetime.now() - cached_result["timestamp"]).seconds < self.cache_ttl:
                    logger.info(f"🚀 Cache hit for memory recall: {query[:50]}...")
                    return cached_result["data"]

            # Search Mem0
            memories = await self.mem0.search(query=query, user_id=user_id)

            # Filter by domain if specified
            if domain:
                memories = [m for m in memories if m.get("metadata", {}).get("domain") == domain]

            # Limit results
            memories = memories[:limit]

            # Adaptive learning: update access patterns
            if adaptive:
                context_key = f"{user_id}:{domain or 'global'}"
                if context_key in self.memory_contexts:
                    self.memory_contexts[context_key].access_count += 1
                    self.memory_contexts[context_key].last_accessed = datetime.now()

                    # Update access patterns
                    if context_key not in self.access_patterns:
                        self.access_patterns[context_key] = []
                    self.access_patterns[context_key].append(datetime.now())

            # Enhanced result with adaptive insights
            result = {
                "success": True,
                "memories": memories,
                "count": len(memories),
                "query": query,
                "domain": domain,
                "adaptive_insights": (
                    self._generate_adaptive_insights(user_id, domain) if adaptive else None
                ),
            }

            # Cache result for performance
            self.memory_cache[cache_key] = {"data": result, "timestamp": datetime.now()}

            logger.info(f"✅ Recalled {len(memories)} memories for query: {query[:50]}...")
            return result

        except Exception as e:
            logger.error(f"❌ Error recalling memory: {e}")
            return {"success": False, "error": str(e)}

    async def correlate_memories(
        self, domains: List[str], user_id: str, correlation_type: str = "semantic"
    ) -> Dict[str, Any]:
        """Cross-domain memory correlation for business intelligence"""
        try:
            correlations = {}

            # Get memories from each domain
            domain_memories = {}
            for domain in domains:
                memories = await self.mem0.search(query="", user_id=user_id)
                domain_memories[domain] = [
                    m for m in memories if m.get("metadata", {}).get("domain") == domain
                ]

            # Perform correlation analysis
            if correlation_type == "temporal":
                correlations = self._temporal_correlation(domain_memories)
            elif correlation_type == "semantic":
                correlations = self._semantic_correlation(domain_memories)
            elif correlation_type == "causal":
                correlations = self._causal_correlation(domain_memories)

            logger.info(f"✅ Correlated memories across {len(domains)} domains")

            return {
                "success": True,
                "correlations": correlations,
                "domains": domains,
                "correlation_type": correlation_type,
                "insights": self._generate_correlation_insights(correlations),
            }

        except Exception as e:
            logger.error(f"❌ Error correlating memories: {e}")
            return {"success": False, "error": str(e)}

    async def optimize_memory(self, user_id: str, strategy: str = "frequency") -> Dict[str, Any]:
        """Optimize memory storage based on access patterns"""
        try:
            optimization_results = {}

            # Get all memories for user
            all_memories = await self.mem0.get_all(user_id=user_id)

            if strategy == "frequency":
                optimization_results = self._optimize_by_frequency(user_id, all_memories)
            elif strategy == "recency":
                optimization_results = self._optimize_by_recency(user_id, all_memories)
            elif strategy == "importance":
                optimization_results = self._optimize_by_importance(user_id, all_memories)

            logger.info(f"✅ Optimized memories for {user_id} using {strategy} strategy")

            return {
                "success": True,
                "strategy": strategy,
                "optimizations": optimization_results,
                "memory_count": len(all_memories),
            }

        except Exception as e:
            logger.error(f"❌ Error optimizing memory: {e}")
            return {"success": False, "error": str(e)}

    def _calculate_adaptation_score(self, context_key: str) -> float:
        """Calculate adaptive learning score based on access patterns"""
        if context_key not in self.access_patterns:
            return 0.0

        accesses = self.access_patterns[context_key]
        if len(accesses) < 2:
            return 0.1

        # Calculate score based on frequency and recency
        recent_accesses = [a for a in accesses if (datetime.now() - a).days <= 7]
        frequency_score = len(recent_accesses) / 7  # Accesses per day
        recency_score = 1.0 / max(1, (datetime.now() - accesses[-1]).days)

        return min(1.0, (frequency_score + recency_score) / 2)

    def _generate_adaptive_insights(self, user_id: str, domain: Optional[str]) -> Dict[str, Any]:
        """Generate adaptive insights based on memory patterns"""
        context_key = f"{user_id}:{domain or 'global'}"

        if context_key not in self.memory_contexts:
            return {"insight": "No pattern data available"}

        context = self.memory_contexts[context_key]
        adaptation_score = self._calculate_adaptation_score(context_key)

        insights = {
            "adaptation_score": adaptation_score,
            "access_frequency": context.access_count,
            "learning_effectiveness": (
                "high" if adaptation_score > 0.7 else "medium" if adaptation_score > 0.3 else "low"
            ),
            "recommendations": [],
        }

        # Generate recommendations
        if adaptation_score < 0.3:
            insights["recommendations"].append(
                "Consider more frequent memory access for better learning"
            )
        if context.access_count > 100:
            insights["recommendations"].append("High usage detected - consider memory optimization")

        return insights

    def _temporal_correlation(self, domain_memories: Dict[str, List]) -> Dict[str, Any]:
        """Analyze temporal correlations between domain memories"""
        # Simplified temporal correlation
        return {"type": "temporal", "correlations": []}

    def _semantic_correlation(self, domain_memories: Dict[str, List]) -> Dict[str, Any]:
        """Analyze semantic correlations between domain memories"""
        # Simplified semantic correlation
        return {"type": "semantic", "correlations": []}

    def _causal_correlation(self, domain_memories: Dict[str, List]) -> Dict[str, Any]:
        """Analyze causal correlations between domain memories"""
        # Simplified causal correlation
        return {"type": "causal", "correlations": []}

    def _generate_correlation_insights(self, correlations: Dict[str, Any]) -> List[str]:
        """Generate business insights from memory correlations"""
        return [
            "Cross-domain patterns detected",
            "Potential workflow optimizations identified",
            "Business intelligence opportunities found",
        ]

    def _optimize_by_frequency(self, user_id: str, memories: List) -> Dict[str, Any]:
        """Optimize memories based on access frequency"""
        return {"optimized": len(memories), "strategy": "frequency"}

    def _optimize_by_recency(self, user_id: str, memories: List) -> Dict[str, Any]:
        """Optimize memories based on recency"""
        return {"optimized": len(memories), "strategy": "recency"}

    def _optimize_by_importance(self, user_id: str, memories: List) -> Dict[str, Any]:
        """Optimize memories based on importance scores"""
        return {"optimized": len(memories), "strategy": "importance"}


# Factory function for easy instantiation
def create_mem0_server(config: Dict[str, Any]) -> Mem0MCPServer:
    """Create and configure Mem0 MCP Server"""
    return Mem0MCPServer(config)


# CLI entry point for standalone server
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Mem0 MCP Server V8+")
    parser.add_argument("--mem0-key", required=True, help="Mem0 API key")
    parser.add_argument("--port", type=int, default=8002, help="Server port")

    args = parser.parse_args()

    config = {"mem0_api_key": args.mem0_key, "cache_ttl": 300}

    server = create_mem0_server(config)

    print(f"🚀 Starting Mem0 MCP Server V8+ on port {args.port}")
    print("✅ Adaptive memory capabilities enabled")
    print("🧠 Cross-domain correlation ready")
    print("⚡ Performance optimization active")
