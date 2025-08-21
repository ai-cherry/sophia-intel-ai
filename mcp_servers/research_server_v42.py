"""
SOPHIA Research Server v4.2 - Robust Multi-Source Research with Enhanced Parsing

Enhanced with:
- Robust ZenRows parsing with multiple fallback strategies
- Improved Apify integration with better error handling
- Fault-tolerant summary generation (LLM + extractive fallbacks)
- Comprehensive error handling and logging
- Budget controls and rate limiting
"""

import asyncio
import json
import logging
import os
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SOPHIA Research Server v4.2", version="4.2.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SourceType(Enum):
    """Research source types"""
    SERPER = "serper"
    TAVILY = "tavily"
    ZENROWS = "zenrows"
    APIFY = "apify"

@dataclass
class ResearchSource:
    """Standardized research source"""
    name: str
    url: str
    title: str
    snippet: str
    relevance_score: float = 0.0
    published_date: str = ""
    content: Optional[str] = None

@dataclass
class SummaryResult:
    """Summary generation result"""
    text: str
    confidence: float
    model: str
    method: str  # "llm", "extractive", "fallback"
    sources_used: int

class SearchRequest(BaseModel):
    """Search request model"""
    query: str
    sources: List[str] = ["serper", "tavily"]
    max_results_per_source: int = 3
    include_content: bool = True
    summarize: bool = True

class SearchResponse(BaseModel):
    """Search response model"""
    query: str
    sources: List[Dict[str, Any]]
    summary: Optional[str] = None
    total_sources: int
    execution_time_ms: int
    errors: List[str] = []
    created_at: str

# Budget tracking
DAILY_REQUEST_LIMITS = {
    "serper": int(os.getenv("SERPER_DAILY_LIMIT", "1000")),
    "tavily": int(os.getenv("TAVILY_DAILY_LIMIT", "1000")),
    "zenrows": int(os.getenv("ZENROWS_DAILY_LIMIT", "500")),
    "apify": int(os.getenv("APIFY_DAILY_LIMIT", "300"))
}

request_counts = {source: 0 for source in DAILY_REQUEST_LIMITS.keys()}

def check_budget(source: str) -> bool:
    """Check if source is within daily budget"""
    return request_counts.get(source, 0) < DAILY_REQUEST_LIMITS.get(source, 1000)

def increment_usage(source: str):
    """Increment usage counter for source"""
    request_counts[source] = request_counts.get(source, 0) + 1

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "4.2.0",
        "services": {
            "serper": bool(os.getenv("SERPER_API_KEY")),
            "tavily": bool(os.getenv("TAVILY_API_KEY")),
            "zenrows": bool(os.getenv("ZENROWS_API_KEY")),
            "apify": bool(os.getenv("APIFY_API_TOKEN"))
        },
        "budget_status": {
            source: f"{count}/{limit}" 
            for source, count in request_counts.items() 
            for limit in [DAILY_REQUEST_LIMITS.get(source, 1000)]
        }
    }

