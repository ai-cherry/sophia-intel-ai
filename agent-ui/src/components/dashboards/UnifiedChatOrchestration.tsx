'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { decodeBase64Audio } from '@/lib/audio';
import {
  Mic, MicOff, Volume2, VolumeX, Send, Bot, User, Zap, Brain,
  Heart, Target, MessageCircle, Phone, History, Search, Settings,
  Play, Pause, SkipForward, SkipBack, RefreshCw, Eye, EyeOff,
  FileText, Download, Upload, Copy, ExternalLink, Star, Flag,
  CheckCircle, XCircle, AlertTriangle, Clock, Users, Activity,
  Headphones, Speaker, Radio, Waves, Circle, Square
} from 'lucide-react';

// ==================== TYPES ====================

interface ChatMessage {
  id: string;
  content: string;
  sender: 'user' | 'agent';
  agent_id?: string;
  agent_name?: string;
  timestamp: string;
  message_type: 'text' | 'audio' | 'image' | 'file' | 'function_call';
  audio_url?: string;
  audio_duration?: number;
  metadata?: {
    confidence_score?: number;
    sentiment?: 'positive' | 'negative' | 'neutral';
    intent?: string;
    entities?: string[];
    function_name?: string;
    function_args?: any;
  };
  context?: {
    dashboard_context?: string;
    selected_items?: string[];
    current_view?: string;
  };
}

interface Agent {
  id: string;
  name: string;
  persona: string;
  description: string;
  capabilities: string[];
  status: 'active' | 'busy' | 'offline' | 'initializing';
  specialties: string[];
  current_context?: string;
  confidence_in_handling: number;
  average_response_time: number;
  success_rate: number;
  avatar_color: string;
  voice_enabled: boolean;
  voice_model?: string;
}

interface VoiceSession {
  id: string;
  is_active: boolean;
  current_agent?: string;
  start_time: string;
  duration: number;
  input_method: 'push_to_talk' | 'voice_activation' | 'continuous';
  noise_suppression: boolean;
  auto_transcription: boolean;
  real_time_feedback: boolean;
}

interface ConversationContext {
  dashboard: 'hermes' | 'asclepius' | 'athena' | 'unified' | null;
  selected_items: string[];
  recent_actions: string[];
  user_preferences: {
    preferred_agent?: string;
    voice_enabled: boolean;
    auto_routing: boolean;
    context_retention: boolean;
  };
  conversation_history_summary: string;
}

// ==================== UNIFIED CHAT ORCHESTRATION ====================

