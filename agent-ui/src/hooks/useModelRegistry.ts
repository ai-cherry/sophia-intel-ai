/**
 * React hook for Model Registry management
 * Provides real-time provider status, cost tracking, and performance metrics
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { ApiClient } from '@/lib/api/client';
import { useUnifiedStore } from '@/lib/state/unifiedStore';

// Types
interface ProviderHealthStatus {
  provider: string;
  status: 'active' | 'degraded' | 'offline';
  last_success: string;
  success_rate: number;
  avg_latency_ms: number;
  error_count: number;
  cost_per_1k_tokens: number;
}

interface VirtualKeyConfig {
  provider: string;
  virtual_key: string;
  models: string[];
  fallback_providers: string[];
  max_tokens: number;
  temperature: number;
  retry_count: number;
}

interface CostAnalytics {
  daily_cost: number;
  weekly_cost: number;
  monthly_cost: number;
  cost_by_provider: Record<string, number>;
  token_usage: Record<string, number>;
  request_count: number;
}

interface FallbackChainConfig {
  primary_provider: string;
  fallback_chain: string[];
  load_balance_weights: Record<string, number>;
  routing_strategy: string;
}

interface PerformanceMetrics {
  provider: string;
  latency_p50: number;
  latency_p95: number;
  latency_p99: number;
  throughput_rpm: number;
  error_rate: number;
  uptime_percentage: number;
}

interface RoutingStrategy {
  name: string;
  display_name: string;
  description: string;
}

interface ModelTestRequest {
  provider: string;
  model?: string;
  test_message: string;
}

interface ModelTestResult {
  provider: string;
  model?: string;
  healthy: boolean;
  timestamp: string;
  test_message: string;
  status: string;
  latency_ms?: number;
  error?: string;
}

interface UseModelRegistryReturn {
  // Data
  providers: ProviderHealthStatus[];
  virtualKeys: VirtualKeyConfig[];
  costAnalytics: CostAnalytics | null;
  fallbackChains: Record<string, FallbackChainConfig>;
  performanceMetrics: PerformanceMetrics[];
  routingStrategies: RoutingStrategy[];

  // Loading states
  isLoading: boolean;
  isTestingModel: boolean;

  // Error states
  error: string | null;

  // Actions
  refreshProviders: () => Promise<void>;
  updateVirtualKey: (provider: string, config: VirtualKeyConfig) => Promise<void>;
  updateFallbackChain: (provider: string, config: FallbackChainConfig) => Promise<void>;
  testModel: (request: ModelTestRequest) => Promise<ModelTestResult>;

  // Real-time connection
  isConnected: boolean;
  lastUpdate: string | null;
}

const API_BASE = '/api/model-registry';

export const useModelRegistry = (): UseModelRegistryReturn => {
  // State
  const [providers, setProviders] = useState<ProviderHealthStatus[]>([]);
  const [virtualKeys, setVirtualKeys] = useState<VirtualKeyConfig[]>([]);
  const [costAnalytics, setCostAnalytics] = useState<CostAnalytics | null>(null);
  const [fallbackChains, setFallbackChains] = useState<Record<string, FallbackChainConfig>>({});
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetrics[]>([]);
  const [routingStrategies, setRoutingStrategies] = useState<RoutingStrategy[]>([]);

  const [isLoading, setIsLoading] = useState(true);
  const [isTestingModel, setIsTestingModel] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // WebSocket connection
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // WebSocket connection management
  const connectWebSocket = useCallback(() => {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}${API_BASE}/ws`;

      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('Model Registry WebSocket connected');
        setIsConnected(true);
        setError(null);

        // Clear reconnect timeout
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          setLastUpdate(message.timestamp);

          switch (message.type) {
            case 'provider_health_update':
              setProviders(message.data);
              break;
            case 'cost_analytics_update':
              setCostAnalytics(message.data);
              break;
            default:
              console.log('Unknown WebSocket message type:', message.type);
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      wsRef.current.onclose = () => {
        console.log('Model Registry WebSocket disconnected');
        setIsConnected(false);

        // Schedule reconnection
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('Attempting to reconnect WebSocket...');
          connectWebSocket();
        }, 5000);
      };

      wsRef.current.onerror = (err) => {
        console.error('Model Registry WebSocket error:', err);
        setError('WebSocket connection failed');
      };

    } catch (err) {
      console.error('Error creating WebSocket connection:', err);
      setError('Failed to establish real-time connection');
    }
  }, []);

  // API functions
  const fetchProviders = async (): Promise<ProviderHealthStatus[]> => {
    const client = new ApiClient('', (cat, ms) => useUnifiedStore.getState().updateLatency(cat, ms));
    return client.get<ProviderHealthStatus[]>(`${API_BASE}/providers`, { category: 'api.modelRegistry.providers' });
  };

  const fetchVirtualKeys = async (): Promise<VirtualKeyConfig[]> => {
    const client = new ApiClient('', (cat, ms) => useUnifiedStore.getState().updateLatency(cat, ms));
    return client.get<VirtualKeyConfig[]>(`${API_BASE}/virtual-keys`, { category: 'api.modelRegistry.virtualKeys' });
  };

  const fetchCostAnalytics = async (): Promise<CostAnalytics> => {
    const response = await fetch(`${API_BASE}/cost-analytics`);
    if (!response.ok) {
      throw new Error(`Failed to fetch cost analytics: ${response.statusText}`);
    }
    return response.json();
  };

  const fetchFallbackChains = async (): Promise<Record<string, FallbackChainConfig>> => {
    const response = await fetch(`${API_BASE}/fallback-chains`);
    if (!response.ok) {
      throw new Error(`Failed to fetch fallback chains: ${response.statusText}`);
    }
    return response.json();
  };

  const fetchPerformanceMetrics = async (): Promise<PerformanceMetrics[]> => {
    const response = await fetch(`${API_BASE}/performance-metrics`);
    if (!response.ok) {
      throw new Error(`Failed to fetch performance metrics: ${response.statusText}`);
    }
    return response.json();
  };

  const fetchRoutingStrategies = async (): Promise<{ strategies: RoutingStrategy[] }> => {
    const response = await fetch(`${API_BASE}/routing-strategies`);
    if (!response.ok) {
      throw new Error(`Failed to fetch routing strategies: ${response.statusText}`);
    }
    return response.json();
  };

  // Action functions
  const refreshProviders = useCallback(async () => {
    try {
      setError(null);
      const newProviders = await fetchProviders();
      setProviders(newProviders);
    } catch (err) {
      console.error('Error refreshing providers:', err);
      setError(err instanceof Error ? err.message : 'Failed to refresh providers');
    }
  }, []);

  const updateVirtualKey = useCallback(async (provider: string, config: VirtualKeyConfig) => {
    try {
      setError(null);
      const response = await fetch(`${API_BASE}/virtual-keys/${provider}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        throw new Error(`Failed to update virtual key: ${response.statusText}`);
      }

      // Refresh virtual keys
      const newVirtualKeys = await fetchVirtualKeys();
      setVirtualKeys(newVirtualKeys);

      // Refresh providers to update status
      await refreshProviders();

    } catch (err) {
      console.error('Error updating virtual key:', err);
      setError(err instanceof Error ? err.message : 'Failed to update virtual key');
      throw err;
    }
  }, [refreshProviders]);

  const updateFallbackChain = useCallback(async (provider: string, config: FallbackChainConfig) => {
    try {
      setError(null);
      const response = await fetch(`${API_BASE}/fallback-chains/${provider}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        throw new Error(`Failed to update fallback chain: ${response.statusText}`);
      }

      // Refresh fallback chains
      const newFallbackChains = await fetchFallbackChains();
      setFallbackChains(newFallbackChains);

    } catch (err) {
      console.error('Error updating fallback chain:', err);
      setError(err instanceof Error ? err.message : 'Failed to update fallback chain');
      throw err;
    }
  }, []);

  const testModel = useCallback(async (request: ModelTestRequest): Promise<ModelTestResult> => {
    try {
      setIsTestingModel(true);
      setError(null);

      const response = await fetch(`${API_BASE}/test-model`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`Failed to test model: ${response.statusText}`);
      }

      const result = await response.json();

      // Refresh providers to update status after test
      await refreshProviders();

      return result;

    } catch (err) {
      console.error('Error testing model:', err);
      setError(err instanceof Error ? err.message : 'Failed to test model');
      throw err;
    } finally {
      setIsTestingModel(false);
    }
  }, [refreshProviders]);

  // Initial data loading
  const loadInitialData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const [
        providersData,
        virtualKeysData,
        costAnalyticsData,
        fallbackChainsData,
        performanceMetricsData,
        routingStrategiesData,
      ] = await Promise.allSettled([
        fetchProviders(),
        fetchVirtualKeys(),
        fetchCostAnalytics(),
        fetchFallbackChains(),
        fetchPerformanceMetrics(),
        fetchRoutingStrategies(),
      ]);

      // Process results
      if (providersData.status === 'fulfilled') {
        setProviders(providersData.value);
      } else {
        console.error('Failed to load providers:', providersData.reason);
      }

      if (virtualKeysData.status === 'fulfilled') {
        setVirtualKeys(virtualKeysData.value);
      } else {
        console.error('Failed to load virtual keys:', virtualKeysData.reason);
      }

      if (costAnalyticsData.status === 'fulfilled') {
        setCostAnalytics(costAnalyticsData.value);
      } else {
        console.error('Failed to load cost analytics:', costAnalyticsData.reason);
      }

      if (fallbackChainsData.status === 'fulfilled') {
        setFallbackChains(fallbackChainsData.value);
      } else {
        console.error('Failed to load fallback chains:', fallbackChainsData.reason);
      }

      if (performanceMetricsData.status === 'fulfilled') {
        setPerformanceMetrics(performanceMetricsData.value);
      } else {
        console.error('Failed to load performance metrics:', performanceMetricsData.reason);
      }

      if (routingStrategiesData.status === 'fulfilled') {
        setRoutingStrategies(routingStrategiesData.value.strategies);
      } else {
        console.error('Failed to load routing strategies:', routingStrategiesData.reason);
      }

    } catch (err) {
      console.error('Error loading initial data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Initialize
  useEffect(() => {
    loadInitialData();
    connectWebSocket();

    return () => {
      // Cleanup WebSocket
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [loadInitialData, connectWebSocket]);

  // Periodic refresh (every 5 minutes when not connected to WebSocket)
  useEffect(() => {
    if (!isConnected) {
      const interval = setInterval(() => {
        loadInitialData();
      }, 5 * 60 * 1000); // 5 minutes

      return () => clearInterval(interval);
    }
  }, [isConnected, loadInitialData]);

  return {
    // Data
    providers,
    virtualKeys,
    costAnalytics,
    fallbackChains,
    performanceMetrics,
    routingStrategies,

    // Loading states
    isLoading,
    isTestingModel,

    // Error states
    error,

    // Actions
    refreshProviders,
    updateVirtualKey,
    updateFallbackChain,
    testModel,

    // Real-time connection
    isConnected,
    lastUpdate,
  };
};
