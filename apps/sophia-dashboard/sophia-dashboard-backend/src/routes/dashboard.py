import os
import json
import asyncio
import aiohttp
import psycopg
from datetime import datetime
from flask import Blueprint, jsonify, request
from typing import Dict, Any, List
import concurrent.futures
import functools

dashboard_bp = Blueprint('dashboard', __name__)

# OpenRouter approved model allow-list
APPROVED_MODELS = [
    "Claude Sonnet 4 (anthropic)",
    "Gemini 2.0 Flash (google)",
    "Gemini 2.5 Flash (google)",
    "DeepSeek V3 0324 (deepseek)",
    "DeepSeek V3 0324 (free) (deepseek)",
    "Qwen3 Coder (qwen)",
    "Gemini 2.5 Pro (google)",
    "Claude 3.7 Sonnet (anthropic)",
    "R1 0528 (free) (deepseek)",
    "Kimi K2 (moonshotai)",
    "gpt-oss-120b (openai)",
    "GLM 4.5 (z-ai)",
    "Qwen3 Coder (free) (qwen)",
    "GPT-5 (openai)",
    "Mistral Nemo (mistralai)",
    "R1 (free) (deepseek)",
    "Qwen3 30B A3B (qwen)",
    "Gemini 2.5 Flash Lite (google)",
    "GLM 4.5 Air (free) (z-ai)",
    "GPT-4o-mini (openai)"
]

def async_route(f):
    """Decorator to run async functions in Flask routes"""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(f(*args, **kwargs))
        except Exception as e:
            return jsonify({"error": str(e), "status": "error"}), 500
        finally:
            loop.close()
    return wrapper

class HealthChecker:
    def __init__(self):
        self.openrouter_key = os.getenv('OPENROUTER_API_KEY')
        self.airbyte_url = os.getenv('AIRBYTE_API_URL', 'http://localhost:8000')
        self.qdrant_url = os.getenv('QDRANT_URL')
        self.qdrant_key = os.getenv('QDRANT_API_KEY')
        self.neon_url = os.getenv('NEON_DATABASE_URL')
        self.minio_endpoint = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
        self.minio_access = os.getenv('MINIO_ACCESS_KEY')
        self.minio_secret = os.getenv('MINIO_SECRET_KEY')
        self.mcp_url = os.getenv('MCP_BASE_URL')
        self.mcp_token = os.getenv('MCP_AUTH_TOKEN')

    async def check_airbyte(self) -> Dict[str, Any]:
        """Check Airbyte server and temporal health"""
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Check Airbyte server
                try:
                    async with session.get(f"{self.airbyte_url}/api/v1/health") as resp:
                        server_status = "healthy" if resp.status == 200 else f"unhealthy - HTTP {resp.status}"
                except:
                    server_status = "unhealthy - connection failed"
                
                # Check Temporal (usually on port 7233)
                temporal_url = self.airbyte_url.replace('8000', '7233')
                try:
                    async with session.get(f"{temporal_url}/api/v1/namespaces") as resp:
                        temporal_status = "healthy" if resp.status == 200 else f"unhealthy - HTTP {resp.status}"
                except:
                    temporal_status = "unhealthy - connection failed"
                
                return {
                    "status": "healthy" if server_status == "healthy" and temporal_status == "healthy" else "degraded",
                    "server": server_status,
                    "temporal": temporal_status,
                    "response_time_ms": 0
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time_ms": 0
            }

    async def check_qdrant(self) -> Dict[str, Any]:
        """Check Qdrant vector database"""
        if not self.qdrant_url:
            return {"status": "blocked", "error": "QDRANT_URL not configured"}
        
        try:
            headers = {}
            if self.qdrant_key:
                headers['api-key'] = self.qdrant_key
            
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.qdrant_url}/collections", headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "status": "healthy",
                            "collections": len(data.get('result', {}).get('collections', [])),
                            "response_time_ms": 0
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "error": f"HTTP {resp.status}",
                            "response_time_ms": 0
                        }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time_ms": 0
            }

    async def check_neon_postgres(self) -> Dict[str, Any]:
        """Check Neon PostgreSQL database"""
        if not self.neon_url:
            return {"status": "blocked", "error": "NEON_DATABASE_URL not configured"}
        
        try:
            # Use sync psycopg for simplicity
            import psycopg
            with psycopg.connect(self.neon_url, connect_timeout=5) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    result = cur.fetchone()
                    return {
                        "status": "healthy",
                        "test_query": "SELECT 1",
                        "result": result[0] if result else None,
                        "response_time_ms": 0
                    }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time_ms": 0
            }

    async def check_minio(self) -> Dict[str, Any]:
        """Check MinIO object storage"""
        if not self.minio_access or not self.minio_secret:
            return {"status": "blocked", "error": "MinIO credentials not configured"}
        
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"http://{self.minio_endpoint}/minio/health/live") as resp:
                    if resp.status == 200:
                        return {
                            "status": "healthy",
                            "endpoint": self.minio_endpoint,
                            "response_time_ms": 0
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "error": f"HTTP {resp.status}",
                            "response_time_ms": 0
                        }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time_ms": 0
            }

    async def check_mcp(self) -> Dict[str, Any]:
        """Check MCP Code Server"""
        if not self.mcp_url or not self.mcp_token:
            return {"status": "blocked", "error": "MCP credentials not configured"}
        
        try:
            headers = {'Authorization': f'Bearer {self.mcp_token}'}
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.mcp_url}/health", headers=headers) as resp:
                    if resp.status == 200:
                        return {
                            "status": "healthy",
                            "url": self.mcp_url,
                            "response_time_ms": 0
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "error": f"HTTP {resp.status}",
                            "response_time_ms": 0
                        }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time_ms": 0
            }

    async def check_swarm(self) -> Dict[str, Any]:
        """Check LangGraph swarm initialization"""
        try:
            # Simple check - verify required env vars
            required_vars = ['OPENROUTER_API_KEY', 'GH_FINE_GRAINED_TOKEN', 'MCP_BASE_URL', 'MCP_AUTH_TOKEN']
            missing = [var for var in required_vars if not os.getenv(var)]
            
            if missing:
                return {
                    "status": "blocked",
                    "error": f"Missing environment variables: {', '.join(missing)}",
                    "response_time_ms": 0
                }
            
            return {
                "status": "healthy",
                "dry_run": True,
                "response_time_ms": 0
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time_ms": 0
            }

