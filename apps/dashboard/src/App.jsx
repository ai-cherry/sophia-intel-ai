import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [apiStatus, setApiStatus] = useState('checking...');
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');

  useEffect(() => {
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
    
    try {
      const res = await fetch('https://sophia-backend-production-1fc3.up.railway.app/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message,
          conversation_id: 'web-' + Date.now()
        })
      });
      
      const data = await res.json();
      setResponse(JSON.stringify(data, null, 2));
    } catch (error) {
      setResponse('Error: ' + error.message);
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
          <div className="chat-input">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Ask SOPHIA anything..."
              onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            />
            <button onClick={sendMessage}>Send</button>
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

