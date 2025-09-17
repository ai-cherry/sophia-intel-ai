export default function IntegrationsTab() {
  const integrations = [
    // Production-Ready Integrations
    {
      name: 'Looker',
      type: 'Business Intelligence',
      status: 'healthy',
      lastSync: '1 minute ago',
      description: 'Data visualization and business analytics',
      category: 'production'
    },
    {
      name: 'Gong',
      type: 'Sales Intelligence',
      status: 'healthy',
      lastSync: '2 minutes ago',
      description: 'Sales call analysis and pipeline insights',
      category: 'production'
    },
    {
      name: 'Slack',
      type: 'Communication',
      status: 'healthy',
      lastSync: '30 seconds ago',
      description: 'Team communication and intelligence',
      category: 'production'
    },
    {
      name: 'HubSpot',
      type: 'CRM & Marketing',
      status: 'healthy',
      lastSync: '3 minutes ago',
      description: 'Customer relationship management and marketing automation',
      category: 'production'
    },
    {
      name: 'Asana',
      type: 'Project Management',
      status: 'healthy',
      lastSync: '2 minutes ago',
      description: 'Project tracking and stuck account detection',
      category: 'production'
    },
    {
      name: 'Linear',
      type: 'Development Tracking',
      status: 'healthy',
      lastSync: '5 minutes ago',
      description: 'Issue tracking and velocity analysis',
      category: 'production'
    },
    {
      name: 'Airtable',
      type: 'Database & Workflow',
      status: 'healthy',
      lastSync: '4 minutes ago',
      description: 'Flexible database and workflow management',
      category: 'production'
    },
    // Scaffolding - Not Ready
    {
      name: 'Microsoft 365',
      type: 'Office Suite',
      status: 'scaffolding',
      lastSync: 'Not configured',
      description: 'Office applications and collaboration tools',
      category: 'scaffolding'
    },
    {
      name: 'UserGems',
      type: 'Sales Intelligence',
      status: 'scaffolding',
      lastSync: 'Not configured',
      description: 'B2B contact tracking and job change alerts',
      category: 'scaffolding'
    },
    {
      name: 'Intercom',
      type: 'Customer Support',
      status: 'scaffolding',
      lastSync: 'Not configured',
      description: 'Customer messaging & support',
      category: 'scaffolding'
    },
    {
      name: 'NetSuite',
      type: 'ERP',
      status: 'scaffolding',
      lastSync: 'Not configured',
      description: 'Customer messaging and support automation',
      category: 'scaffolding'
    }
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-800'
      case 'warning':
        return 'bg-yellow-100 text-yellow-800'
      case 'error':
        return 'bg-red-100 text-red-800'
      case 'scaffolding':
        return 'bg-blue-100 text-blue-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const productionIntegrations = integrations.filter(i => i.category === 'production')
  const scaffoldingIntegrations = integrations.filter(i => i.category === 'scaffolding')

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Business Integrations</h2>
        <p className="text-gray-600">Connected business tools and their health status</p>
      </div>

      {/* Integration Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="text-2xl mr-3">🔗</div>
            <div>
              <div className="text-2xl font-bold text-gray-900">{integrations.length}</div>
              <div className="text-sm text-gray-500">Total Integrations</div>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="text-2xl mr-3">✅</div>
            <div>
              <div className="text-2xl font-bold text-green-600">{productionIntegrations.length}</div>
              <div className="text-sm text-gray-500">Production Ready</div>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="text-2xl mr-3">🚧</div>
            <div>
              <div className="text-2xl font-bold text-blue-600">{scaffoldingIntegrations.length}</div>
              <div className="text-sm text-gray-500">In Development</div>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="text-2xl mr-3">🔄</div>
            <div>
              <div className="text-2xl font-bold text-green-600">99.8%</div>
              <div className="text-sm text-gray-500">Uptime</div>
            </div>
          </div>
        </div>
      </div>

      {/* Integration Details */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Integration Details</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Integration
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Sync
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {integrations.map((integration) => (
                <tr key={integration.name}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{integration.name}</div>
                      <div className="text-sm text-gray-500">{integration.description}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-500">{integration.type}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(integration.status)}`}>
                      {integration.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {integration.lastSync}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button className="text-blue-600 hover:text-blue-900 mr-3">
                      Configure
                    </button>
                    <button className="text-gray-600 hover:text-gray-900 mr-3">
                      Test
                    </button>
                    <button className="text-green-600 hover:text-green-900">
                      Sync Now
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Integration Health Details */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Integration Health Details</h3>
        <div className="space-y-4">
          <div className="border-l-4 border-yellow-400 bg-yellow-50 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <span className="text-yellow-400">⚠️</span>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-yellow-800">
                  Gong Integration Delayed
                </h3>
                <div className="mt-2 text-sm text-yellow-700">
                  <p>
                    Last sync was 15 minutes ago. Expected sync interval is 5 minutes.
                    This may indicate API rate limiting or connectivity issues.
                  </p>
                </div>
                <div className="mt-4">
                  <button className="bg-yellow-100 hover:bg-yellow-200 text-yellow-800 px-3 py-1 rounded text-sm font-medium">
                    Retry Sync
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}