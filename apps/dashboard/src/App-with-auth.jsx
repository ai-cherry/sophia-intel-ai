import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [apiStatus, setApiStatus] = useState('checking...');
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [authToken, setAuthToken] = useState('');

  // Simple authentication token for development
  const DEV_AUTH_TOKEN = 'sophia-dev-token-2024';

  useEffect(() => {
    // Set development auth token
    setAuthToken(DEV_AUTH_TOKEN);
    
    // Check backend API health
    fetch('https://sophia-backend-production-1fc3.up.railway.app/health')
      .then(res => res.json())
      .then(data => {
        setApiStatus('✅ Connected');
        console.log('Backend health:', data);
      })
      .catch(err => {
        setApiStatus('❌ Disconnected');
        console.error('Backend error:', err);
      });
  }, []);

  const sendMessage = async () => {
    if (!message.trim()) return;
    
    setIsLoading(true);
    setResponse('');
    
    try {
      // Try the enhanced chat endpoint with authentication
      const res = await fetch('https://sophia-backend-production-1fc3.up.railway.app/api/v1/sophia/chat/enhanced', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          message: message,
          conversation_id: 'web-' + Date.now(),
          stream: false
        })
      });
      
      if (res.status === 401) {
        // If authentication fails, try without auth for development
        console.log('Auth failed, trying without authentication...');
        const fallbackRes = await fetch('https://sophia-backend-production-1fc3.up.railway.app/api/v1/sophia/status', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          }
        });
        
        if (fallbackRes.ok) {
          const fallbackData = await fallbackRes.json();
          setResponse(JSON.stringify({
            message: "Authentication is required for chat. System status retrieved instead:",
            status: fallbackData
          }, null, 2));
        } else {
          throw new Error(`HTTP ${fallbackRes.status}: ${fallbackRes.statusText}`);
        }
      } else if (res.ok) {
        const data = await res.json();
        setResponse(JSON.stringify(data, null, 2));
      } else {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      
    } catch (error) {
      console.error('Chat error:', error);
      setResponse(`Error: ${error.message}\n\nNote: The chat system requires proper authentication. This is a development version showing system status instead.`);
    } finally {
      setIsLoading(false);
    }
  };

  const testAuthentication = async () => {
    try {
      setResponse('Testing authentication...');
      
      // Test with different endpoints to understand auth requirements
      const endpoints = [
        { name: 'Health Check (No Auth)', url: '/health' },
        { name: 'System Status (May Need Auth)', url: '/api/v1/sophia/status' },
        { name: 'Chat Enhanced (Needs Auth)', url: '/api/v1/sophia/chat/enhanced' }
      ];
      
      const results = [];
      
      for (const endpoint of endpoints) {
        try {
          const res = await fetch(`https://sophia-backend-production-1fc3.up.railway.app${endpoint.url}`, {
            method: endpoint.url.includes('chat') ? 'POST' : 'GET',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${authToken}`
            },
            body: endpoint.url.includes('chat') ? JSON.stringify({
              message: 'test',
              conversation_id: 'auth-test'
            }) : undefined
          });
          
          results.push({
            endpoint: endpoint.name,
            status: res.status,
            success: res.ok,
            response: res.ok ? 'Success' : `Error: ${res.status} ${res.statusText}`
          });
        } catch (error) {
          results.push({
            endpoint: endpoint.name,
            status: 'Error',
            success: false,
            response: error.message
          });
        }
      }
      
      setResponse(JSON.stringify({
        message: 'Authentication Test Results',
        token_used: authToken,
        results: results
      }, null, 2));
      
    } catch (error) {
      setResponse(`Authentication test failed: ${error.message}`);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <img src="/sophia-logo.png" alt="SOPHIA" className="logo" />
        <h1>SOPHIA Intel</h1>
        <p>Advanced AI Development Platform</p>
        <div className="status">Backend Status: {apiStatus}</div>
      </header>

      <main className="app-main">
        <section className="chat-section">
          <h2>Chat with SOPHIA</h2>
          
          <div className="auth-section">
            <label>
              Auth Token (Development):
              <input
                type="text"
                value={authToken}
                onChange={(e) => setAuthToken(e.target.value)}
                placeholder="Enter authentication token"
                style={{ width: '300px', margin: '10px' }}
              />
            </label>
            <button onClick={testAuthentication} style={{ margin: '10px' }}>
              Test Authentication
            </button>
          </div>
          
          <div className="chat-input">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Ask SOPHIA anything..."
              onKeyPress={(e) => e.key === 'Enter' && !isLoading && sendMessage()}
              disabled={isLoading}
            />
            <button onClick={sendMessage} disabled={isLoading || !message.trim()}>
              {isLoading ? 'Sending...' : 'Send'}
            </button>
          </div>
          
          {response && (
            <div className="response">
              <h3>Response:</h3>
              <pre>{response}</pre>
            </div>
          )}
        </section>

        <section className="features">
          <h2>Platform Features</h2>
          <div className="feature-grid">
            <div className="feature">
              <h3>🤖 Intelligent Chat</h3>
              <p>Advanced AI routing with confidence scoring</p>
            </div>
            <div className="feature">
              <h3>⚡ Lambda Labs</h3>
              <p>GH200 GPU integration for high-performance computing</p>
            </div>
            <div className="feature">
              <h3>🔧 Infrastructure</h3>
              <p>Automated deployment and monitoring</p>
            </div>
            <div className="feature">
              <h3>📊 Observability</h3>
              <p>Real-time metrics and health monitoring</p>
            </div>
          </div>
        </section>
      </main>

      <footer className="app-footer">
        <p>SOPHIA Intel - Production Ready AI Platform</p>
        <p>Backend: <a href="https://sophia-backend-production-1fc3.up.railway.app/" target="_blank" rel="noopener noreferrer">API Endpoint</a></p>
      </footer>
    </div>
  );
}

export default App;

