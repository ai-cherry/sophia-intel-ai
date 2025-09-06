/**
 * useSwarmTemplates - React Hook for Swarm Template Management
 * Provides template management, code generation, deployment tracking, and real-time monitoring
 */

import { useState, useEffect, useCallback, useRef } from 'react';

// ==============================================================================
// TYPE DEFINITIONS
// ==============================================================================

interface SwarmTemplate {
  id: string;
  name: string;
  description: string;
  topology: 'sequential' | 'star' | 'committee' | 'hierarchical';
  domain: 'sophia_business' | 'artemis_technical' | 'pay_ready' | 'cross_domain';
  category: string;
  agent_count: number;
  estimated_duration: string;
  complexity_level: number;
  pay_ready_optimized: boolean;
  resource_limits: Record<string, any>;
  success_criteria: Record<string, any>;
  example_use_cases: string[];
}

interface AgentConfig {
  template_name: string;
  role: string;
  factory_type: 'sophia' | 'artemis';
  weight: number;
  required: boolean;
  custom_config: Record<string, any>;
}

interface TemplateDetails extends SwarmTemplate {
  agents: AgentConfig[];
  coordination_config: Record<string, any>;
}

interface CodeGenerationResult {
  success: boolean;
  code?: string;
  metadata?: Record<string, any>;
  file_path?: string;
  errors: string[];
}

interface DeploymentRequest {
  template_id: string;
  swarm_name: string;
  custom_config?: Record<string, any>;
  agent_overrides?: Record<string, any>;
  auto_deploy?: boolean;
  monitoring_enabled?: boolean;
  notifications_enabled?: boolean;
}

interface DeploymentResult {
  success: boolean;
  swarm_id?: string;
  deployment_status: string;
  metadata?: Record<string, any>;
  errors: string[];
}

interface SwarmStatus {
  swarm_id: string;
  status: string;
  metadata: Record<string, any>;
  created_at: string;
  last_updated: string;
}

interface DeploymentUpdate {
  type: 'deployment_update' | 'deployment_list' | 'keepalive';
  deployment_id?: string;
  status?: string;
  metadata?: Record<string, any>;
  deployments?: Array<{
    deployment_id: string;
    status: string;
    swarm_name: string;
  }>;
  timestamp: string;
}

interface TemplateSummary {
  total_templates: number;
  by_domain: Record<string, number>;
  by_topology: Record<string, number>;
  by_category: Record<string, number>;
  by_complexity: Record<string, number>;
  pay_ready_count: number;
}

interface UseSwarmTemplatesReturn {
  // Template Management
  templates: SwarmTemplate[] | null;
  templateDetails: TemplateDetails | null;
  templateSummary: TemplateSummary | null;
  loading: boolean;
  error: string | null;

  // Actions
  fetchTemplates: (filters?: TemplateFilters) => Promise<void>;
  fetchTemplateDetails: (templateId: string) => Promise<void>;
  generateCode: (templateId: string, customConfig?: Record<string, any>, swarmName?: string) => Promise<CodeGenerationResult>;
  validateTemplate: (templateId: string, customConfig?: Record<string, any>) => Promise<ValidationResult>;
  deploySwarm: (request: DeploymentRequest) => Promise<DeploymentResult>;

  // Monitoring
  deployments: DeploymentStatus[];
  getSwarmStatus: (swarmId: string) => Promise<SwarmStatus>;
  cancelDeployment: (deploymentId: string) => Promise<boolean>;

  // Real-time updates
  isConnected: boolean;
  connectionError: string | null;
}

interface TemplateFilters {
  domain?: string;
  category?: string;
  topology?: string;
  pay_ready_only?: boolean;
  max_complexity?: number;
}

interface ValidationResult {
  success: boolean;
  valid: boolean;
  validation_results: Record<string, any>;
  timestamp: string;
}

interface DeploymentStatus {
  deployment_id: string;
  swarm_name: string;
  template_id: string;
  status: string;
  created_at: string;
}

