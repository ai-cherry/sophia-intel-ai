#!/usr/bin/env python3
"""
SOPHIA Intel Production Backend - Autonomous AI Orchestrator
Complete production-ready backend with real system access and autonomous capabilities.
All secrets managed via Pulumi ESC + GitHub Organization Secrets.
"""

import os
import sys
import json
import subprocess
import httpx
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Production FastAPI app
app = FastAPI(
    title="SOPHIA Intel Production Backend",
    description="Autonomous AI Orchestrator with Real System Access",
    version="1.0.0"
)

# CORS middleware for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Secure environment loading from Pulumi ESC + GitHub Secrets
def load_production_secrets():
    """Load secrets from environment variables (Pulumi ESC + GitHub Secrets)"""
    return {
        'OPENROUTER_API_KEY': os.getenv('OPENROUTER_API_KEY'),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY'),
        'GITHUB_TOKEN': os.getenv('GITHUB_TOKEN'),
        'LAMBDA_LABS_API_KEY': os.getenv('LAMBDA_LABS_API_KEY'),
        'PULUMI_ACCESS_TOKEN': os.getenv('PULUMI_ACCESS_TOKEN'),
    }

# Load production secrets
env_vars = load_production_secrets()

# Production AI Agent and Swarm Management
AGENT_REGISTRY = {}
SWARM_REGISTRY = {}

# Pydantic Models
class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    timestamp: str
    model_used: str
    processing_time: float

class SystemCommand(BaseModel):
    command: str
    working_dir: Optional[str] = "/tmp"
    timeout: Optional[int] = 30

class FileOperation(BaseModel):
    file_path: str
    content: Optional[str] = None
    operation: str  # read, write, append

class CodeModification(BaseModel):
    file_path: str
    old_content: str
    new_content: str
    commit_message: Optional[str] = None

class AgentConfig(BaseModel):
    name: str
    type: str
    capabilities: List[str]
    model: Optional[str] = "gpt-4"

class WebScrapeRequest(BaseModel):
    url: str
    extract_type: str = "text"  # text, links, images

