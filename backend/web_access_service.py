"""
Unified Web Access Service for SOPHIA Intel
Integrates Bright Data, Apify, and ZenRows for comprehensive web scraping and search
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx
from loguru import logger
from pydantic import BaseModel

from config.config import settings


class WebSearchRequest(BaseModel):
    query: str
    max_results: int = 10
    strategy: str = "auto"  # auto, apify, brightdata


class WebScrapeRequest(BaseModel):
    url: str
    strategy: str = "auto"  # auto, brightdata, zenrows, apify
    extract_text: bool = True
    extract_links: bool = False
    extract_images: bool = False


class WebAccessService:
    """
    Unified web access service that abstracts multiple providers:
    - Bright Data: Browser-like scraping for JS-heavy pages
    - Apify: Specialized actors for structured data extraction
    - ZenRows: Simple HTML extraction with anti-bot handling
    """

    def __init__(self):
        self.brightdata_key = getattr(settings, "BRIGHTDATA_API_KEY", "")
        self.apify_key = getattr(settings, "APIFY_API_KEY", "")
        self.zenrows_key = getattr(settings, "ZENROWS_API_KEY", "")

        # Cache for results (simple in-memory cache)
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes

        # Rate limiting
        self.last_request_time = {}
        self.min_request_interval = 1.0  # 1 second between requests per provider

    async def search(self, query: str, max_results: int = 10, strategy: str = "auto") -> List[Dict[str, Any]]:
        """
        Perform web search using the best available provider
        """
        cache_key = f"search:{query}:{max_results}:{strategy}"

        # Check cache first
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            logger.debug(f"Cache hit for search: {query[:50]}")
            return cached_result

        try:
            if strategy == "auto":
                # Try Apify first, fallback to Bright Data
                if self.apify_key:
                    results = await self._apify_search(query, max_results)
                elif self.brightdata_key:
                    results = await self._brightdata_search(query, max_results)
                else:
                    raise ValueError("No search providers configured")
            elif strategy == "apify" and self.apify_key:
                results = await self._apify_search(query, max_results)
            elif strategy == "brightdata" and self.brightdata_key:
                results = await self._brightdata_search(query, max_results)
            else:
                raise ValueError(f"Strategy '{strategy}' not available or not configured")

            # Cache results
            self._cache_result(cache_key, results)
            return results

        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return []

    async def scrape(
        self,
        url: str,
        strategy: str = "auto",
        extract_text: bool = True,
        extract_links: bool = False,
        extract_images: bool = False,
    ) -> Dict[str, Any]:
        """
        Scrape content from a URL using the best available provider
        """
        cache_key = f"scrape:{url}:{strategy}:{extract_text}:{extract_links}:{extract_images}"

        # Check cache first
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            logger.debug(f"Cache hit for scrape: {url}")
            return cached_result

        try:
            if strategy == "auto":
                # Decide based on URL characteristics
                if self._needs_browser_rendering(url):
                    if self.brightdata_key:
                        result = await self._brightdata_scrape(url, extract_text, extract_links, extract_images)
                    elif self.zenrows_key:
                        result = await self._zenrows_scrape(url, extract_text, extract_links, extract_images)
                    else:
                        raise ValueError("No browser-capable providers configured")
                else:
                    if self.zenrows_key:
                        result = await self._zenrows_scrape(url, extract_text, extract_links, extract_images)
                    elif self.brightdata_key:
                        result = await self._brightdata_scrape(url, extract_text, extract_links, extract_images)
                    else:
                        raise ValueError("No scraping providers configured")
            elif strategy == "brightdata" and self.brightdata_key:
                result = await self._brightdata_scrape(url, extract_text, extract_links, extract_images)
            elif strategy == "zenrows" and self.zenrows_key:
                result = await self._zenrows_scrape(url, extract_text, extract_links, extract_images)
            elif strategy == "apify" and self.apify_key:
                result = await self._apify_scrape(url, extract_text, extract_links, extract_images)
            else:
                raise ValueError(f"Strategy '{strategy}' not available or not configured")

            # Cache results
            self._cache_result(cache_key, result)
            return result

        except Exception as e:
            logger.error(f"Web scraping failed for {url}: {e}")
            return {
                "url": url,
                "error": str(e),
                "success": False,
                "content": "",
                "title": "",
                "links": [],
                "images": [],
            }

    async def _apify_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search using Apify Google Search actor"""
        await self._rate_limit("apify")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Start Apify actor run
                run_response = await client.post(
                    "https://api.apify.com/v2/acts/apify~google-search-results-scraper/runs",
                    headers={"Authorization": f"Bearer {self.apify_key}"},
                    json={
                        "queries": [query],
                        "maxPagesPerQuery": 1,
                        "resultsPerPage": max_results,
                        "mobileResults": False,
                        "languageCode": "en",
                        "countryCode": "US",
                    },
                )
                run_response.raise_for_status()
                run_data = run_response.json()
                run_id = run_data["data"]["id"]

                # Wait for completion and get results
                for _ in range(30):  # Wait up to 30 seconds
                    await asyncio.sleep(1)

                    status_response = await client.get(
                        f"https://api.apify.com/v2/acts/runs/{run_id}",
                        headers={"Authorization": f"Bearer {self.apify_key}"},
                    )
                    status_data = status_response.json()

                    if status_data["data"]["status"] == "SUCCEEDED":
                        # Get results
                        results_response = await client.get(
                            f"https://api.apify.com/v2/datasets/{status_data['data']['defaultDatasetId']}/items",
                            headers={"Authorization": f"Bearer {self.apify_key}"},
                        )
                        results_data = results_response.json()

                        # Format results
                        formatted_results = []
                        for item in results_data:
                            if "organicResults" in item:
                                for result in item["organicResults"]:
                                    formatted_results.append(
                                        {
                                            "title": result.get("title", ""),
                                            "url": result.get("url", ""),
                                            "snippet": result.get("description", ""),
                                            "source": "apify",
                                        }
                                    )

                        return formatted_results[:max_results]

                raise TimeoutError("Apify search timed out")

        except Exception as e:
            logger.error(f"Apify search failed: {e}")
            raise

    async def _brightdata_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search using Bright Data SERP API"""
        await self._rate_limit("brightdata")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(
                    "https://api.brightdata.com/serp/google/search",
                    headers={"Authorization": f"Bearer {self.brightdata_key}"},
                    params={"q": query, "num": max_results, "hl": "en", "gl": "us"},
                )
                response.raise_for_status()
                data = response.json()

                # Format results
                formatted_results = []
                for result in data.get("organic_results", []):
                    formatted_results.append(
                        {
                            "title": result.get("title", ""),
                            "url": result.get("link", ""),
                            "snippet": result.get("snippet", ""),
                            "source": "brightdata",
                        }
                    )

                return formatted_results

        except Exception as e:
            logger.error(f"Bright Data search failed: {e}")
            raise

    async def _brightdata_scrape(
        self, url: str, extract_text: bool, extract_links: bool, extract_images: bool
    ) -> Dict[str, Any]:
        """Scrape using Bright Data browser API"""
        await self._rate_limit("brightdata")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.brightdata.com/web-scraper/trigger",
                    headers={"Authorization": f"Bearer {self.brightdata_key}"},
                    json={
                        "url": url,
                        "format": "json",
                        "render_js": True,
                        "extract_text": extract_text,
                        "extract_links": extract_links,
                        "extract_images": extract_images,
                    },
                )
                response.raise_for_status()
                data = response.json()

                return {
                    "url": url,
                    "success": True,
                    "title": data.get("title", ""),
                    "content": data.get("text", ""),
                    "links": data.get("links", []) if extract_links else [],
                    "images": data.get("images", []) if extract_images else [],
                    "source": "brightdata",
                }

        except Exception as e:
            logger.error(f"Bright Data scraping failed: {e}")
            raise

    async def _zenrows_scrape(
        self, url: str, extract_text: bool, extract_links: bool, extract_images: bool
    ) -> Dict[str, Any]:
        """Scrape using ZenRows API"""
        await self._rate_limit("zenrows")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                params = {"url": url, "apikey": self.zenrows_key, "js_render": "true", "antibot": "true"}

                if extract_text:
                    params["css_extractor"] = json.dumps({"title": "title", "content": "body"})

                response = await client.get("https://api.zenrows.com/v1/", params=params)
                response.raise_for_status()

                # Parse response based on content type
                if "application/json" in response.headers.get("content-type", ""):
                    data = response.json()
                    return {
                        "url": url,
                        "success": True,
                        "title": data.get("title", ""),
                        "content": data.get("content", ""),
                        "links": [],  # ZenRows doesn't extract links by default
                        "images": [],  # ZenRows doesn't extract images by default
                        "source": "zenrows",
                    }
                else:
                    # HTML response - extract basic info
                    html_content = response.text
                    return {
                        "url": url,
                        "success": True,
                        "title": self._extract_title_from_html(html_content),
                        "content": self._extract_text_from_html(html_content),
                        "links": [],
                        "images": [],
                        "source": "zenrows",
                    }

        except Exception as e:
            logger.error(f"ZenRows scraping failed: {e}")
            raise

    async def _apify_scrape(
        self, url: str, extract_text: bool, extract_links: bool, extract_images: bool
    ) -> Dict[str, Any]:
        """Scrape using Apify Web Scraper actor"""
        await self._rate_limit("apify")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Start Apify web scraper run
                run_response = await client.post(
                    "https://api.apify.com/v2/acts/apify~web-scraper/runs",
                    headers={"Authorization": f"Bearer {self.apify_key}"},
                    json={
                        "startUrls": [{"url": url}],
                        "pageFunction": """
                        async function pageFunction(context) {
                            const { page, request } = context;
                            const title = await page.title();
                            const content = await page.evaluate(() => document.body.innerText);
                            return { title, content, url: request.url };
                        }
                        """,
                    },
                )
                run_response.raise_for_status()
                run_data = run_response.json()
                run_id = run_data["data"]["id"]

                # Wait for completion and get results
                for _ in range(30):  # Wait up to 30 seconds
                    await asyncio.sleep(1)

                    status_response = await client.get(
                        f"https://api.apify.com/v2/acts/runs/{run_id}",
                        headers={"Authorization": f"Bearer {self.apify_key}"},
                    )
                    status_data = status_response.json()

                    if status_data["data"]["status"] == "SUCCEEDED":
                        # Get results
                        results_response = await client.get(
                            f"https://api.apify.com/v2/datasets/{status_data['data']['defaultDatasetId']}/items",
                            headers={"Authorization": f"Bearer {self.apify_key}"},
                        )
                        results_data = results_response.json()

                        if results_data:
                            result = results_data[0]
                            return {
                                "url": url,
                                "success": True,
                                "title": result.get("title", ""),
                                "content": result.get("content", ""),
                                "links": [],
                                "images": [],
                                "source": "apify",
                            }

                raise TimeoutError("Apify scraping timed out")

        except Exception as e:
            logger.error(f"Apify scraping failed: {e}")
            raise

    def _needs_browser_rendering(self, url: str) -> bool:
        """Determine if URL likely needs browser rendering"""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Domains that typically require JS rendering
        js_heavy_domains = [
            "twitter.com",
            "x.com",
            "facebook.com",
            "instagram.com",
            "linkedin.com",
            "youtube.com",
            "tiktok.com",
            "pinterest.com",
            "reddit.com",
            "medium.com",
            "substack.com",
        ]

        return any(domain.endswith(js_domain) for js_domain in js_heavy_domains)

    def _extract_title_from_html(self, html: str) -> str:
        """Extract title from HTML content"""
        import re

        title_match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
        return title_match.group(1).strip() if title_match else ""

    def _extract_text_from_html(self, html: str) -> str:
        """Extract text content from HTML"""
        import re

        # Remove script and style elements
        html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", html)
        # Clean up whitespace
        text = re.sub(r"\\s+", " ", text).strip()
        return text[:5000]  # Limit to 5000 characters

    async def _rate_limit(self, provider: str):
        """Enforce rate limiting per provider"""
        current_time = time.time()
        last_time = self.last_request_time.get(provider, 0)

        if current_time - last_time < self.min_request_interval:
            sleep_time = self.min_request_interval - (current_time - last_time)
            await asyncio.sleep(sleep_time)

        self.last_request_time[provider] = time.time()

    def _get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Get result from cache if not expired"""
        if cache_key in self.cache:
            cached_item = self.cache[cache_key]
            if time.time() - cached_item["timestamp"] < self.cache_ttl:
                return cached_item["data"]
            else:
                del self.cache[cache_key]
        return None

    def _cache_result(self, cache_key: str, data: Any):
        """Cache result with timestamp"""
        self.cache[cache_key] = {"data": data, "timestamp": time.time()}

        # Simple cache cleanup - remove oldest entries if cache gets too large
        if len(self.cache) > 1000:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest_key]
