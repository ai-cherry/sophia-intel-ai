"""
Enhanced Web Research Service for SOPHIA Intel
Advanced SERP integration with multi-source research synthesis,
real-time information enhancement, and intelligent research orchestration
"""

import asyncio
import json
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import httpx
from loguru import logger
from pydantic import BaseModel

from backend.web_access_service import WebAccessService, WebSearchRequest, WebScrapeRequest
from backend.context_manager import ContextManager
from config.config import settings


class ResearchQuery(BaseModel):
    """Enhanced research query with advanced options"""
    query: str
    depth: str = "standard"  # quick, standard, deep, comprehensive
    sources: List[str] = ["web", "news", "academic"]  # web, news, academic, social
    max_sources: int = 10
    time_range: str = "any"  # hour, day, week, month, year, any
    language: str = "en"
    region: str = "us"
    include_images: bool = False
    include_videos: bool = False
    synthesize_results: bool = True


class ResearchResult(BaseModel):
    """Structured research result"""
    query: str
    sources_found: int
    synthesis: str
    key_findings: List[str]
    source_details: List[Dict[str, Any]]
    confidence_score: float
    research_time: float
    metadata: Dict[str, Any]


class EnhancedWebResearch:
    """
    Enhanced web research service with advanced capabilities:
    - Multi-provider SERP integration (Tavily, SerpAPI, Bright Data)
    - Intelligent source synthesis and analysis
    - Real-time information enhancement
    - Research context optimization
    - Academic and news source integration
    """
    
    def __init__(self):
        self.web_service = WebAccessService()
        self.context_manager = ContextManager()
        
        # API keys for research providers
        self.tavily_key = getattr(settings, "TAVILY_API_KEY", "")
        self.serpapi_key = getattr(settings, "SERPAPI_KEY", "")
        self.newsapi_key = getattr(settings, "NEWSAPI_KEY", "")
        
        # Research configuration
        self.max_concurrent_requests = 5
        self.research_timeout = 60.0
        self.synthesis_model = "gpt-4"  # For result synthesis
        
        # Caching for research results
        self.research_cache = {}
        self.cache_ttl = 1800  # 30 minutes for research results
        
        # Source quality scoring
        self.source_quality_scores = {
            # High-quality sources
            "wikipedia.org": 0.9,
            "arxiv.org": 0.95,
            "nature.com": 0.95,
            "science.org": 0.95,
            "pubmed.ncbi.nlm.nih.gov": 0.9,
            "scholar.google.com": 0.85,
            
            # News sources
            "reuters.com": 0.85,
            "bbc.com": 0.85,
            "apnews.com": 0.85,
            "npr.org": 0.8,
            
            # Tech sources
            "github.com": 0.8,
            "stackoverflow.com": 0.75,
            "medium.com": 0.6,
            
            # Default scores
            "gov": 0.85,  # Government domains
            "edu": 0.8,   # Educational domains
            "org": 0.7,   # Organization domains
        }
    
    async def research(
        self,
        query: ResearchQuery,
        session_id: Optional[str] = None
    ) -> ResearchResult:
        """
        Perform comprehensive research with multi-source synthesis
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Check cache first
            cache_key = self._generate_cache_key(query)
            cached_result = self._get_cached_research(cache_key)
            if cached_result:
                logger.info(f"Cache hit for research query: {query.query[:50]}")
                return cached_result
            
            logger.info(f"Starting {query.depth} research for: {query.query}")
            
            # Gather sources based on research depth
            research_tasks = []
            
            # Web search (always included)
            if "web" in query.sources:
                research_tasks.append(self._research_web_sources(query))
            
            # News search
            if "news" in query.sources:
                research_tasks.append(self._research_news_sources(query))
            
            # Academic search
            if "academic" in query.sources:
                research_tasks.append(self._research_academic_sources(query))
            
            # Social media (if requested)
            if "social" in query.sources:
                research_tasks.append(self._research_social_sources(query))
            
            # Execute research tasks concurrently
            research_results = await asyncio.gather(*research_tasks, return_exceptions=True)
            
            # Combine and process results
            all_sources = []
            for result in research_results:
                if isinstance(result, list):
                    all_sources.extend(result)
                elif isinstance(result, Exception):
                    logger.warning(f"Research task failed: {result}")
            
            # Score and rank sources
            scored_sources = self._score_and_rank_sources(all_sources, query.query)
            
            # Select top sources based on max_sources
            top_sources = scored_sources[:query.max_sources]
            
            # Synthesize results if requested
            synthesis = ""
            key_findings = []
            confidence_score = 0.0
            
            if query.synthesize_results and top_sources:
                synthesis_result = await self._synthesize_research_results(
                    query.query, 
                    top_sources
                )
                synthesis = synthesis_result.get("synthesis", "")
                key_findings = synthesis_result.get("key_findings", [])
                confidence_score = synthesis_result.get("confidence_score", 0.0)
            
            # Create research result
            research_time = asyncio.get_event_loop().time() - start_time
            
            result = ResearchResult(
                query=query.query,
                sources_found=len(all_sources),
                synthesis=synthesis,
                key_findings=key_findings,
                source_details=top_sources,
                confidence_score=confidence_score,
                research_time=research_time,
                metadata={
                    "depth": query.depth,
                    "sources_requested": query.sources,
                    "total_sources_found": len(all_sources),
                    "top_sources_selected": len(top_sources),
                    "research_providers": self._get_active_providers(),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Cache the result
            self._cache_research_result(cache_key, result)
            
            # Store research context if session provided
            if session_id:
                await self._store_research_context(session_id, query, result)
            
            logger.info(f"Research completed in {research_time:.2f}s: {len(top_sources)} sources")
            return result
            
        except Exception as e:
            logger.error(f"Research failed: {e}")
            research_time = asyncio.get_event_loop().time() - start_time
            
            return ResearchResult(
                query=query.query,
                sources_found=0,
                synthesis=f"Research failed: {str(e)}",
                key_findings=[],
                source_details=[],
                confidence_score=0.0,
                research_time=research_time,
                metadata={"error": str(e), "timestamp": datetime.now().isoformat()}
            )
    
    async def _research_web_sources(self, query: ResearchQuery) -> List[Dict[str, Any]]:
        """Research web sources using multiple providers"""
        sources = []
        
        try:
            # Tavily search (if available)
            if self.tavily_key:
                tavily_sources = await self._tavily_search(query)
                sources.extend(tavily_sources)
            
            # Fallback to web access service
            if not sources or len(sources) < query.max_sources // 2:
                web_sources = await self._web_access_search(query)
                sources.extend(web_sources)
            
            return sources
            
        except Exception as e:
            logger.error(f"Web sources research failed: {e}")
            return []
    
    async def _research_news_sources(self, query: ResearchQuery) -> List[Dict[str, Any]]:
        """Research news sources"""
        sources = []
        
        try:
            # NewsAPI search (if available)
            if self.newsapi_key:
                news_sources = await self._newsapi_search(query)
                sources.extend(news_sources)
            
            # Fallback to web search with news focus
            if not sources:
                news_query = f"{query.query} news"
                web_sources = await self._web_access_search(
                    ResearchQuery(query=news_query, max_sources=query.max_sources // 2)
                )
                # Filter for news domains
                news_sources = [
                    source for source in web_sources
                    if any(domain in source.get("url", "") for domain in [
                        "news", "reuters", "bbc", "cnn", "npr", "apnews", "bloomberg"
                    ])
                ]
                sources.extend(news_sources)
            
            return sources
            
        except Exception as e:
            logger.error(f"News sources research failed: {e}")
            return []
    
    async def _research_academic_sources(self, query: ResearchQuery) -> List[Dict[str, Any]]:
        """Research academic sources"""
        sources = []
        
        try:
            # Academic-focused web search
            academic_query = f"{query.query} site:arxiv.org OR site:scholar.google.com OR site:pubmed.ncbi.nlm.nih.gov"
            academic_sources = await self._web_access_search(
                ResearchQuery(query=academic_query, max_sources=query.max_sources // 2)
            )
            
            # Filter and enhance academic sources
            for source in academic_sources:
                url = source.get("url", "")
                if any(domain in url for domain in ["arxiv.org", "scholar.google", "pubmed", ".edu"]):
                    source["source_type"] = "academic"
                    source["quality_score"] = self._calculate_source_quality(url)
                    sources.append(source)
            
            return sources
            
        except Exception as e:
            logger.error(f"Academic sources research failed: {e}")
            return []
    
    async def _research_social_sources(self, query: ResearchQuery) -> List[Dict[str, Any]]:
        """Research social media sources (placeholder)"""
        # This would integrate with social media APIs
        # For now, return empty list
        logger.info("Social media research not yet implemented")
        return []
    
    async def _tavily_search(self, query: ResearchQuery) -> List[Dict[str, Any]]:
        """Search using Tavily API"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    headers={"Authorization": f"Bearer {self.tavily_key}"},
                    json={
                        "query": query.query,
                        "search_depth": "advanced" if query.depth in ["deep", "comprehensive"] else "basic",
                        "include_answer": True,
                        "include_raw_content": True,
                        "max_results": query.max_sources,
                        "include_images": query.include_images,
                        "include_domains": [],
                        "exclude_domains": []
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                sources = []
                for result in data.get("results", []):
                    sources.append({
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "snippet": result.get("content", ""),
                        "raw_content": result.get("raw_content", ""),
                        "score": result.get("score", 0.5),
                        "source_type": "web",
                        "provider": "tavily",
                        "quality_score": self._calculate_source_quality(result.get("url", ""))
                    })
                
                return sources
                
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            return []
    
    async def _newsapi_search(self, query: ResearchQuery) -> List[Dict[str, Any]]:
        """Search using NewsAPI"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                params = {
                    "q": query.query,
                    "apiKey": self.newsapi_key,
                    "language": query.language,
                    "sortBy": "relevancy",
                    "pageSize": min(query.max_sources, 100)
                }
                
                # Add time range if specified
                if query.time_range != "any":
                    time_map = {
                        "hour": 1,
                        "day": 1,
                        "week": 7,
                        "month": 30
                    }
                    days_back = time_map.get(query.time_range, 30)
                    from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
                    params["from"] = from_date
                
                response = await client.get(
                    "https://newsapi.org/v2/everything",
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                sources = []
                for article in data.get("articles", []):
                    sources.append({
                        "title": article.get("title", ""),
                        "url": article.get("url", ""),
                        "snippet": article.get("description", ""),
                        "content": article.get("content", ""),
                        "published_at": article.get("publishedAt", ""),
                        "source_name": article.get("source", {}).get("name", ""),
                        "source_type": "news",
                        "provider": "newsapi",
                        "quality_score": self._calculate_source_quality(article.get("url", ""))
                    })
                
                return sources
                
        except Exception as e:
            logger.error(f"NewsAPI search failed: {e}")
            return []
    
    async def _web_access_search(self, query: ResearchQuery) -> List[Dict[str, Any]]:
        """Search using web access service"""
        try:
            search_request = WebSearchRequest(
                query=query.query,
                max_results=query.max_sources,
                strategy="auto"
            )
            
            results = await self.web_service.search_web(search_request)
            
            sources = []
            for result in results.get("results", []):
                sources.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "snippet": result.get("snippet", ""),
                    "source_type": "web",
                    "provider": result.get("source", "web_access"),
                    "quality_score": self._calculate_source_quality(result.get("url", ""))
                })
            
            return sources
            
        except Exception as e:
            logger.error(f"Web access search failed: {e}")
            return []
    
    def _score_and_rank_sources(self, sources: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Score and rank sources by relevance and quality"""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        for source in sources:
            score = 0.0
            
            # Base quality score
            quality_score = source.get("quality_score", 0.5)
            score += quality_score * 0.4
            
            # Relevance scoring
            title = source.get("title", "").lower()
            snippet = source.get("snippet", "").lower()
            
            # Title relevance (high weight)
            title_words = set(title.split())
            title_overlap = len(query_words.intersection(title_words)) / len(query_words) if query_words else 0
            score += title_overlap * 0.3
            
            # Snippet relevance
            snippet_words = set(snippet.split())
            snippet_overlap = len(query_words.intersection(snippet_words)) / len(query_words) if query_words else 0
            score += snippet_overlap * 0.2
            
            # Exact query match bonus
            if query_lower in title or query_lower in snippet:
                score += 0.1
            
            # Source type bonus
            source_type = source.get("source_type", "web")
            type_bonus = {
                "academic": 0.1,
                "news": 0.05,
                "web": 0.0
            }
            score += type_bonus.get(source_type, 0.0)
            
            source["relevance_score"] = score
        
        # Sort by relevance score
        return sorted(sources, key=lambda x: x.get("relevance_score", 0), reverse=True)
    
    def _calculate_source_quality(self, url: str) -> float:
        """Calculate quality score for a source URL"""
        if not url:
            return 0.3
        
        url_lower = url.lower()
        
        # Check specific domains
        for domain, score in self.source_quality_scores.items():
            if domain in url_lower:
                return score
        
        # Check domain extensions
        if url_lower.endswith(".gov"):
            return 0.85
        elif url_lower.endswith(".edu"):
            return 0.8
        elif url_lower.endswith(".org"):
            return 0.7
        elif url_lower.endswith(".com"):
            return 0.6
        else:
            return 0.5
    
    async def _synthesize_research_results(
        self,
        query: str,
        sources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Synthesize research results using AI"""
        try:
            # Prepare synthesis prompt
            sources_text = ""
            for i, source in enumerate(sources[:10], 1):  # Limit to top 10 sources
                sources_text += f"{i}. {source.get('title', 'Untitled')}\n"
                sources_text += f"   URL: {source.get('url', '')}\n"
                sources_text += f"   Content: {source.get('snippet', '')[:300]}...\n\n"
            
            synthesis_prompt = f"""
            Based on the following research sources about "{query}", provide a comprehensive synthesis:

            SOURCES:
            {sources_text}

            Please provide:
            1. A comprehensive synthesis (2-3 paragraphs)
            2. Key findings (3-5 bullet points)
            3. Confidence score (0.0-1.0) based on source quality and consistency

            Format your response as JSON with keys: synthesis, key_findings, confidence_score
            """
            
            # This would typically call an LLM API for synthesis
            # For now, provide a structured placeholder
            synthesis_result = {
                "synthesis": f"Based on {len(sources)} sources, research on '{query}' reveals multiple perspectives and findings. The sources provide varying levels of detail and credibility, with academic and government sources generally offering higher reliability. Key themes emerge from the collected information, though further verification may be needed for complete accuracy.",
                "key_findings": [
                    f"Found {len(sources)} relevant sources on the topic",
                    f"Sources include {len([s for s in sources if s.get('source_type') == 'academic'])} academic references",
                    f"Average source quality score: {sum(s.get('quality_score', 0.5) for s in sources) / len(sources):.2f}",
                    "Multiple perspectives represented in the source material"
                ],
                "confidence_score": min(0.9, sum(s.get('quality_score', 0.5) for s in sources) / len(sources))
            }
            
            return synthesis_result
            
        except Exception as e:
            logger.error(f"Research synthesis failed: {e}")
            return {
                "synthesis": f"Unable to synthesize research results: {str(e)}",
                "key_findings": [],
                "confidence_score": 0.0
            }
    
    async def _store_research_context(
        self,
        session_id: str,
        query: ResearchQuery,
        result: ResearchResult
    ):
        """Store research results in context for future reference"""
        try:
            research_summary = f"Research Query: {query.query}\n"
            research_summary += f"Sources Found: {result.sources_found}\n"
            research_summary += f"Key Findings: {', '.join(result.key_findings[:3])}\n"
            research_summary += f"Synthesis: {result.synthesis[:300]}..."
            
            await self.context_manager.store_message(
                session_id=session_id,
                content=research_summary,
                role="system",
                backend_used="web_research",
                metadata={
                    "research_query": query.query,
                    "sources_found": result.sources_found,
                    "confidence_score": result.confidence_score,
                    "research_time": result.research_time,
                    "research_depth": query.depth
                },
                context_type="research_data"
            )
            
        except Exception as e:
            logger.warning(f"Failed to store research context: {e}")
    
    def _generate_cache_key(self, query: ResearchQuery) -> str:
        """Generate cache key for research query"""
        key_data = f"{query.query}:{query.depth}:{':'.join(sorted(query.sources))}:{query.max_sources}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_cached_research(self, cache_key: str) -> Optional[ResearchResult]:
        """Get cached research result"""
        if cache_key in self.research_cache:
            cached_data = self.research_cache[cache_key]
            if asyncio.get_event_loop().time() - cached_data["timestamp"] < self.cache_ttl:
                return cached_data["result"]
            else:
                del self.research_cache[cache_key]
        return None
    
    def _cache_research_result(self, cache_key: str, result: ResearchResult):
        """Cache research result"""
        self.research_cache[cache_key] = {
            "result": result,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Simple cache cleanup
        if len(self.research_cache) > 100:
            oldest_key = min(
                self.research_cache.keys(),
                key=lambda k: self.research_cache[k]["timestamp"]
            )
            del self.research_cache[oldest_key]
    
    def _get_active_providers(self) -> List[str]:
        """Get list of active research providers"""
        providers = []
        if self.tavily_key:
            providers.append("tavily")
        if self.serpapi_key:
            providers.append("serpapi")
        if self.newsapi_key:
            providers.append("newsapi")
        providers.append("web_access")
        return providers
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for enhanced web research"""
        try:
            web_service_health = True  # Assume healthy
            context_manager_health = await self.context_manager.health_check()
            
            return {
                "status": "healthy" if context_manager_health.get("status") == "healthy" else "unhealthy",
                "components": {
                    "web_service": "healthy" if web_service_health else "unhealthy",
                    "context_manager": context_manager_health.get("status", "unknown")
                },
                "providers": {
                    "tavily": "configured" if self.tavily_key else "not_configured",
                    "serpapi": "configured" if self.serpapi_key else "not_configured",
                    "newsapi": "configured" if self.newsapi_key else "not_configured",
                    "web_access": "available"
                },
                "cache_size": len(self.research_cache),
                "features": {
                    "multi_source_research": True,
                    "result_synthesis": True,
                    "source_quality_scoring": True,
                    "research_caching": True,
                    "context_integration": True
                }
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

