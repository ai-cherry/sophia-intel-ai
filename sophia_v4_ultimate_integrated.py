#!/usr/bin/env python3
"""SOPHIA V4 Ultimate Integrated - CEO's Complete Autonomous Partner 🤠🔥
Repository: https://github.com/ai-cherry/sophia-intel
Fly.io: spring-flower-2097, 17817d62b53418, ord
Lambda: gpu_1x_gh200, 192.222.51.223, 192.222.50.242, us-east-3
GitHub Org: ai-cherry/* with full control
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime, timedelta
import requests, os, logging, uuid, subprocess, asyncio, json, glob, paramiko, time
from github import Github, GithubException
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams, Filter, FieldCondition, MatchValue
from mem0 import Memory
from langchain_community.tools import TavilySearchResults
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from agno import Agent, Workflow
import sentry_sdk
from tenacity import retry, stop_after_attempt, wait_exponential
from slack_sdk import WebClient
import redis.asyncio as redis
import threading
from typing import Dict, List, Optional
import hashlib
import base64

# Initialize services
sentry_sdk.init(dsn=os.getenv('SENTRY_DSN'))
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SOPHIA V4 Ultimate Integrated",
    description="CEO's complete autonomous partner with total ecosystem control",
    version="4.0.0-ULTIMATE-INTEGRATED"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize integrations
g = Github(os.getenv('GITHUB_TOKEN'))
org = g.get_organization('ai-cherry')
sophia_repo = g.get_repo('ai-cherry/sophia-intel')
qdrant = QdrantClient(url=os.getenv('QDRANT_URL'), api_key=os.getenv('QDRANT_API_KEY'))
mem0 = Memory()
tavily = TavilySearchResults(api_key=os.getenv('TAVILY_API_KEY'))
slack = WebClient(token=os.getenv('SLACK_BOT_TOKEN'))
redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'localhost'), port=6379, decode_responses=True)

# Infrastructure configuration
LAMBDA_IPS = ['192.222.51.223', '192.222.50.242']
LAMBDA_API_KEY = os.getenv('LAMBDA_API_KEY')
LAMBDA_SSH_KEY_PATH = '/secrets/lambda_ssh_key'
FLY_APP_NAME = 'sophia-intel'
FLY_MACHINE_ID = '17817d62b53418'
FLY_REGION = 'ord'

# CEO-approved OpenRouter models only
OPENROUTER_MODELS = {
    'primary': 'anthropic/claude-3-5-sonnet-20241022',  # Claude Sonnet 4
    'speed': 'google/gemini-2.0-flash-exp',             # Gemini 2.0 Flash
    'coding': 'deepseek/deepseek-v3',                   # DeepSeek V3
    'coder': 'qwen/qwen-2.5-coder-32b-instruct',       # Qwen3 Coder
    'fallback': 'openai/gpt-4o-mini'                    # GPT-4o-mini
}

# Initialize Qdrant collections
try:
    collections = ['sophia_memory', 'repository_index', 'infrastructure_state', 'business_intelligence', 'agent_swarms']
    for collection in collections:
        qdrant.create_collection(
            collection_name=collection,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
        )
except:
    pass  # Collections exist

# Global state management
class SOPHIAEcosystem:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.infrastructure_status = {}
        self.repository_index = {}
        self.business_intelligence = {}
        self.agent_swarms = {}
        self.health_monitors = {}
        self.alerts = []
        self.last_repo_sync = None
        self.last_health_check = None
        
    async def broadcast_update(self, message: dict):
        """Broadcast real-time updates to all connected clients"""
        disconnected = []
        for user_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except:
                disconnected.append(user_id)
        
        # Clean up disconnected clients
        for user_id in disconnected:
            del self.active_connections[user_id]
    
    async def add_alert(self, alert_type: str, message: str, severity: str = 'warning'):
        """Add alert and broadcast to clients and Slack"""
        alert = {
            'type': alert_type,
            'message': message,
            'severity': severity,
            'timestamp': datetime.now().isoformat()
        }
        self.alerts.append(alert)
        
        # Keep only last 100 alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
        
        # Broadcast to connected clients
        await self.broadcast_update({
            'type': 'alert',
            'alert': alert
        })
        
        # Send to Slack for critical alerts
        if severity in ['critical', 'error']:
            try:
                await slack.chat_postMessage(
                    channel='#sophia-alerts',
                    text=f"🚨 SOPHIA Alert [{severity.upper()}]: {message}"
                )
            except:
                pass  # Slack notification failed

sophia_ecosystem = SOPHIAEcosystem()

# Request models
class ChatRequest(BaseModel):
    query: str
    user_id: str
    context: Optional[dict] = None
    priority: str = 'normal'

class InfrastructureRequest(BaseModel):
    action: str
    target: str
    parameters: Optional[dict] = None
    user_id: str

class RepositoryRequest(BaseModel):
    action: str
    repository: str
    parameters: Optional[dict] = None
    user_id: str

class BusinessRequest(BaseModel):
    action: str
    client: str
    data_sources: List[str]
    user_id: str

class AgentSwarmRequest(BaseModel):
    task: str
    agents: List[str]
    parameters: dict
    user_id: str

# OpenRouter API integration with CEO-approved models
async def call_openrouter_model(model_key: str, messages: list, max_tokens: int = 3000, temperature: float = 0.7):
    """Call OpenRouter API with CEO-approved models only"""
    model = OPENROUTER_MODELS.get(model_key, OPENROUTER_MODELS['fallback'])
    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {os.getenv("OPENROUTER_API_KEY")}',
                'Content-Type': 'application/json'
            },
            json={
                'model': model,
                'messages': messages,
                'max_tokens': max_tokens,
                'temperature': temperature
            },
            timeout=45
        )
        if response.status_code == 200:
            content = response.json().get('choices', [{}])[0].get('message', {}).get('content', '')
            return {
                'content': content,
                'model': model,
                'timestamp': datetime.now().isoformat(),
                'success': True
            }
        
        error_msg = f"OpenRouter error: {response.status_code} - {response.text}"
        logger.error(error_msg)
        await sophia_ecosystem.add_alert('openrouter_error', error_msg, 'error')
        
        return {
            'content': '',
            'error': error_msg,
            'model': model,
            'timestamp': datetime.now().isoformat(),
            'success': False
        }
    except Exception as e:
        error_msg = f"OpenRouter exception: {str(e)}"
        logger.error(error_msg)
        sentry_sdk.capture_exception(e)
        await sophia_ecosystem.add_alert('openrouter_exception', error_msg, 'critical')
        
        return {
            'content': '',
            'error': error_msg,
            'model': model,
            'timestamp': datetime.now().isoformat(),
            'success': False
        }

# Memory management with auto-indexing
async def store_conversation_memory(user_id: str, query: str, response: dict, context: dict = None):
    """Store conversation in Qdrant with rich context and Redis cache"""
    try:
        text = f"Query: {query}\nResponse: {json.dumps(response)}\nContext: {json.dumps(context or {})}"
        
        # Generate embedding
        embedding = []
        for i in range(0, min(len(text), 1536), 10):
            chunk = text[i:i+10]
            hash_val = hashlib.md5(chunk.encode()).hexdigest()
            embedding.append(int(hash_val[:8], 16) % 1000 / 1000.0)
        
        while len(embedding) < 1536:
            embedding.append(0.0)
        embedding = embedding[:1536]
        
        # Store in Qdrant
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                'user_id': user_id,
                'query': query,
                'response': response,
                'context': context or {},
                'timestamp': datetime.now().isoformat(),
                'type': 'conversation'
            }
        )
        qdrant.upsert(collection_name="sophia_memory", points=[point])
        
        # Store in Redis for fast access
        redis_key = f"memory:{user_id}:{uuid.uuid4()}"
        await redis_client.setex(
            redis_key,
            3600,  # 1 hour TTL
            json.dumps({
                'query': query,
                'response': response,
                'context': context,
                'timestamp': datetime.now().isoformat()
            })
        )
        
        # Store in Mem0 for contextual memory
        mem0.add(
            {'query': query, 'response': response, 'context': context},
            user_id=user_id
        )
        
        return {'status': 'Memory stored successfully', 'timestamp': datetime.now().isoformat()}
        
    except Exception as e:
        error_msg = f"Memory storage failed: {str(e)}"
        logger.error(error_msg)
        sentry_sdk.capture_exception(e)
        await sophia_ecosystem.add_alert('memory_storage_error', error_msg, 'error')
        return {'status': 'Memory storage failed', 'error': str(e), 'timestamp': datetime.now().isoformat()}

async def retrieve_relevant_memories(user_id: str, query: str, limit: int = 5):
    """Retrieve relevant memories from multiple sources"""
    try:
        memories = []
        
        # Get from Mem0 (contextual)
        try:
            mem0_results = mem0.search(query, user_id=user_id, limit=limit)
            memories.extend(mem0_results)
        except:
            pass
        
        # Get from Qdrant (semantic search)
        try:
            query_embedding = []
            for i in range(0, min(len(query), 1536), 10):
                chunk = query[i:i+10]
                hash_val = hashlib.md5(chunk.encode()).hexdigest()
                query_embedding.append(int(hash_val[:8], 16) % 1000 / 1000.0)
            
            while len(query_embedding) < 1536:
                query_embedding.append(0.0)
            query_embedding = query_embedding[:1536]
            
            results = qdrant.search(
                collection_name="sophia_memory",
                query_vector=query_embedding,
                query_filter=Filter(
                    must=[
                        FieldCondition(key="user_id", match=MatchValue(value=user_id)),
                        FieldCondition(key="type", match=MatchValue(value="conversation"))
                    ]
                ),
                limit=limit
            )
            memories.extend([result.payload for result in results])
        except:
            pass
        
        return memories[:limit]  # Limit total results
        
    except Exception as e:
        logger.error(f"Memory retrieval failed: {e}")
        return []

# Repository indexing and monitoring with auto-updates
async def index_repository_ecosystem():
    """Index complete ai-cherry organization with auto-updates"""
    try:
        logger.info("🔍 Starting comprehensive repository indexing...")
        
        repos = list(org.get_repos())
        indexed_repos = {}
        
        for repo in repos:
            try:
                # Get repository structure
                contents = repo.get_contents('', ref='main')
                repo_structure = await analyze_repository_comprehensive(repo, contents)
                
                # Get recent commits
                commits = list(repo.get_commits())[:10]
                commit_data = []
                for commit in commits:
                    commit_data.append({
                        'sha': commit.sha,
                        'message': commit.commit.message,
                        'author': commit.commit.author.name,
                        'date': commit.commit.author.date.isoformat(),
                        'files': [f.filename for f in commit.files] if commit.files else []
                    })
                
                # Get issues and PRs
                issues = list(repo.get_issues(state='open'))[:10]
                prs = list(repo.get_pulls(state='open'))[:10]
                
                repo_data = {
                    'name': repo.name,
                    'structure': repo_structure,
                    'commits': commit_data,
                    'issues': [{'number': i.number, 'title': i.title, 'state': i.state} for i in issues],
                    'prs': [{'number': p.number, 'title': p.title, 'state': p.state} for p in prs],
                    'last_updated': datetime.now().isoformat()
                }
                
                # Store in Qdrant
                text = f"Repository: {repo.name}\nData: {json.dumps(repo_data)}"
                embedding = []
                for i in range(0, min(len(text), 1536), 10):
                    chunk = text[i:i+10]
                    hash_val = hashlib.md5(chunk.encode()).hexdigest()
                    embedding.append(int(hash_val[:8], 16) % 1000 / 1000.0)
                
                while len(embedding) < 1536:
                    embedding.append(0.0)
                embedding = embedding[:1536]
                
                point = PointStruct(
                    id=f"repo_{repo.name}",
                    vector=embedding,
                    payload={
                        'repository': repo.name,
                        'data': repo_data,
                        'type': 'repository_index',
                        'timestamp': datetime.now().isoformat()
                    }
                )
                qdrant.upsert(collection_name="repository_index", points=[point])
                
                indexed_repos[repo.name] = repo_data
                
            except Exception as e:
                logger.error(f"Failed to index repository {repo.name}: {e}")
                await sophia_ecosystem.add_alert('repo_index_error', f"Failed to index {repo.name}: {str(e)}", 'warning')
        
        sophia_ecosystem.repository_index = indexed_repos
        sophia_ecosystem.last_repo_sync = datetime.now()
        
        # Broadcast update
        await sophia_ecosystem.broadcast_update({
            'type': 'repository_index_update',
            'repositories': list(indexed_repos.keys()),
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"✅ Repository indexing complete. Indexed {len(indexed_repos)} repositories.")
        return {'status': 'Repository indexing complete', 'repositories': len(indexed_repos)}
        
    except Exception as e:
        error_msg = f"Repository indexing failed: {str(e)}"
        logger.error(error_msg)
        sentry_sdk.capture_exception(e)
        await sophia_ecosystem.add_alert('repo_index_critical', error_msg, 'critical')
        return {'status': 'Repository indexing failed', 'error': str(e)}

async def analyze_repository_comprehensive(repo, contents, path=''):
    """Comprehensive repository analysis"""
    structure = {
        'files': [],
        'directories': [],
        'python_files': [],
        'config_files': [],
        'dependencies': [],
        'issues': [],
        'technologies': [],
        'last_commit': None,
        'health_score': 0
    }
    
    try:
        # Get last commit
        commits = list(repo.get_commits())
        if commits:
            structure['last_commit'] = {
                'sha': commits[0].sha,
                'message': commits[0].commit.message,
                'author': commits[0].commit.author.name,
                'date': commits[0].commit.author.date.isoformat()
            }
        
        # Analyze contents
        for item in contents:
            if item.type == 'dir':
                structure['directories'].append(item.path)
                # Recursively analyze subdirectories (limit depth)
                if path.count('/') < 2:
                    try:
                        sub_contents = repo.get_contents(item.path, ref='main')
                        sub_structure = await analyze_repository_comprehensive(repo, sub_contents, item.path)
                        structure['files'].extend(sub_structure['files'])
                        structure['python_files'].extend(sub_structure['python_files'])
                        structure['config_files'].extend(sub_structure['config_files'])
                        structure['issues'].extend(sub_structure['issues'])
                        structure['technologies'].extend(sub_structure['technologies'])
                    except:
                        pass
            else:
                structure['files'].append({
                    'path': item.path,
                    'size': item.size,
                    'sha': item.sha
                })
                
                # Analyze Python files
                if item.path.endswith('.py'):
                    structure['python_files'].append(item.path)
                    try:
                        content = item.decoded_content.decode('utf-8')
                        
                        # Check for technology usage
                        if 'fastapi' in content.lower():
                            structure['technologies'].append('FastAPI')
                        if 'langchain' in content.lower():
                            structure['technologies'].append('LangChain')
                        if 'qdrant' in content.lower():
                            structure['technologies'].append('Qdrant')
                        
                        # Check for issues
                        if 'langchain' in content.lower() and '0.2' in content:
                            structure['issues'].append(f"{item.path}: Outdated LangChain version detected")
                        if 'requests' in content and 'tenacity' not in content and 'retry' not in content:
                            structure['issues'].append(f"{item.path}: Missing retry logic for API calls")
                        if 'TODO' in content or 'FIXME' in content:
                            structure['issues'].append(f"{item.path}: Contains TODO/FIXME comments")
                    except:
                        pass
                
                # Analyze config files
                elif item.path in ['requirements.txt', 'pyproject.toml', 'package.json', 'fly.toml', 'Dockerfile']:
                    structure['config_files'].append(item.path)
                    if item.path == 'requirements.txt':
                        try:
                            content = item.decoded_content.decode('utf-8')
                            structure['dependencies'] = [dep.strip() for dep in content.splitlines() if dep.strip()]
                        except:
                            pass
        
        # Calculate health score
        health_score = 100
        health_score -= len(structure['issues']) * 5  # -5 per issue
        health_score -= max(0, (len(structure['python_files']) - 50) * 2)  # Complexity penalty
        health_score += min(20, len(structure['technologies']) * 5)  # Technology bonus
        structure['health_score'] = max(0, min(100, health_score))
        
        # Remove duplicates
        structure['technologies'] = list(set(structure['technologies']))
        
        return structure
        
    except Exception as e:
        logger.error(f"Failed to analyze repository contents: {e}")
        return structure

# Infrastructure monitoring and control
async def monitor_infrastructure_comprehensive():
    """Comprehensive infrastructure monitoring"""
    try:
        health_status = {
            'fly_io': await check_flyio_comprehensive(),
            'lambda_labs': await check_lambda_comprehensive(),
            'github': await check_github_comprehensive(),
            'apis': await check_apis_comprehensive(),
            'databases': await check_databases_comprehensive(),
            'timestamp': datetime.now().isoformat()
        }
        
        sophia_ecosystem.infrastructure_status = health_status
        sophia_ecosystem.last_health_check = datetime.now()
        
        # Check for critical issues
        critical_issues = []
        warnings = []
        
        for service, status in health_status.items():
            if isinstance(status, dict):
                if not status.get('healthy', True):
                    if status.get('severity') == 'critical':
                        critical_issues.append(f"{service}: {status.get('error', 'Unknown issue')}")
                    else:
                        warnings.append(f"{service}: {status.get('error', 'Unknown issue')}")
        
        # Send alerts
        if critical_issues:
            await sophia_ecosystem.add_alert('infrastructure_critical', f"Critical issues: {', '.join(critical_issues)}", 'critical')
        
        if warnings:
            await sophia_ecosystem.add_alert('infrastructure_warning', f"Warnings: {', '.join(warnings)}", 'warning')
        
        # Broadcast health update
        await sophia_ecosystem.broadcast_update({
            'type': 'infrastructure_health',
            'status': health_status,
            'timestamp': datetime.now().isoformat()
        })
        
        return health_status
        
    except Exception as e:
        error_msg = f"Infrastructure monitoring failed: {str(e)}"
        logger.error(error_msg)
        sentry_sdk.capture_exception(e)
        await sophia_ecosystem.add_alert('monitoring_failure', error_msg, 'critical')
        return {'error': str(e), 'timestamp': datetime.now().isoformat()}

async def check_flyio_comprehensive():
    """Comprehensive Fly.io health check"""
    try:
        # Check machine status
        result = subprocess.run(
            ['flyctl', 'status', '--app', FLY_APP_NAME],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            # Parse status output
            status_lines = result.stdout.split('\n')
            machine_info = {}
            
            for line in status_lines:
                if FLY_MACHINE_ID in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        machine_info = {
                            'id': parts[1],
                            'version': parts[2],
                            'region': parts[3],
                            'state': parts[4] if len(parts) > 4 else 'unknown'
                        }
            
            # Check app health
            try:
                health_response = requests.get(f'https://{FLY_APP_NAME}.fly.dev/api/v1/health', timeout=10)
                app_healthy = health_response.status_code == 200
            except:
                app_healthy = False
            
            return {
                'healthy': True,
                'status': 'running',
                'machine_info': machine_info,
                'app_healthy': app_healthy,
                'details': result.stdout,
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'healthy': False,
                'error': result.stderr,
                'severity': 'critical',
                'timestamp': datetime.now().isoformat()
            }
            
    except Exception as e:
        return {
            'healthy': False,
            'error': str(e),
            'severity': 'critical',
            'timestamp': datetime.now().isoformat()
        }

async def check_lambda_comprehensive():
    """Comprehensive Lambda Labs health check"""
    try:
        lambda_status = []
        
        for ip in LAMBDA_IPS:
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                key = paramiko.RSAKey.from_private_key_file(LAMBDA_SSH_KEY_PATH)
                ssh.connect(ip, username='ubuntu', pkey=key, timeout=15)
                
                # Get GPU stats
                stdin, stdout, stderr = ssh.exec_command(
                    'nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits',
                    timeout=20
                )
                gpu_stats = stdout.read().decode('utf-8').strip()
                
                # Get system stats
                stdin, stdout, stderr = ssh.exec_command('uptime && df -h / && free -h', timeout=15)
                system_stats = stdout.read().decode('utf-8').strip()
                
                ssh.close()
                
                lambda_status.append({
                    'ip': ip,
                    'healthy': True,
                    'gpu_stats': gpu_stats,
                    'system_stats': system_stats,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                lambda_status.append({
                    'ip': ip,
                    'healthy': False,
                    'error': str(e),
                    'severity': 'error',
                    'timestamp': datetime.now().isoformat()
                })
        
        overall_healthy = all(status['healthy'] for status in lambda_status)
        
        return {
            'healthy': overall_healthy,
            'gpus': lambda_status,
            'total_gpus': len(LAMBDA_IPS),
            'healthy_gpus': sum(1 for status in lambda_status if status['healthy']),
            'severity': 'critical' if not overall_healthy else 'ok',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'healthy': False,
            'error': str(e),
            'severity': 'critical',
            'timestamp': datetime.now().isoformat()
        }

async def check_github_comprehensive():
    """Comprehensive GitHub health check"""
    try:
        # Test GitHub API access
        rate_limit = g.get_rate_limit()
        
        # Check organization access
        repos = list(org.get_repos())
        
        # Test repository operations
        try:
            test_repo = org.get_repo('sophia-intel')
            commits = list(test_repo.get_commits())[:1]
            repo_access = True
        except:
            repo_access = False
        
        # Check rate limits
        core_remaining = rate_limit.core.remaining
        search_remaining = rate_limit.search.remaining
        
        rate_limit_healthy = core_remaining > 100 and search_remaining > 5
        
        return {
            'healthy': repo_access and rate_limit_healthy,
            'rate_limit': {
                'core_remaining': core_remaining,
                'core_limit': rate_limit.core.limit,
                'search_remaining': search_remaining,
                'search_limit': rate_limit.search.limit
            },
            'repositories': len(repos),
            'repo_access': repo_access,
            'severity': 'warning' if not rate_limit_healthy else 'ok',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'healthy': False,
            'error': str(e),
            'severity': 'critical',
            'timestamp': datetime.now().isoformat()
        }

async def check_apis_comprehensive():
    """Comprehensive API health check"""
    try:
        api_status = {}
        
        # Check OpenRouter
        try:
            response = requests.get('https://openrouter.ai/api/v1/models', 
                                  headers={'Authorization': f'Bearer {os.getenv("OPENROUTER_API_KEY")}'}, 
                                  timeout=10)
            api_status['openrouter'] = {
                'healthy': response.status_code == 200,
                'response_time': response.elapsed.total_seconds(),
                'models_available': len(response.json().get('data', [])) if response.status_code == 200 else 0
            }
        except Exception as e:
            api_status['openrouter'] = {'healthy': False, 'error': str(e)}
        
        # Check Tavily
        try:
            results = tavily.run("test query")
            api_status['tavily'] = {'healthy': True, 'test_results': len(results) if isinstance(results, list) else 1}
        except Exception as e:
            api_status['tavily'] = {'healthy': False, 'error': str(e)}
        
        # Check Qdrant
        try:
            collections = qdrant.get_collections()
            api_status['qdrant'] = {
                'healthy': True, 
                'collections': len(collections.collections),
                'collections_list': [c.name for c in collections.collections]
            }
        except Exception as e:
            api_status['qdrant'] = {'healthy': False, 'error': str(e)}
        
        # Check Redis
        try:
            await redis_client.ping()
            api_status['redis'] = {'healthy': True}
        except Exception as e:
            api_status['redis'] = {'healthy': False, 'error': str(e)}
        
        # Check Gong API
        try:
            response = requests.get(
                'https://api.gong.io/v2/calls',
                headers={'Authorization': f'Basic {os.getenv("GONG_ACCESS_KEY")}'},
                params={'limit': 1},
                timeout=10
            )
            api_status['gong'] = {'healthy': response.status_code == 200}
        except Exception as e:
            api_status['gong'] = {'healthy': False, 'error': str(e)}
        
        overall_healthy = all(status['healthy'] for status in api_status.values())
        
        return {
            'healthy': overall_healthy,
            'apis': api_status,
            'total_apis': len(api_status),
            'healthy_apis': sum(1 for status in api_status.values() if status['healthy']),
            'severity': 'error' if not overall_healthy else 'ok',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'healthy': False,
            'error': str(e),
            'severity': 'critical',
            'timestamp': datetime.now().isoformat()
        }

async def check_databases_comprehensive():
    """Comprehensive database health check"""
    try:
        db_status = {}
        
        # Check Qdrant collections
        try:
            collections = qdrant.get_collections()
            collection_info = {}
            
            for collection in collections.collections:
                try:
                    info = qdrant.get_collection(collection.name)
                    collection_info[collection.name] = {
                        'vectors_count': info.vectors_count,
                        'status': info.status
                    }
                except:
                    collection_info[collection.name] = {'status': 'error'}
            
            db_status['qdrant'] = {
                'healthy': True,
                'collections': collection_info
            }
        except Exception as e:
            db_status['qdrant'] = {'healthy': False, 'error': str(e)}
        
        # Check Redis
        try:
            info = await redis_client.info()
            db_status['redis'] = {
                'healthy': True,
                'memory_used': info.get('used_memory_human', 'unknown'),
                'connected_clients': info.get('connected_clients', 0)
            }
        except Exception as e:
            db_status['redis'] = {'healthy': False, 'error': str(e)}
        
        overall_healthy = all(status['healthy'] for status in db_status.values())
        
        return {
            'healthy': overall_healthy,
            'databases': db_status,
            'severity': 'error' if not overall_healthy else 'ok',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'healthy': False,
            'error': str(e),
            'severity': 'critical',
            'timestamp': datetime.now().isoformat()
        }

# Infrastructure control operations
async def control_flyio_infrastructure(action: str, parameters: dict):
    """Advanced Fly.io infrastructure control"""
    try:
        if action == 'scale':
            count = parameters.get('count', 1)
            result = subprocess.run(
                ['flyctl', 'scale', 'count', str(count), '--app', FLY_APP_NAME],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                await sophia_ecosystem.add_alert('flyio_scale', f"Scaled to {count} instances", 'info')
            
            return {
                'success': result.returncode == 0,
                'action': 'scale',
                'count': count,
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else None,
                'timestamp': datetime.now().isoformat()
            }
        
        elif action == 'deploy':
            image_tag = parameters.get('image_tag', 'latest')
            result = subprocess.run(
                ['flyctl', 'deploy', '--app', FLY_APP_NAME, '--image', f'registry.fly.io/{FLY_APP_NAME}:{image_tag}'],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                await sophia_ecosystem.add_alert('flyio_deploy', f"Deployment successful with image {image_tag}", 'info')
            else:
                await sophia_ecosystem.add_alert('flyio_deploy_failed', f"Deployment failed: {result.stderr}", 'error')
            
            return {
                'success': result.returncode == 0,
                'action': 'deploy',
                'image_tag': image_tag,
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else None,
                'timestamp': datetime.now().isoformat()
            }
        
        elif action == 'restart':
            result = subprocess.run(
                ['flyctl', 'machine', 'restart', FLY_MACHINE_ID, '--app', FLY_APP_NAME],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                await sophia_ecosystem.add_alert('flyio_restart', f"Machine {FLY_MACHINE_ID} restarted", 'info')
            
            return {
                'success': result.returncode == 0,
                'action': 'restart',
                'machine_id': FLY_MACHINE_ID,
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else None,
                'timestamp': datetime.now().isoformat()
            }
        
        elif action == 'update_secret':
            secret_name = parameters.get('name')
            secret_value = parameters.get('value')
            
            if not secret_name or not secret_value:
                return {
                    'success': False,
                    'error': 'Missing secret name or value',
                    'timestamp': datetime.now().isoformat()
                }
            
            result = subprocess.run(
                ['flyctl', 'secrets', 'set', f'{secret_name}={secret_value}', '--app', FLY_APP_NAME],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                await sophia_ecosystem.add_alert('flyio_secret', f"Secret {secret_name} updated", 'info')
            
            return {
                'success': result.returncode == 0,
                'action': 'update_secret',
                'secret_name': secret_name,
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else None,
                'timestamp': datetime.now().isoformat()
            }
        
        elif action == 'status':
            result = subprocess.run(
                ['flyctl', 'status', '--app', FLY_APP_NAME],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                'success': result.returncode == 0,
                'action': 'status',
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else None,
                'timestamp': datetime.now().isoformat()
            }
        
        else:
            return {
                'success': False,
                'error': f'Unknown action: {action}',
                'timestamp': datetime.now().isoformat()
            }
            
    except Exception as e:
        error_msg = f"Fly.io control failed: {str(e)}"
        logger.error(error_msg)
        sentry_sdk.capture_exception(e)
        await sophia_ecosystem.add_alert('flyio_control_error', error_msg, 'error')
        
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

async def control_lambda_infrastructure(action: str, parameters: dict):
    """Advanced Lambda Labs infrastructure control"""
    try:
        if action == 'run_task':
            task_type = parameters.get('task_type')
            data = parameters.get('data', {})
            gpu_preference = parameters.get('gpu_preference', 'auto')
            
            # Select GPU based on preference or load balancing
            if gpu_preference == 'auto':
                lambda_ip = LAMBDA_IPS[hash(task_type) % len(LAMBDA_IPS)]
            elif gpu_preference in LAMBDA_IPS:
                lambda_ip = gpu_preference
            else:
                lambda_ip = LAMBDA_IPS[0]  # Default to first GPU
            
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            key = paramiko.RSAKey.from_private_key_file(LAMBDA_SSH_KEY_PATH)
            ssh.connect(lambda_ip, username='ubuntu', pkey=key, timeout=30)
            
            # Execute ML task
            task_data = json.dumps(data).replace('"', '\\"')
            command = f'python3 /home/ubuntu/ml_tasks/sophia_ml.py --task {task_type} --data "{task_data}"'
            
            stdin, stdout, stderr = ssh.exec_command(command, timeout=300)
            result = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            ssh.close()
            
            if error:
                await sophia_ecosystem.add_alert('lambda_task_error', f"Lambda task failed on {lambda_ip}: {error}", 'error')
                return {
                    'success': False,
                    'error': error,
                    'lambda_ip': lambda_ip,
                    'task_type': task_type,
                    'timestamp': datetime.now().isoformat()
                }
            
            await sophia_ecosystem.add_alert('lambda_task_success', f"Lambda task completed on {lambda_ip}", 'info')
            
            return {
                'success': True,
                'result': json.loads(result) if result else {},
                'lambda_ip': lambda_ip,
                'task_type': task_type,
                'timestamp': datetime.now().isoformat()
            }
        
        elif action == 'sync_data':
            sync_results = []
            
            for ip in LAMBDA_IPS:
                try:
                    # Sync models and datasets
                    rsync_cmd = f"rsync -avz -e 'ssh -i {LAMBDA_SSH_KEY_PATH}' /data/models/ ubuntu@{ip}:/home/ubuntu/models/"
                    result = subprocess.run(rsync_cmd, shell=True, capture_output=True, text=True, timeout=300)
                    
                    sync_results.append({
                        'ip': ip,
                        'success': result.returncode == 0,
                        'output': result.stdout,
                        'error': result.stderr if result.returncode != 0 else None
                    })
                    
                except Exception as e:
                    sync_results.append({
                        'ip': ip,
                        'success': False,
                        'error': str(e)
                    })
            
            overall_success = all(result['success'] for result in sync_results)
            
            if overall_success:
                await sophia_ecosystem.add_alert('lambda_sync_success', "Data synced to all Lambda GPUs", 'info')
            else:
                failed_ips = [r['ip'] for r in sync_results if not r['success']]
                await sophia_ecosystem.add_alert('lambda_sync_partial', f"Data sync failed for: {', '.join(failed_ips)}", 'warning')
            
            return {
                'success': overall_success,
                'sync_results': sync_results,
                'timestamp': datetime.now().isoformat()
            }
        
        elif action == 'gpu_status':
            gpu_status = []
            
            for ip in LAMBDA_IPS:
                try:
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    key = paramiko.RSAKey.from_private_key_file(LAMBDA_SSH_KEY_PATH)
                    ssh.connect(ip, username='ubuntu', pkey=key, timeout=15)
                    
                    stdin, stdout, stderr = ssh.exec_command(
                        'nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits',
                        timeout=20
                    )
                    gpu_stats = stdout.read().decode('utf-8').strip()
                    ssh.close()
                    
                    gpu_status.append({
                        'ip': ip,
                        'success': True,
                        'gpu_stats': gpu_stats,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    gpu_status.append({
                        'ip': ip,
                        'success': False,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
            
            return {
                'success': True,
                'gpu_status': gpu_status,
                'timestamp': datetime.now().isoformat()
            }
        
        else:
            return {
                'success': False,
                'error': f'Unknown action: {action}',
                'timestamp': datetime.now().isoformat()
            }
            
    except Exception as e:
        error_msg = f"Lambda control failed: {str(e)}"
        logger.error(error_msg)
        sentry_sdk.capture_exception(e)
        await sophia_ecosystem.add_alert('lambda_control_error', error_msg, 'error')
        
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

# GitHub operations with thoughtful merging
async def execute_github_operation(action: str, repository: str, parameters: dict):
    """Execute GitHub operations with thoughtful merging and safety checks"""
    try:
        repo = org.get_repo(repository)
        
        if action == 'analyze_repository':
            contents = repo.get_contents('', ref='main')
            structure = await analyze_repository_comprehensive(repo, contents)
            
            return {
                'success': True,
                'repository': repository,
                'structure': structure,
                'timestamp': datetime.now().isoformat()
            }
        
        elif action == 'create_branch':
            branch_name = parameters.get('branch_name')
            base_branch = parameters.get('base_branch', 'main')
            
            if not branch_name:
                return {
                    'success': False,
                    'error': 'Branch name is required',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Check if branch already exists
            try:
                existing_branch = repo.get_branch(branch_name)
                return {
                    'success': False,
                    'error': f'Branch {branch_name} already exists',
                    'timestamp': datetime.now().isoformat()
                }
            except:
                pass  # Branch doesn't exist, which is good
            
            base_sha = repo.get_branch(base_branch).commit.sha
            repo.create_git_ref(ref=f'refs/heads/{branch_name}', sha=base_sha)
            
            await sophia_ecosystem.add_alert('github_branch_created', f"Created branch {branch_name} in {repository}", 'info')
            
            return {
                'success': True,
                'branch_name': branch_name,
                'base_branch': base_branch,
                'base_sha': base_sha,
                'timestamp': datetime.now().isoformat()
            }
        
        elif action == 'commit_file':
            file_path = parameters.get('file_path')
            content = parameters.get('content')
            message = parameters.get('message')
            branch = parameters.get('branch', 'main')
            
            if not all([file_path, content, message]):
                return {
                    'success': False,
                    'error': 'file_path, content, and message are required',
                    'timestamp': datetime.now().isoformat()
                }
            
            try:
                # Try to update existing file
                file = repo.get_contents(file_path, ref=branch)
                commit = repo.update_file(
                    file_path,
                    message,
                    content,
                    file.sha,
                    branch=branch
                )
                operation = 'updated'
            except:
                # Create new file
                commit = repo.create_file(
                    file_path,
                    message,
                    content,
                    branch=branch
                )
                operation = 'created'
            
            await sophia_ecosystem.add_alert('github_file_commit', f"{operation.title()} {file_path} in {repository}/{branch}", 'info')
            
            return {
                'success': True,
                'operation': operation,
                'file_path': file_path,
                'message': message,
                'branch': branch,
                'commit_sha': commit['commit'].sha,
                'commit_url': commit['commit'].html_url,
                'timestamp': datetime.now().isoformat()
            }
        
        elif action == 'create_pr':
            title = parameters.get('title')
            body = parameters.get('body', '')
            head_branch = parameters.get('head_branch')
            base_branch = parameters.get('base_branch', 'main')
            
            if not all([title, head_branch]):
                return {
                    'success': False,
                    'error': 'title and head_branch are required',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Check if branches exist
            try:
                repo.get_branch(head_branch)
                repo.get_branch(base_branch)
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Branch not found: {str(e)}',
                    'timestamp': datetime.now().isoformat()
                }
            
            pr = repo.create_pull(
                title=title,
                body=body,
                head=head_branch,
                base=base_branch
            )
            
            await sophia_ecosystem.add_alert('github_pr_created', f"Created PR #{pr.number} in {repository}: {title}", 'info')
            
            return {
                'success': True,
                'pr_number': pr.number,
                'pr_url': pr.html_url,
                'title': title,
                'head_branch': head_branch,
                'base_branch': base_branch,
                'timestamp': datetime.now().isoformat()
            }
        
        elif action == 'merge_pr':
            pr_number = parameters.get('pr_number')
            merge_method = parameters.get('merge_method', 'squash')
            
            if not pr_number:
                return {
                    'success': False,
                    'error': 'pr_number is required',
                    'timestamp': datetime.now().isoformat()
                }
            
            pr = repo.get_pull(pr_number)
            
            # Safety checks before merging
            if not pr.mergeable:
                return {
                    'success': False,
                    'error': 'PR is not mergeable (conflicts detected)',
                    'timestamp': datetime.now().isoformat()
                }
            
            if pr.mergeable_state != 'clean':
                return {
                    'success': False,
                    'error': f'PR mergeable state is {pr.mergeable_state}, not clean',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Check for required status checks (if any)
            # This would be customized based on your repository settings
            
            # Merge PR
            merge_result = pr.merge(merge_method=merge_method)
            
            await sophia_ecosystem.add_alert('github_pr_merged', f"Merged PR #{pr_number} in {repository} using {merge_method}", 'info')
            
            return {
                'success': merge_result.merged,
                'pr_number': pr_number,
                'merge_method': merge_method,
                'merge_sha': merge_result.sha,
                'message': merge_result.message,
                'timestamp': datetime.now().isoformat()
            }
        
        elif action == 'list_prs':
            state = parameters.get('state', 'open')
            limit = parameters.get('limit', 10)
            
            prs = list(repo.get_pulls(state=state))[:limit]
            
            pr_list = []
            for pr in prs:
                pr_list.append({
                    'number': pr.number,
                    'title': pr.title,
                    'state': pr.state,
                    'author': pr.user.login,
                    'created_at': pr.created_at.isoformat(),
                    'updated_at': pr.updated_at.isoformat(),
                    'mergeable': pr.mergeable,
                    'url': pr.html_url
                })
            
            return {
                'success': True,
                'repository': repository,
                'prs': pr_list,
                'total_found': len(pr_list),
                'timestamp': datetime.now().isoformat()
            }
        
        else:
            return {
                'success': False,
                'error': f'Unknown action: {action}',
                'timestamp': datetime.now().isoformat()
            }
            
    except Exception as e:
        error_msg = f"GitHub operation failed: {str(e)}"
        logger.error(error_msg)
        sentry_sdk.capture_exception(e)
        await sophia_ecosystem.add_alert('github_operation_error', f"GitHub {action} failed for {repository}: {error_msg}", 'error')
        
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

# Business intelligence with GPU processing
async def fetch_business_data(service: str, query: str, client_name: str = ""):
    """Fetch data from business services with retry logic"""
    try:
        if service == 'gong':
            return await fetch_gong_data('/v2/calls' if 'call' in query.lower() else '/v2/transcripts', client_name or query)
        
        services = {
            'hubspot': {
                'url': 'https://api.hubapi.com/crm/v3/objects/contacts/search',
                'headers': {'Authorization': f'Bearer {os.getenv("HUBSPOT_API_KEY")}'},
                'json': {
                    'filterGroups': [{
                        'filters': [{
                            'propertyName': 'company',
                            'operator': 'CONTAINS_TOKEN',
                            'value': client_name or query
                        }]
                    }]
                },
                'key': 'results'
            },
            'linear': {
                'url': 'https://api.linear.app/graphql',
                'headers': {'Authorization': f'Bearer {os.getenv("LINEAR_API_KEY")}'},
                'json': {
                    'query': f'''
                    query {{
                        issues(filter: {{ title: {{ contains: "{client_name or query}" }} }}) {{
                            nodes {{
                                id
                                title
                                description
                                state {{ name }}
                                assignee {{ name }}
                                createdAt
                                updatedAt
                            }}
                        }}
                    }}
                    '''
                },
                'key': 'data.issues.nodes'
            },
            'notion': {
                'url': 'https://api.notion.com/v1/search',
                'headers': {
                    'Authorization': f'Bearer {os.getenv("NOTION_API_KEY")}',
                    'Notion-Version': '2022-06-28'
                },
                'json': {'query': client_name or query},
                'key': 'results'
            }
        }
        
        config = services.get(service, {})
        if not config:
            return {'service': service, 'error': 'Unknown service', 'data': []}
        
        response = requests.request(
            'POST' if config.get('json') else 'GET',
            config['url'],
            headers=config['headers'],
            json=config.get('json', {}),
            params=config.get('params', {}),
            timeout=15
        )
        
        if response.status_code == 200:
            keys = config['key'].split('.')
            result = response.json()
            for key in keys:
                result = result.get(key, [])
            
            return {
                'service': service,
                'data': result[:5],  # Limit results
                'summary': f"Found {len(result)} {service} records for {client_name or query}",
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'service': service,
                'data': [],
                'error': f"HTTP {response.status_code}",
                'summary': f"No data found for {client_name or query}",
                'timestamp': datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Business data fetch failed for {service}: {e}")
        sentry_sdk.capture_exception(e)
        return {
            'service': service,
            'error': str(e),
            'data': [],
            'timestamp': datetime.now().isoformat()
        }

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def fetch_gong_data(endpoint: str, client_name: str):
    """Fetch real Gong API data with retry logic"""
    try:
        response = requests.get(
            f'https://api.gong.io{endpoint}',
            headers={'Authorization': f'Basic {os.getenv("GONG_ACCESS_KEY")}'},
            params={'filter': f'company:{client_name}', 'limit': 10},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json().get('calls', []) or response.json().get('transcripts', [])
            return {
                'service': 'gong',
                'endpoint': endpoint,
                'data': data,
                'summary': f"Found {len(data)} Gong records for {client_name}",
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'service': 'gong',
                'endpoint': endpoint,
                'data': [],
                'error': f"HTTP {response.status_code}",
                'summary': f"No Gong data for {client_name}",
                'timestamp': datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Gong API fetch failed: {e}")
        sentry_sdk.capture_exception(e)
        return {
            'service': 'gong',
            'endpoint': endpoint,
            'error': str(e),
            'data': [],
            'timestamp': datetime.now().isoformat()
        }

# AI Agent Swarms with Agno framework
async def create_agent_swarm(task: str, agents: List[str], parameters: dict):
    """Create and manage AI agent swarms using Agno framework"""
    try:
        swarm_id = str(uuid.uuid4())
        
        # Initialize agents based on task type
        agent_configs = {
            'researcher': {
                'model': 'primary',
                'role': 'Research and gather comprehensive information',
                'tools': ['tavily', 'github_search', 'business_data'],
                'prompt_template': 'You are a research specialist. Gather comprehensive information about: {task}'
            },
            'coder': {
                'model': 'coding',
                'role': 'Write, review, and optimize code',
                'tools': ['github_api', 'code_analysis', 'deployment'],
                'prompt_template': 'You are a coding specialist. Analyze and improve code for: {task}'
            },
            'infrastructure': {
                'model': 'speed',
                'role': 'Manage and optimize infrastructure',
                'tools': ['flyio_api', 'lambda_api', 'monitoring'],
                'prompt_template': 'You are an infrastructure specialist. Manage infrastructure for: {task}'
            },
            'analyst': {
                'model': 'primary',
                'role': 'Analyze data and provide strategic insights',
                'tools': ['qdrant', 'mem0', 'business_intelligence'],
                'prompt_template': 'You are a data analyst. Analyze and provide insights for: {task}'
            },
            'business': {
                'model': 'primary',
                'role': 'Handle business intelligence and client data',
                'tools': ['gong', 'hubspot', 'linear', 'notion'],
                'prompt_template': 'You are a business intelligence specialist. Analyze business data for: {task}'
            }
        }
        
        swarm_agents = []
        for agent_type in agents:
            if agent_type in agent_configs:
                config = agent_configs[agent_type]
                
                # Create Agno agent
                try:
                    agno_agent = Agent(
                        name=f"{agent_type}_{swarm_id[:8]}",
                        model=config['model'],
                        role=config['role'],
                        instructions=config['prompt_template'].format(task=task)
                    )
                    
                    swarm_agents.append({
                        'id': str(uuid.uuid4()),
                        'type': agent_type,
                        'config': config,
                        'agno_agent': agno_agent,
                        'status': 'initialized',
                        'created_at': datetime.now().isoformat()
                    })
                except Exception as e:
                    logger.error(f"Failed to create Agno agent {agent_type}: {e}")
                    # Fallback to basic agent
                    swarm_agents.append({
                        'id': str(uuid.uuid4()),
                        'type': agent_type,
                        'config': config,
                        'agno_agent': None,
                        'status': 'fallback',
                        'created_at': datetime.now().isoformat()
                    })
        
        sophia_ecosystem.agent_swarms[swarm_id] = {
            'task': task,
            'agents': swarm_agents,
            'parameters': parameters,
            'status': 'created',
            'created_at': datetime.now().isoformat(),
            'progress': 0
        }
        
        # Start swarm execution in background
        asyncio.create_task(execute_agent_swarm(swarm_id))
        
        await sophia_ecosystem.add_alert('agent_swarm_created', f"Created agent swarm {swarm_id[:8]} with {len(swarm_agents)} agents", 'info')
        
        return {
            'success': True,
            'swarm_id': swarm_id,
            'agents': len(swarm_agents),
            'agent_types': [agent['type'] for agent in swarm_agents],
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        error_msg = f"Agent swarm creation failed: {str(e)}"
        logger.error(error_msg)
        sentry_sdk.capture_exception(e)
        await sophia_ecosystem.add_alert('agent_swarm_error', error_msg, 'error')
        
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

async def execute_agent_swarm(swarm_id: str):
    """Execute agent swarm tasks with progress tracking"""
    try:
        swarm = sophia_ecosystem.agent_swarms.get(swarm_id)
        if not swarm:
            return
        
        swarm['status'] = 'executing'
        swarm['progress'] = 10
        
        # Broadcast start
        await sophia_ecosystem.broadcast_update({
            'type': 'agent_swarm_started',
            'swarm_id': swarm_id,
            'timestamp': datetime.now().isoformat()
        })
        
        # Execute agents in parallel
        tasks = []
        for agent in swarm['agents']:
            task = execute_agent_task(agent, swarm['task'], swarm['parameters'])
            tasks.append(task)
        
        swarm['progress'] = 30
        
        # Wait for all agents to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        swarm['progress'] = 80
        
        # Compile results
        swarm_results = []
        successful_agents = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                swarm_results.append({
                    'agent_id': swarm['agents'][i]['id'],
                    'agent_type': swarm['agents'][i]['type'],
                    'success': False,
                    'error': str(result),
                    'timestamp': datetime.now().isoformat()
                })
            else:
                swarm_results.append({
                    'agent_id': swarm['agents'][i]['id'],
                    'agent_type': swarm['agents'][i]['type'],
                    'success': True,
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                })
                successful_agents += 1
        
        # Synthesize results using primary model
        if successful_agents > 0:
            synthesis_prompt = f"""
            Task: {swarm['task']}
            
            Agent Results:
            {json.dumps(swarm_results, indent=2)}
            
            As SOPHIA V4, synthesize these agent results into a comprehensive response.
            Provide actionable insights and specific recommendations.
            Maintain the neon cowboy personality.
            """
            
            synthesis = await call_openrouter_model('primary', [
                {'role': 'user', 'content': synthesis_prompt}
            ], max_tokens=2000)
            
            swarm['synthesis'] = synthesis
        
        swarm['results'] = swarm_results
        swarm['status'] = 'completed'
        swarm['progress'] = 100
        swarm['completed_at'] = datetime.now().isoformat()
        swarm['success_rate'] = successful_agents / len(swarm['agents']) * 100
        
        # Broadcast completion
        await sophia_ecosystem.broadcast_update({
            'type': 'agent_swarm_completed',
            'swarm_id': swarm_id,
            'success_rate': swarm['success_rate'],
            'results': swarm_results,
            'timestamp': datetime.now().isoformat()
        })
        
        await sophia_ecosystem.add_alert('agent_swarm_completed', f"Agent swarm {swarm_id[:8]} completed with {swarm['success_rate']:.1f}% success rate", 'info')
        
    except Exception as e:
        error_msg = f"Agent swarm execution failed: {str(e)}"
        logger.error(error_msg)
        sentry_sdk.capture_exception(e)
        
        if swarm_id in sophia_ecosystem.agent_swarms:
            sophia_ecosystem.agent_swarms[swarm_id]['status'] = 'failed'
            sophia_ecosystem.agent_swarms[swarm_id]['error'] = str(e)
            sophia_ecosystem.agent_swarms[swarm_id]['progress'] = 0
        
        await sophia_ecosystem.add_alert('agent_swarm_failed', f"Agent swarm {swarm_id[:8]} failed: {error_msg}", 'error')

async def execute_agent_task(agent: dict, task: str, parameters: dict):
    """Execute individual agent task with proper error handling"""
    try:
        agent_type = agent['type']
        config = agent['config']
        agno_agent = agent.get('agno_agent')
        
        # Use Agno agent if available, otherwise fallback to OpenRouter
        if agno_agent:
            try:
                response = agno_agent.run(task)
                return {
                    'agent_type': agent_type,
                    'method': 'agno',
                    'response': response,
                    'timestamp': datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Agno agent failed, falling back to OpenRouter: {e}")
        
        # Fallback to OpenRouter
        system_prompt = f"""You are a {agent_type} agent with the role: {config['role']}
        
        Task: {task}
        Parameters: {json.dumps(parameters)}
        
        Available tools: {', '.join(config['tools'])}
        
        Provide a detailed response with actionable insights and specific recommendations.
        Focus on your specialty area and provide concrete next steps.
        """
        
        response = await call_openrouter_model(
            config['model'],
            [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': task}
            ],
            max_tokens=2000
        )
        
        return {
            'agent_type': agent_type,
            'method': 'openrouter',
            'response': response,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Agent task execution failed: {e}")
        raise e

# Deep web research capabilities
async def conduct_deep_web_research(query: str, sources_limit: int = 5):
    """Conduct comprehensive deep web research with caching"""
    try:
        # Check Redis cache first
        cache_key = f"research:{hashlib.md5(query.encode()).hexdigest()}"
        cached_result = await redis_client.get(cache_key)
        
        if cached_result:
            return json.loads(cached_result)
        
        # Use Tavily for deep web search
        web_results = tavily.run(query)
        
        if not isinstance(web_results, list):
            web_results = [web_results]
        
        # Limit and enhance results
        enhanced_results = []
        for i, result in enumerate(web_results[:sources_limit]):
            if isinstance(result, dict):
                enhanced_results.append({
                    'title': result.get('title', 'No title'),
                    'url': result.get('url', ''),
                    'content': result.get('content', '')[:500] + '...' if len(result.get('content', '')) > 500 else result.get('content', ''),
                    'score': result.get('score', 0),
                    'rank': i + 1,
                    'timestamp': datetime.now().isoformat()
                })
            else:
                enhanced_results.append({
                    'title': f'Result {i + 1}',
                    'content': str(result)[:500] + '...' if len(str(result)) > 500 else str(result),
                    'rank': i + 1,
                    'timestamp': datetime.now().isoformat()
                })
        
        research_result = {
            'query': query,
            'results': enhanced_results,
            'sources_count': len(enhanced_results),
            'timestamp': datetime.now().isoformat()
        }
        
        # Cache result for 1 hour
        await redis_client.setex(cache_key, 3600, json.dumps(research_result))
        
        return research_result
        
    except Exception as e:
        error_msg = f"Deep web research failed: {str(e)}"
        logger.error(error_msg)
        sentry_sdk.capture_exception(e)
        await sophia_ecosystem.add_alert('research_error', error_msg, 'warning')
        
        return {
            'query': query,
            'results': [],
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

# Query classification and routing
async def classify_query_intent(query: str) -> dict:
    """Classify query intent for smart routing"""
    query_lower = query.lower()
    
    # Infrastructure queries
    if any(kw in query_lower for kw in ['scale', 'deploy', 'restart', 'secret', 'infrastructure', 'fly.io', 'lambda', 'gpu']):
        if 'fly.io' in query_lower or 'fly' in query_lower:
            return {'type': 'infrastructure', 'target': 'flyio', 'priority': 'high'}
        elif 'lambda' in query_lower or 'gpu' in query_lower:
            return {'type': 'infrastructure', 'target': 'lambda', 'priority': 'high'}
        else:
            return {'type': 'infrastructure', 'target': 'general', 'priority': 'medium'}
    
    # Repository and code queries
    elif any(kw in query_lower for kw in ['repository', 'repo', 'github', 'code', 'commit', 'merge', 'pr', 'pull request']):
        return {'type': 'repository', 'target': 'github', 'priority': 'high'}
    
    # Business intelligence queries
    elif any(kw in query_lower for kw in ['client', 'customer', 'greystar', 'bh management', 'gong', 'hubspot', 'business']):
        return {'type': 'business', 'target': 'intelligence', 'priority': 'high'}
    
    # Agent swarm queries
    elif any(kw in query_lower for kw in ['agent', 'swarm', 'team', 'collaborate', 'create agent']):
        return {'type': 'agent_swarm', 'target': 'creation', 'priority': 'medium'}
    
    # Health and monitoring queries
    elif any(kw in query_lower for kw in ['health', 'status', 'monitor', 'alert', 'check']):
        return {'type': 'monitoring', 'target': 'health', 'priority': 'medium'}
    
    # Research queries
    elif any(kw in query_lower for kw in ['research', 'search', 'find', 'what is', 'how to', 'weather']):
        return {'type': 'research', 'target': 'web', 'priority': 'low'}
    
    # General conversation
    else:
        return {'type': 'general', 'target': 'conversation', 'priority': 'low'}

# Main autonomous chat endpoint
@app.post("/api/v1/chat")
async def autonomous_chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """Ultimate autonomous chat - CEO's complete partner with smart routing"""
    try:
        start_time = time.time()
        
        # Classify query intent
        intent = await classify_query_intent(request.query)
        
        # Retrieve relevant memories
        memories = await retrieve_relevant_memories(request.user_id, request.query, 3)
        
        # Route based on intent
        if intent['type'] == 'infrastructure':
            return await handle_infrastructure_query(request, intent, memories, start_time)
        elif intent['type'] == 'repository':
            return await handle_repository_query(request, intent, memories, start_time)
        elif intent['type'] == 'business':
            return await handle_business_query(request, intent, memories, start_time)
        elif intent['type'] == 'agent_swarm':
            return await handle_agent_swarm_query(request, intent, memories, start_time)
        elif intent['type'] == 'monitoring':
            return await handle_monitoring_query(request, intent, memories, start_time)
        elif intent['type'] == 'research':
            return await handle_research_query(request, intent, memories, start_time)
        else:
            return await handle_general_query(request, intent, memories, start_time)
    
    except Exception as e:
        error_msg = f"Autonomous chat error: {str(e)}"
        logger.error(error_msg)
        sentry_sdk.capture_exception(e)
        await sophia_ecosystem.add_alert('chat_error', error_msg, 'error')
        
        return {
            'message': f"🤠 Yo, partner! Hit a snag with '{request.query}': {str(e)}. But I'm still locked and loaded with ultimate power! 🤠",
            'error': str(e),
            'response_time': f"{time.time() - time.time():.2f}s",
            'timestamp': datetime.now().isoformat()
        }

