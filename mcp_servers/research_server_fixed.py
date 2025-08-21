"""
Enhanced Research Server v4.2 - REAL Implementation
Comprehensive multi-source research with robust error handling
"""

import os
import re
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResearchSource(BaseModel):
    name: str
    url: str
    title: str
    snippet: str
    content: Optional[str] = None
    relevance_score: float = 0.0
    timestamp: str = None

class SummaryResult(BaseModel):
    text: str
    confidence: float
    model: str
    method: str
    sources_used: int

class ResearchRequest(BaseModel):
    query: str
    max_sources: int = 10
    include_summary: bool = True

class ResearchResponse(BaseModel):
    query: str
    sources: List[ResearchSource]
    summary: Optional[SummaryResult] = None
    total_sources: int
    created_at: str

# Initialize FastAPI app
app = FastAPI(title="SOPHIA Research Server v4.2", version="4.2.0")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "research-server",
        "version": "4.2.0",
        "apis_configured": {
            "serper": bool(os.getenv("SERPER_API_KEY")),
            "tavily": bool(os.getenv("TAVILY_API_KEY")),
            "zenrows": bool(os.getenv("ZENROWS_API_KEY")),
            "apify": bool(os.getenv("APIFY_API_TOKEN")),
            "openai": bool(os.getenv("OPENAI_API_KEY"))
        }
    }

