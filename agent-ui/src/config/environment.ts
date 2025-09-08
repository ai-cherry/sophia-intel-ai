/**
 * Environment configuration for the frontend application
 * Centralizes all environment variables and provides defaults
 */

interface EnvironmentConfig {
  // API Configuration
  apiBaseUrl: string;
  wsBaseUrl: string;

  // Feature flags
  debugMode: boolean;

  // Deployment environment
  environment: 'development' | 'staging' | 'production';
}

interface DashboardConfig {
  wsEndpoints: {
    sales: string;
    clientHealth: string;
    projectMgmt: string;
    unifiedChat: string;
    general: string;
  };
  apiEndpoints: {
    sales: {
      reps: string;
      gongCalls: string;
      teamMetrics: string;
      coaching: string;
    };
    clients: {
      health: string;
      recoveryPlans: string;
      metrics: string;
      healthCheck: (id: string) => string;
      recoveryPlan: (id: string) => string;
    };
    projects: {
      list: string;
      syncStatus: string;
      syncAll: string;
      communicationMetrics: string;
      blockerResolve: (projectId: string, blockerId: string) => string;
    };
    team: {
      members: string;
    };
    voice: {
      process: string;
    };
    agents: {
      available: string;
      recommend: string;
    };
  };
  themes: {
    hermes: {
      primaryColor: string;
      secondaryColor: string;
      gradientFrom: string;
      gradientTo: string;
      iconColor: string;
    };
    asclepius: {
      primaryColor: string;
      secondaryColor: string;
      gradientFrom: string;
      gradientTo: string;
      iconColor: string;
    };
    athena: {
      primaryColor: string;
      secondaryColor: string;
      gradientFrom: string;
      gradientTo: string;
      iconColor: string;
    };
    unified: {
      primaryColor: string;
      secondaryColor: string;
      gradientFrom: string;
      gradientTo: string;
      iconColor: string;
    };
  };
}

// Helper to safely get environment variables
const getEnvVar = (key: string, defaultValue: string): string => {
  // In Next.js, public environment variables must be prefixed with NEXT_PUBLIC_
  const envKey = `NEXT_PUBLIC_${key}`;

  // Check if running in browser
  if (typeof window !== 'undefined') {
    // @ts-ignore - process.env is available in Next.js
    return process.env[envKey] || defaultValue;
  }

  // Server-side
  return process.env[envKey] || defaultValue;
};

// Helper to determine environment
const getEnvironment = (): 'development' | 'staging' | 'production' => {
  const env = getEnvVar('NODE_ENV', 'development').toLowerCase();
  if (env === 'production') return 'production';
  if (env === 'staging') return 'staging';
  return 'development';
};

// Helper to build WebSocket URL
const buildWebSocketUrl = (): string => {
  const wsHost = getEnvVar('WS_HOST', 'localhost');
  const wsPort = getEnvVar('WS_PORT', '8000');
  const wsPath = getEnvVar('WS_PATH', '/ws/orchestrator');
  const wsProtocol = getEnvVar('WS_PROTOCOL', 'ws');

  // Use configured URL if provided
  const configuredUrl = getEnvVar('WS_URL', '');
  if (configuredUrl) {
    return configuredUrl;
  }

  // Build URL from components
  return `${wsProtocol}://${wsHost}:${wsPort}${wsPath}`;
};

// Helper to build API base URL
const buildApiBaseUrl = (): string => {
  const apiHost = getEnvVar('API_HOST', 'localhost');
  const apiPort = getEnvVar('API_PORT', '8000');
  const apiProtocol = getEnvVar('API_PROTOCOL', 'http');

  // Use configured URL if provided
  const configuredUrl = getEnvVar('API_URL', '');
  if (configuredUrl) {
    return configuredUrl;
  }

  // Build URL from components
  return `${apiProtocol}://${apiHost}:${apiPort}`;
};

// Create and export the configuration
export const config: EnvironmentConfig = {
  apiBaseUrl: buildApiBaseUrl(),
  wsBaseUrl: buildWebSocketUrl(),
  debugMode: getEnvVar('DEBUG_MODE', 'false') === 'true',
  environment: getEnvironment(),
};

// Export individual config values for convenience
export const { apiBaseUrl, wsBaseUrl, debugMode, environment } = config;