@app.post("/search", response_model=SearchResponse)
async def search_endpoint(request: SearchRequest):
    """Enhanced multi-source research endpoint"""
    start_time = time.time()
    errors = []
    all_sources = []
    
    logger.info(f"Research request: {request.query} with sources: {request.sources}")
    
    # Validate sources
    available_sources = []
    for source in request.sources:
        if source in ["serper", "tavily", "zenrows", "apify"]:
            if check_budget(source):
                available_sources.append(source)
            else:
                errors.append(f"Daily budget exceeded for {source}")
        else:
            errors.append(f"Unknown source: {source}")
    
    if not available_sources:
        raise HTTPException(status_code=400, detail="No available sources within budget")
    
    # Execute searches concurrently
    search_tasks = []
    
    for source in available_sources:
        if source == "serper":
            search_tasks.append(search_serper_robust(request.query, request.max_results_per_source))
        elif source == "tavily":
            search_tasks.append(search_tavily_robust(request.query, request.max_results_per_source))
        elif source == "zenrows":
            search_tasks.append(search_zenrows_robust(request.query, request.max_results_per_source))
        elif source == "apify":
            search_tasks.append(search_apify_robust(request.query, request.max_results_per_source))
    
    # Execute all searches concurrently
    search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
    
    # Process results and handle exceptions
    for i, result in enumerate(search_results):
        source = available_sources[i]
        increment_usage(source)
        
        if isinstance(result, Exception):
            errors.append(f"{source}: {str(result)}")
            logger.error(f"{source} search failed: {result}")
        elif isinstance(result, list):
            all_sources.extend(result)
            logger.info(f"{source} returned {len(result)} sources")
        else:
            errors.append(f"{source}: Invalid response format")
    
    # Deduplicate sources by URL
    unique_sources = {}
    for source in all_sources:
        url = source.url
        if url not in unique_sources or source.relevance_score > unique_sources[url].relevance_score:
            unique_sources[url] = source
    
    final_sources = list(unique_sources.values())
    
    # Sort by relevance score
    final_sources.sort(key=lambda x: x.relevance_score, reverse=True)
    
    # Generate summary if requested
    summary = None
    if request.summarize and final_sources:
        try:
            summary_result = await generate_summary_robust(request.query, final_sources)
            summary = summary_result.text
        except Exception as e:
            errors.append(f"Summary generation failed: {str(e)}")
            logger.error(f"Summary generation failed: {e}")
    
    execution_time = int((time.time() - start_time) * 1000)
    
    return SearchResponse(
        query=request.query,
        sources=[asdict(source) for source in final_sources],
        summary=summary,
        total_sources=len(final_sources),
        execution_time_ms=execution_time,
        errors=errors,
        created_at=datetime.utcnow().isoformat() + "Z"
    )

async def search_serper_robust(query: str, max_results: int) -> List[ResearchSource]:
    """Robust Serper search with error handling"""
    try:
        api_key = os.getenv("SERPER_API_KEY")
        if not api_key:
            raise ValueError("SERPER_API_KEY not configured")
        
        url = "https://google.serper.dev/search"
        headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
        payload = {"q": query, "num": max_results}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=15.0)
            response.raise_for_status()
            data = response.json()
            
            sources = []
            organic_results = data.get("organic", [])
            
            for result in organic_results[:max_results]:
                sources.append(ResearchSource(
                    name="serper",
                    url=result.get("link", ""),
                    title=result.get("title", ""),
                    snippet=result.get("snippet", ""),
                    relevance_score=0.8,
                    published_date=result.get("date", "")
                ))
            
            logger.info(f"Serper returned {len(sources)} sources")
            return sources
            
    except Exception as e:
        logger.error(f"Serper search failed: {e}")
        raise

async def search_tavily_robust(query: str, max_results: int) -> List[ResearchSource]:
    """Robust Tavily search with error handling"""
    try:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY not configured")
        
        url = "https://api.tavily.com/search"
        headers = {"Content-Type": "application/json"}
        payload = {
            "api_key": api_key,
            "query": query,
            "search_depth": "advanced",
            "include_answer": False,
            "include_raw_content": True,
            "max_results": max_results
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=20.0)
            response.raise_for_status()
            data = response.json()
            
            sources = []
            results = data.get("results", [])
            
            for result in results[:max_results]:
                sources.append(ResearchSource(
                    name="tavily",
                    url=result.get("url", ""),
                    title=result.get("title", ""),
                    snippet=result.get("content", ""),
                    relevance_score=result.get("score", 0.7),
                    published_date=result.get("published_date", ""),
                    content=result.get("raw_content", "")
                ))
            
            logger.info(f"Tavily returned {len(sources)} sources")
            return sources
            
    except Exception as e:
        logger.error(f"Tavily search failed: {e}")
        raise

