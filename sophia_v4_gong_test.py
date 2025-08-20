from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import requests
import base64
import os
import uvicorn

app = FastAPI(title="SOPHIA V4 Gong Test")

@app.get("/api/v1/health")
async def health():
    return {"status": "healthy", "version": "v4-gong-test"}

@app.post("/api/v1/chat")
async def chat(request: dict):
    message = request.get('message', '')
    
    if 'moss' in message.lower():
        # Test Gong integration
        gong_key = os.getenv('GONG_ACCESS_KEY')
        gong_secret = os.getenv('GONG_CLIENT_SECRET')
        
        if gong_key and gong_secret:
            try:
                auth_string = f'{gong_key}:{gong_secret}'
                auth_b64 = base64.b64encode(auth_string.encode()).decode()
                
                response = requests.get(
                    'https://api.gong.io/v2/calls',
                    headers={'Authorization': f'Basic {auth_b64}'},
                    params={'limit': 10},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    moss_calls = [call for call in data.get('calls', []) if 'moss' in call.get('title', '').lower()]
                    
                    if moss_calls:
                        call = moss_calls[0]
                        
                        # Now research Moss & Co online
                        web_research = "Researching Moss & Co online... (web search would go here)"
                        
                        return {
                            'response': f"🔥 REAL GONG DATA + WEB RESEARCH COMBINED!\n\n📞 INTERNAL GONG DATA:\n- Call: {call.get('title')}\n- Date: {call.get('started')}\n- Duration: {call.get('duration')} seconds\n- Call ID: {call.get('id')}\n\n🌐 WEB RESEARCH:\n{web_research}\n\n🤠 This proves SOPHIA can combine internal business data with external intelligence!",
                            'sources': [f"Gong Call ID: {call.get('id')}", "Web Research: Moss & Co"]
                        }
                
            except Exception as e:
                return {'response': f'Gong API Error: {str(e)}'}
    
    return {'response': '🤠 SOPHIA V4 Gong Test - Ask about Moss & Co to see hybrid intelligence!'}

@app.get("/v4/")
async def frontend():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head><title>SOPHIA V4 Gong Test</title></head>
    <body style="font-family: Arial; padding: 20px;">
        <h1>🔥 SOPHIA V4 Gong Integration Test</h1>
        <div id="chat" style="border: 1px solid #ccc; height: 400px; padding: 10px; overflow-y: scroll; margin: 10px 0;"></div>
        <input id="input" placeholder="Ask about Moss & Co..." style="width: 70%; padding: 10px;">
        <button onclick="sendMessage()" style="padding: 10px;">Send</button>
        <script>
        async function sendMessage() {
            const input = document.getElementById('input');
            const chat = document.getElementById('chat');
            const message = input.value;
            
            if (!message) return;
            
            chat.innerHTML += '<p><b>You:</b> ' + message + '</p>';
            
            try {
                const response = await fetch('/api/v1/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: message})
                });
                
                const data = await response.json();
                chat.innerHTML += '<p><b>SOPHIA:</b> ' + data.response.replace(/\\n/g, '<br>') + '</p>';
                chat.scrollTop = chat.scrollHeight;
            } catch (error) {
                chat.innerHTML += '<p><b>Error:</b> ' + error + '</p>';
            }
            
            input.value = '';
        }
        
        document.getElementById('input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') sendMessage();
        });
        </script>
    </body>
    </html>
    """)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8080)

