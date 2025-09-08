#!/usr/bin/env python3
"""
Enhanced Search Service for Sophia AI
Multi-source intelligence with Serper, Perplexity, Brave, Exa, and Tavily APIs
"""

import asyncio
import aiohttp
import time
import hashlib
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration
API_KEYS = {
    'serper': '7b616d4bf53e98d9169e89c25d6f4bf4389a9ed5',
    'perplexity': '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',
    'brave': 'BSApz0194z7SG6DplmVozl7ttFOi0Eo',
    'exa': 'fdf07f38-34ad-44a9-ab6f-74ca2ca90fd4',
    'tavily': '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'
}

class QueryType(str, Enum):
    REAL_TIME = "real_time"
    RESEARCH = "research"
    SEMANTIC = "semantic"
    REASONING = "reasoning"
    FACTUAL = "factual"
    GENERAL = "general"

@dataclass
class SearchResult:
    source: str
    title: str
    content: str
    url: str
    confidence: float
    timestamp: float

class SearchRequest(BaseModel):
    query: str
    max_results: int = 10
    include_sources: List[str] = None
    query_types: List[QueryType] = None

class EnhancedSearchResponse(BaseModel):
    query: str
    primary_response: str
    sources: List[Dict[str, Any]]
    confidence: float
    response_time_ms: int
    apis_used: List[str]
    query_types: List[str]

class QueryClassifier:
    """Intelligent query classification for optimal API routing"""

    QUERY_PATTERNS = {
        QueryType.REAL_TIME: ['news', 'current', 'latest', 'today', 'recent', 'breaking', 'now'],
        QueryType.RESEARCH: ['analyze', 'study', 'research', 'academic', 'paper', 'journal', 'scientific'],
        QueryType.SEMANTIC: ['similar', 'related', 'like', 'concept', 'meaning', 'compare'],
        QueryType.REASONING: ['why', 'how', 'explain', 'complex', 'analyze', 'understand', 'reason'],
        QueryType.FACTUAL: ['what', 'when', 'where', 'who', 'definition', 'define', 'fact']
    }

    def classify_query(self, query: str) -> List[QueryType]:
        """Classify query to determine optimal API routing"""
        query_lower = query.lower()
        classifications = []

        for query_type, keywords in self.QUERY_PATTERNS.items():
            if any(keyword in query_lower for keyword in keywords):
                classifications.append(query_type)

        return classifications if classifications else [QueryType.GENERAL]

class APIClient:
    """Base API client with rate limiting and error handling"""

    def __init__(self, api_name: str, api_key: str):
        self.api_name = api_name
        self.api_key = api_key
        self.session = None
        self.rate_limit_remaining = 1000
        self.last_request_time = 0

    async def get_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        if self.session:
            await self.session.close()

class SerperClient(APIClient):
    """Serper.dev Google Search API client"""

    def __init__(self):
        super().__init__("serper", API_KEYS['serper'])
        self.base_url = "https://google.serper.dev"

    async def search(self, query: str, search_type: str = "search") -> List[SearchResult]:
        """Execute search via Serper API"""
        try:
            session = await self.get_session()

            headers = {
                'X-API-KEY': self.api_key,
                'Content-Type': 'application/json'
            }

            payload = {
                'q': query,
                'num': 10
            }

            url = f"{self.base_url}/{search_type}"

            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_serper_results(data)
                else:
                    logger.error(f"Serper API error: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Serper search error: {e}")
            return []

    def _parse_serper_results(self, data: Dict) -> List[SearchResult]:
        """Parse Serper API response"""
        results = []

        # Parse organic results
        for item in data.get('organic', []):
            results.append(SearchResult(
                source='serper',
                title=item.get('title', ''),
                content=item.get('snippet', ''),
                url=item.get('link', ''),
                confidence=0.8,
                timestamp=time.time()
            ))

        # Parse news results if available
        for item in data.get('news', []):
            results.append(SearchResult(
                source='serper_news',
                title=item.get('title', ''),
                content=item.get('snippet', ''),
                url=item.get('link', ''),
                confidence=0.9,
                timestamp=time.time()
            ))

        return results

