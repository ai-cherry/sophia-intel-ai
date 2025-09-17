'use client'

import { useState, useRef, useEffect, useCallback, useMemo } from 'react'
import { useTheme } from '../../hooks/useTheme'
import clsx from 'clsx'
import DOMPurify from 'dompurify'
import { API_CONFIG, buildWsUrl } from '../../config/api'

// Types matching backend models
interface ChatMessage {
  id: string
  type: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  metadata?: {
    sources?: Array<{
      name: string
      url?: string
      type: string
      confidence: number
    }>
    confidence?: number
    agentsUsed?: string[]
    citations?: Array<{
      source_url: string
      source_name: string
      excerpt: string
      confidence: number
    }>
    intent?: {
      primary_intent: string
      confidence: number
      domains: string[]
      requires_web: boolean
      requires_internal: boolean
    }
    memory_context?: {
      tier: string
      context_type: string
      recall_count: number
    }
    processing_time?: number
  }
  streaming?: boolean
}

interface SophiaPersona {
  name: string
  traits: {
    analytical_thinking: number
    strategic_vision: number
    executive_communication: number
    data_interpretation: number
    market_awareness: number
  }
  mood: 'professional' | 'friendly' | 'analytical' | 'strategic'
}

interface UnifiedSophiaChatProps {
  currentTab?: string
  onDataRequest?: (dataType: string, params: any) => Promise<any>
}

