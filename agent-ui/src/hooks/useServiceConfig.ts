import { useEffect, useState } from 'react';
import { APIRoutes } from '../api/routes';
import { usePlaygroundStore } from '../store';

interface ServiceManifest {
  environment: {
    name: string;
    type: string;
    domain: string;
    region: string;
    loaded_from: string;
    loaded_at: string;
    config_hash: string;
  };
  services: {
    unified_api: {
      url: string;
      health: string;
      docs: string;
    };
    frontend: {
      url: string;
    };
    mcp_server: {
      url: string;
    };
    vector_store: {
      url: string;
    };
    weaviate: {
      url: string;
    };
    redis: {
      host: string;
      port: number;
    };
  };
  models: {
    orchestrator: {
      model: string;
      description: string;
    };
    agent_swarm: {
      allowed_models: string[];
      description: string;
    };
    embeddings: {
      primary: string;
      fallbacks: string[];
      cache: {
        enabled: boolean;
        ttl_seconds: number;
        similarity_threshold: number;
      };
      batch_size: number;
    };
  };
  features: {
    streaming: boolean;
    memory: boolean;
    teams: boolean;
    workflows: boolean;
    apps: boolean;
    evaluation_gates: boolean;
    safety_checks: boolean;
  };
  limits: {
    daily_budget_usd: number;
    max_tokens_per_request: number;
    max_requests_per_minute: number;
    api_rate_limit: number;
    api_rate_window: number;
  };
  ports: {
    api: number;
    frontend: number;
    mcp: number;
    vector_store: number;
  };
  health?: Record<string, any>;
  timestamp: string;
  version: string;
}

export const useServiceConfig = () => {
  const [manifest, setManifest] = useState<ServiceManifest | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const selectedEndpoint = usePlaygroundStore((state) => state.selectedEndpoint);
  const setSelectedEndpoint = usePlaygroundStore((state) => state.setSelectedEndpoint);

  useEffect(() => {
    const fetchManifest = async () => {
      try {
        setLoading(true);
        setError(null);

        // Try to fetch config from the current endpoint
        const configUrl = APIRoutes.GetConfig(selectedEndpoint);
        const response = await fetch(configUrl);

        if (!response.ok) {
          // If config endpoint fails, try to determine correct URL
          if (response.status === 404 || response.status === 403) {
            console.warn('Config endpoint not available, using defaults');
            return;
          }
          throw new Error(`Failed to fetch config: ${response.status}`);
        }

        const data: ServiceManifest = await response.json();
        setManifest(data);

        // Auto-update endpoint if manifest suggests a different one
        if (data.services?.unified_api?.url) {
          const manifestUrl = data.services.unified_api.url;
          if (manifestUrl !== selectedEndpoint) {
            setSelectedEndpoint(manifestUrl);
          }
        }

        // Log discovered services
          environment: data.environment?.name,
          services: Object.keys(data.services || {}),
          models: {
            orchestrator: data.models?.orchestrator?.model,
            swarm_count: data.models?.agent_swarm?.allowed_models?.length
          },
          features: data.features
        });

      } catch (err) {
        console.error('Failed to load service manifest:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');

        // Set default manifest on error
        setManifest({
          environment: {
            name: 'dev',
            type: 'development',
            domain: 'localhost',
            region: 'local',
            loaded_from: 'defaults',
            loaded_at: new Date().toISOString(),
            config_hash: 'default'
          },
          services: {
            unified_api: {
              url: selectedEndpoint,
              health: `${selectedEndpoint}/healthz`,
              docs: `${selectedEndpoint}/docs`
            },
            frontend: {
              url: window.location.origin
            },
            mcp_server: {
              url: 'http://localhost:8004'
            },
            vector_store: {
              url: 'http://localhost:8005'
            },
            weaviate: {
              url: 'http://localhost:8080'
            },
            redis: {
              host: 'localhost',
              port: 6379
            }
          },
          models: {
            orchestrator: {
              model: 'openai/gpt-5',
              description: 'Primary orchestrator model'
            },
            agent_swarm: {
              allowed_models: [
                'x-ai/grok-code-fast-1',
                'google/gemini-2.5-flash',
                'google/gemini-2.5-pro',
                'deepseek/deepseek-chat-v3-0324',
                'deepseek/deepseek-chat-v3.1',
                'qwen/qwen3-30b-a3b',
                'qwen/qwen3-coder',
                'openai/gpt-5',
                'deepseek/deepseek-r1-0528:free',
                'openai/gpt-4o-mini',
                'z-ai/glm-4.5'
              ],
              description: 'Models available for agent swarm'
            },
            embeddings: {
              primary: 'togethercomputer/m2-bert-80M-8k-retrieval',
              fallbacks: ['BAAI/bge-large-en-v1.5', 'BAAI/bge-base-en-v1.5'],
              cache: {
                enabled: true,
                ttl_seconds: 3600,
                similarity_threshold: 0.95
              },
              batch_size: 32
            }
          },
          features: {
            streaming: true,
            memory: true,
            teams: true,
            workflows: true,
            apps: true,
            evaluation_gates: true,
            safety_checks: true
          },
          limits: {
            daily_budget_usd: 100,
            max_tokens_per_request: 4096,
            max_requests_per_minute: 60,
            api_rate_limit: 100,
            api_rate_window: 60
          },
          ports: {
            api: 8003,
            frontend: 3000,
            mcp: 8004,
            vector_store: 8005
          },
          timestamp: new Date().toISOString(),
          version: '2.0.0'
        });
      } finally {
        setLoading(false);
      }
    };

    // Fetch manifest on mount and when endpoint changes
    fetchManifest();

    // Refresh manifest every 5 minutes
    const interval = setInterval(fetchManifest, 5 * 60 * 1000);

    return () => clearInterval(interval);
  }, [selectedEndpoint, setSelectedEndpoint]);

  return {
    manifest,
    loading,
    error,
    isOrchestratorModel: (model: string) => manifest?.models?.orchestrator?.model === model,
    isAllowedSwarmModel: (model: string) =>
      manifest?.models?.agent_swarm?.allowed_models?.includes(model) ?? false,
    getServiceUrl: (service: keyof ServiceManifest['services']) =>
      manifest?.services?.[service] ?? null,
    isFeatureEnabled: (feature: keyof ServiceManifest['features']) =>
      manifest?.features?.[feature] ?? false
  };
};