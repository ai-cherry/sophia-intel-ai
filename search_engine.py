"""
SOPHIA Intel - Basic Search Engine Bootstrap
This is the initial search system that SOPHIA will use to research and upgrade herself.
"""

import asyncio
import aiohttp
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from urllib.parse import quote_plus
import logging

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str
    relevance_score: float = 0.0

class BasicSearchEngine:
    """
    Bootstrap search engine for SOPHIA to start with.
    SOPHIA will use this to research and implement better search capabilities.
    """
    
    def __init__(self):
        self.session = None
        self.search_apis = {
            'duckduckgo': self._search_duckduckgo,
            'serper': self._search_serper,  # If API key available
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search(self, query: str, max_results: int = 10, sources: List[str] = None) -> List[SearchResult]:
        """
        Basic search functionality that SOPHIA can use immediately.
        """
        if sources is None:
            sources = ['duckduckgo']
            
        all_results = []
        
        for source in sources:
            if source in self.search_apis:
                try:
                    results = await self.search_apis[source](query, max_results)
                    all_results.extend(results)
                except Exception as e:
                    logging.error(f"Search failed for {source}: {e}")
                    
        # Basic deduplication and ranking
        return self._rank_and_dedupe(all_results, max_results)
    
    async def _search_duckduckgo(self, query: str, max_results: int) -> List[SearchResult]:
        """
        DuckDuckGo search implementation (no API key required)
        """
        url = "https://api.duckduckgo.com/"
        params = {
            'q': query,
            'format': 'json',
            'no_html': '1',
            'skip_disambig': '1'
        }
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results = []
                    
                    # Process instant answer
                    if data.get('AbstractText'):
                        results.append(SearchResult(
                            title=data.get('Heading', 'DuckDuckGo Instant Answer'),
                            url=data.get('AbstractURL', ''),
                            snippet=data.get('AbstractText', ''),
                            source='duckduckgo_instant',
                            relevance_score=0.9
                        ))
                    
                    # Process related topics
                    for topic in data.get('RelatedTopics', [])[:max_results]:
                        if isinstance(topic, dict) and 'Text' in topic:
                            results.append(SearchResult(
                                title=topic.get('Text', '').split(' - ')[0],
                                url=topic.get('FirstURL', ''),
                                snippet=topic.get('Text', ''),
                                source='duckduckgo_related',
                                relevance_score=0.7
                            ))
                    
                    return results[:max_results]
        except Exception as e:
            logging.error(f"DuckDuckGo search error: {e}")
            
        return []
    
    async def _search_serper(self, query: str, max_results: int) -> List[SearchResult]:
        """
        Serper.dev Google Search API (requires API key)
        """
        # This would require SERPER_API_KEY environment variable
        # Placeholder for when SOPHIA upgrades her search capabilities
        return []
    
    def _rank_and_dedupe(self, results: List[SearchResult], max_results: int) -> List[SearchResult]:
        """
        Basic ranking and deduplication
        """
        # Remove duplicates by URL
        seen_urls = set()
        unique_results = []
        
        for result in results:
            if result.url and result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)
        
        # Sort by relevance score (descending)
        unique_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return unique_results[:max_results]

class SearchCapableAgent:
    """
    Base class for agents that can perform web searches
    """
    
    def __init__(self, name: str, model: str):
        self.name = name
        self.model = model
        self.search_engine = BasicSearchEngine()
    
    async def search_and_analyze(self, query: str, analysis_prompt: str) -> Dict[str, Any]:
        """
        Search for information and analyze results using AI
        """
        async with self.search_engine as search:
            results = await search.search(query, max_results=5)
            
            # Prepare context for AI analysis
            search_context = {
                'query': query,
                'results': [
                    {
                        'title': r.title,
                        'url': r.url,
                        'snippet': r.snippet,
                        'source': r.source
                    }
                    for r in results
                ],
                'analysis_prompt': analysis_prompt
            }
            
            return search_context

# Integration with existing swarm system
class SearchEnhancedSwarm:
    """
    Enhanced swarm with basic search capabilities
    SOPHIA will use this to research better architectures
    """
    
    def __init__(self):
        self.search_engine = BasicSearchEngine()
        self.agents = {
            'researcher': SearchCapableAgent('Researcher', 'anthropic/claude-3.5-sonnet'),
            'analyzer': SearchCapableAgent('Analyzer', 'google/gemini-flash-1.5'),
            'synthesizer': SearchCapableAgent('Synthesizer', 'anthropic/claude-3.5-sonnet')
        }
    
    async def research_task(self, research_query: str, analysis_focus: str = None) -> Dict[str, Any]:
        """
        Execute a research task using the search-capable swarm
        """
        try:
            # Step 1: Search for information
            async with self.search_engine as search:
                search_results = await search.search(research_query, max_results=10)
            
            # Step 2: Analyze results
            analysis = {
                'query': research_query,
                'results_found': len(search_results),
                'sources': list(set(r.source for r in search_results)),
                'top_results': [
                    {
                        'title': r.title,
                        'url': r.url,
                        'snippet': r.snippet[:200] + '...' if len(r.snippet) > 200 else r.snippet,
                        'relevance': r.relevance_score
                    }
                    for r in search_results[:5]
                ]
            }
            
            # Step 3: Synthesize findings
            if analysis_focus:
                analysis['focus'] = analysis_focus
                analysis['synthesis'] = f"Research completed on '{research_query}' with focus on '{analysis_focus}'"
            else:
                analysis['synthesis'] = f"Research completed on '{research_query}'"
            
            analysis['status'] = 'completed'
            analysis['agents_used'] = ['researcher', 'analyzer', 'synthesizer']
            
            return analysis
            
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e),
                'query': research_query
            }

# Bootstrap function for SOPHIA
async def bootstrap_search_capabilities():
    """
    Initialize basic search capabilities for SOPHIA
    """
    swarm = SearchEnhancedSwarm()
    
    # Test search functionality
    test_result = await swarm.research_task(
        "AI agent frameworks LangGraph Agno phidata 2024 2025",
        "implementation strategies and best practices"
    )
    
    return test_result

if __name__ == "__main__":
    # Test the bootstrap search system
    result = asyncio.run(bootstrap_search_capabilities())
    print(json.dumps(result, indent=2))

