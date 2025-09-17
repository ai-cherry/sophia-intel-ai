import { useState, useEffect } from 'react'

interface FlowiseConfig {
  url: string
  status: 'connected' | 'disconnected' | 'error'
}

export default function FlowiseTab() {
  const [flowiseConfig, setFlowiseConfig] = useState<FlowiseConfig>({
    url: 'http://localhost:3000',
    status: 'disconnected'
  })

  useEffect(() => {
    // Check Flowise connection
    checkFlowiseConnection()
  }, [])

  const checkFlowiseConnection = async () => {
    try {
      const response = await fetch('/api/flowise/health')
      if (response.ok) {
        setFlowiseConfig(prev => ({ ...prev, status: 'connected' }))
      } else {
        setFlowiseConfig(prev => ({ ...prev, status: 'error' }))
      }
    } catch (error) {
      setFlowiseConfig(prev => ({ ...prev, status: 'error' }))
    }
  }

  const StatusIndicator = () => {
    const statusColors = {
      connected: 'bg-green-500',
      disconnected: 'bg-yellow-500',
      error: 'bg-red-500'
    }

    return (
      <div className="flex items-center space-x-2">
        <div className={`w-3 h-3 rounded-full ${statusColors[flowiseConfig.status]}`} />
        <span className="text-sm font-medium">
          {flowiseConfig.status === 'connected' ? 'Connected' :
           flowiseConfig.status === 'disconnected' ? 'Disconnected' : 'Error'}
        </span>
      </div>
    )
  }

  return (
    <div className="h-full">
      <div className="mb-4 flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Employee Agent Builder</h2>
          <p className="text-gray-600">Build custom AI agents with visual workflows</p>
        </div>
        <StatusIndicator />
      </div>

      {flowiseConfig.status === 'connected' ? (
        <div className="border rounded-lg overflow-hidden" style={{ height: 'calc(100vh - 200px)' }}>
          <iframe
            src={flowiseConfig.url}
            className="w-full h-full border-0"
            title="Flowise Agent Builder"
            sandbox="allow-same-origin allow-scripts allow-forms"
          />
        </div>
      ) : (
        <div className="flex items-center justify-center h-96 border-2 border-dashed border-gray-300 rounded-lg">
          <div className="text-center">
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Flowise Not Available
            </h3>
            <p className="text-gray-500 mb-4">
              Unable to connect to Flowise service at {flowiseConfig.url}
            </p>
            <button
              onClick={checkFlowiseConnection}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Retry Connection
            </button>
          </div>
        </div>
      )}

      <div className="mt-6">
        <h3 className="text-lg font-medium text-gray-900 mb-3">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50">
            <div className="text-lg mb-2">📝</div>
            <div className="font-medium">Create Agent</div>
            <div className="text-sm text-gray-500">Start with a template</div>
          </button>
          <button className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50">
            <div className="text-lg mb-2">🚀</div>
            <div className="font-medium">Deploy Agent</div>
            <div className="text-sm text-gray-500">Publish to production</div>
          </button>
          <button className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50">
            <div className="text-lg mb-2">📊</div>
            <div className="font-medium">View Analytics</div>
            <div className="text-sm text-gray-500">Monitor performance</div>
          </button>
        </div>
      </div>
    </div>
  )
}