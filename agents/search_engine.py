# agents/search_engine.py
import aiohttp
import asyncio
import json
import os
from typing import List, Dict, Optional
import time
from urllib.parse import quote_plus

class DeepSearchEngine:
    def __init__(self):
        self.providers = {
            "duckduckgo": {
                "url": "https://api.duckduckgo.com/",
                "headers": {},
                "enabled": True
            },
            "brightdata": {
                "url": "https://api.brightdata.com/search",
                "headers": {"Authorization": f"Bearer {os.getenv('BRIGHTDATA_API_KEY', '')}"},
                "enabled": bool(os.getenv('BRIGHTDATA_API_KEY'))
            },
            "serper": {
                "url": "https://google.serper.dev/search",
                "headers": {"X-API-KEY": os.getenv('SERPER_API_KEY', '')},
                "enabled": bool(os.getenv('SERPER_API_KEY'))
            }
        }
    
    async def search_duckduckgo(self, query: str, limit: int = 5) -> List[Dict]:
        """Search using DuckDuckGo API"""
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "q": query,
                    "format": "json",
                    "no_html": "1",
                    "skip_disambig": "1"
                }
                
                async with session.get(
                    "https://api.duckduckgo.com/",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []
                        
                        # Process RelatedTopics
                        for topic in data.get("RelatedTopics", [])[:limit]:
                            if isinstance(topic, dict) and "Text" in topic:
                                results.append({
                                    "title": topic.get("Text", "")[:100] + "...",
                                    "url": topic.get("FirstURL", ""),
                                    "summary": topic.get("Text", ""),
                                    "source": "DuckDuckGo",
                                    "relevance_score": 0.7
                                })
                        
                        # If no RelatedTopics, use Abstract
                        if not results and data.get("Abstract"):
                            results.append({
                                "title": data.get("Heading", query),
                                "url": data.get("AbstractURL", ""),
                                "summary": data.get("Abstract", ""),
                                "source": "DuckDuckGo",
                                "relevance_score": 0.8
                            })
                        
                        return results[:limit]
                    
        except Exception as e:
            print(f"DuckDuckGo search error: {str(e)}")
        
        return []
    
    async def search_brightdata(self, query: str, limit: int = 5) -> List[Dict]:
        """Search using Bright Data API"""
        if not self.providers["brightdata"]["enabled"]:
            return []
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "query": query,
                    "limit": limit,
                    "country": "US"
                }
                
                async with session.post(
                    self.providers["brightdata"]["url"],
                    headers=self.providers["brightdata"]["headers"],
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []
                        
                        for item in data.get("results", [])[:limit]:
                            results.append({
                                "title": item.get("title", ""),
                                "url": item.get("url", ""),
                                "summary": item.get("snippet", ""),
                                "source": "Bright Data",
                                "relevance_score": item.get("relevance", 0.8)
                            })
                        
                        return results
                    
        except Exception as e:
            print(f"Bright Data search error: {str(e)}")
        
        return []
    
    async def search_serper(self, query: str, limit: int = 5) -> List[Dict]:
        """Search using Serper Google API"""
        if not self.providers["serper"]["enabled"]:
            return []
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "q": query,
                    "num": limit
                }
                
                async with session.post(
                    self.providers["serper"]["url"],
                    headers=self.providers["serper"]["headers"],
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []
                        
                        for item in data.get("organic", [])[:limit]:
                            results.append({
                                "title": item.get("title", ""),
                                "url": item.get("link", ""),
                                "summary": item.get("snippet", ""),
                                "source": "Google (Serper)",
                                "relevance_score": 0.9
                            })
                        
                        return results
                    
        except Exception as e:
            print(f"Serper search error: {str(e)}")
        
        return []
    
    async def extract_content(self, url: str) -> str:
        """Extract content from a URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=10),
                    headers={"User-Agent": "SOPHIA-AI/4.0 (Autonomous Research Bot)"}
                ) as response:
                    if response.status == 200:
                        content = await response.text()
                        # Simple content extraction - in production, use proper HTML parsing
                        return content[:1000] + "..." if len(content) > 1000 else content
        except Exception as e:
            print(f"Content extraction error for {url}: {str(e)}")
        
        return "Content extraction failed"
    
    async def perform_multi_provider_search(self, query: str, sources_limit: int = 5) -> List[Dict]:
        """Perform search across multiple providers and aggregate results"""
        search_tasks = []
        
        # Create search tasks for enabled providers
        if self.providers["duckduckgo"]["enabled"]:
            search_tasks.append(self.search_duckduckgo(query, sources_limit))
        
        if self.providers["brightdata"]["enabled"]:
            search_tasks.append(self.search_brightdata(query, sources_limit))
        
        if self.providers["serper"]["enabled"]:
            search_tasks.append(self.search_serper(query, sources_limit))
        
        # Execute searches in parallel
        try:
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Aggregate and deduplicate results
            all_results = []
            seen_urls = set()
            
            for provider_results in search_results:
                if isinstance(provider_results, list):
                    for result in provider_results:
                        url = result.get("url", "")
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            all_results.append(result)
            
            # Sort by relevance score and limit results
            all_results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
            return all_results[:sources_limit]
            
        except Exception as e:
            print(f"Multi-provider search error: {str(e)}")
            return []
    
    async def plan_query(self, query: str) -> List[str]:
        """Break down complex queries into sub-queries"""
        # Simple query planning - in production, use LLM for better decomposition
        keywords = query.lower().split()
        
        if len(keywords) <= 3:
            return [query]
        
        # Create sub-queries for complex queries
        sub_queries = [query]
        
        # Add specific sub-queries based on keywords
        if any(word in keywords for word in ["latest", "recent", "new", "2024", "2025"]):
            sub_queries.append(f"{query} latest trends")
        
        if any(word in keywords for word in ["how", "what", "why", "when"]):
            sub_queries.append(f"{query} explanation")
        
        if any(word in keywords for word in ["best", "top", "comparison"]):
            sub_queries.append(f"{query} comparison review")
        
        return sub_queries[:3]  # Limit to 3 sub-queries
    
    async def synthesize_answer(self, results: List[Dict], query: str) -> Dict:
        """Synthesize search results into a coherent answer"""
        if not results:
            return {
                "answer": "I couldn't find specific information about that topic, partner. Want me to try a different search approach?",
                "sources": [],
                "confidence": 0.0
            }
        
        # Simple synthesis - in production, use LLM for better synthesis
        sources = []
        for result in results:
            sources.append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "summary": result.get("summary", ""),
                "source": result.get("source", ""),
                "relevance_score": result.get("relevance_score", 0.0)
            })
        
        # Generate summary based on sources
        if len(sources) > 0:
            answer = f"Based on my search across {len(set(s['source'] for s in sources))} sources, I found {len(sources)} relevant results about '{query}'. "
            
            if sources[0]["summary"]:
                answer += f"Key insight: {sources[0]['summary'][:200]}..."
        else:
            answer = "I found some results but couldn't extract meaningful content. The sources are available for your review."
        
        return {
            "answer": answer,
            "sources": sources,
            "confidence": min(sum(s["relevance_score"] for s in sources) / len(sources), 1.0) if sources else 0.0
        }

