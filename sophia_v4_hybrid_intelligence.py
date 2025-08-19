#!/usr/bin/env python3
"""
SOPHIA V4 Hybrid Intelligence - Dynamic Web + Internal Data Fusion! 🤠🔥
Repository: https://github.com/ai-cherry/sophia-intel
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import requests
import os
import logging
import uuid
import subprocess
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
import sentry_sdk
from github import Github
import glob

# Initialize Sentry for monitoring
sentry_sdk.init(dsn=os.getenv('SENTRY_DSN', ''))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="SOPHIA V4 Hybrid Intelligence",
    description="The most badass AI with dynamic web + internal data fusion! 🤠",
    version="4.0.0-HYBRID-INTELLIGENCE"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize GitHub
g = Github(os.getenv('GITHUB_TOKEN'))
repo = g.get_repo('ai-cherry/sophia-intel')

# Pydantic models
class ChatRequest(BaseModel):
    query: str
    user_id: str
    sources_limit: int = 3
    action: str = 'search'

class SelfRequest(BaseModel):
    action: str
    query: str = ''
    user_id: str

# Internal data functions
async def get_internal_repo_data():
    """Get SOPHIA's internal repository data"""
    try:
        contents = repo.get_contents('', ref='main')
        structure = {
            'repository': 'ai-cherry/sophia-intel',
            'files': {},
            'python_files': [],
            'docs': [],
            'configs': [],
            'total_files': 0
        }
        
        def parse_contents(items, path=''):
            for item in items:
                key = f'{path}/{item.path}' if path else item.path
                structure['total_files'] += 1
                
                if item.type == 'dir':
                    structure['files'][key] = {'type': 'directory'}
                    try:
                        parse_contents(repo.get_contents(item.path, ref='main'), key)
                    except:
                        pass
                else:
                    structure['files'][key] = {
                        'type': 'file', 
                        'size': item.size, 
                        'sha': item.sha[:8]
                    }
                    
                    if item.name.endswith('.py'):
                        structure['python_files'].append(key)
                    elif item.name.endswith('.md'):
                        structure['docs'].append(key)
                    elif item.name in ['fly.toml', 'Dockerfile', 'requirements.txt']:
                        structure['configs'].append(key)
        
        parse_contents(contents)
        
        # Get recent commits
        commits = repo.get_commits()[:3]
        structure['recent_commits'] = [
            {
                'sha': commit.sha[:8],
                'message': commit.commit.message.split('\n')[0][:80],
                'author': commit.commit.author.name,
                'date': commit.commit.author.date.strftime('%Y-%m-%d %H:%M')
            }
            for commit in commits
        ]
        
        return structure
    except Exception as e:
        logger.error(f"Internal repo data failed: {e}")
        return {'error': str(e)}

async def get_internal_infra_data():
    """Get SOPHIA's internal infrastructure data"""
    try:
        # Get Fly.io status
        try:
            status = subprocess.check_output(['flyctl', 'status', '--app', 'sophia-intel', '--json'], timeout=10).decode()
            status_json = json.loads(status)
            machines = status_json.get('Machines', [])
        except:
            machines = []
        
        # Get health status
        try:
            health = requests.get('https://sophia-intel.fly.dev/api/v1/health', timeout=5).json()
        except:
            health = {'status': 'unknown'}
        
        return {
            'app': 'sophia-intel',
            'machines': len(machines),
            'regions': list(set(m.get('region', 'unknown') for m in machines)),
            'health': health.get('status', 'unknown'),
            'url': 'https://sophia-intel.fly.dev',
            'version': health.get('version', '4.0.0'),
            'mode': health.get('mode', 'HYBRID_INTELLIGENCE')
        }
    except Exception as e:
        logger.error(f"Internal infra data failed: {e}")
        return {'error': str(e)}