async def search_zenrows_robust(query: str, max_results: int) -> List[ResearchSource]:
    """Robust ZenRows search with multiple parsing strategies"""
    try:
        api_key = os.getenv("ZENROWS_API_KEY")
        if not api_key:
            raise ValueError("ZENROWS_API_KEY not configured")
        
        sources = []
        
        # Strategy 1: Google Search with CSS extraction
        try:
            sources.extend(await _zenrows_google_search(query, api_key, max_results))
        except Exception as e:
            logger.warning(f"ZenRows Google search failed: {e}")
        
        # Strategy 2: Specialized scraping based on query
        try:
            await _zenrows_specialized_scraping(query, api_key, sources, max_results)
        except Exception as e:
            logger.warning(f"ZenRows specialized scraping failed: {e}")
        
        # Strategy 3: Fallback to simple HTML parsing
        if not sources:
            try:
                sources.extend(await _zenrows_fallback_search(query, api_key, max_results))
            except Exception as e:
                logger.warning(f"ZenRows fallback search failed: {e}")
        
        logger.info(f"ZenRows returned {len(sources)} sources")
        return sources[:max_results]
        
    except Exception as e:
        logger.error(f"ZenRows search failed: {e}")
        raise

async def _zenrows_google_search(query: str, api_key: str, max_results: int) -> List[ResearchSource]:
    """ZenRows Google search with CSS extraction"""
    sources = []
    
    google_url = f"https://www.google.com/search?q={query.replace(' ', '+')}&num={max_results}"
    
    params = {
        "url": google_url,
        "apikey": api_key,
        "js_render": "true",
        "premium_proxy": "true",
        "proxy_country": "US",
        "wait": "2000",
        "css_extractor": json.dumps({
            "results": {
                "selector": ".g",
                "type": "list",
                "output": {
                    "title": {"selector": "h3", "output": "text"},
                    "link": {"selector": "a", "output": "@href"},
                    "snippet": {"selector": ".VwiC3b", "output": "text"}
                }
            }
        })
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.zenrows.com/v1/",
            params=params,
            timeout=30.0
        )
        
        if response.status_code == 200:
            try:
                data = response.json()
                
                if "results" in data and isinstance(data["results"], list):
                    for result in data["results"][:max_results]:
                        title = result.get("title", "").strip()
                        link = result.get("link", "").strip()
                        snippet = result.get("snippet", "").strip()
                        
                        if title and link and link.startswith("http") and "google.com" not in link:
                            sources.append(ResearchSource(
                                name="zenrows",
                                url=link,
                                title=title,
                                snippet=snippet,
                                relevance_score=0.7
                            ))
                else:
                    # Fallback to HTML parsing
                    html_content = response.text
                    sources.extend(_parse_google_html_fallback(html_content, max_results))
                    
            except json.JSONDecodeError:
                # Fallback to HTML parsing
                html_content = response.text
                sources.extend(_parse_google_html_fallback(html_content, max_results))
        else:
            raise Exception(f"ZenRows API returned {response.status_code}: {response.text}")
    
    return sources

