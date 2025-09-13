/**
 * AG-UI Events Hook
 * React hook for consuming AG-UI formatted events with WebSocket fallback
 * Provides modern streaming capabilities while maintaining backwards compatibility
 */

import { useState, useEffect, useCallback, useRef } from 'react';

// AG-UI Event Types
export interface AGUIEventMetadata {
  event_id: string;
  timestamp: string;
  source: string;
  domain: string;
  session_id?: string;
  user_id?: string;
  tenant_id?: string;
  correlation_id?: string;
  sequence: number;
  version: string;
}

export interface AGUITextDelta {
  delta: string;
  index: number;
  cumulative_text: string;
  tokens_processed: number;
  tokens_remaining?: number;
  finish_reason?: string;
}

export interface AGUIToolCall {
  tool_name: string;
  tool_id: string;
  arguments: Record<string, any>;
  status: 'pending' | 'running' | 'complete' | 'error';
  result?: any;
  error?: string;
  start_time?: string;
  end_time?: string;
  duration_ms?: number;
}

export interface AGUIStateUpdate {
  state: string;
  previous_state?: string;
  context: Record<string, any>;
  progress?: number; // 0.0 to 1.0
  message?: string;
}

export interface AGUIEvent {
  type: string;
  metadata: AGUIEventMetadata;
  data: AGUITextDelta | AGUIToolCall | AGUIStateUpdate | Record<string, any>;
  raw_data?: Record<string, any>;
}

// Event type constants
export const AGUI_EVENT_TYPES = {
  // Text streaming
  TEXT_DELTA: 'text_delta',
  TEXT_COMPLETE: 'text_complete',

  // Tool execution
  TOOL_CALL_START: 'tool_call_start',
  TOOL_CALL_DELTA: 'tool_call_delta',
  TOOL_CALL_COMPLETE: 'tool_call_complete',
  TOOL_RESULT: 'tool_result',

  // Agent state
  STATE_UPDATE: 'state_update',
  STATUS_CHANGE: 'status_change',

  // Business domain (Pay Ready)
  ACCOUNT_STATUS_UPDATE: 'account_status_update',
  PAYMENT_FLOW_UPDATE: 'payment_flow_update',
  STUCK_ACCOUNT_ALERT: 'stuck_account_alert',

  // Technical domain (Sophia)
  TACTICAL_OPERATION: 'tactical_operation',
  DEPLOYMENT_STATUS: 'deployment_status',
  SYSTEM_HEALTH: 'system_health',

  // Intelligence (Sophia)
  INTELLIGENCE_INSIGHT: 'intelligence_insight',
  PERFORMANCE_METRIC: 'performance_metric',
  OPERATIONAL_UPDATE: 'operational_update',

  // Swarm events
  SWARM_START: 'swarm_start',
  SWARM_PROGRESS: 'swarm_progress',
  SWARM_COMPLETE: 'swarm_complete',
  SWARM_ERROR: 'swarm_error',

  // Memory events
  MEMORY_UPDATE: 'memory_update',
  MEMORY_RETRIEVAL: 'memory_retrieval',

  // Connection events
  CONNECTED: 'connected',
  HEARTBEAT: 'heartbeat',
  ERROR: 'error'
} as const;

export const DOMAIN_CONTEXTS = {
  PAY_READY: 'pay_ready',
  CUSTOMER_SUCCESS: 'customer_success',
  OPERATIONS: 'operations',
  SOPHIA: 'sophia',
  SOPHIA_INTEL: 'sophia_intel',
  SYSTEM: 'system',
  GENERAL: 'general'
} as const;

// Hook configuration
interface UseAGUIEventsConfig {
  // Connection settings
  sseEndpoint?: string;
  websocketEndpoint?: string;
  enableSSE?: boolean;
  enableWebSocket?: boolean;

  // Event filtering
  eventTypes?: string[];
  domains?: string[];

  // Authentication
  authToken?: string;
  sessionId?: string;
  userId?: string;
  tenantId?: string;

  // Behavior settings
  autoReconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  bufferSize?: number;

  // Streaming settings
  enableStreaming?: boolean;
  enableDeltas?: boolean;
}