# Health endpoint
@app.get("/health")
async def health_check():
    """Production health check with comprehensive system status"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "capabilities": {
            "autonomous_code_modification": True,
            "system_command_execution": True,
            "ai_agent_orchestration": True,
            "web_research_scraping": True,
            "github_integration": True,
            "production_monitoring": True
        },
        "environment": {
            "secrets_loaded": bool(env_vars.get('OPENROUTER_API_KEY')),
            "github_integration": bool(env_vars.get('GITHUB_TOKEN')),
            "ai_providers_available": len([k for k, v in env_vars.items() if v and 'API_KEY' in k])
        }
    }

# Chat endpoint with LLM integration
@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_sophia(request: ChatRequest):
    """Chat with SOPHIA using production LLM providers"""
    start_time = datetime.now()
    
    try:
        # Use OpenRouter as primary provider
        if env_vars.get('OPENROUTER_API_KEY'):
            response = await call_openrouter_api(request.message, request.context)
            model_used = "openrouter/gpt-4"
        elif env_vars.get('OPENAI_API_KEY'):
            response = await call_openai_api(request.message, request.context)
            model_used = "openai/gpt-4"
        else:
            raise HTTPException(status_code=500, detail="No AI providers available")
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return ChatResponse(
            response=response,
            timestamp=datetime.now().isoformat(),
            model_used=model_used,
            processing_time=processing_time
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

# System command execution
@app.post("/api/system/execute")
async def execute_system_command(command: SystemCommand):
    """Execute system commands with security controls"""
    try:
        # Security: Restrict dangerous commands
        dangerous_commands = ['rm -rf', 'sudo rm', 'format', 'mkfs', 'dd if=']
        if any(dangerous in command.command for dangerous in dangerous_commands):
            raise HTTPException(status_code=403, detail="Dangerous command blocked")
        
        result = subprocess.run(
            command.command,
            shell=True,
            cwd=command.working_dir,
            capture_output=True,
            text=True,
            timeout=command.timeout
        )
        
        return {
            "command": command.command,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timestamp": datetime.now().isoformat()
        }
    
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Command timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")

# File operations
@app.post("/api/file/operation")
async def file_operation(operation: FileOperation):
    """Perform file operations with security controls"""
    try:
        file_path = Path(operation.file_path)
        
        # Security: Restrict to safe directories
        safe_dirs = ['/tmp', '/home/ubuntu', '/app']
        if not any(str(file_path).startswith(safe_dir) for safe_dir in safe_dirs):
            raise HTTPException(status_code=403, detail="File path not allowed")
        
        if operation.operation == "read":
            if file_path.exists():
                content = file_path.read_text()
                return {"content": content, "size": len(content)}
            else:
                raise HTTPException(status_code=404, detail="File not found")
        
        elif operation.operation == "write":
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(operation.content)
            return {"message": "File written successfully", "path": str(file_path)}
        
        elif operation.operation == "append":
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'a') as f:
                f.write(operation.content)
            return {"message": "Content appended successfully", "path": str(file_path)}
        
        else:
            raise HTTPException(status_code=400, detail="Invalid operation")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File operation error: {str(e)}")

# Code modification with Git integration
@app.post("/api/code/modify")
async def modify_code(modification: CodeModification):
    """Modify code files with Git integration"""
    try:
        file_path = Path(modification.file_path)
        
        # Read current content
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        current_content = file_path.read_text()
        
        # Verify old content matches
        if modification.old_content not in current_content:
            raise HTTPException(status_code=400, detail="Old content not found in file")
        
        # Perform replacement
        new_content = current_content.replace(modification.old_content, modification.new_content)
        file_path.write_text(new_content)
        
        # Git commit if requested
        if modification.commit_message:
            subprocess.run(['git', 'add', str(file_path)], cwd=file_path.parent)
            subprocess.run(['git', 'commit', '-m', modification.commit_message], cwd=file_path.parent)
        
        return {
            "message": "Code modified successfully",
            "file_path": str(file_path),
            "committed": bool(modification.commit_message)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Code modification error: {str(e)}")

# AI Agent management
@app.post("/api/agent/create")
async def create_agent(config: AgentConfig):
    """Create and register AI agent"""
    try:
        agent_id = f"agent_{len(AGENT_REGISTRY) + 1}"
        AGENT_REGISTRY[agent_id] = {
            "id": agent_id,
            "name": config.name,
            "type": config.type,
            "capabilities": config.capabilities,
            "model": config.model,
            "created_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        return {"agent_id": agent_id, "status": "created", "config": AGENT_REGISTRY[agent_id]}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent creation error: {str(e)}")

@app.get("/api/agents")
async def list_agents():
    """List all registered agents"""
    return {"agents": AGENT_REGISTRY, "count": len(AGENT_REGISTRY)}

# Web scraping
@app.post("/api/web/scrape")
async def scrape_web_content(request: WebScrapeRequest):
    """Scrape web content for research"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(request.url, timeout=30)
            response.raise_for_status()
            
            if request.extract_type == "text":
                # Basic text extraction (would use BeautifulSoup in production)
                content = response.text
                return {"url": request.url, "content": content[:5000], "type": "text"}
            
            elif request.extract_type == "links":
                # Extract links (simplified)
                import re
                links = re.findall(r'href=[\'"]?([^\'" >]+)', response.text)
                return {"url": request.url, "links": links[:50], "type": "links"}
            
            else:
                return {"url": request.url, "raw_content": response.text[:1000], "type": "raw"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Web scraping error: {str(e)}")

# GitHub integration
@app.post("/api/github/operation")
async def github_operation(operation: dict):
    """Perform GitHub operations"""
    if not env_vars.get('GITHUB_TOKEN'):
        raise HTTPException(status_code=401, detail="GitHub token not available")
    
    try:
        headers = {"Authorization": f"token {env_vars['GITHUB_TOKEN']}"}
        
        async with httpx.AsyncClient() as client:
            if operation.get('type') == 'list_repos':
                response = await client.get("https://api.github.com/user/repos", headers=headers)
                return response.json()
            
            elif operation.get('type') == 'get_file':
                repo = operation.get('repo')
                file_path = operation.get('file_path')
                url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
                response = await client.get(url, headers=headers)
                return response.json()
            
            else:
                raise HTTPException(status_code=400, detail="Invalid GitHub operation")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GitHub operation error: {str(e)}")

# Helper functions for LLM APIs
async def call_openrouter_api(message: str, context: Optional[str] = None):
    """Call OpenRouter API"""
    if not env_vars.get('OPENROUTER_API_KEY'):
        raise Exception("OpenRouter API key not available")
    
    headers = {
        "Authorization": f"Bearer {env_vars['OPENROUTER_API_KEY']}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "openai/gpt-4",
        "messages": [
            {"role": "system", "content": "You are SOPHIA, an autonomous AI orchestrator with real system access."},
            {"role": "user", "content": f"{context}\n\n{message}" if context else message}
        ]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post("https://openrouter.ai/api/v1/chat/completions", 
                                   headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']

async def call_openai_api(message: str, context: Optional[str] = None):
    """Call OpenAI API"""
    if not env_vars.get('OPENAI_API_KEY'):
        raise Exception("OpenAI API key not available")
    
    headers = {
        "Authorization": f"Bearer {env_vars['OPENAI_API_KEY']}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "You are SOPHIA, an autonomous AI orchestrator with real system access."},
            {"role": "user", "content": f"{context}\n\n{message}" if context else message}
        ]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post("https://api.openai.com/v1/chat/completions", 
                                   headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)

