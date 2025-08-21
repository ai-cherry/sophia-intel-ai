"""
Simplified Research Server - Direct API calls without model router dependency
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import asyncio
import httpx
import uuid

logger = logging.getLogger(__name__)

# Pydantic models
class ResearchRequest(BaseModel):
    query: str
    sources: Optional[List[str]] = ["serper", "tavily", "apify", "zenrows"]
    max_results_per_source: Optional[int] = 5
    include_content: Optional[bool] = True
    summarize: Optional[bool] = True

class ResearchSource(BaseModel):
    name: str
    url: str
    title: str
    snippet: str
    content: Optional[str] = None
    relevance_score: Optional[float] = None
    published_date: Optional[str] = None

class ResearchResult(BaseModel):
    query: str
    sources: List[ResearchSource]
    summary: Optional[str] = None
    total_sources: int
    research_id: str
    created_at: datetime

# Create router
router = APIRouter()

# Research storage
research_store: Dict[str, ResearchResult] = {}

def generate_research_id() -> str:
    """Generate unique research ID."""
    return str(uuid.uuid4())

async def search_serper(query: str, api_key: str, max_results: int = 5) -> List[ResearchSource]:
    """Search using Serper API."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": api_key},
                json={
                    "q": query,
                    "num": max_results
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                sources = []
                
                for result in data.get("organic", []):
                    sources.append(ResearchSource(
                        name="serper",
                        url=result.get("link", ""),
                        title=result.get("title", ""),
                        snippet=result.get("snippet", ""),
                        relevance_score=0.8
                    ))
                
                logger.info(f"Serper returned {len(sources)} results for query: {query}")
                return sources
            else:
                logger.error(f"Serper API error: {response.status_code} - {response.text}")
                return []
                
    except Exception as e:
        logger.error(f"Serper search failed: {e}")
        return []

async def search_tavily(query: str, api_key: str, max_results: int = 5) -> List[ResearchSource]:
    """Search using Tavily API."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.tavily.com/search",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "query": query,
                    "max_results": max_results,
                    "include_answer": True,
                    "include_raw_content": False
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                sources = []
                
                for result in data.get("results", []):
                    sources.append(ResearchSource(
                        name="tavily",
                        url=result.get("url", ""),
                        title=result.get("title", ""),
                        snippet=result.get("content", ""),
                        relevance_score=result.get("score", 0.7)
                    ))
                
                logger.info(f"Tavily returned {len(sources)} results for query: {query}")
                return sources
            else:
                logger.error(f"Tavily API error: {response.status_code} - {response.text}")
                return []
                
    except Exception as e:
        logger.error(f"Tavily search failed: {e}")
        return []

async def search_apify(query: str, api_key: str, max_results: int = 5) -> List[ResearchSource]:
    """Search using Apify Google Search Scraper."""
    try:
        async with httpx.AsyncClient() as client:
            # Start Apify actor run
            response = await client.post(
                "https://api.apify.com/v2/acts/apify~google-search-scraper/runs",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "queries": [query],
                    "resultsPerPage": max_results,
                    "countryCode": "US",
                    "languageCode": "en",
                    "mobileResults": False,
                    "includeUnfilteredResults": False
                },
                timeout=60.0
            )
            
            if response.status_code == 201:
                run_data = response.json()
                run_id = run_data["data"]["id"]
                
                # Wait for completion and get results
                await asyncio.sleep(5)  # Wait for processing
                
                results_response = await client.get(
                    f"https://api.apify.com/v2/acts/apify~google-search-scraper/runs/{run_id}/dataset/items",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=30.0
                )
                
                if results_response.status_code == 200:
                    results = results_response.json()
                    sources = []
                    
                    for result in results:
                        if result.get("organicResults"):
                            for organic in result["organicResults"][:max_results]:
                                sources.append(ResearchSource(
                                    name="apify",
                                    url=organic.get("url", ""),
                                    title=organic.get("title", ""),
                                    snippet=organic.get("description", ""),
                                    relevance_score=0.75
                                ))
                    
                    logger.info(f"Apify returned {len(sources)} results for query: {query}")
                    return sources
                else:
                    logger.error(f"Apify results error: {results_response.status_code}")
                    return []
            else:
                logger.error(f"Apify API error: {response.status_code} - {response.text}")
                return []
                
    except Exception as e:
        logger.error(f"Apify search failed: {e}")
        return []

async def search_zenrows(query: str, api_key: str, max_results: int = 5) -> List[ResearchSource]:
    """Search using ZenRows web scraping for Google results."""
    try:
        async with httpx.AsyncClient() as client:
            # Use ZenRows to scrape Google search results
            google_url = f"https://www.google.com/search?q={query}&num={max_results}"
            
            response = await client.get(
                "https://api.zenrows.com/v1/",
                params={
                    "url": google_url,
                    "apikey": api_key,
                    "js_render": "true",
                    "premium_proxy": "true",
                    "proxy_country": "US"
                },
                timeout=45.0
            )
            
            if response.status_code == 200:
                # Parse HTML content for search results
                html_content = response.text
                sources = []
                
                # Simple regex parsing for Google results
                import re
                
                # Extract search result patterns
                title_pattern = r'<h3[^>]*>([^<]+)</h3>'
                url_pattern = r'<a[^>]*href="([^"]*)"[^>]*>'
                snippet_pattern = r'<span[^>]*>([^<]{50,200})</span>'
                
                titles = re.findall(title_pattern, html_content)
                urls = re.findall(url_pattern, html_content)
                snippets = re.findall(snippet_pattern, html_content)
                
                # Filter valid URLs (not Google internal)
                valid_results = []
                for i, url in enumerate(urls):
                    if not any(x in url for x in ['google.com', 'youtube.com', 'maps.google']):
                        if i < len(titles) and i < len(snippets):
                            valid_results.append({
                                'title': titles[i] if i < len(titles) else 'No title',
                                'url': url,
                                'snippet': snippets[i] if i < len(snippets) else 'No description'
                            })
                
                # Create sources from valid results
                for result in valid_results[:max_results]:
                    sources.append(ResearchSource(
                        name="zenrows",
                        url=result['url'],
                        title=result['title'],
                        snippet=result['snippet'],
                        relevance_score=0.7
                    ))
                
                logger.info(f"ZenRows returned {len(sources)} results for query: {query}")
                return sources
            else:
                logger.error(f"ZenRows API error: {response.status_code} - {response.text}")
                return []
                
    except Exception as e:
        logger.error(f"ZenRows search failed: {e}")
        return []

def generate_simple_summary(query: str, sources: List[ResearchSource]) -> str:
    """Generate a simple summary without LLM dependency."""
    if not sources:
        return "No sources found for the query."
    
    # Extract key information
    key_info = []
    for source in sources[:3]:  # Top 3 sources
        if source.snippet:
            key_info.append(f"• {source.snippet[:200]}...")
    
    summary = f"Research Summary for '{query}':\n\n"
    summary += f"Found {len(sources)} relevant sources:\n\n"
    summary += "\n".join(key_info)
    summary += f"\n\nTop source: {sources[0].title} ({sources[0].url})"
    
    return summary

@router.post("/search", response_model=ResearchResult)
async def conduct_research(request: ResearchRequest):
    """
    Conduct research across multiple sources with simplified processing.
    """
    try:
        research_id = generate_research_id()
        all_sources = []
        
        # Get API keys
        serper_key = os.getenv("SERPER_API_KEY")
        tavily_key = os.getenv("TAVILY_API_KEY")
        
        logger.info(f"Starting research for query: {request.query}")
        logger.info(f"API keys available - Serper: {'Yes' if serper_key else 'No'}, Tavily: {'Yes' if tavily_key else 'No'}")
        
        # Prepare search tasks
        search_tasks = []
        
        if "serper" in request.sources and serper_key:
            search_tasks.append(search_serper(request.query, serper_key, request.max_results_per_source))
        
        if "tavily" in request.sources and tavily_key:
            search_tasks.append(search_tavily(request.query, tavily_key, request.max_results_per_source))
        
        # Execute searches concurrently
        if search_tasks:
            logger.info(f"Executing {len(search_tasks)} search tasks")
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Combine results
            for result in search_results:
                if isinstance(result, list):
                    all_sources.extend(result)
                    logger.info(f"Added {len(result)} sources from search task")
                elif isinstance(result, Exception):
                    logger.error(f"Search task failed: {result}")
        
        # Deduplicate by URL
        seen_urls = set()
        unique_sources = []
        for source in all_sources:
            if source.url not in seen_urls:
                seen_urls.add(source.url)
                unique_sources.append(source)
        
        logger.info(f"After deduplication: {len(unique_sources)} unique sources")
        
        # Generate simple summary
        summary = None
        if request.summarize and unique_sources:
            try:
                summary = generate_simple_summary(request.query, unique_sources)
                logger.info("Generated simple summary successfully")
            except Exception as e:
                logger.error(f"Summary generation failed: {e}")
                summary = f"Summary generation failed: {str(e)}"
        
        # Create research result
        research_result = ResearchResult(
            query=request.query,
            sources=unique_sources,
            summary=summary,
            total_sources=len(unique_sources),
            research_id=research_id,
            created_at=datetime.now(timezone.utc)
        )
        
        # Store research result
        research_store[research_id] = research_result
        
        logger.info(f"Completed research {research_id} with {len(unique_sources)} sources")
        return research_result
        
    except Exception as e:
        logger.error(f"Research failed: {e}")
        raise HTTPException(status_code=500, detail=f"Research failed: {str(e)}")

@router.get("/research/{research_id}", response_model=ResearchResult)
async def get_research_result(research_id: str):
    """Get stored research result by ID."""
    if research_id not in research_store:
        raise HTTPException(status_code=404, detail="Research result not found")
    
    return research_store[research_id]

@router.get("/health")
async def research_server_health():
    """Health check for research server."""
    api_keys_status = {
        "serper": "configured" if os.getenv("SERPER_API_KEY") else "missing",
        "tavily": "configured" if os.getenv("TAVILY_API_KEY") else "missing",
        "zenrows": "configured" if os.getenv("ZENROWS_API_KEY") else "missing"
    }
    
    return {
        "status": "healthy",
        "service": "sophia-mcp-research-simple",
        "version": "1.0.0",
        "api_keys": api_keys_status,
        "capabilities": [
            "web_search",
            "multi_source_search",
            "simple_summarization",
            "source_deduplication"
        ]
    }

