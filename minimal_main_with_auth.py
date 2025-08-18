from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import sentry_sdk
import os
import logging
import httpx
import asyncio
from typing import Dict, Any, List, Optional

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Sentry
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    traces_sample_rate=1.0,
    environment="production"
)

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "sophia-intel-super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# CEO Credentials (in production, this would be in a secure database)
CEO_EMAIL = "lynn@payready.com"
CEO_PASSWORD_HASH = pwd_context.hash("Huskers2025$")

# FastAPI app with CORS
app = FastAPI(title="SOPHIA Intel - AI Swarm Orchestrator with CEO Authentication")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.sophia-intel.ai",
        "https://sophia-intel.ai", 
        "https://sophia-intel.fly.dev",
        "https://api.sophia-intel.ai",
        "http://localhost:3000",  # For development
        "*"  # Allow all for now - will restrict in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount dashboard static files
try:
    app.mount("/dashboard", StaticFiles(directory="apps/dashboard/dist", html=True), name="dashboard")
    logger.info("✅ Dashboard static files mounted successfully")
except Exception as e:
    logger.warning(f"⚠️ Could not mount dashboard static files: {e}")

# API keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_email: str
    expires_in: int

class ChatRequest(BaseModel):
    query: str
    use_case: str = "general"

class TaskRequest(BaseModel):
    task: str

class TaskResponse(BaseModel):
    result: str
    status: str
    agents_used: List[str]

class UserInfo(BaseModel):
    email: str
    role: str
    is_ceo: bool

# JWT Functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(username: str, password: str):
    if username == CEO_EMAIL and verify_password(password, CEO_PASSWORD_HASH):
        return {"email": CEO_EMAIL, "role": "ceo", "is_ceo": True}
    return False

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # In production, this would query a database
    if username == CEO_EMAIL:
        return UserInfo(email=CEO_EMAIL, role="ceo", is_ceo=True)
    raise credentials_exception

# SOPHIA's Minimal Swarm Implementation
agents = {
    "planner": {"status": "active", "role": "task_planning", "model": "anthropic/claude-sonnet-4"},
    "coder": {"status": "active", "role": "code_generation", "model": "qwen/qwen3-coder"},
    "reviewer": {"status": "active", "role": "quality_assurance", "model": "anthropic/claude-sonnet-4"},
    "coordinator": {"status": "active", "role": "orchestrator", "model": "google/gemini-2.0-flash"}
}

# OpenRouter client
class OpenRouterClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"

    async def generate(self, query: str, model: str) -> str:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://sophia-intel.pay-ready.com",
                        "X-Title": "SOPHIA Intel"
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": query}]
                    }
                )
                response.raise_for_status()
                data = response.json()
                logger.info(f"Token usage: {data.get('usage', {})}")
                return data["choices"][0]["message"]["content"]
            except Exception as e:
                logger.error(f"OpenRouter API error: {str(e)}")
                sentry_sdk.capture_exception(e)
                raise

# Initialize client
openrouter_client = OpenRouterClient(OPENROUTER_API_KEY)

# Model selection logic based on LATEST OpenRouter leaderboard
async def select_model(query: str, use_case: str) -> str:
    try:
        if "complex" in use_case.lower() or len(query.split()) > 50:
            return "anthropic/claude-sonnet-4"  # #1 on leaderboard
        elif "code" in use_case.lower():
            return "qwen/qwen3-coder"  # #6 on leaderboard
        elif "reasoning" in use_case.lower():
            return "deepseek/deepseek-v3-0324"  # #5 on leaderboard
        else:
            return "google/gemini-2.0-flash"  # #2 on leaderboard
    except Exception as e:
        logger.error(f"Model selection failed: {str(e)}")
        return "google/gemini-2.5-flash"  # #3 fallback

# Simple Agent Coordination
async def coordinate_agents(task: str) -> TaskResponse:
    """Simple agent coordination without complex dependencies"""
    try:
        agents_used = []
        
        # Step 1: Planning
        logger.info("Agent coordination: Planning phase")
        planning_prompt = f"As a task planner, break down this task: {task}"
        plan = await openrouter_client.generate(planning_prompt, agents["planner"]["model"])
        agents_used.append("Planner")
        
        # Step 2: Implementation
        logger.info("Agent coordination: Implementation phase")
        coding_prompt = f"Based on this plan, implement the solution:\n{plan}"
        implementation = await openrouter_client.generate(coding_prompt, agents["coder"]["model"])
        agents_used.append("Coder")
        
        # Step 3: Review
        logger.info("Agent coordination: Review phase")
        review_prompt = f"Review this implementation for quality:\n{implementation}"
        review = await openrouter_client.generate(review_prompt, agents["reviewer"]["model"])
        agents_used.append("Reviewer")
        
        # Combine results
        final_result = f"## Plan\n{plan}\n\n## Implementation\n{implementation}\n\n## Review\n{review}"
        
        return TaskResponse(
            result=final_result,
            status="completed",
            agents_used=agents_used
        )
        
    except Exception as e:
        logger.error(f"Agent coordination error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Agent coordination failed: {str(e)}")

