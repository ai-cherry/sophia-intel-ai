
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