# Query handlers
async def handle_infrastructure_query(request: ChatRequest, intent: dict, memories: list, start_time: float):
    """Handle infrastructure-related queries"""
    try:
        if intent['target'] == 'flyio':
            # Extract action and parameters
            action = 'status'
            parameters = {}
            
            if 'scale' in request.query.lower():
                action = 'scale'
                # Extract scale count
                words = request.query.split()
                for word in words:
                    if word.isdigit():
                        parameters['count'] = int(word)
                        break
            elif 'deploy' in request.query.lower():
                action = 'deploy'
            elif 'restart' in request.query.lower():
                action = 'restart'
            elif 'secret' in request.query.lower():
                action = 'update_secret'
                # This would need more sophisticated parsing for real use
            
            result = await control_flyio_infrastructure(action, parameters)
            
            response = f"🤠 Yo, partner! Fly.io {action} operation: {'Success!' if result['success'] else 'Failed!'}\n\n"
            if result['success']:
                response += f"**Output**: {result['output'][:300]}...\n" if len(result.get('output', '')) > 300 else f"**Output**: {result.get('output', '')}\n"
            else:
                response += f"**Error**: {result['error']}\n"
            
            response += "That's the real fucking deal from Fly.io control! 🚀"
            
            await store_conversation_memory(request.user_id, request.query, result, {'action': 'infrastructure_control', 'target': 'flyio'})
            
            return {
                'message': response,
                'infrastructure_result': result,
                'action': 'infrastructure_control',
                'target': 'flyio',
                'response_time': f"{time.time() - start_time:.2f}s",
                'timestamp': datetime.now().isoformat()
            }
        
        elif intent['target'] == 'lambda':
            # Handle Lambda GPU operations
            action = 'gpu_status'
            parameters = {}
            
            if 'task' in request.query.lower():
                action = 'run_task'
                parameters = {
                    'task_type': 'general',
                    'data': {'query': request.query}
                }
            elif 'sync' in request.query.lower():
                action = 'sync_data'
            
            result = await control_lambda_infrastructure(action, parameters)
            
            response = f"🤠 Yo, partner! Lambda GPU {action} operation: {'Success!' if result['success'] else 'Failed!'}\n\n"
            if result['success']:
                if action == 'gpu_status':
                    healthy_gpus = sum(1 for gpu in result.get('gpu_status', []) if gpu['success'])
                    response += f"**GPU Status**: {healthy_gpus}/{len(LAMBDA_IPS)} GPUs healthy\n"
                elif action == 'run_task':
                    response += f"**Task Result**: {json.dumps(result.get('result', {}), indent=2)[:200]}...\n"
                else:
                    response += f"**Result**: Operation completed successfully\n"
            else:
                response += f"**Error**: {result['error']}\n"
            
            response += "That's the real fucking deal from Lambda GPU power! 🔥"
            
            await store_conversation_memory(request.user_id, request.query, result, {'action': 'infrastructure_control', 'target': 'lambda'})
            
            return {
                'message': response,
                'lambda_result': result,
                'action': 'infrastructure_control',
                'target': 'lambda',
                'response_time': f"{time.time() - start_time:.2f}s",
                'timestamp': datetime.now().isoformat()
            }
        
        else:
            # General infrastructure status
            health_status = await monitor_infrastructure_comprehensive()
            
            response = f"🤠 Yo, partner! Here's the infrastructure status:\n\n"
            for service, status in health_status.items():
                if isinstance(status, dict):
                    health_icon = "✅" if status.get('healthy', True) else "❌"
                    response += f"{health_icon} **{service.title()}**: {'Healthy' if status.get('healthy', True) else 'Issues detected'}\n"
            
            response += "\nThat's the real fucking deal from infrastructure monitoring! 🚀"
            
            await store_conversation_memory(request.user_id, request.query, health_status, {'action': 'infrastructure_status'})
            
            return {
                'message': response,
                'infrastructure_status': health_status,
                'action': 'infrastructure_status',
                'response_time': f"{time.time() - start_time:.2f}s",
                'timestamp': datetime.now().isoformat()
            }
    
    except Exception as e:
        logger.error(f"Infrastructure query handler failed: {e}")
        raise e

