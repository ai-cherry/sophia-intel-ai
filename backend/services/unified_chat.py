"""
Sophia AI Platform v4.0 - Unified Chat Service
Enhanced with intent caching, predictive fetching, and intelligent blending
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any
from functools import lru_cache
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib

from services.circuit_breaker import CircuitBreaker, circuit_breaker, CircuitBreakerConfig

logger = logging.getLogger(__name__)

class QueryIntent(Enum):
    """Types of query intents"""
    WEB_SEARCH = "web_search"
    INTERNAL_DATA = "internal_data"
    MCP_QUERY = "mcp_query"
    MIXED = "mixed"
    UNKNOWN = "unknown"

@dataclass
class Intent:
    """Query intent analysis result"""
    primary_intent: QueryIntent
    confidence: float
    requires_web: bool = False
    requires_internal: bool = False
    requires_mcp: bool = False
    domains: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)

@dataclass
class QueryResult:
    """Result from a query source"""
    source: str
    data: Any
    confidence: float
    response_time: float
    error: Optional[str] = None

class IntentAnalyzer:
    """Analyzes query intent using simple heuristics"""

    def __init__(self):
        self.web_keywords = {
            'search', 'find', 'google', 'web', 'internet', 'online',
            'latest', 'news', 'current', 'recent', 'today'
        }
        self.internal_keywords = {
            'dashboard', 'report', 'analytics', 'data', 'metrics',
            'sales', 'marketing', 'crm', 'pipeline', 'revenue'
        }
        self.mcp_keywords = {
            'gong', 'slack', 'github', 'notion', 'asana', 'hubspot',
            'integration', 'sync', 'connect', 'api'
        }

    async def analyze(self, query: str, user_context: Dict) -> Intent:
        """
        Analyze query intent

        Args:
            query: User query string
            user_context: User context including domains and preferences

        Returns:
            Intent: Analyzed intent with requirements
        """
        query_lower = query.lower()
        words = set(query_lower.split())

        # Calculate intent scores
        web_score = len(words.intersection(self.web_keywords))
        internal_score = len(words.intersection(self.internal_keywords))
        mcp_score = len(words.intersection(self.mcp_keywords))

        # Determine primary intent
        scores = {
            QueryIntent.WEB_SEARCH: web_score,
            QueryIntent.INTERNAL_DATA: internal_score,
            QueryIntent.MCP_QUERY: mcp_score
        }

        primary_intent = max(scores, key=scores.get)
        max_score = scores[primary_intent]

        if max_score == 0:
            primary_intent = QueryIntent.UNKNOWN
            confidence = 0.3
        elif sum(scores.values()) > max_score:
            primary_intent = QueryIntent.MIXED
            confidence = 0.8
        else:
            confidence = min(0.9, max_score / 3.0)

        # Determine requirements
        requires_web = web_score > 0 or 'search' in query_lower
        requires_internal = internal_score > 0 or any(
            domain in query_lower for domain in user_context.get('domains', [])
        )
        requires_mcp = mcp_score > 0

        # Extract domains and keywords
        domains = [d for d in user_context.get('domains', []) if d in query_lower]
        keywords = [w for w in words if len(w) > 3][:5]  # Top 5 keywords

        return Intent(
            primary_intent=primary_intent,
            confidence=confidence,
            requires_web=requires_web,
            requires_internal=requires_internal,
            requires_mcp=requires_mcp,
            domains=domains,
            keywords=keywords
        )

class PredictiveCache:
    """Predictive cache for query results and patterns"""

    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.cache: Dict[str, Dict] = {}
        self.max_size = max_size
        self.ttl = ttl
        self.access_patterns: Dict[str, int] = {}

    def _generate_key(self, query: str, context: Dict) -> str:
        """Generate cache key from query and context"""
        context_str = json.dumps(context, sort_keys=True)
        combined = f"{query}:{context_str}"
        return hashlib.md5(combined.encode()).hexdigest()

    async def get(self, query: str, context: Dict) -> Optional[Dict]:
        """Get cached result if available and not expired"""
        key = self._generate_key(query, context)

        if key in self.cache:
            cached = self.cache[key]
            if time.time() - cached['timestamp'] < self.ttl:
                self.access_patterns[key] = self.access_patterns.get(key, 0) + 1
                return cached['data']
            else:
                # Expired, remove from cache
                del self.cache[key]

        return None

    async def set(self, query: str, context: Dict, data: Dict):
        """Cache query result"""
        key = self._generate_key(query, context)

        # Evict oldest entries if cache is full
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]['timestamp'])
            del self.cache[oldest_key]
            if oldest_key in self.access_patterns:
                del self.access_patterns[oldest_key]

        self.cache[key] = {
            'data': data,
            'timestamp': time.time()
        }

    async def prefetch_related(self, query: str, context: Dict):
        """Prefetch related queries based on patterns"""
        # Placeholder for predictive prefetching logic
        # In a real implementation, this would analyze query patterns
        # and prefetch likely follow-up queries

    async def warm_common_queries(self):
        """Warm cache with common queries"""
        # Placeholder for cache warming logic

class UnifiedChatService:
    """
    Unified chat service with intelligent blending of multiple sources
    """

    def __init__(self):
        self.intent_analyzer = IntentAnalyzer()
        self.intent_cache: Dict[str, Intent] = {}
        self.predictive_cache = PredictiveCache()

        # Initialize circuit breakers for external services
        self.web_circuit = CircuitBreaker(
            "web_search",
            CircuitBreakerConfig(failure_threshold=3, recovery_timeout=30)
        )
        self.mcp_circuit = CircuitBreaker(
            "mcp_services", 
            CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60)
        )

        logger.info("🤖 Unified Chat Service initialized")

    async def process_query(self, query: str, user_context: Dict) -> Dict:
        """
        Process user query with intelligent source blending

        Args:
            query: User query string
            user_context: User context including role, domains, preferences

        Returns:
            Dict: Processed response with sources and confidence
        """
        start_time = time.time()

        # Check cache first
        cached_result = await self.predictive_cache.get(query, user_context)
        if cached_result:
            logger.info(f"📋 Cache hit for query: {query[:50]}...")
            cached_result['cached'] = True
            return cached_result

        # Analyze intent
        intent = await self._get_or_analyze_intent(query, user_context)

        # Predictive pre-fetch for likely follow-up queries
        asyncio.create_task(
            self.predictive_cache.prefetch_related(query, user_context)
        )

        # Parallel fetch with smart timeout management
        fetch_tasks = []
        timeout_map = {
            'web': 3.0,      # Flexible timeout for web
            'internal': 1.5,  # Fast internal systems
            'mcp': 4.0       # More flexible for MCP
        }

        if intent.requires_web:
            fetch_tasks.append(
                self._fetch_with_timeout(
                    self._fetch_web_results(query, user_context),
                    timeout_map['web'],
                    'web'
                )
            )

        if intent.requires_internal:
            fetch_tasks.append(
                self._fetch_with_timeout(
                    self._fetch_internal_results(query, user_context),
                    timeout_map['internal'],
                    'internal'
                )
            )

        if intent.requires_mcp:
            fetch_tasks.append(
                self._fetch_with_timeout(
                    self._fetch_mcp_results(query, user_context),
                    timeout_map['mcp'],
                    'mcp'
                )
            )

        # Execute all fetches in parallel
        results = await asyncio.gather(*fetch_tasks, return_exceptions=True)

        # Process results and handle exceptions
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Fetch failed: {result}")
                continue
            if result:  # Not None
                processed_results.append(result)

        # Intelligent blending with source confidence scoring
        response = await self._blend_with_confidence(
            query, processed_results, user_context, intent
        )

        # Add metadata
        response.update({
            'processing_time': time.time() - start_time,
            'intent': {
                'primary': intent.primary_intent.value,
                'confidence': intent.confidence,
                'domains': intent.domains
            },
            'cached': False
        })

        # Cache the result
        await self.predictive_cache.set(query, user_context, response)

        # Track interaction for learning
        await self._track_interaction(query, response, user_context)

        return response

    async def _get_or_analyze_intent(self, query: str, user_context: Dict) -> Intent:
        """Get intent from cache or analyze"""
        cache_key = f"{query}:{user_context.get('role', 'unknown')}"

        if cache_key in self.intent_cache:
            return self.intent_cache[cache_key]

        intent = await self.intent_analyzer.analyze(query, user_context)

        # Cache intent (with size limit)
        if len(self.intent_cache) > 100:
            # Remove oldest entry
            oldest_key = next(iter(self.intent_cache))
            del self.intent_cache[oldest_key]

        self.intent_cache[cache_key] = intent
        return intent

    async def _fetch_with_timeout(self, 
                                 coro, 
                                 timeout: float, 
                                 source: str) -> Optional[QueryResult]:
        """Fetch with timeout and error handling"""
        start_time = time.time()

        try:
            result = await asyncio.wait_for(coro, timeout=timeout)
            response_time = time.time() - start_time

            return QueryResult(
                source=source,
                data=result,
                confidence=0.8,  # Default confidence
                response_time=response_time
            )

        except asyncio.TimeoutError:
            logger.warning(f"⏰ {source} fetch timed out after {timeout}s")
            return QueryResult(
                source=source,
                data={},
                confidence=0.0,
                response_time=timeout,
                error="timeout"
            )
        except Exception as e:
            logger.error(f"❌ {source} fetch failed: {e}")
            return QueryResult(
                source=source,
                data={},
                confidence=0.0,
                response_time=time.time() - start_time,
                error=str(e)
            )

    async def _fetch_web_results(self, query: str, context: Dict) -> Dict:
        """Fetch web search results with circuit breaker"""
        try:
            return await self.web_circuit.call(self._web_search_impl, query, context)
        except Exception as e:
            logger.warning(f"Web search failed: {e}")
            return {"results": [], "source": "web", "error": str(e)}

    async def _web_search_impl(self, query: str, context: Dict) -> Dict:
        """Implementation of web search (placeholder)"""
        # Simulate web search
        await asyncio.sleep(0.5)  # Simulate network delay

        return {
            "results": [
                {
                    "title": f"Web result for: {query}",
                    "snippet": f"This is a simulated web search result for '{query}'",
                    "url": "https://example.com/result1"
                }
            ],
            "source": "web",
            "query": query
        }

    async def _fetch_internal_results(self, query: str, context: Dict) -> Dict:
        """Fetch internal system results"""
        # Simulate internal data fetch
        await asyncio.sleep(0.2)  # Fast internal systems

        return {
            "results": [
                {
                    "type": "dashboard_metric",
                    "title": f"Internal data for: {query}",
                    "value": "42",
                    "source": "internal_db"
                }
            ],
            "source": "internal",
            "domains": context.get('domains', [])
        }

    async def _fetch_mcp_results(self, query: str, context: Dict) -> Dict:
        """Fetch MCP server results with circuit breaker"""
        try:
            return await self.mcp_circuit.call(self._mcp_query_impl, query, context)
        except Exception as e:
            logger.warning(f"MCP query failed: {e}")
            return {"results": [], "source": "mcp", "error": str(e)}

    async def _mcp_query_impl(self, query: str, context: Dict) -> Dict:
        """Implementation of MCP query (placeholder)"""
        # Simulate MCP server query
        await asyncio.sleep(1.0)  # MCP servers might be slower

        return {
            "results": [
                {
                    "server": "gong",
                    "type": "sales_insight",
                    "data": f"MCP result for: {query}",
                    "confidence": 0.85
                }
            ],
            "source": "mcp",
            "servers_queried": ["gong", "hubspot", "slack"]
        }

    async def _blend_with_confidence(self, 
                                   query: str, 
                                   results: List[QueryResult], 
                                   context: Dict,
                                   intent: Intent) -> Dict:
        """Blend results from multiple sources with confidence scoring"""

        if not results:
            return {
                "response": "I couldn't find relevant information for your query.",
                "sources": [],
                "confidence": 0.0
            }

        # Sort results by confidence and response time
        valid_results = [r for r in results if r.error is None]
        valid_results.sort(key=lambda r: (r.confidence, -r.response_time), reverse=True)

        # Generate blended response
        response_parts = []
        sources_used = []

        for result in valid_results[:3]:  # Use top 3 results
            if result.data and result.data.get('results'):
                response_parts.append(f"From {result.source}: {self._summarize_result(result.data)}")
                sources_used.append({
                    'source': result.source,
                    'confidence': result.confidence,
                    'response_time': result.response_time,
                    'data_points': len(result.data.get('results', []))
                })

        if not response_parts:
            response_text = "I found some information but couldn't extract meaningful results."
            overall_confidence = 0.2
        else:
            response_text = " ".join(response_parts)
            overall_confidence = sum(s['confidence'] for s in sources_used) / len(sources_used)

        return {
            "response": response_text,
            "sources": sources_used,
            "confidence": overall_confidence,
            "query": query,
            "intent_matched": intent.primary_intent.value
        }

    def _summarize_result(self, data: Dict) -> str:
        """Summarize result data for response"""
        results = data.get('results', [])
        if not results:
            return "No specific results found."

        if len(results) == 1:
            result = results[0]
            return result.get('title', result.get('snippet', str(result)))
        else:
            return f"Found {len(results)} relevant items."

    async def _track_interaction(self, query: str, response: Dict, context: Dict):
        """Track interaction for learning and analytics"""
        # Placeholder for interaction tracking
        # In a real implementation, this would log to analytics system
        logger.info(f"📊 Query processed: confidence={response.get('confidence', 0):.2f}, "
                   f"sources={len(response.get('sources', []))}")

    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            "web_circuit": self.web_circuit.get_stats(),
            "mcp_circuit": self.mcp_circuit.get_stats(),
            "intent_cache_size": len(self.intent_cache),
            "predictive_cache_size": len(self.predictive_cache.cache)
        }

# Example usage
if __name__ == "__main__":
    async def sophia_unified_chat():
        """Test the unified chat service"""
        service = UnifiedChatService()

        sophia_queries = [
            "What are our sales numbers this month?",
            "Search for latest PropTech trends",
            "Show me Gong call insights",
            "What's in our marketing pipeline?"
        ]

        user_context = {
            "role": "manager",
            "domains": ["sales", "marketing", "bi"],
            "user_id": "sophia_user"
        }

        for query in sophia_queries:
            print(f"\n🔍 Query: {query}")
            result = await service.process_query(query, user_context)
            print(f"📝 Response: {result['response']}")
            print(f"📊 Confidence: {result['confidence']:.2f}")
            print(f"⏱️  Processing time: {result['processing_time']:.2f}s")
            print(f"🎯 Intent: {result['intent']['primary']}")
            print("-" * 60)

        # Print service stats
        stats = service.get_service_stats()
        print(f"\n📈 Service Stats:")
        print(json.dumps(stats, indent=2))

    # Run test
    asyncio.run(sophia_unified_chat())
