/**
 * API Configuration
 * Centralizes all API endpoints and configuration
 */

export const API_CONFIG = {
  baseUrl: process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000',
  wsUrl: process.env.NEXT_PUBLIC_WS_URL || 'ws://127.0.0.1:8000',
  timeout: Number(process.env.NEXT_PUBLIC_API_TIMEOUT) || 30000,

  // API endpoints
  endpoints: {
    chat: {
      query: '/api/chat/query',
      ws: '/ws/chat',
    },
    bi: {
      metrics: '/api/bi/metrics',
    },
    flowise: {
      health: '/api/flowise/health',
    },
    integrations: {
      status: '/api/integrations/status',
    },
  },
} as const

// Helper function to build full URLs
export const buildUrl = (endpoint: string): string => {
  return `${API_CONFIG.baseUrl}${endpoint}`
}

// Helper function to build WebSocket URLs
export const buildWsUrl = (endpoint: string): string => {
  return `${API_CONFIG.wsUrl}${endpoint}`
}