/**
 * React hook for real-time orchestrator coordination monitoring
 * Provides WebSocket-based live updates for cross-orchestrator coordination
 */

import { useState, useEffect, useRef, useCallback } from 'react';

// ==================== TYPES ====================

interface OrchestratorStatus {
  id: string;
  name: string;
  type: 'sophia' | 'artemis';
  status: 'active' | 'idle' | 'overloaded' | 'error';
  activeTasks: number;
  maxTasks: number;
  queueSize: number;
  performance: number;
  uptime: number;
  domain: string;
  resourceUsage: {
    cpuPercent: number;
    memoryPercent: number;
    ioPercent: number;
  };
  lastHeartbeat: string;
}

interface TaskBridge {
  id: string;
  sourceOrchestrator: string;
  targetOrchestrator: string;
  taskType: string;
  priority: 'high' | 'medium' | 'low';
  status: 'pending' | 'in_transit' | 'delivered' | 'failed';
  contextPreserved: boolean;
  payReadyContext: boolean;
  createdAt: string;
  completedAt?: string;
  processingTimeMs?: number;
}

interface CoordinationMetrics {
  totalTasksProcessed: number;
  taskFlowRatePerMinute: number;
  averageResponseTimeMs: number;
  resourceUtilizationPercent: number;
  bridgeHealthScore: number;
  synchronizationLagMs: number;
  activeBottlenecks: number;
  successRatePercent: number;
  peakThroughput: number;
  lastUpdated: string;
}

interface TaskFlowAnalytics {
  orchestratorUtilization: Record<string, number>;
  taskDistribution: Record<string, number>;
  priorityBreakdown: Record<string, number>;
  processingTimes: Record<string, number[]>;
  bottleneckAnalysis: Record<string, any>;
  flowEfficiency: number;
  resourceAllocation: Record<string, any>;
}

interface ResourceAllocation {
  orchestratorId: string;
  allocatedTasks: number;
  availableCapacity: number;
  utilizationPercent: number;
  queueDepth: number;
  averageWaitTimeMs: number;
  predictedCapacity: number;
  scalingRecommendation?: string;
}

interface PerformanceBottleneck {
  id: string;
  type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  orchestratorAffected: string;
  description: string;
  impactScore: number;
  suggestedAction: string;
  detectedAt: string;
  resolvedAt?: string;
}

interface CoordinationUpdate {
  type: 'initial' | 'update' | 'alert' | 'bottleneck';
  orchestrators?: OrchestratorStatus[];
  taskBridges?: TaskBridge[];
  metrics?: CoordinationMetrics;
  analytics?: TaskFlowAnalytics;
  bottlenecks?: PerformanceBottleneck[];
  timestamp: string;
}

// ==================== HOOK IMPLEMENTATION ====================

interface UseOrchestratorCoordinationResult {
  // Core Data
  orchestrators: OrchestratorStatus[];
  taskBridges: TaskBridge[];
  metrics: CoordinationMetrics | null;
  analytics: TaskFlowAnalytics | null;
  resourceAllocations: ResourceAllocation[];
  bottlenecks: PerformanceBottleneck[];

  // Connection State
  isConnected: boolean;
  isLoading: boolean;
  error: string | null;
  connectionAttempts: number;

  // Actions
  refreshData: () => Promise<void>;
  acknowledgeBottleneck: (bottleneckId: string) => Promise<void>;
  triggerHealthCheck: () => Promise<void>;

  // Real-time control
  toggleRealTimeUpdates: () => void;
  setUpdateInterval: (intervalMs: number) => void;
}

