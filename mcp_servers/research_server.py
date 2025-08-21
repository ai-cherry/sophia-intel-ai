"""
Research Server - MCP server for research operations
Orchestrates multi-API research using Serper, ZenRows, Apify, Bright Data, and Tavily.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import asyncio
import httpx

logger = logging.getLogger(__name__)

# Pydantic models
class ResearchRequest(BaseModel):
    query: str
    sources: Optional[List[str]] = ["serper", "tavily", "zenrows"]
    max_results_per_source: Optional[int] = 10
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

class DeepResearchRequest(BaseModel):
    topic: str
    research_depth: Optional[str] = "standard"  # basic, standard, comprehensive
    focus_areas: Optional[List[str]] = None
    exclude_domains: Optional[List[str]] = None

class ResearchSummaryRequest(BaseModel):
    research_id: str
    summary_type: Optional[str] = "executive"  # executive, detailed, bullet_points

# Create router
router = APIRouter()

# Research storage
research_store: Dict[str, ResearchResult] = {}

async def get_api_manager():
    """Get API manager for external service calls."""
    from sophia.core.api_manager import SOPHIAAPIManager
    return SOPHIAAPIManager()

async def get_model_router():
    """Get model router for summarization."""
    from sophia.core.ultimate_model_router import UltimateModelRouter
    return UltimateModelRouter()

def generate_research_id() -> str:
    """Generate unique research ID."""
    import uuid
    return str(uuid.uuid4())

async def search_serper(query: str, api_key: str, max_results: int = 10) -> List[ResearchSource]:
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
                        relevance_score=0.8  # Mock score
                    ))
                
                return sources
            else:
                logger.error(f"Serper API error: {response.status_code}")
                return []
                
    except Exception as e:
        logger.error(f"Serper search failed: {e}")
        return []

async def search_tavily(query: str, api_key: str, max_results: int = 10) -> List[ResearchSource]:
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
                    "include_raw_content": True
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
                        content=result.get("raw_content", ""),
                        relevance_score=result.get("score", 0.7)
                    ))
                
                return sources
            else:
                logger.error(f"Tavily API error: {response.status_code}")
                return []
                
    except Exception as e:
        logger.error(f"Tavily search failed: {e}")
        return []

async def search_zenrows(query: str, api_key: str, max_results: int = 10) -> List[ResearchSource]:
    """Search using ZenRows for proxy-based web scraping."""
    try:
        sources = []
        
        # First, use ZenRows to scrape Google search results
        await _zenrows_google_search(query, api_key, sources, max_results)
        
        # Then try specialized scraping based on query content
        await _zenrows_specialized_scraping(query, api_key, sources, max_results)
        
        return sources[:max_results]
        
    except Exception as e:
        logger.error(f"ZenRows search failed: {e}")
        return []

async def _zenrows_google_search(query: str, api_key: str, sources: List[ResearchSource], max_results: int):
    """Scrape Google search results using ZenRows."""
    try:
        # Construct Google search URL
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}&num={max_results}"
        
        # ZenRows API endpoint
        zenrows_url = "https://api.zenrows.com/v1/"
        
        params = {
            "url": search_url,
            "apikey": api_key,
            "js_render": "true",  # Enable JavaScript rendering
            "premium_proxy": "true",  # Use premium residential proxies
            "proxy_country": "US",  # Use US proxies
            "wait": "2000",  # Wait 2 seconds for page load
            "css_extractor": json.dumps({
                "results": {
                    "selector": ".g",  # Google search result containers
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
                zenrows_url,
                params=params,
                timeout=60.0  # ZenRows can take longer due to proxy routing
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "results" in data and isinstance(data["results"], list):
                    for result in data["results"][:max_results]:
                        if result.get("title") and result.get("link"):
                            # Clean up the link (remove Google redirect)
                            link = result["link"]
                            if link.startswith("/url?q="):
                                link = link.split("/url?q=")[1].split("&")[0]
                            
                            sources.append(ResearchSource(
                                name="zenrows-google",
                                url=link,
                                title=result["title"],
                                snippet=result.get("snippet", ""),
                                relevance_score=0.8
                            ))
            else:
                logger.error(f"ZenRows Google search failed: {response.status_code}")
                
    except Exception as e:
        logger.error(f"ZenRows Google search failed: {e}")

async def _zenrows_specialized_scraping(query: str, api_key: str, sources: List[ResearchSource], max_results: int):
    """Perform specialized scraping using ZenRows based on query content."""
    try:
        query_lower = query.lower()
        
        # Reddit scraping for community insights
        if any(keyword in query_lower for keyword in ["reddit", "community", "discussion", "opinion"]):
            await _zenrows_reddit_scraping(query, api_key, sources)
        
        # News site scraping for current events
        if any(keyword in query_lower for keyword in ["news", "breaking", "latest", "current"]):
            await _zenrows_news_scraping(query, api_key, sources)
        
        # E-commerce scraping for product information
        if any(keyword in query_lower for keyword in ["product", "price", "review", "buy", "shop"]):
            await _zenrows_ecommerce_scraping(query, api_key, sources)
        
        # Academic/research scraping
        if any(keyword in query_lower for keyword in ["research", "study", "academic", "paper", "journal"]):
            await _zenrows_academic_scraping(query, api_key, sources)
            
    except Exception as e:
        logger.error(f"ZenRows specialized scraping failed: {e}")

async def _zenrows_reddit_scraping(query: str, api_key: str, sources: List[ResearchSource]):
    """Scrape Reddit using ZenRows."""
    try:
        # Search Reddit
        reddit_search_url = f"https://www.reddit.com/search/?q={query.replace(' ', '+')}&sort=relevance&t=month"
        
        params = {
            "url": reddit_search_url,
            "apikey": api_key,
            "js_render": "true",
            "premium_proxy": "true",
            "proxy_country": "US",
            "wait": "3000",
            "css_extractor": json.dumps({
                "posts": {
                    "selector": "[data-testid='post-container']",
                    "type": "list",
                    "output": {
                        "title": {"selector": "h3", "output": "text"},
                        "link": {"selector": "a[data-click-id='body']", "output": "@href"},
                        "subreddit": {"selector": "[data-testid='subreddit-name']", "output": "text"},
                        "score": {"selector": "[data-testid='vote-arrows'] span", "output": "text"},
                        "comments": {"selector": "[data-testid='comment-count']", "output": "text"}
                    }
                }
            })
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.zenrows.com/v1/",
                params=params,
                timeout=60.0
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "posts" in data and isinstance(data["posts"], list):
                    for post in data["posts"][:5]:  # Limit Reddit results
                        if post.get("title") and post.get("link"):
                            link = post["link"]
                            if not link.startswith("http"):
                                link = f"https://www.reddit.com{link}"
                            
                            sources.append(ResearchSource(
                                name="zenrows-reddit",
                                url=link,
                                title=f"Reddit ({post.get('subreddit', 'r/unknown')}): {post['title']}",
                                snippet=f"Score: {post.get('score', 'N/A')} | Comments: {post.get('comments', 'N/A')}",
                                relevance_score=0.7
                            ))
                            
    except Exception as e:
        logger.error(f"ZenRows Reddit scraping failed: {e}")

async def _zenrows_news_scraping(query: str, api_key: str, sources: List[ResearchSource]):
    """Scrape news sites using ZenRows."""
    try:
        # List of news sites to scrape
        news_sites = [
            f"https://www.reuters.com/search/news?blob={query.replace(' ', '%20')}",
            f"https://apnews.com/search?q={query.replace(' ', '+')}",
            f"https://www.bbc.com/search?q={query.replace(' ', '+')}"
        ]
        
        for site_url in news_sites[:2]:  # Limit to 2 news sites
            try:
                params = {
                    "url": site_url,
                    "apikey": api_key,
                    "js_render": "true",
                    "premium_proxy": "true",
                    "proxy_country": "US",
                    "wait": "3000",
                    "css_extractor": json.dumps({
                        "articles": {
                            "selector": "article, .story, .search-result",
                            "type": "list",
                            "output": {
                                "title": {"selector": "h1, h2, h3, .headline", "output": "text"},
                                "link": {"selector": "a", "output": "@href"},
                                "summary": {"selector": "p, .summary, .description", "output": "text"},
                                "date": {"selector": "time, .date", "output": "text"}
                            }
                        }
                    })
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        "https://api.zenrows.com/v1/",
                        params=params,
                        timeout=60.0
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if "articles" in data and isinstance(data["articles"], list):
                            for article in data["articles"][:3]:  # Limit per site
                                if article.get("title") and article.get("link"):
                                    link = article["link"]
                                    if not link.startswith("http"):
                                        # Construct full URL
                                        from urllib.parse import urljoin
                                        link = urljoin(site_url, link)
                                    
                                    site_name = "Reuters" if "reuters" in site_url else "AP News" if "apnews" in site_url else "BBC"
                                    
                                    sources.append(ResearchSource(
                                        name="zenrows-news",
                                        url=link,
                                        title=f"{site_name}: {article['title']}",
                                        snippet=article.get("summary", "")[:300],
                                        relevance_score=0.85,
                                        published_date=article.get("date", "")
                                    ))
                                    
            except Exception as e:
                logger.error(f"ZenRows news scraping failed for {site_url}: {e}")
                continue
                
    except Exception as e:
        logger.error(f"ZenRows news scraping failed: {e}")

async def _zenrows_ecommerce_scraping(query: str, api_key: str, sources: List[ResearchSource]):
    """Scrape e-commerce sites using ZenRows."""
    try:
        # Amazon product search
        amazon_url = f"https://www.amazon.com/s?k={query.replace(' ', '+')}"
        
        params = {
            "url": amazon_url,
            "apikey": api_key,
            "js_render": "true",
            "premium_proxy": "true",
            "proxy_country": "US",
            "wait": "4000",
            "css_extractor": json.dumps({
                "products": {
                    "selector": "[data-component-type='s-search-result']",
                    "type": "list",
                    "output": {
                        "title": {"selector": "h2 a span", "output": "text"},
                        "link": {"selector": "h2 a", "output": "@href"},
                        "price": {"selector": ".a-price-whole", "output": "text"},
                        "rating": {"selector": ".a-icon-alt", "output": "text"},
                        "reviews": {"selector": ".a-size-base", "output": "text"}
                    }
                }
            })
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.zenrows.com/v1/",
                params=params,
                timeout=60.0
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "products" in data and isinstance(data["products"], list):
                    for product in data["products"][:5]:  # Limit Amazon results
                        if product.get("title") and product.get("link"):
                            link = product["link"]
                            if not link.startswith("http"):
                                link = f"https://www.amazon.com{link}"
                            
                            price_str = f"${product.get('price', 'N/A')}" if product.get('price') else "Price N/A"
                            rating_str = product.get('rating', 'No rating')
                            reviews_str = product.get('reviews', 'No reviews')
                            
                            sources.append(ResearchSource(
                                name="zenrows-amazon",
                                url=link,
                                title=f"Amazon: {product['title']}",
                                snippet=f"{price_str} | {rating_str} | {reviews_str}",
                                relevance_score=0.8
                            ))
                            
    except Exception as e:
        logger.error(f"ZenRows e-commerce scraping failed: {e}")

async def _zenrows_academic_scraping(query: str, api_key: str, sources: List[ResearchSource]):
    """Scrape academic sources using ZenRows."""
    try:
        # Google Scholar search
        scholar_url = f"https://scholar.google.com/scholar?q={query.replace(' ', '+')}"
        
        params = {
            "url": scholar_url,
            "apikey": api_key,
            "js_render": "true",
            "premium_proxy": "true",
            "proxy_country": "US",
            "wait": "3000",
            "css_extractor": json.dumps({
                "papers": {
                    "selector": ".gs_r",
                    "type": "list",
                    "output": {
                        "title": {"selector": ".gs_rt a", "output": "text"},
                        "link": {"selector": ".gs_rt a", "output": "@href"},
                        "authors": {"selector": ".gs_a", "output": "text"},
                        "snippet": {"selector": ".gs_rs", "output": "text"},
                        "citations": {"selector": ".gs_fl a", "output": "text"}
                    }
                }
            })
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.zenrows.com/v1/",
                params=params,
                timeout=60.0
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "papers" in data and isinstance(data["papers"], list):
                    for paper in data["papers"][:4]:  # Limit academic results
                        if paper.get("title") and paper.get("link"):
                            sources.append(ResearchSource(
                                name="zenrows-scholar",
                                url=paper["link"],
                                title=f"Scholar: {paper['title']}",
                                snippet=f"Authors: {paper.get('authors', 'N/A')} | {paper.get('snippet', '')}",
                                relevance_score=0.9,  # Academic sources are highly relevant
                                published_date=paper.get('citations', '')
                            ))
                            
    except Exception as e:
        logger.error(f"ZenRows academic scraping failed: {e}")

# Helper function to safely import json
import json

async def search_apify(query: str, api_token: str, max_results: int = 10) -> List[ResearchSource]:
    """Search using Apify actors for comprehensive web scraping."""
    try:
        sources = []
        
        # Use Google Search Results Scraper actor for general queries
        google_actor_id = "apify/google-search-scraper"
        
        # Prepare input for Google Search Scraper
        actor_input = {
            "queries": [query],
            "maxPagesPerQuery": 1,
            "resultsPerPage": max_results,
            "mobileResults": False,
            "languageCode": "en",
            "countryCode": "US"
        }
        
        async with httpx.AsyncClient() as client:
            # Start the actor run
            run_response = await client.post(
                f"https://api.apify.com/v2/acts/{google_actor_id}/runs",
                headers={
                    "Authorization": f"Bearer {api_token}",
                    "Content-Type": "application/json"
                },
                json=actor_input,
                timeout=30.0
            )
            
            if run_response.status_code != 201:
                logger.error(f"Apify actor start failed: {run_response.status_code}")
                return []
            
            run_data = run_response.json()
            run_id = run_data["data"]["id"]
            
            # Wait for the run to complete (with timeout)
            max_wait_time = 60  # seconds
            wait_interval = 2   # seconds
            waited_time = 0
            
            while waited_time < max_wait_time:
                status_response = await client.get(
                    f"https://api.apify.com/v2/acts/{google_actor_id}/runs/{run_id}",
                    headers={"Authorization": f"Bearer {api_token}"},
                    timeout=10.0
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data["data"]["status"]
                    
                    if status == "SUCCEEDED":
                        break
                    elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                        logger.error(f"Apify actor run failed with status: {status}")
                        return []
                
                await asyncio.sleep(wait_interval)
                waited_time += wait_interval
            
            # Get the results
            results_response = await client.get(
                f"https://api.apify.com/v2/acts/{google_actor_id}/runs/{run_id}/dataset/items",
                headers={"Authorization": f"Bearer {api_token}"},
                timeout=30.0
            )
            
            if results_response.status_code == 200:
                results_data = results_response.json()
                
                for item in results_data:
                    if "organicResults" in item:
                        for result in item["organicResults"][:max_results]:
                            sources.append(ResearchSource(
                                name="apify",
                                url=result.get("url", ""),
                                title=result.get("title", ""),
                                snippet=result.get("description", ""),
                                relevance_score=0.75  # Apify provides good quality results
                            ))
            
            # Try additional specialized scraping if query suggests specific domains
            await _apify_specialized_scraping(query, api_token, sources, max_results, client)
            
        return sources[:max_results]
        
    except Exception as e:
        logger.error(f"Apify search failed: {e}")
        return []

async def _apify_specialized_scraping(query: str, api_token: str, sources: List[ResearchSource], max_results: int, client: httpx.AsyncClient):
    """Perform specialized scraping based on query content."""
    try:
        query_lower = query.lower()
        
        # LinkedIn scraping for professional/business queries
        if any(keyword in query_lower for keyword in ["linkedin", "professional", "business", "company", "executive"]):
            await _scrape_linkedin_apify(query, api_token, sources, client)
        
        # Twitter/X scraping for social media insights
        if any(keyword in query_lower for keyword in ["twitter", "social media", "trending", "sentiment"]):
            await _scrape_twitter_apify(query, api_token, sources, client)
        
        # News scraping for current events
        if any(keyword in query_lower for keyword in ["news", "breaking", "latest", "current events"]):
            await _scrape_news_apify(query, api_token, sources, client)
        
        # E-commerce scraping for product research
        if any(keyword in query_lower for keyword in ["product", "price", "review", "amazon", "shopping"]):
            await _scrape_ecommerce_apify(query, api_token, sources, client)
            
    except Exception as e:
        logger.error(f"Specialized Apify scraping failed: {e}")

async def _scrape_linkedin_apify(query: str, api_token: str, sources: List[ResearchSource], client: httpx.AsyncClient):
    """Scrape LinkedIn using Apify."""
    try:
        actor_id = "apify/linkedin-company-scraper"
        
        # Extract company names from query if possible
        company_urls = []
        if "linkedin.com/company/" in query:
            company_urls = [query]
        else:
            # Use a simple heuristic to find potential company names
            words = query.split()
            for word in words:
                if len(word) > 3 and word.isalpha():
                    company_urls.append(f"https://www.linkedin.com/company/{word.lower()}")
        
        if not company_urls:
            return
        
        actor_input = {
            "startUrls": company_urls[:3],  # Limit to 3 companies
            "maxEmployees": 10
        }
        
        # Quick run with shorter timeout for specialized scraping
        run_response = await client.post(
            f"https://api.apify.com/v2/acts/{actor_id}/runs",
            headers={
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            },
            json=actor_input,
            timeout=20.0
        )
        
        if run_response.status_code == 201:
            run_data = run_response.json()
            run_id = run_data["data"]["id"]
            
            # Wait briefly for results
            await asyncio.sleep(10)
            
            results_response = await client.get(
                f"https://api.apify.com/v2/acts/{actor_id}/runs/{run_id}/dataset/items",
                headers={"Authorization": f"Bearer {api_token}"},
                timeout=15.0
            )
            
            if results_response.status_code == 200:
                results_data = results_response.json()
                
                for item in results_data[:2]:  # Limit results
                    if item.get("companyName"):
                        sources.append(ResearchSource(
                            name="apify-linkedin",
                            url=item.get("companyUrl", ""),
                            title=f"LinkedIn: {item.get('companyName', '')}",
                            snippet=f"Industry: {item.get('industry', 'N/A')}, Size: {item.get('companySize', 'N/A')}, Description: {item.get('description', '')[:200]}...",
                            relevance_score=0.8
                        ))
                        
    except Exception as e:
        logger.error(f"LinkedIn Apify scraping failed: {e}")

async def _scrape_twitter_apify(query: str, api_token: str, sources: List[ResearchSource], client: httpx.AsyncClient):
    """Scrape Twitter/X using Apify."""
    try:
        actor_id = "apify/twitter-scraper"
        
        actor_input = {
            "searchTerms": [query],
            "maxTweets": 20,
            "onlyImage": False,
            "onlyQuote": False,
            "onlyTwitterBlue": False,
            "onlyVerified": False
        }
        
        run_response = await client.post(
            f"https://api.apify.com/v2/acts/{actor_id}/runs",
            headers={
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            },
            json=actor_input,
            timeout=20.0
        )
        
        if run_response.status_code == 201:
            run_data = run_response.json()
            run_id = run_data["data"]["id"]
            
            await asyncio.sleep(15)  # Wait for Twitter scraping
            
            results_response = await client.get(
                f"https://api.apify.com/v2/acts/{actor_id}/runs/{run_id}/dataset/items",
                headers={"Authorization": f"Bearer {api_token}"},
                timeout=15.0
            )
            
            if results_response.status_code == 200:
                results_data = results_response.json()
                
                for item in results_data[:5]:  # Limit Twitter results
                    if item.get("text"):
                        sources.append(ResearchSource(
                            name="apify-twitter",
                            url=item.get("url", ""),
                            title=f"Twitter: @{item.get('author', {}).get('userName', 'unknown')}",
                            snippet=item.get("text", "")[:300],
                            relevance_score=0.7,
                            published_date=item.get("createdAt", "")
                        ))
                        
    except Exception as e:
        logger.error(f"Twitter Apify scraping failed: {e}")

async def _scrape_news_apify(query: str, api_token: str, sources: List[ResearchSource], client: httpx.AsyncClient):
    """Scrape news sources using Apify."""
    try:
        actor_id = "apify/google-news-scraper"
        
        actor_input = {
            "searchTerms": [query],
            "maxArticles": 15,
            "timeRange": "7d",  # Last 7 days
            "language": "en"
        }
        
        run_response = await client.post(
            f"https://api.apify.com/v2/acts/{actor_id}/runs",
            headers={
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            },
            json=actor_input,
            timeout=20.0
        )
        
        if run_response.status_code == 201:
            run_data = run_response.json()
            run_id = run_data["data"]["id"]
            
            await asyncio.sleep(12)
            
            results_response = await client.get(
                f"https://api.apify.com/v2/acts/{actor_id}/runs/{run_id}/dataset/items",
                headers={"Authorization": f"Bearer {api_token}"},
                timeout=15.0
            )
            
            if results_response.status_code == 200:
                results_data = results_response.json()
                
                for item in results_data[:8]:  # Limit news results
                    sources.append(ResearchSource(
                        name="apify-news",
                        url=item.get("url", ""),
                        title=item.get("title", ""),
                        snippet=item.get("snippet", ""),
                        relevance_score=0.85,  # News is usually highly relevant
                        published_date=item.get("publishedAt", "")
                    ))
                    
    except Exception as e:
        logger.error(f"News Apify scraping failed: {e}")

async def _scrape_ecommerce_apify(query: str, api_token: str, sources: List[ResearchSource], client: httpx.AsyncClient):
    """Scrape e-commerce sites using Apify."""
    try:
        # Use Amazon scraper for product research
        actor_id = "apify/amazon-product-scraper"
        
        actor_input = {
            "searchTerms": [query],
            "maxProducts": 10,
            "includeReviews": True,
            "maxReviews": 5
        }
        
        run_response = await client.post(
            f"https://api.apify.com/v2/acts/{actor_id}/runs",
            headers={
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            },
            json=actor_input,
            timeout=20.0
        )
        
        if run_response.status_code == 201:
            run_data = run_response.json()
            run_id = run_data["data"]["id"]
            
            await asyncio.sleep(20)  # Amazon scraping takes longer
            
            results_response = await client.get(
                f"https://api.apify.com/v2/acts/{actor_id}/runs/{run_id}/dataset/items",
                headers={"Authorization": f"Bearer {api_token}"},
                timeout=15.0
            )
            
            if results_response.status_code == 200:
                results_data = results_response.json()
                
                for item in results_data[:5]:  # Limit product results
                    price = item.get("price", {})
                    price_str = f"${price.get('value', 'N/A')}" if price else "Price N/A"
                    
                    sources.append(ResearchSource(
                        name="apify-amazon",
                        url=item.get("url", ""),
                        title=f"Amazon: {item.get('title', '')}",
                        snippet=f"{price_str} - Rating: {item.get('stars', 'N/A')}/5 - {item.get('description', '')[:200]}...",
                        relevance_score=0.8
                    ))
                    
    except Exception as e:
        logger.error(f"E-commerce Apify scraping failed: {e}")

async def search_bright_data(query: str, credentials: Dict, max_results: int = 10) -> List[ResearchSource]:
    """Search using Bright Data."""
    try:
        # TODO: Implement Bright Data search
        logger.warning("Bright Data search not yet implemented")
        return []
        
    except Exception as e:
        logger.error(f"Bright Data search failed: {e}")
        return []

@router.post("/search", response_model=ResearchResult)
async def conduct_research(
    request: ResearchRequest,
    api_manager = Depends(get_api_manager),
    model_router = Depends(get_model_router)
):
    """
    Conduct research across multiple sources and optionally summarize results.
    """
    try:
        research_id = generate_research_id()
        all_sources = []
        
        # Get API keys
        serper_key = os.getenv("SERPER_API_KEY")
        tavily_key = os.getenv("TAVILY_API_KEY")
        zenrows_key = os.getenv("ZENROWS_API_KEY")
        apify_token = os.getenv("APIFY_API_TOKEN")
        
        # Prepare search tasks
        search_tasks = []
        
        if "serper" in request.sources and serper_key:
            search_tasks.append(search_serper(request.query, serper_key, request.max_results_per_source))
        
        if "tavily" in request.sources and tavily_key:
            search_tasks.append(search_tavily(request.query, tavily_key, request.max_results_per_source))
        
        if "zenrows" in request.sources and zenrows_key:
            search_tasks.append(search_zenrows(request.query, zenrows_key, request.max_results_per_source))
        
        if "apify" in request.sources and apify_token:
            search_tasks.append(search_apify(request.query, apify_token, request.max_results_per_source))
        
        # Execute searches concurrently
        if search_tasks:
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Combine results
            for result in search_results:
                if isinstance(result, list):
                    all_sources.extend(result)
                elif isinstance(result, Exception):
                    logger.error(f"Search task failed: {result}")
        
        # Deduplicate by URL
        seen_urls = set()
        unique_sources = []
        for source in all_sources:
            if source.url not in seen_urls:
                seen_urls.add(source.url)
                unique_sources.append(source)
        
        # Generate summary if requested
        summary = None
        if request.summarize and unique_sources:
            try:
                # Prepare content for summarization
                content_for_summary = f"Research Query: {request.query}\n\n"
                for i, source in enumerate(unique_sources[:10], 1):  # Limit to top 10 for summary
                    content_for_summary += f"{i}. {source.title}\n"
                    content_for_summary += f"   URL: {source.url}\n"
                    content_for_summary += f"   Summary: {source.snippet}\n\n"
                
                # Use approved model for summarization
                model_config = model_router.select_model("research")
                
                summary_prompt = f"""
