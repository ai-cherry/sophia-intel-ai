import React, { useState, useEffect } from 'react';
import { AlertCircle, CheckCircle, Settings, MessageSquare, Database, Activity, Server, Shield } from 'lucide-react';
import SystemStats from './SystemStats';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://sophia-intel.fly.dev';

// Authentication context
const AuthContext = React.createContext();

// Authentication provider
const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authToken, setAuthToken] = useState(null);
  const [userInfo, setUserInfo] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing token
    const token = localStorage.getItem('sophia_auth_token');
    if (token) {
      setAuthToken(token);
      setIsAuthenticated(true);
      // Decode user info from token if needed
      setUserInfo({ user_id: 'admin_user', access_level: 'admin' });
    }
    setLoading(false);
  }, []);

  const login = async (apiKey) => {
    try {
      // For now, use API key directly as Bearer token
      setAuthToken(apiKey);
      setIsAuthenticated(true);
      setUserInfo({ user_id: 'admin_user', access_level: 'admin' });
      localStorage.setItem('sophia_auth_token', apiKey);
      return true;
    } catch (error) {
      console.error('Login failed:', error);
      return false;
    }
  };

  const logout = () => {
    setAuthToken(null);
    setIsAuthenticated(false);
    setUserInfo(null);
    localStorage.removeItem('sophia_auth_token');
  };

  return (
    <AuthContext.Provider value={{
      isAuthenticated,
      authToken,
      userInfo,
      loading,
      login,
      logout
    }}>
      {children}
    </AuthContext.Provider>
  );
};

