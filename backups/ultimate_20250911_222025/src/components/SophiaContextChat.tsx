"use client";

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { usePathname } from 'next/navigation';
import { 
  MessageSquare, X, Minimize2, Maximize2, Send, Bot, 
  Briefcase, GitBranch, Brain, Users, BarChart3, Settings,
  HelpCircle, Sparkles
} from 'lucide-react';

type Message = { 
  role: "user" | "assistant" | "system"; 
  content: string;
  timestamp?: string;
  context?: string;
};

type PageContext = {
  page: string;
  title: string;
  description: string;
  suggestedPrompts: string[];
  icon: React.ReactNode;
  metadata?: Record<string, any>;
};

function genId() {
  return Math.random().toString(36).slice(2);
}

// Page context mappings
const PAGE_CONTEXTS: Record<string, PageContext> = {
  '/projects': {
    page: 'projects',
    title: 'Project Management',
    description: 'Viewing unified project data from Asana, Linear, and Slack',
    suggestedPrompts: [
      "What are the critical risks in my projects?",
      "Show me overdue projects from Asana",
      "Which Slack channels need attention?",
      "Analyze team velocity trends"
    ],
    icon: <Briefcase className="w-4 h-4" />,
    metadata: { source: 'pm_dashboard', integrations: ['asana', 'linear', 'slack'] }
  },
  '/chat': {
    page: 'chat',
    title: 'Sophia Chat',
    description: 'Direct conversation with Sophia AI',
    suggestedPrompts: [
      "Help me understand our revenue metrics",
      "What are today's priorities?",
      "Analyze recent customer feedback",
      "Generate a status report"
    ],
    icon: <MessageSquare className="w-4 h-4" />,
    metadata: { source: 'chat_page' }
  },
  '/swarms': {
    page: 'swarms',
    title: 'Agent Swarms',
    description: 'Managing AI agent orchestration',
    suggestedPrompts: [
      "Show active agent swarms",
      "What's the swarm performance?",
      "Debug the last failed task",
      "Optimize agent allocation"
    ],
    icon: <Users className="w-4 h-4" />,
    metadata: { source: 'swarms_dashboard' }
  },
  '/brain': {
    page: 'brain',
    title: 'Knowledge Brain',
    description: 'Sophia\'s knowledge and memory system',
    suggestedPrompts: [
      "What do you know about our customers?",
      "Search for product documentation",
      "Show recent learnings",
      "Update knowledge base"
    ],
    icon: <Brain className="w-4 h-4" />,
    metadata: { source: 'brain_interface' }
  },
  '/index': {
    page: 'dashboard',
    title: 'Main Dashboard',
    description: 'System overview and metrics',
    suggestedPrompts: [
      "Show system health status",
      "What are today's metrics?",
      "Any critical alerts?",
      "Generate daily summary"
    ],
    icon: <BarChart3 className="w-4 h-4" />,
    metadata: { source: 'main_dashboard' }
  },
  '/router': {
    page: 'router',
    title: 'Model Router',
    description: 'LLM routing and optimization',
    suggestedPrompts: [
      "Show model performance stats",
      "Which model is most cost-effective?",
      "Analyze routing patterns",
      "Optimize model selection"
    ],
    icon: <GitBranch className="w-4 h-4" />,
    metadata: { source: 'model_router' }
  }
};