def _parse_google_html_fallback(html_content: str, max_results: int) -> List[ResearchSource]:
    """Fallback HTML parsing for Google search results"""
    sources = []
    
    try:
        # Multiple regex patterns for different Google layouts
        patterns = [
            # Pattern 1: Standard Google results
            {
                "title": r'<h3[^>]*>([^<]+)</h3>',
                "url": r'<a[^>]*href="([^"]+)"[^>]*><h3',
                "snippet": r'<span[^>]*class="[^"]*VwiC3b[^"]*"[^>]*>([^<]+)</span>'
            },
            # Pattern 2: Alternative layout
            {
                "title": r'<h3[^>]*><span[^>]*>([^<]+)</span></h3>',
                "url": r'<a[^>]*href="([^"]+)"[^>]*>.*?<h3',
                "snippet": r'<div[^>]*class="[^"]*s3v9rd[^"]*"[^>]*>([^<]+)</div>'
            },
            # Pattern 3: Simplified pattern
            {
                "title": r'aria-level="3"[^>]*>([^<]+)<',
                "url": r'href="(https?://[^"]+)"',
                "snippet": r'<span[^>]*>([^<]{50,200})</span>'
            }
        ]
        
        for pattern_set in patterns:
            titles = re.findall(pattern_set["title"], html_content, re.IGNORECASE | re.DOTALL)
            urls = re.findall(pattern_set["url"], html_content, re.IGNORECASE)
            snippets = re.findall(pattern_set["snippet"], html_content, re.IGNORECASE | re.DOTALL)
            
            if titles and urls:
                logger.info(f"HTML parsing found {len(titles)} titles, {len(urls)} URLs")
                
                for i in range(min(len(titles), len(urls), max_results)):
                    title = titles[i].strip()
                    url = urls[i].strip()
                    snippet = snippets[i].strip() if i < len(snippets) else ""
                    
                    # Clean and validate URL
                    if url.startswith("http") and "google.com" not in url and len(title) > 5:
                        sources.append(ResearchSource(
                            name="zenrows",
                            url=url,
                            title=title,
                            snippet=snippet,
                            relevance_score=0.6
                        ))
                
                if sources:
                    break  # Use first successful pattern
                    
    except Exception as e:
        logger.error(f"HTML parsing failed: {e}")
    
    return sources

async def _zenrows_specialized_scraping(query: str, api_key: str, sources: List[ResearchSource], max_results: int):
    """Specialized scraping based on query content"""
    query_lower = query.lower()
    
    # Reddit scraping for community insights
    if any(keyword in query_lower for keyword in ["reddit", "community", "discussion"]):
        try:
            reddit_sources = await _zenrows_reddit_scraping(query, api_key)
            sources.extend(reddit_sources[:2])  # Limit Reddit results
        except Exception as e:
            logger.warning(f"Reddit scraping failed: {e}")
    
    # News scraping for current events
    if any(keyword in query_lower for keyword in ["news", "breaking", "latest"]):
        try:
            news_sources = await _zenrows_news_scraping(query, api_key)
            sources.extend(news_sources[:3])  # Limit news results
        except Exception as e:
            logger.warning(f"News scraping failed: {e}")

async def _zenrows_reddit_scraping(query: str, api_key: str) -> List[ResearchSource]:
    """Scrape Reddit with robust parsing"""
    sources = []
    
    reddit_url = f"https://www.reddit.com/search/?q={query.replace(' ', '+')}&sort=relevance"
    
    params = {
        "url": reddit_url,
        "apikey": api_key,
        "js_render": "true",
        "premium_proxy": "true",
        "wait": "3000"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.zenrows.com/v1/",
            params=params,
            timeout=30.0
        )
        
        if response.status_code == 200:
            html_content = response.text
            
            # Parse Reddit posts with multiple patterns
            post_patterns = [
                r'<h3[^>]*><a[^>]*href="([^"]*)"[^>]*>([^<]+)</a></h3>',
                r'data-click-id="body"[^>]*href="([^"]*)"[^>]*>.*?<h3[^>]*>([^<]+)</h3>',
                r'<a[^>]*href="(/r/[^"]*)"[^>]*>.*?<h3[^>]*>([^<]+)</h3>'
            ]
            
            for pattern in post_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)
                
                for match in matches[:3]:  # Limit Reddit results
                    if len(match) == 2:
                        url, title = match
                        if not url.startswith("http"):
                            url = f"https://www.reddit.com{url}"
                        
                        sources.append(ResearchSource(
                            name="zenrows-reddit",
                            url=url,
                            title=f"Reddit: {title.strip()}",
                            snippet="Community discussion",
                            relevance_score=0.6
                        ))
                
                if sources:
                    break
    
    return sources