// Login component
const LoginForm = () => {
  const [apiKey, setApiKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { login } = React.useContext(AuthContext);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const success = await login(apiKey);
    if (!success) {
      setError('Authentication failed. Please check your API key.');
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 flex items-center justify-center p-4">
      <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 w-full max-w-md border border-white/20">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">SOPHIA Intel</h1>
          <p className="text-blue-200">AI Orchestration Platform</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-blue-200 mb-2">
              API Key
            </label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
              placeholder="Enter your API key"
              required
            />
          </div>

          {error && (
            <div className="flex items-center space-x-2 text-red-300 text-sm">
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium py-3 px-4 rounded-lg transition-colors"
          >
            {loading ? 'Authenticating...' : 'Login'}
          </button>
        </form>

        <div className="mt-6 p-4 bg-blue-900/30 rounded-lg">
          <p className="text-xs text-blue-200 mb-2">For testing, use one of these API keys:</p>
          <div className="space-y-1 text-xs font-mono">
            <div className="text-green-300">Admin: Get from /auth/keys endpoint</div>
            <div className="text-yellow-300">User: Contact administrator</div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Enhanced Chat Component
const EnhancedChatPanel = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [systemStatus, setSystemStatus] = useState(null);
  const { authToken } = React.useContext(AuthContext);

  useEffect(() => {
    // Generate session ID
    setSessionId(`session_${Date.now()}`);
    
    // Load system status
    loadSystemStatus();
    
    // Add welcome message
    setMessages([{
      role: 'assistant',
      content: 'Hello! I\'m SOPHIA, your AI orchestrator with complete ecosystem awareness. I can help you manage infrastructure, databases, deployments, and business integrations. What would you like me to do?',
      timestamp: new Date().toISOString(),
      metadata: { system_message: true }
    }]);
  }, []);

  const loadSystemStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/system/status`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const status = await response.json();
        setSystemStatus(status);
      }
    } catch (error) {
      console.error('Failed to load system status:', error);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || loading) return;

    const userMessage = {
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/api/v1/sophia/chat/enhanced`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: inputMessage,
          session_id: sessionId,
          web_access: true,
          deep_research: true,
          use_swarm: false
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      const assistantMessage = {
        role: 'assistant',
        content: data.response,
        timestamp: new Date().toISOString(),
        metadata: data.metadata
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      // Update system status if provided
      if (data.metadata?.system_status) {
        setSystemStatus(data.metadata.system_status);
      }

    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = {
        role: 'assistant',
        content: `I encountered an error: ${error.message}. Please check your connection and try again.`,
        timestamp: new Date().toISOString(),
        metadata: { error: true }
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* System Status Bar */}
      {systemStatus && (
        <div className="bg-gray-800 border-b border-gray-700 p-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${
                  systemStatus.status === 'operational' ? 'bg-green-400' : 
                  systemStatus.status === 'degraded' ? 'bg-yellow-400' : 'bg-red-400'
                }`}></div>
                <span className="text-sm text-gray-300">
                  System: {systemStatus.status}
                </span>
              </div>
              <div className="text-xs text-gray-400">
                Services: {Object.keys(systemStatus.services).length} active
              </div>
            </div>
            <div className="text-xs text-gray-400">
              Session: {sessionId?.slice(-8)}
            </div>
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message, index) => (
          <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-3xl p-4 rounded-lg ${
              message.role === 'user' 
                ? 'bg-blue-600 text-white' 
                : message.metadata?.error 
                  ? 'bg-red-900/50 text-red-200 border border-red-700'
                  : 'bg-gray-800 text-gray-100'
            }`}>
              <div className="whitespace-pre-wrap">{message.content}</div>
              {message.metadata && !message.metadata.system_message && (
                <div className="mt-2 pt-2 border-t border-gray-600 text-xs text-gray-400">
                  {message.metadata.backend_used && (
                    <span>Backend: {message.metadata.backend_used} • </span>
                  )}
                  {message.metadata.access_level && (
                    <span>Access: {message.metadata.access_level} • </span>
                  )}
                  <span>{new Date(message.timestamp).toLocaleTimeString()}</span>
                </div>
              )}
            </div>
          </div>
        ))}
        
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-800 text-gray-100 p-4 rounded-lg">
              <div className="flex items-center space-x-2">
                <div className="animate-spin w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full"></div>
                <span>SOPHIA is thinking...</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-gray-700 p-4">
        <div className="flex space-x-4">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask SOPHIA anything about infrastructure, deployments, databases, or business operations..."
            className="flex-1 bg-gray-800 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-400 resize-none"
            rows="2"
            disabled={loading}
          />
          <button
            onClick={sendMessage}
            disabled={loading || !inputMessage.trim()}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-6 py-3 rounded-lg font-medium transition-colors"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
};

// System Status Component
const SystemStatusPanel = () => {
  const [status, setStatus] = useState(null);
  const [capabilities, setCapabilities] = useState(null);
  const [loading, setLoading] = useState(true);
  const { authToken } = React.useContext(AuthContext);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [statusRes, capabilitiesRes] = await Promise.all([
        fetch(`${API_BASE_URL}/api/v1/system/status`, {
          headers: { 'Authorization': `Bearer ${authToken}` }
        }),
        fetch(`${API_BASE_URL}/api/v1/system/capabilities`, {
          headers: { 'Authorization': `Bearer ${authToken}` }
        })
      ]);

      if (statusRes.ok) {
        setStatus(await statusRes.json());
      }
      if (capabilitiesRes.ok) {
        setCapabilities(await capabilitiesRes.json());
      }
    } catch (error) {
      console.error('Failed to load system data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-2 border-blue-400 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Overall Status */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">System Overview</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-700 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <CheckCircle className="text-green-400" size={20} />
              <span className="text-white font-medium">Status</span>
            </div>
            <p className="text-2xl font-bold text-green-400 capitalize">
              {status?.status || 'Unknown'}
            </p>
          </div>
          
          <div className="bg-gray-700 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Activity className="text-blue-400" size={20} />
              <span className="text-white font-medium">Uptime</span>
            </div>
            <p className="text-2xl font-bold text-blue-400">
              {status?.metrics?.uptime || 'N/A'}
            </p>
          </div>
          
          <div className="bg-gray-700 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Server className="text-purple-400" size={20} />
              <span className="text-white font-medium">Services</span>
            </div>
            <p className="text-2xl font-bold text-purple-400">
              {status?.services ? Object.keys(status.services).length : 0}
            </p>
          </div>
        </div>
      </div>

      {/* Services Status */}
      {status?.services && (
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Services Status</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {Object.entries(status.services).map(([service, serviceStatus]) => (
              <div key={service} className="bg-gray-700 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-300">{service}</span>
                  <div className={`w-2 h-2 rounded-full ${
                    serviceStatus === 'operational' ? 'bg-green-400' : 
                    serviceStatus === 'degraded' ? 'bg-yellow-400' : 'bg-red-400'
                  }`}></div>
                </div>
                <p className="text-xs text-gray-400 capitalize mt-1">{serviceStatus}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Capabilities */}
      {capabilities && (
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">SOPHIA Capabilities</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-blue-400">Infrastructure Control</h4>
              <div className="flex items-center space-x-2">
                <Shield className={capabilities.infrastructure_control_enabled ? 'text-green-400' : 'text-red-400'} size={16} />
                <span className="text-sm text-gray-300">
                  {capabilities.infrastructure_control_enabled ? 'Enabled' : 'Disabled'}
                </span>
              </div>
            </div>
            
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-blue-400">Admin Mode</h4>
              <div className="flex items-center space-x-2">
                <Shield className={capabilities.admin_mode_enabled ? 'text-green-400' : 'text-red-400'} size={16} />
                <span className="text-sm text-gray-300">
                  {capabilities.admin_mode_enabled ? 'Enabled' : 'Disabled'}
                </span>
              </div>
            </div>
          </div>
          
          <div className="mt-4 pt-4 border-t border-gray-700">
            <p className="text-sm text-gray-400">
              Total Capabilities: {capabilities.total_capabilities} • 
              Categories: {capabilities.categories?.length || 0} • 
              Services: {capabilities.services_registered || 0}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

// Main Dashboard Component
const EnhancedDashboard = () => {
  const [activeTab, setActiveTab] = useState('chat');
  const { logout, userInfo } = React.useContext(AuthContext);

  const tabs = [
    { id: 'chat', label: 'Chat', icon: MessageSquare },
    { id: 'status', label: 'System Status', icon: Activity },
    { id: 'database', label: 'Database', icon: Database },
    { id: 'settings', label: 'Settings', icon: Settings }
  ];

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              SOPHIA Intel
            </h1>
            <span className="text-sm text-gray-400">Enhanced AI Orchestrator</span>
          </div>
          
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-400">
              {userInfo?.access_level} • {userInfo?.user_id}
            </span>
            <button
              onClick={logout}
              className="text-sm text-red-400 hover:text-red-300 transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <div className="flex h-[calc(100vh-73px)]">
        {/* Sidebar */}
        <nav className="w-64 bg-gray-800 border-r border-gray-700 p-4">
          <div className="space-y-2">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                    activeTab === tab.id
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  }`}
                >
                  <Icon size={20} />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>
        </nav>

        {/* Main Content */}
        <main className="flex-1 overflow-hidden">
          {activeTab === 'chat' && <EnhancedChatPanel />}
          {activeTab === 'status' && (
            <div className="p-6 space-y-6">
              <SystemStats />
              <SystemStatusPanel />
            </div>
          )}
          {activeTab === 'database' && (
            <div className="p-6">
              <h2 className="text-2xl font-bold mb-4">Database Management</h2>
              <p className="text-gray-400">Database management interface coming soon...</p>
            </div>
          )}
          {activeTab === 'settings' && (
            <div className="p-6">
              <h2 className="text-2xl font-bold mb-4">Settings</h2>
              <p className="text-gray-400">Settings interface coming soon...</p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

// Main App Component
const EnhancedAuthenticatedApp = () => {
  return (
    <AuthProvider>
      <AuthContext.Consumer>
        {({ isAuthenticated, loading }) => {
          if (loading) {
            return (
              <div className="min-h-screen bg-gray-900 flex items-center justify-center">
                <div className="animate-spin w-8 h-8 border-2 border-blue-400 border-t-transparent rounded-full"></div>
              </div>
            );
          }
          
          return isAuthenticated ? <EnhancedDashboard /> : <LoginForm />;
        }}
      </AuthContext.Consumer>
    </AuthProvider>
  );
};

export default EnhancedAuthenticatedApp;

