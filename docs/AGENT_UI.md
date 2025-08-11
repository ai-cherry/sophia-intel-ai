# Agent UI Setup Guide

This guide covers setting up the optional Agent UI for the Sophia Intel platform. The Agent UI provides a web-based interface for interacting with agents, monitoring performance, and managing sessions.

## Overview

The Sophia Agent UI is built with React and provides:
- **Agent Interaction**: Submit code analysis and modification requests
- **Session Management**: Track conversations across multiple interactions
- **Real-time Monitoring**: View agent status, performance metrics, and logs  
- **Memory Context**: Browse and search stored context from MCP
- **Multi-agent Support**: Interface for different agent types

## Quick Setup

### Option 1: Use Existing Agent UI Package

If you have access to a pre-built Agent UI package:

```bash
# Navigate to frontend directory
cd frontend

# Install the Agent UI package
npm install @agno/agent-ui@latest

# Configure for Sophia platform
cat > src/config.js << 'EOF'
export const config = {
  apiEndpoint: process.env.REACT_APP_API_ENDPOINT || 'http://localhost:8000',
  agnoApiEndpoint: process.env.REACT_APP_AGNO_ENDPOINT || 'http://localhost:7777', 
  mcpEndpoint: process.env.REACT_APP_MCP_ENDPOINT || 'http://localhost:8001',
  enableRealtime: true,
  enableMemoryBrowsing: true
};
EOF

# Update package.json scripts
npm pkg set scripts.start="REACT_APP_API_ENDPOINT=http://localhost:8000 REACT_APP_AGNO_ENDPOINT=http://localhost:7777 REACT_APP_MCP_ENDPOINT=http://localhost:8001 react-scripts start"

# Start development server
npm start
```

### Option 2: Use Built-in React Frontend

The repository includes a basic React frontend in the `frontend/` directory:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Set environment variables
cat > .env.local << 'EOF'
REACT_APP_API_ENDPOINT=http://localhost:8000
REACT_APP_AGNO_ENDPOINT=http://localhost:7777
REACT_APP_MCP_ENDPOINT=http://localhost:8001
EOF

# Start development server
npm start
```

The UI will be available at http://localhost:3000

## Enhanced Setup

### Environment Configuration

Create a comprehensive environment configuration:

```bash
# frontend/.env.local
REACT_APP_API_ENDPOINT=http://localhost:8000
REACT_APP_AGNO_ENDPOINT=http://localhost:7777
REACT_APP_MCP_ENDPOINT=http://localhost:8001

# Feature flags
REACT_APP_ENABLE_MEMORY_BROWSER=true
REACT_APP_ENABLE_METRICS_DASHBOARD=true
REACT_APP_ENABLE_REAL_TIME_LOGS=true
REACT_APP_ENABLE_MULTI_AGENT=true