// Hook state
interface AGUIEventsState {
  events: AGUIEvent[];
  lastEvent: AGUIEvent | null;
  connectionState: 'disconnected' | 'connecting' | 'connected' | 'error';
  streamingText: Record<string, string>;
  activeToolCalls: Record<string, AGUIToolCall>;
  currentState: Record<string, AGUIStateUpdate>;
  error: string | null;
  isStreaming: boolean;
  eventCount: number;
}

// Text transformation utilities
export const textTransforms = {
  /**
   * Apply delta to existing text
   */
  applyDelta: (currentText: string, delta: AGUITextDelta): string => {
    if (delta.cumulative_text) {
      return delta.cumulative_text;
    }
    return currentText + delta.delta;
  },

  /**
   * Extract streaming text from events
   */
  extractStreamingText: (events: AGUIEvent[]): string => {
    return events
      .filter(event =>
        event.type === AGUI_EVENT_TYPES.TEXT_DELTA ||
        event.type === AGUI_EVENT_TYPES.TEXT_COMPLETE
      )
      .reduce((text, event) => {
        const delta = event.data as AGUITextDelta;
        return textTransforms.applyDelta(text, delta);
      }, '');
  },

  /**
   * Get final text from delta sequence
   */
  getFinalText: (events: AGUIEvent[]): string => {
    const completeEvent = events
      .reverse()
      .find(event => event.type === AGUI_EVENT_TYPES.TEXT_COMPLETE);

    if (completeEvent) {
      const delta = completeEvent.data as AGUITextDelta;
      return delta.cumulative_text || delta.delta;
    }

    return textTransforms.extractStreamingText(events);
  }
};

