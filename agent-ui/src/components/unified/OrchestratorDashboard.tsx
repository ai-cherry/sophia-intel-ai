'use client';

import React, { useState, useEffect, useRef } from 'react';
import { 
  Send, Bot, User, Activity, Shield, Zap, Settings, 
  AlertCircle, CheckCircle, XCircle, TrendingUp, 
  Server, Cpu, Database, GitBranch, ToggleLeft, ToggleRight,
  BarChart3, Clock, Users, Layers
} from 'lucide-react';

// ==================== Types ====================

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sessionId?: string;
  correlationId?: string;
  executionTime?: number;
  tokens?: number;
}

interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  components: {
    orchestrator: ComponentHealth;
    circuitBreakers: CircuitBreakerStatus[];
    connectionPool: ConnectionPoolStatus;
    degradationLevel: DegradationLevel;
  };
}

interface ComponentHealth {
  name: string;
  status: 'healthy' | 'degraded' | 'unhealthy';
  uptime: number;
  errorRate: number;
  responseTime: number;
}

interface CircuitBreakerStatus {
  name: string;
  state: 'CLOSED' | 'OPEN' | 'HALF_OPEN';
  failureCount: number;
  successCount: number;
  lastFailure?: Date;
}

interface ConnectionPoolStatus {
  active: number;
  idle: number;
  total: number;
  maxAllowed: number;
  utilizationPercent: number;
}

interface DegradationLevel {
  level: 'NORMAL' | 'LIMITED' | 'ESSENTIAL' | 'EMERGENCY' | 'MAINTENANCE';
  disabledFeatures: string[];
  reason?: string;
}

interface FeatureFlag {
  name: string;
  enabled: boolean;
  strategy: string;
  percentage: number;
}

interface SessionInfo {
  id: string;
  messageCount: number;
  tokenCount: number;
  startTime: Date;
  lastActivity: Date;
}

interface MetricsData {
  requestRate: number;
  errorRate: number;
  p95ResponseTime: number;
  activeConnections: number;
  throughput: number;
}

// ==================== Main Component ====================

