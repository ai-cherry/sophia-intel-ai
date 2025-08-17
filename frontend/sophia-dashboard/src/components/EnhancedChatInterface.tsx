import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Send, Mic, MicOff, Settings, Zap, Brain, Server } from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: {
    backend?: string;
    performance_metrics?: any;
    research_context?: any;
    sophia_context?: any;
  };
}

interface ChatSettings {
  useSwarm: boolean;
  webAccess: boolean;
  deepResearch: boolean;
  voice: boolean;
  persona: string;
  model: string;
  temperature: number;
}

const EnhancedChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [settings, setSettings] = useState<ChatSettings>({
    useSwarm: false,
    webAccess: true,
    deepResearch: false,
    voice: false,
    persona: 'default',
    model: 'claude-3.5-sonnet',
    temperature: 0.7
  });
  const [sessionId] = useState(() => `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`);
  const [showSettings, setShowSettings] = useState(false);
  const [systemStatus, setSystemStatus] = useState<any>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Auto-scroll to bottom
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Initialize WebSocket connection
  useEffect(() => {
    const connectWebSocket = () => {
      const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/v1/sophia/ws/chat`;
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
      };

      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'chunk') {
          // Handle streaming chunk
          setMessages(prev => {
            const lastMessage = prev[prev.length - 1];
            if (lastMessage && lastMessage.role === 'assistant' && lastMessage.id === data.session_id) {
              return prev.map(msg => 
                msg.id === data.session_id 
                  ? { ...msg, content: msg.content + data.content }
                  : msg
              );
            } else {
              return [...prev, {
                id: data.session_id,
                role: 'assistant',
                content: data.content,
                timestamp: new Date(),
                metadata: {}
              }];
            }
          });
        } else if (data.type === 'response') {
          // Handle complete response
          setMessages(prev => [...prev, {
            id: `msg-${Date.now()}`,
            role: 'assistant',
            content: data.message,
            timestamp: new Date(),
            metadata: {
              performance_metrics: data.performance_metrics
            }
          }]);
        } else if (data.type === 'complete') {
          setIsStreaming(false);
          setIsLoading(false);
        } else if (data.type === 'error') {
          console.error('WebSocket error:', data.error);
          setIsLoading(false);
          setIsStreaming(false);
        }
      };

      wsRef.current.onclose = () => {
        console.log('WebSocket disconnected');
        // Attempt to reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    };

    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // Fetch system status
  useEffect(() => {
    const fetchSystemStatus = async () => {
      try {
        const response = await fetch('/api/v1/sophia/status');
        const status = await response.json();
        setSystemStatus(status);
      } catch (error) {
        console.error('Failed to fetch system status:', error);
      }
    };

    fetchSystemStatus();
    const interval = setInterval(fetchSystemStatus, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  }, []);

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: inputMessage.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      if (settings.voice || isStreaming) {
        // Use WebSocket for streaming/voice
        setIsStreaming(true);
        const chatRequest = {
          message: userMessage.content,
          session_id: sessionId,
          user_id: 'current-user',
          use_swarm: settings.useSwarm,
          web_access: settings.webAccess,
          deep_research: settings.deepResearch,
          voice: settings.voice,
          persona: settings.persona,
          model: settings.model,
          temperature: settings.temperature,
          stream: true
        };

        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify(chatRequest));
        }
      } else {
        // Use HTTP for regular requests
        const response = await fetch('/api/v1/sophia/chat/enhanced', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message: userMessage.content,
            session_id: sessionId,
            user_id: 'current-user',
            use_swarm: settings.useSwarm,
            web_access: settings.webAccess,
            deep_research: settings.deepResearch,
            voice: settings.voice,
            persona: settings.persona,
            model: settings.model,
            temperature: settings.temperature
          })
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        const assistantMessage: Message = {
          id: `msg-${Date.now()}`,
          role: 'assistant',
          content: data.message,
          timestamp: new Date(),
          metadata: {
            backend: data.backend_used,
            performance_metrics: data.performance_metrics,
            research_context: data.research_context,
            sophia_context: data.sophia_context
          }
        };

        setMessages(prev => [...prev, assistantMessage]);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: `msg-${Date.now()}`,
        role: 'system',
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error occurred'}`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      if (!isStreaming) {
        setIsLoading(false);
      }
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const toggleRecording = () => {
    setIsRecording(!isRecording);
    // TODO: Implement voice recording functionality
  };

  const getBackendIcon = (backend?: string) => {
    switch (backend) {
      case 'swarm':
        return <Brain className="w-4 h-4 text-purple-500" />;
      case 'orchestrator':
        return <Zap className="w-4 h-4 text-blue-500" />;
      default:
        return <Server className="w-4 h-4 text-gray-500" />;
    }
  };

  const getSystemStatusColor = () => {
    if (!systemStatus) return 'gray';
    switch (systemStatus.status) {
      case 'operational': return 'green';
      case 'degraded': return 'yellow';
      case 'down': return 'red';
      default: return 'gray';
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <Brain className="w-8 h-8 text-purple-600" />
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">SOPHIA Intel</h1>
            </div>
            <div className={`w-3 h-3 rounded-full bg-${getSystemStatusColor()}-500`} title="System Status" />
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            >
              <Settings className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Settings Panel */}
        {showSettings && (
          <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={settings.useSwarm}
                  onChange={(e) => setSettings(prev => ({ ...prev, useSwarm: e.target.checked }))}
                  className="rounded"
                />
                <span className="text-sm">Use Swarm</span>
              </label>
              
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={settings.webAccess}
                  onChange={(e) => setSettings(prev => ({ ...prev, webAccess: e.target.checked }))}
                  className="rounded"
                />
                <span className="text-sm">Web Access</span>
              </label>
              
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={settings.deepResearch}
                  onChange={(e) => setSettings(prev => ({ ...prev, deepResearch: e.target.checked }))}
                  className="rounded"
                />
                <span className="text-sm">Deep Research</span>
              </label>
              
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={settings.voice}
                  onChange={(e) => setSettings(prev => ({ ...prev, voice: e.target.checked }))}
                  className="rounded"
                />
                <span className="text-sm">Voice</span>
              </label>
            </div>
            
            <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Model</label>
                <select
                  value={settings.model}
                  onChange={(e) => setSettings(prev => ({ ...prev, model: e.target.value }))}
                  className="w-full p-2 border rounded-lg dark:bg-gray-600 dark:border-gray-500"
                >
                  <option value="claude-3.5-sonnet">Claude 3.5 Sonnet</option>
                  <option value="gpt-4-turbo">GPT-4 Turbo</option>
                  <option value="gemini-2.0-flash">Gemini 2.0 Flash</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Temperature</label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={settings.temperature}
                  onChange={(e) => setSettings(prev => ({ ...prev, temperature: parseFloat(e.target.value) }))}
                  className="w-full"
                />
                <span className="text-xs text-gray-500">{settings.temperature}</span>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Persona</label>
                <select
                  value={settings.persona}
                  onChange={(e) => setSettings(prev => ({ ...prev, persona: e.target.value }))}
                  className="w-full p-2 border rounded-lg dark:bg-gray-600 dark:border-gray-500"
                >
                  <option value="default">Default</option>
                  <option value="professional">Professional</option>
                  <option value="creative">Creative</option>
                  <option value="technical">Technical</option>
                </select>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-3xl p-4 rounded-lg ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : message.role === 'system'
                  ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                  : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700'
              }`}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <span className="font-medium capitalize">{message.role}</span>
                  {message.metadata?.backend && getBackendIcon(message.metadata.backend)}
                </div>
                <span className="text-xs opacity-70">
                  {message.timestamp.toLocaleTimeString()}
                </span>
              </div>
              
              <div className="prose dark:prose-invert max-w-none">
                <p className="whitespace-pre-wrap">{message.content}</p>
              </div>
              
              {message.metadata?.performance_metrics && (
                <div className="mt-2 text-xs opacity-70">
                  Response time: {message.metadata.performance_metrics.response_time?.toFixed(2)}s
                </div>
              )}
              
              {message.metadata?.research_context && (
                <div className="mt-2 p-2 bg-gray-100 dark:bg-gray-700 rounded text-xs">
                  <strong>Research Context:</strong> {message.metadata.research_context.summary}
                </div>
              )}
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                <span className="text-gray-600 dark:text-gray-400">SOPHIA is thinking...</span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 p-4">
        <div className="flex items-end space-x-2">
          <div className="flex-1">
            <textarea
              ref={inputRef}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask SOPHIA anything..."
              className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
              rows={1}
              style={{ minHeight: '44px', maxHeight: '120px' }}
            />
          </div>
          
          <button
            onClick={toggleRecording}
            className={`p-3 rounded-lg transition-colors ${
              isRecording
                ? 'bg-red-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
            disabled={isLoading}
          >
            {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
          </button>
          
          <button
            onClick={sendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className="p-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default EnhancedChatInterface;

