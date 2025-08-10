import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [code, setCode] = useState('');
  const [query, setQuery] = useState('');
  const [sessionId, setSessionId] = useState('demo-session');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await axios.post('http://localhost:7777/agent/coding', {
        session_id: sessionId,
        code: code,
        query: query
      });
      setResult(response.data);
    } catch (error) {
      setResult({ error: error.message });
    }
    setLoading(false);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Sophia AI Agent Platform</h1>
        <p>Coding Agent Playground</p>
      </header>
      
      <div className="container">
        <form onSubmit={handleSubmit} className="agent-form">
          <div className="form-group">
            <label htmlFor="sessionId">Session ID:</label>
            <input
              type="text"
              id="sessionId"
              value={sessionId}
              onChange={(e) => setSessionId(e.target.value)}
              placeholder="Enter session ID"
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="code">Code:</label>
            <textarea
              id="code"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="Enter your code here..."
              rows="10"
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="query">Query:</label>
            <input
              type="text"
              id="query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="What would you like the agent to do?"
            />
          </div>
          
          <button type="submit" disabled={loading} className="submit-btn">
            {loading ? 'Processing...' : 'Send to Agent'}
          </button>
        </form>
        
        {result && (
          <div className="result-section">
            <h3>Agent Response:</h3>
            <pre className="result-output">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;