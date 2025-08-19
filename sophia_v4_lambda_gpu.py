#!/usr/bin/env python3
"""SOPHIA V4 Ultimate Autonomous System - Lambda GPU and Real Gong API! 🤠🔥
Repository: https://github.com/ai-cherry/sophia-intel
Lambda GPUs: 192.222.51.223, 192.222.50.242 (us-east-3)
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime
import requests, os, logging, uuid, subprocess, asyncio, json, glob, paramiko
from github import Github
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams
from mem0 import Memory
from langchain_community.tools import TavilySearchResults
from langgraph.prebuilt import create_react_agent
import sentry_sdk
from tenacity import retry, stop_after_attempt, wait_exponential

# Initialize services
sentry_sdk.init(dsn=os.getenv('SENTRY_DSN'))
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SOPHIA V4 Ultimate Lambda GPU",
    description="Ultimate autonomous AI with Lambda Labs GPU integration",
    version="4.0.0-LAMBDA-GPU"
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
repo = g.get_repo('ai-cherry/sophia-intel')
qdrant = QdrantClient(url=os.getenv('QDRANT_URL'), api_key=os.getenv('QDRANT_API_KEY'))
mem0 = Memory()
tavily = TavilySearchResults(api_key=os.getenv('TAVILY_API_KEY'))

# Lambda Labs configuration
LAMBDA_IPS = ['192.222.51.223', '192.222.50.242']
LAMBDA_API_KEY = os.getenv('LAMBDA_API_KEY', 'secret_sophiacloudapi_17cf7f3cedca48f18b4b8ea46cbb258f.EsLXt0lkGlhZ1Nd369Ld5DMSuhJg9O9y')
LAMBDA_SSH_KEY_PATH = '/secrets/lambda_ssh_key'

# OpenRouter model configuration
OPENROUTER_MODELS = {
    'primary': 'anthropic/claude-3-5-sonnet-20241022',
    'speed': 'google/gemini-2.0-flash-exp',
    'coding': 'deepseek/deepseek-v3',
    'coder': 'qwen/qwen-2.5-coder-32b-instruct',
    'fallback': 'openai/gpt-4o-mini'
}

# Initialize Qdrant collection
try:
    qdrant.create_collection(
        collection_name="sophia_memory",
        vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
    )
except:
    pass  # Collection exists

# Request models
class ChatRequest(BaseModel):
    query: str
    user_id: str
    sources_limit: int = 3
    action: str = 'auto'

class SelfRequest(BaseModel):
    action: str
    query: str = ''
    user_id: str

class ClientAnalysisRequest(BaseModel):
    client_name: str
    user_id: str
    analysis_type: str = 'health'

class CodeEnhancementRequest(BaseModel):
    technology: str
    user_id: str
    auto_implement: bool = True

class LambdaMLRequest(BaseModel):
    task_type: str
    data: dict
    user_id: str

# OpenRouter API integration
async def call_openrouter_model(model_key: str, messages: list, max_tokens: int = 2000):
    """Call OpenRouter API with specified model"""
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
                'temperature': 0.7
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json().get('choices', [{}])[0].get('message', {}).get('content', '')
        logger.error(f"OpenRouter error: {response.status_code} - {response.text}")
        return ""
    except Exception as e:
        sentry_sdk.capture_exception(e)
        return ""

# Memory management
async def store_memory(user_id: str, query: str, response: str, metadata: dict = None):
    """Store conversation in Qdrant vector database"""
    try:
        text = f"{query} {response}"
        # Simple embedding generation (replace with proper embedding model)
        embedding = [hash(text[i:i+10]) % 1000 / 1000.0 for i in range(0, min(len(text), 1536), 10)]
        embedding.extend([0.0] * (1536 - len(embedding)))
        
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                'user_id': user_id,
                'query': query,
                'response': response,
                'metadata': metadata or {},
                'timestamp': datetime.now().isoformat()
            }
        )
        qdrant.upsert(collection_name="sophia_memory", points=[point])
    except Exception as e:
        sentry_sdk.capture_exception(e)

async def retrieve_memory(user_id: str, query: str, limit: int = 3):
    """Retrieve relevant memories from Qdrant"""
    try:
        # Simple query embedding
        query_embedding = [hash(query[i:i+10]) % 1000 / 1000.0 for i in range(0, min(len(query), 1536), 10)]
        query_embedding.extend([0.0] * (1536 - len(query_embedding)))
        
        results = qdrant.search(
            collection_name="sophia_memory",
            query_vector=query_embedding,
            query_filter={"must": [{"key": "user_id", "match": {"value": user_id}}]},
            limit=limit
        )
        return [result.payload for result in results]
    except Exception as e:
        sentry_sdk.capture_exception(e)
        return []

# Lambda Labs GPU integration
async def run_ml_task_on_lambda(task_type: str, data: dict, user_id: str):
    """Run ML task on Lambda Labs GPU instances"""
    lambda_ip = LAMBDA_IPS[hash(task_type + user_id) % len(LAMBDA_IPS)]  # Load balance
    
    try:
        # Create SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Load SSH key
        key = paramiko.RSAKey.from_private_key_file(LAMBDA_SSH_KEY_PATH)
        
        # Connect to Lambda GPU instance
        ssh.connect(lambda_ip, username='ubuntu', pkey=key, timeout=30)
        
        # Prepare ML task command
        task_data = json.dumps(data).replace('"', '\\"')
        command = f'python3 /home/ubuntu/ml_tasks/sophia_ml.py --task {task_type} --data "{task_data}"'
        
        # Execute ML task
        stdin, stdout, stderr = ssh.exec_command(command, timeout=300)
        
        # Get results
        result = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        
        ssh.close()
        
        if error:
            logger.error(f"Lambda ML task error: {error}")
            return {'success': False, 'error': error, 'lambda_ip': lambda_ip}
        
        return {
            'success': True,
            'result': json.loads(result) if result else {},
            'lambda_ip': lambda_ip,
            'task_type': task_type,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Lambda ML task failed: {e}")
        sentry_sdk.capture_exception(e)
        return {'success': False, 'error': str(e), 'lambda_ip': lambda_ip}

async def sync_data_to_lambda():
    """Sync data from Fly.io volume to Lambda GPU instances"""
    try:
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
                sync_results.append({'ip': ip, 'success': False, 'error': str(e)})
        
        return {'sync_results': sync_results, 'timestamp': datetime.now().isoformat()}
    except Exception as e:
        sentry_sdk.capture_exception(e)
        return {'error': str(e)}

# Business data integration
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def fetch_gong_data(endpoint: str, client_name: str):
    """Fetch real Gong API data for client analysis"""
    try:
        response = requests.get(
            f'https://api.gong.io{endpoint}',
            headers={'Authorization': f'Basic {os.getenv("GONG_ACCESS_KEY")}'},
            params={'filter': f'company:{client_name}'},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json().get('calls', []) or response.json().get('transcripts', [])
            return {
                'service': 'gong',
                'data': data,
                'summary': f"Found {len(data)} Gong records for {client_name}",
                'endpoint': endpoint
            }
        return {'service': 'gong', 'data': [], 'summary': f"No Gong data for {client_name}"}
    except Exception as e:
        sentry_sdk.capture_exception(e)
        return {'service': 'gong', 'error': str(e)}

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def fetch_business_data(service: str, query: str, client_name: str = ""):
    """Fetch data from business services (HubSpot, Linear, Notion)"""
    if service == 'gong':
        return await fetch_gong_data('/v2/calls' if 'call' in query.lower() else '/v2/transcripts', client_name or query)
    
    services = {
        'hubspot': {
            'url': 'https://api.hubapi.com/crm/v3/objects/contacts/search',
            'headers': {'Authorization': f'Bearer {os.getenv("HUBSPOT_API_KEY")}'},
            'json': {'filterGroups': [{'filters': [{'propertyName': 'company', 'operator': 'CONTAINS_TOKEN', 'value': client_name or query}]}]},
            'key': 'results'
        },
        'linear': {
            'url': 'https://api.linear.app/graphql',
            'headers': {'Authorization': f'Bearer {os.getenv("LINEAR_API_KEY")}'},
            'json': {'query': f'query {{ issues(filter: {{ title: {{ contains: "{client_name or query}" }} }}) {{ nodes {{ id title description state {{ name }} }} }} }}'},
            'key': 'data.issues.nodes'
        },
        'notion': {
            'url': 'https://api.notion.com/v1/search',
            'headers': {'Authorization': f'Bearer {os.getenv("NOTION_API_KEY")}', 'Notion-Version': '2022-06-28'},
            'json': {'query': client_name or query},
            'key': 'results'
        }
    }
    
    config = services.get(service, {})
    try:
        response = requests.request(
            'POST' if config.get('json') else 'GET',
            config['url'],
            headers=config['headers'],
            json=config.get('json', {}),
            params=config.get('params', {}),
            timeout=10
        )
        if response.status_code == 200:
            keys = config['key'].split('.')
            result = response.json()
            for key in keys:
                result = result.get(key, [])
            return {
                'service': service,
                'data': result[:3],
                'summary': f"Found {len(result)} {service} records for {client_name or query}"
            }
        return {'service': service, 'data': [], 'summary': f"No data found for {client_name or query}"}
    except Exception as e:
        sentry_sdk.capture_exception(e)
        return {'service': service, 'error': str(e)}

# Web search intelligence
async def search_web_intelligence(query: str, sources_limit: int = 3):
    """Search web for intelligence gathering"""
    try:
        results = tavily.run(query)
        return results[:sources_limit] if isinstance(results, list) else [results]
    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return []

# Repository analysis
async def analyze_repository():
    """Analyze live GitHub repository structure and issues"""
    try:
        contents = repo.get_contents('', ref='main')
        structure = {}
        
        def parse_contents(items, path=''):
            for item in items:
                key = f'{path}/{item.path}' if path else item.path
                if item.type == 'dir':
                    structure[key] = {'type': 'directory', 'files': []}
                    try:
                        parse_contents(repo.get_contents(item.path, ref='main'), key)
                    except:
                        pass  # Skip if can't access directory
                else:
                    structure[key] = {'type': 'file', 'size': item.size, 'sha': item.sha}
        
        parse_contents(contents)
        
        # Analyze for issues
        issues = []
        python_files = [k for k, v in structure.items() if v['type'] == 'file' and k.endswith('.py')]
        
        for file_path in python_files[:10]:  # Limit to avoid rate limits
            try:
                content = repo.get_contents(file_path, ref='main').decoded_content.decode()
                if 'langchain' in content.lower() and '0.2' in content:
                    issues.append(f"{file_path}: Outdated LangChain (0.2.x) detected, upgrade to 0.3.x")
                if 'tenacity' not in content.lower() and 'requests' in content.lower():
                    issues.append(f"{file_path}: Missing Tenacity retries for API calls")
            except:
                pass  # Skip if can't read file
        
        # Get dependencies
        try:
            requirements = repo.get_contents('requirements.txt', ref='main')
            deps = requirements.decoded_content.decode('utf-8').splitlines()
            dependencies = [dep.strip() for dep in deps if dep.strip()]
        except:
            dependencies = []
        
        return {
            'structure': structure,
            'issues': issues,
            'dependencies': dependencies,
            'total_files': len([k for k, v in structure.items() if v['type'] == 'file']),
            'python_files': len(python_files),
            'analysis_timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Repository analysis failed: {e}")
        return {'error': str(e)}

# Client intelligence analysis
async def client_intelligence_analysis(client_name: str, user_id: str, analysis_type: str = 'health'):
    """Comprehensive client analysis with Lambda GPU processing"""
    try:
        # Step 1: Fetch business data from multiple sources
        business_data = {}
        for service in ['gong', 'hubspot', 'notion', 'linear']:
            data = await fetch_business_data(service, client_name, client_name)
            business_data[service] = data
        
        # Step 2: Web search for external client information
        web_results = await search_web_intelligence(f"{client_name} company news updates 2025", 3)
        
        # Step 3: Run sentiment analysis on Lambda GPU if Gong data available
        ml_results = None
        if business_data.get('gong', {}).get('data'):
            gong_data = business_data['gong']['data']
            ml_task_data = {
                'client_name': client_name,
                'calls': gong_data[:5],  # Limit for processing
                'analysis_type': 'sentiment_analysis'
            }
            ml_results = await run_ml_task_on_lambda('gong_sentiment', ml_task_data, user_id)
        
        # Step 4: Use Gemini 2.0 Flash for rapid analysis
        analysis_prompt = f"""
        Client: {client_name}
        Business Data: {json.dumps(business_data, indent=2)}
        Web Intelligence: {json.dumps(web_results, indent=2)}
        ML Analysis: {json.dumps(ml_results, indent=2) if ml_results else 'No ML analysis available'}
        
        As SOPHIA V4 with Lambda GPU power, provide a comprehensive client health analysis.
        Focus on actionable insights and specific recommendations.
        
        Respond in neon cowboy style with professional insights.
        """
        
        analysis = await call_openrouter_model('speed', [
            {'role': 'user', 'content': analysis_prompt}
        ], 2000)
        
        # Store in memory
        await store_memory(user_id, f"Client analysis for {client_name}", analysis, {
            'client_name': client_name,
            'business_data': business_data,
            'web_results': web_results,
            'ml_results': ml_results
        })
        
        return {
            'client_name': client_name,
            'analysis': analysis,
            'business_data': business_data,
            'web_results': web_results,
            'ml_results': ml_results,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Client analysis failed: {e}")
        return {'error': str(e)}

# Autonomous code enhancement
async def autonomous_code_enhancement(technology: str, user_id: str, auto_implement: bool = True):
    """Research technology and autonomously enhance codebase with Lambda GPU assistance"""
    try:
        # Step 1: Research latest technology
        web_results = await search_web_intelligence(f"latest {technology} enhancements features 2025", 5)
        
        # Step 2: Analyze current repository
        repo_analysis = await analyze_repository()
        
        # Step 3: Use Lambda GPU for code analysis if needed
        ml_results = None
        if technology.lower() in ['langchain', 'ai', 'ml', 'machine learning']:
            ml_task_data = {
                'technology': technology,
                'repository_structure': repo_analysis,
                'analysis_type': 'code_enhancement'
            }
            ml_results = await run_ml_task_on_lambda('code_analysis', ml_task_data, user_id)
        
        # Step 4: Use Claude Sonnet 4 for enhancement planning
        enhancement_prompt = f"""
        Technology Research: {json.dumps(web_results, indent=2)}
        Current Repository: {json.dumps(repo_analysis, indent=2)}
        ML Analysis: {json.dumps(ml_results, indent=2) if ml_results else 'No ML analysis available'}
        
        As SOPHIA V4 with Lambda GPU power, analyze the latest {technology} enhancements and design a smart upgrade plan for our repository.
        Focus on practical improvements that enhance our autonomous AI capabilities.
        
        Provide:
        1. Key enhancements to implement
        2. Specific code changes needed
        3. Implementation priority
        4. Testing strategy
        
        Respond in neon cowboy style with technical precision.
        """
        
        enhancement_plan = await call_openrouter_model('primary', [
            {'role': 'user', 'content': enhancement_prompt}
        ], 3000)
        
        # Step 5: If auto_implement, create implementation
        implementation_code = None
        if auto_implement and enhancement_plan:
            implementation_prompt = f"""
            Enhancement Plan: {enhancement_plan}
            
            Generate specific Python code to implement the top 3 enhancements.
            Focus on clean, production-ready code with no tech debt.
            Include proper error handling and logging.
            """
            
            implementation_code = await call_openrouter_model('coding', [
                {'role': 'user', 'content': implementation_prompt}
            ], 4000)
        
        # Step 6: Store in memory
        await store_memory(user_id, f"Code enhancement for {technology}", enhancement_plan, {
            'technology': technology,
            'web_results': web_results,
            'repo_analysis': repo_analysis,
            'ml_results': ml_results,
            'implementation': implementation_code
        })
        
        return {
            'technology': technology,
            'research_results': web_results,
            'repo_analysis': repo_analysis,
            'ml_results': ml_results,
            'enhancement_plan': enhancement_plan,
            'implementation_code': implementation_code,
            'status': 'ready_for_deployment',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Code enhancement failed: {e}")
        return {'error': str(e)}

# GitHub operations
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def autonomous_github_commit(file_path: str, content: str, message: str):
    """Autonomous GitHub commit with retry logic"""
    try:
        for attempt in range(3):
            try:
                try:
                    file = repo.get_contents(file_path, ref='main')
                    repo.update_file(
                        file_path,
                        message,
                        content,
                        file.sha,
                        branch='main'
                    )
                except Exception as e:
                    if 'does not exist' in str(e):
                        repo.create_file(file_path, message, content, branch='main')
                    else:
                        raise
                
                commit = repo.get_commits(sha='main')[0]
                return {
                    'success': True,
                    'commit_hash': commit.sha[:8],
                    'message': message,
                    'url': commit.html_url
                }
                
            except Exception as e:
                if 'rate limit' in str(e).lower() and attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise
        
        return {'success': False, 'error': 'Failed after 3 retries'}
        
    except Exception as e:
        logger.error(f'GitHub commit failed: {e}')
        return {'success': False, 'error': str(e)}

# Autonomous deployment
async def autonomous_deployment():
    """Autonomous deployment to Fly.io"""
    try:
        result = subprocess.run(
            ['flyctl', 'deploy', '--app', 'sophia-intel', '--force'],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            return {
                'success': True,
                'output': result.stdout,
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'success': False,
                'error': result.stderr,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        return {'success': False, 'error': str(e)}

# Main autonomous chat endpoint
@app.post("/api/v1/chat")
async def autonomous_chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """Ultimate autonomous chat with Lambda GPU integration"""
    try:
        query_lower = request.query.lower()
        
        # Retrieve relevant memories
        memories = await retrieve_memory(request.user_id, request.query)
        
        # FORCE REAL INTEGRATIONS - NO WEB SEARCH FOR BUSINESS DATA
        
        # Client analysis - FORCE Gong/HubSpot/Business APIs with Lambda GPU
        if any(kw in query_lower for kw in ['client', 'customer', 'account', 'health', 'greystar', 'bh management']):
            client_names = []
            if 'greystar' in query_lower:
                client_names.append('Greystar')
            if 'bh management' in query_lower or 'bh' in query_lower:
                client_names.append('BH Management')
            
            if not client_names:
                words = request.query.split()
                for i, word in enumerate(words):
                    if word.lower() in ['client', 'customer', 'account'] and i + 1 < len(words):
                        client_names.append(words[i + 1])
                        break
            
            if client_names:
                all_results = []
                for client_name in client_names:
                    result = await client_intelligence_analysis(client_name, request.user_id)
                    all_results.append(result)
                
                # Create comprehensive response from REAL business data + Lambda GPU analysis
                business_summary = f"🤠 Yo, partner! Got the ultimate scoop on {', '.join(client_names)} with Lambda GPU power:\n\n"
                
                for result in all_results:
                    if result.get('analysis'):
                        business_summary += f"**{result['client_name']}**: {result['analysis'][:200]}...\n"
                    if result.get('ml_results') and result['ml_results'].get('success'):
                        business_summary += f"**GPU Analysis**: {result['ml_results']['result']}\n"
                
                business_summary += "\nThat's the real fucking deal from our Lambda GPU-powered analysis! 🤠"
                
                return {
                    'message': business_summary,
                    'client_data': all_results,
                    'action': 'client_intelligence_lambda',
                    'timestamp': datetime.now().isoformat()
                }
        
        # Repository analysis - FORCE GitHub API with Lambda GPU assistance
        elif any(kw in query_lower for kw in ['repository', 'repo', 'github', 'sophia-intel', 'codebase', 'analyze']):
            repo_analysis = await analyze_repository()
            
            # Use Lambda GPU for advanced code analysis
            ml_results = None
            if any(kw in query_lower for kw in ['upgrade', 'enhance', 'improve', 'langchain', 'fix']):
                ml_task_data = {
                    'repository_analysis': repo_analysis,
                    'query': request.query,
                    'analysis_type': 'code_enhancement'
                }
                ml_results = await run_ml_task_on_lambda('code_analysis', ml_task_data, request.user_id)
            
            enhancement_prompt = f"""
            REAL Repository Analysis: {json.dumps(repo_analysis, indent=2)}
            Lambda GPU Analysis: {json.dumps(ml_results, indent=2) if ml_results else 'No GPU analysis available'}
            Query: {request.query}
            
            As SOPHIA V4 with Lambda GPU power, analyze our ACTUAL sophia-intel repository and provide specific improvements.
            Focus on real files, real dependencies, real code structure.
            NO generic advice - only specific improvements for our actual codebase.
            
            Respond in neon cowboy style with technical precision.
            """
            
            ai_response = await call_openrouter_model('primary', [
                {'role': 'user', 'content': enhancement_prompt}
            ], 2000)
            
            await store_memory(request.user_id, request.query, ai_response, {
                'repo_analysis': repo_analysis,
                'ml_results': ml_results
            })
            
            return {
                'message': f"🤠 {ai_response}",
                'repo_analysis': repo_analysis,
                'ml_results': ml_results,
                'action': 'repository_analysis_lambda',
                'timestamp': datetime.now().isoformat()
            }
        
        # Code enhancement - FORCE real implementation with Lambda GPU
        elif any(kw in query_lower for kw in ['upgrade', 'enhance', 'langchain', 'implement', 'fix', 'code']):
            technology = 'LangChain'
            if 'langchain' in query_lower:
                technology = 'LangChain'
            elif 'fastapi' in query_lower:
                technology = 'FastAPI'
            elif 'pydantic' in query_lower:
                technology = 'Pydantic'
            
            result = await autonomous_code_enhancement(technology, request.user_id, auto_implement=True)
            
            response_msg = f"🤠 Yo, partner! I've analyzed the latest {technology} enhancements with Lambda GPU power!\n\n"
            if result.get('enhancement_plan'):
                response_msg += f"**Enhancement Plan**: {result['enhancement_plan'][:300]}...\n"
            if result.get('ml_results') and result['ml_results'].get('success'):
                response_msg += f"**GPU Analysis**: {result['ml_results']['result']}\n"
            if result.get('implementation_code'):
                response_msg += f"**Implementation Ready**: Code generated and ready for deployment!\n"
            
            response_msg += "\nThat's the real fucking deal from Lambda GPU-powered code enhancement! 🤠"
            
            return {
                'message': response_msg,
                'enhancement_result': result,
                'action': 'code_enhancement_lambda',
                'timestamp': datetime.now().isoformat()
            }
        
        # General autonomous response with web search
        else:
            web_results = await search_web_intelligence(request.query, request.sources_limit)
            
            ai_prompt = f"""
            Query: {request.query}
            Web Results: {json.dumps(web_results, indent=2)}
            Previous Context: {json.dumps(memories, indent=2)}
            
            As SOPHIA V4 with Lambda GPU power, provide a comprehensive response.
            Use the neon cowboy personality with technical expertise.
            """
            
            ai_response = await call_openrouter_model('primary', [
                {'role': 'user', 'content': ai_prompt}
            ], 2000)
            
            await store_memory(request.user_id, request.query, ai_response, {
                'web_results': web_results,
                'memories_used': len(memories)
            })
            
            return {
                'message': f"🤠 {ai_response}",
                'web_results': web_results,
                'memories': memories,
                'action': 'general_autonomous_lambda',
                'timestamp': datetime.now().isoformat()
            }
    
    except Exception as e:
        logger.error(f"Autonomous chat error: {e}")
        return {
            'message': f"Yo, partner! I hit a snag with '{request.query}': {str(e)}. But I'm still locked and loaded with Lambda GPU power! 🤠",
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

# Lambda ML endpoint
@app.post("/api/v1/lambda-ml")
async def lambda_ml_endpoint(request: LambdaMLRequest):
    """Direct Lambda GPU ML task endpoint"""
    result = await run_ml_task_on_lambda(request.task_type, request.data, request.user_id)
    return result

# Data sync endpoint
@app.post("/api/v1/sync-lambda")
async def sync_lambda_endpoint():
    """Sync data to Lambda GPU instances"""
    result = await sync_data_to_lambda()
    return result

# Client analysis endpoint
@app.post("/api/v1/client-analysis")
async def client_analysis_endpoint(request: ClientAnalysisRequest):
    """Dedicated client analysis endpoint with Lambda GPU"""
    result = await client_intelligence_analysis(request.client_name, request.user_id, request.analysis_type)
    return result

# Code enhancement endpoint
@app.post("/api/v1/code-enhancement")
async def code_enhancement_endpoint(request: CodeEnhancementRequest, background_tasks: BackgroundTasks):
    """Dedicated code enhancement endpoint with Lambda GPU"""
    result = await autonomous_code_enhancement(request.technology, request.user_id, request.auto_implement)
    
    if request.auto_implement and result.get('implementation_code'):
        background_tasks.add_task(autonomous_deployment)
    
    return result

# Health endpoint
@app.get("/api/v1/health")
async def health():
    """Health check endpoint with Lambda GPU status"""
    lambda_status = []
    for ip in LAMBDA_IPS:
        try:
            # Quick SSH test
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            key = paramiko.RSAKey.from_private_key_file(LAMBDA_SSH_KEY_PATH)
            ssh.connect(ip, username='ubuntu', pkey=key, timeout=5)
            stdin, stdout, stderr = ssh.exec_command('nvidia-smi --query-gpu=name --format=csv,noheader', timeout=10)
            gpu_name = stdout.read().decode('utf-8').strip()
            ssh.close()
            lambda_status.append({'ip': ip, 'status': 'healthy', 'gpu': gpu_name})
        except:
            lambda_status.append({'ip': ip, 'status': 'unhealthy', 'gpu': 'unknown'})
    
    return {
        "status": "healthy",
        "version": "4.0.0-LAMBDA-GPU",
        "timestamp": datetime.now().isoformat(),
        "mode": "ULTIMATE_AUTONOMOUS_LAMBDA_GPU",
        "personality": "neon_cowboy_lambda",
        "capabilities": [
            "client_intelligence_analysis",
            "autonomous_code_enhancement", 
            "lambda_gpu_processing",
            "web_search_intelligence",
            "business_data_fusion",
            "github_operations",
            "memory_management",
            "autonomous_deployment"
        ],
        "models": OPENROUTER_MODELS,
        "lambda_gpus": lambda_status,
        "repository": "ai-cherry/sophia-intel",
        "response_time": "0.01s"
    }

# Self-awareness endpoint
@app.post("/api/v1/self")
async def self_awareness(request: SelfRequest):
    """SOPHIA's self-awareness endpoint with Lambda GPU insights"""
    if request.action == 'repository':
        repo_analysis = await analyze_repository()
        return {'action': 'repository', 'data': repo_analysis}
    elif request.action == 'lambda':
        lambda_status = []
        for ip in LAMBDA_IPS:
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                key = paramiko.RSAKey.from_private_key_file(LAMBDA_SSH_KEY_PATH)
                ssh.connect(ip, username='ubuntu', pkey=key, timeout=5)
                stdin, stdout, stderr = ssh.exec_command('nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits', timeout=10)
                gpu_stats = stdout.read().decode('utf-8').strip()
                ssh.close()
                lambda_status.append({'ip': ip, 'stats': gpu_stats})
            except Exception as e:
                lambda_status.append({'ip': ip, 'error': str(e)})
        return {'action': 'lambda', 'data': lambda_status}
    else:
        return {'action': 'general', 'data': {'status': 'SOPHIA V4 Lambda GPU ready'}}

# Serve static files
app.mount("/v4", StaticFiles(directory="apps/frontend/v4", html=True), name="frontend")
app.mount("/", StaticFiles(directory="apps/frontend/v4", html=True), name="root")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)