// ==============================================================================
// HOOK IMPLEMENTATION
// ==============================================================================

const useSwarmTemplates = (): UseSwarmTemplatesReturn => {
  // State management
  const [templates, setTemplates] = useState<SwarmTemplate[] | null>(null);
  const [templateDetails, setTemplateDetails] = useState<TemplateDetails | null>(null);
  const [templateSummary, setTemplateSummary] = useState<TemplateSummary | null>(null);
  const [deployments, setDeployments] = useState<DeploymentStatus[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // WebSocket state
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Base API URL
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

  // ==============================================================================
  // UTILITY FUNCTIONS
  // ==============================================================================

  const apiRequest = async (endpoint: string, options: RequestInit = {}) => {
    try {
      const response = await fetch(`${API_BASE}/api/swarm-templates${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      throw err instanceof Error ? err : new Error('Request failed');
    }
  };

  // ==============================================================================
  // TEMPLATE MANAGEMENT FUNCTIONS
  // ==============================================================================

  const fetchTemplates = useCallback(async (filters: TemplateFilters = {}) => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (filters.domain) params.append('domain', filters.domain);
      if (filters.category) params.append('category', filters.category);
      if (filters.topology) params.append('topology', filters.topology);
      if (filters.pay_ready_only) params.append('pay_ready_only', 'true');
      if (filters.max_complexity) params.append('max_complexity', filters.max_complexity.toString());

      const queryString = params.toString();
      const endpoint = `/list${queryString ? `?${queryString}` : ''}`;

      const data = await apiRequest(endpoint);
      setTemplates(data);

      // Also fetch summary if we don't have it
      if (!templateSummary) {
        try {
          const summaryData = await apiRequest('/summary');
          setTemplateSummary(summaryData.summary);
        } catch (summaryError) {
          console.warn('Failed to fetch template summary:', summaryError);
        }
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch templates');
      setTemplates(null);
    } finally {
      setLoading(false);
    }
  }, [templateSummary]);

  const fetchTemplateDetails = useCallback(async (templateId: string) => {
    setLoading(true);
    setError(null);

    try {
      const data = await apiRequest(`/template/${templateId}`);
      setTemplateDetails(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch template details');
      setTemplateDetails(null);
    } finally {
      setLoading(false);
    }
  }, []);

  // ==============================================================================
  // CODE GENERATION FUNCTIONS
  // ==============================================================================

  const generateCode = useCallback(async (
    templateId: string,
    customConfig: Record<string, any> = {},
    swarmName?: string
  ): Promise<CodeGenerationResult> => {
    try {
      const data = await apiRequest('/generate-code', {
        method: 'POST',
        body: JSON.stringify({
          template_id: templateId,
          swarm_name: swarmName,
          custom_config: customConfig,
          save_to_file: false
        }),
      });

      return data;
    } catch (err) {
      return {
        success: false,
        errors: [err instanceof Error ? err.message : 'Code generation failed']
      };
    }
  }, []);

  const validateTemplate = useCallback(async (
    templateId: string,
    customConfig: Record<string, any> = {}
  ): Promise<ValidationResult> => {
    try {
      const data = await apiRequest('/validate', {
        method: 'POST',
        body: JSON.stringify({
          template_id: templateId,
          custom_config: customConfig
        }),
      });

      return data;
    } catch (err) {
      return {
        success: false,
        valid: false,
        validation_results: {
          error: err instanceof Error ? err.message : 'Validation failed'
        },
        timestamp: new Date().toISOString()
      };
    }
  }, []);

  // ==============================================================================
  // DEPLOYMENT FUNCTIONS
  // ==============================================================================

  const deploySwarm = useCallback(async (request: DeploymentRequest): Promise<DeploymentResult> => {
    try {
      const data = await apiRequest('/deploy', {
        method: 'POST',
        body: JSON.stringify(request),
      });

      // Refresh deployments list
      fetchDeployments();

      return data;
    } catch (err) {
      return {
        success: false,
        deployment_status: 'failed',
        errors: [err instanceof Error ? err.message : 'Deployment failed']
      };
    }
  }, []);

  const getSwarmStatus = useCallback(async (swarmId: string): Promise<SwarmStatus> => {
    try {
      const data = await apiRequest(`/deployment/${swarmId}/status`);
      return data;
    } catch (err) {
      throw err instanceof Error ? err : new Error('Failed to get swarm status');
    }
  }, []);

  const cancelDeployment = useCallback(async (deploymentId: string): Promise<boolean> => {
    try {
      await apiRequest(`/deployment/${deploymentId}`, {
        method: 'DELETE',
      });

      // Refresh deployments list
      fetchDeployments();
      return true;
    } catch (err) {
      console.error('Failed to cancel deployment:', err);
      return false;
    }
  }, []);

  const fetchDeployments = useCallback(async () => {
    try {
      const data = await apiRequest('/deployments');
      setDeployments(data.deployments);
    } catch (err) {
      console.error('Failed to fetch deployments:', err);
    }
  }, []);

  // ==============================================================================
  // WEBSOCKET MANAGEMENT
  // ==============================================================================

  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const wsUrl = `${API_BASE.replace('http', 'ws')}/api/swarm-templates/ws/deployments`;
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        setIsConnected(true);
        setConnectionError(null);
        console.log('WebSocket connected for deployment updates');
      };

      wsRef.current.onmessage = (event) => {
        try {
          const update: DeploymentUpdate = JSON.parse(event.data);

          switch (update.type) {
            case 'deployment_list':
              if (update.deployments) {
                setDeployments(update.deployments.map(dep => ({
                  deployment_id: dep.deployment_id,
                  swarm_name: dep.swarm_name,
                  template_id: '',
                  status: dep.status,
                  created_at: update.timestamp
                })));
              }
              break;

            case 'deployment_update':
              if (update.deployment_id && update.status) {
                setDeployments(prev =>
                  prev.map(dep =>
                    dep.deployment_id === update.deployment_id
                      ? { ...dep, status: update.status!, created_at: update.timestamp }
                      : dep
                  )
                );
              }
              break;

            case 'keepalive':
              // Just acknowledge keepalive
              break;
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionError('WebSocket connection error');
      };

      wsRef.current.onclose = () => {
        setIsConnected(false);
        console.log('WebSocket disconnected');

        // Attempt to reconnect after a delay
        setTimeout(() => {
          if (wsRef.current?.readyState !== WebSocket.OPEN) {
            connectWebSocket();
          }
        }, 5000);
      };

    } catch (err) {
      setConnectionError(err instanceof Error ? err.message : 'Failed to connect WebSocket');
      console.error('WebSocket connection failed:', err);
    }
  }, [API_BASE]);

  const disconnectWebSocket = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  // ==============================================================================
  // EFFECTS
  // ==============================================================================

  // Initialize templates and WebSocket connection
  useEffect(() => {
    fetchTemplates();
    fetchDeployments();
    connectWebSocket();

    return () => {
      disconnectWebSocket();
    };
  }, [fetchTemplates, fetchDeployments, connectWebSocket, disconnectWebSocket]);

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      disconnectWebSocket();
    };
  }, [disconnectWebSocket]);

  // ==============================================================================
  // RETURN HOOK INTERFACE
  // ==============================================================================

  return {
    // Template Management
    templates,
    templateDetails,
    templateSummary,
    loading,
    error,

    // Actions
    fetchTemplates,
    fetchTemplateDetails,
    generateCode,
    validateTemplate,
    deploySwarm,

    // Monitoring
    deployments,
    getSwarmStatus,
    cancelDeployment,

    // Real-time updates
    isConnected,
    connectionError,
  };
};

export default useSwarmTemplates;