// Main hook
export function useAGUIEvents(config: UseAGUIEventsConfig = {}) {
  // Configuration with defaults
  const {
    sseEndpoint = '/api/agui/stream',
    websocketEndpoint = '/ws',
    enableSSE = true,
    enableWebSocket = true,
    eventTypes = [],
    domains = [],
    authToken,
    sessionId,
    userId,
    tenantId,
    autoReconnect = true,
    reconnectInterval = 5000,
    maxReconnectAttempts = 5,
    bufferSize = 1000,
    enableStreaming = true,
    enableDeltas = true
  } = config;

  // State
  const [state, setState] = useState<AGUIEventsState>({
    events: [],
    lastEvent: null,
    connectionState: 'disconnected',
    streamingText: {},
    activeToolCalls: {},
    currentState: {},
    error: null,
    isStreaming: false,
    eventCount: 0
  });

  // Refs for connection management
  const eventSourceRef = useRef<EventSource | null>(null);
  const websocketRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Event handlers
  const handleEvent = useCallback((event: AGUIEvent) => {
    setState(prevState => {
      const newEvents = [...prevState.events, event].slice(-bufferSize);
      const newState = { ...prevState };

      // Update event list
      newState.events = newEvents;
      newState.lastEvent = event;
      newState.eventCount = prevState.eventCount + 1;

      // Handle text streaming
      if (event.type === AGUI_EVENT_TYPES.TEXT_DELTA || event.type === AGUI_EVENT_TYPES.TEXT_COMPLETE) {
        const delta = event.data as AGUITextDelta;
        const streamId = event.metadata.correlation_id || 'default';

        if (enableStreaming && enableDeltas) {
          newState.streamingText = {
            ...prevState.streamingText,
            [streamId]: textTransforms.applyDelta(
              prevState.streamingText[streamId] || '',
              delta
            )
          };

          newState.isStreaming = event.type === AGUI_EVENT_TYPES.TEXT_DELTA;
        }
      }

      // Handle tool calls
      if (event.type.startsWith('tool_call_') || event.type === AGUI_EVENT_TYPES.TOOL_RESULT) {
        const toolCall = event.data as AGUIToolCall;
        newState.activeToolCalls = {
          ...prevState.activeToolCalls,
          [toolCall.tool_id]: toolCall
        };

        // Remove completed tool calls after a delay
        if (toolCall.status === 'complete' || toolCall.status === 'error') {
          setTimeout(() => {
            setState(current => ({
              ...current,
              activeToolCalls: {
                ...current.activeToolCalls,
                [toolCall.tool_id]: undefined
              }
            }));
          }, 5000);
        }
      }

      // Handle state updates
      if (event.type === AGUI_EVENT_TYPES.STATE_UPDATE) {
        const stateUpdate = event.data as AGUIStateUpdate;
        const stateKey = event.metadata.session_id || 'default';

        newState.currentState = {
          ...prevState.currentState,
          [stateKey]: stateUpdate
        };
      }

      return newState;
    });
  }, [bufferSize, enableStreaming, enableDeltas]);

  // SSE connection
  const connectSSE = useCallback(() => {
    if (!enableSSE || eventSourceRef.current) return;

    setState(prev => ({ ...prev, connectionState: 'connecting' }));

    const params = new URLSearchParams();
    if (eventTypes.length > 0) params.append('types', eventTypes.join(','));
    if (domains.length > 0) params.append('domains', domains.join(','));
    if (sessionId) params.append('session_id', sessionId);
    if (userId) params.append('user_id', userId);
    if (tenantId) params.append('tenant_id', tenantId);

    const url = `${sseEndpoint}?${params.toString()}`;

    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setState(prev => ({ ...prev, connectionState: 'connected', error: null }));
      reconnectAttemptsRef.current = 0;
    };

    eventSource.onmessage = (e) => {
      try {
        const event: AGUIEvent = JSON.parse(e.data);
        handleEvent(event);
      } catch (error) {
        console.error('Failed to parse SSE event:', error);
      }
    };

    eventSource.onerror = () => {
      setState(prev => ({
        ...prev,
        connectionState: 'error',
        error: 'SSE connection error'
      }));

      eventSource.close();
      eventSourceRef.current = null;

      // Auto-reconnect
      if (autoReconnect && reconnectAttemptsRef.current < maxReconnectAttempts) {
        reconnectAttemptsRef.current++;
        reconnectTimeoutRef.current = setTimeout(() => {
          connectSSE();
        }, reconnectInterval);
      }
    };
  }, [
    enableSSE, sseEndpoint, eventTypes, domains, sessionId, userId, tenantId,
    handleEvent, autoReconnect, maxReconnectAttempts, reconnectInterval
  ]);

  // WebSocket connection (fallback)
  const connectWebSocket = useCallback(() => {
    if (!enableWebSocket || websocketRef.current) return;

    setState(prev => ({ ...prev, connectionState: 'connecting' }));

    const params = new URLSearchParams();
    if (authToken) params.append('token', authToken);

    const url = `${websocketEndpoint}${sessionId ? `/${sessionId}` : ''}?${params.toString()}`;
    const ws = new WebSocket(url);
    websocketRef.current = ws;

    ws.onopen = () => {
      setState(prev => ({ ...prev, connectionState: 'connected', error: null }));
      reconnectAttemptsRef.current = 0;

      // Subscribe to events
      if (eventTypes.length > 0 || domains.length > 0) {
        ws.send(JSON.stringify({
          type: 'subscribe_agui',
          event_types: eventTypes,
          domains: domains
        }));
      }
    };

    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);

        // Convert legacy WebSocket event to AG-UI format if needed
        if (data.type && !data.metadata) {
          // This would be handled by the server-side adapter
          // but we can also do client-side conversion for fallback
          console.log('Received legacy WebSocket event:', data);
        } else {
          handleEvent(data as AGUIEvent);
        }
      } catch (error) {
        console.error('Failed to parse WebSocket event:', error);
      }
    };

    ws.onerror = () => {
      setState(prev => ({
        ...prev,
        connectionState: 'error',
        error: 'WebSocket connection error'
      }));
    };

    ws.onclose = () => {
      websocketRef.current = null;

      if (autoReconnect && reconnectAttemptsRef.current < maxReconnectAttempts) {
        reconnectAttemptsRef.current++;
        reconnectTimeoutRef.current = setTimeout(() => {
          connectWebSocket();
        }, reconnectInterval);
      } else {
        setState(prev => ({ ...prev, connectionState: 'disconnected' }));
      }
    };
  }, [
    enableWebSocket, websocketEndpoint, sessionId, authToken, eventTypes, domains,
    handleEvent, autoReconnect, maxReconnectAttempts, reconnectInterval
  ]);

  // Connect on mount
  useEffect(() => {
    if (enableSSE) {
      connectSSE();
    } else if (enableWebSocket) {
      connectWebSocket();
    }

    return () => {
      // Cleanup
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      if (websocketRef.current) {
        websocketRef.current.close();
        websocketRef.current = null;
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };
  }, [enableSSE, enableWebSocket, connectSSE, connectWebSocket]);

  // Utility functions
  const sendMessage = useCallback((message: Record<string, any>) => {
    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      websocketRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, cannot send message');
    }
  }, []);

  const clearEvents = useCallback(() => {
    setState(prev => ({
      ...prev,
      events: [],
      lastEvent: null,
      streamingText: {},
      activeToolCalls: {},
      currentState: {},
      eventCount: 0
    }));
  }, []);

  const getEventsByType = useCallback((eventType: string) => {
    return state.events.filter(event => event.type === eventType);
  }, [state.events]);

  const getEventsByDomain = useCallback((domain: string) => {
    return state.events.filter(event => event.metadata.domain === domain);
  }, [state.events]);

  const getStreamingText = useCallback((streamId: string = 'default') => {
    return state.streamingText[streamId] || '';
  }, [state.streamingText]);

  const getCurrentState = useCallback((stateKey: string = 'default') => {
    return state.currentState[stateKey];
  }, [state.currentState]);

  const getActiveToolCalls = useCallback(() => {
    return Object.values(state.activeToolCalls).filter(Boolean) as AGUIToolCall[];
  }, [state.activeToolCalls]);

  // Return hook interface
  return {
    // State
    events: state.events,
    lastEvent: state.lastEvent,
    connectionState: state.connectionState,
    error: state.error,
    isStreaming: state.isStreaming,
    eventCount: state.eventCount,

    // Streaming data
    streamingText: state.streamingText,
    activeToolCalls: state.activeToolCalls,
    currentState: state.currentState,

    // Actions
    sendMessage,
    clearEvents,

    // Utilities
    getEventsByType,
    getEventsByDomain,
    getStreamingText,
    getCurrentState,
    getActiveToolCalls,

    // Connection management
    reconnect: () => {
      if (enableSSE) connectSSE();
      else if (enableWebSocket) connectWebSocket();
    },

    // Constants
    EVENT_TYPES: AGUI_EVENT_TYPES,
    DOMAINS: DOMAIN_CONTEXTS
  };
}