async def _zenrows_news_scraping(query: str, api_key: str) -> List[ResearchSource]:
    """Scrape news sites with robust parsing"""
    sources = []
    
    # Try multiple news sources
    news_sites = [
        f"https://news.google.com/search?q={query.replace(' ', '+')}&hl=en-US&gl=US&ceid=US:en",
        f"https://www.reuters.com/search/news?blob={query.replace(' ', '+')}"
    ]
    
    for news_url in news_sites:
        try:
            params = {
                "url": news_url,
                "apikey": api_key,
                "js_render": "true",
                "premium_proxy": "true",
                "wait": "2000"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.zenrows.com/v1/",
                    params=params,
                    timeout=25.0
                )
                
                if response.status_code == 200:
                    html_content = response.text
                    
                    # Parse news articles
                    article_patterns = [
                        r'<article[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>.*?<h3[^>]*>([^<]+)</h3>',
                        r'<h3[^>]*><a[^>]*href="([^"]*)"[^>]*>([^<]+)</a></h3>',
                        r'data-n-tid="[^"]*"[^>]*href="([^"]*)"[^>]*>([^<]+)</a>'
                    ]
                    
                    for pattern in article_patterns:
                        matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)
                        
                        for match in matches[:2]:  # Limit per site
                            if len(match) == 2:
                                url, title = match
                                if not url.startswith("http"):
                                    if "google.com" in news_url:
                                        continue  # Skip relative URLs from Google News
                                    url = f"https://www.reuters.com{url}"
                                
                                sources.append(ResearchSource(
                                    name="zenrows-news",
                                    url=url,
                                    title=f"News: {title.strip()}",
                                    snippet="Latest news article",
                                    relevance_score=0.8
                                ))
                        
                        if sources:
                            break
                    
                    if len(sources) >= 2:
                        break
                        
        except Exception as e:
            logger.warning(f"News scraping failed for {news_url}: {e}")
            continue
    
    return sources

async def _zenrows_fallback_search(query: str, api_key: str, max_results: int) -> List[ResearchSource]:
    """Fallback search using simple DuckDuckGo scraping"""
    sources = []
    
    try:
        duckduckgo_url = f"https://duckduckgo.com/?q={query.replace(' ', '+')}"
        
        params = {
            "url": duckduckgo_url,
            "apikey": api_key,
            "premium_proxy": "true",
            "wait": "2000"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.zenrows.com/v1/",
                params=params,
                timeout=20.0
            )
            
            if response.status_code == 200:
                html_content = response.text
                
                # Parse DuckDuckGo results
                result_pattern = r'<a[^>]*href="([^"]*)"[^>]*class="[^"]*result__a[^"]*"[^>]*>([^<]+)</a>'
                matches = re.findall(result_pattern, html_content, re.IGNORECASE)
                
                for match in matches[:max_results]:
                    url, title = match
                    if url.startswith("http") and "duckduckgo.com" not in url:
                        sources.append(ResearchSource(
                            name="zenrows-fallback",
                            url=url,
                            title=title.strip(),
                            snippet="DuckDuckGo search result",
                            relevance_score=0.5
                        ))
                        
    except Exception as e:
        logger.error(f"ZenRows fallback search failed: {e}")
    
    return sources

async def search_apify_robust(query: str, max_results: int) -> List[ResearchSource]:
    """Robust Apify search with enhanced error handling"""
    try:
        api_token = os.getenv("APIFY_API_TOKEN")
        if not api_token:
            raise ValueError("APIFY_API_TOKEN not configured")
        
        sources = []
        
        # Strategy 1: Google Search Scraper (primary)
        try:
            sources.extend(await _apify_google_search(query, api_token, max_results))
        except Exception as e:
            logger.warning(f"Apify Google search failed: {e}")
        
        # Strategy 2: Specialized scraping based on query
        if len(sources) < max_results:
            try:
                await _apify_specialized_scraping(query, api_token, sources, max_results)
            except Exception as e:
                logger.warning(f"Apify specialized scraping failed: {e}")
        
        logger.info(f"Apify returned {len(sources)} sources")
        return sources[:max_results]
        
    except Exception as e:
        logger.error(f"Apify search failed: {e}")
        raise