const useOrchestratorCoordination = (
  autoConnect: boolean = true,
  updateIntervalMs: number = 5000
): UseOrchestratorCoordinationResult => {
  // ==================== STATE ====================

  const [orchestrators, setOrchestrators] = useState<OrchestratorStatus[]>([]);
  const [taskBridges, setTaskBridges] = useState<TaskBridge[]>([]);
  const [metrics, setMetrics] = useState<CoordinationMetrics | null>(null);
  const [analytics, setAnalytics] = useState<TaskFlowAnalytics | null>(null);
  const [resourceAllocations, setResourceAllocations] = useState<ResourceAllocation[]>([]);
  const [bottlenecks, setBottlenecks] = useState<PerformanceBottleneck[]>([]);

  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [connectionAttempts, setConnectionAttempts] = useState<number>(0);
  const [realTimeEnabled, setRealTimeEnabled] = useState<boolean>(true);

  // Refs for connection management
  const websocketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const healthCheckIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // ==================== API UTILITIES ====================

  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8001/api';
  const WS_BASE = process.env.NEXT_PUBLIC_WS_BASE || 'ws://localhost:8001/api';

  const fetchWithAuth = async (endpoint: string, options: RequestInit = {}) => {
    const token = localStorage.getItem('auth_token');
    return fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': token ? `Bearer ${token}` : '',
        'Content-Type': 'application/json',
      },
    });
  };

  // ==================== DATA FETCHING ====================

  const fetchOrchestratorStatus = useCallback(async (): Promise<OrchestratorStatus[]> => {
    const response = await fetchWithAuth('/orchestrator-coordination/status');
    if (!response.ok) {
      throw new Error(`Failed to fetch orchestrator status: ${response.statusText}`);
    }
    const data = await response.json();
    return data.map((orch: any) => ({
      ...orch,
      resourceUsage: orch.resource_usage || {},
      activeTasks: orch.active_tasks,
      maxTasks: orch.max_tasks,
      queueSize: orch.queue_size,
      lastHeartbeat: orch.last_heartbeat,
      performance: orch.performance_score
    }));
  }, []);

  const fetchTaskBridges = useCallback(async (): Promise<TaskBridge[]> => {
    const response = await fetchWithAuth('/orchestrator-coordination/task-bridges');
    if (!response.ok) {
      throw new Error(`Failed to fetch task bridges: ${response.statusText}`);
    }
    const data = await response.json();
    return data.map((bridge: any) => ({
      ...bridge,
      sourceOrchestrator: bridge.source_orchestrator,
      targetOrchestrator: bridge.target_orchestrator,
      taskType: bridge.task_type,
      contextPreserved: bridge.context_preserved,
      payReadyContext: bridge.pay_ready_context,
      createdAt: bridge.created_at,
      completedAt: bridge.completed_at,
      processingTimeMs: bridge.processing_time_ms
    }));
  }, []);

  const fetchMetrics = useCallback(async (timeRange: string = '1h'): Promise<CoordinationMetrics> => {
    const response = await fetchWithAuth(`/orchestrator-coordination/metrics?time_range=${timeRange}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch coordination metrics: ${response.statusText}`);
    }
    const data = await response.json();
    return {
      ...data,
      totalTasksProcessed: data.total_tasks_processed,
      taskFlowRatePerMinute: data.task_flow_rate_per_minute,
      averageResponseTimeMs: data.average_response_time_ms,
      resourceUtilizationPercent: data.resource_utilization_percent,
      bridgeHealthScore: data.bridge_health_score,
      synchronizationLagMs: data.synchronization_lag_ms,
      activeBottlenecks: data.active_bottlenecks,
      successRatePercent: data.success_rate_percent,
      peakThroughput: data.peak_throughput,
      lastUpdated: data.last_updated
    };
  }, []);

  const fetchAnalytics = useCallback(async (timeRange: string = '1h'): Promise<TaskFlowAnalytics> => {
    const response = await fetchWithAuth(`/orchestrator-coordination/analytics?time_range=${timeRange}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch analytics: ${response.statusText}`);
    }
    const data = await response.json();
    return {
      ...data,
      orchestratorUtilization: data.orchestrator_utilization,
      taskDistribution: data.task_distribution,
      priorityBreakdown: data.priority_breakdown,
      processingTimes: data.processing_times,
      bottleneckAnalysis: data.bottleneck_analysis,
      flowEfficiency: data.flow_efficiency,
      resourceAllocation: data.resource_allocation
    };
  }, []);

  const fetchResourceAllocations = useCallback(async (): Promise<ResourceAllocation[]> => {
    const response = await fetchWithAuth('/orchestrator-coordination/resource-allocation');
    if (!response.ok) {
      throw new Error(`Failed to fetch resource allocations: ${response.statusText}`);
    }
    const data = await response.json();
    return data.map((allocation: any) => ({
      ...allocation,
      orchestratorId: allocation.orchestrator_id,
      allocatedTasks: allocation.allocated_tasks,
      availableCapacity: allocation.available_capacity,
      utilizationPercent: allocation.utilization_percent,
      queueDepth: allocation.queue_depth,
      averageWaitTimeMs: allocation.average_wait_time_ms,
      predictedCapacity: allocation.predicted_capacity,
      scalingRecommendation: allocation.scaling_recommendation
    }));
  }, []);

  const fetchBottlenecks = useCallback(async (): Promise<PerformanceBottleneck[]> => {
    const response = await fetchWithAuth('/orchestrator-coordination/bottlenecks');
    if (!response.ok) {
      throw new Error(`Failed to fetch bottlenecks: ${response.statusText}`);
    }
    const data = await response.json();
    return data.map((bottleneck: any) => ({
      ...bottleneck,
      orchestratorAffected: bottleneck.orchestrator_affected,
      impactScore: bottleneck.impact_score,
      suggestedAction: bottleneck.suggested_action,
      detectedAt: bottleneck.detected_at,
      resolvedAt: bottleneck.resolved_at
    }));
  }, []);

  // ==================== INITIAL DATA LOAD ====================

  const refreshData = useCallback(async () => {
    if (!realTimeEnabled) return;

    setIsLoading(true);
    setError(null);

    try {
      const [
        orchestratorsData,
        bridgesData,
        metricsData,
        analyticsData,
        allocationsData,
        bottlenecksData
      ] = await Promise.all([
        fetchOrchestratorStatus(),
        fetchTaskBridges(),
        fetchMetrics(),
        fetchAnalytics(),
        fetchResourceAllocations(),
        fetchBottlenecks()
      ]);

      setOrchestrators(orchestratorsData);
      setTaskBridges(bridgesData);
      setMetrics(metricsData);
      setAnalytics(analyticsData);
      setResourceAllocations(allocationsData);
      setBottlenecks(bottlenecksData);

      setError(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      console.error('Failed to refresh coordination data:', err);
    } finally {
      setIsLoading(false);
    }
  }, [
    fetchOrchestratorStatus,
    fetchTaskBridges,
    fetchMetrics,
    fetchAnalytics,
    fetchResourceAllocations,
    fetchBottlenecks,
    realTimeEnabled
  ]);

  // ==================== WEBSOCKET CONNECTION ====================

  const connectWebSocket = useCallback(() => {
    if (websocketRef.current?.readyState === WebSocket.OPEN) return;
    if (!realTimeEnabled) return;

    const token = localStorage.getItem('auth_token');
    const wsUrl = `${WS_BASE}/orchestrator-coordination/ws${token ? `?token=${token}` : ''}`;

    websocketRef.current = new WebSocket(wsUrl);

    websocketRef.current.onopen = () => {
      console.log('WebSocket connected to orchestrator coordination');
      setIsConnected(true);
      setConnectionAttempts(0);
      setError(null);
    };

    websocketRef.current.onmessage = (event) => {
      try {
        const update: CoordinationUpdate = JSON.parse(event.data);

        switch (update.type) {
          case 'initial':
          case 'update':
            if (update.orchestrators) setOrchestrators(update.orchestrators);
            if (update.taskBridges) setTaskBridges(update.taskBridges);
            if (update.metrics) setMetrics(update.metrics);
            if (update.analytics) setAnalytics(update.analytics);
            break;

          case 'bottleneck':
            if (update.bottlenecks) {
              setBottlenecks(prev => [...prev, ...update.bottlenecks!]);
            }
            break;

          case 'alert':
            // Handle coordination alerts
            console.warn('Coordination alert:', update);
            break;
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    websocketRef.current.onclose = () => {
      console.log('WebSocket disconnected from orchestrator coordination');
      setIsConnected(false);

      if (realTimeEnabled && connectionAttempts < 5) {
        setConnectionAttempts(prev => prev + 1);
        reconnectTimeoutRef.current = setTimeout(() => {
          connectWebSocket();
        }, Math.min(1000 * Math.pow(2, connectionAttempts), 30000));
      }
    };

    websocketRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError('WebSocket connection failed');
    };
  }, [realTimeEnabled, connectionAttempts]);

  // ==================== ACTION HANDLERS ====================

  const acknowledgeBottleneck = useCallback(async (bottleneckId: string): Promise<void> => {
    try {
      await fetchWithAuth(`/orchestrator-coordination/bottlenecks/${bottleneckId}/acknowledge`, {
        method: 'POST'
      });

      setBottlenecks(prev => prev.filter(b => b.id !== bottleneckId));
    } catch (err) {
      console.error('Failed to acknowledge bottleneck:', err);
      throw err;
    }
  }, []);

  const triggerHealthCheck = useCallback(async (): Promise<void> => {
    try {
      await fetchWithAuth('/orchestrator-coordination/bridge-health-check', {
        method: 'POST'
      });

      // Refresh data after health check
      await refreshData();
    } catch (err) {
      console.error('Failed to trigger health check:', err);
      throw err;
    }
  }, [refreshData]);

  const toggleRealTimeUpdates = useCallback(() => {
    setRealTimeEnabled(prev => {
      const newValue = !prev;
      if (!newValue && websocketRef.current) {
        websocketRef.current.close();
      } else if (newValue) {
        connectWebSocket();
      }
      return newValue;
    });
  }, [connectWebSocket]);

  const setUpdateInterval = useCallback((intervalMs: number) => {
    if (healthCheckIntervalRef.current) {
      clearInterval(healthCheckIntervalRef.current);
    }

    if (intervalMs > 0) {
      healthCheckIntervalRef.current = setInterval(refreshData, intervalMs);
    }
  }, [refreshData]);

  // ==================== EFFECTS ====================

  // Initial connection and cleanup
  useEffect(() => {
    if (autoConnect) {
      refreshData();

      if (realTimeEnabled) {
        connectWebSocket();
      }

      // Set up periodic refresh as fallback
      setUpdateInterval(updateIntervalMs);
    }

    return () => {
      if (websocketRef.current) {
        websocketRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (healthCheckIntervalRef.current) {
        clearInterval(healthCheckIntervalRef.current);
      }
    };
  }, [autoConnect, realTimeEnabled, updateIntervalMs, connectWebSocket, refreshData, setUpdateInterval]);

  // ==================== RETURN ====================

  return {
    // Core Data
    orchestrators,
    taskBridges,
    metrics,
    analytics,
    resourceAllocations,
    bottlenecks,

    // Connection State
    isConnected,
    isLoading,
    error,
    connectionAttempts,

    // Actions
    refreshData,
    acknowledgeBottleneck,
    triggerHealthCheck,

    // Real-time control
    toggleRealTimeUpdates,
    setUpdateInterval,
  };
};

export default useOrchestratorCoordination;
