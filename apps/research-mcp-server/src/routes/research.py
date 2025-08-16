"""
SOPHIA Intel Research MCP Server Routes
BrightData integration for unstoppable web data ingestion
"""

from flask import Blueprint, request, jsonify
import os
import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union
import json
import time

# Create blueprint
research_bp = Blueprint('research', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResearchMCP:
    """Research MCP for web data ingestion using BrightData"""
    
    def __init__(self):
        # Get API key from environment variables (populated by Kubernetes secrets)
        self.brightdata_api_key = os.getenv("BRIGHTDATA_API_KEY")
        
        # BrightData configuration
        self.base_url = "https://api.brightdata.com"
        self.session = requests.Session()
        
        if self.brightdata_api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {self.brightdata_api_key}",
                "Content-Type": "application/json"
            })
        
        logger.info("Research MCP initialized with BrightData integration")
    
    def get_web_data(self, url: str, strategy: str = "unlocker") -> Dict:
        """Get web data using specified strategy"""
        try:
            if not self.brightdata_api_key:
                return {"error": "BrightData API key not configured"}
            
            if strategy == "unlocker":
                return self._unlocker_strategy(url)
            elif strategy == "browser":
                return self._browser_strategy(url)
            elif strategy == "serp":
                return self._serp_strategy(url)
            else:
                return {"error": f"Unknown strategy: {strategy}. Use 'unlocker', 'browser', or 'serp'"}
                
        except Exception as e:
            logger.error(f"Error getting web data: {e}")
            return {"error": str(e)}
    
    def _unlocker_strategy(self, url: str) -> Dict:
        """Use BrightData Unlocker for anti-bot bypass"""
        try:
            # BrightData Unlocker API endpoint
            endpoint = f"{self.base_url}/unlocker/v1/scrape"
            
            payload = {
                "url": url,
                "format": "html",
                "country": "US",
                "render_js": True,
                "wait_for": 3000  # Wait 3 seconds for JS to load
            }
            
            response = self.session.post(endpoint, json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "strategy": "unlocker",
                    "url": url,
                    "content": data.get("content", ""),
                    "status_code": data.get("status_code", 200),
                    "headers": data.get("headers", {}),
                    "metadata": {
                        "render_time_ms": data.get("render_time", 0),
                        "country": "US",
                        "anti_bot_bypass": True
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {"error": f"BrightData Unlocker error: {response.status_code} - {response.text}"}
                
        except Exception as e:
            return {"error": f"Unlocker strategy failed: {str(e)}"}
    
    def _browser_strategy(self, url: str) -> Dict:
        """Use BrightData Browser for JavaScript execution"""
        try:
            # BrightData Browser API endpoint
            endpoint = f"{self.base_url}/browser/v1/scrape"
            
            payload = {
                "url": url,
                "browser": "chrome",
                "viewport": {"width": 1920, "height": 1080},
                "wait_for": "networkidle",
                "timeout": 30000,
                "screenshot": True,
                "extract": {
                    "title": "document.title",
                    "text": "document.body.innerText",
                    "links": "Array.from(document.querySelectorAll('a')).map(a => ({href: a.href, text: a.textContent}))"
                }
            }
            
            response = self.session.post(endpoint, json=payload, timeout=90)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "strategy": "browser",
                    "url": url,
                    "content": data.get("html", ""),
                    "extracted_data": data.get("extract", {}),
                    "screenshot": data.get("screenshot", ""),
                    "metadata": {
                        "browser": "chrome",
                        "viewport": "1920x1080",
                        "javascript_executed": True,
                        "load_time_ms": data.get("load_time", 0)
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {"error": f"BrightData Browser error: {response.status_code} - {response.text}"}
                
        except Exception as e:
            return {"error": f"Browser strategy failed: {str(e)}"}
    
    def _serp_strategy(self, query: str) -> Dict:
        """Use BrightData SERP API for search results"""
        try:
            # BrightData SERP API endpoint
            endpoint = f"{self.base_url}/serp/v1/search"
            
            payload = {
                "q": query,
                "engine": "google",
                "location": "United States",
                "hl": "en",
                "gl": "us",
                "num": 10,
                "safe": "off"
            }
            
            response = self.session.post(endpoint, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "strategy": "serp",
                    "query": query,
                    "results": data.get("organic_results", []),
                    "knowledge_graph": data.get("knowledge_graph", {}),
                    "related_searches": data.get("related_searches", []),
                    "metadata": {
                        "engine": "google",
                        "location": "United States",
                        "total_results": data.get("search_information", {}).get("total_results", 0),
                        "search_time": data.get("search_information", {}).get("time_taken", 0)
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {"error": f"BrightData SERP error: {response.status_code} - {response.text}"}
                
        except Exception as e:
            return {"error": f"SERP strategy failed: {str(e)}"}
    
    def batch_research(self, requests_list: List[Dict]) -> Dict:
        """Process multiple research requests in batch"""
        try:
            results = []
            errors = []
            
            for i, req in enumerate(requests_list):
                url = req.get("url", "")
                strategy = req.get("strategy", "unlocker")
                
                if not url:
                    errors.append({"index": i, "error": "Missing URL"})
                    continue
                
                result = self.get_web_data(url, strategy)
                if "error" in result:
                    errors.append({"index": i, "url": url, "error": result["error"]})
                else:
                    results.append({"index": i, "data": result})
                
                # Rate limiting - small delay between requests
                time.sleep(0.5)
            
            return {
                "results": results,
                "errors": errors,
                "total_processed": len(requests_list),
                "successful": len(results),
                "failed": len(errors),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_research_capabilities(self) -> Dict:
        """Get available research capabilities and status"""
        return {
            "strategies": {
                "unlocker": {
                    "description": "Anti-bot bypass for protected websites",
                    "features": ["JavaScript rendering", "Proxy rotation", "CAPTCHA solving"],
                    "use_cases": ["E-commerce sites", "Social media", "Protected content"]
                },
                "browser": {
                    "description": "Full browser automation with JavaScript execution",
                    "features": ["Chrome browser", "Screenshot capture", "Data extraction", "Network monitoring"],
                    "use_cases": ["SPAs", "Dynamic content", "Complex interactions"]
                },
                "serp": {
                    "description": "Search engine results parsing",
                    "features": ["Google search", "Knowledge graph", "Related searches", "Organic results"],
                    "use_cases": ["Market research", "Competitor analysis", "Trend monitoring"]
                }
            },
            "configuration": {
                "brightdata_configured": bool(self.brightdata_api_key),
                "rate_limits": "0.5s between requests",
                "timeout": "60s for unlocker, 90s for browser, 30s for SERP"
            },
            "timestamp": datetime.utcnow().isoformat()
        }

# Initialize research MCP
research_mcp = ResearchMCP()

@research_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "service": "research-mcp",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "brightdata_configured": bool(research_mcp.brightdata_api_key)
    })

@research_bp.route('/capabilities', methods=['GET'])
def get_capabilities():
    """Get research capabilities"""
    return jsonify(research_mcp.get_research_capabilities())

@research_bp.route('/scrape', methods=['POST'])
def scrape_web_data():
    """Scrape web data using specified strategy"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({"error": "Missing 'url' field in request"}), 400
        
        url = data['url']
        strategy = data.get('strategy', 'unlocker')
        
        result = research_mcp.get_web_data(url, strategy)
        
        if "error" in result:
            return jsonify(result), 400
        else:
            return jsonify(result)
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@research_bp.route('/batch', methods=['POST'])
def batch_research():
    """Process multiple research requests"""
    try:
        data = request.get_json()
        if not data or 'requests' not in data:
            return jsonify({"error": "Missing 'requests' field in request"}), 400
        
        requests_list = data['requests']
        
        if not isinstance(requests_list, list):
            return jsonify({"error": "'requests' must be a list"}), 400
        
        result = research_mcp.batch_research(requests_list)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@research_bp.route('/test', methods=['GET'])
def test_research():
    """Test research capabilities with sample requests"""
    test_cases = [
        {"url": "https://example.com", "strategy": "unlocker"},
        {"url": "https://httpbin.org/json", "strategy": "browser"},
        {"query": "AI news 2024", "strategy": "serp"}
    ]
    
    results = []
    for test_case in test_cases:
        if "query" in test_case:
            # SERP test
            result = research_mcp._serp_strategy(test_case["query"])
        else:
            # Web scraping test
            result = research_mcp.get_web_data(test_case["url"], test_case["strategy"])
        
        results.append({
            "test_case": test_case,
            "success": "error" not in result,
            "result": result if "error" not in result else {"error": result["error"]}
        })
    
    return jsonify({
        "test_status": "completed",
        "results": results,
        "timestamp": datetime.utcnow().isoformat()
    })

