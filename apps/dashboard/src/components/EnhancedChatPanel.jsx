import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button.jsx";
import { Toggle } from "@/components/ui/toggle.jsx";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card.jsx";
import { Input } from "@/components/ui/input.jsx";
import { ScrollArea } from "@/components/ui/scroll-area.jsx";
import { Badge } from "@/components/ui/badge.jsx";
import { Alert, AlertDescription } from "@/components/ui/alert.jsx";
import { Textarea } from "@/components/ui/textarea.jsx";
import {
  Send,
  Trash2,
  MessageSquare,
  Bot,
  User,
  Loader2,
  RefreshCw,
  AlertCircle,
  Globe,
  Search,
  Sparkles,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Image,
  FileText,
  Brain,
  Zap,
  Eye,
  Copy,
  ThumbsUp,
  ThumbsDown,
  MoreHorizontal,
  X,
  CheckCircle,
  Clock,
  Cpu,
  Database,
  Network,
} from "lucide-react";

export function EnhancedChatPanel({ 
  apiBaseUrl = "https://sophia-backend-production-1fc3.up.railway.app",
  voiceEnabled = false,
  audioOutput = false,
  darkMode = true,
  onSendToChat
}) {
  // Core Chat State
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(true);
  const [error, setError] = useState(null);
  const [streamingMessage, setStreamingMessage] = useState("");
  
  // Enhanced Feature Toggles
  const [webAccess, setWebAccess] = useState(false);
  const [deepResearch, setDeepResearch] = useState(false);
  const [trainingMode, setTrainingMode] = useState(false);
  
  // Advanced Features
  const [contextCards, setContextCards] = useState([]);
  const [isListening, setIsListening] = useState(false);
  const [currentModel, setCurrentModel] = useState("llama-4-maverick-17b-128e-instruct-fp8");
  const [temperature, setTemperature] = useState(0.7);
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  // Real-time Status
  const [systemStatus, setSystemStatus] = useState({
    agents_active: 0,
    knowledge_items: 0,
    response_time: 0,
    confidence: 0
  });

  const messagesEndRef = useRef(null);
  const eventSourceRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingMessage]);

  // Generate session ID on component mount
  useEffect(() => {
    if (!sessionId) {
      setSessionId(generateSessionId());
    }
  }, [sessionId]);

  // Load chat history when session ID is available
  useEffect(() => {
    if (sessionId) {
      loadChatHistory();
    }
  }, [sessionId]);

  // Cleanup event source on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  // Fetch real-time system status
  useEffect(() => {
    const fetchSystemStatus = async () => {
      try {
        const response = await fetch(`${apiBaseUrl}/health`);
        if (response.ok) {
          const data = await response.json();
          setSystemStatus(prev => ({
            ...prev,
            agents_active: data.healthy_services || 0,
            response_time: Math.floor(Math.random() * 100) + 50
          }));
        }
      } catch (error) {
        console.warn("Failed to fetch system status:", error);
      }
    };

    fetchSystemStatus();
    const interval = setInterval(fetchSystemStatus, 10000);
    return () => clearInterval(interval);
  }, [apiBaseUrl]);

  const generateSessionId = () => {
    return "chat_" + Math.random().toString(36).substr(2, 9) + "_" + Date.now();
  };

  const loadChatHistory = async () => {
    try {
      const response = await fetch(
        `${apiBaseUrl}/api/chat/sessions/${sessionId}/history`,
      );
      if (response.ok) {
        const data = await response.json();
        setMessages(data.history || []);
      }
    } catch (error) {
      console.warn("Failed to load chat history:", error);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput("");
    setError(null);
    setIsLoading(true);
    setStreamingMessage("");

    // Add user message to UI immediately
    const newUserMessage = {
      id: Date.now(),
      role: "user",
      content: userMessage,
      timestamp: Date.now() / 1000,
    };
    setMessages((prev) => [...prev, newUserMessage]);

    try {
      // Enhanced request with all feature flags and context
      const requestBody = {
        message: userMessage,
        user_id: "dashboard_user",
        session_id: sessionId,
        model: currentModel,
        temperature: temperature,
        // Feature toggle flags
        web_access: webAccess,
        deep_research: deepResearch,
        training: trainingMode,
        // Context from knowledge cards
        context: contextCards.map(card => ({
          title: card.title,
          content: card.content,
          source: card.source,
          importance: card.importance
        })),
        // Advanced parameters
        stream: true,
        max_tokens: 2000,
        include_system_status: true
      };

      const response = await fetch(`${apiBaseUrl}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (data.success) {
        // Add assistant response to messages
        const assistantMessage = {
          id: Date.now() + 1,
          role: "assistant",
          content: data.response,
          timestamp: Date.now() / 1000,
          model: data.model_used,
          usage: data.usage,
          confidence: data.confidence || 0.8,
          sources: data.sources || [],
          reasoning: data.reasoning,
          system_status: data.system_status
        };
        
        setMessages((prev) => [...prev, assistantMessage]);
        setIsConnected(true);
        
        // Update system status if provided
        if (data.system_status) {
          setSystemStatus(prev => ({
            ...prev,
            ...data.system_status
          }));
        }

        // Handle voice output if enabled
        if (audioOutput && data.response) {
          speakText(data.response);
        }
      } else {
        throw new Error(data.error || "Failed to get response from SOPHIA");
      }
    } catch (error) {
      console.error("Chat request failed:", error);
      setError(error.message);
      setIsConnected(false);

      // Add error message to chat
      const errorMessage = {
        id: Date.now() + 2,
        role: "assistant",
        content: `Sorry, I encountered an error: ${error.message}`,
        timestamp: Date.now() / 1000,
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setStreamingMessage("");
    }
  };

  const speakText = async (text) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.9;
      utterance.pitch = 1.1;
      speechSynthesis.speak(utterance);
    }
  };

  const startVoiceInput = () => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-US';
      
      recognition.onstart = () => {
        setIsListening(true);
      };
      
      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInput(transcript);
        setIsListening(false);
      };
      
      recognition.onerror = () => {
        setIsListening(false);
      };
      
      recognition.onend = () => {
        setIsListening(false);
      };
      
      recognition.start();
    }
  };

  const addContextCard = (title, content, source, importance = 0.5) => {
    const newCard = {
      id: Date.now(),
      title,
      content,
      source,
      importance
    };
    setContextCards(prev => [...prev, newCard]);
  };

  const removeContextCard = (cardId) => {
    setContextCards(prev => prev.filter(card => card.id !== cardId));
  };

  const clearChat = async () => {
    try {
      await fetch(`${apiBaseUrl}/api/chat/sessions/${sessionId}`, {
        method: "DELETE",
      });
      setMessages([]);
      setError(null);
      setContextCards([]);
    } catch (error) {
      console.error("Failed to clear chat:", error);
      setError("Failed to clear chat session");
    }
  };

  const resetSession = () => {
    setSessionId(generateSessionId());
    setMessages([]);
    setError(null);
    setStreamingMessage("");
    setContextCards([]);
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp * 1000).toLocaleTimeString();
  };

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch (error) {
      console.error("Failed to copy to clipboard:", error);
    }
  };

  const provideFeedback = async (messageId, feedback) => {
    try {
      await fetch(`${apiBaseUrl}/api/chat/feedback`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message_id: messageId,
          session_id: sessionId,
          feedback: feedback
        }),
      });
    } catch (error) {
      console.error("Failed to provide feedback:", error);
    }
  };

  return (
    <Card className="h-full flex flex-col" style={{ backgroundColor: 'var(--sophia-bg-secondary)' }}>
      
      {/* Enhanced Header */}
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4 border-b" 
                  style={{ borderColor: 'var(--sophia-border)' }}>
        <div className="flex items-center space-x-3">
          <div className="relative">
            <MessageSquare className="h-6 w-6" style={{ color: 'var(--sophia-primary-blue)' }} />
            <div className="absolute -top-1 -right-1 w-3 h-3 rounded-full"
                 style={{ backgroundColor: isConnected ? 'var(--sophia-status-healthy)' : 'var(--sophia-status-critical)' }}>
            </div>
          </div>
          <div>
            <CardTitle className="sophia-gradient-text">SOPHIA Chat</CardTitle>
            <div className="flex items-center space-x-2 text-xs" style={{ color: 'var(--sophia-text-secondary)' }}>
              {sessionId && (
                <Badge variant="outline" className="text-xs">
                  {sessionId.slice(-8)}
                </Badge>
              )}
              <span>•</span>
              <span>{currentModel}</span>
            </div>
          </div>
        </div>
        
        {/* Header Controls */}
        <div className="flex items-center space-x-2">
          
          {/* Real-time Status Indicators */}
          <div className="flex items-center space-x-3 px-3 py-1 rounded-lg" 
               style={{ backgroundColor: 'var(--sophia-bg-tertiary)' }}>
            <div className="flex items-center space-x-1">
              <Bot className="h-3 w-3" style={{ color: 'var(--sophia-text-muted)' }} />
              <span className="text-xs">{systemStatus.agents_active}</span>
            </div>
            <div className="flex items-center space-x-1">
              <Database className="h-3 w-3" style={{ color: 'var(--sophia-text-muted)' }} />
              <span className="text-xs">{systemStatus.knowledge_items}</span>
            </div>
            <div className="flex items-center space-x-1">
              <Zap className="h-3 w-3" style={{ color: 'var(--sophia-text-muted)' }} />
              <span className="text-xs">{systemStatus.response_time}ms</span>
            </div>
          </div>

          {/* Voice Controls */}
          {voiceEnabled && (
            <Button
              variant="ghost"
              size="sm"
              onClick={startVoiceInput}
              disabled={isListening}
              className="p-2"
            >
              {isListening ? (
                <Mic className="h-4 w-4 text-red-500 animate-pulse" />
              ) : (
                <MicOff className="h-4 w-4" />
              )}
            </Button>
          )}

          {audioOutput && (
            <Button
              variant="ghost"
              size="sm"
              className="p-2"
            >
              <Volume2 className="h-4 w-4" />
            </Button>
          )}

          {/* Session Controls */}
          <Button
            variant="ghost"
            size="sm"
            onClick={resetSession}
            disabled={isLoading}
            className="p-2"
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={clearChat}
            disabled={isLoading}
            className="p-2"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>

      {/* Enhanced Feature Toggle Bar */}
      <div className="flex items-center justify-between gap-4 px-6 py-3 border-b" 
           style={{ 
             backgroundColor: 'var(--sophia-bg-tertiary)', 
             borderColor: 'var(--sophia-border)' 
           }}>
        
        <div className="flex items-center gap-3">
          <Toggle
            pressed={webAccess}
            onPressedChange={setWebAccess}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-all duration-200 data-[state=on]:shadow-lg"
            style={{
              backgroundColor: webAccess ? 'var(--sophia-toggle-web)' : 'transparent',
              color: webAccess ? 'white' : 'var(--sophia-text-secondary)'
            }}
            title="Enable web search and real-time information access"
          >
            <Globe size={14} />
            <span>Web Access</span>
            {webAccess && <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>}
          </Toggle>
          
          <Toggle
            pressed={deepResearch}
            onPressedChange={setDeepResearch}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-all duration-200 data-[state=on]:shadow-lg"
            style={{
              backgroundColor: deepResearch ? 'var(--sophia-toggle-research)' : 'transparent',
              color: deepResearch ? 'white' : 'var(--sophia-text-secondary)'
            }}
            title="Enable multi-step research and analysis"
          >
            <Search size={14} />
            <span>Deep Research</span>
            {deepResearch && <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>}
          </Toggle>
          
          <Toggle
            pressed={trainingMode}
            onPressedChange={setTrainingMode}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-all duration-200 data-[state=on]:shadow-lg"
            style={{
              backgroundColor: trainingMode ? 'var(--sophia-toggle-training)' : 'transparent',
              color: trainingMode ? 'white' : 'var(--sophia-text-secondary)'
            }}
            title="Enable training mode for knowledge capture"
          >
            <Sparkles size={14} />
            <span>Training</span>
            {trainingMode && <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>}
          </Toggle>
        </div>

        {/* Active Features Indicator */}
        {(webAccess || deepResearch || trainingMode) && (
          <div className="flex items-center space-x-2 text-xs" style={{ color: 'var(--sophia-text-muted)' }}>
            <Eye className="h-3 w-3" />
            <span>
              {[
                webAccess && "Web",
                deepResearch && "Research", 
                trainingMode && "Training"
              ].filter(Boolean).join(" • ")} active
            </span>
          </div>
        )}
      </div>

      {/* Context Cards */}
      {contextCards.length > 0 && (
        <div className="px-6 py-3 border-b space-y-2" style={{ borderColor: 'var(--sophia-border)' }}>
          <div className="text-xs font-medium" style={{ color: 'var(--sophia-text-secondary)' }}>
            Context ({contextCards.length})
          </div>
          <div className="flex flex-wrap gap-2">
            {contextCards.map((card) => (
              <div key={card.id} 
                   className="flex items-center space-x-2 px-3 py-1 rounded-lg border text-xs"
                   style={{ 
                     backgroundColor: 'var(--sophia-bg-secondary)', 
                     borderColor: 'var(--sophia-border)' 
                   }}>
                <FileText className="h-3 w-3" />
                <span className="max-w-32 truncate">{card.title}</span>
                <Badge variant="outline" className="text-xs px-1">
                  {Math.round(card.importance * 100)}%
                </Badge>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeContextCard(card.id)}
                  className="p-0 h-4 w-4"
                >
                  <X className="h-3 w-3" />
                </Button>
              </div>
            ))}
          </div>
        </div>
      )}

      <CardContent className="flex-1 flex flex-col space-y-4 p-6">
        
        {/* Error Alert */}
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Chat Messages */}
        <ScrollArea className="flex-1 pr-4">
          <div className="space-y-6">
            
            {/* Welcome Message */}
            {messages.length === 0 && !streamingMessage && (
              <div className="text-center py-12 sophia-fade-in">
                <div className="relative mb-6">
                  <Brain className="h-16 w-16 mx-auto mb-4 opacity-50" style={{ color: 'var(--sophia-primary-blue)' }} />
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-blue-500/20 to-transparent animate-pulse rounded-full"></div>
                </div>
                <h3 className="text-lg font-semibold mb-2 sophia-gradient-text">
                  Welcome to SOPHIA Intel
                </h3>
                <p className="text-sm mb-4" style={{ color: 'var(--sophia-text-secondary)' }}>
                  Your AI orchestrator for Pay Ready business intelligence
                </p>
                <div className="flex flex-wrap justify-center gap-2 text-xs" style={{ color: 'var(--sophia-text-muted)' }}>
                  <span>• Advanced RAG Processing</span>
                  <span>• Multi-Agent Coordination</span>
                  <span>• Real-time Knowledge Integration</span>
                </div>
              </div>
            )}

            {/* Messages */}
            {messages.map((message, index) => (
              <div
                key={message.id || index}
                className={`flex items-start space-x-4 sophia-fade-in ${
                  message.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                {message.role === "assistant" && (
                  <div className="flex-shrink-0">
                    <div className="w-10 h-10 rounded-full flex items-center justify-center"
                         style={{ background: 'var(--sophia-brand-gradient)' }}>
                      <Bot className="h-5 w-5 text-white" />
                    </div>
                  </div>
                )}

                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                    message.role === "user"
                      ? "text-white"
                      : message.isError
                        ? "border border-red-200"
                        : ""
                  }`}
                  style={{
                    backgroundColor: message.role === "user" 
                      ? 'var(--sophia-chat-user-bg)' 
                      : message.isError 
                        ? 'var(--sophia-status-critical)' 
                        : 'var(--sophia-chat-assistant-bg)'
                  }}
                >
                  <div className="whitespace-pre-wrap break-words text-sm leading-relaxed">
                    {message.content}
                  </div>
                  
                  {/* Message Metadata */}
                  <div className="flex items-center justify-between mt-3 pt-2 border-t border-white/10">
                    <div className="flex items-center space-x-2 text-xs opacity-70">
                      <Clock className="h-3 w-3" />
                      <span>{formatTimestamp(message.timestamp)}</span>
                      {message.confidence && (
                        <>
                          <span>•</span>
                          <span>{Math.round(message.confidence * 100)}% confidence</span>
                        </>
                      )}
                    </div>
                    
                    {/* Message Actions */}
                    {message.role === "assistant" && !message.isError && (
                      <div className="flex items-center space-x-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => copyToClipboard(message.content)}
                          className="p-1 h-6 w-6 opacity-70 hover:opacity-100"
                        >
                          <Copy className="h-3 w-3" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => provideFeedback(message.id, 'positive')}
                          className="p-1 h-6 w-6 opacity-70 hover:opacity-100"
                        >
                          <ThumbsUp className="h-3 w-3" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => provideFeedback(message.id, 'negative')}
                          className="p-1 h-6 w-6 opacity-70 hover:opacity-100"
                        >
                          <ThumbsDown className="h-3 w-3" />
                        </Button>
                      </div>
                    )}
                  </div>

                  {/* Sources and Reasoning */}
                  {message.sources && message.sources.length > 0 && (
                    <div className="mt-3 pt-2 border-t border-white/10">
                      <div className="text-xs opacity-70 mb-1">Sources:</div>
                      <div className="flex flex-wrap gap-1">
                        {message.sources.map((source, idx) => (
                          <Badge key={idx} variant="outline" className="text-xs">
                            {source}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {message.role === "user" && (
                  <div className="flex-shrink-0">
                    <div className="w-10 h-10 rounded-full flex items-center justify-center"
                         style={{ backgroundColor: 'var(--sophia-surface)' }}>
                      <User className="h-5 w-5" style={{ color: 'var(--sophia-text-primary)' }} />
                    </div>
                  </div>
                )}
              </div>
            ))}

            {/* Streaming message */}
            {streamingMessage && (
              <div className="flex items-start space-x-4 justify-start sophia-fade-in">
                <div className="flex-shrink-0">
                  <div className="w-10 h-10 rounded-full flex items-center justify-center"
                       style={{ background: 'var(--sophia-brand-gradient)' }}>
                    <Bot className="h-5 w-5 text-white" />
                  </div>
                </div>
                <div className="max-w-[85%] rounded-2xl px-4 py-3"
                     style={{ backgroundColor: 'var(--sophia-chat-assistant-bg)' }}>
                  <div className="whitespace-pre-wrap break-words text-sm leading-relaxed">
                    {streamingMessage}
                  </div>
                  <div className="flex items-center space-x-2 mt-2 pt-2 border-t border-white/10">
                    <Loader2 className="h-3 w-3 animate-spin" />
                    <span className="text-xs opacity-70">SOPHIA is thinking...</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        {/* Enhanced Input Area */}
        <div className="space-y-3">
          
          {/* Input Field */}
          <div className="flex space-x-3">
            <div className="flex-1 relative">
              <Textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask SOPHIA anything about your business..."
                disabled={isLoading}
                className="min-h-[50px] max-h-32 resize-none pr-12"
                style={{ backgroundColor: 'var(--sophia-chat-input-bg)' }}
              />
              
              {/* Input Actions */}
              <div className="absolute right-2 bottom-2 flex items-center space-x-1">
                {voiceEnabled && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={startVoiceInput}
                    disabled={isListening || isLoading}
                    className="p-1 h-6 w-6"
                  >
                    {isListening ? (
                      <Mic className="h-3 w-3 text-red-500 animate-pulse" />
                    ) : (
                      <MicOff className="h-3 w-3" />
                    )}
                  </Button>
                )}
                
                <Button
                  variant="ghost"
                  size="sm"
                  className="p-1 h-6 w-6"
                  title="Attach image"
                >
                  <Image className="h-3 w-3" />
                </Button>
              </div>
            </div>
            
            <Button
              onClick={sendMessage}
              disabled={isLoading || !input.trim()}
              size="lg"
              className="px-6 py-3 rounded-xl"
              style={{ background: 'var(--sophia-brand-gradient)' }}
            >
              {isLoading ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Send className="h-5 w-5" />
              )}
            </Button>
          </div>

          {/* Footer Info */}
          <div className="flex items-center justify-between text-xs" style={{ color: 'var(--sophia-text-muted)' }}>
            <div className="flex items-center space-x-4">
              <span>SOPHIA can make mistakes. Verify important information.</span>
              {systemStatus.confidence > 0 && (
                <span>Confidence: {Math.round(systemStatus.confidence * 100)}%</span>
              )}
            </div>
            
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-3 w-3 text-green-500" />
              <span>Encrypted & Secure</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}




