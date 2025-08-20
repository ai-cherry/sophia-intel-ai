"""
SOPHIA Research Master
Orchestrates multi-API research operations and manages research workflows.
"""

import os
import logging
from typing import Dict, List, Optional, Any
import asyncio
from datetime import datetime, timezone

from .api_manager import SOPHIAAPIManager
from .ultimate_model_router import UltimateModelRouter
from .mcp_client import SOPHIAMCPClient

logger = logging.getLogger(__name__)

class SOPHIAResearchMaster:
    """
    Master class for research operations.
    Orchestrates multi-source research, summarization, and knowledge synthesis.
    """
    
    def __init__(self):
        """Initialize research master with required components."""
        self.api_manager = SOPHIAAPIManager()
        self.model_router = UltimateModelRouter()
        self.mcp_client = None  # Will be initialized when needed
        
        # Research configuration
        self.default_sources = ["serper", "tavily", "zenrows"]
        self.max_concurrent_searches = 5
        self.default_max_results = 10
        
        logger.info("Initialized SOPHIAResearchMaster")
    
    async def _get_mcp_client(self) -> SOPHIAMCPClient:
        """Get or create MCP client."""
        if self.mcp_client is None:
            self.mcp_client = SOPHIAMCPClient()
        return self.mcp_client
    
    async def research(
        self,
        query: str,
        sources: Optional[List[str]] = None,
        max_results_per_source: int = None,
        include_summary: bool = True,
        store_results: bool = True
    ) -> Dict[str, Any]:
        """
        Conduct comprehensive research on a topic.
        
        Args:
            query: Research query/topic
            sources: List of sources to search (defaults to configured sources)
            max_results_per_source: Maximum results per source
            include_summary: Whether to generate AI summary
            store_results: Whether to store results in memory
            
        Returns:
            Research results with sources and optional summary
        """
        try:
            logger.info(f"Starting research for query: {query}")
            
            # Use MCP client for research if available
            mcp_client = await self._get_mcp_client()
            
            try:
                # Try MCP server first
                result = await mcp_client.conduct_research(
                    query=query,
                    sources=sources or self.default_sources,
                    max_results_per_source=max_results_per_source or self.default_max_results,
                    summarize=include_summary
                )
                
                # Store in memory if requested
                if store_results:
                    await self._store_research_memory(query, result)
                
                return result
                
            except Exception as mcp_error:
                logger.warning(f"MCP research failed, falling back to direct API: {mcp_error}")
                
                # Fallback to direct API calls
                return await self._direct_research(
                    query, sources, max_results_per_source, include_summary, store_results
                )
                
        except Exception as e:
            logger.error(f"Research failed: {e}")
            raise
    
    async def deep_research(
        self,
        topic: str,
        research_depth: str = "standard",
        focus_areas: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        store_results: bool = True
    ) -> Dict[str, Any]:
        """
        Conduct comprehensive deep research with multiple query variations.
        
        Args:
            topic: Main research topic
            research_depth: Depth level (basic, standard, comprehensive)
            focus_areas: Specific areas to focus on
            exclude_domains: Domains to exclude from results
            store_results: Whether to store results in memory
            
        Returns:
            Comprehensive research results
        """
        try:
            logger.info(f"Starting deep research for topic: {topic}")
            
            mcp_client = await self._get_mcp_client()
            
            try:
                # Try MCP server first
                result = await mcp_client.conduct_deep_research(
                    topic=topic,
                    research_depth=research_depth,
                    focus_areas=focus_areas,
                    exclude_domains=exclude_domains
                )
                
                # Store in memory if requested
                if store_results:
                    await self._store_research_memory(topic, result, memory_type="deep_research")
                
                return result
                
            except Exception as mcp_error:
                logger.warning(f"MCP deep research failed, falling back: {mcp_error}")
                
                # Fallback to multiple standard research calls
                return await self._deep_research_fallback(
                    topic, research_depth, focus_areas, exclude_domains, store_results
                )
                
        except Exception as e:
            logger.error(f"Deep research failed: {e}")
            raise
    
    async def _direct_research(
        self,
        query: str,
        sources: Optional[List[str]],
        max_results_per_source: Optional[int],
        include_summary: bool,
        store_results: bool
    ) -> Dict[str, Any]:
        """Direct API research fallback."""
        try:
            sources = sources or self.default_sources
            max_results = max_results_per_source or self.default_max_results
            
            # Prepare search tasks
            search_tasks = []
            
            if "serper" in sources:
                search_tasks.append(self._search_serper(query, max_results))
            
            if "tavily" in sources:
                search_tasks.append(self._search_tavily(query, max_results))
            
            if "zenrows" in sources:
                search_tasks.append(self._search_zenrows(query, max_results))
            
            # Execute searches concurrently
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Combine and process results
            all_sources = []
            for result in search_results:
                if isinstance(result, list):
                    all_sources.extend(result)
                elif isinstance(result, Exception):
                    logger.error(f"Search task failed: {result}")
            
            # Deduplicate by URL
            unique_sources = self._deduplicate_sources(all_sources)
            
            # Generate summary if requested
            summary = None
            if include_summary and unique_sources:
                summary = await self._generate_summary(query, unique_sources)
            
            result = {
                "query": query,
                "sources": unique_sources,
                "summary": summary,
                "total_sources": len(unique_sources),
                "research_id": self._generate_research_id(),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Store in memory if requested
            if store_results:
                await self._store_research_memory(query, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Direct research failed: {e}")
            raise
    
    async def _deep_research_fallback(
        self,
        topic: str,
        research_depth: str,
        focus_areas: Optional[List[str]],
        exclude_domains: Optional[List[str]],
        store_results: bool
    ) -> Dict[str, Any]:
        """Deep research fallback using multiple queries."""
        try:
            # Generate query variations
            queries = [topic]
            
            if focus_areas:
                for area in focus_areas:
                    queries.append(f"{topic} {area}")
            
            # Adjust depth
            max_results = {
                "basic": 5,
                "standard": 10,
                "comprehensive": 20
            }.get(research_depth, 10)
            
            # Conduct research for each query
            all_results = []
            for query in queries:
                try:
                    result = await self._direct_research(
                        query, self.default_sources, max_results, False, False
                    )
                    all_results.extend(result.get("sources", []))
                except Exception as e:
                    logger.error(f"Query research failed for '{query}': {e}")
            
            # Deduplicate and filter
            unique_sources = self._deduplicate_sources(all_results)
            
            if exclude_domains:
                unique_sources = [
                    source for source in unique_sources
                    if not any(domain in source.get("url", "") for domain in exclude_domains)
                ]
            
            # Generate comprehensive summary
            summary = await self._generate_comprehensive_summary(topic, unique_sources)
            
            result = {
                "query": topic,
                "sources": unique_sources,
                "summary": summary,
                "total_sources": len(unique_sources),
                "research_id": self._generate_research_id(),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "research_type": "deep_research",
                "research_depth": research_depth
            }
            
            if store_results:
                await self._store_research_memory(topic, result, memory_type="deep_research")
            
            return result
            
        except Exception as e:
            logger.error(f"Deep research fallback failed: {e}")
            raise
    
    async def _search_serper(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search using Serper API."""
        # TODO: Implement direct Serper API calls
        logger.warning("Direct Serper search not implemented")
        return []
    
    async def _search_tavily(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search using Tavily API."""
        # TODO: Implement direct Tavily API calls
        logger.warning("Direct Tavily search not implemented")
        return []
    
    async def _search_zenrows(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search using ZenRows API."""
        # TODO: Implement direct ZenRows API calls
        logger.warning("Direct ZenRows search not implemented")
        return []
    
    def _deduplicate_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate sources by URL."""
        seen_urls = set()
        unique_sources = []
        
        for source in sources:
            url = source.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_sources.append(source)
        
        return unique_sources
    
    async def _generate_summary(self, query: str, sources: List[Dict[str, Any]]) -> str:
        """Generate research summary using approved models."""
        try:
            # Prepare content for summarization
            content = f"Research Query: {query}\n\n"
            for i, source in enumerate(sources[:10], 1):
                content += f"{i}. {source.get('title', 'No title')}\n"
                content += f"   URL: {source.get('url', 'No URL')}\n"
                content += f"   Summary: {source.get('snippet', 'No summary')}\n\n"
            
            # Use approved model for summarization
            model_config = self.model_router.select_model("research")
            
            summary_prompt = f"""
Analyze the following research results and provide a comprehensive summary:

{content}

Please provide:
1. Key findings and insights
2. Main themes and patterns
3. Notable sources and their contributions
4. Conclusions and implications

Summary:
"""
            
            summary = await self.model_router.call_model(
                model_config,
                summary_prompt,
                temperature=0.3,
                max_tokens=2048
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return "Summary generation failed"
    
    async def _generate_comprehensive_summary(self, topic: str, sources: List[Dict[str, Any]]) -> str:
        """Generate comprehensive summary for deep research."""
        try:
            # Prepare detailed content
            content = f"Deep Research Topic: {topic}\n\n"
            content += f"Total Sources Analyzed: {len(sources)}\n\n"
            
            for i, source in enumerate(sources[:15], 1):
                content += f"{i}. {source.get('title', 'No title')}\n"
                content += f"   Source: {source.get('name', 'Unknown').upper()}\n"
                content += f"   URL: {source.get('url', 'No URL')}\n"
                content += f"   Content: {source.get('snippet', 'No content')}\n\n"
            
            model_config = self.model_router.select_model("research")
            
            summary_prompt = f"""
Conduct a comprehensive analysis of the following research data:

{content}

Please provide a detailed research summary including:

1. EXECUTIVE SUMMARY
   - Key findings and main insights
   - Primary conclusions

2. DETAILED ANALYSIS
   - Major themes and patterns identified
   - Supporting evidence from sources

3. SOURCE EVALUATION
   - Quality and credibility of sources
   - Most valuable sources and why

4. IMPLICATIONS AND RECOMMENDATIONS
   - Practical implications of findings
   - Areas requiring further research

5. CONCLUSION
   - Summary of key takeaways
   - Overall assessment

Research Summary:
"""
            
            summary = await self.model_router.call_model(
                model_config,
                summary_prompt,
                temperature=0.2,
                max_tokens=4096
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Comprehensive summary generation failed: {e}")
            return "Comprehensive summary generation failed"
    
    async def _store_research_memory(
        self,
        query: str,
        result: Dict[str, Any],
        memory_type: str = "research"
    ):
        """Store research results in memory."""
        try:
            mcp_client = await self._get_mcp_client()
            
            # Store main research result
            content = f"Research Query: {query}\n"
            content += f"Total Sources: {result.get('total_sources', 0)}\n"
            if result.get('summary'):
                content += f"Summary: {result['summary'][:500]}...\n"
            
            await mcp_client.store_memory(
                content=content,
                memory_type=memory_type,
                metadata={
                    "research_id": result.get("research_id"),
                    "query": query,
                    "source_count": result.get("total_sources", 0),
                    "created_at": result.get("created_at")
                }
            )
            
            logger.info(f"Stored research memory for query: {query}")
            
        except Exception as e:
            logger.error(f"Failed to store research memory: {e}")
    
    def _generate_research_id(self) -> str:
        """Generate unique research ID."""
        import uuid
        return str(uuid.uuid4())
    
    async def get_research_history(
        self,
        limit: int = 10,
        memory_type: str = "research"
    ) -> List[Dict[str, Any]]:
        """Get research history from memory."""
        try:
            mcp_client = await self._get_mcp_client()
            
            result = await mcp_client.retrieve_memories(
                query="research",
                memory_type=memory_type,
                limit=limit
            )
            
            return result.get("memories", [])
            
        except Exception as e:
            logger.error(f"Failed to get research history: {e}")
            return []
    
    async def search_research_memory(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search previous research results."""
        try:
            mcp_client = await self._get_mcp_client()
            
            result = await mcp_client.retrieve_memories(
                query=query,
                memory_type="research",
                limit=limit
            )
            
            return result.get("memories", [])
            
        except Exception as e:
            logger.error(f"Failed to search research memory: {e}")
            return []
    
    async def close(self):
        """Close connections."""
        if self.mcp_client:
            await self.mcp_client.close()

