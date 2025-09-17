import { useState, useEffect } from 'react'

interface SystemMetrics {
  agentStatus: { active: number; total: number }
  integrationHealth: { healthy: number; total: number }
  systemLoad: { cpu: number; memory: number }
  businessMetrics: { processedToday: number; automationRate: number }
}

export default function OperationsTab() {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchMetrics()
    const interval = setInterval(fetchMetrics, 30000) // Update every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const fetchMetrics = async () => {
    try {
      // Simulate API call with mock data
      await new Promise(resolve => setTimeout(resolve, 500))
      setMetrics({
        agentStatus: { active: 6, total: 8 },
        integrationHealth: { healthy: 3, total: 4 },
        systemLoad: { cpu: 34, memory: 67 },
        businessMetrics: { processedToday: 156, automationRate: 87 }
      })
    } catch (error) {
      console.error('Failed to fetch metrics:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Operations Center</h2>
        <p className="text-gray-600">System monitoring and health dashboard</p>
      </div>

      {/* System Health Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="text-2xl mr-3">🤖</div>
            <div>
              <div className="text-2xl font-bold text-gray-900">
                {metrics?.agentStatus.active || 0}/{metrics?.agentStatus.total || 0}
              </div>
              <div className="text-sm text-gray-500">Active Agents</div>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="text-2xl mr-3">🔗</div>
            <div>
              <div className="text-2xl font-bold text-gray-900">
                {metrics?.integrationHealth.healthy || 0}/{metrics?.integrationHealth.total || 0}
              </div>
              <div className="text-sm text-gray-500">Healthy Integrations</div>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="text-2xl mr-3">⚡</div>
            <div>
              <div className="text-2xl font-bold text-gray-900">
                {metrics?.systemLoad.cpu || 0}%
              </div>
              <div className="text-sm text-gray-500">CPU Usage</div>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="text-2xl mr-3">📊</div>
            <div>
              <div className="text-2xl font-bold text-gray-900">
                {metrics?.businessMetrics.automationRate || 0}%
              </div>
              <div className="text-sm text-gray-500">Automation Rate</div>
            </div>
          </div>
        </div>
      </div>

      {/* System Performance */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">System Performance</h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-gray-500">CPU Usage</span>
                <span className="text-sm font-medium text-gray-900">{metrics?.systemLoad.cpu}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full"
                  style={{ width: `${metrics?.systemLoad.cpu}%` }}
                ></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-gray-500">Memory Usage</span>
                <span className="text-sm font-medium text-gray-900">{metrics?.systemLoad.memory}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-green-600 h-2 rounded-full"
                  style={{ width: `${metrics?.systemLoad.memory}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Business Metrics</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-500">Tasks Processed Today</span>
              <span className="text-lg font-semibold text-gray-900">{metrics?.businessMetrics.processedToday}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-500">Automation Rate</span>
              <span className="text-lg font-semibold text-green-600">{metrics?.businessMetrics.automationRate}%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-500">System Uptime</span>
              <span className="text-lg font-semibold text-blue-600">99.7%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activities */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Recent Activities</h3>
        </div>
        <div className="p-6">
          <div className="space-y-3">
            <div className="flex items-center justify-between py-2">
              <div className="flex items-center">
                <span className="text-green-500 mr-2">✅</span>
                <span>Sales pipeline analysis completed</span>
              </div>
              <span className="text-sm text-gray-500">2 minutes ago</span>
            </div>
            <div className="flex items-center justify-between py-2">
              <div className="flex items-center">
                <span className="text-blue-500 mr-2">🔄</span>
                <span>Finance swarm processing invoices</span>
              </div>
              <span className="text-sm text-gray-500">5 minutes ago</span>
            </div>
            <div className="flex items-center justify-between py-2">
              <div className="flex items-center">
                <span className="text-yellow-500 mr-2">⚠️</span>
                <span>Gong integration sync delayed</span>
              </div>
              <span className="text-sm text-gray-500">10 minutes ago</span>
            </div>
            <div className="flex items-center justify-between py-2">
              <div className="flex items-center">
                <span className="text-purple-500 mr-2">🚀</span>
                <span>Customer success agent deployed</span>
              </div>
              <span className="text-sm text-gray-500">15 minutes ago</span>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <button className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 text-center">
            <div className="text-lg mb-2">🔄</div>
            <div className="font-medium">Sync All</div>
            <div className="text-sm text-gray-500">Force sync integrations</div>
          </button>
          <button className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 text-center">
            <div className="text-lg mb-2">📊</div>
            <div className="font-medium">Generate Report</div>
            <div className="text-sm text-gray-500">System health report</div>
          </button>
          <button className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 text-center">
            <div className="text-lg mb-2">🔧</div>
            <div className="font-medium">Settings</div>
            <div className="text-sm text-gray-500">System configuration</div>
          </button>
          <button className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 text-center">
            <div className="text-lg mb-2">📝</div>
            <div className="font-medium">View Logs</div>
            <div className="text-sm text-gray-500">System and error logs</div>
          </button>
        </div>
      </div>
    </div>
  )
}