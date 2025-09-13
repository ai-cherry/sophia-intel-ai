/**
 * AG-UI Stream Display Component
 * Advanced component for displaying streamed text with delta updates, tool visualization,
 * and real-time state changes with smooth animations
 */

import React, { useState, useEffect, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  useAGUIEvents,
  AGUIEvent,
  AGUITextDelta,
  AGUIToolCall,
  AGUIStateUpdate,
  AGUI_EVENT_TYPES,
  textTransforms
} from '../../hooks/useAGUIEvents';

// Component interfaces
interface AGUIStreamDisplayProps {
  sessionId?: string;
  userId?: string;
  tenantId?: string;
  domains?: string[];
  eventTypes?: string[];
  className?: string;

  // Display options
  showToolCalls?: boolean;
  showStateUpdates?: boolean;
  showTimestamps?: boolean;
  showTokenCount?: boolean;
  showProgress?: boolean;

  // Streaming options
  typewriterEffect?: boolean;
  typewriterSpeed?: number;
  animateDeltas?: boolean;

  // Styling options
  theme?: 'light' | 'dark' | 'auto';
  compact?: boolean;
  maxHeight?: string;

  // Event handlers
  onEventReceived?: (event: AGUIEvent) => void;
  onTextComplete?: (text: string) => void;
  onToolCallComplete?: (toolCall: AGUIToolCall) => void;
  onStateChange?: (state: AGUIStateUpdate) => void;
  onError?: (error: string) => void;
}

interface ToolCallDisplayProps {
  toolCall: AGUIToolCall;
  compact?: boolean;
  theme?: string;
}

interface StateUpdateDisplayProps {
  stateUpdate: AGUIStateUpdate;
  compact?: boolean;
  theme?: string;
}

interface TokenCounterProps {
  tokensProcessed: number;
  tokensRemaining?: number;
  className?: string;
}

// Token counter component
const TokenCounter: React.FC<TokenCounterProps> = ({
  tokensProcessed,
  tokensRemaining,
  className = ''
}) => (
  <div className={`flex items-center text-xs text-gray-500 ${className}`}>
    <span className="mr-2">Tokens: {tokensProcessed.toLocaleString()}</span>
    {tokensRemaining && (
      <span className="text-yellow-600">
        ({tokensRemaining.toLocaleString()} remaining)
      </span>
    )}
  </div>
);

// Tool call display component
const ToolCallDisplay: React.FC<ToolCallDisplayProps> = ({
  toolCall,
  compact = false,
  theme = 'light'
}) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'text-yellow-600';
      case 'running': return 'text-blue-600';
      case 'complete': return 'text-green-600';
      case 'error': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending': return '⏳';
      case 'running': return '⚡';
      case 'complete': return '✅';
      case 'error': return '❌';
      default: return '❓';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className={`
        border rounded-lg p-3 mb-2
        ${theme === 'dark' ? 'border-gray-700 bg-gray-800' : 'border-gray-200 bg-gray-50'}
        ${compact ? 'p-2 text-sm' : 'p-3'}
      `}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center">
          <span className="mr-2">{getStatusIcon(toolCall.status)}</span>
          <span className="font-medium">{toolCall.tool_name}</span>
          <span className={`ml-2 text-sm ${getStatusColor(toolCall.status)}`}>
            {toolCall.status}
          </span>
        </div>

        {toolCall.duration_ms && (
          <span className="text-xs text-gray-500">
            {toolCall.duration_ms}ms
          </span>
        )}
      </div>

      {!compact && Object.keys(toolCall.arguments).length > 0 && (
        <div className="mb-2">
          <div className="text-xs text-gray-600 mb-1">Arguments:</div>
          <pre className={`
            text-xs p-2 rounded overflow-x-auto
            ${theme === 'dark' ? 'bg-gray-900 text-gray-300' : 'bg-white text-gray-700'}
          `}>
            {JSON.stringify(toolCall.arguments, null, 2)}
          </pre>
        </div>
      )}

      {toolCall.result && (
        <div className="mb-2">
          <div className="text-xs text-gray-600 mb-1">Result:</div>
          <div className={`
            text-sm p-2 rounded
            ${theme === 'dark' ? 'bg-gray-900 text-gray-300' : 'bg-white text-gray-700'}
          `}>
            {typeof toolCall.result === 'string'
              ? toolCall.result
              : JSON.stringify(toolCall.result, null, 2)
            }
          </div>
        </div>
      )}

      {toolCall.error && (
        <div className="mb-2">
          <div className="text-xs text-red-600 mb-1">Error:</div>
          <div className="text-sm p-2 rounded bg-red-50 text-red-700">
            {toolCall.error}
          </div>
        </div>
      )}
    </motion.div>
  );
};