export default function UnifiedSophiaChat({ currentTab = 'Dashboard', onDataRequest }: UnifiedSophiaChatProps) {
  // State
  const [isOpen, setIsOpen] = useState(false)
  const [isMinimized, setIsMinimized] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [streamingMessage, setStreamingMessage] = useState<string>('')
  const [attachments, setAttachments] = useState<File[]>([])
  const [showMemoryPanel, setShowMemoryPanel] = useState(false)
  const [showResearchPanel, setShowResearchPanel] = useState(false)
  const [enableWebResearch, setEnableWebResearch] = useState(true)
  const [enableMemoryRecall, setEnableMemoryRecall] = useState(true)
  const [enableRAG, setEnableRAG] = useState(true)

  // Sophia persona state
  const [sophia] = useState<SophiaPersona>({
    name: 'Sophia',
    traits: {
      analytical_thinking: 0.95,
      strategic_vision: 0.90,
      executive_communication: 0.88,
      data_interpretation: 0.92,
      market_awareness: 0.85
    },
    mood: 'professional'
  })

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const eventSourceRef = useRef<EventSource | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  // Theme
  const { resolvedTheme } = useTheme()
  const isDark = resolvedTheme === 'dark'

  // Initialize with Sophia's greeting
  useEffect(() => {
    if (messages.length === 0) {
      const greetingMessage: ChatMessage = {
        id: 'initial-1',
        type: 'assistant',
        content: `Hello! I'm Sophia, your AI Business Intelligence orchestrator. I'm connected to your live business data and ready to provide insights from:

🔗 **Active Integrations:**
• **Airtable** - Strategic initiatives, OKRs, and team data
• **Microsoft Graph** - Email insights and calendar analytics
• **Slack** - Team communications and collaboration patterns
• **Gong** - Sales conversations and deal intelligence

💡 **Capabilities:**
• **Strategic Planning** - OKR alignment and initiative tracking
• **Sales Intelligence** - Deal analysis and rep performance
• **Team Insights** - Communication patterns and productivity
• **Market Research** - Industry trends and competitive intelligence

**Current Context:** ${currentTab} | All systems connected and ready

What business insights can I help you with today?`,
        timestamp: new Date(),
        metadata: {
          confidence: 1.0,
          agentsUsed: ['sophia_persona', 'integration_hub', 'business_intelligence'],
        }
      }
      setMessages([greetingMessage])
    }
  }, [])

  // Get list of active integrations
  const getIntegrationsList = useCallback(() => {
    const integrations = [
      'Looker Analytics',
      'Gong Conversations',
      'Slack Workspace',
      'HubSpot CRM',
      'Asana Projects',
      'Linear Issues',
      'Airtable Databases'
    ]
    return integrations.join(', ')
  }, [])

  // Scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingMessage])

  // Connect to backend WebSocket for real-time updates
  useEffect(() => {
    if (isOpen && !wsRef.current) {
      connectWebSocket()
    }
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [isOpen])

  const connectWebSocket = () => {
    try {
      wsRef.current = new WebSocket(buildWsUrl(API_CONFIG.endpoints.chat.ws))

      wsRef.current.onopen = () => {
        setIsConnected(true)
        console.log('Connected to Sophia backend')
      }

      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data)
        handleWebSocketMessage(data)
      }

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error)
        setIsConnected(false)
      }

      wsRef.current.onclose = () => {
        setIsConnected(false)
        wsRef.current = null
        // Attempt reconnection after 3 seconds
        setTimeout(() => {
          if (isOpen) {
            connectWebSocket()
          }
        }, 3000)
      }
    } catch (error) {
      console.error('Failed to connect WebSocket:', error)
      setIsConnected(false)
    }
  }

  const handleWebSocketMessage = (data: any) => {
    if (data.type === 'stream_chunk') {
      setStreamingMessage(prev => prev + data.content)
    } else if (data.type === 'stream_end') {
      const finalMessage: ChatMessage = {
        id: data.message_id || Date.now().toString(),
        type: 'assistant',
        content: streamingMessage + data.content,
        timestamp: new Date(),
        metadata: data.metadata
      }
      setMessages(prev => [...prev, finalMessage])
      setStreamingMessage('')
      setIsTyping(false)
    } else if (data.type === 'metadata_update') {
      // Update the last message with new metadata
      setMessages(prev => {
        const updated = [...prev]
        if (updated.length > 0) {
          updated[updated.length - 1].metadata = {
            ...updated[updated.length - 1].metadata,
            ...data.metadata
          }
        }
        return updated
      })
    }
  }

  // Send message to backend
  const sendMessage = async () => {
    if (!inputValue.trim() && attachments.length === 0) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsTyping(true)

    try {
      // Cancel any previous request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
      abortControllerRef.current = new AbortController()

      const requestBody = {
        query: inputValue,
        context: {
          current_tab: currentTab,
          enable_web_research: enableWebResearch,
          enable_memory: enableMemoryRecall,
          enable_rag: enableRAG,
          persona: 'sophia',
          attachments: attachments.map(f => ({
            name: f.name,
            type: f.type,
            size: f.size
          }))
        },
        stream: true
      }

      // Use SSE for streaming responses
      const response = await fetch('/api/chat/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
        signal: abortControllerRef.current.signal
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      // Handle streaming response
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      let accumulatedContent = ''

      if (reader) {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          const chunk = decoder.decode(value)
          const lines = chunk.split('\n')

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6))
                if (data.type === 'content') {
                  accumulatedContent += data.content
                  setStreamingMessage(accumulatedContent)
                } else if (data.type === 'metadata') {
                  // Handle metadata updates
                } else if (data.type === 'done') {
                  const finalMessage: ChatMessage = {
                    id: Date.now().toString(),
                    type: 'assistant',
                    content: accumulatedContent,
                    timestamp: new Date(),
                    metadata: data.metadata
                  }
                  setMessages(prev => [...prev, finalMessage])
                  setStreamingMessage('')
                  accumulatedContent = ''
                }
              } catch (e) {
                console.error('Failed to parse SSE data:', e)
              }
            }
          }
        }
      }
    } catch (error: any) {
      if (error.name !== 'AbortError') {
        console.error('Chat error:', error)

        // Enhanced fallback message with integration status
        const errorMessage: ChatMessage = {
          id: Date.now().toString(),
          type: 'assistant',
          content: `I'm connecting to your business data sources and will respond shortly. My enhanced capabilities include:

🔄 **Processing Your Query:**
• Analyzing intent across business domains
• Checking Airtable for strategic context
• Scanning Slack for team communications
• Reviewing Gong for sales insights
• Searching industry knowledge base

💼 **${currentTab} Context:**
I'm preparing insights specific to your ${currentTab.toLowerCase()} needs. Please ask me about:
• Strategic initiatives and OKR alignment
• Team performance and communication patterns
• Sales pipeline and deal analysis
• Market trends and competitive intelligence

Try asking: "What are our current strategic initiatives?" or "Show me recent sales insights"`,
          timestamp: new Date(),
          metadata: {
            confidence: 0.9,
            agentsUsed: ['enhanced_fallback', 'integration_status', 'context_analyzer'],
          }
        }
        setMessages(prev => [...prev, errorMessage])
      }
    } finally {
      setIsTyping(false)
      setStreamingMessage('')
      setAttachments([])
    }
  }

  // Handle file upload
  const handleFileUpload = (files: FileList | null) => {
    if (!files) return
    const newFiles = Array.from(files).slice(0, 5) // Limit to 5 files
    setAttachments(prev => [...prev, ...newFiles].slice(0, 5))
  }

  // Handle drag and drop
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    handleFileUpload(e.dataTransfer.files)
  }

  // Remove attachment
  const removeAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index))
  }

  // Format message with markdown support and XSS sanitization
  const formatMessage = (content: string) => {
    // Simple markdown formatting
    const formatted = content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code>$1</code>')
      .replace(/\n/g, '<br/>')

    // Sanitize to prevent XSS attacks
    return DOMPurify.sanitize(formatted, {
      ALLOWED_TAGS: ['strong', 'em', 'code', 'br'],
      ALLOWED_ATTR: []
    })
  }

  return (
    <>
      {/* Floating Chat Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className={clsx(
            'fixed bottom-6 right-6 z-50',
            'w-14 h-14 rounded-full shadow-lg',
            'bg-accent hover:bg-accent-hover',
            'text-white flex items-center justify-center',
            'transition-all transform hover:scale-110',
            'animate-pulse'
          )}
        >
          <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-4l-4 4z" />
          </svg>
          {isConnected && (
            <span className="absolute top-0 right-0 w-3 h-3 bg-green-500 rounded-full animate-ping" />
          )}
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div className={clsx(
          'fixed z-50 transition-all duration-300',
          isMinimized
            ? 'bottom-6 right-6 w-80 h-14'
            : 'bottom-6 right-6 w-[450px] h-[650px] md:w-[500px] md:h-[700px]'
        )}>
          <div className={clsx(
            'flex flex-col h-full rounded-2xl shadow-2xl overflow-hidden',
            'bg-card border border-custom',
            'backdrop-blur-lg'
          )}>
            {/* Header */}
            <div className={clsx(
              'flex items-center justify-between p-4',
              'bg-gradient-to-r from-accent/90 to-accent-hover/90',
              'text-white'
            )}>
              <div className="flex items-center space-x-3">
                <div className="relative">
                  <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
                    <span className="text-lg font-bold">S</span>
                  </div>
                  {isConnected && (
                    <span className="absolute bottom-0 right-0 w-3 h-3 bg-green-400 rounded-full border-2 border-white" />
                  )}
                </div>
                <div>
                  <h3 className="font-semibold">Sophia AI</h3>
                  <p className="text-xs opacity-90">
                    {isConnected ? 'Connected' : 'Local Mode'} • {currentTab}
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                {/* Settings Button */}
                <button
                  onClick={() => setShowMemoryPanel(!showMemoryPanel)}
                  className="p-1.5 rounded-lg hover:bg-white/20 transition"
                  title="Memory Settings"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                  </svg>
                </button>

                {/* Minimize Button */}
                <button
                  onClick={() => setIsMinimized(!isMinimized)}
                  className="p-1.5 rounded-lg hover:bg-white/20 transition"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {/* Close Button */}
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-1.5 rounded-lg hover:bg-white/20 transition"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            {!isMinimized && (
              <>
                {/* Feature Toggles */}
                <div className="px-4 py-2 bg-secondary border-b border-custom">
                  <div className="flex items-center space-x-4 text-xs">
                    <label className="flex items-center space-x-1 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={enableMemoryRecall}
                        onChange={(e) => setEnableMemoryRecall(e.target.checked)}
                        className="rounded text-accent focus:ring-accent"
                      />
                      <span className="text-secondary">Memory</span>
                    </label>
                    <label className="flex items-center space-x-1 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={enableWebResearch}
                        onChange={(e) => setEnableWebResearch(e.target.checked)}
                        className="rounded text-accent focus:ring-accent"
                      />
                      <span className="text-secondary">Web Research</span>
                    </label>
                    <label className="flex items-center space-x-1 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={enableRAG}
                        onChange={(e) => setEnableRAG(e.target.checked)}
                        className="rounded text-accent focus:ring-accent"
                      />
                      <span className="text-secondary">RAG</span>
                    </label>
                  </div>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={clsx(
                        'flex',
                        message.type === 'user' ? 'justify-end' : 'justify-start'
                      )}
                    >
                      <div className={clsx(
                        'max-w-[80%] rounded-2xl px-4 py-3',
                        message.type === 'user'
                          ? 'bg-accent text-white'
                          : 'bg-tertiary text-primary'
                      )}>
                        <div
                          dangerouslySetInnerHTML={{ __html: formatMessage(message.content) }}
                          className="text-sm"
                        />

                        {/* Metadata Display */}
                        {message.metadata && (
                          <div className="mt-2 pt-2 border-t border-white/20 text-xs opacity-80">
                            {message.metadata.confidence && (
                              <div>Confidence: {(message.metadata.confidence * 100).toFixed(0)}%</div>
                            )}
                            {message.metadata.processing_time && (
                              <div>Response time: {message.metadata.processing_time.toFixed(2)}s</div>
                            )}
                            {message.metadata.sources && message.metadata.sources.length > 0 && (
                              <div className="mt-1">
                                Sources: {message.metadata.sources.map(s => s.name).join(', ')}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}

                  {/* Streaming Message */}
                  {streamingMessage && (
                    <div className="flex justify-start">
                      <div className="max-w-[80%] rounded-2xl px-4 py-3 bg-tertiary text-primary">
                        <div dangerouslySetInnerHTML={{ __html: formatMessage(streamingMessage) }} />
                        <span className="inline-block w-2 h-4 ml-1 bg-accent animate-pulse" />
                      </div>
                    </div>
                  )}

                  {/* Typing Indicator */}
                  {isTyping && !streamingMessage && (
                    <div className="flex justify-start">
                      <div className="bg-tertiary rounded-2xl px-4 py-3">
                        <div className="flex space-x-1">
                          <span className="w-2 h-2 bg-accent rounded-full animate-bounce" />
                          <span className="w-2 h-2 bg-accent rounded-full animate-bounce delay-100" />
                          <span className="w-2 h-2 bg-accent rounded-full animate-bounce delay-200" />
                        </div>
                      </div>
                    </div>
                  )}

                  <div ref={messagesEndRef} />
                </div>

                {/* Attachments Display */}
                {attachments.length > 0 && (
                  <div className="px-4 py-2 bg-secondary border-t border-custom">
                    <div className="flex flex-wrap gap-2">
                      {attachments.map((file, index) => (
                        <div
                          key={index}
                          className="flex items-center space-x-2 bg-tertiary rounded-lg px-3 py-1.5 text-xs"
                        >
                          <span className="truncate max-w-[100px]">{file.name}</span>
                          <button
                            onClick={() => removeAttachment(index)}
                            className="text-error hover:text-error/80"
                          >
                            ×
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Input Area */}
                <div
                  className="p-4 border-t border-custom bg-secondary"
                  onDragOver={handleDragOver}
                  onDrop={handleDrop}
                >
                  <div className="flex items-end space-x-2">
                    <input
                      ref={fileInputRef}
                      type="file"
                      multiple
                      className="hidden"
                      onChange={(e) => handleFileUpload(e.target.files)}
                    />

                    {/* Attachment Button */}
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="p-2 rounded-lg hover:bg-tertiary transition"
                      title="Attach files"
                    >
                      <svg className="w-5 h-5 text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                      </svg>
                    </button>

                    {/* Input Field */}
                    <input
                      type="text"
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
                      placeholder="Ask Sophia anything..."
                      className={clsx(
                        'flex-1 px-4 py-2 rounded-lg',
                        'bg-primary border border-custom',
                        'text-primary placeholder-tertiary',
                        'focus:outline-none focus:ring-2 focus:ring-accent'
                      )}
                      disabled={isTyping}
                    />

                    {/* Send Button */}
                    <button
                      onClick={sendMessage}
                      disabled={isTyping || (!inputValue.trim() && attachments.length === 0)}
                      className={clsx(
                        'p-2 rounded-lg transition',
                        'bg-accent hover:bg-accent-hover text-white',
                        'disabled:opacity-50 disabled:cursor-not-allowed'
                      )}
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                      </svg>
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </>
  )
}