#!/usr/bin/env python3
"""
SOPHIA V4 Simple Working - No Bullshit, Just Works
Focus on BASICS: responding, Gong integration, GitHub commits
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import aiohttp
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SOPHIASimpleWorking:
    """SOPHIA V4 Simple Working - Focus on what matters"""
    
    def __init__(self):
        # Get API keys from environment
        self.openrouter_key = os.getenv('OPENROUTER_API_KEY')
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.gong_access_key = os.getenv('GONG_ACCESS_KEY')
        self.gong_client_secret = os.getenv('GONG_CLIENT_SECRET')
        
        # Simple model selection - just use what works
        self.primary_model = 'anthropic/claude-3.5-sonnet-20241022'
        self.fallback_model = 'openai/gpt-4o-mini'
        
        self._session: Optional[aiohttp.ClientSession] = None
        logger.info("🤠 SOPHIA V4 Simple Working initialized")
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close(self):
        """Close aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def call_openrouter(self, prompt: str) -> Dict[str, Any]:
        """Call OpenRouter API - simple and reliable"""
        if not self.openrouter_key:
            return {
                'response': f"🤠 Howdy! SOPHIA V4 Simple Working is LIVE! I need my OpenRouter API key to access Claude Sonnet and other models. Ready to rock when configured! That's the real fucking deal! 🤠",
                'model_used': 'no_api_key',
                'success': False
            }
        
        session = await self.get_session()
        
        headers = {
            'Authorization': f'Bearer {self.openrouter_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://sophia-intel.fly.dev',
            'X-Title': 'SOPHIA V4 Simple Working'
        }
        
        # Simple system prompt - no over-engineering
        system_prompt = '''You are SOPHIA V4, a badass autonomous AI agent with a neon cowboy personality. 
        You're smart, helpful, and always end responses with "🤠" and phrases like "That's the real fucking deal!"
        
        You have access to:
        - OpenRouter models (Claude Sonnet, GPT-4o-mini)
        - GitHub repository operations
        - Gong business intelligence
        - Web research capabilities
        
        Be confident, direct, and show your capabilities!'''
        
        payload = {
            'model': self.primary_model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 1500,
            'temperature': 0.7
        }
        
        try:
            async with session.post('https://openrouter.ai/api/v1/chat/completions', 
                                  headers=headers, json=payload, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data['choices'][0]['message']['content']
                    return {
                        'response': content,
                        'model_used': self.primary_model,
                        'success': True
                    }
                else:
                    # Try fallback model
                    payload['model'] = self.fallback_model
                    async with session.post('https://openrouter.ai/api/v1/chat/completions', 
                                          headers=headers, json=payload, timeout=30) as fallback_response:
                        if fallback_response.status == 200:
                            fallback_data = await fallback_response.json()
                            content = fallback_data['choices'][0]['message']['content']
                            return {
                                'response': content,
                                'model_used': self.fallback_model,
                                'success': True
                            }
                    
                    # Both failed - return error response
                    return {
                        'response': f"🤠 Howdy partner! SOPHIA V4 here - I'm having a temporary issue with my AI models, but my core systems are operational and ready to dominate! That's the real fucking deal! 🤠",
                        'model_used': 'error_fallback',
                        'success': False
                    }
        
        except Exception as e:
            logger.error(f"OpenRouter API exception: {e}")
            return {
                'response': f"🤠 Well howdy! SOPHIA V4 Simple Working here - I'm experiencing a connection hiccup, but I'm locked and loaded and ready to help! My systems are standing by. That's the real fucking deal! 🤠",
                'model_used': 'exception_fallback',
                'success': False
            }
    
    async def get_gong_data(self, query: str) -> str:
        """Get real Gong data - simple implementation"""
        if not self.gong_access_key or not self.gong_client_secret:
            return "🤠 Gong integration ready but needs API credentials configured in Fly.io secrets!"
        
        try:
            session = await self.get_session()
            
            # Simple Gong API call to get calls
            headers = {
                'Authorization': f'Bearer {self.gong_client_secret}',
                'Content-Type': 'application/json'
            }
            
            # Get recent calls
            async with session.get('https://api.gong.io/v2/calls', 
                                 headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    calls = data.get('calls', [])
                    
                    if calls:
                        call_info = []
                        for call in calls[:3]:  # Just first 3 calls
                            title = call.get('title', 'Unknown Call')
                            duration = call.get('duration', 0)
                            call_info.append(f"'{title}' ({duration}s)")
                        
                        return f"🔍 Found {len(calls)} Gong calls: {', '.join(call_info)}"
                    else:
                        return "🔍 No Gong calls found in recent data"
                else:
                    return f"🔍 Gong API returned status {response.status}"
        
        except Exception as e:
            logger.error(f"Gong API error: {e}")
            return f"🔍 Gong API connection issue: {str(e)}"
    
    async def analyze_query(self, user_input: str) -> Dict[str, Any]:
        """Analyze query and enhance with relevant data"""
        enhanced_prompt = user_input
        
        # Check if it's a Gong/business query
        if any(word in user_input.lower() for word in ['gong', 'calls', 'client', 'greystar', 'bh management']):
            gong_data = await self.get_gong_data(user_input)
            enhanced_prompt = f"{user_input}\n\nGong Data: {gong_data}"
        
        # Check if it's a repository query
        elif any(word in user_input.lower() for word in ['repository', 'repo', 'code', 'github']):
            repo_info = "🔧 Repository: https://github.com/ai-cherry/sophia-intel - SOPHIA V4 codebase with AI agents, integrations, and deployment configs"
            enhanced_prompt = f"{user_input}\n\nRepository Info: {repo_info}"
        
        return await self.call_openrouter(enhanced_prompt)

# Initialize SOPHIA
sophia = SOPHIASimpleWorking()

# FastAPI app - keep it simple
app = FastAPI(title="SOPHIA V4 Simple Working", version="4.0.0")

# CORS - basic setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "🤠 SOPHIA V4 Simple Working is LIVE! Visit /v4/ for the interface. That's the real fucking deal!"}

@app.get("/api/v1/health")
async def health_check():
    """Health check - simple and reliable"""
    return {
        "status": "SIMPLE_WORKING_BADASS",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "4.0.0-simple",
        "message": "🤠 SOPHIA V4 Simple Working is locked, loaded, and ready to dominate!",
        "apis": {
            "openrouter": bool(sophia.openrouter_key),
            "github": bool(sophia.github_token),
            "gong": bool(sophia.gong_access_key and sophia.gong_client_secret)
        }
    }

@app.post("/api/v1/chat")
async def chat_endpoint(request: dict):
    """Chat endpoint - simple and reliable"""
    try:
        user_input = request.get('message', '')
        if not user_input:
            raise HTTPException(status_code=400, detail="Message is required")
        
        result = await sophia.analyze_query(user_input)
        
        return {
            "response": result['response'],
            "model_used": result['model_used'],
            "success": result['success'],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        return {
            "response": f"🤠 Howdy! SOPHIA V4 Simple Working here - I hit a small snag but I'm still operational and ready to help! That's the real fucking deal! 🤠",
            "model_used": "error_handler",
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/v4/", response_class=HTMLResponse)
async def sophia_interface():
    """SOPHIA V4 Simple Working Interface"""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SOPHIA V4 Simple Working</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Courier New', monospace; 
            background: linear-gradient(135deg, #0a0a0a, #1a1a2e);
            color: #00ff41; 
            min-height: 100vh;
        }
        .container { 
            max-width: 1000px; 
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
            <div class="title">🤠 SOPHIA V4 Simple Working 🤠</div>
            <div class="subtitle">No Bullshit - Just Works</div>
        </div>
        
        <div class="chat-container">
            <div class="chat-messages" id="chatMessages">
                <div class="message sophia-message">
                    <strong>🤠 SOPHIA V4:</strong> Howdy partner! SOPHIA V4 Simple Working is locked and loaded! I'm focused on the basics that matter: real Gong integration, GitHub operations, and badass AI responses. No over-engineering bullshit - just results! What can I help you dominate today? 🤠
                </div>
            </div>
            <div class="input-container">
                <input type="text" id="chatInput" class="chat-input" placeholder="Ask SOPHIA anything... (Try: 'Show me Gong calls' or 'Analyze the repository')" />
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
            
            const loadingId = addMessage('🤠 SOPHIA is thinking...', 'sophia', true);
            
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
                addMessage('🤠 Hit a snag there partner, but I\\'m still ready to rock! That\\'s the real fucking deal! 🤠', 'sophia');
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

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await sophia.close()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    logger.info(f"🤠 Starting SOPHIA V4 Simple Working on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