// Dashboard-specific configuration
export const dashboardConfig: DashboardConfig = {
  wsEndpoints: {
    sales: `${wsBaseUrl}/sales-hermes`,
    clientHealth: `${wsBaseUrl}/client-health-asclepius`,
    projectMgmt: `${wsBaseUrl}/project-mgmt-athena`,
    unifiedChat: `${wsBaseUrl}/unified-chat`,
    general: `${wsBaseUrl}/general`
  },
  apiEndpoints: {
    sales: {
      reps: `${apiBaseUrl}/api/sales/reps`,
      gongCalls: `${apiBaseUrl}/api/sales/gong-calls`,
      teamMetrics: `${apiBaseUrl}/api/sales/team-metrics`,
      coaching: `${apiBaseUrl}/api/sales/coaching`
    },
    clients: {
      health: `${apiBaseUrl}/api/clients/health`,
      recoveryPlans: `${apiBaseUrl}/api/clients/recovery-plans`,
      metrics: `${apiBaseUrl}/api/clients/metrics`,
      healthCheck: (id: string) => `${apiBaseUrl}/api/clients/${id}/health-check`,
      recoveryPlan: (id: string) => `${apiBaseUrl}/api/clients/${id}/recovery-plan`
    },
    projects: {
      list: `${apiBaseUrl}/api/projects`,
      syncStatus: `${apiBaseUrl}/api/projects/sync-status`,
      syncAll: `${apiBaseUrl}/api/projects/sync-all`,
      communicationMetrics: `${apiBaseUrl}/api/projects/communication-metrics`,
      blockerResolve: (projectId: string, blockerId: string) =>
        `${apiBaseUrl}/api/projects/${projectId}/blockers/${blockerId}/resolve`
    },
    team: {
      members: `${apiBaseUrl}/api/team/members`
    },
    voice: {
      process: `${apiBaseUrl}/api/voice/process`
    },
    agents: {
      available: `${apiBaseUrl}/api/agents/available`,
      recommend: `${apiBaseUrl}/api/agents/recommend`
    }
  },
  themes: {
    hermes: {
      primaryColor: '#3B82F6',
      secondaryColor: '#8B5CF6',
      gradientFrom: 'from-blue-50',
      gradientTo: 'to-indigo-100',
      iconColor: 'text-blue-600'
    },
    asclepius: {
      primaryColor: '#10B981',
      secondaryColor: '#14B8A6',
      gradientFrom: 'from-emerald-50',
      gradientTo: 'to-teal-100',
      iconColor: 'text-emerald-600'
    },
    athena: {
      primaryColor: '#8B5CF6',
      secondaryColor: '#EC4899',
      gradientFrom: 'from-purple-50',
      gradientTo: 'to-pink-100',
      iconColor: 'text-purple-600'
    },
    unified: {
      primaryColor: '#6366F1',
      secondaryColor: '#8B5CF6',
      gradientFrom: 'from-indigo-50',
      gradientTo: 'to-purple-100',
      iconColor: 'text-indigo-600'
    }
  }
};

// Feature flags for dashboards
export const featureFlags = {
  voiceEnabled: getEnvVar('VOICE_ENABLED', 'true') === 'true',
  realtimeUpdates: getEnvVar('REALTIME_UPDATES', 'true') === 'true',
  crossPlatformSync: getEnvVar('CROSS_PLATFORM_SYNC', 'true') === 'true',
  advancedAnalytics: getEnvVar('ADVANCED_ANALYTICS', 'true') === 'true',
  experimentalFeatures: environment === 'development'
};

// Update intervals
export const updateIntervals = {
  realtime: 1000,     // 1 second
  frequent: 5000,     // 5 seconds
  normal: 30000,      // 30 seconds
  slow: 60000         // 1 minute
};

// Voice configuration
export const voiceConfig = {
  elevenLabs: {
    apiKey: getEnvVar('ELEVENLABS_API_KEY', ''),
    defaultVoiceId: getEnvVar('ELEVENLABS_DEFAULT_VOICE_ID', 'rachel'),
    baseUrl: 'https://api.elevenlabs.io/v1'
  },
  settings: {
    sampleRate: 22050,
    channels: 1,
    bitDepth: 16,
    format: 'mp3'
  }
};

// Log configuration in debug mode (but not sensitive data)
if (config.debugMode && typeof window !== 'undefined') {
    environment: config.environment,
    apiBaseUrl: config.apiBaseUrl,
    wsBaseUrl: config.wsBaseUrl,
    debugMode: config.debugMode,
    featureFlags,
  });
}

export default config;