Analyze the following research results and provide a comprehensive summary:

{content_for_summary}

Please provide:
1. Key findings and insights
2. Main themes and patterns
3. Notable sources and their contributions
4. Conclusions and implications

Summary:
"""
                
                summary = await model_router.call_model(
                    model_config,
                    summary_prompt,
                    temperature=0.3,
                    max_tokens=2048
                )
                
            except Exception as e:
                logger.error(f"Summarization failed: {e}")
                summary = "Summary generation failed"
        
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

@router.post("/deep-research", response_model=ResearchResult)
async def conduct_deep_research(
    request: DeepResearchRequest,
    api_manager = Depends(get_api_manager),
    model_router = Depends(get_model_router)
):
    """
    Conduct comprehensive deep research with multiple query variations.
    """
    try:
        # Generate related queries based on topic and focus areas
        base_queries = [request.topic]
        
        if request.focus_areas:
            for area in request.focus_areas:
                base_queries.append(f"{request.topic} {area}")
        
        # Adjust search depth
        max_results_per_query = {
            "basic": 5,
            "standard": 10,
            "comprehensive": 20
        }.get(request.research_depth, 10)
        
        all_sources = []
        
        # Conduct research for each query
        for query in base_queries:
            research_request = ResearchRequest(
                query=query,
                sources=["serper", "tavily", "zenrows"],
                max_results_per_source=max_results_per_query,
                include_content=True,
                summarize=False  # We'll summarize at the end
            )
            
            result = await conduct_research(research_request, api_manager, model_router)
            all_sources.extend(result.sources)
        
        # Deduplicate and rank sources
        seen_urls = set()
        unique_sources = []
        for source in all_sources:
            if source.url not in seen_urls:
                if request.exclude_domains:
                    domain_excluded = any(domain in source.url for domain in request.exclude_domains)
                    if domain_excluded:
                        continue
                
                seen_urls.add(source.url)
                unique_sources.append(source)
        
        # Generate comprehensive summary
        summary = await generate_comprehensive_summary(
            request.topic, unique_sources, model_router
        )
        
        research_id = generate_research_id()
        research_result = ResearchResult(
            query=request.topic,
            sources=unique_sources,
            summary=summary,
            total_sources=len(unique_sources),
            research_id=research_id,
            created_at=datetime.now(timezone.utc)
        )
        
        research_store[research_id] = research_result
        
        logger.info(f"Completed deep research {research_id} with {len(unique_sources)} sources")
        return research_result
        
    except Exception as e:
        logger.error(f"Deep research failed: {e}")
        raise HTTPException(status_code=500, detail=f"Deep research failed: {str(e)}")

async def generate_comprehensive_summary(topic: str, sources: List[ResearchSource], model_router) -> str:
    """Generate a comprehensive summary from research sources."""
    try:
        # Prepare detailed content
        content = f"Deep Research Topic: {topic}\n\n"
        content += f"Total Sources Analyzed: {len(sources)}\n\n"
        
        for i, source in enumerate(sources[:15], 1):  # Limit to top 15 for summary
            content += f"{i}. {source.title}\n"
            content += f"   Source: {source.name.upper()}\n"
            content += f"   URL: {source.url}\n"
            content += f"   Content: {source.snippet}\n"
            if source.content:
                content += f"   Full Content: {source.content[:500]}...\n"
            content += "\n"
        
        model_config = model_router.select_model("research")
        
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
   - Contradictions or conflicting information

3. SOURCE EVALUATION
   - Quality and credibility of sources
   - Most valuable sources and why
   - Gaps in information

4. IMPLICATIONS AND RECOMMENDATIONS
   - Practical implications of findings
   - Areas requiring further research
   - Actionable recommendations

5. CONCLUSION
   - Summary of key takeaways
   - Overall assessment

Research Summary:
"""
        
        summary = await model_router.call_model(
            model_config,
            summary_prompt,
            temperature=0.2,
            max_tokens=4096
        )
        
        return summary
        
    except Exception as e:
        logger.error(f"Summary generation failed: {e}")
        return "Comprehensive summary generation failed"

