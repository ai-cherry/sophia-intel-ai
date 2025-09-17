export default function AgnoAgentsTab() {
  const agents = [
    {
      id: 1,
      name: 'Sales Pipeline Agent',
      type: 'Sales Automation',
      status: 'active',
      tasksCompleted: 45,
      lastActivity: '2 minutes ago'
    },
    {
      id: 2,
      name: 'Finance Analysis Agent',
      type: 'Financial Processing',
      status: 'active',
      tasksCompleted: 23,
      lastActivity: '5 minutes ago'
    },
    {
      id: 3,
      name: 'Customer Success Agent',
      type: 'Customer Management',
      status: 'idle',
      tasksCompleted: 12,
      lastActivity: '1 hour ago'
    }
  ]

  const handleAction = (action: string, agentName: string) => {
    alert(`Coming Soon: ${action} for ${agentName}`)
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-primary mb-2">Agno Business Agents</h2>
        <p className="text-secondary">AI agent swarms for business process automation</p>
      </div>

      {/* Agent Swarm Status */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-card p-6 rounded-lg shadow border border-custom">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-primary">Sales Swarm</h3>
            <span className="px-2 py-1 text-xs font-semibold text-green-800 bg-green-100 dark:text-green-100 dark:bg-green-800/30 rounded-full">
              Active
            </span>
          </div>
          <p className="text-sm text-secondary mb-2">Pipeline analysis, lead qualification</p>
          <div className="text-2xl font-bold text-primary">3/3</div>
          <div className="text-sm text-tertiary">Agents Running</div>
        </div>

        <div className="bg-card p-6 rounded-lg shadow border border-custom">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-primary">Finance Swarm</h3>
            <span className="px-2 py-1 text-xs font-semibold text-blue-800 bg-blue-100 dark:text-blue-100 dark:bg-blue-800/30 rounded-full">
              Processing
            </span>
          </div>
          <p className="text-sm text-secondary mb-2">Invoice processing, revenue analysis</p>
          <div className="text-2xl font-bold text-primary">2/3</div>
          <div className="text-sm text-tertiary">Agents Running</div>
        </div>

        <div className="bg-card p-6 rounded-lg shadow border border-custom">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-primary">Customer Swarm</h3>
            <span className="px-2 py-1 text-xs font-semibold text-yellow-800 bg-yellow-100 dark:text-yellow-100 dark:bg-yellow-800/30 rounded-full">
              Idle
            </span>
          </div>
          <p className="text-sm text-secondary mb-2">Health scoring, churn prediction</p>
          <div className="text-2xl font-bold text-primary">1/3</div>
          <div className="text-sm text-tertiary">Agents Running</div>
        </div>
      </div>

      {/* Individual Agents */}
      <div className="bg-card rounded-lg shadow border border-custom">
        <div className="px-6 py-4 border-b border-custom">
          <h3 className="text-lg font-medium text-primary">Active Agents</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead className="border-b border-custom">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                  Agent Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                  Tasks Completed
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                  Last Activity
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-custom">
              {agents.map((agent) => (
                <tr key={agent.id} className="hover:bg-card-hover transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-primary">{agent.name}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-secondary">{agent.type}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      agent.status === 'active'
                        ? 'bg-green-100 text-green-800 dark:bg-green-800/30 dark:text-green-100'
                        : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-800/30 dark:text-yellow-100'
                    }`}>
                      {agent.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary">
                    {agent.tasksCompleted}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-tertiary">
                    {agent.lastActivity}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button
                      onClick={() => handleAction('View Details', agent.name)}
                      className="text-accent hover:text-accent/80 mr-3 transition-colors"
                    >
                      View Details
                    </button>
                    <button
                      onClick={() => handleAction('Configure', agent.name)}
                      className="text-secondary hover:text-primary transition-colors"
                    >
                      Configure
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <button
          onClick={() => handleAction('Deploy', 'New Agent')}
          className="p-4 bg-accent/10 border border-accent/30 rounded-lg hover:bg-accent/20 transition-colors text-center"
        >
          <div className="text-lg mb-2">➕</div>
          <div className="font-medium text-primary">Deploy New Agent</div>
          <div className="text-sm text-secondary">Create custom business agent</div>
        </button>
        <button
          onClick={() => handleAction('View', 'Swarm Analytics')}
          className="p-4 bg-card border border-custom rounded-lg hover:bg-card-hover transition-colors text-center"
        >
          <div className="text-lg mb-2">📊</div>
          <div className="font-medium text-primary">Swarm Analytics</div>
          <div className="text-sm text-secondary">Performance metrics & insights</div>
        </button>
        <button
          onClick={() => handleAction('Access', 'Agent Marketplace')}
          className="p-4 bg-card border border-custom rounded-lg hover:bg-card-hover transition-colors text-center"
        >
          <div className="text-lg mb-2">🛍️</div>
          <div className="font-medium text-primary">Agent Marketplace</div>
          <div className="text-sm text-secondary">Pre-built agent templates</div>
        </button>
      </div>
    </div>
  )
}