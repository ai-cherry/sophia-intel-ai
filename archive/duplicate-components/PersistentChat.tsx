import { useState, useRef, useEffect } from 'react'

interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface PersistentChatProps {
  currentTab: string
}

export default function PersistentChat({ currentTab }: PersistentChatProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'assistant',
      content: `Hello! I'm Sophia, your AI assistant. I can help you with ${currentTab.toLowerCase()} tasks and questions. How can I assist you today?`,
      timestamp: new Date()
    }
  ])
  const [inputValue, setInputValue] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Update context message when tab changes
  useEffect(() => {
    if (messages.length > 0) {
      const contextMessage: Message = {
        id: `context-${Date.now()}`,
        type: 'assistant',
        content: `I see you've switched to the ${currentTab} tab. I'm here to help with any questions about ${currentTab.toLowerCase()} functionality.`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, contextMessage])
    }
  }, [currentTab])

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsTyping(true)

    // Simulate AI response
    setTimeout(() => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: getContextualResponse(inputValue, currentTab),
        timestamp: new Date()
      }
      setMessages(prev => [...prev, assistantMessage])
      setIsTyping(false)
    }, 1500)
  }

  const getContextualResponse = (input: string, tab: string): string => {
    const lowerInput = input.toLowerCase()

    // Context-aware responses based on current tab
    if (tab === 'Dashboard' && lowerInput.includes('kpi')) {
      return "I can help you understand your KPIs. Currently showing $2.4M monthly revenue, 87% automation rate, and 156 tasks processed today. Would you like me to explain any specific metric?"
    }

    if (tab === 'Agno Agents' && lowerInput.includes('agent')) {
      return "Your Agno agent swarms are running well! Sales swarm has 3/3 agents active, Finance swarm is processing with 2/3 agents, and Customer swarm is idle with 1/3 agents. Need help with agent configuration?"
    }

    if (tab === 'Integrations' && lowerInput.includes('integration')) {
      return "All your business integrations are healthy! Looker, Gong, Slack, HubSpot, Asana, Linear, and Airtable are all connected. Microsoft 365, UserGems, and Intercom are in development. Need help with any specific integration?"
    }

    if (tab === 'Training Brain' && lowerInput.includes('training')) {
      return "Your knowledge base has 2,259 documents processed (381.6 MB). Vector embeddings are complete, knowledge graph is 73% built. Ready to upload more documents or need help with training parameters?"
    }

    if (tab === 'Project Management' && lowerInput.includes('project')) {
      return "I see 4 projects in your portfolio. Sophia AI Integration is 78% complete (high priority), Customer Portal Redesign has 6 blocked tasks, and BI Dashboard is finished. Need help with project insights?"
    }

    if (tab === 'Operations' && lowerInput.includes('system')) {
      return "System health looks good! 6/8 agents active, 3/4 integrations healthy, CPU at 34%, memory at 67%. 87% automation rate with 156 tasks processed today. What would you like to monitor?"
    }

    // Generic helpful responses
    if (lowerInput.includes('help')) {
      return `I'm here to help with ${tab.toLowerCase()}! I can explain features, provide insights, troubleshoot issues, or guide you through tasks. What specific area would you like assistance with?`
    }

    if (lowerInput.includes('status')) {
      return `Based on the ${tab} view, everything appears to be running smoothly. Is there a specific status you'd like me to check?`
    }

    return `That's a great question about ${tab.toLowerCase()}! I can help you with specific tasks, explain features, or provide detailed insights. Could you be more specific about what you'd like to know?`
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <>
      {/* Chat Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`fixed bottom-6 right-6 w-14 h-14 rounded-full shadow-lg flex items-center justify-center transition-all duration-300 z-50 ${
          isOpen ? 'bg-red-500 hover:bg-red-600' : 'bg-blue-500 hover:bg-blue-600'
        }`}
      >
        {isOpen ? (
          <span className="text-white text-xl">×</span>
        ) : (
          <span className="text-white text-xl">💬</span>
        )}
      </button>

      {/* Chat Panel */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 w-96 h-96 bg-white rounded-lg shadow-2xl border border-gray-200 flex flex-col z-40">
          {/* Chat Header */}
          <div className="p-4 border-b border-gray-200 bg-blue-500 text-white rounded-t-lg">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-medium">Sophia AI Assistant</h3>
                <p className="text-xs text-blue-100">Context: {currentTab}</p>
              </div>
              <div className="w-2 h-2 bg-green-400 rounded-full"></div>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-xs px-3 py-2 rounded-lg text-sm ${
                    message.type === 'user'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {message.content}
                  <div
                    className={`text-xs mt-1 ${
                      message.type === 'user' ? 'text-blue-100' : 'text-gray-500'
                    }`}
                  >
                    {message.timestamp.toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </div>
                </div>
              </div>
            ))}

            {isTyping && (
              <div className="flex justify-start">
                <div className="bg-gray-100 text-gray-800 px-3 py-2 rounded-lg text-sm">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-4 border-t border-gray-200">
            <div className="flex space-x-2">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask Sophia anything..."
                className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={handleSendMessage}
                disabled={!inputValue.trim()}
                className="px-4 py-2 bg-blue-500 text-white rounded-md text-sm hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Send
              </button>
            </div>
            <div className="text-xs text-gray-500 mt-2">
              Press Enter to send • Context-aware responses for {currentTab}
            </div>
          </div>
        </div>
      )}
    </>
  )
}