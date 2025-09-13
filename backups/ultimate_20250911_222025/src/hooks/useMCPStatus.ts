/**
 * React hook for real-time MCP server status monitoring
 * Provides WebSocket-based live updates for MCP server health and metrics
 */

import { useState, useEffect, useRef, useCallback } from 'react';

// ==================== TYPES ====================

interface MCPServerHealth {
  server_name: string;
  server_type: string;
  domain: string;
  status: 'operational' | 'degraded' | 'down' | 'unknown';
  uptime_percentage: number;
  response_time_ms: number;
  throughput_ops_per_sec: number;
  error_rate: number;
  last_activity: string;
  connections: {
    active: number;
    max: number;
    utilization: number;
  };
  business_context?: string;
}

interface MCPDomainSummary {
  domain: string;
  total_servers: number;
  operational_servers: number;
  degraded_servers: number;
  down_servers: number;
  total_connections: number;
  avg_response_time_ms: number;
  overall_health_score: number;
  pay_ready_context?: {
    processing_volume_today?: number;
    market_share?: number;
    properties_under_management?: number;
    compliance_score?: number;
  };
}

interface MythologyAgent {
  id: string;
  name: string;
  domain: string;
  title: string;
  assigned_mcp_servers: string[];
  status: string;
  primary_metric: {
    label: string;
    value: string;
    trend: 'up' | 'down' | 'stable';
  };
  pay_ready_context?: string;
}

interface MCPSystemOverview {
  timestamp: string;
  overall_status: 'operational' | 'degraded' | 'critical';
  total_servers: number;
  healthy_servers: number;
  domain_summaries: MCPDomainSummary[];
  system_metrics: {
    total_active_connections: number;
    server_utilization: Record<string, any>;
    partition_count: number;
    websocket_connections: number;
    uptime_hours: number;
    last_restart: string;
  };
  mythology_agents: MythologyAgent[];
}

interface MCPStatusState {
  overview: MCPSystemOverview | null;
  servers: MCPServerHealth[];
  domainSummaries: Record<string, MCPDomainSummary>;
  mythologyAgents: MythologyAgent[];
  isConnected: boolean;
  isLoading: boolean;
  error: string | null;
  lastUpdate: Date | null;
}

interface UseMCPStatusOptions {
  domain?: string;
  autoConnect?: boolean;
  reconnectInterval?: number;
  subscriptions?: string[];
}

// ==================== CUSTOM HOOK ====================