const UnifiedChatOrchestration: React.FC = () => {
  // Core State
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(false);
  const [currentAgent, setCurrentAgent] = useState<Agent | null>(null);

  // Chat State
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [conversationContext, setConversationContext] = useState<ConversationContext>({
    dashboard: null,
    selected_items: [],
    recent_actions: [],
    user_preferences: {
      voice_enabled: true,
      auto_routing: true,
      context_retention: true
    },
    conversation_history_summary: ''
  });

  // Voice State
  const [voiceSession, setVoiceSession] = useState<VoiceSession | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [playingAudio, setPlayingAudio] = useState<string | null>(null);
  const [voiceSettings, setVoiceSettings] = useState({
    input_method: 'push_to_talk' as const,
    noise_suppression: true,
    auto_transcription: true,
    real_time_feedback: true,
    voice_model: 'eleven_labs_default'
  });

  // Agent State
  const [availableAgents, setAvailableAgents] = useState<Agent[]>([]);
  const [agentSuggestions, setAgentSuggestions] = useState<Agent[]>([]);

  // UI State
  const [activeTab, setActiveTab] = useState('chat');
  const [showHistory, setShowHistory] = useState(false);
  const [showAgentPanel, setShowAgentPanel] = useState(true);

  // Refs
  const ws = useRef<WebSocket | null>(null);
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const audioContext = useRef<AudioContext | null>(null);
  const analyser = useRef<AnalyserNode | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  // ==================== WEBSOCKET & INITIALIZATION ====================

  useEffect(() => {
    initializeAudioContext();
    connectWebSocket();
    loadAvailableAgents();

    return () => {
      if (ws.current) ws.current.close();
      if (mediaRecorder.current) mediaRecorder.current.stop();
      if (audioContext.current) audioContext.current.close();
    };
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const initializeAudioContext = async () => {
    try {
      audioContext.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      analyser.current = audioContext.current.createAnalyser();
      analyser.current.fftSize = 256;
    } catch (error) {
      console.error('Audio context initialization failed:', error);
    }
  };

  const connectWebSocket = () => {
    try {
      ws.current = new WebSocket('/ws/unified-chat');

      ws.current.onopen = () => {
        setConnected(true);
        sendCommand({ type: 'initialize_session', context: conversationContext });
      };

      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      };

      ws.current.onclose = () => {
        setConnected(false);
        setTimeout(connectWebSocket, 3000);
      };
    } catch (error) {
      console.error('WebSocket connection failed:', error);
      setConnected(false);
    }
  };

  const loadAvailableAgents = async () => {
    try {
      const response = await fetch('/api/agents/available');
      if (response.ok) {
        const agents = await response.json();
        setAvailableAgents(agents);
      }
    } catch (error) {
      console.error('Failed to load available agents:', error);
    }
  };

  // ==================== WEBSOCKET MESSAGE HANDLING ====================

  const handleWebSocketMessage = (data: any) => {
    switch (data.type) {
      case 'agent_response':
        addMessage({
          id: data.message_id,
          content: data.content,
          sender: 'agent',
          agent_id: data.agent_id,
          agent_name: data.agent_name,
          timestamp: data.timestamp,
          message_type: data.message_type,
          audio_url: data.audio_url,
          metadata: data.metadata
        });
        setIsTyping(false);
        break;

      case 'agent_typing':
        setIsTyping(true);
        setCurrentAgent(availableAgents.find(a => a.id === data.agent_id) || null);
        break;

      case 'agent_suggestion':
        setAgentSuggestions(data.suggested_agents);
        break;

      case 'context_update':
        setConversationContext(prev => ({ ...prev, ...data.context }));
        break;

      case 'voice_response':
        if (data.audio_data) {
          playAudioResponse(data.audio_data);
        }
        break;

      case 'function_call_result':
        addMessage({
          id: data.message_id,
          content: `Function executed: ${data.function_name}`,
          sender: 'agent',
          timestamp: data.timestamp,
          message_type: 'function_call',
          metadata: {
            function_name: data.function_name,
            function_args: data.function_args
          }
        });
        break;

      case 'agent_switched':
        setCurrentAgent(availableAgents.find(a => a.id === data.new_agent_id) || null);
        addMessage({
          id: `switch_${Date.now()}`,
          content: `Switched to ${data.new_agent_name} for better assistance.`,
          sender: 'agent',
          timestamp: new Date().toISOString(),
          message_type: 'text'
        });
        break;
    }
  };

  // ==================== MESSAGE HANDLING ====================

  const sendCommand = (command: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(command));
    }
  };

  const addMessage = (message: ChatMessage) => {
    setMessages(prev => [...prev, message]);
  };

  const sendTextMessage = async () => {
    if (!inputText.trim() || !connected) return;

    const userMessage: ChatMessage = {
      id: `user_${Date.now()}`,
      content: inputText,
      sender: 'user',
      timestamp: new Date().toISOString(),
      message_type: 'text',
      context: {
        dashboard_context: conversationContext.dashboard || undefined,
        selected_items: conversationContext.selected_items,
        current_view: activeTab
      }
    };

    addMessage(userMessage);
    setInputText('');
    setIsTyping(true);

    // Send to backend for processing
    sendCommand({
      type: 'user_message',
      message: userMessage,
      context: conversationContext,
      preferred_agent: currentAgent?.id
    });
  };

  // ==================== VOICE HANDLING ====================

  const startVoiceRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: voiceSettings.noise_suppression,
          autoGainControl: true
        }
      });

      mediaRecorder.current = new MediaRecorder(stream);
      const audioChunks: Blob[] = [];

      mediaRecorder.current.ondataavailable = (event) => {
        audioChunks.push(event.data);
      };

      mediaRecorder.current.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        await processVoiceInput(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      // Connect audio analysis for real-time feedback
      if (audioContext.current && analyser.current) {
        const source = audioContext.current.createMediaStreamSource(stream);
        source.connect(analyser.current);
        startAudioLevelMonitoring();
      }

      mediaRecorder.current.start();
      setIsRecording(true);

      // Create voice session
      setVoiceSession({
        id: `voice_${Date.now()}`,
        is_active: true,
        current_agent: currentAgent?.id,
        start_time: new Date().toISOString(),
        duration: 0,
        input_method: voiceSettings.input_method,
        noise_suppression: voiceSettings.noise_suppression,
        auto_transcription: voiceSettings.auto_transcription,
        real_time_feedback: voiceSettings.real_time_feedback
      });

    } catch (error) {
      console.error('Failed to start voice recording:', error);
    }
  };

  const stopVoiceRecording = () => {
    if (mediaRecorder.current && isRecording) {
      mediaRecorder.current.stop();
      setIsRecording(false);
      setAudioLevel(0);

      if (voiceSession) {
        setVoiceSession(prev => prev ? { ...prev, is_active: false } : null);
      }
    }
  };

  const startAudioLevelMonitoring = () => {
    if (!analyser.current) return;

    const dataArray = new Uint8Array(analyser.current.frequencyBinCount);

    const updateAudioLevel = () => {
      if (!analyser.current || !isRecording) return;

      analyser.current.getByteFrequencyData(dataArray);
      const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
      setAudioLevel(Math.min(100, (average / 128) * 100));

      if (isRecording) {
        requestAnimationFrame(updateAudioLevel);
      }
    };

    updateAudioLevel();
  };

  const processVoiceInput = async (audioBlob: Blob) => {
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'voice_input.wav');
      formData.append('context', JSON.stringify(conversationContext));
      formData.append('voice_settings', JSON.stringify(voiceSettings));

      const response = await fetch('/api/voice/process', {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        const result = await response.json();

        if (result.transcription) {
          // Add user message with transcription
          addMessage({
            id: `voice_${Date.now()}`,
            content: result.transcription,
            sender: 'user',
            timestamp: new Date().toISOString(),
            message_type: 'audio',
            metadata: {
              confidence_score: result.confidence,
              intent: result.intent,
              entities: result.entities
            }
          });

          // Process the transcription
          setIsTyping(true);
          sendCommand({
            type: 'voice_message',
            transcription: result.transcription,
            context: conversationContext,
            metadata: result.metadata,
            preferred_agent: currentAgent?.id
          });
        }
      }
    } catch (error) {
      console.error('Failed to process voice input:', error);
    }
  };

  const playAudioResponse = async (audioData: string) => {
    try {
      const audioUrl = decodeBase64Audio(audioData, 'audio/mpeg');

      if (audioRef.current) {
        audioRef.current.src = audioUrl;
        audioRef.current.play();
        setPlayingAudio(audioUrl);
      }
    } catch (error) {
      console.error('Failed to play audio response:', error);
    }
  };

  // ==================== AGENT SWITCHING ====================

  const switchToAgent = (agent: Agent) => {
    setCurrentAgent(agent);
    sendCommand({
      type: 'switch_agent',
      agent_id: agent.id,
      context: conversationContext
    });
  };

  const getAgentRecommendation = async (message: string) => {
    try {
      const response = await fetch('/api/agents/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          context: conversationContext,
          current_agent: currentAgent?.id
        })
      });

      if (response.ok) {
        const recommendations = await response.json();
        setAgentSuggestions(recommendations);
      }
    } catch (error) {
      console.error('Failed to get agent recommendations:', error);
    }
  };

  // ==================== UTILITY FUNCTIONS ====================

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const exportConversation = () => {
    const conversationData = {
      messages,
      context: conversationContext,
      agents_used: [...new Set(messages.filter(m => m.agent_id).map(m => m.agent_id))],
      export_time: new Date().toISOString()
    };

    const blob = new Blob([JSON.stringify(conversationData, null, 2)], {
      type: 'application/json'
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `conversation_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // ==================== RENDER METHODS ====================

  const renderMessage = (message: ChatMessage) => (
    <div key={message.id} className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-[70%] ${message.sender === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-100 dark:bg-gray-800'} rounded-lg p-3`}>
        {message.sender === 'agent' && message.agent_name && (
          <div className="text-xs opacity-70 mb-1">
            {message.agent_name}
          </div>
        )}

        <div className="text-sm">{message.content}</div>

        {message.message_type === 'audio' && message.audio_url && (
          <div className="flex items-center space-x-2 mt-2">
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                if (audioRef.current) {
                  audioRef.current.src = message.audio_url!;
                  audioRef.current.play();
                }
              }}
            >
              <Play className="w-3 h-3" />
            </Button>
            {message.audio_duration && (
              <span className="text-xs opacity-70">
                {Math.round(message.audio_duration)}s
              </span>
            )}
          </div>
        )}

        {message.metadata?.confidence_score && (
          <div className="text-xs opacity-70 mt-1">
            Confidence: {Math.round(message.metadata.confidence_score * 100)}%
          </div>
        )}

        <div className="text-xs opacity-50 mt-1">
          {formatTimestamp(message.timestamp)}
        </div>
      </div>
    </div>
  );

  const renderAgentCard = (agent: Agent, isRecommended: boolean = false) => (
    <Card
      key={agent.id}
      className={`cursor-pointer transition-all hover:shadow-md ${
        currentAgent?.id === agent.id ? 'ring-2 ring-blue-500' : ''
      } ${isRecommended ? 'border-yellow-300' : ''}`}
      onClick={() => switchToAgent(agent)}
    >
      <CardContent className="p-3">
        <div className="flex items-center space-x-2 mb-2">
          <div
            className={`w-3 h-3 rounded-full`}
            style={{ backgroundColor: agent.avatar_color }}
          ></div>
          <span className="font-medium text-sm">{agent.name}</span>
          <Badge variant={agent.status === 'active' ? 'default' : 'secondary'} className="text-xs">
            {agent.status}
          </Badge>
        </div>

        <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
          {agent.description}
        </p>

        <div className="flex flex-wrap gap-1 mb-2">
          {agent.capabilities.slice(0, 2).map((capability) => (
            <Badge key={capability} variant="outline" className="text-xs">
              {capability}
            </Badge>
          ))}
          {agent.capabilities.length > 2 && (
            <Badge variant="outline" className="text-xs">
              +{agent.capabilities.length - 2}
            </Badge>
          )}
        </div>

        <div className="flex justify-between text-xs text-gray-500">
          <span>Confidence: {agent.confidence_in_handling}%</span>
          <span>{agent.average_response_time}ms</span>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="h-screen bg-gradient-to-br from-indigo-50 to-purple-100 dark:from-gray-900 dark:to-gray-950 flex">
      {/* Left Sidebar - Agent Panel */}
      {showAgentPanel && (
        <div className="w-80 border-r bg-white/80 dark:bg-gray-900/80 backdrop-blur-lg">
          <div className="p-4 border-b">
            <h2 className="text-lg font-bold text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-purple-600">
              AI Agents
            </h2>
            <p className="text-xs text-gray-600 dark:text-gray-400">
              Smart routing and context-aware assistance
            </p>
          </div>

          <Tabs defaultValue="available" className="flex-1">
            <TabsList className="grid w-full grid-cols-2 m-2">
              <TabsTrigger value="available">Available</TabsTrigger>
              <TabsTrigger value="suggestions">Suggestions</TabsTrigger>
            </TabsList>

            <TabsContent value="available" className="p-2 space-y-2">
              <ScrollArea className="h-[calc(100vh-200px)]">
                {availableAgents.map((agent) => renderAgentCard(agent))}
              </ScrollArea>
            </TabsContent>

            <TabsContent value="suggestions" className="p-2 space-y-2">
              <ScrollArea className="h-[calc(100vh-200px)]">
                {agentSuggestions.length > 0 ? (
                  agentSuggestions.map((agent) => renderAgentCard(agent, true))
                ) : (
                  <div className="text-center text-gray-500 py-8">
                    <Bot className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">No suggestions yet</p>
                    <p className="text-xs">Start a conversation to get agent recommendations</p>
                  </div>
                )}
              </ScrollArea>
            </TabsContent>
          </Tabs>
        </div>
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="border-b bg-white/80 dark:bg-gray-900/80 backdrop-blur-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <MessageCircle className="w-6 h-6 text-indigo-600" />
                <h1 className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-purple-600">
                  Sophia Intelligence
                </h1>
              </div>

              {currentAgent && (
                <div className="flex items-center space-x-2 px-3 py-1 bg-gray-100 dark:bg-gray-800 rounded-full">
                  <div
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: currentAgent.avatar_color }}
                  ></div>
                  <span className="text-sm font-medium">{currentAgent.name}</span>
                  <Badge variant="outline" className="text-xs">
                    {currentAgent.persona}
                  </Badge>
                </div>
              )}
            </div>

            <div className="flex items-center space-x-2">
              {/* Voice Controls */}
              <div className="flex items-center space-x-1 px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded">
                <Button
                  size="sm"
                  variant="ghost"
                  className="p-1"
                  onClick={() => setVoiceSettings(prev => ({ ...prev, input_method: 'push_to_talk' }))}
                >
                  <Radio className={`w-3 h-3 ${voiceSettings.input_method === 'push_to_talk' ? 'text-blue-600' : 'text-gray-400'}`} />
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  className="p-1"
                  onClick={() => setVoiceSettings(prev => ({ ...prev, input_method: 'voice_activation' }))}
                >
                  <Waves className={`w-3 h-3 ${voiceSettings.input_method === 'voice_activation' ? 'text-blue-600' : 'text-gray-400'}`} />
                </Button>
              </div>

              {/* Connection Status */}
              <Badge variant={connected ? 'default' : 'destructive'} className="text-xs">
                {connected ? 'Connected' : 'Disconnected'}
              </Badge>

              {/* Controls */}
              <Button
                size="sm"
                variant="outline"
                onClick={() => setShowHistory(!showHistory)}
              >
                <History className="w-4 h-4" />
              </Button>

              <Button
                size="sm"
                variant="outline"
                onClick={exportConversation}
              >
                <Download className="w-4 h-4" />
              </Button>

              <Button
                size="sm"
                variant="outline"
                onClick={() => setShowAgentPanel(!showAgentPanel)}
              >
                {showAgentPanel ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </Button>
            </div>
          </div>
        </div>

        {/* Messages Area */}
        <ScrollArea className="flex-1 p-4">
          <div className="max-w-4xl mx-auto">
            {messages.length === 0 ? (
              <div className="text-center py-16">
                <Bot className="w-16 h-16 mx-auto mb-4 text-gray-400" />
                <h3 className="text-lg font-medium text-gray-600 dark:text-gray-400 mb-2">
                  Welcome to Sophia Intelligence
                </h3>
                <p className="text-gray-500 mb-4">
                  Start a conversation with natural language or voice commands
                </p>
                <div className="flex justify-center space-x-2">
                  <Badge variant="outline">Ask about sales performance</Badge>
                  <Badge variant="outline">Check client health</Badge>
                  <Badge variant="outline">Review project status</Badge>
                </div>
              </div>
            ) : (
              <>
                {messages.map(renderMessage)}
                {isTyping && currentAgent && (
                  <div className="flex justify-start mb-4">
                    <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-3">
                      <div className="text-xs opacity-70 mb-1">
                        {currentAgent.name}
                      </div>
                      <div className="flex items-center space-x-1">
                        <div className="flex space-x-1">
                          <Circle className="w-2 h-2 fill-current animate-bounce" />
                          <Circle className="w-2 h-2 fill-current animate-bounce" style={{ animationDelay: '0.1s' }} />
                          <Circle className="w-2 h-2 fill-current animate-bounce" style={{ animationDelay: '0.2s' }} />
                        </div>
                        <span className="text-xs opacity-70">thinking...</span>
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        {/* Input Area */}
        <div className="border-t bg-white/80 dark:bg-gray-900/80 backdrop-blur-lg p-4">
          <div className="max-w-4xl mx-auto">
            {/* Voice Recording Indicator */}
            {isRecording && (
              <div className="mb-3 p-3 bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                    <span className="text-sm text-red-700 dark:text-red-300">Recording...</span>
                    {voiceSession && (
                      <span className="text-xs text-red-600 dark:text-red-400">
                        {Math.round((Date.now() - new Date(voiceSession.start_time).getTime()) / 1000)}s
                      </span>
                    )}
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-16 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div
                        className="bg-red-500 h-2 rounded-full transition-all duration-100"
                        style={{ width: `${audioLevel}%` }}
                      ></div>
                    </div>
                    <Button size="sm" variant="destructive" onClick={stopVoiceRecording}>
                      <Square className="w-3 h-3" />
                    </Button>
                  </div>
                </div>
              </div>
            )}

            <div className="flex space-x-2">
              {/* Voice Input Button */}
              <Button
                variant={isRecording ? 'destructive' : 'outline'}
                size="lg"
                onMouseDown={voiceSettings.input_method === 'push_to_talk' ? startVoiceRecording : undefined}
                onMouseUp={voiceSettings.input_method === 'push_to_talk' ? stopVoiceRecording : undefined}
                onClick={voiceSettings.input_method === 'voice_activation' ?
                  (isRecording ? stopVoiceRecording : startVoiceRecording) : undefined}
                disabled={!connected}
              >
                {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
              </Button>

              {/* Text Input */}
              <Input
                ref={inputRef}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && sendTextMessage()}
                placeholder="Type a message or use voice input..."
                className="flex-1 text-base"
                disabled={!connected || isRecording}
              />

              {/* Send Button */}
              <Button
                onClick={sendTextMessage}
                disabled={!inputText.trim() || !connected || isRecording}
                size="lg"
              >
                <Send className="w-5 h-5" />
              </Button>
            </div>

            {/* Quick Actions */}
            <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
              <div className="flex space-x-4">
                <button onClick={() => setInputText("Show me today's sales performance")}>
                  Sales Dashboard
                </button>
                <button onClick={() => setInputText("What clients need attention?")}>
                  Client Health
                </button>
                <button onClick={() => setInputText("Are there any project blockers?")}>
                  Project Status
                </button>
              </div>

              <div className="flex items-center space-x-2">
                {conversationContext.dashboard && (
                  <Badge variant="outline" className="text-xs">
                    Context: {conversationContext.dashboard}
                  </Badge>
                )}
                {voiceSettings.input_method === 'push_to_talk' && (
                  <span>Hold to talk</span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Audio Element */}
      <audio
        ref={audioRef}
        onEnded={() => setPlayingAudio(null)}
        className="hidden"
      />
    </div>
  );
};

export default UnifiedChatOrchestration;
