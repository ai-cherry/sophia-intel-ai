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

// Log configuration in debug mode (but not sensitive data)
if (config.debugMode && typeof window !== 'undefined') {
  console.log('Environment Configuration:', {
    environment: config.environment,
    apiBaseUrl: config.apiBaseUrl,
    wsBaseUrl: config.wsBaseUrl,
    debugMode: config.debugMode,
  });
}

export default config;