export const useMCPStatus = (options: UseMCPStatusOptions = {}) => {
  const {
    domain,
    autoConnect = true,
    reconnectInterval = 5000,
    subscriptions = []
  } = options;

  const [state, setState] = useState<MCPStatusState>({
    overview: null,
    servers: [],
    domainSummaries: {},
    mythologyAgents: [],
    isConnected: false,
    isLoading: true,
    error: null,
    lastUpdate: null
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const clientId = useRef<string>(`mcp_client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);

  // ==================== WEBSOCKET MANAGEMENT ====================

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }));

      const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/mcp-status/ws/${clientId.current}`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('MCP Status WebSocket connected');
        setState(prev => ({ ...prev, isConnected: true, isLoading: false, error: null }));

        // Subscribe to requested channels
        subscriptions.forEach(subscription => {
          ws.send(JSON.stringify({
            type: 'subscribe',
            channel: subscription
          }));
        });

        // Domain-specific subscriptions
        if (domain) {
          ws.send(JSON.stringify({
            type: 'subscribe',
            channel: `mcp_domain_${domain}`
          }));
        }
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleWebSocketMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onclose = (event) => {
        console.log('MCP Status WebSocket disconnected:', event.code, event.reason);
        setState(prev => ({ ...prev, isConnected: false }));

        // Attempt to reconnect unless it was a clean close
        if (event.code !== 1000 && autoConnect) {
          scheduleReconnect();
        }
      };

      ws.onerror = (error) => {
        console.error('MCP Status WebSocket error:', error);
        setState(prev => ({
          ...prev,
          error: 'WebSocket connection failed',
          isConnected: false,
          isLoading: false
        }));
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setState(prev => ({
        ...prev,
        error: 'Failed to establish connection',
        isLoading: false
      }));
    }
  }, [domain, subscriptions, autoConnect]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect');
      wsRef.current = null;
    }

    setState(prev => ({ ...prev, isConnected: false }));
  }, []);

  const scheduleReconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    reconnectTimeoutRef.current = setTimeout(() => {
      console.log('Attempting to reconnect MCP Status WebSocket...');
      connect();
    }, reconnectInterval);
  }, [connect, reconnectInterval]);

  // ==================== MESSAGE HANDLING ====================

  const handleWebSocketMessage = useCallback((message: any) => {
    setState(prev => ({ ...prev, lastUpdate: new Date() }));

    switch (message.type) {
      case 'mcp_status_update':
        if (message.data) {
          setState(prev => ({
            ...prev,
            overview: message.data,
            domainSummaries: message.data.domain_summaries?.reduce((acc: any, summary: MCPDomainSummary) => {
              acc[summary.domain] = summary;
              return acc;
            }, {}) || prev.domainSummaries,
            mythologyAgents: message.data.mythology_agents || prev.mythologyAgents
          }));
        }
        break;

      case 'mcp_server_update':
        if (message.server_data) {
          setState(prev => ({
            ...prev,
            servers: prev.servers.map(server =>
              server.server_name === message.server_data.server_name
                ? { ...server, ...message.server_data }
                : server
            )
          }));
        }
        break;

      case 'mcp_domain_update':
        if (message.domain_data && message.domain) {
          setState(prev => ({
            ...prev,
            domainSummaries: {
              ...prev.domainSummaries,
              [message.domain]: message.domain_data
            }
          }));
        }
        break;

      case 'mcp_mythology_update':
        if (message.agents_data) {
          setState(prev => ({
            ...prev,
            mythologyAgents: message.agents_data
          }));
        }
        break;

      case 'server_restart':
        console.log('Server restart event:', message.server_name);
        break;

      case 'connected':
        console.log('MCP Status WebSocket handshake complete');
        break;

      case 'pong':
        // Heartbeat response
        break;

      default:
        console.log('Unknown MCP status message type:', message.type);
    }
  }, []);

  // ==================== API METHODS ====================

  const fetchInitialData = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }));

      // Fetch system overview
      const overviewResponse = await fetch('/api/mcp-status/');
      if (!overviewResponse.ok) {
        throw new Error('Failed to fetch MCP system overview');
      }
      const overview = await overviewResponse.json();

      // Fetch servers if domain filter is applied
      let servers: MCPServerHealth[] = [];
      if (domain) {
        const serversResponse = await fetch(`/api/mcp-status/servers?domain=${domain}`);
        if (serversResponse.ok) {
          servers = await serversResponse.json();
        }
      }

      setState(prev => ({
        ...prev,
        overview,
        servers,
        domainSummaries: overview.domain_summaries?.reduce((acc: any, summary: MCPDomainSummary) => {
          acc[summary.domain] = summary;
          return acc;
        }, {}) || {},
        mythologyAgents: overview.mythology_agents || [],
        isLoading: false
      }));

    } catch (error) {
      console.error('Failed to fetch initial MCP data:', error);
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to fetch data',
        isLoading: false
      }));
    }
  }, [domain]);

  const refreshData = useCallback(async () => {
    await fetchInitialData();
  }, [fetchInitialData]);

  const subscribeToChannel = useCallback((channel: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'subscribe',
        channel
      }));
    }
  }, []);

  const unsubscribeFromChannel = useCallback((channel: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'unsubscribe',
        channel
      }));
    }
  }, []);

  const restartServer = useCallback(async (serverName: string) => {
    try {
      const response = await fetch(`/api/mcp-status/server/${serverName}/restart`, {
        method: 'POST'
      });

      if (!response.ok) {
        throw new Error('Failed to restart server');
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to restart server:', error);
      throw error;
    }
  }, []);

  // ==================== LIFECYCLE ====================

  useEffect(() => {
    // Fetch initial data
    fetchInitialData();

    // Connect WebSocket if auto-connect is enabled
    if (autoConnect) {
      connect();
    }

    // Cleanup
    return () => {
      disconnect();
    };
  }, [fetchInitialData, connect, disconnect, autoConnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  // ==================== COMPUTED VALUES ====================

  const healthSummary = {
    overall_health: state.overview?.overall_status || 'unknown',
    total_servers: state.overview?.total_servers || 0,
    healthy_servers: state.overview?.healthy_servers || 0,
    health_percentage: state.overview ?
      Math.round((state.overview.healthy_servers / state.overview.total_servers) * 100) : 0
  };

  const domainHealth = domain ? state.domainSummaries[domain] : null;

  const criticalServers = state.servers.filter(server =>
    server.status === 'down' || server.status === 'degraded'
  );

  const mythologyAgentsByDomain = state.mythologyAgents.reduce((acc, agent) => {
    if (!acc[agent.domain]) acc[agent.domain] = [];
    acc[agent.domain].push(agent);
    return acc;
  }, {} as Record<string, MythologyAgent[]>);

  // ==================== RETURN VALUE ====================

  return {
    // State
    ...state,
    healthSummary,
    domainHealth,
    criticalServers,
    mythologyAgentsByDomain,

    // Methods
    connect,
    disconnect,
    refreshData,
    subscribeToChannel,
    unsubscribeFromChannel,
    restartServer,

    // Computed
    isHealthy: state.overview?.overall_status === 'operational',
    needsAttention: criticalServers.length > 0,
    connectionStatus: state.isConnected ? 'connected' : state.isLoading ? 'connecting' : 'disconnected'
  };
};

export default useMCPStatus;