// State update display component
const StateUpdateDisplay: React.FC<StateUpdateDisplayProps> = ({
  stateUpdate,
  compact = false,
  theme = 'light'
}) => (
  <motion.div
    initial={{ opacity: 0, scale: 0.95 }}
    animate={{ opacity: 1, scale: 1 }}
    exit={{ opacity: 0, scale: 0.95 }}
    className={`
      border-l-4 border-blue-500 pl-4 py-2 mb-2
      ${theme === 'dark' ? 'bg-gray-800' : 'bg-blue-50'}
      ${compact ? 'py-1' : 'py-2'}
    `}
  >
    <div className="flex items-center justify-between">
      <div className="flex items-center">
        <span className="font-medium text-blue-600">
          {stateUpdate.state}
        </span>
        {stateUpdate.previous_state && (
          <span className="text-xs text-gray-500 ml-2">
            (from {stateUpdate.previous_state})
          </span>
        )}
      </div>

      {stateUpdate.progress !== undefined && (
        <div className="flex items-center">
          <div className={`
            w-16 h-2 bg-gray-200 rounded-full overflow-hidden mr-2
            ${theme === 'dark' ? 'bg-gray-700' : 'bg-gray-200'}
          `}>
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${stateUpdate.progress * 100}%` }}
              transition={{ duration: 0.5 }}
              className="h-full bg-blue-500"
            />
          </div>
          <span className="text-xs text-gray-600">
            {Math.round(stateUpdate.progress * 100)}%
          </span>
        </div>
      )}
    </div>

    {stateUpdate.message && (
      <div className={`
        text-sm mt-1
        ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}
      `}>
        {stateUpdate.message}
      </div>
    )}

    {!compact && Object.keys(stateUpdate.context).length > 0 && (
      <details className="mt-2">
        <summary className="text-xs text-gray-500 cursor-pointer">
          Context ({Object.keys(stateUpdate.context).length} items)
        </summary>
        <pre className={`
          text-xs mt-1 p-2 rounded overflow-x-auto
          ${theme === 'dark' ? 'bg-gray-900 text-gray-300' : 'bg-white text-gray-700'}
        `}>
          {JSON.stringify(stateUpdate.context, null, 2)}
        </pre>
      </details>
    )}
  </motion.div>
);

// Typewriter effect component
const TypewriterText: React.FC<{
  text: string;
  speed: number;
  onComplete?: () => void;
  className?: string;
}> = ({ text, speed, onComplete, className = '' }) => {
  const [displayedText, setDisplayedText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    if (currentIndex < text.length) {
      const timer = setTimeout(() => {
        setDisplayedText(prev => prev + text[currentIndex]);
        setCurrentIndex(prev => prev + 1);
      }, speed);

      return () => clearTimeout(timer);
    } else if (onComplete) {
      onComplete();
    }
  }, [text, currentIndex, speed, onComplete]);

  useEffect(() => {
    // Reset when text changes
    setDisplayedText('');
    setCurrentIndex(0);
  }, [text]);

  return (
    <span className={className}>
      {displayedText}
      {currentIndex < text.length && (
        <motion.span
          animate={{ opacity: [1, 0] }}
          transition={{ repeat: Infinity, duration: 0.8 }}
          className="ml-1"
        >
          |
        </motion.span>
      )}
    </span>
  );
};

// Main component
const AGUIStreamDisplay: React.FC<AGUIStreamDisplayProps> = ({
  sessionId,
  userId,
  tenantId,
  domains = [],
  eventTypes = [],
  className = '',

  // Display options
  showToolCalls = true,
  showStateUpdates = true,
  showTimestamps = false,
  showTokenCount = true,
  showProgress = true,

  // Streaming options
  typewriterEffect = false,
  typewriterSpeed = 50,
  animateDeltas = true,

  // Styling options
  theme = 'auto',
  compact = false,
  maxHeight = '500px',

  // Event handlers
  onEventReceived,
  onTextComplete,
  onToolCallComplete,
  onStateChange,
  onError
}) => {
  // Use AG-UI events hook
  const {
    events,
    lastEvent,
    connectionState,
    error,
    isStreaming,
    eventCount,
    streamingText,
    activeToolCalls,
    currentState,
    getStreamingText,
    getActiveToolCalls,
    getCurrentState
  } = useAGUIEvents({
    sessionId,
    userId,
    tenantId,
    domains,
    eventTypes: eventTypes.length > 0 ? eventTypes : [
      AGUI_EVENT_TYPES.TEXT_DELTA,
      AGUI_EVENT_TYPES.TEXT_COMPLETE,
      AGUI_EVENT_TYPES.TOOL_CALL_START,
      AGUI_EVENT_TYPES.TOOL_CALL_COMPLETE,
      AGUI_EVENT_TYPES.TOOL_RESULT,
      AGUI_EVENT_TYPES.STATE_UPDATE
    ],
    enableStreaming: true,
    enableDeltas: true
  });

  // Theme detection
  const effectiveTheme = theme === 'auto'
    ? (window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
    : theme;

  // Refs
  const scrollRef = useRef<HTMLDivElement>(null);
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true);

  // Auto-scroll to bottom
  useEffect(() => {
    if (shouldAutoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events, streamingText, shouldAutoScroll]);

  // Handle scroll detection for auto-scroll
  const handleScroll = () => {
    if (scrollRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
      const isAtBottom = scrollTop + clientHeight >= scrollHeight - 10;
      setShouldAutoScroll(isAtBottom);
    }
  };

  // Event handlers
  useEffect(() => {
    if (lastEvent && onEventReceived) {
      onEventReceived(lastEvent);
    }

    if (lastEvent?.type === AGUI_EVENT_TYPES.TEXT_COMPLETE && onTextComplete) {
      const textData = lastEvent.data as AGUITextDelta;
      onTextComplete(textData.cumulative_text || textData.delta);
    }

    if (lastEvent?.type === AGUI_EVENT_TYPES.TOOL_CALL_COMPLETE && onToolCallComplete) {
      const toolCall = lastEvent.data as AGUIToolCall;
      onToolCallComplete(toolCall);
    }

    if (lastEvent?.type === AGUI_EVENT_TYPES.STATE_UPDATE && onStateChange) {
      const stateUpdate = lastEvent.data as AGUIStateUpdate;
      onStateChange(stateUpdate);
    }
  }, [lastEvent, onEventReceived, onTextComplete, onToolCallComplete, onStateChange]);

  // Error handling
  useEffect(() => {
    if (error && onError) {
      onError(error);
    }
  }, [error, onError]);

  // Get current streaming text
  const currentText = getStreamingText();
  const currentStateUpdate = getCurrentState();
  const currentToolCalls = getActiveToolCalls();

  // Process text events for display
  const textEvents = useMemo(() => {
    return events.filter(event =>
      event.type === AGUI_EVENT_TYPES.TEXT_DELTA ||
      event.type === AGUI_EVENT_TYPES.TEXT_COMPLETE
    );
  }, [events]);

  const finalText = useMemo(() => {
    return textTransforms.getFinalText(textEvents);
  }, [textEvents]);

  return (
    <div className={`
      agui-stream-display
      ${effectiveTheme === 'dark' ? 'bg-gray-900 text-white' : 'bg-white text-gray-900'}
      ${className}
    `}>
      {/* Connection status */}
      <div className="flex items-center justify-between p-2 border-b">
        <div className="flex items-center">
          <div className={`
            w-2 h-2 rounded-full mr-2
            ${connectionState === 'connected' ? 'bg-green-500' :
              connectionState === 'connecting' ? 'bg-yellow-500' : 'bg-red-500'}
          `} />
          <span className="text-sm font-medium">
            {connectionState === 'connected' ? 'Connected' :
             connectionState === 'connecting' ? 'Connecting...' :
             connectionState === 'error' ? 'Error' : 'Disconnected'}
          </span>
          {isStreaming && (
            <motion.span
              animate={{ opacity: [0.5, 1] }}
              transition={{ repeat: Infinity, duration: 1 }}
              className="ml-2 text-sm text-blue-500"
            >
              Streaming...
            </motion.span>
          )}
        </div>

        {showTokenCount && textEvents.length > 0 && (
          <TokenCounter
            tokensProcessed={textEvents[textEvents.length - 1]?.data.tokens_processed || 0}
            tokensRemaining={textEvents[textEvents.length - 1]?.data.tokens_remaining}
          />
        )}
      </div>

      {/* Main content area */}
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="overflow-y-auto p-4 space-y-4"
        style={{ maxHeight }}
      >
        {/* State updates */}
        <AnimatePresence>
          {showStateUpdates && currentStateUpdate && (
            <StateUpdateDisplay
              stateUpdate={currentStateUpdate}
              compact={compact}
              theme={effectiveTheme}
            />
          )}
        </AnimatePresence>

        {/* Active tool calls */}
        <AnimatePresence>
          {showToolCalls && currentToolCalls.map((toolCall) => (
            <ToolCallDisplay
              key={toolCall.tool_id}
              toolCall={toolCall}
              compact={compact}
              theme={effectiveTheme}
            />
          ))}
        </AnimatePresence>

        {/* Streaming text */}
        {currentText && (
          <motion.div
            initial={animateDeltas ? { opacity: 0, y: 10 } : undefined}
            animate={animateDeltas ? { opacity: 1, y: 0 } : undefined}
            className={`
              prose max-w-none
              ${effectiveTheme === 'dark' ? 'prose-invert' : ''}
              ${compact ? 'prose-sm' : 'prose-base'}
            `}
          >
            {typewriterEffect && !isStreaming ? (
              <TypewriterText
                text={finalText}
                speed={typewriterSpeed}
                onComplete={() => onTextComplete?.(finalText)}
              />
            ) : (
              <div className="whitespace-pre-wrap">
                {isStreaming ? currentText : finalText}
              </div>
            )}
          </motion.div>
        )}

        {/* Event history (if no streaming text) */}
        {!currentText && events.length > 0 && (
          <div className="space-y-2">
            {events.slice(-10).map((event, index) => (
              <motion.div
                key={`${event.metadata.event_id}-${index}`}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className={`
                  p-2 rounded text-sm border-l-2
                  ${effectiveTheme === 'dark' ? 'bg-gray-800 border-gray-600' : 'bg-gray-50 border-gray-300'}
                `}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">{event.type}</span>
                  {showTimestamps && (
                    <span className="text-xs text-gray-500">
                      {new Date(event.metadata.timestamp).toLocaleTimeString()}
                    </span>
                  )}
                </div>
                <div className="text-xs text-gray-600 mt-1">
                  Domain: {event.metadata.domain}
                </div>
              </motion.div>
            ))}
          </div>
        )}

        {/* Empty state */}
        {events.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <div className="text-lg mb-2">🔄</div>
            <div>Waiting for events...</div>
            <div className="text-sm">
              Events: {eventCount} | Connection: {connectionState}
            </div>
          </div>
        )}

        {/* Error display */}
        {error && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700"
          >
            <div className="font-medium">Connection Error</div>
            <div className="text-sm mt-1">{error}</div>
          </motion.div>
        )}
      </div>

      {/* Auto-scroll indicator */}
      {!shouldAutoScroll && (
        <motion.button
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 10 }}
          onClick={() => {
            setShouldAutoScroll(true);
            if (scrollRef.current) {
              scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
            }
          }}
          className="
            fixed bottom-4 right-4 bg-blue-500 hover:bg-blue-600
            text-white px-3 py-1 rounded-full text-sm font-medium
            shadow-lg transition-colors
          "
        >
          ↓ New messages
        </motion.button>
      )}
    </div>
  );
};

export default AGUIStreamDisplay;
export type { AGUIStreamDisplayProps, ToolCallDisplayProps, StateUpdateDisplayProps };