async def get_internal_api_data():
    """Get SOPHIA's internal API configuration"""
    try:
        # Check environment variables
        api_status = {
            'search_apis': {
                'serper': bool(os.getenv('SERPER_API_KEY')),
                'brave': bool(os.getenv('BRAVE_API_KEY')),
                'tavily': bool(os.getenv('TAVILY_API_KEY')),
                'brightdata': bool(os.getenv('BRIGHTDATA_API_KEY')),
                'zenrows': bool(os.getenv('ZENROWS_API_KEY')),
                'apify': bool(os.getenv('APIFY_API_TOKEN'))
            },
            'ai_apis': {
                'grok': bool(os.getenv('GROK_API_KEY')),
                'huggingface': bool(os.getenv('HUGGINGFACE_API_TOKEN')),
                'openrouter': bool(os.getenv('OPENROUTER_API_KEY'))
            },
            'business_apis': {
                'github': bool(os.getenv('GITHUB_TOKEN')),
                'salesforce': bool(os.getenv('SALESFORCE_TOKEN')),
                'hubspot': bool(os.getenv('HUBSPOT_API_KEY')),
                'slack': bool(os.getenv('SLACK_TOKEN')),
                'notion': bool(os.getenv('NOTION_API_KEY'))
            }
        }
        
        total_configured = sum(
            sum(category.values()) for category in api_status.values()
        )
        
        return {
            'api_status': api_status,
            'total_configured': total_configured,
            'search_count': sum(api_status['search_apis'].values()),
            'ai_count': sum(api_status['ai_apis'].values()),
            'business_count': sum(api_status['business_apis'].values())
        }
    except Exception as e:
        logger.error(f"Internal API data failed: {e}")
        return {'error': str(e)}

