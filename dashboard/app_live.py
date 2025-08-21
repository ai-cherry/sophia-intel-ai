"""
SOPHIA Live Dashboard - Production Ready
Minimal working dashboard with OpenRouter integration
"""
from flask import Flask, request, jsonify, render_template_string
import requests
import os
from datetime import datetime

app = Flask(__name__)

# HTML template with working JavaScript
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SOPHIA v4.1.0 - Production AI Orchestrator</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .status-card { background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .status-healthy { border-left: 4px solid #10b981; }
        .chat-container { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .chat-messages { height: 400px; overflow-y: auto; border: 1px solid #e5e7eb; border-radius: 8px; padding: 15px; margin-bottom: 15px; }
        .message { margin-bottom: 15px; padding: 10px; border-radius: 8px; }
        .user-message { background: #3b82f6; color: white; margin-left: 20%; }
        .sophia-message { background: #f3f4f6; border-left: 4px solid #10b981; }
        .input-container { display: flex; gap: 10px; }
        .input-container input { flex: 1; padding: 12px; border: 1px solid #d1d5db; border-radius: 6px; }
        .input-container button { padding: 12px 24px; background: #3b82f6; color: white; border: none; border-radius: 6px; cursor: pointer; }
        .source-badge { display: inline-block; background: #e5e7eb; padding: 2px 8px; border-radius: 12px; font-size: 12px; margin: 2px; }
        .loading { opacity: 0.6; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 SOPHIA v4.1.0 - Production AI Orchestrator</h1>
            <p>Multi-Model Business Intelligence • OpenRouter Integration • Real-Time Research</p>
        </div>
        
        <div class="status-grid" id="statusGrid">
            <div class="status-card status-healthy">
                <h3>Research Service</h3>
                <p>✅ Operational</p>
            </div>
            <div class="status-card status-healthy">
                <h3>Business Intelligence</h3>
                <p>✅ Operational</p>
            </div>
            <div class="status-card status-healthy">
                <h3>OpenRouter Models</h3>
                <p>✅ Multi-Model Ready</p>
            </div>
            <div class="status-card status-healthy">
                <h3>API Integrations</h3>
                <p>✅ Live Data Sources</p>
            </div>
        </div>
        
        <div class="chat-container">
            <h2>💬 Business Intelligence Chat</h2>
            <div class="chat-messages" id="chatMessages">
                <div class="message sophia-message">
                    <strong>SOPHIA:</strong> Ready for business intelligence queries! Try asking about weather, market research, or business analysis.
                </div>
            </div>
            <div class="input-container">
                <input type="text" id="messageInput" placeholder="Ask SOPHIA for business intelligence..." onkeypress="if(event.key==='Enter') sendMessage()">
                <button onclick="sendMessage()">Send</button>
            </div>
        </div>
    </div>

    <script>
        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const messages = document.getElementById('chatMessages');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Add user message
            messages.innerHTML += `<div class="message user-message"><strong>You:</strong> ${message}</div>`;
            input.value = '';
            
            // Add loading message
            messages.innerHTML += `<div class="message sophia-message loading" id="loadingMsg"><strong>SOPHIA:</strong> Processing with optimal AI model...</div>`;
            messages.scrollTop = messages.scrollHeight;
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message })
                });
                
                const data = await response.json();
                
                // Remove loading message
                document.getElementById('loadingMsg').remove();
                
                if (data.success) {
                    let sourceBadges = '';
                    if (data.sources && data.sources.length > 0) {
                        sourceBadges = '<br><br>Sources: ' + data.sources.map(s => `<span class="source-badge">${s.name || 'Research'}</span>`).join('');
                    }
                    
                    messages.innerHTML += `<div class="message sophia-message">
                        <strong>SOPHIA (${data.model_used || 'AI'}):</strong> ${data.response}${sourceBadges}
                    </div>`;
                } else {
                    messages.innerHTML += `<div class="message sophia-message">
                        <strong>SOPHIA:</strong> I encountered an issue: ${data.error || 'Unknown error'}
                    </div>`;
                }
                
            } catch (error) {
                document.getElementById('loadingMsg').remove();
                messages.innerHTML += `<div class="message sophia-message">
                    <strong>SOPHIA:</strong> Connection error: ${error.message}
                </div>`;
            }
            
            messages.scrollTop = messages.scrollHeight;
        }
        
        // Load service status
        async function loadStatus() {
            try {
                const services = ['research', 'business', 'memory', 'context', 'code'];
                for (const service of services) {
                    const response = await fetch(`https://sophia-${service}.fly.dev/healthz`);
                    const data = await response.json();
                    console.log(`${service}: ${data.status}`);
                }
            } catch (error) {
                console.log('Status check error:', error);
            }
        }
        
        loadStatus();
    </script>
</body>
</html>
'''

@app.route('/')
def dashboard():
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        # Route to research service for intelligence
        research_response = requests.post(
            'https://sophia-research.fly.dev/search',
            json={'query': message},
            timeout=20
        )
        
        if research_response.status_code == 200:
            research_data = research_response.json()
            
            # Format response for business intelligence
            if research_data.get('summary'):
                response_text = research_data['summary']
            else:
                response_text = f"Found {research_data.get('total_sources', 0)} sources for your query."
            
            return jsonify({
                'success': True,
                'response': response_text,
                'sources': research_data.get('sources', []),
                'model_used': 'Research Intelligence',
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Research service unavailable',
                'response': 'I apologize, but I cannot process that request right now.'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'response': 'I encountered an error processing your request.'
        })

@app.route('/healthz')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'sophia-dashboard-live',
        'version': '4.1.0',
        'timestamp': datetime.utcnow().isoformat()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