class PerplexityClient(APIClient):
    """Perplexity AI API client"""

    def __init__(self):
        super().__init__("perplexity", API_KEYS['perplexity'])
        self.base_url = "https://api.perplexity.ai"

    async def chat(self, query: str, model: str = "pplx-7b-online") -> Optional[str]:
        """Execute reasoning query via Perplexity API"""
        try:
            session = await self.get_session()

            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            payload = {
                'model': model,
                'messages': [
                    {
                        'role': 'user',
                        'content': query
                    }
                ],
                'max_tokens': 1000,
                'temperature': 0.2
            }

            async with session.post(f"{self.base_url}/chat/completions", 
                                  headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['choices'][0]['message']['content']
                else:
                    logger.error(f"Perplexity API error: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Perplexity chat error: {e}")
            return None

class BraveClient(APIClient):
    """Brave Search API client"""

    def __init__(self):
        super().__init__("brave", API_KEYS['brave'])
        self.base_url = "https://api.search.brave.com/res/v1"

    async def search(self, query: str, freshness: str = None) -> List[SearchResult]:
        """Execute search via Brave API"""
        try:
            session = await self.get_session()

            headers = {
                'X-Subscription-Token': self.api_key,
                'Accept': 'application/json'
            }

            params = {
                'q': query,
                'count': 10
            }

            if freshness:
                params['freshness'] = freshness

            async with session.get(f"{self.base_url}/web/search", 
                                 headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_brave_results(data)
                else:
                    logger.error(f"Brave API error: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Brave search error: {e}")
            return []

    def _parse_brave_results(self, data: Dict) -> List[SearchResult]:
        """Parse Brave API response"""
        results = []

        for item in data.get('web', {}).get('results', []):
            results.append(SearchResult(
                source='brave',
                title=item.get('title', ''),
                content=item.get('description', ''),
                url=item.get('url', ''),
                confidence=0.8,
                timestamp=time.time()
            ))

        return results

class ExaClient(APIClient):
    """Exa (Metaphor) API client"""

    def __init__(self):
        super().__init__("exa", API_KEYS['exa'])
        self.base_url = "https://api.exa.ai"

    async def search(self, query: str, search_type: str = "neural") -> List[SearchResult]:
        """Execute semantic search via Exa API"""
        try:
            session = await self.get_session()

            headers = {
                'x-api-key': self.api_key,
                'Content-Type': 'application/json'
            }

            payload = {
                'query': query,
                'numResults': 10,
                'type': search_type,
                'contents': {
                    'text': True
                }
            }

            async with session.post(f"{self.base_url}/search", 
                                  headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_exa_results(data)
                else:
                    logger.error(f"Exa API error: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Exa search error: {e}")
            return []

    def _parse_exa_results(self, data: Dict) -> List[SearchResult]:
        """Parse Exa API response"""
        results = []

        for item in data.get('results', []):
            results.append(SearchResult(
                source='exa',
                title=item.get('title', ''),
                content=item.get('text', '')[:500],  # Truncate long content
                url=item.get('url', ''),
                confidence=0.85,
                timestamp=time.time()
            ))

        return results

class TavilyClient(APIClient):
    """Tavily Search API client"""

    def __init__(self):
        super().__init__("tavily", API_KEYS['tavily'])
        self.base_url = "https://api.tavily.com"

    async def research(self, query: str) -> List[SearchResult]:
        """Execute research query via Tavily API"""
        try:
            session = await self.get_session()

            headers = {
                'Content-Type': 'application/json'
            }

            payload = {
                'api_key': self.api_key,
                'query': query,
                'search_depth': 'advanced',
                'include_answer': True,
                'include_raw_content': False,
                'max_results': 10
            }

            async with session.post(f"{self.base_url}/search", 
                                  headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_tavily_results(data)
                else:
                    logger.error(f"Tavily API error: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Tavily research error: {e}")
            return []

    def _parse_tavily_results(self, data: Dict) -> List[SearchResult]:
        """Parse Tavily API response"""
        results = []

        for item in data.get('results', []):
            results.append(SearchResult(
                source='tavily',
                title=item.get('title', ''),
                content=item.get('content', ''),
                url=item.get('url', ''),
                confidence=0.9,
                timestamp=time.time()
            ))

        return results

class EnhancedSearchService:
    """Main enhanced search service orchestrator"""

    def __init__(self):
        self.classifier = QueryClassifier()
        self.serper = SerperClient()
        self.perplexity = PerplexityClient()
        self.brave = BraveClient()
        self.exa = ExaClient()
        self.tavily = TavilyClient()
        self.cache = {}  # Simple in-memory cache

    async def search(self, request: SearchRequest) -> EnhancedSearchResponse:
        """Execute enhanced multi-source search"""
        start_time = time.time()

        # Classify query if not provided
        query_types = request.query_types or self.classifier.classify_query(request.query)

        # Check cache
        cache_key = self._get_cache_key(request.query, query_types)
        if cache_key in self.cache:
            cached_result = self.cache[cache_key]
            if time.time() - cached_result['timestamp'] < 300:  # 5 minute cache
                return cached_result['response']

        # Execute parallel searches based on query types
        search_tasks = []
        apis_used = []

        # Real-time search
        if QueryType.REAL_TIME in query_types:
            search_tasks.append(self.serper.search(request.query, "news"))
            search_tasks.append(self.brave.search(request.query, "pd"))
            apis_used.extend(['serper', 'brave'])

        # Research and semantic search
        if QueryType.RESEARCH in query_types or QueryType.SEMANTIC in query_types:
            search_tasks.append(self.exa.search(request.query))
            search_tasks.append(self.tavily.research(request.query))
            apis_used.extend(['exa', 'tavily'])

        # General search if no specific type
        if QueryType.GENERAL in query_types:
            search_tasks.append(self.serper.search(request.query))
            apis_used.append('serper')

        # AI reasoning
        reasoning_task = None
        if QueryType.REASONING in query_types:
            reasoning_task = self.perplexity.chat(request.query)
            apis_used.append('perplexity')

        # Execute searches
        search_results = []
        if search_tasks:
            results = await asyncio.gather(*search_tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, list):
                    search_results.extend(result)

        # Get AI reasoning
        ai_reasoning = None
        if reasoning_task:
            ai_reasoning = await reasoning_task

        # Fuse responses
        response = await self._fuse_responses(
            request.query, search_results, ai_reasoning, query_types, apis_used
        )

        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        response.response_time_ms = response_time_ms

        # Cache result
        self.cache[cache_key] = {
            'response': response,
            'timestamp': time.time()
        }

        return response

    async def _fuse_responses(self, query: str, search_results: List[SearchResult], 
                            ai_reasoning: Optional[str], query_types: List[QueryType],
                            apis_used: List[str]) -> EnhancedSearchResponse:
        """Fuse multiple sources into coherent response"""

        # Sort results by confidence
        search_results.sort(key=lambda x: x.confidence, reverse=True)

        # Create primary response
        if ai_reasoning:
            primary_response = ai_reasoning
            confidence = 0.95
        elif search_results:
            # Combine top results
            top_results = search_results[:3]
            primary_response = f"Based on multiple sources:\n\n"
            for i, result in enumerate(top_results, 1):
                primary_response += f"{i}. {result.content}\n\n"
            confidence = sum(r.confidence for r in top_results) / len(top_results)
        else:
            primary_response = f"I couldn't find specific information about: {query}"
            confidence = 0.1

        # Prepare sources
        sources = []
        for result in search_results[:10]:  # Top 10 sources
            sources.append({
                'source': result.source,
                'title': result.title,
                'content': result.content,
                'url': result.url,
                'confidence': result.confidence
            })

        return EnhancedSearchResponse(
            query=query,
            primary_response=primary_response,
            sources=sources,
            confidence=confidence,
            response_time_ms=0,  # Will be set by caller
            apis_used=list(set(apis_used)),
            query_types=[qt.value for qt in query_types]
        )

    def _get_cache_key(self, query: str, query_types: List[QueryType]) -> str:
        """Generate cache key for query"""
        key_data = f"{query}:{sorted([qt.value for qt in query_types])}"
        return hashlib.md5(key_data.encode()).hexdigest()

    async def close(self):
        """Close all API clients"""
        await self.serper.close()
        await self.perplexity.close()
        await self.brave.close()
        await self.exa.close()
        await self.tavily.close()

# FastAPI app
app = FastAPI(
    title="Sophia AI Enhanced Search Service",
    description="Multi-source intelligence search for sophia-intel.ai",
    version="1.0.0"
)

# Global search service
search_service = None

@app.on_event("startup")
async def startup_event():
    global search_service
    search_service = EnhancedSearchService()
    logger.info("Enhanced Search Service started")

@app.on_event("shutdown")
async def shutdown_event():
    global search_service
    if search_service:
        await search_service.close()
    logger.info("Enhanced Search Service stopped")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "enhanced-search",
        "version": "1.0.0",
        "apis": list(API_KEYS.keys()),
        "timestamp": time.time()
    }

@app.post("/search", response_model=EnhancedSearchResponse)
async def enhanced_search(request: SearchRequest):
    """Enhanced multi-source search endpoint"""
    try:
        result = await search_service.search(request)
        return result
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Sophia AI Enhanced Search Service",
        "status": "operational",
        "endpoints": ["/health", "/search"],
        "apis": list(API_KEYS.keys())
    }

if __name__ == "__main__":
    uvicorn.run(app, host="${BIND_IP}", port=8004)