# Web search functions
async def search_web_apis(query: str, sources_limit: int = 3):
    """Search external web APIs"""
    try:
        results = []
        
        # Try Serper first
        if os.getenv('SERPER_API_KEY'):
            try:
                response = requests.post(
                    'https://google.serper.dev/search',
                    headers={'X-API-KEY': os.getenv('SERPER_API_KEY')},
                    json={'q': query, 'num': sources_limit},
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get('organic', [])[:sources_limit]:
                        results.append({
                            'title': item.get('title', ''),
                            'snippet': item.get('snippet', ''),
                            'link': item.get('link', ''),
                            'source': 'Serper (Google)'
                        })
                    if results:
                        return results
            except Exception as e:
                logger.warning(f"Serper failed: {e}")
        
        # Try Brave as fallback
        if os.getenv('BRAVE_API_KEY') and not results:
            try:
                response = requests.get(
                    f'https://api.brave.com/search?q={query}&count={sources_limit}',
                    headers={'Authorization': f'Bearer {os.getenv("BRAVE_API_KEY")}'},
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get('results', [])[:sources_limit]:
                        results.append({
                            'title': item.get('title', ''),
                            'snippet': item.get('description', ''),
                            'link': item.get('url', ''),
                            'source': 'Brave Search'
                        })
            except Exception as e:
                logger.warning(f"Brave failed: {e}")
        
        return results
    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return []

async def enhance_with_grok(query: str, internal_data: dict, web_results: list):
    """Enhance response with Grok AI"""
    try:
        if not os.getenv('GROK_API_KEY'):
            return ""
        
        prompt = f"""
        Query: {query}
        Internal Data: {json.dumps(internal_data, indent=2)}
        Web Results: {json.dumps(web_results, indent=2)}
        
        Provide a comprehensive response combining internal and external data with neon cowboy personality.
        """
        
        response = requests.post(
            'https://api.x.ai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {os.getenv("GROK_API_KEY")}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'grok-beta',
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': 500
            },
            timeout=15
        )
        
        if response.status_code == 200:
            return response.json().get('choices', [{}])[0].get('message', {}).get('content', '')
    except Exception as e:
        logger.warning(f"Grok enhancement failed: {e}")
    
    return ""

# Hybrid intelligence core
async def hybrid_intelligence_response(query: str, user_id: str, sources_limit: int = 3):
    """Generate hybrid response combining internal data and web search"""
    try:
        query_lower = query.lower()
        internal_data = {}
        web_results = []
        response_parts = []
        
        # Determine what internal data to fetch
        fetch_repo = any(kw in query_lower for kw in [
            'repository', 'repo', 'github', 'ai-cherry', 'sophia-intel', 
            'files', 'commits', 'code', 'structure'
        ])
        
        fetch_infra = any(kw in query_lower for kw in [
            'infrastructure', 'deployment', 'fly.io', 'machine', 'status',
            'health', 'server', 'hosting'
        ])
        
        fetch_apis = any(kw in query_lower for kw in [
            'api', 'integration', 'capabilities', 'keys', 'services'
        ])
        
        # Fetch internal data
        if fetch_repo:
            repo_data = await get_internal_repo_data()
            internal_data['repository'] = repo_data
            response_parts.append(f"My repository at ai-cherry/sophia-intel has {repo_data.get('total_files', 0)} files including {len(repo_data.get('python_files', []))} Python modules")
        
        if fetch_infra:
            infra_data = await get_internal_infra_data()
            internal_data['infrastructure'] = infra_data
            response_parts.append(f"I'm running on {infra_data.get('machines', 0)} Fly.io machines across {len(infra_data.get('regions', []))} regions with {infra_data.get('health', 'unknown')} health status")
        
        if fetch_apis:
            api_data = await get_internal_api_data()
            internal_data['apis'] = api_data
            response_parts.append(f"I have {api_data.get('total_configured', 0)} APIs configured including {api_data.get('search_count', 0)} search APIs and {api_data.get('business_count', 0)} business integrations")
        
        # Fetch web data for external queries
        needs_web_search = not (fetch_repo or fetch_infra or fetch_apis) or any(kw in query_lower for kw in [
            'weather', 'news', 'stock', 'price', 'market', 'current', 'latest', 'recent'
        ])
        
        if needs_web_search:
            web_results = await search_web_apis(query, sources_limit)
            if web_results:
                response_parts.append(f"External search found {len(web_results)} relevant results")
        
        # Generate enhanced response with Grok
        grok_enhancement = await enhance_with_grok(query, internal_data, web_results)
        
        # Build final response
        if grok_enhancement:
            message = grok_enhancement
        else:
            # Fallback response
            if response_parts:
                message = f"Yo, partner! Here's what I found: {'. '.join(response_parts)}. "
            else:
                message = f"Yo, partner! I heard '{query}' but need more context. "
            
            if web_results:
                message += f"External sources show: {web_results[0].get('snippet', 'relevant information')}. "
            
            message += "I'm combining my internal knowledge with live web data to give you the complete picture! 🤠"
        
        return {
            'message': message,
            'internal_data': internal_data,
            'web_results': web_results,
            'sources': [r.get('source', 'Unknown') for r in web_results],
            'data_types': {
                'repository': fetch_repo,
                'infrastructure': fetch_infra,
                'apis': fetch_apis,
                'web_search': bool(web_results)
            },
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Hybrid intelligence failed: {e}")
        return {
            'message': f"Yo, partner! I hit a snag processing '{query}': {str(e)}. But I'm still locked and loaded! 🤠",
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

# Main chat endpoint with hybrid intelligence
@app.post("/api/v1/chat")
async def chat(request: ChatRequest):
    """Main chat endpoint with hybrid intelligence"""
    try:
        return await hybrid_intelligence_response(
            request.query, 
            request.user_id, 
            request.sources_limit
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Self-awareness endpoint (for direct internal queries)
@app.post("/api/v1/self")
async def self_awareness(request: SelfRequest):
    """Direct self-awareness endpoint"""
    try:
        if request.action == 'repository':
            data = await get_internal_repo_data()
            return {
                "message": f"Yo, partner! My repository analysis: {data.get('total_files', 0)} files, {len(data.get('python_files', []))} Python modules, latest commit: {data.get('recent_commits', [{}])[0].get('message', 'unknown')} 🤠",
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
        
        elif request.action == 'infrastructure':
            data = await get_internal_infra_data()
            return {
                "message": f"Yo, partner! Infrastructure status: {data.get('machines', 0)} machines, health: {data.get('health', 'unknown')}, running {data.get('version', 'unknown')} 🤠",
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
        
        elif request.action == 'apis':
            data = await get_internal_api_data()
            return {
                "message": f"Yo, partner! API status: {data.get('total_configured', 0)} total configured, {data.get('search_count', 0)} search APIs, {data.get('business_count', 0)} business integrations 🤠",
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")
    
    except Exception as e:
        logger.error(f"Self-awareness error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health endpoint
@app.get("/api/v1/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "4.0.0-HYBRID-INTELLIGENCE",
        "timestamp": datetime.now().isoformat(),
        "mode": "HYBRID_INTELLIGENCE_BADASS",
        "personality": "neon_cowboy_ultimate",
        "capabilities": "web_search + internal_data + ai_enhancement",
        "repository": "ai-cherry/sophia-intel",
        "response_time": "0.02s"
    }

# Serve static files
app.mount("/v4", StaticFiles(directory="apps/frontend/v4", html=True), name="frontend")
app.mount("/", StaticFiles(directory="apps/frontend/v4", html=True), name="root")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)

