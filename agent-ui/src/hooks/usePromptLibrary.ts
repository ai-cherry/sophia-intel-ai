/**
 * React Hook for Prompt Library Management
 * Comprehensive hook for prompt CRUD, version control, and real-time collaboration
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import axios, { AxiosResponse } from 'axios';

// Types
interface PromptMetadata {
  domain: string;
  agent_name?: string;
  task_type?: string;
  business_context?: string[];
  performance_tags?: string[];
  author?: string;
  created_at?: string;
  updated_at?: string;
}

interface PromptVersion {
  id: string;
  prompt_id: string;
  branch: string;
  version: string;
  content: string;
  metadata: PromptMetadata;
  status: string;
  created_at: string;
  performance_metrics?: { [key: string]: number };
  a_b_test_data?: { [key: string]: unknown };
}

interface Branch {
  name: string;
  base_version: string;
  head_version: string;
  created_at: string;
  description?: string;
  is_merged: boolean;
  merged_at?: string;
}

interface DiffResult {
  from_version: string;
  to_version: string;
  content_diff: string[];
  metadata_diff: { [key: string]: unknown };
  similarity_score: number;
  change_summary: string;
}

interface ABTest {
  test_id: string;
  name: string;
  description: string;
  control_version: string;
  test_versions: string[];
  traffic_split: { [key: string]: number };
  success_metrics: string[];
  start_time: string;
  end_time?: string;
  status: string;
  minimum_sample_size?: number;
}

interface ABTestResult {
  test_id: string;
  version_id: string;
  sample_size: number;
  success_rate: number;
  confidence_interval: [number, number];
  metrics: { [key: string]: number };
  statistical_significance: boolean;
  winner?: boolean;
}

interface SearchParams {
  query?: string;
  domain?: string;
  agent_name?: string;
  tags?: string[];
  limit?: number;
}

interface CreatePromptRequest {
  prompt_id: string;
  content: string;
  domain: string;
  agent_name?: string;
  task_type?: string;
  business_context?: string[];
  performance_tags?: string[];
  branch?: string;
  commit_message?: string;
}

interface UpdatePromptRequest {
  content: string;
  commit_message?: string;
  branch?: string;
}

interface CreateBranchRequest {
  branch_name: string;
  from_branch?: string;
  description?: string;
}

interface MergeRequest {
  from_branch: string;
  to_branch?: string;
  strategy?: 'fast_forward' | 'three_way' | 'manual';
  commit_message?: string;
}

interface CreateABTestRequest {
  name: string;
  description: string;
  control_version: string;
  test_versions: string[];
  traffic_split: { [key: string]: number };
  success_metrics: string[];
  end_time?: string;
  minimum_sample_size?: number;
}

interface LeaderboardEntry {
  prompt_id: string;
  version_id: string;
  agent_name: string;
  domain: string;
  task_type: string;
  score: number;
  business_contexts: string[];
  performance_tags: string[];
}

// API Configuration
const API_BASE_URL = '/api/v1/prompts';

// HTTP Client with interceptors
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth
apiClient.interceptors.request.use((config) => {
  // Add auth token if available
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);

    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }

    return Promise.reject(error);
  }
);

// Main Hook
export const usePromptLibrary = () => {
  // State
  const [prompts, setPrompts] = useState<PromptVersion[]>([]);
  const [branches, setBranches] = useState<{ [promptId: string]: Branch[] }>({});
  const [abTests, setABTests] = useState<ABTest[]>([]);
  const [selectedPrompt, setSelectedPrompt] = useState<PromptVersion | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [wsConnection, setWsConnection] = useState<WebSocket | null>(null);

  // WebSocket connection for real-time updates
  useEffect(() => {
    const connectWebSocket = () => {
      const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/v1/prompts/ws`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setWsConnection(ws);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onclose = () => {
        setWsConnection(null);
        // Reconnect after 5 seconds
        setTimeout(connectWebSocket, 5000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    };

    connectWebSocket();

    return () => {
      if (wsConnection) {
        wsConnection.close();
      }
    };
  }, []);

  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback((data: unknown) => {
    switch (data.type) {
      case 'prompt_updated':
        setPrompts(prev => prev.map(p =>
          p.id === data.prompt.id ? data.prompt : p
        ));
        break;
      case 'prompt_created':
        setPrompts(prev => [...prev, data.prompt]);
        break;
      case 'branch_created':
        setBranches(prev => ({
          ...prev,
          [data.prompt_id]: [...(prev[data.prompt_id] || []), data.branch]
        }));
        break;
      case 'ab_test_updated':
        setABTests(prev => prev.map(test =>
          test.test_id === data.test.test_id ? data.test : test
        ));
        break;
      default:
    }
  }, []);

  // Error handler
  const handleError = useCallback((error: unknown, context: string) => {
    const errorMessage = error.response?.data?.detail || error.message || 'An unexpected error occurred';
    setError(`${context}: ${errorMessage}`);
    console.error(`${context}:`, error);
  }, []);

  // Clear error
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Search prompts
  const searchPrompts = useCallback(async (params: SearchParams): Promise<PromptVersion[]> => {
    setLoading(true);
    clearError();

    try {
      const response: AxiosResponse<PromptVersion[]> = await apiClient.post('/search', params);
      setPrompts(response.data);
      return response.data;
    } catch (error) {
      handleError(error, 'Failed to search prompts');
      return [];
    } finally {
      setLoading(false);
    }
  }, [clearError, handleError]);

  // Create prompt
  const createPrompt = useCallback(async (request: CreatePromptRequest): Promise<PromptVersion | null> => {
    setLoading(true);
    clearError();

    try {
      const response: AxiosResponse<PromptVersion> = await apiClient.post('/create', request);
      const newPrompt = response.data;
      setPrompts(prev => [...prev, newPrompt]);

      // Send WebSocket notification
      if (wsConnection) {
        wsConnection.send(JSON.stringify({
          type: 'prompt_created',
          prompt: newPrompt
        }));
      }

      return newPrompt;
    } catch (error) {
      handleError(error, 'Failed to create prompt');
      return null;
    } finally {
      setLoading(false);
    }
  }, [clearError, handleError, wsConnection]);

  // Update prompt
  const updatePrompt = useCallback(async (promptId: string, request: UpdatePromptRequest): Promise<PromptVersion | null> => {
    setLoading(true);
    clearError();

    try {
      const response: AxiosResponse<PromptVersion> = await apiClient.put(`/${promptId}/update`, request);
      const updatedPrompt = response.data;

      setPrompts(prev => prev.map(p =>
        p.prompt_id === promptId && p.branch === (request.branch || 'main') ? updatedPrompt : p
      ));

      // Send WebSocket notification
      if (wsConnection) {
        wsConnection.send(JSON.stringify({
          type: 'prompt_updated',
          prompt: updatedPrompt
        }));
      }

      return updatedPrompt;
    } catch (error) {
      handleError(error, 'Failed to update prompt');
      return null;
    } finally {
      setLoading(false);
    }
  }, [clearError, handleError, wsConnection]);

  // Delete prompt
  const deletePrompt = useCallback(async (promptId: string): Promise<boolean> => {
    setLoading(true);
    clearError();

    try {
      await apiClient.delete(`/${promptId}`);
      setPrompts(prev => prev.filter(p => p.prompt_id !== promptId));
      return true;
    } catch (error) {
      handleError(error, 'Failed to delete prompt');
      return false;
    } finally {
      setLoading(false);
    }
  }, [clearError, handleError]);

  // Get prompt
  const getPrompt = useCallback(async (promptId: string, branch = 'main', version?: string): Promise<PromptVersion | null> => {
    setLoading(true);
    clearError();

    try {
      const params = new URLSearchParams({ branch });
      if (version) params.append('version', version);

      const response: AxiosResponse<PromptVersion> = await apiClient.get(`/${promptId}?${params}`);
      return response.data;
    } catch (error) {
      handleError(error, 'Failed to get prompt');
      return null;
    } finally {
      setLoading(false);
    }
  }, [clearError, handleError]);

  // Get prompt history
  const getPromptHistory = useCallback(async (promptId: string, branch?: string): Promise<PromptVersion[]> => {
    setLoading(true);
    clearError();

    try {
      const params = branch ? `?branch=${branch}` : '';
      const response: AxiosResponse<PromptVersion[]> = await apiClient.get(`/${promptId}/history${params}`);
      return response.data;
    } catch (error) {
      handleError(error, 'Failed to get prompt history');
      return [];
    } finally {
      setLoading(false);
    }
  }, [clearError, handleError]);

  // Create branch
  const createBranch = useCallback(async (promptId: string, request: CreateBranchRequest): Promise<Branch | null> => {
    setLoading(true);
    clearError();

    try {
      const response: AxiosResponse<Branch> = await apiClient.post(`/${promptId}/branches`, request);
      const newBranch = response.data;

      setBranches(prev => ({
        ...prev,
        [promptId]: [...(prev[promptId] || []), newBranch]
      }));

      // Send WebSocket notification
      if (wsConnection) {
        wsConnection.send(JSON.stringify({
          type: 'branch_created',
          prompt_id: promptId,
          branch: newBranch
        }));
      }

      return newBranch;
    } catch (error) {
      handleError(error, 'Failed to create branch');
      return null;
    } finally {
      setLoading(false);
    }
  }, [clearError, handleError, wsConnection]);

  // Get branches
  const getBranches = useCallback(async (promptId: string): Promise<Branch[]> => {
    setLoading(true);
    clearError();

    try {
      const response: AxiosResponse<Branch[]> = await apiClient.get(`/${promptId}/branches`);
      const branchList = response.data;

      setBranches(prev => ({
        ...prev,
        [promptId]: branchList
      }));

      return branchList;
    } catch (error) {
      handleError(error, 'Failed to get branches');
      return [];
    } finally {
      setLoading(false);
    }
  }, [clearError, handleError]);

  // Merge branch
  const mergeBranch = useCallback(async (promptId: string, request: MergeRequest): Promise<PromptVersion | null> => {
    setLoading(true);
    clearError();

    try {
      const response: AxiosResponse<PromptVersion> = await apiClient.post(`/${promptId}/merge`, request);
      const mergedVersion = response.data;

      setPrompts(prev => [...prev, mergedVersion]);

      // Update branch status
      setBranches(prev => ({
        ...prev,
        [promptId]: prev[promptId]?.map(branch =>
          branch.name === request.from_branch
            ? { ...branch, is_merged: true, merged_at: new Date().toISOString() }
            : branch
        ) || []
      }));

      return mergedVersion;
    } catch (error) {
      handleError(error, 'Failed to merge branch');
      return null;
    } finally {
      setLoading(false);
    }
  }, [clearError, handleError]);

  // Diff versions
  const diffVersions = useCallback(async (promptId: string, fromVersion: string, toVersion: string): Promise<DiffResult | null> => {
    setLoading(true);
    clearError();

    try {
      const response: AxiosResponse<DiffResult> = await apiClient.get(`/${promptId}/diff`, {
        params: { from_version: fromVersion, to_version: toVersion }
      });
      return response.data;
    } catch (error) {
      handleError(error, 'Failed to generate diff');
      return null;
    } finally {
      setLoading(false);
    }
  }, [clearError, handleError]);

  // Create A/B test
  const createABTest = useCallback(async (request: CreateABTestRequest): Promise<string | null> => {
    setLoading(true);
    clearError();

    try {
      const response: AxiosResponse<{ test_id: string; message: string }> = await apiClient.post('/ab-tests', request);

      // Refresh A/B tests list
      getActiveABTests();

      return response.data.test_id;
    } catch (error) {
      handleError(error, 'Failed to create A/B test');
      return null;
    } finally {
      setLoading(false);
    }
  }, [clearError, handleError]);

  // Record A/B test result
  const recordABTestResult = useCallback(async (testId: string, versionId: string, success: boolean, metrics?: { [key: string]: number }): Promise<boolean> => {
    try {
      await apiClient.post(`/ab-tests/${testId}/results`, {
        version_id: versionId,
        success,
        metrics
      });
      return true;
    } catch (error) {
      handleError(error, 'Failed to record A/B test result');
      return false;
    }
  }, [handleError]);

  // Get A/B test results
  const getABTestResults = useCallback(async (testId: string): Promise<{ [versionId: string]: ABTestResult } | null> => {
    setLoading(true);
    clearError();

    try {
      const response: AxiosResponse<{ test_id: string; results: { [versionId: string]: ABTestResult } }> = await apiClient.get(`/ab-tests/${testId}/results`);
      return response.data.results;
    } catch (error) {
      handleError(error, 'Failed to get A/B test results');
      return null;
    } finally {
      setLoading(false);
    }
  }, [clearError, handleError]);

  // Get active A/B tests
  const getActiveABTests = useCallback(async (): Promise<ABTest[]> => {
    try {
      const response: AxiosResponse<ABTest[]> = await apiClient.get('/ab-tests');
      setABTests(response.data);
      return response.data;
    } catch (error) {
      handleError(error, 'Failed to get active A/B tests');
      return [];
    }
  }, [handleError]);

  // Update performance metrics
  const updateMetrics = useCallback(async (versionId: string, metrics: { [key: string]: number }): Promise<boolean> => {
    try {
      await apiClient.post(`/${versionId}/metrics`, metrics);

      // Update local state
      setPrompts(prev => prev.map(p =>
        p.id === versionId
          ? { ...p, performance_metrics: { ...(p.performance_metrics || {}), ...metrics } }
          : p
      ));

      return true;
    } catch (error) {
      handleError(error, 'Failed to update metrics');
      return false;
    }
  }, [handleError]);

  // Get performance leaderboard
  const getLeaderboard = useCallback(async (domain?: string, metric = 'success_rate', limit = 10): Promise<LeaderboardEntry[]> => {
    try {
      const params = new URLSearchParams({ metric, limit: limit.toString() });
      if (domain) params.append('domain', domain);

      const response: AxiosResponse<LeaderboardEntry[]> = await apiClient.get(`/performance/leaderboard?${params}`);
      return response.data;
    } catch (error) {
      handleError(error, 'Failed to get performance leaderboard');
      return [];
    }
  }, [handleError]);

  // Get context-aware prompt
  const getContextPrompt = useCallback(async (agentName: string, businessContext: string, taskType: string): Promise<{ prompt_content: string } | null> => {
    try {
      const response: AxiosResponse<{ agent_name: string; business_context: string; task_type: string; prompt_content: string }> =
        await apiClient.get(`/mythology/${agentName}/context/${businessContext}`, {
          params: { task_type: taskType }
        });
      return { prompt_content: response.data.prompt_content };
    } catch (error) {
      handleError(error, 'Failed to get context prompt');
      return null;
    }
  }, [handleError]);

  // Export prompts
  const exportPrompts = useCallback(async (promptIds?: string[]): Promise<any | null> => {
    setLoading(true);
    clearError();

    try {
      const params = promptIds ? `?${promptIds.map(id => `prompt_ids=${id}`).join('&')}` : '';
      const response: AxiosResponse<any> = await apiClient.get(`/export${params}`);

      // Trigger download
      const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `prompts-export-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      return response.data;
    } catch (error) {
      handleError(error, 'Failed to export prompts');
      return null;
    } finally {
      setLoading(false);
    }
  }, [clearError, handleError]);

  // Import prompts
  const importPrompts = useCallback(async (importData: unknown, overwrite = false): Promise<boolean> => {
    setLoading(true);
    clearError();

    try {
      await apiClient.post('/import', importData, {
        params: { overwrite }
      });

      // Refresh prompts list
      searchPrompts({});

      return true;
    } catch (error) {
      handleError(error, 'Failed to import prompts');
      return false;
    } finally {
      setLoading(false);
    }
  }, [clearError, handleError, searchPrompts]);

  // Health check
  const healthCheck = useCallback(async (): Promise<any> => {
    try {
      const response = await apiClient.get('/health');
      return response.data;
    } catch (error) {
      handleError(error, 'Health check failed');
      return null;
    }
  }, [handleError]);

  // Initialize data on mount
  useEffect(() => {
    const initialize = async () => {
      await searchPrompts({});
      await getActiveABTests();
    };

    initialize();
  }, [searchPrompts, getActiveABTests]);

  // Memoized values
  const availableAgents = useMemo(() => {
    const agents = new Set<string>();
    prompts.forEach(p => {
      if (p.metadata.agent_name) {
        agents.add(p.metadata.agent_name);
      }
    });
    return Array.from(agents).sort();
  }, [prompts]);

  const availableDomains = useMemo(() => {
    const domains = new Set<string>();
    prompts.forEach(p => domains.add(p.metadata.domain));
    return Array.from(domains).sort();
  }, [prompts]);

  const availableTags = useMemo(() => {
    const tags = new Set<string>();
    prompts.forEach(p => {
      p.metadata.performance_tags?.forEach(tag => tags.add(tag));
    });
    return Array.from(tags).sort();
  }, [prompts]);

  return {
    // Data
    prompts,
    branches,
    abTests,
    selectedPrompt,
    availableAgents,
    availableDomains,
    availableTags,
    loading,
    error,
    wsConnection: !!wsConnection,

    // Actions
    searchPrompts,
    createPrompt,
    updatePrompt,
    deletePrompt,
    getPrompt,
    getPromptHistory,
    setSelectedPrompt,
    createBranch,
    getBranches,
    mergeBranch,
    diffVersions,
    createABTest,
    recordABTestResult,
    getABTestResults,
    getActiveABTests,
    updateMetrics,
    getLeaderboard,
    getContextPrompt,
    exportPrompts,
    importPrompts,
    healthCheck,
    clearError,
  };
};