async def _apify_google_search(query: str, api_token: str, max_results: int) -> List[ResearchSource]:
    """Apify Google Search with robust error handling"""
    sources = []
    
    # Use the sync endpoint for faster results
    apify_url = "https://api.apify.com/v2/acts/apify~google-search-scraper/run-sync-get-dataset-items"
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "queries": query,
        "maxPagesPerQuery": 1,
        "resultsPerPage": max_results,
        "mobileResults": False,
        "languageCode": "en",
        "countryCode": "US",
        "includeUnfilteredResults": False
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            apify_url,
            headers=headers,
            json=payload,
            timeout=25.0
        )
        
        if response.status_code == 200:
            try:
                data = response.json()
                
                if isinstance(data, list):
                    for item in data[:max_results]:
                        if isinstance(item, dict) and item.get("title") and item.get("url"):
                            # Validate URL
                            url = item["url"]
                            if url.startswith("http") and "google.com" not in url:
                                sources.append(ResearchSource(
                                    name="apify",
                                    url=url,
                                    title=item["title"],
                                    snippet=item.get("description", ""),
                                    relevance_score=0.8
                                ))
                else:
                    logger.warning(f"Apify returned unexpected data format: {type(data)}")
                    
            except json.JSONDecodeError as e:
                logger.error(f"Apify JSON decode error: {e}")
                raise Exception("Invalid JSON response from Apify")
        else:
            error_text = response.text[:200]  # Limit error text
            raise Exception(f"Apify API returned {response.status_code}: {error_text}")
    
    return sources

async def _apify_specialized_scraping(query: str, api_token: str, sources: List[ResearchSource], max_results: int):
    """Specialized Apify scraping based on query content"""
    query_lower = query.lower()
    
    # News scraping for current events
    if any(keyword in query_lower for keyword in ["news", "breaking", "latest"]):
        try:
            news_sources = await _apify_news_scraping(query, api_token)
            sources.extend(news_sources[:2])
        except Exception as e:
            logger.warning(f"Apify news scraping failed: {e}")
    
    # Social media scraping for trends
    if any(keyword in query_lower for keyword in ["twitter", "social", "trending"]):
        try:
            social_sources = await _apify_social_scraping(query, api_token)
            sources.extend(social_sources[:2])
        except Exception as e:
            logger.warning(f"Apify social scraping failed: {e}")

async def _apify_news_scraping(query: str, api_token: str) -> List[ResearchSource]:
    """Scrape news using Apify"""
    sources = []
    
    try:
        # Use Google News scraper
        apify_url = "https://api.apify.com/v2/acts/apify~google-news-scraper/run-sync-get-dataset-items"
        
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "searchTerms": query,
            "maxItems": 5,
            "language": "en",
            "country": "US"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                apify_url,
                headers=headers,
                json=payload,
                timeout=20.0
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    for item in data[:3]:  # Limit news results
                        if isinstance(item, dict) and item.get("title") and item.get("url"):
                            sources.append(ResearchSource(
                                name="apify-news",
                                url=item["url"],
                                title=f"News: {item['title']}",
                                snippet=item.get("snippet", ""),
                                relevance_score=0.8,
                                published_date=item.get("publishedAt", "")
                            ))
                            
    except Exception as e:
        logger.warning(f"Apify news scraping failed: {e}")
    
    return sources

async def _apify_social_scraping(query: str, api_token: str) -> List[ResearchSource]:
    """Scrape social media using Apify"""
    sources = []
    
    # Note: This is a placeholder for social media scraping
    # In practice, you would use specific Apify actors for Twitter, LinkedIn, etc.
    # For now, we'll skip this to avoid API errors
    
    return sources

