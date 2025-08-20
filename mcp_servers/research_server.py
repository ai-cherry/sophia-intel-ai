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
    """Search using ZenRows for web scraping."""
    try:
        # TODO: Implement ZenRows web scraping
        logger.warning("ZenRows search not yet implemented")
        return []
        
    except Exception as e:
        logger.error(f"ZenRows search failed: {e}")
        return []

async def search_apify(query: str, api_token: str, max_results: int = 10) -> List[ResearchSource]:
    """Search using Apify actors."""
    try:
        # TODO: Implement Apify actor calls
        logger.warning("Apify search not yet implemented")
        return []
        
    except Exception as e:
        logger.error(f"Apify search failed: {e}")
        return []

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