@router.get("/research/{research_id}", response_model=ResearchResult)
async def get_research_result(research_id: str):
    """Get stored research result by ID."""
    if research_id not in research_store:
        raise HTTPException(status_code=404, detail="Research result not found")
    
    return research_store[research_id]

@router.get("/research")
async def list_research_results(limit: int = 20, offset: int = 0):
    """List stored research results."""
    results = list(research_store.values())
    results.sort(key=lambda x: x.created_at, reverse=True)
    
    paginated_results = results[offset:offset + limit]
    
    return {
        "results": [{"research_id": r.research_id, "query": r.query, "created_at": r.created_at, "total_sources": r.total_sources} for r in paginated_results],
        "total": len(results),
        "limit": limit,
        "offset": offset
    }

@router.delete("/research/{research_id}")
async def delete_research_result(research_id: str):
    """Delete a research result."""
    if research_id not in research_store:
        raise HTTPException(status_code=404, detail="Research result not found")
    
    del research_store[research_id]
    return {"status": "success", "message": f"Research {research_id} deleted"}

@router.get("/health")
async def research_server_health():
    """Health check for research server."""
    api_keys_status = {
        "serper": "configured" if os.getenv("SERPER_API_KEY") else "missing",
        "tavily": "configured" if os.getenv("TAVILY_API_KEY") else "missing",
        "zenrows": "configured" if os.getenv("ZENROWS_API_KEY") else "missing",
        "apify": "configured" if os.getenv("APIFY_API_TOKEN") else "missing"
    }
    
    return {
        "status": "healthy",
        "service": "research_server",
        "stored_research": len(research_store),
        "api_keys": api_keys_status,
        "capabilities": [
            "multi_source_search",
            "deep_research",
            "content_summarization",
            "source_deduplication"
        ]
    }