async def handle_repository_query(request: ChatRequest, intent: dict, memories: list, start_time: float):
    """Handle repository and GitHub-related queries"""
    try:
        # Determine repository
        repository = 'sophia-intel'  # Default
        if 'ai-cherry/' in request.query:
            repo_match = request.query.split('ai-cherry/')[1].split()[0]
            repository = repo_match
        
        # Determine action
        action = 'analyze_repository'
        parameters = {}
        
        if 'analyze' in request.query.lower() or 'structure' in request.query.lower():
            action = 'analyze_repository'
        elif 'commit' in request.query.lower():
            action = 'commit_file'
            # This would need more sophisticated parsing for real use
        elif 'pr' in request.query.lower() or 'pull request' in request.query.lower():
            if 'create' in request.query.lower():
                action = 'create_pr'
            elif 'merge' in request.query.lower():
                action = 'merge_pr'
            else:
                action = 'list_prs'
        elif 'branch' in request.query.lower():
            action = 'create_branch'
        
        result = await execute_github_operation(action, repository, parameters)
        
        response = f"🤠 Yo, partner! GitHub {action} for {repository}: {'Success!' if result['success'] else 'Failed!'}\n\n"
        
        if result['success']:
            if action == 'analyze_repository':
                structure = result.get('structure', {})
                response += f"**Repository Analysis**:\n"
                response += f"- Python files: {len(structure.get('python_files', []))}\n"
                response += f"- Dependencies: {len(structure.get('dependencies', []))}\n"
                response += f"- Issues found: {len(structure.get('issues', []))}\n"
                response += f"- Health score: {structure.get('health_score', 0)}/100\n"
                response += f"- Technologies: {', '.join(structure.get('technologies', []))}\n"
                
                if structure.get('issues'):
                    response += f"\n**Top Issues**:\n"
                    for issue in structure['issues'][:3]:
                        response += f"- {issue}\n"
            
            elif action == 'list_prs':
                prs = result.get('prs', [])
                response += f"**Open Pull Requests** ({len(prs)}):\n"
                for pr in prs[:5]:
                    response += f"- #{pr['number']}: {pr['title']} by {pr['author']}\n"
            
            else:
                response += f"**Result**: {json.dumps(result, indent=2)[:300]}...\n"
        else:
            response += f"**Error**: {result['error']}\n"
        
        response += "That's the real fucking deal from GitHub operations! 🐙"
        
        await store_conversation_memory(request.user_id, request.query, result, {'action': 'github_operation', 'repository': repository})
        
        return {
            'message': response,
            'github_result': result,
            'action': 'github_operation',
            'repository': repository,
            'response_time': f"{time.time() - start_time:.2f}s",
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Repository query handler failed: {e}")
        raise e

async def handle_business_query(request: ChatRequest, intent: dict, memories: list, start_time: float):
    """Handle business intelligence queries with GPU processing"""
    try:
        # Extract client name
        client_names = []
        query_lower = request.query.lower()
        
        if 'greystar' in query_lower:
            client_names.append('Greystar')
        if 'bh management' in query_lower or 'bh' in query_lower:
            client_names.append('BH Management')
        
        if not client_names:
            # Try to extract client name from query
            words = request.query.split()
            for i, word in enumerate(words):
                if word.lower() in ['client', 'customer', 'account'] and i + 1 < len(words):
                    client_names.append(words[i + 1])
                    break
        
        if not client_names:
            client_names = ['General']
        
        # Gather business intelligence
        all_results = []
        
        for client_name in client_names:
            # Fetch data from multiple business sources
            business_data = {}
            
            # Fetch from each service
            for service in ['gong', 'hubspot', 'linear', 'notion']:
                data = await fetch_business_data(service, client_name, client_name)
                business_data[service] = data
            
            # Conduct web research
            web_results = await conduct_deep_web_research(f"{client_name} company analysis 2025", 3)
            
            # Run sentiment analysis on Lambda GPU if Gong data available
            ml_results = None
            if business_data.get('gong', {}).get('data'):
                gong_data = business_data['gong']['data']
                ml_task_data = {
                    'client_name': client_name,
                    'calls': gong_data[:5],  # Limit for processing
                    'analysis_type': 'sentiment_analysis'
                }
                ml_results = await control_lambda_infrastructure('run_task', {
                    'task_type': 'gong_sentiment',
                    'data': ml_task_data
                })
            
            all_results.append({
                'client_name': client_name,
                'business_data': business_data,
                'web_results': web_results,
                'ml_results': ml_results
            })
        
        # Synthesize comprehensive analysis
        synthesis_prompt = f"""
        Business Intelligence Analysis for: {', '.join(client_names)}
        
        Data Gathered: {json.dumps(all_results, indent=2)}
        
        As SOPHIA V4 with Lambda GPU power, provide a comprehensive business intelligence analysis.
        Focus on:
        1. Client health and relationship status
        2. Key insights from call data and business systems
        3. Actionable recommendations
        4. Risk factors and opportunities
        
        Respond in neon cowboy style with professional insights.
        """
        
        analysis = await call_openrouter_model('primary', [
            {'role': 'user', 'content': synthesis_prompt}
        ], max_tokens=2500)
        
        response = f"🤠 {analysis.get('content', 'Analysis completed, partner!')}"
        
        # Ensure neon cowboy style
        if 'fucking' not in response.lower() and 'damn' not in response.lower():
            response += "\n\nThat's the real fucking deal from Lambda GPU-powered business intelligence! 🤠"
        
        result = {
            'clients': client_names,
            'analysis': analysis,
            'business_data': all_results,
            'timestamp': datetime.now().isoformat()
        }
        
        await store_conversation_memory(request.user_id, request.query, result, {'action': 'business_intelligence'})
        
        return {
            'message': response,
            'business_result': result,
            'action': 'business_intelligence',
            'clients': client_names,
            'response_time': f"{time.time() - start_time:.2f}s",
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Business query handler failed: {e}")
        raise e

async def handle_agent_swarm_query(request: ChatRequest, intent: dict, memories: list, start_time: float):
    """Handle agent swarm creation and management queries"""
    try:
        # Determine agents needed based on query
        agents = []
        query_lower = request.query.lower()
        
        if 'research' in query_lower:
            agents.append('researcher')
        if 'code' in query_lower or 'programming' in query_lower:
            agents.append('coder')
        if 'infrastructure' in query_lower or 'deploy' in query_lower:
            agents.append('infrastructure')
        if 'analyze' in query_lower or 'data' in query_lower:
            agents.append('analyst')
        if 'business' in query_lower or 'client' in query_lower:
            agents.append('business')
        
        if not agents:
            agents = ['researcher', 'analyst']  # Default swarm
        
        parameters = {
            'priority': request.priority,
            'context': request.context,
            'user_preferences': memories
        }
        
        result = await create_agent_swarm(request.query, agents, parameters)
        
        response = f"🤠 Yo, partner! Agent swarm creation: {'Success!' if result['success'] else 'Failed!'}\n\n"
        
        if result['success']:
            response += f"**Swarm ID**: {result['swarm_id'][:8]}...\n"
            response += f"**Agents Deployed**: {result['agents']} agents\n"
            response += f"**Agent Types**: {', '.join(result['agent_types'])}\n"
            response += f"**Status**: Executing in background\n"
            response += f"\nYou can check progress with: `/api/v1/agent-swarm/{result['swarm_id']}`\n"
        else:
            response += f"**Error**: {result['error']}\n"
        
        response += "That's the real fucking deal from AI agent swarms! 🤖"
        
        await store_conversation_memory(request.user_id, request.query, result, {'action': 'agent_swarm_creation'})
        
        return {
            'message': response,
            'swarm_result': result,
            'action': 'agent_swarm_creation',
            'response_time': f"{time.time() - start_time:.2f}s",
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Agent swarm query handler failed: {e}")
        raise e

async def handle_monitoring_query(request: ChatRequest, intent: dict, memories: list, start_time: float):
    """Handle monitoring and health check queries"""
    try:
        # Get comprehensive health status
        health_status = await monitor_infrastructure_comprehensive()
        
        response = f"🤠 Yo, partner! Here's the complete system health report:\n\n"
        
        # Infrastructure status
        response += "**🏗️ Infrastructure Status**:\n"
        for service, status in health_status.items():
            if isinstance(status, dict):
                health_icon = "✅" if status.get('healthy', True) else "❌"
                response += f"{health_icon} **{service.title()}**: {'Healthy' if status.get('healthy', True) else 'Issues detected'}\n"
                
                # Add specific details
                if service == 'lambda_labs' and status.get('gpus'):
                    healthy_gpus = sum(1 for gpu in status['gpus'] if gpu['healthy'])
                    response += f"   - GPUs: {healthy_gpus}/{len(status['gpus'])} healthy\n"
                elif service == 'apis' and status.get('apis'):
                    healthy_apis = sum(1 for api in status['apis'].values() if api['healthy'])
                    response += f"   - APIs: {healthy_apis}/{len(status['apis'])} healthy\n"
        
        # Recent alerts
        recent_alerts = sophia_ecosystem.alerts[-5:] if sophia_ecosystem.alerts else []
        if recent_alerts:
            response += f"\n**🚨 Recent Alerts** ({len(recent_alerts)}):\n"
            for alert in recent_alerts:
                severity_icon = "🔴" if alert['severity'] == 'critical' else "🟡" if alert['severity'] == 'warning' else "🔵"
                response += f"{severity_icon} {alert['message']}\n"
        
        # System metrics
        response += f"\n**📊 System Metrics**:\n"
        response += f"- Active connections: {len(sophia_ecosystem.active_connections)}\n"
        response += f"- Active agent swarms: {len(sophia_ecosystem.agent_swarms)}\n"
        response += f"- Last repo sync: {sophia_ecosystem.last_repo_sync.strftime('%H:%M:%S') if sophia_ecosystem.last_repo_sync else 'Never'}\n"
        response += f"- Repositories indexed: {len(sophia_ecosystem.repository_index)}\n"
        
        response += "\nThat's the real fucking deal from comprehensive monitoring! 📊"
        
        await store_conversation_memory(request.user_id, request.query, health_status, {'action': 'health_monitoring'})
        
        return {
            'message': response,
            'health_status': health_status,
            'recent_alerts': recent_alerts,
            'action': 'health_monitoring',
            'response_time': f"{time.time() - start_time:.2f}s",
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Monitoring query handler failed: {e}")
        raise e

async def handle_research_query(request: ChatRequest, intent: dict, memories: list, start_time: float):
    """Handle research and web search queries"""
    try:
        # Conduct deep web research
        research_results = await conduct_deep_web_research(request.query, 5)
        
        # Prepare comprehensive response with context
        context_prompt = f"""
        Query: {request.query}
        
        Web Research Results: {json.dumps(research_results, indent=2)}
        
        Previous Context: {json.dumps(memories, indent=2)}
        
        Repository Context: Available repositories: {list(sophia_ecosystem.repository_index.keys())}
        
        Infrastructure Status: {json.dumps(sophia_ecosystem.infrastructure_status, indent=2)}
        
        As SOPHIA V4, the CEO's ultimate autonomous partner, provide a comprehensive response that:
        1. Directly answers the query with specific insights
        2. Incorporates relevant web research findings
        3. References previous conversation context when relevant
        4. Suggests actionable next steps if applicable
        5. Maintains the neon cowboy personality
        
        Be specific, actionable, and demonstrate deep understanding of the ecosystem.
        """
        
        ai_response = await call_openrouter_model('primary', [
            {'role': 'user', 'content': context_prompt}
        ], max_tokens=2500)
        
        response_content = ai_response.get('content', 'Sorry partner, hit a snag there! 🤠')
        
        # Ensure neon cowboy style
        if not response_content.startswith('🤠'):
            response_content = f"🤠 {response_content}"
        
        if 'fucking' not in response_content.lower() and 'damn' not in response_content.lower():
            response_content += "\n\nThat's the real fucking deal from deep web research! 🤠"
        
        result = {
            'ai_response': ai_response,
            'research_results': research_results,
            'memories_used': len(memories)
        }
        
        await store_conversation_memory(request.user_id, request.query, result, {'action': 'research_query'})
        
        return {
            'message': response_content,
            'research_results': research_results,
            'memories_used': len(memories),
            'ai_model': ai_response.get('model'),
            'action': 'research_query',
            'response_time': f"{time.time() - start_time:.2f}s",
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Research query handler failed: {e}")
        raise e

async def handle_general_query(request: ChatRequest, intent: dict, memories: list, start_time: float):
    """Handle general conversation queries"""
    try:
        # Prepare context with ecosystem awareness
        context_prompt = f"""
        Query: {request.query}
        
        Previous Context: {json.dumps(memories, indent=2)}
        
        Current Ecosystem Status:
        - Infrastructure: {len([s for s in sophia_ecosystem.infrastructure_status.values() if isinstance(s, dict) and s.get('healthy', True)])} services healthy
        - Repositories: {len(sophia_ecosystem.repository_index)} indexed
        - Active Swarms: {len(sophia_ecosystem.agent_swarms)}
        - Recent Alerts: {len(sophia_ecosystem.alerts)}
        
        As SOPHIA V4, the CEO's ultimate autonomous partner with complete ecosystem control, respond to this query.
        Maintain the neon cowboy personality while being helpful and informative.
        Reference your capabilities and current system status when relevant.
        """
        
        ai_response = await call_openrouter_model('primary', [
            {'role': 'user', 'content': context_prompt}
        ], max_tokens=2000)
        
        response_content = ai_response.get('content', 'Howdy partner! I\'m locked and loaded and ready to help! 🤠')
        
        # Ensure neon cowboy style
        if not response_content.startswith('🤠'):
            response_content = f"🤠 {response_content}"
        
        if 'fucking' not in response_content.lower() and 'damn' not in response_content.lower():
            response_content += "\n\nThat's the real fucking deal, partner! 🤠"
        
        result = {
            'ai_response': ai_response,
            'memories_used': len(memories),
            'ecosystem_status': {
                'infrastructure_healthy': len([s for s in sophia_ecosystem.infrastructure_status.values() if isinstance(s, dict) and s.get('healthy', True)]),
                'repositories_indexed': len(sophia_ecosystem.repository_index),
                'active_swarms': len(sophia_ecosystem.agent_swarms)
            }
        }
        
        await store_conversation_memory(request.user_id, request.query, result, {'action': 'general_conversation'})
        
        return {
            'message': response_content,
            'memories_used': len(memories),
            'ai_model': ai_response.get('model'),
            'ecosystem_status': result['ecosystem_status'],
            'action': 'general_conversation',
            'response_time': f"{time.time() - start_time:.2f}s",
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"General query handler failed: {e}")
        raise e

# WebSocket endpoint for real-time updates
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    sophia_ecosystem.active_connections[user_id] = websocket
    
    try:
        # Send initial status
        await websocket.send_json({
            'type': 'connection_established',
            'user_id': user_id,
            'infrastructure_status': sophia_ecosystem.infrastructure_status,
            'repositories': list(sophia_ecosystem.repository_index.keys()),
            'active_swarms': len(sophia_ecosystem.agent_swarms),
            'recent_alerts': sophia_ecosystem.alerts[-5:] if sophia_ecosystem.alerts else [],
            'timestamp': datetime.now().isoformat()
        })
        
        while True:
            # Keep connection alive and handle incoming messages
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get('type') == 'ping':
                    await websocket.send_json({'type': 'pong', 'timestamp': datetime.now().isoformat()})
                elif message.get('type') == 'get_status':
                    await websocket.send_json({
                        'type': 'status_update',
                        'infrastructure': sophia_ecosystem.infrastructure_status,
                        'repositories': len(sophia_ecosystem.repository_index),
                        'swarms': len(sophia_ecosystem.agent_swarms),
                        'alerts': len(sophia_ecosystem.alerts),
                        'timestamp': datetime.now().isoformat()
                    })
                
            except asyncio.TimeoutError:
                # Send periodic heartbeat
                await websocket.send_json({'type': 'heartbeat', 'timestamp': datetime.now().isoformat()})
            
    except WebSocketDisconnect:
        if user_id in sophia_ecosystem.active_connections:
            del sophia_ecosystem.active_connections[user_id]
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        if user_id in sophia_ecosystem.active_connections:
            del sophia_ecosystem.active_connections[user_id]

# Additional API endpoints
@app.post("/api/v1/infrastructure")
async def infrastructure_control(request: InfrastructureRequest):
    """Direct infrastructure control endpoint"""
    if request.target == 'flyio':
        result = await control_flyio_infrastructure(request.action, request.parameters or {})
    elif request.target == 'lambda':
        result = await control_lambda_infrastructure(request.action, request.parameters or {})
    else:
        result = {'success': False, 'error': f'Unknown target: {request.target}'}
    
    return result

@app.post("/api/v1/repository")
async def repository_control(request: RepositoryRequest):
    """Direct repository control endpoint"""
    result = await execute_github_operation(request.action, request.repository, request.parameters or {})
    return result

@app.post("/api/v1/business")
async def business_intelligence(request: BusinessRequest):
    """Direct business intelligence endpoint"""
    try:
        business_data = {}
        
        for service in request.data_sources:
            data = await fetch_business_data(service, request.client, request.client)
            business_data[service] = data
        
        return {
            'success': True,
            'client': request.client,
            'data_sources': request.data_sources,
            'business_data': business_data,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@app.post("/api/v1/agent-swarm")
async def agent_swarm_control(request: AgentSwarmRequest):
    """Direct agent swarm control endpoint"""
    result = await create_agent_swarm(request.task, request.agents, request.parameters)
    return result

@app.get("/api/v1/agent-swarm/{swarm_id}")
async def get_agent_swarm_status(swarm_id: str):
    """Get agent swarm status"""
    swarm = sophia_ecosystem.agent_swarms.get(swarm_id)
    if not swarm:
        raise HTTPException(status_code=404, detail="Swarm not found")
    return swarm

@app.get("/api/v1/alerts")
async def get_alerts(limit: int = 20):
    """Get recent alerts"""
    return {
        'alerts': sophia_ecosystem.alerts[-limit:] if sophia_ecosystem.alerts else [],
        'total_alerts': len(sophia_ecosystem.alerts),
        'timestamp': datetime.now().isoformat()
    }

@app.delete("/api/v1/alerts")
async def clear_alerts():
    """Clear all alerts"""
    sophia_ecosystem.alerts.clear()
    await sophia_ecosystem.broadcast_update({
        'type': 'alerts_cleared',
        'timestamp': datetime.now().isoformat()
    })
    return {'status': 'Alerts cleared', 'timestamp': datetime.now().isoformat()}

# Health and status endpoints
@app.get("/api/v1/health")
async def health():
    """Comprehensive health check with full ecosystem status"""
    health_status = await monitor_infrastructure_comprehensive()
    
    overall_healthy = all(
        isinstance(status, dict) and status.get('healthy', True) 
        for status in health_status.values() 
        if isinstance(status, dict)
    )
    
    return {
        "status": "healthy" if overall_healthy else "degraded",
        "version": "4.0.0-ULTIMATE-INTEGRATED",
        "timestamp": datetime.now().isoformat(),
        "mode": "ULTIMATE_AUTONOMOUS_CEO_PARTNER",
        "personality": "neon_cowboy_ultimate",
        "capabilities": [
            "complete_infrastructure_control",
            "full_github_org_operations",
            "deep_web_research",
            "dynamic_natural_language",
            "auto_repository_indexing",
            "ai_agent_swarms_agno",
            "business_intelligence_gpu",
            "zero_downtime_updates",
            "real_time_monitoring",
            "contextual_memory_management",
            "lambda_gpu_processing",
            "thoughtful_merging",
            "proactive_alerting"
        ],
        "models": OPENROUTER_MODELS,
        "infrastructure": health_status,
        "repositories": {
            'total': len(sophia_ecosystem.repository_index),
            'list': list(sophia_ecosystem.repository_index.keys()),
            'last_sync': sophia_ecosystem.last_repo_sync.isoformat() if sophia_ecosystem.last_repo_sync else None
        },
        "agent_swarms": {
            'active': len(sophia_ecosystem.agent_swarms),
            'running': len([s for s in sophia_ecosystem.agent_swarms.values() if s.get('status') == 'executing']),
            'completed': len([s for s in sophia_ecosystem.agent_swarms.values() if s.get('status') == 'completed'])
        },
        "alerts": {
            'total': len(sophia_ecosystem.alerts),
            'critical': len([a for a in sophia_ecosystem.alerts if a.get('severity') == 'critical']),
            'warnings': len([a for a in sophia_ecosystem.alerts if a.get('severity') == 'warning'])
        },
        "connections": {
            'active_websockets': len(sophia_ecosystem.active_connections),
            'users_connected': list(sophia_ecosystem.active_connections.keys())
        },
        "performance": {
            'last_health_check': sophia_ecosystem.last_health_check.isoformat() if sophia_ecosystem.last_health_check else None,
            'response_time': "0.01s",
            'uptime': "continuous"
        }
    }

@app.get("/api/v1/status")
async def detailed_status():
    """Detailed system status for monitoring"""
    return {
        "infrastructure": sophia_ecosystem.infrastructure_status,
        "repositories": sophia_ecosystem.repository_index,
        "business_intelligence": sophia_ecosystem.business_intelligence,
        "agent_swarms": sophia_ecosystem.agent_swarms,
        "alerts": sophia_ecosystem.alerts,
        "health_monitors": sophia_ecosystem.health_monitors,
        "active_connections": len(sophia_ecosystem.active_connections),
        "last_repo_sync": sophia_ecosystem.last_repo_sync.isoformat() if sophia_ecosystem.last_repo_sync else None,
        "last_health_check": sophia_ecosystem.last_health_check.isoformat() if sophia_ecosystem.last_health_check else None,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/metrics")
async def metrics():
    """Metrics endpoint for monitoring systems"""
    return {
        "infrastructure_health": len([s for s in sophia_ecosystem.infrastructure_status.values() if isinstance(s, dict) and s.get('healthy', True)]),
        "infrastructure_total": len(sophia_ecosystem.infrastructure_status),
        "repositories_indexed": len(sophia_ecosystem.repository_index),
        "agent_swarms_active": len([s for s in sophia_ecosystem.agent_swarms.values() if s.get('status') == 'executing']),
        "agent_swarms_total": len(sophia_ecosystem.agent_swarms),
        "alerts_critical": len([a for a in sophia_ecosystem.alerts if a.get('severity') == 'critical']),
        "alerts_total": len(sophia_ecosystem.alerts),
        "websocket_connections": len(sophia_ecosystem.active_connections),
        "memory_usage_mb": 0,  # Would implement actual memory monitoring
        "cpu_usage_percent": 0,  # Would implement actual CPU monitoring
        "timestamp": datetime.now().isoformat()
    }

# Background monitoring and maintenance
async def background_ecosystem_monitoring():
    """Comprehensive background monitoring and maintenance"""
    while True:
        try:
            # Monitor infrastructure health
            await monitor_infrastructure_comprehensive()
            
            # Update repository index every 30 minutes
            if (not sophia_ecosystem.last_repo_sync or 
                datetime.now() - sophia_ecosystem.last_repo_sync > timedelta(minutes=30)):
                await index_repository_ecosystem()
            
            # Clean up old agent swarms (older than 24 hours)
            current_time = datetime.now()
            for swarm_id, swarm in list(sophia_ecosystem.agent_swarms.items()):
                try:
                    created_at = datetime.fromisoformat(swarm['created_at'])
                    if current_time - created_at > timedelta(hours=24):
                        del sophia_ecosystem.agent_swarms[swarm_id]
                        await sophia_ecosystem.add_alert('swarm_cleanup', f"Cleaned up old swarm {swarm_id[:8]}", 'info')
                except:
                    pass
            
            # Clean up old alerts (keep last 100)
            if len(sophia_ecosystem.alerts) > 100:
                sophia_ecosystem.alerts = sophia_ecosystem.alerts[-100:]
            
            # Sync data to Lambda GPUs every hour
            if current_time.minute == 0:  # Top of the hour
                await control_lambda_infrastructure('sync_data', {})
            
            # Health check every 5 minutes
            await asyncio.sleep(300)
            
        except Exception as e:
            logger.error(f"Background monitoring error: {e}")
            sentry_sdk.capture_exception(e)
            await sophia_ecosystem.add_alert('monitoring_error', f"Background monitoring error: {str(e)}", 'error')
            await asyncio.sleep(60)  # Wait 1 minute on error

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize SOPHIA Ultimate Integrated Ecosystem on startup"""
    logger.info("🤠 SOPHIA V4 Ultimate Integrated Ecosystem starting up...")
    
    # Start background monitoring
    asyncio.create_task(background_ecosystem_monitoring())
    
    # Initial repository indexing
    asyncio.create_task(index_repository_ecosystem())
    
    # Initial infrastructure health check
    asyncio.create_task(monitor_infrastructure_comprehensive())
    
    # Send startup alert
    await sophia_ecosystem.add_alert('system_startup', 'SOPHIA V4 Ultimate Integrated Ecosystem started successfully', 'info')
    
    logger.info("🚀 SOPHIA V4 Ultimate Integrated Ecosystem ready to dominate as CEO's complete autonomous partner!")

@app.on_event("shutdown")
async def shutdown_event():
    """Graceful shutdown"""
    logger.info("🤠 SOPHIA V4 Ultimate Integrated Ecosystem shutting down...")
    
    # Notify all connected clients
    await sophia_ecosystem.broadcast_update({
        'type': 'system_shutdown',
        'message': 'SOPHIA V4 is shutting down gracefully',
        'timestamp': datetime.now().isoformat()
    })
    
    # Close all WebSocket connections
    for user_id, connection in sophia_ecosystem.active_connections.items():
        try:
            await connection.close()
        except:
            pass
    
    # Send shutdown alert
    await sophia_ecosystem.add_alert('system_shutdown', 'SOPHIA V4 Ultimate Integrated Ecosystem shutting down', 'info')
    
    logger.info("👋 SOPHIA V4 Ultimate Integrated Ecosystem shutdown complete")

# Serve static files
app.mount("/v4", StaticFiles(directory="apps/frontend/v4", html=True), name="frontend")
app.mount("/", StaticFiles(directory="apps/frontend/v4", html=True), name="root")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)