// Specialized hooks for specific use cases

/**
 * Hook for Pay Ready business events
 */
export function usePayReadyEvents(config: Omit<UseAGUIEventsConfig, 'domains' | 'eventTypes'> = {}) {
  return useAGUIEvents({
    ...config,
    domains: [DOMAIN_CONTEXTS.PAY_READY],
    eventTypes: [
      AGUI_EVENT_TYPES.ACCOUNT_STATUS_UPDATE,
      AGUI_EVENT_TYPES.PAYMENT_FLOW_UPDATE,
      AGUI_EVENT_TYPES.STUCK_ACCOUNT_ALERT
    ]
  });
}

/**
 * Hook for Sophia tactical events
 */
export function useArtemisEvents(config: Omit<UseAGUIEventsConfig, 'domains' | 'eventTypes'> = {}) {
  return useAGUIEvents({
    ...config,
    domains: [DOMAIN_CONTEXTS.SOPHIA],
    eventTypes: [
      AGUI_EVENT_TYPES.TACTICAL_OPERATION,
      AGUI_EVENT_TYPES.DEPLOYMENT_STATUS,
      AGUI_EVENT_TYPES.SWARM_START,
      AGUI_EVENT_TYPES.SWARM_PROGRESS,
      AGUI_EVENT_TYPES.SWARM_COMPLETE,
      AGUI_EVENT_TYPES.SWARM_ERROR
    ]
  });
}

/**
 * Hook for text streaming
 */
export function useTextStreaming(config: Omit<UseAGUIEventsConfig, 'eventTypes'> = {}) {
  return useAGUIEvents({
    ...config,
    eventTypes: [
      AGUI_EVENT_TYPES.TEXT_DELTA,
      AGUI_EVENT_TYPES.TEXT_COMPLETE
    ],
    enableStreaming: true,
    enableDeltas: true
  });
}

/**
 * Hook for tool execution monitoring
 */
export function useToolExecution(config: Omit<UseAGUIEventsConfig, 'eventTypes'> = {}) {
  return useAGUIEvents({
    ...config,
    eventTypes: [
      AGUI_EVENT_TYPES.TOOL_CALL_START,
      AGUI_EVENT_TYPES.TOOL_CALL_DELTA,
      AGUI_EVENT_TYPES.TOOL_CALL_COMPLETE,
      AGUI_EVENT_TYPES.TOOL_RESULT
    ]
  });
}

export default useAGUIEvents;