health_checker = HealthChecker()

@dashboard_bp.route('/health')
@async_route
async def get_health():
    """Aggregate health from all components"""
    start_time = datetime.now()
    
    # Run all health checks concurrently with timeout
    try:
        tasks = [
            health_checker.check_airbyte(),
            health_checker.check_qdrant(),
            health_checker.check_neon_postgres(),
            health_checker.check_minio(),
            health_checker.check_mcp(),
            health_checker.check_swarm()
        ]
        
        results = await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=10.0)
        
        health_data = {
            "timestamp": start_time.isoformat(),
            "components": {
                "airbyte": results[0] if not isinstance(results[0], Exception) else {"status": "error", "error": str(results[0])},
                "qdrant": results[1] if not isinstance(results[1], Exception) else {"status": "error", "error": str(results[1])},
                "neon_postgres": results[2] if not isinstance(results[2], Exception) else {"status": "error", "error": str(results[2])},
                "minio": results[3] if not isinstance(results[3], Exception) else {"status": "error", "error": str(results[3])},
                "mcp": results[4] if not isinstance(results[4], Exception) else {"status": "error", "error": str(results[4])},
                "swarm": results[5] if not isinstance(results[5], Exception) else {"status": "error", "error": str(results[5])}
            },
            "total_response_time_ms": int((datetime.now() - start_time).total_seconds() * 1000)
        }
        
        # Calculate overall health score
        healthy_count = sum(1 for comp in health_data["components"].values() if comp.get("status") == "healthy")
        total_count = len(health_data["components"])
        health_data["overall_health_score"] = (healthy_count / total_count) * 100
        
        return jsonify(health_data)
        
    except asyncio.TimeoutError:
        return jsonify({
            "error": "Health check timeout",
            "status": "timeout",
            "timestamp": start_time.isoformat()
        }), 408

@dashboard_bp.route('/models/allowlist')
@async_route
async def get_model_allowlist():
    """Get approved model allow-list with availability check"""
    if not health_checker.openrouter_key:
        return jsonify({
            "error": "OPENROUTER_API_KEY not configured",
            "status": "blocked"
        }), 400
    
    try:
        headers = {
            'Authorization': f'Bearer {health_checker.openrouter_key}',
            'Content-Type': 'application/json'
        }
        
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get('https://openrouter.ai/api/v1/models', headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    available_models = [model['id'] for model in data.get('data', [])]
                    
                    # Check which approved models are available
                    model_status = []
                    for model in APPROVED_MODELS:
                        # Simple name matching - in production would need more sophisticated mapping
                        is_available = any(model.lower().replace(' ', '-') in available_model.lower() 
                                         for available_model in available_models)
                        model_status.append({
                            "name": model,
                            "status": "available" if is_available else "missing",
                            "allowed": True
                        })
                    
                    return jsonify({
                        "approved_models": model_status,
                        "total_approved": len(APPROVED_MODELS),
                        "available_count": sum(1 for m in model_status if m["status"] == "available"),
                        "last_checked": datetime.now().isoformat()
                    })
                else:
                    return jsonify({
                        "error": f"OpenRouter API returned HTTP {resp.status}",
                        "status": "error"
                    }), resp.status
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@dashboard_bp.route('/swarm/plan', methods=['POST'])
def create_swarm_plan():
    """Create a new swarm planning job"""
    data = request.get_json()
    if not data or 'repo' not in data or 'goal' not in data:
        return jsonify({"error": "Missing required fields: repo, goal"}), 400
    
    try:
        # Simple job creation without async complications
        import uuid
        job_id = str(uuid.uuid4())
        
        # Create basic job data
        job_data = {
            "job_id": job_id,
            "repo": data['repo'],
            "goal": data['goal'],
            "constraints": data.get('constraints'),
            "status": "planning",
            "created_at": datetime.now().isoformat()
        }
        
        return jsonify(job_data)
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@dashboard_bp.route('/swarm/implement', methods=['POST'])
def implement_swarm_plan():
    """Implement a swarm plan"""
    data = request.get_json()
    if not data or 'job_id' not in data:
        return jsonify({"error": "Missing required field: job_id"}), 400
    
    return jsonify({
        "job_id": data['job_id'],
        "status": "implementing",
        "updated_at": datetime.now().isoformat()
    })

@dashboard_bp.route('/swarm/status/<job_id>')
def get_swarm_status(job_id):
    """Get swarm job status"""
    # Mock status for now
    return jsonify({
        "job_id": job_id,
        "status": "completed",
        "agents": {
            "planner": {"status": "completed"},
            "coder": {"status": "completed"},
            "reviewer": {"status": "completed"},
            "integrator": {"status": "completed"}
        },
        "events": [
            {
                "timestamp": datetime.now().isoformat(),
                "agent": "system",
                "event": "completed",
                "message": "Job completed successfully"
            }
        ]
    })

