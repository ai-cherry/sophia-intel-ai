export type TabKey = 'business-intelligence' | 'agent-factory' | 'developer-studio'

export interface DashboardTabConfig {
  key: TabKey
  label: string
  component: React.ComponentType
  description?: string
}

export interface AgentDefinition {
  id: string
  name: string
  type: string
  description?: string
  capabilities?: string[]
  status?: 'active' | 'inactive' | 'pending'
  version?: string
  tags?: string[]
}

export interface AgnoWorkspaceSummary {
  id: string
  name: string
  agents: AgentDefinition[]
  createdAt: Date
  updatedAt: Date
  health?: 'healthy' | 'warning' | 'error'
  purpose?: string
  maintainer?: string
  pipelines?: number
  version?: string
}

export interface FlowwiseFactorySummary {
  id: string
  name: string
  flows: AgentDefinition[]
  createdAt: Date
  updatedAt: Date
}

export interface BusinessMetric {
  id: string
  name: string
  label?: string
  value: number
  unit?: string
  trend?: 'up' | 'down' | 'stable'
  change?: number
  lastUpdated?: Date
  target?: number
  tags?: Record<string, any>
}
