import { useState } from 'react'

export default function ProjectManagementTab() {
  const [selectedProject, setSelectedProject] = useState('all')

  const projects = [
    {
      id: 1,
      name: 'Sophia AI Integration',
      status: 'active',
      progress: 78,
      dueDate: '2025-10-15',
      team: ['Sarah', 'Mike', 'Alex'],
      priority: 'high',
      tasks: { total: 24, completed: 18, inProgress: 4, blocked: 2 }
    },
    {
      id: 2,
      name: 'Customer Portal Redesign',
      status: 'active',
      progress: 45,
      dueDate: '2025-11-30',
      team: ['Jessica', 'Tom', 'Linda'],
      priority: 'medium',
      tasks: { total: 32, completed: 14, inProgress: 12, blocked: 6 }
    },
    {
      id: 3,
      name: 'Business Intelligence Dashboard',
      status: 'completed',
      progress: 100,
      dueDate: '2025-09-01',
      team: ['David', 'Emma', 'Chris'],
      priority: 'high',
      tasks: { total: 28, completed: 28, inProgress: 0, blocked: 0 }
    },
    {
      id: 4,
      name: 'Mobile App Development',
      status: 'planning',
      progress: 12,
      dueDate: '2026-02-28',
      team: ['Rachel', 'Kevin', 'Maya'],
      priority: 'low',
      tasks: { total: 45, completed: 5, inProgress: 3, blocked: 1 }
    }
  ]

  const integrationData = [
    {
      source: 'Asana',
      type: 'Project Management',
      projects: 15,
      lastSync: '2 minutes ago',
      status: 'healthy'
    },
    {
      source: 'Linear',
      type: 'Issue Tracking',
      projects: 8,
      lastSync: '5 minutes ago',
      status: 'healthy'
    },
    {
      source: 'Airtable',
      type: 'Database',
      projects: 12,
      lastSync: '3 minutes ago',
      status: 'healthy'
    },
    {
      source: 'HubSpot',
      type: 'CRM Projects',
      projects: 6,
      lastSync: '1 minute ago',
      status: 'healthy'
    },
    {
      source: 'Slack',
      type: 'Communication',
      projects: 23,
      lastSync: '10 minutes ago',
      status: 'healthy'
    },
    {
      source: 'Gong',
      type: 'Sales Intelligence',
      projects: 9,
      lastSync: '15 minutes ago',
      status: 'syncing'
    }
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800 dark:bg-green-800/30 dark:text-green-100'
      case 'completed':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-800/30 dark:text-blue-100'
      case 'planning':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-800/30 dark:text-yellow-100'
      case 'on-hold':
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800/30 dark:text-gray-100'
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800/30 dark:text-gray-100'
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'bg-red-100 text-red-800 dark:bg-red-800/30 dark:text-red-100'
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-800/30 dark:text-yellow-100'
      case 'low':
        return 'bg-green-100 text-green-800 dark:bg-green-800/30 dark:text-green-100'
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800/30 dark:text-gray-100'
    }
  }

  const handleTaskClick = (taskType: string) => {
    alert(`Coming Soon: Detailed view for ${taskType}`)
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-primary mb-2">Project Management</h2>
        <p className="text-secondary">Unified project tracking across all tools</p>
      </div>

      {/* Task Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <button
          onClick={() => handleTaskClick('Active Tasks')}
          className="bg-card p-6 rounded-lg shadow hover:shadow-lg transition-all hover:scale-105 text-left border border-custom"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-3xl">✅</span>
            <span className="text-xs font-medium px-2 py-1 bg-green-100 text-green-800 dark:bg-green-800/30 dark:text-green-100 rounded-full">
              Active
            </span>
          </div>
          <div className="text-2xl font-bold text-primary">37</div>
          <div className="text-sm text-secondary">Active Tasks</div>
        </button>

        <button
          onClick={() => handleTaskClick('Completed Tasks')}
          className="bg-card p-6 rounded-lg shadow hover:shadow-lg transition-all hover:scale-105 text-left border border-custom"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-3xl">🎉</span>
            <span className="text-xs font-medium px-2 py-1 bg-blue-100 text-blue-800 dark:bg-blue-800/30 dark:text-blue-100 rounded-full">
              Done
            </span>
          </div>
          <div className="text-2xl font-bold text-primary">65</div>
          <div className="text-sm text-secondary">Completed Tasks</div>
        </button>

        <button
          onClick={() => handleTaskClick('In Progress Tasks')}
          className="bg-card p-6 rounded-lg shadow hover:shadow-lg transition-all hover:scale-105 text-left border border-custom"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-3xl">🔄</span>
            <span className="text-xs font-medium px-2 py-1 bg-yellow-100 text-yellow-800 dark:bg-yellow-800/30 dark:text-yellow-100 rounded-full">
              Progress
            </span>
          </div>
          <div className="text-2xl font-bold text-primary">19</div>
          <div className="text-sm text-secondary">In Progress</div>
        </button>

        <button
          onClick={() => handleTaskClick('Blocked Tasks')}
          className="bg-card p-6 rounded-lg shadow hover:shadow-lg transition-all hover:scale-105 text-left border border-custom"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-3xl">🚫</span>
            <span className="text-xs font-medium px-2 py-1 bg-red-100 text-red-800 dark:bg-red-800/30 dark:text-red-100 rounded-full">
              Blocked
            </span>
          </div>
          <div className="text-2xl font-bold text-primary">9</div>
          <div className="text-sm text-secondary">Blocked Tasks</div>
        </button>
      </div>

      {/* Project Sources */}
      <div className="bg-card rounded-lg shadow border border-custom">
        <div className="px-6 py-4 border-b border-custom">
          <h3 className="text-lg font-medium text-primary">Project Sources</h3>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {integrationData.map((integration) => (
              <button
                key={integration.source}
                onClick={() => alert(`Coming Soon: View ${integration.source} projects`)}
                className="flex flex-col items-center p-4 bg-card-hover rounded-lg hover:bg-tertiary transition-all hover:scale-105 border border-custom"
              >
                <div className="text-2xl mb-2">
                  {integration.source === 'Asana' && '📋'}
                  {integration.source === 'Linear' && '🔄'}
                  {integration.source === 'Airtable' && '📊'}
                  {integration.source === 'HubSpot' && '🎯'}
                  {integration.source === 'Slack' && '💬'}
                  {integration.source === 'Gong' && '📞'}
                </div>
                <div className="text-sm font-medium text-primary">{integration.source}</div>
                <div className="text-xs text-secondary mt-1">{integration.projects} projects</div>
                <div className={`mt-2 w-2 h-2 rounded-full ${
                  integration.status === 'healthy' ? 'bg-green-500' :
                  integration.status === 'syncing' ? 'bg-yellow-500 animate-pulse' :
                  'bg-gray-400'
                }`} />
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Projects Table */}
      <div className="bg-card rounded-lg shadow border border-custom">
        <div className="px-6 py-4 border-b border-custom">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-primary">Active Projects</h3>
            <select
              value={selectedProject}
              onChange={(e) => setSelectedProject(e.target.value)}
              className="rounded-md border-custom bg-card text-primary px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
            >
              <option value="all">All Sources</option>
              {integrationData.map((integration) => (
                <option key={integration.source} value={integration.source}>
                  {integration.source}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead className="border-b border-custom">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                  Project
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                  Priority
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                  Progress
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                  Team
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                  Due Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-secondary uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-custom">
              {projects.map((project) => (
                <tr key={project.id} className="hover:bg-card-hover transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div>
                        <div className="text-sm font-medium text-primary">{project.name}</div>
                        <div className="text-xs text-tertiary">
                          {project.tasks.total} tasks • {project.tasks.blocked} blocked
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(project.status)}`}>
                      {project.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getPriorityColor(project.priority)}`}>
                      {project.priority}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-1">
                        <div className="text-xs text-secondary mb-1">{project.progress}%</div>
                        <div className="w-24 bg-tertiary rounded-full h-2">
                          <div
                            className="bg-accent h-2 rounded-full"
                            style={{ width: `${project.progress}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex -space-x-2">
                      {project.team.slice(0, 3).map((member, index) => (
                        <div
                          key={index}
                          className="w-6 h-6 rounded-full bg-accent/20 border-2 border-card flex items-center justify-center text-xs font-medium text-accent"
                        >
                          {member[0]}
                        </div>
                      ))}
                      {project.team.length > 3 && (
                        <div className="w-6 h-6 rounded-full bg-tertiary border-2 border-card flex items-center justify-center text-xs font-medium text-secondary">
                          +{project.team.length - 3}
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary">
                    {project.dueDate}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button
                      onClick={() => alert('Coming Soon: View Details')}
                      className="text-accent hover:text-accent/80 mr-3 transition-colors"
                    >
                      View Details
                    </button>
                    <button
                      onClick={() => alert('Coming Soon: Edit Project')}
                      className="text-secondary hover:text-primary transition-colors"
                    >
                      Edit
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}