export const OrchestratorDashboard: React.FC = () => {
  // State
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [sessionInfo, setSessionInfo] = useState<SessionInfo | null>(null);
  const [featureFlags, setFeatureFlags] = useState<FeatureFlag[]>([]);
  const [apiVersion, setApiVersion] = useState<'v1' | 'v2'>('v2');
  const [optimizationMode, setOptimizationMode] = useState<'lite' | 'balanced' | 'quality'>('balanced');
  const [swarmType, setSwarmType] = useState<string | null>(null);
  const [useMemory, setUseMemory] = useState(false);
  const [activeTab, setActiveTab] = useState<'chat' | 'health' | 'metrics' | 'settings'>('chat');
  
  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // WebSocket connection
  useEffect(() => {
    const clientId = `client-${Math.random().toString(36).substr(2, 9)}`;
    const sessionId = `session-${Date.now()}`;
    const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/chat/ws/${clientId}/${sessionId}`;
    
    try {
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        setIsConnected(true);
        console.log('Connected to AI Orchestra with enhanced features');
        
        // Request initial status
        wsRef.current?.send(JSON.stringify({
          type: 'control',
          data: { type: 'status' }
        }));
      };

      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        switch (data.type) {
          case 'chat':
            setMessages(prev => [...prev, {
              id: data.id || Date.now().toString(),
              role: 'assistant',
              content: data.response,
              timestamp: new Date(),
              sessionId: data.session_id,
              correlationId: data.correlation_id,
              executionTime: data.execution_time,
              tokens: data.tokens_used
            }]);
            setIsTyping(false);
            break;
            
          case 'status':
            updateSystemStatus(data.data);
            break;
            
          case 'metrics':
            setMetrics(data.data);
            break;
            
          case 'stream':
            // Handle token streaming
            handleStreamToken(data.token);
            break;
            
          case 'typing':
            setIsTyping(true);
            break;
        }
      };

      wsRef.current.onclose = () => {
        setIsConnected(false);
        console.log('Disconnected from AI Orchestra');
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      };
    } catch (error) {
      console.error('Failed to connect to WebSocket:', error);
    }

    // Cleanup
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // Periodic health check
  useEffect(() => {
    const interval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          type: 'control',
          data: { type: 'metrics' }
        }));
      }
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  // Helper functions
  const updateSystemStatus = (data: any) => {
    setSystemHealth({
      status: data.overall_health || 'healthy',
      components: {
        orchestrator: data.orchestrator || { 
          name: 'Orchestrator', 
          status: 'healthy',
          uptime: 0,
          errorRate: 0,
          responseTime: 0
        },
        circuitBreakers: data.circuit_breakers || [],
        connectionPool: data.connection_pool || {
          active: 0,
          idle: 0,
          total: 0,
          maxAllowed: 1000,
          utilizationPercent: 0
        },
        degradationLevel: data.degradation_level || {
          level: 'NORMAL',
          disabledFeatures: []
        }
      }
    });

    if (data.session_info) {
      setSessionInfo(data.session_info);
    }

    if (data.feature_flags) {
      setFeatureFlags(data.feature_flags);
    }
  };

  const handleStreamToken = (token: string) => {
    setMessages(prev => {
      const last = prev[prev.length - 1];
      if (last && last.role === 'assistant') {
        return [
          ...prev.slice(0, -1),
          { ...last, content: last.content + token }
        ];
      }
      return prev;
    });
  };

  const sendMessage = () => {
    if (!input.trim() || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    const message: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, message]);
    
    // Send with V2 API format including new features
    wsRef.current.send(JSON.stringify({
      type: 'chat',
      data: {
        message: input,
        api_version: apiVersion,
        optimization_mode: optimizationMode,
        swarm_type: swarmType,
        use_memory: useMemory,
        context: {
          session_id: sessionInfo?.id,
          correlation_id: `corr-${Date.now()}`
        }
      }
    }));

    setInput('');
    setIsTyping(true);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Component renders
  const renderHealthStatus = () => {
    if (!systemHealth) return null;

    const getStatusColor = (status: string) => {
      switch (status) {
        case 'healthy': return 'text-green-400';
        case 'degraded': return 'text-yellow-400';
        case 'unhealthy': return 'text-red-400';
        default: return 'text-gray-400';
      }
    };

    const getCircuitBreakerColor = (state: string) => {
      switch (state) {
        case 'CLOSED': return 'bg-green-500';
        case 'OPEN': return 'bg-red-500';
        case 'HALF_OPEN': return 'bg-yellow-500';
        default: return 'bg-gray-500';
      }
    };

    return (
      <div className="space-y-4">
        {/* Overall Health */}
        <div className="bg-white/5 backdrop-blur-md rounded-lg p-4 border border-white/10">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Activity className="w-5 h-5" />
              System Health
            </h3>
            <span className={`font-medium ${getStatusColor(systemHealth.status)}`}>
              {systemHealth.status.toUpperCase()}
            </span>
          </div>

          {/* Degradation Level */}
          <div className="mb-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-white/70">Degradation Level</span>
              <span className={`font-medium ${
                systemHealth.components.degradationLevel.level === 'NORMAL' 
                  ? 'text-green-400' 
                  : 'text-yellow-400'
              }`}>
                {systemHealth.components.degradationLevel.level}
              </span>
            </div>
            {systemHealth.components.degradationLevel.disabledFeatures.length > 0 && (
              <div className="mt-2 text-xs text-white/50">
                Disabled: {systemHealth.components.degradationLevel.disabledFeatures.join(', ')}
              </div>
            )}
          </div>

          {/* Connection Pool */}
          <div className="mb-3">
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="text-white/70">Connection Pool</span>
              <span className="text-white">
                {systemHealth.components.connectionPool.active}/{systemHealth.components.connectionPool.maxAllowed}
              </span>
            </div>
            <div className="w-full bg-white/10 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-[#00e0ff] to-[#ff00c3] h-2 rounded-full transition-all"
                style={{ width: `${systemHealth.components.connectionPool.utilizationPercent}%` }}
              />
            </div>
          </div>
        </div>

        {/* Circuit Breakers */}
        <div className="bg-white/5 backdrop-blur-md rounded-lg p-4 border border-white/10">
          <h3 className="text-lg font-semibold flex items-center gap-2 mb-3">
            <Shield className="w-5 h-5" />
            Circuit Breakers
          </h3>
          <div className="space-y-2">
            {systemHealth.components.circuitBreakers.map(cb => (
              <div key={cb.name} className="flex items-center justify-between text-sm">
                <span className="text-white/70">{cb.name}</span>
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-1 rounded text-xs ${getCircuitBreakerColor(cb.state)} text-white`}>
                    {cb.state}
                  </span>
                  <span className="text-white/50 text-xs">
                    {cb.failureCount} fails / {cb.successCount} success
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderMetrics = () => {
    if (!metrics) return null;

    return (
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <div className="bg-white/5 backdrop-blur-md rounded-lg p-4 border border-white/10">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-4 h-4 text-green-400" />
            <span className="text-sm text-white/70">Request Rate</span>
          </div>
          <p className="text-2xl font-bold">{metrics.requestRate.toFixed(1)}/s</p>
        </div>

        <div className="bg-white/5 backdrop-blur-md rounded-lg p-4 border border-white/10">
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle className="w-4 h-4 text-red-400" />
            <span className="text-sm text-white/70">Error Rate</span>
          </div>
          <p className="text-2xl font-bold">{(metrics.errorRate * 100).toFixed(2)}%</p>
        </div>

        <div className="bg-white/5 backdrop-blur-md rounded-lg p-4 border border-white/10">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="w-4 h-4 text-blue-400" />
            <span className="text-sm text-white/70">P95 Response</span>
          </div>
          <p className="text-2xl font-bold">{metrics.p95ResponseTime.toFixed(0)}ms</p>
        </div>

        <div className="bg-white/5 backdrop-blur-md rounded-lg p-4 border border-white/10">
          <div className="flex items-center gap-2 mb-2">
            <Users className="w-4 h-4 text-purple-400" />
            <span className="text-sm text-white/70">Active Connections</span>
          </div>
          <p className="text-2xl font-bold">{metrics.activeConnections}</p>
        </div>

        <div className="bg-white/5 backdrop-blur-md rounded-lg p-4 border border-white/10">
          <div className="flex items-center gap-2 mb-2">
            <Zap className="w-4 h-4 text-yellow-400" />
            <span className="text-sm text-white/70">Throughput</span>
          </div>
          <p className="text-2xl font-bold">{metrics.throughput.toFixed(0)}/min</p>
        </div>

        <div className="bg-white/5 backdrop-blur-md rounded-lg p-4 border border-white/10">
          <div className="flex items-center gap-2 mb-2">
            <Database className="w-4 h-4 text-cyan-400" />
            <span className="text-sm text-white/70">Session Tokens</span>
          </div>
          <p className="text-2xl font-bold">{sessionInfo?.tokenCount || 0}</p>
        </div>
      </div>
    );
  };

  const renderSettings = () => {
    return (
      <div className="space-y-4">
        {/* API Configuration */}
        <div className="bg-white/5 backdrop-blur-md rounded-lg p-4 border border-white/10">
          <h3 className="text-lg font-semibold flex items-center gap-2 mb-4">
            <Settings className="w-5 h-5" />
            API Configuration
          </h3>

          <div className="space-y-3">
            {/* API Version */}
            <div className="flex items-center justify-between">
              <label className="text-sm text-white/70">API Version</label>
              <select 
                value={apiVersion}
                onChange={(e) => setApiVersion(e.target.value as 'v1' | 'v2')}
                className="bg-white/10 border border-white/20 rounded px-3 py-1 text-sm"
              >
                <option value="v1">V1 (Legacy)</option>
                <option value="v2">V2 (Enhanced)</option>
              </select>
            </div>

            {/* Optimization Mode */}
            <div className="flex items-center justify-between">
              <label className="text-sm text-white/70">Optimization Mode</label>
              <select 
                value={optimizationMode}
                onChange={(e) => setOptimizationMode(e.target.value as any)}
                className="bg-white/10 border border-white/20 rounded px-3 py-1 text-sm"
                disabled={apiVersion === 'v1'}
              >
                <option value="lite">Lite (Fast)</option>
                <option value="balanced">Balanced</option>
                <option value="quality">Quality (Slow)</option>
              </select>
            </div>

            {/* Swarm Type */}
            <div className="flex items-center justify-between">
              <label className="text-sm text-white/70">Swarm Type</label>
              <select 
                value={swarmType || ''}
                onChange={(e) => setSwarmType(e.target.value || null)}
                className="bg-white/10 border border-white/20 rounded px-3 py-1 text-sm"
                disabled={apiVersion === 'v1'}
              >
                <option value="">None</option>
                <option value="coding-team">Coding Team</option>
                <option value="research-team">Research Team</option>
                <option value="creative-team">Creative Team</option>
                <option value="coding-debate">Coding Debate</option>
              </select>
            </div>

            {/* Memory */}
            <div className="flex items-center justify-between">
              <label className="text-sm text-white/70">Use Memory</label>
              <button
                onClick={() => setUseMemory(!useMemory)}
                className={`p-1 rounded ${useMemory ? 'text-green-400' : 'text-gray-400'}`}
                disabled={apiVersion === 'v1'}
              >
                {useMemory ? <ToggleRight className="w-6 h-6" /> : <ToggleLeft className="w-6 h-6" />}
              </button>
            </div>
          </div>
        </div>

        {/* Feature Flags */}
        <div className="bg-white/5 backdrop-blur-md rounded-lg p-4 border border-white/10">
          <h3 className="text-lg font-semibold flex items-center gap-2 mb-4">
            <GitBranch className="w-5 h-5" />
            Feature Flags
          </h3>

          <div className="space-y-2">
            {featureFlags.map(flag => (
              <div key={flag.name} className="flex items-center justify-between text-sm">
                <span className="text-white/70">{flag.name}</span>
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${flag.enabled ? 'bg-green-400' : 'bg-red-400'}`} />
                  <span className="text-xs text-white/50">{flag.strategy} ({flag.percentage}%)</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Session Info */}
        {sessionInfo && (
          <div className="bg-white/5 backdrop-blur-md rounded-lg p-4 border border-white/10">
            <h3 className="text-lg font-semibold flex items-center gap-2 mb-4">
              <Layers className="w-5 h-5" />
              Session Information
            </h3>

            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-white/70">Session ID</span>
                <span className="text-xs font-mono">{sessionInfo.id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-white/70">Messages</span>
                <span>{sessionInfo.messageCount}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-white/70">Tokens Used</span>
                <span>{sessionInfo.tokenCount}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-white/70">Duration</span>
                <span>{Math.round((Date.now() - new Date(sessionInfo.startTime).getTime()) / 60000)} min</span>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderChat = () => {
    return (
      <div className="flex flex-col h-full">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-white/50 py-8">
              <Bot className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>Start a conversation with the Enhanced AI Orchestra</p>
              <p className="text-sm mt-2">Now with circuit breakers, graceful degradation, and advanced monitoring</p>
            </div>
          )}
          
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
            >
              <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                message.role === 'user' 
                  ? 'bg-blue-500' 
                  : 'bg-gradient-to-r from-[#00e0ff] to-[#ff00c3]'
              }`}>
                {message.role === 'user' ? (
                  <User className="w-5 h-5 text-white" />
                ) : (
                  <Bot className="w-5 h-5 text-white" />
                )}
              </div>
              <div className={`max-w-[70%] ${message.role === 'user' ? 'text-right' : ''}`}>
                <div className={`inline-block p-3 rounded-lg ${
                  message.role === 'user'
                    ? 'bg-blue-500/20 text-white'
                    : 'bg-white/10 text-white'
                }`}>
                  <p className="whitespace-pre-wrap">{message.content}</p>
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <p className="text-xs text-white/50">
                    {message.timestamp.toLocaleTimeString()}
                  </p>
                  {message.executionTime && (
                    <span className="text-xs text-white/30">• {message.executionTime.toFixed(2)}s</span>
                  )}
                  {message.tokens && (
                    <span className="text-xs text-white/30">• {message.tokens} tokens</span>
                  )}
                  {message.correlationId && (
                    <span className="text-xs text-white/20 font-mono">• {message.correlationId.substring(0, 8)}</span>
                  )}
                </div>
              </div>
            </div>
          ))}
          
          {isTyping && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-r from-[#00e0ff] to-[#ff00c3] flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div className="bg-white/10 p-3 rounded-lg">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-white/50 rounded-full animate-bounce" style={{animationDelay: '0ms'}}></span>
                  <span className="w-2 h-2 bg-white/50 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></span>
                  <span className="w-2 h-2 bg-white/50 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="border-t border-white/10 bg-white/5 backdrop-blur-md p-4">
          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={`Ask the Orchestra (${optimizationMode} mode, API ${apiVersion})...`}
              className="flex-1 bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-white/50 focus:outline-none focus:border-[#00e0ff] transition-colors"
              disabled={!isConnected}
            />
            <button
              onClick={sendMessage}
              disabled={!isConnected || !input.trim()}
              className="px-4 py-2 bg-gradient-to-r from-[#00e0ff] to-[#ff00c3] text-white rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-white/5 backdrop-blur-md border-b border-white/10 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-r from-[#00e0ff] to-[#ff00c3] flex items-center justify-center">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="font-semibold">AI Orchestra Dashboard</h3>
              <p className="text-sm text-white/70">
                {isConnected ? (
                  <span className="text-green-400">● Connected</span>
                ) : (
                  <span className="text-red-400">● Disconnected</span>
                )}
                {systemHealth && (
                  <span className="ml-2 text-xs">
                    • {systemHealth.components.degradationLevel.level}
                  </span>
                )}
              </p>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="flex gap-2">
            {(['chat', 'health', 'metrics', 'settings'] as const).map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-3 py-1 rounded text-sm transition-colors ${
                  activeTab === tab 
                    ? 'bg-white/20 text-white' 
                    : 'bg-white/5 text-white/70 hover:bg-white/10'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'chat' && renderChat()}
        {activeTab === 'health' && (
          <div className="p-4">
            {renderHealthStatus()}
          </div>
        )}
        {activeTab === 'metrics' && (
          <div className="p-4">
            {renderMetrics()}
          </div>
        )}
        {activeTab === 'settings' && (
          <div className="p-4">
            {renderSettings()}
          </div>
        )}
      </div>
    </div>
  );
};

export default OrchestratorDashboard;