export default function SophiaContextChat() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [minimized, setMinimized] = useState(false);
  const [sessionId, setSessionId] = useState<string>("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [startMeta, setStartMeta] = useState<any>(null);
  const [metrics, setMetrics] = useState<{ tokens?: number; cost?: number }>({});
  const [showSuggestions, setShowSuggestions] = useState(true);
  const evtSrc = useRef<EventSource | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Get current page context
  const currentContext = useMemo(() => {
    const context = PAGE_CONTEXTS[pathname] || {
      page: 'unknown',
      title: 'Sophia AI',
      description: 'AI Assistant',
      suggestedPrompts: ["How can I help you today?"],
      icon: <Bot className="w-4 h-4" />,
      metadata: {}
    };
    return context;
  }, [pathname]);

  // Initialize session
  useEffect(() => {
    const saved = typeof window !== "undefined" ? localStorage.getItem("sophia-session") : null;
    const sid = saved || genId();
    setSessionId(sid);
    if (!saved && typeof window !== "undefined") localStorage.setItem("sophia-session", sid);
  }, []);

  // Add context message when page changes
  useEffect(() => {
    if (sessionId && open) {
      const contextMessage: Message = {
        role: "system",
        content: `Now viewing: ${currentContext.title}`,
        context: currentContext.page,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, contextMessage]);
      setShowSuggestions(true);
    }
  }, [pathname, sessionId, open, currentContext]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = useCallback(async (text?: string) => {
    const messageText = text || input.trim();
    if (!messageText || streaming) return;
    
    // Build context payload with current page information
    const payload = {
      message: messageText,
      sessionId,
      context: {
        path: pathname,
        page: currentContext.page,
        title: currentContext.title,
        metadata: currentContext.metadata,
        timestamp: new Date().toISOString()
      },
    };
    
    setMessages((m) => [...m, { 
      role: "user", 
      content: messageText,
      timestamp: new Date().toISOString()
    }]);
    setInput("");
    setStreaming(true);
    setShowSuggestions(false);

    try {
      // Start SSE handshake
      const resp = await fetch("/api/sophia/chat/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      
      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}`);
      }
      
      const { stream_url } = await resp.json();
      const url = stream_url || "/events";
      const es = new EventSource(url);
      evtSrc.current = es;
      let buffer = "";
      
      es.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data);
          
          // Handle metadata
          if (data?.data?.type === "start" || data?.type === "start") {
            const meta = data?.data?.metadata || data?.metadata;
            if (meta) setStartMeta(meta);
          }
          
          const meta = data?.data?.metadata || data?.metadata;
          if (meta && (meta.tokens || meta.cost)) {
            setMetrics((m) => ({ 
              tokens: meta.tokens ?? m.tokens, 
              cost: meta.cost ?? m.cost 
            }));
          }
          
          // Handle content
          if (data?.data?.data?.content) {
            buffer += data.data.data.content;
            setMessages((m) => {
              const last = m[m.length - 1];
              if (last && last.role === "assistant") {
                const copy = m.slice();
                copy[copy.length - 1] = { 
                  role: "assistant", 
                  content: buffer,
                  timestamp: new Date().toISOString()
                };
                return copy;
              }
              return [...m, { 
                role: "assistant", 
                content: buffer,
                timestamp: new Date().toISOString()
              }];
            });
          }
        } catch (e) {
          console.error('Parse error:', e);
        }
      };
      
      es.onerror = () => {
        es.close();
        evtSrc.current = null;
        setStreaming(false);
      };
    } catch (error) {
      setStreaming(false);
      setMessages((m) => [...m, { 
        role: "assistant", 
        content: "Sorry, I encountered an error. Please try again.",
        timestamp: new Date().toISOString()
      }]);
    }
  }, [input, sessionId, streaming, pathname, currentContext]);

  // Handle suggested prompts
  const handleSuggestedPrompt = (prompt: string) => {
    setInput(prompt);
    send(prompt);
  };

  return (
    <>
      {/* Chat Widget */}
      <div 
        className={`fixed z-50 transition-all duration-300 ${
          minimized ? 'bottom-4 right-4' : 'bottom-4 right-4'
        }`} 
        data-testid="sophia-context-chat"
      >
        {open && !minimized && (
          <div className="w-96 h-[600px] border rounded-lg shadow-xl bg-white dark:bg-gray-900 flex flex-col">
            {/* Header */}
            <div className="px-4 py-3 border-b bg-gradient-to-r from-blue-50 to-purple-50 dark:from-gray-800 dark:to-gray-900 rounded-t-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 bg-white dark:bg-gray-700 rounded-full">
                    <Bot className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div>
                    <div className="font-semibold text-gray-900 dark:text-white">Sophia AI</div>
                    <div className="text-xs text-gray-600 dark:text-gray-400 flex items-center gap-1">
                      {currentContext.icon}
                      {currentContext.title}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <button 
                    className="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-md transition-colors"
                    onClick={() => setMinimized(true)}
                    title="Minimize"
                  >
                    <Minimize2 className="w-4 h-4" />
                  </button>
                  <button 
                    className="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-md transition-colors"
                    onClick={() => setOpen(false)}
                    title="Close"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>

            {/* Metrics Bar */}
            {startMeta && (
              <div className="px-3 py-2 text-xs bg-gray-50 dark:bg-gray-800 border-b flex items-center gap-2 overflow-x-auto">
                <span className="inline-flex items-center rounded bg-white dark:bg-gray-700 px-2 py-0.5 border">
                  Session: {sessionId.slice(0, 6)}
                </span>
                {typeof metrics.tokens === 'number' && (
                  <span className="inline-flex items-center rounded bg-white dark:bg-gray-700 px-2 py-0.5 border">
                    Tokens: {metrics.tokens}
                  </span>
                )}
                {typeof metrics.cost === 'number' && (
                  <span className="inline-flex items-center rounded bg-white dark:bg-gray-700 px-2 py-0.5 border">
                    Cost: ${metrics.cost.toFixed(4)}
                  </span>
                )}
              </div>
            )}

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {/* Welcome message if no messages */}
              {messages.length === 0 && (
                <div className="text-center py-8">
                  <Sparkles className="w-12 h-12 mx-auto text-purple-500 mb-3" />
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                    Hi! I'm Sophia, your AI assistant
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                    I'm aware you're on the {currentContext.title} page. 
                    How can I help you today?
                  </p>
                </div>
              )}

              {/* Suggested prompts */}
              {showSuggestions && messages.length === 0 && (
                <div className="space-y-2">
                  <p className="text-xs text-gray-500 dark:text-gray-400 font-medium">
                    Suggested questions:
                  </p>
                  {currentContext.suggestedPrompts.map((prompt, idx) => (
                    <button
                      key={idx}
                      className="w-full text-left p-2.5 text-sm bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors border border-gray-200 dark:border-gray-700"
                      onClick={() => handleSuggestedPrompt(prompt)}
                    >
                      <HelpCircle className="w-3 h-3 inline mr-2 text-gray-400" />
                      {prompt}
                    </button>
                  ))}
                </div>
              )}

              {/* Messages */}
              {messages.map((m, i) => (
                <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                  {m.role === "system" ? (
                    <div className="text-center w-full">
                      <div className="inline-block px-3 py-1 bg-gray-100 dark:bg-gray-800 rounded-full text-xs text-gray-600 dark:text-gray-400">
                        {m.content}
                      </div>
                    </div>
                  ) : (
                    <div className={`max-w-[80%] ${m.role === "user" ? "order-2" : ""}`}>
                      <div className={`px-3 py-2 rounded-lg ${
                        m.role === "user" 
                          ? "bg-blue-600 text-white" 
                          : "bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white"
                      }`}>
                        <div className="text-sm whitespace-pre-wrap">{m.content}</div>
                        {m.timestamp && (
                          <div className={`text-xs mt-1 ${
                            m.role === "user" ? "text-blue-100" : "text-gray-500 dark:text-gray-400"
                          }`}>
                            {new Date(m.timestamp).toLocaleTimeString()}
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
              
              {streaming && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 dark:bg-gray-800 rounded-lg px-3 py-2">
                    <div className="flex items-center gap-2">
                      <div className="animate-pulse flex gap-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-3 border-t bg-gray-50 dark:bg-gray-800">
              <div className="flex gap-2">
                <input
                  data-testid="sophia-context-input"
                  className="flex-1 border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder={`Ask about ${currentContext.title.toLowerCase()}...`}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      send();
                    }
                  }}
                  disabled={streaming}
                />
                <button 
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-1"
                  onClick={() => send()} 
                  disabled={streaming || !input.trim()}
                >
                  <Send className="w-4 h-4" />
                  Send
                </button>
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-2 text-center">
                Context-aware AI • Press Enter to send
              </div>
            </div>
          </div>
        )}

        {/* Minimized State */}
        {open && minimized && (
          <div className="bg-white dark:bg-gray-900 border rounded-lg shadow-xl p-3 flex items-center gap-3">
            <Bot className="w-5 h-5 text-blue-600" />
            <span className="font-medium">Sophia AI</span>
            <button 
              className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
              onClick={() => setMinimized(false)}
            >
              <Maximize2 className="w-4 h-4" />
            </button>
            <button 
              className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
              onClick={() => setOpen(false)}
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Floating Action Button */}
        {!open && (
          <button 
            data-testid="sophia-chat-toggle" 
            className="group flex items-center gap-2 px-4 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-full shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200"
            onClick={() => setOpen(true)}
          >
            <div className="relative">
              <Bot className="w-5 h-5" />
              <div className="absolute -top-1 -right-1 w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            </div>
            <span className="font-medium">Chat with Sophia</span>
            <div className="text-xs opacity-90">
              {currentContext.title}
            </div>
          </button>
        )}
      </div>
    </>
  );
}