@app.post("/search", response_model=ResearchResponse)
async def comprehensive_search(request: ResearchRequest):
    """Comprehensive multi-source research with robust error handling"""
    try:
        logger.info(f"Research request: {request.query}")
        
        # Parallel search across all sources
        search_tasks = [
            search_serper_safe(request.query, request.max_sources // 4),
            search_tavily_safe(request.query, request.max_sources // 4),
            search_zenrows_robust(request.query, request.max_sources // 4),
            search_apify_robust(request.query, request.max_sources // 4)
        ]
        
        # Execute searches concurrently
        search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # Combine results from all sources
        all_sources = []
        for i, result in enumerate(search_results):
            if isinstance(result, Exception):
                logger.warning(f"Search {i} failed: {result}")
                continue
            if isinstance(result, list):
                all_sources.extend(result)
        
        # Remove duplicates and sort by relevance
        unique_sources = remove_duplicate_sources(all_sources)
        sorted_sources = sorted(unique_sources, key=lambda x: x.relevance_score, reverse=True)
        final_sources = sorted_sources[:request.max_sources]
        
        # Generate summary if requested
        summary = None
        if request.include_summary and final_sources:
            try:
                summary = await generate_summary_robust(request.query, final_sources)
            except Exception as e:
                logger.warning(f"Summary generation failed: {e}")
                summary = SummaryResult(
                    text=f"Found {len(final_sources)} relevant sources but unable to generate summary.",
                    confidence=0.3,
                    model="fallback",
                    method="error",
                    sources_used=len(final_sources)
                )
        
        return ResearchResponse(
            query=request.query,
            sources=final_sources,
            summary=summary,
            total_sources=len(final_sources),
            created_at=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Research failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def search_serper_safe(query: str, max_results: int) -> List[ResearchSource]:
    """Safe Serper search with error handling"""
    try:
        api_key = os.getenv("SERPER_API_KEY")
        if not api_key:
            return []
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
                json={"q": query, "num": max_results},
                timeout=15.0
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
                        relevance_score=0.9
                    ))
                
                logger.info(f"Serper returned {len(sources)} sources")
                return sources
            else:
                logger.warning(f"Serper API error: {response.status_code}")
                return []
                
    except Exception as e:
        logger.error(f"Serper search failed: {e}")
        return []

async def search_tavily_safe(query: str, max_results: int) -> List[ResearchSource]:
    """Safe Tavily search with error handling"""
    try:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return []
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.tavily.com/search",
                headers={"Content-Type": "application/json"},
                json={
                    "api_key": api_key,
                    "query": query,
                    "search_depth": "advanced",
                    "max_results": max_results
                },
                timeout=20.0
            )
            
            if response.status_code == 200:
                data = response.json()
                sources = []
                
                for result in data.get("results", []):
                    sources.append(ResearchSource(
                        name="tavily",
                        url=result.get("url", ""),
                        title=result.get("title", ""),
                        snippet=result.get("content", "")[:300],
                        content=result.get("content", ""),
                        relevance_score=result.get("score", 0.8)
                    ))
                
                logger.info(f"Tavily returned {len(sources)} sources")
                return sources
            else:
                logger.warning(f"Tavily API error: {response.status_code}")
                return []
                
    except Exception as e:
        logger.error(f"Tavily search failed: {e}")
        return []

async def search_zenrows_robust(query: str, max_results: int) -> List[ResearchSource]:
    """Enhanced ZenRows search with multiple parsing strategies"""
    try:
        api_key = os.getenv("ZENROWS_API_KEY")
        if not api_key:
            return []
        
        sources = []
        
        # Strategy 1: Google Search with robust parsing
        try:
            google_sources = await _zenrows_google_search(query, api_key, max_results)
            sources.extend(google_sources)
        except Exception as e:
            logger.warning(f"ZenRows Google search failed: {e}")
        
        # Strategy 2: Reddit search for discussion queries
        if len(sources) < max_results and any(term in query.lower() for term in ['discussion', 'opinion', 'reddit', 'community']):
            try:
                reddit_sources = await _zenrows_reddit_search(query, api_key, max_results - len(sources))
                sources.extend(reddit_sources)
            except Exception as e:
                logger.warning(f"ZenRows Reddit search failed: {e}")
        
        logger.info(f"ZenRows returned {len(sources)} sources")
        return sources[:max_results]
        
    except Exception as e:
        logger.error(f"ZenRows search failed: {e}")
        return []

async def _zenrows_google_search(query: str, api_key: str, max_results: int) -> List[ResearchSource]:
    """Robust Google search through ZenRows"""
    sources = []
    
    try:
        google_url = f"https://www.google.com/search?q={query.replace(' ', '+')}&num={max_results}"
        
        params = {
            "url": google_url,
            "apikey": api_key,
            "premium_proxy": "true",
            "js_render": "true",
            "wait": "3000"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.zenrows.com/v1/",
                params=params,
                timeout=25.0
            )
            
            if response.status_code == 200:
                html_content = response.text
                
                # Multiple parsing strategies
                sources.extend(_parse_google_method1(html_content))
                if not sources:
                    sources.extend(_parse_google_method2(html_content))
                if not sources:
                    sources.extend(_parse_google_method3(html_content))
                
                # Filter and validate
                valid_sources = []
                for source in sources:
                    if (source.url and source.title and 
                        source.url.startswith("http") and 
                        "google.com" not in source.url and
                        len(source.title.strip()) > 3):
                        valid_sources.append(source)
                
                return valid_sources[:max_results]
            else:
                logger.warning(f"ZenRows returned {response.status_code}")
                return []
                
    except Exception as e:
        logger.error(f"ZenRows Google search failed: {e}")
        return []

def _parse_google_method1(html: str) -> List[ResearchSource]:
    """Primary Google parsing method"""
    sources = []
    try:
        # Standard Google result structure
        pattern = r'<h3[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>([^<]+)</a>.*?</h3>.*?<span[^>]*>([^<]*)</span>'
        matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
        
        for url, title, snippet in matches:
            if url.startswith("http"):
                sources.append(ResearchSource(
                    name="zenrows",
                    url=url,
                    title=title.strip(),
                    snippet=snippet.strip()[:200],
                    relevance_score=0.8
                ))
    except Exception as e:
        logger.debug(f"Parse method 1 failed: {e}")
    
    return sources

def _parse_google_method2(html: str) -> List[ResearchSource]:
    """Alternative Google parsing method"""
    sources = []
    try:
        # Div-based structure
        div_pattern = r'<div[^>]*class="[^"]*g[^"]*"[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>.*?<h3[^>]*>([^<]+)</h3>.*?</div>'
        matches = re.findall(div_pattern, html, re.DOTALL | re.IGNORECASE)
        
        for url, title in matches:
            if url.startswith("http"):
                sources.append(ResearchSource(
                    name="zenrows",
                    url=url,
                    title=title.strip(),
                    snippet="Google search result",
                    relevance_score=0.7
                ))
    except Exception as e:
        logger.debug(f"Parse method 2 failed: {e}")
    
    return sources

def _parse_google_method3(html: str) -> List[ResearchSource]:
    """Fallback Google parsing method"""
    sources = []
    try:
        # Simple link extraction
        link_pattern = r'<a[^>]*href="(https?://[^"]*)"[^>]*>([^<]+)</a>'
        matches = re.findall(link_pattern, html, re.IGNORECASE)
        
        seen_urls = set()
        for url, title in matches:
            if (url not in seen_urls and 
                not any(skip in url for skip in ['google.com', 'youtube.com', 'facebook.com']) and
                len(title.strip()) > 5):
                
                seen_urls.add(url)
                sources.append(ResearchSource(
                    name="zenrows",
                    url=url,
                    title=title.strip(),
                    snippet="Extracted link",
                    relevance_score=0.6
                ))
                
                if len(sources) >= 5:
                    break
                    
    except Exception as e:
        logger.debug(f"Parse method 3 failed: {e}")
    
    return sources

async def _zenrows_reddit_search(query: str, api_key: str, max_results: int) -> List[ResearchSource]:
    """Reddit search through ZenRows"""
    sources = []
    
    try:
        reddit_url = f"https://www.reddit.com/search/?q={query.replace(' ', '+')}"
        
        params = {
            "url": reddit_url,
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
                
                # Parse Reddit posts
                post_pattern = r'<a[^>]*href="(/r/[^"]*)"[^>]*>([^<]+)</a>'
                matches = re.findall(post_pattern, html_content, re.IGNORECASE)
                
                for path, title in matches[:max_results]:
                    url = f"https://www.reddit.com{path}"
                    sources.append(ResearchSource(
                        name="zenrows-reddit",
                        url=url,
                        title=title.strip(),
                        snippet="Reddit discussion",
                        relevance_score=0.6
                    ))
                        
    except Exception as e:
        logger.error(f"ZenRows Reddit search failed: {e}")
    
    return sources

async def search_apify_robust(query: str, max_results: int) -> List[ResearchSource]:
    """Robust Apify search with enhanced error handling"""
    try:
        api_token = os.getenv("APIFY_API_TOKEN")
        if not api_token:
            return []
        
        sources = []
        
        # Use Google Search Scraper
        try:
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
                "countryCode": "US"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    apify_url,
                    headers=headers,
                    json=payload,
                    timeout=25.0
                )
                
                if response.status_code == 200:
                    results = response.json()
                    
                    for item in results:
                        if isinstance(item, dict) and item.get("url") and item.get("title"):
                            sources.append(ResearchSource(
                                name="apify",
                                url=item.get("url"),
                                title=item.get("title"),
                                snippet=item.get("description", "")[:200],
                                relevance_score=0.8
                            ))
                else:
                    logger.warning(f"Apify API error: {response.status_code}")
                    
        except Exception as e:
            logger.warning(f"Apify search failed: {e}")
        
        logger.info(f"Apify returned {len(sources)} sources")
        return sources[:max_results]
        
    except Exception as e:
        logger.error(f"Apify search failed: {e}")
        return []

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
        for i, source in enumerate(sources[:5]):
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
        for source in sources[:3]:
            content = source.content or source.snippet
            if content:
                # Split into sentences
                source_sentences = re.split(r'[.!?]+', content)
                for sentence in source_sentences:
                    if len(sentence.strip()) > 20:
                        # Score based on query term overlap
                        sentence_terms = set(sentence.lower().split())
                        overlap = len(query_terms.intersection(sentence_terms))
                        if overlap > 0:
                            sentences.append((sentence.strip(), overlap))
        
        # Sort by relevance and take top sentences
        sentences.sort(key=lambda x: x[1], reverse=True)
        top_sentences = [s[0] for s in sentences[:3]]
        
        if top_sentences:
            return " ".join(top_sentences)
        else:
            return None
            
    except Exception as e:
        logger.error(f"Extractive summary failed: {e}")
        return None

def _generate_fallback_summary(sources: List[ResearchSource]) -> str:
    """Generate simple fallback summary"""
    if not sources:
        return "No sources found for the query."
    
    summary_parts = [f"Found {len(sources)} relevant sources:"]
    
    for i, source in enumerate(sources[:3], 1):
        title = source.title[:100] if source.title else "Untitled"
        summary_parts.append(f"{i}. {title}")
    
    if len(sources) > 3:
        summary_parts.append(f"...and {len(sources) - 3} more sources.")
    
    return " ".join(summary_parts)

def remove_duplicate_sources(sources: List[ResearchSource]) -> List[ResearchSource]:
    """Remove duplicate sources based on URL"""
    seen_urls = set()
    unique_sources = []
    
    for source in sources:
        if source.url and source.url not in seen_urls:
            seen_urls.add(source.url)
            unique_sources.append(source)
    
    return unique_sources

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