# UI Configuration
REACT_APP_THEME=dark
REACT_APP_DEFAULT_SESSION_TIMEOUT=3600000
REACT_APP_MAX_CODE_LENGTH=50000
REACT_APP_ENABLE_SYNTAX_HIGHLIGHTING=true
```

### Custom Agent UI Components

If extending the UI with custom components:

#### Agent Interaction Component

```jsx
// src/components/AgentInterface.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const AgentInterface = () => {
  const [sessionId, setSessionId] = useState('');
  const [code, setCode] = useState('');
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await axios.post(`${process.env.REACT_APP_AGNO_ENDPOINT}/agent/coding`, {
        session_id: sessionId || `session-${Date.now()}`,
        code,
        query,
        file_path: '',
        language: 'python'
      });
      
      setResult(response.data);
      setHistory(prev => [...prev, { query, code, result: response.data, timestamp: new Date() }]);
      
      // Store in memory if successful
      if (response.data.success) {
        await storeInMemory(sessionId, query, code, response.data.result);
      }
    } catch (error) {
      setResult({ success: false, error: error.message });
    } finally {
      setLoading(false);
    }
  };

  const storeInMemory = async (sessionId, query, code, result) => {
    try {
      await axios.post(`${process.env.REACT_APP_MCP_ENDPOINT}/context/store`, {
        session_id: sessionId,
        content: `Query: ${query}\nCode: ${code}\nResult: ${result.summary}`,
        metadata: {
          context_type: 'agent_interaction',
          query,
          summary: result.summary
        }
      });
    } catch (error) {
      console.warn('Failed to store interaction in memory:', error);
    }
  };

  return (
    <div className="agent-interface">
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="sessionId">Session ID:</label>
          <input
            type="text"
            id="sessionId"
            value={sessionId}
            onChange={(e) => setSessionId(e.target.value)}
            placeholder="Leave empty for auto-generated"
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="code">Code:</label>
          <textarea
            id="code"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="Enter your code here..."
            rows="15"
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="query">Task:</label>
          <input
            type="text"
            id="query"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="What should the agent do with this code?"
            required
          />
        </div>
        
        <button type="submit" disabled={loading}>
          {loading ? 'Processing...' : 'Send to Agent'}
        </button>
      </form>
      
      {result && (
        <div className="result-section">
          <h3>Agent Response</h3>
          {result.success ? (
            <div className="success-result">
              <div className="summary">
                <h4>Summary:</h4>
                <p>{result.result.summary}</p>
              </div>
              {result.result.patch && (
                <div className="patch">
                  <h4>Changes:</h4>
                  <pre className="diff">{result.result.patch}</pre>
                </div>
              )}
            </div>
          ) : (
            <div className="error-result">
              <h4>Error:</h4>
              <p>{result.error}</p>
            </div>
          )}
        </div>
      )}
      
      {history.length > 0 && (
        <div className="history-section">
          <h3>Session History</h3>
          {history.map((item, index) => (
            <div key={index} className="history-item">
              <div className="timestamp">{item.timestamp.toLocaleTimeString()}</div>
              <div className="query">{item.query}</div>
              <div className="summary">{item.result.result?.summary}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AgentInterface;
```

#### Memory Browser Component

```jsx
// src/components/MemoryBrowser.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const MemoryBrowser = () => {
  const [sessions, setSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState('');
  const [contexts, setContexts] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);

  const searchContexts = async () => {
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    try {
      const response = await axios.post(`${process.env.REACT_APP_MCP_ENDPOINT}/context/query`, {
        session_id: selectedSession,
        query: searchQuery,
        top_k: 10,
        global_search: !selectedSession
      });
      
      setContexts(response.data.results || []);
    } catch (error) {
      console.error('Search failed:', error);
      setContexts([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="memory-browser">
      <div className="search-section">
        <div className="search-controls">
          <input
            type="text"
            value={selectedSession}
            onChange={(e) => setSelectedSession(e.target.value)}
            placeholder="Session ID (leave empty for global search)"
          />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search memory contexts..."
          />
          <button onClick={searchContexts} disabled={loading}>
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </div>
      
      <div className="results-section">
        {contexts.length > 0 ? (
          <div className="contexts-list">
            {contexts.map((context, index) => (
              <div key={index} className="context-item">
                <div className="context-header">
                  <span className="score">Score: {context.score?.toFixed(3)}</span>
                  <span className="session">Session: {context.session_id}</span>
                  <span className="timestamp">{context.timestamp}</span>
                </div>
                <div className="context-content">
                  {context.content}
                </div>
                {context.metadata && (
                  <div className="context-metadata">
                    {Object.entries(context.metadata).map(([key, value]) => (
                      <span key={key} className="metadata-tag">
                        {key}: {String(value)}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="no-results">
            {searchQuery ? 'No contexts found for your search.' : 'Enter a search query to browse memory contexts.'}
          </div>
        )}
      </div>
    </div>
  );
};

export default MemoryBrowser;
```

### Agent Status Dashboard

```jsx
// src/components/AgentDashboard.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const AgentDashboard = () => {
  const [agentStats, setAgentStats] = useState(null);
  const [systemHealth, setSystemHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [statsResponse, healthResponse] = await Promise.all([
          axios.get(`${process.env.REACT_APP_AGNO_ENDPOINT}/agent/coding/stats`),
          axios.get(`${process.env.REACT_APP_AGNO_ENDPOINT}/health`)
        ]);
        
        setAgentStats(statsResponse.data);
        setSystemHealth(healthResponse.data);
      } catch (error) {
        console.error('Failed to fetch stats:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 30000); // Update every 30 seconds
    
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div>Loading dashboard...</div>;

  return (
    <div className="agent-dashboard">
      <div className="dashboard-grid">
        <div className="stat-card">
          <h3>Agent Performance</h3>
          <div className="stat-item">
            <span className="label">Status:</span>
            <span className={`status ${agentStats?.status?.toLowerCase()}`}>
              {agentStats?.status}
            </span>
          </div>
          <div className="stat-item">
            <span className="label">Tasks Completed:</span>
            <span className="value">{agentStats?.tasks_completed || 0}</span>
          </div>
          <div className="stat-item">
            <span className="label">Success Rate:</span>
            <span className="value">
              {((agentStats?.success_rate || 0) * 100).toFixed(1)}%
            </span>
          </div>
          <div className="stat-item">
            <span className="label">Avg Response Time:</span>
            <span className="value">
              {(agentStats?.average_duration || 0).toFixed(2)}s
            </span>
          </div>
        </div>
        
        <div className="stat-card">
          <h3>System Health</h3>
          <div className="stat-item">
            <span className="label">Overall Status:</span>
            <span className={`status ${systemHealth?.status}`}>
              {systemHealth?.status}
            </span>
          </div>
          {systemHealth?.agents && (
            <div className="agents-status">
              {Object.entries(systemHealth.agents).map(([agentName, status]) => (
                <div key={agentName} className="stat-item">
                  <span className="label">{agentName}:</span>
                  <span className={`status ${status.healthy ? 'healthy' : 'unhealthy'}`}>
                    {status.healthy ? 'Healthy' : 'Unhealthy'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AgentDashboard;
```

## Styling

Add enhanced styling for a professional look:

```css
/* src/AgentUI.css */
.agent-interface {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #333;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-family: 'Monaco', 'Menlo', monospace;
}

.result-section {
  margin-top: 30px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.diff {
  background: #2d3748;
  color: #e2e8f0;
  padding: 16px;
  border-radius: 6px;
  overflow-x: auto;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
}

.status.healthy {
  color: #38a169;
  font-weight: 600;
}

.status.unhealthy,
.status.error {
  color: #e53e3e;
  font-weight: 600;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.stat-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #eee;
}

.stat-item:last-child {
  border-bottom: none;
}

.context-item {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.context-header {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
  font-size: 12px;
  color: #666;
}

.metadata-tag {
  background: #e2e8f0;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  margin-right: 8px;
}
```

## Production Deployment

For production deployment:

```bash
# Build optimized version
npm run build

# Serve with nginx or similar
# nginx.conf location block:
location / {
  try_files $uri $uri/ /index.html;
}

location /api {
  proxy_pass http://localhost:8000;
  proxy_set_header Host $host;
  proxy_set_header X-Real-IP $remote_addr;
}

location /agent {
  proxy_pass http://localhost:7777;
  proxy_set_header Host $host;
  proxy_set_header X-Real-IP $remote_addr;
}

location /mcp {
  proxy_pass http://localhost:8001;
  proxy_set_header Host $host;
  proxy_set_header X-Real-IP $remote_addr;
}
```

## Environment Variables

Complete environment configuration for production:

```bash
# Production .env
REACT_APP_API_ENDPOINT=https://api.sophia.yourdomain.com
REACT_APP_AGNO_ENDPOINT=https://agents.sophia.yourdomain.com  
REACT_APP_MCP_ENDPOINT=https://mcp.sophia.yourdomain.com

REACT_APP_ENABLE_MEMORY_BROWSER=true
REACT_APP_ENABLE_METRICS_DASHBOARD=true
REACT_APP_ENABLE_REAL_TIME_LOGS=true
REACT_APP_ENABLE_MULTI_AGENT=true

REACT_APP_THEME=auto
REACT_APP_DEFAULT_SESSION_TIMEOUT=7200000
REACT_APP_MAX_CODE_LENGTH=100000
REACT_APP_ENABLE_SYNTAX_HIGHLIGHTING=true

# Security
REACT_APP_ENABLE_AUTH=true
REACT_APP_AUTH_PROVIDER=oauth2
```

The Agent UI provides a comprehensive interface for interacting with the Sophia Intel platform, with support for real-time agent interaction, memory browsing, and system monitoring.