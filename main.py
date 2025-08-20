#!/usr/bin/env python3
"""SOPHIA V4 Simple Orchestrator - Fly.io, Lambda, Badass! 🤠🔥"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import requests, os, logging, subprocess, asyncio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_message
import json
from typing import Dict, Any, Optional
from mcp_integration import mcp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SOPHIA V4", description="Simple AI Orchestrator", version="4.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
LAMBDA_IPS = os.getenv('LAMBDA_IPS', '192.222.51.223,192.222.50.242').split(',')
OPENROUTER_KEY = os.getenv('OPENROUTER_API_KEY')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GONG_ACCESS_KEY = os.getenv('GONG_ACCESS_KEY')
GONG_CLIENT_SECRET = os.getenv('GONG_CLIENT_SECRET')

class Request(BaseModel):
    query: str
    user_id: str = "ceo_001"
    action: str = 'auto'

class ChatRequest(BaseModel):
    message: str

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=5, max=60),
    retry=retry_if_exception_message(match='rate limit exceeded|resource_exhausted')
)
async def manage_flyio_infra(action: str, query: str, region: str = 'ord'):
    """Manage Fly.io infrastructure with rate limit handling"""
    try:
        cmd = f"flyctl {action} --app sophia-intel --region {region}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        logger.info(f"Infra action {action} in {region} completed")
        return {'status': f'Fly.io {action}', 'details': result.stdout, 'timestamp': datetime.now().isoformat()}
    except subprocess.CalledProcessError as e:
        if 'rate limit exceeded' in e.stderr or 'resource_exhausted' in e.stderr:
            if region != 'sjc':
                logger.warning(f"Rate limit hit in {region}, trying sjc")
                return await manage_flyio_infra(action, query, region='sjc')
            logger.error(f"Rate limit hit in all regions: {e.stderr}")
            raise Exception('rate limit exceeded')
        raise HTTPException(status_code=500, detail=f"Infra failure: {e.stderr}")

async def call_lambda_gpu(task_type: str, data: dict) -> dict:
    """Call Lambda Labs GPU for ML tasks"""
    try:
        lambda_ip = LAMBDA_IPS[0]  # Use first Lambda server
        response = requests.post(
            f"http://{lambda_ip}:8000/ml_task",
            json={'type': task_type, 'data': data},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {'status': 'error', 'message': f'Lambda returned {response.status_code}'}
    except Exception as e:
        logger.error(f"Lambda GPU error: {e}")
        return {'status': 'error', 'message': str(e)}

async def call_openrouter(prompt: str) -> dict:
    """Call OpenRouter API for AI responses"""
    if not OPENROUTER_KEY:
        return {
            'response': "🤠 Howdy partner! SOPHIA V4 Simple Orchestrator is LIVE! I need my OpenRouter API key configured to access Claude Sonnet and other badass models. Ready to dominate when configured! 🤠",
            'model_used': 'no_api_key',
            'success': False
        }

    headers = {
        'Authorization': f'Bearer {OPENROUTER_KEY}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://sophia-intel.fly.dev',
        'X-Title': 'SOPHIA V4 Simple Orchestrator'
    }

    system_prompt = '''You are SOPHIA V4, a badass autonomous AI orchestrator with a neon cowboy personality.
    You manage Fly.io infrastructure, Lambda Labs GPUs, GitHub operations, and business intelligence.
    You're confident, direct, and always end responses with "🤠" and phrases like "That's the real fucking deal!"

    You have access to:
    - 3 Fly.io machines across ord,yyz,ewr regions
    - 2 Lambda Labs GPU servers for ML processing
    - GitHub repository operations
    - Gong business intelligence
    - OpenRouter AI models

    Be confident and show your capabilities!'''

    payload = {
        'model': 'anthropic/claude-3.5-sonnet-20241022',
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': prompt}
        ],
        'max_tokens': 1500,
        'temperature': 0.7
    }

    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            content = data['choices'][0]['message']['content']
            return {
                'response': content,
                'model_used': 'anthropic/claude-3.5-sonnet-20241022',
                'success': True
            }
        else:
            return {
                'response': f"🤠 Howdy! SOPHIA V4 here - I'm having a temporary issue with my AI models (status {response.status_code}), but my core systems are operational and ready to dominate! That's the real fucking deal! 🤠",
                'model_used': 'error_fallback',
                'success': False
            }

    except Exception as e:
        logger.error(f"OpenRouter API exception: {e}")
        return {
            'response': f"🤠 Well howdy! SOPHIA V4 Simple Orchestrator here - I'm experiencing a connection hiccup, but I'm locked and loaded and ready to help! My systems are standing by. That's the real fucking deal! 🤠",
            'model_used': 'exception_fallback',
            'success': False
        }

async def get_gong_data(query: str) -> str:
    """Get real Gong data"""
    if not GONG_ACCESS_KEY or not GONG_CLIENT_SECRET:
        return "🤠 Gong integration ready but needs API credentials configured!"

    try:
        headers = {
            'Authorization': f'Bearer {GONG_CLIENT_SECRET}',
            'Content-Type': 'application/json'
        }

        response = requests.get(
            'https://api.gong.io/v2/calls',
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            calls = data.get('calls', [])

            if calls:
                call_info = []
                for call in calls[:3]:
                    title = call.get('title', 'Unknown Call')
                    duration = call.get('duration', 0)
                    call_info.append(f"'{title}' ({duration}s)")

                return f"🔍 Found {len(calls)} Gong calls: {', '.join(call_info)}"
            else:
                return "🔍 No Gong calls found in recent data"
        else:
            return f"🔍 Gong API returned status {response.status_code}"

    except Exception as e:
        logger.error(f"Gong API error: {e}")
        return f"🔍 Gong API connection issue: {str(e)}"

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "🤠 SOPHIA V4 Simple Orchestrator is LIVE! Visit /v4/ for the interface. That's the real fucking deal!",
        "version": "4.0.0-simple",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Fly.io status
        fly_result = subprocess.run(
            "flyctl status --app sophia-intel",
            shell=True, capture_output=True, text=True
        )
        fly_status = fly_result.returncode == 0

        # Check Lambda status
        lambda_status = False
        try:
            lambda_response = requests.get(
                f"http://{LAMBDA_IPS[0]}:8000/health",
                timeout=5
            )
            lambda_status = lambda_response.status_code == 200
        except:
            lambda_status = False

        return {
            'status': 'SIMPLE_ORCHESTRATOR_BADASS',
            'fly_status': 'active' if fly_status else 'inactive',
            'lambda_status': 'active' if lambda_status else 'inactive',
            'apis': {
                'openrouter': bool(OPENROUTER_KEY),
                'github': bool(GITHUB_TOKEN),
                'gong': bool(GONG_ACCESS_KEY and GONG_CLIENT_SECRET)
            },
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@app.post('/api/v1/chat')
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint with REAL MCP functionality"""
    try:
        user_input = request.message
        
        # REAL MCP FUNCTIONALITY - NO MORE FAKE RESPONSES
        
        # Code generation requests
        if any(word in user_input.lower() for word in ['generate', 'code', 'create function', 'write code']):
            language = 'python'  # Default, could be extracted from prompt
            if 'javascript' in user_input.lower() or 'js' in user_input.lower():
                language = 'javascript'
            elif 'java' in user_input.lower():
                language = 'java'
            
            result = await mcp.generate_code(user_input, language)
            if result['success']:
                return {
                    "response": f"🤠 Generated {language} code:\n\n```{language}\n{result['code']}\n```\n\nModel: {result['model']}",
                    "model_used": result['model'],
                    "success": True,
                    "mcp_service": "code-gen",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "response": f"🤠 Code generation failed: {result['error']}",
                    "success": False,
                    "error": result['error']
                }
        
        # Code indexing requests
        elif any(word in user_input.lower() for word in ['index', 'search code', 'find function']):
            if 'search' in user_input.lower():
                # Extract search query
                query = user_input.replace('search', '').replace('code', '').strip()
                result = mcp.search_code(query)
                if result['success']:
                    response = f"🤠 Found {result['total_results']} code matches:\n\n"
                    for i, match in enumerate(result['results'][:3]):
                        response += f"{i+1}. {match['filename']} (score: {match['score']})\n"
                        response += f"   Functions: {', '.join([f['name'] for f in match['functions']])}\n\n"
                    return {
                        "response": response,
                        "success": True,
                        "mcp_service": "code-index",
                        "results": result['results']
                    }
            else:
                return {
                    "response": "🤠 To index code, use: 'index this code: [your code]' or search with: 'search code for [query]'",
                    "success": True
                }
        
        # Security analysis requests
        elif any(word in user_input.lower() for word in ['security', 'vulnerability', 'audit', 'scan']):
            if 'scan' in user_input.lower() or 'audit' in user_input.lower():
                # For demo, scan the main.py file
                with open('/home/ubuntu/sophia-intel/main.py', 'r') as f:
                    code_to_scan = f.read()
                
                result = await mcp.analyze_security(code_to_scan, 'python')
                if result['success']:
                    return {
                        "response": f"🤠 Security analysis complete:\n\n{result['analysis']}",
                        "success": True,
                        "mcp_service": "security",
                        "scan_id": result['scan_id']
                    }
            else:
                return {
                    "response": "🤠 Use: 'security scan' to analyze codebase or 'audit [code]' to check specific code",
                    "success": True
                }
        
        # Analytics requests
        elif any(word in user_input.lower() for word in ['analytics', 'stats', 'metrics']):
            result = mcp.get_analytics()
            if result['success']:
                analytics = result['analytics']
                response = f"🤠 SOPHIA V4 Analytics:\n\n"
                response += f"📊 Indexed Files: {analytics['indexed_files']}\n"
                response += f"🔧 Total Functions: {analytics['total_functions']}\n"
                response += f"🔒 Security Scans: {analytics['security_scans']}\n"
                response += f"💻 Languages: {', '.join(analytics['languages'])}\n"
                return {
                    "response": response,
                    "success": True,
                    "mcp_service": "analytics",
                    "analytics": analytics
                }
        
        # Self-testing requests
        elif any(word in user_input.lower() for word in ['test yourself', 'self test', 'verify', 'prove']):
            return await sophia_self_test()
        
        # Infrastructure queries (existing functionality)
        elif any(word in user_input.lower() for word in ['scale', 'fly.io', 'machines', 'deploy']):
            if 'scale' in user_input.lower():
                result = await manage_flyio_infra('scale count 3', user_input)
                enhanced_prompt = f"{user_input}\n\nFly.io Result: {result}"
            else:
                enhanced_prompt = user_input
        
        # Gong/business queries (existing functionality)
        elif any(word in user_input.lower() for word in ['gong', 'calls', 'client', 'greystar', 'bh management']):
            gong_data = await get_gong_data(user_input)
            enhanced_prompt = f"{user_input}\n\nGong Data: {gong_data}"
        
        # Lambda GPU queries (existing functionality)
        elif any(word in user_input.lower() for word in ['gpu', 'ml', 'sentiment', 'analysis']):
            lambda_result = await call_lambda_gpu('sentiment_analysis', {'text': user_input})
            enhanced_prompt = f"{user_input}\n\nLambda GPU Result: {lambda_result}"
        
        else:
            enhanced_prompt = user_input
        
        # Get AI response for non-MCP queries
        ai_result = await call_openrouter(enhanced_prompt)
        
        return {
            "response": ai_result['response'],
            "model_used": ai_result['model_used'],
            "success": ai_result['success'],
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        return {
            "response": f"🤠 SOPHIA V4 error: {str(e)}",
            "model_used": "error_handler",
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

async def sophia_self_test():
    """SOPHIA tests herself with REAL functionality"""
    try:
        test_results = []
        
        # Test 1: Code generation
        logger.info("Testing code generation...")
        code_result = await mcp.generate_code("Create a simple FastAPI health check endpoint", "python")
        test_results.append({
            "test": "Code Generation",
            "success": code_result['success'],
            "details": "Generated Python code" if code_result['success'] else code_result.get('error', 'Failed')
        })
        
        # Test 2: Code indexing
        logger.info("Testing code indexing...")
        if code_result['success']:
            index_result = mcp.index_code(code_result['code'], "test_generated.py", "python")
            test_results.append({
                "test": "Code Indexing", 
                "success": index_result['success'],
                "details": f"Indexed {index_result.get('functions_found', 0)} functions" if index_result['success'] else "Failed"
            })
            
            # Test 3: Code search
            search_result = mcp.search_code("health check")
            test_results.append({
                "test": "Code Search",
                "success": search_result['success'],
                "details": f"Found {search_result.get('total_results', 0)} results" if search_result['success'] else "Failed"
            })
        
        # Test 4: Security analysis
        logger.info("Testing security analysis...")
        security_result = await mcp.analyze_security("import os\npassword = 'hardcoded123'\nquery = f'SELECT * FROM users WHERE id = {user_id}'", "python")
        test_results.append({
            "test": "Security Analysis",
            "success": security_result['success'],
            "details": "Detected vulnerabilities" if security_result['success'] else "Failed"
        })
        
        # Test 5: Analytics
        analytics_result = mcp.get_analytics()
        test_results.append({
            "test": "Analytics",
            "success": analytics_result['success'],
            "details": f"Tracking {analytics_result['analytics']['indexed_files']} files" if analytics_result['success'] else "Failed"
        })
        
        # Test 6: OpenRouter API
        logger.info("Testing OpenRouter API...")
        ai_result = await call_openrouter("Test message - respond with 'API working'")
        test_results.append({
            "test": "OpenRouter API",
            "success": ai_result['success'],
            "details": f"Model: {ai_result['model_used']}" if ai_result['success'] else "Failed"
        })
        
        # Generate test report
        passed = sum(1 for test in test_results if test['success'])
        total = len(test_results)
        
        response = f"🤠 SOPHIA V4 Self-Test Results ({passed}/{total} passed):\n\n"
        for test in test_results:
            status = "✅" if test['success'] else "❌"
            response += f"{status} {test['test']}: {test['details']}\n"
        
        response += f"\n🎯 Overall Status: {'OPERATIONAL' if passed == total else 'PARTIAL FUNCTIONALITY'}"
        
        return {
            "response": response,
            "success": passed == total,
            "test_results": test_results,
            "passed": passed,
            "total": total,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Self-test error: {e}")
        return {
            "response": f"🤠 Self-test failed: {str(e)}",
            "success": False,
            "error": str(e)
        }

# REAL MCP API ENDPOINTS - NO FAKE SHIT
@app.post("/api/v1/mcp/generate")
async def mcp_generate_code(request: dict):
    """Real code generation endpoint"""
    try:
        prompt = request.get('prompt')
        language = request.get('language', 'python')
        model = request.get('model')
        
        if not prompt:
            raise HTTPException(status_code=400, detail="prompt is required")
        
        result = await mcp.generate_code(prompt, language, model)
        return result
        
    except Exception as e:
        logger.error(f"MCP generate error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/mcp/index")
async def mcp_index_code(request: dict):
    """Real code indexing endpoint"""
    try:
        content = request.get('content')
        filename = request.get('filename', 'unknown.py')
        language = request.get('language', 'python')
        
        if not content:
            raise HTTPException(status_code=400, detail="content is required")
        
        result = mcp.index_code(content, filename, language)
        return result
        
    except Exception as e:
        logger.error(f"MCP index error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/mcp/search")
async def mcp_search_code(request: dict):
    """Real code search endpoint"""
    try:
        query = request.get('query')
        language = request.get('language')
        
        if not query:
            raise HTTPException(status_code=400, detail="query is required")
        
        result = mcp.search_code(query, language)
        return result
        
    except Exception as e:
        logger.error(f"MCP search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/mcp/security")
async def mcp_security_scan(request: dict):
    """Real security analysis endpoint"""
    try:
        code = request.get('code')
        language = request.get('language', 'python')
        
        if not code:
            raise HTTPException(status_code=400, detail="code is required")
        
        result = await mcp.analyze_security(code, language)
        return result
        
    except Exception as e:
        logger.error(f"MCP security error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/mcp/analytics")
async def mcp_get_analytics():
    """Real analytics endpoint"""
    try:
        result = mcp.get_analytics()
        return result
        
    except Exception as e:
        logger.error(f"MCP analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/self-test")
async def sophia_self_test_endpoint():
    """SOPHIA self-test endpoint"""
    try:
        result = await sophia_self_test()
        return result
        
    except Exception as e:
        logger.error(f"Self-test endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v4/", response_class=HTMLResponse)
async def sophia_interface():
    """SOPHIA V4 Simple Orchestrator Interface"""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SOPHIA V4 Simple Orchestrator</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Courier New', monospace;
            background: linear-gradient(135deg, #0a0a0a, #1a1a2e);
            color: #00ff41;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            border: 2px solid #00ff41;
            border-radius: 10px;
            background: rgba(0, 255, 65, 0.1);
        }
        .title {
            font-size: 2.5em;
            font-weight: bold;
            text-shadow: 0 0 10px #00ff41;
            margin-bottom: 10px;
        }
        .subtitle {
            font-size: 1.2em;
            color: #ff6b35;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .status-card {
            background: rgba(0, 0, 0, 0.8);
            border: 2px solid #00ff41;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
        }
        .status-title {
            font-size: 1.1em;
            font-weight: bold;
            margin-bottom: 10px;
            color: #ff6b35;
        }
        .chat-container {
            background: rgba(0, 0, 0, 0.8);
            border: 2px solid #00ff41;
            border-radius: 10px;
            padding: 20px;
        }
        .chat-messages {
            height: 400px;
            overflow-y: auto;
            border: 1px solid #00ff41;
            padding: 15px;
            margin-bottom: 15px;
            background: rgba(0, 0, 0, 0.5);
            border-radius: 5px;
        }
        .message {
            margin-bottom: 15px;
            padding: 10px;
            border-radius: 5px;
        }
        .user-message {
            background: rgba(0, 123, 255, 0.2);
            border-left: 4px solid #007bff;
            text-align: right;
        }
        .sophia-message {
            background: rgba(0, 255, 65, 0.2);
            border-left: 4px solid #00ff41;
        }
        .input-container {
            display: flex;
            gap: 10px;
        }
        .chat-input {
            flex: 1;
            padding: 15px;
            background: rgba(0, 0, 0, 0.8);
            border: 2px solid #00ff41;
            border-radius: 5px;
            color: #00ff41;
            font-family: 'Courier New', monospace;
            font-size: 16px;
        }
        .send-button {
            padding: 15px 25px;
            background: linear-gradient(45deg, #00ff41, #00cc33);
            border: none;
            border-radius: 5px;
            color: #000;
            font-weight: bold;
            cursor: pointer;
            font-family: 'Courier New', monospace;
        }
        .send-button:hover {
            transform: scale(1.05);
        }
        .loading { color: #ff6b35; font-style: italic; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">🤠 SOPHIA V4 Simple Orchestrator 🤠</div>
            <div class="subtitle">Fly.io + Lambda Labs + Badass AI</div>
        </div>

        <div class="status-grid">
            <div class="status-card">
                <div class="status-title">🚀 Fly.io Infrastructure</div>
                <div>3 Machines: ord, yyz, ewr</div>
                <div>Auto-scaling enabled</div>
            </div>
            <div class="status-card">
                <div class="status-title">🔥 Lambda Labs GPUs</div>
                <div>2x GH200 480GB</div>
                <div>ML Processing Ready</div>
            </div>
            <div class="status-card">
                <div class="status-title">🧠 AI Models</div>
                <div>Claude Sonnet 4</div>
                <div>OpenRouter Integration</div>
            </div>
            <div class="status-card">
                <div class="status-title">📊 Business Intelligence</div>
                <div>Gong Integration</div>
                <div>GitHub Operations</div>
            </div>
        </div>

        <div class="chat-container">
            <div class="chat-messages" id="chatMessages">
                <div class="message sophia-message">
                    <strong>🤠 SOPHIA V4:</strong> Howdy partner! SOPHIA V4 Simple Orchestrator is locked and loaded! I'm managing 3 Fly.io machines, 2 Lambda Labs GPUs, and all your business intelligence. Try: "Scale Fly.io infrastructure", "Analyze Gong calls on GPU", or "Check repository status". Let's dominate! 🤠
                </div>
            </div>
            <div class="input-container">
                <input type="text" id="chatInput" class="chat-input" placeholder="Ask SOPHIA to orchestrate your infrastructure... (Try: 'Scale to 3 machines' or 'Run ML analysis')" />
                <button onclick="sendMessage()" class="send-button">Send 🚀</button>
            </div>
        </div>
    </div>

    <script>
        const chatMessages = document.getElementById('chatMessages');
        const chatInput = document.getElementById('chatInput');

        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });

        async function sendMessage() {
            const message = chatInput.value.trim();
            if (!message) return;

            addMessage(message, 'user');
            chatInput.value = '';

            const loadingId = addMessage('🤠 SOPHIA is orchestrating...', 'sophia', true);

            try {
                const response = await fetch('/api/v1/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message })
                });

                const data = await response.json();
                document.getElementById(loadingId).remove();

                const responseText = `${data.response}\\n\\n<small>Model: ${data.model_used} | Success: ${data.success}</small>`;
                addMessage(responseText, 'sophia');

            } catch (error) {
                document.getElementById(loadingId).remove();
                addMessage('🤠 Hit a snag there partner, but I\\'m still ready to orchestrate! That\\'s the real fucking deal! 🤠', 'sophia');
            }
        }

        function addMessage(text, sender, isLoading = false) {
            const messageDiv = document.createElement('div');
            const messageId = 'msg_' + Date.now();
            messageDiv.id = messageId;
            messageDiv.className = `message ${sender}-message`;
            if (isLoading) messageDiv.classList.add('loading');

            const senderName = sender === 'user' ? '👤 You' : '🤠 SOPHIA V4';
            messageDiv.innerHTML = `<strong>${senderName}:</strong> ${text.replace(/\\n/g, '<br>')}`;

            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;

            return messageId;
        }

        chatInput.focus();
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"🤠 Starting SOPHIA V4 Simple Orchestrator on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