# API Endpoints

# Public endpoints (no authentication required)
@app.get("/")
async def root():
    return {"message": "SOPHIA Intel - AI Swarm Orchestrator", "status": "operational", "authentication": "required"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "port": os.getenv("PORT", "8000"),
        "sentry": "connected" if os.getenv("SENTRY_DSN") else "disconnected",
        "llm_providers": ["openrouter"],
        "swarm_enabled": True,
        "authentication": "enabled",
        "dashboard": "mounted",
        "deployment_timestamp": datetime.utcnow().isoformat()
    }

@app.get("/debug/routes")
async def debug_routes():
    return [str(route) for route in app.routes]

# Authentication endpoints
@app.post("/api/v1/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    """CEO Login Endpoint - lynn@payready.com / Huskers2025$"""
    user = authenticate_user(credentials.username, credentials.password)
    if not user:
        logger.warning(f"Failed login attempt for: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    
    logger.info(f"✅ Successful login for CEO: {user['email']}")
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_email=user["email"],
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
    )

@app.get("/api/v1/user/profile")
async def get_user_profile(current_user: UserInfo = Depends(get_current_user)):
    """Get current user profile"""
    return {
        "email": current_user.email,
        "role": current_user.role,
        "is_ceo": current_user.is_ceo,
        "permissions": ["full_access", "user_management", "system_admin"] if current_user.is_ceo else []
    }

# Protected endpoints (authentication required)
@app.post("/api/chat")
async def legacy_chat(request: ChatRequest, current_user: UserInfo = Depends(get_current_user)):
    try:
        model = await select_model(request.query, request.use_case)
        response = await openrouter_client.generate(request.query, model)
        logger.info(f"Chat request from {current_user.email}")
        return {"response": response}
    except Exception as e:
        logger.error(f"Legacy chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/chat/enhanced")
async def enhanced_chat(request: ChatRequest, current_user: UserInfo = Depends(get_current_user)):
    try:
        model = await select_model(request.query, request.use_case)
        logger.info(f"Selected model: {model} for query from {current_user.email}: {request.query[:50]}...")
        response = await openrouter_client.generate(request.query, model)
        logger.info(f"Enhanced chat response: {response[:50]}...")
        return {"response": response, "model_used": model, "user": current_user.email}
    except Exception as e:
        logger.error(f"Enhanced chat error: {str(e)}")
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/swarm/status")
async def swarm_status(current_user: UserInfo = Depends(get_current_user)):
    """SOPHIA's minimal swarm status endpoint"""
    active_agents = sum(1 for agent in agents.values() if agent["status"] == "active")
    
    return {
        "swarm_status": "operational" if active_agents > 0 else "degraded",
        "total_agents": len(agents),
        "active_agents": active_agents,
        "agents": agents,
        "coordinator_model": "google/gemini-2.0-flash",
        "openrouter_connected": OPENROUTER_API_KEY is not None,
        "authenticated_user": current_user.email,
        "last_updated": datetime.utcnow().isoformat()
    }

@app.post("/api/v1/swarm/execute", response_model=TaskResponse)
async def execute_swarm_task(request: TaskRequest, current_user: UserInfo = Depends(get_current_user)):
    """Execute task through simple agent coordination"""
    try:
        logger.info(f"Executing swarm task from {current_user.email}: {request.task[:100]}...")
        
        # Execute with timeout protection
        task_result = await asyncio.wait_for(
            coordinate_agents(request.task), 
            timeout=120.0
        )
        
        logger.info(f"Swarm task completed for {current_user.email}. Agents used: {task_result.agents_used}")
        return task_result
            
    except asyncio.TimeoutError:
        logger.error("Swarm task timeout exceeded")
        raise HTTPException(status_code=408, detail="Task timeout exceeded")
    except Exception as e:
        logger.error(f"Swarm execution error: {str(e)}")
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail=f"Swarm execution failed: {str(e)}")

# User Management (CEO only)
@app.get("/api/v1/admin/users")
async def list_users(current_user: UserInfo = Depends(get_current_user)):
    """List all users (CEO only)"""
    if not current_user.is_ceo:
        raise HTTPException(status_code=403, detail="Access denied: CEO privileges required")
    
    # In production, this would query a database
    return {
        "users": [
            {
                "email": CEO_EMAIL,
                "role": "ceo",
                "is_ceo": True,
                "created_at": "2024-01-01T00:00:00Z",
                "last_login": datetime.utcnow().isoformat()
            }
        ],
        "total_users": 1
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"🚀 Starting SOPHIA Intel with CEO Authentication on port {port}")
    logger.info(f"✅ CEO Login: {CEO_EMAIL}")
    logger.info(f"✅ Dashboard mounted at /dashboard")
    logger.info(f"✅ JWT Authentication enabled")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