async def generate_summary_robust(query: str, sources: List[ResearchSource]) -> SummaryResult:
    """Generate summary with LLM + extractive fallbacks"""
    
    # Strategy 1: LLM-based summary (primary)
    try:
        llm_summary = await _generate_llm_summary(query, sources)
        if llm_summary and len(llm_summary) > 50:
            return SummaryResult(
                text=llm_summary,
                confidence=0.9,
                model="gpt-4",
                method="llm",
                sources_used=len(sources)
            )
    except Exception as e:
        logger.warning(f"LLM summary generation failed: {e}")
    
    # Strategy 2: Extractive summary (fallback)
    try:
        extractive_summary = _generate_extractive_summary(query, sources)
        if extractive_summary:
            return SummaryResult(
                text=extractive_summary,
                confidence=0.7,
                model="extractive",
                method="extractive",
                sources_used=len(sources)
            )
    except Exception as e:
        logger.warning(f"Extractive summary generation failed: {e}")
    
    # Strategy 3: Simple concatenation (last resort)
    fallback_summary = _generate_fallback_summary(sources)
    return SummaryResult(
        text=fallback_summary,
        confidence=0.5,
        model="fallback",
        method="fallback",
        sources_used=len(sources)
    )

async def _generate_llm_summary(query: str, sources: List[ResearchSource]) -> str:
    """Generate summary using OpenAI API"""
    try:
        import openai
        
        # Prepare context from sources
        context_parts = []
        for i, source in enumerate(sources[:5]):  # Limit to top 5 sources
            content = source.content or source.snippet
            if content:
                context_parts.append(f"Source {i+1} ({source.name}): {content[:300]}")
        
        context = "\n\n".join(context_parts)
        
        prompt = f"""Based on the following research sources, provide a comprehensive summary for the query: "{query}"

Research Sources:
{context}

Please provide a well-structured summary that:
1. Directly answers the query
2. Synthesizes information from multiple sources
3. Highlights key findings and insights
4. Is approximately 150-200 words

Summary:"""

        client = openai.AsyncOpenAI()
        
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a research analyst providing comprehensive summaries based on multiple sources."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.3
        )
        
        summary = response.choices[0].message.content.strip()
        return summary
        
    except Exception as e:
        logger.error(f"LLM summary generation failed: {e}")
        raise

def _generate_extractive_summary(query: str, sources: List[ResearchSource]) -> str:
    """Generate extractive summary using keyword matching"""
    try:
        # Extract key terms from query
        query_terms = set(query.lower().split())
        
        # Score sentences based on keyword overlap
        sentences = []
        for source in sources[:5]:
            content = source.content or source.snippet
            if content:
                # Simple sentence splitting
                source_sentences = re.split(r'[.!?]+', content)
                for sentence in source_sentences:
                    if len(sentence.strip()) > 30:  # Minimum sentence length
                        sentence_terms = set(sentence.lower().split())
                        overlap = len(query_terms.intersection(sentence_terms))
                        if overlap > 0:
                            sentences.append((sentence.strip(), overlap, source.name))
        
        # Sort by relevance and select top sentences
        sentences.sort(key=lambda x: x[1], reverse=True)
        
        # Build summary from top sentences
        summary_parts = []
        used_sources = set()
        
        for sentence, score, source_name in sentences[:4]:
            if source_name not in used_sources:
                summary_parts.append(sentence)
                used_sources.add(source_name)
        
        if summary_parts:
            return " ".join(summary_parts)
        else:
            return ""
            
    except Exception as e:
        logger.error(f"Extractive summary generation failed: {e}")
        return ""

def _generate_fallback_summary(sources: List[ResearchSource]) -> str:
    """Generate simple fallback summary"""
    if not sources:
        return "No sources found for the query."
    
    # Simple concatenation of snippets
    snippets = []
    for source in sources[:3]:
        if source.snippet:
            snippets.append(source.snippet[:100])
    
    if snippets:
        summary = " ".join(snippets)
        return f"Based on {len(sources)} sources: {summary}"
    else:
        return f"Found {len(sources)} relevant sources but unable to generate summary."

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

