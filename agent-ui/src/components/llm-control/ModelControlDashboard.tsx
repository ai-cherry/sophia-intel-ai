'use client'

import React, { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Icon } from '@/components/ui/icon/Icon'
import { Heading } from '@/components/ui/typography/Heading/Heading'
import { Paragraph } from '@/components/ui/typography/Paragraph/Paragraph'
import { toast } from 'sonner'

interface ModelInfo {
  purpose: string
  description: string
  priority: number
  cost_tier: 'premium' | 'standard' | 'economy' | 'free'
}

interface ApprovedModels {
  [key: string]: ModelInfo
}

interface ModelHealth {
  [key: string]: 'healthy' | 'degraded' | 'failing'
}

interface UsageStats {
  [key: string]: number
}

interface TaskRouting {
  [key: string]: string[]
}

interface DashboardData {
  approved_models: string[]
  active_model: string
  model_health: ModelHealth
  usage_stats: UsageStats
  task_routing: TaskRouting
  primary_models: {
    critical: string
    counter_reasoning: string
  }
}

const ModelControlDashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null)
  const [selectedTask, setSelectedTask] = useState<string>('critical_decision')
  const [loading, setLoading] = useState(true)
  const [autoRefresh, setAutoRefresh] = useState(true)

  // Approved models with detailed info (matching centralized_model_control.py)
  const APPROVED_MODELS: ApprovedModels = {
    'openai/gpt-5': {
      purpose: 'CRITICAL',
      description: 'Most important tasks - PRIMARY MODEL',
      priority: 1,
      cost_tier: 'premium'
    },
    'x-ai/grok-4': {
      purpose: 'COUNTER_REASONING',
      description: 'Counter-reasoning and critical review',
      priority: 2,
      cost_tier: 'premium'
    },
    'x-ai/grok-code-fast-1': {
      purpose: 'FAST_CODING',
      description: 'Fast code generation',
      priority: 3,
      cost_tier: 'standard'
    },
    'qwen/qwen3-30b-a3b-thinking-2507': {
      purpose: 'DEEP_THINKING',
      description: 'Deep thinking and complex reasoning',
      priority: 3,
      cost_tier: 'standard'
    },
    'nousresearch/hermes-4-405b': {
      purpose: 'RESEARCH',
      description: 'Research and information gathering',
      priority: 4,
      cost_tier: 'standard'
    },
    'google/gemini-2.5-flash-image-preview:free': {
      purpose: 'VISION',
      description: 'Vision and image tasks (FREE)',
      priority: 5,
      cost_tier: 'free'
    },
    'openai/gpt-5-mini': {
      purpose: 'QUICK',
      description: 'Quick simple tasks',
      priority: 5,
      cost_tier: 'economy'
    },
    'anthropic/claude-sonnet-4': {
      purpose: 'CREATIVE',
      description: 'Creative and balanced tasks',
      priority: 4,
      cost_tier: 'standard'
    },
    'deepseek/deepseek-chat-v3-0324': {
      purpose: 'CREATIVE',
      description: 'Creative exploration',
      priority: 4,
      cost_tier: 'economy'
    },
    'z-ai/glm-4.5v': {
      purpose: 'VISION',
      description: 'Advanced vision tasks',
      priority: 4,
      cost_tier: 'standard'
    }
  }

  const fetchDashboardData = async () => {
    try {
      const response = await fetch('http://localhost:8005/api/model-control/dashboard')
      if (response.ok) {
        const data = await response.json()
        setDashboardData(data)
      } else {
        // Use mock data if endpoint not ready
        setDashboardData({
          approved_models: Object.keys(APPROVED_MODELS),
          active_model: 'openai/gpt-5',
          model_health: Object.fromEntries(
            Object.keys(APPROVED_MODELS).map(model => [model, 'healthy'])
          ),
          usage_stats: Object.fromEntries(
            Object.keys(APPROVED_MODELS).map(model => [model, 0])
          ),
          task_routing: {
            critical_decision: ['openai/gpt-5', 'x-ai/grok-4'],
            code_generation: ['x-ai/grok-code-fast-1', 'qwen/qwen3-30b-a3b-thinking-2507'],
            research_analysis: ['openai/gpt-5', 'nousresearch/hermes-4-405b'],
            creative_tasks: ['anthropic/claude-sonnet-4', 'deepseek/deepseek-chat-v3-0324'],
            vision_tasks: ['google/gemini-2.5-flash-image-preview:free', 'z-ai/glm-4.5v'],
            quick_tasks: ['openai/gpt-5-mini', 'x-ai/grok-code-fast-1'],
            deep_reasoning: ['qwen/qwen3-30b-a3b-thinking-2507', 'openai/gpt-5']
          },
          primary_models: {
            critical: 'openai/gpt-5',
            counter_reasoning: 'x-ai/grok-4'
          }
        })
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDashboardData()

    if (autoRefresh) {
      const interval = setInterval(fetchDashboardData, 5000)
      return () => clearInterval(interval)
    }
  }, [autoRefresh])

  const getHealthColor = (health: string) => {
    switch (health) {
      case 'healthy': return 'text-green-500'
      case 'degraded': return 'text-yellow-500'
      case 'failing': return 'text-red-500'
      default: return 'text-gray-500'
    }
  }

  const getCostTierBadge = (tier: string) => {
    switch (tier) {
      case 'premium': return 'bg-purple-100 text-purple-800'
      case 'standard': return 'bg-blue-100 text-blue-800'
      case 'economy': return 'bg-green-100 text-green-800'
      case 'free': return 'bg-gray-100 text-gray-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const handleModelSwitch = async (model: string, taskType: string) => {
    try {
      const response = await fetch('http://localhost:8005/api/model-control/assign', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model, task_type: taskType })
      })

      if (response.ok) {
        toast.success(`Assigned ${model} to ${taskType}`)
        fetchDashboardData()
      } else {
        toast.error('Failed to update model assignment')
      }
    } catch (error) {
      toast.error('Failed to update model assignment')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <Heading level={1} className="text-3xl font-bold">
          LLM Control Center
        </Heading>
        <div className="flex gap-4">
          <Button
            variant={autoRefresh ? 'default' : 'outline'}
            onClick={() => setAutoRefresh(!autoRefresh)}
            className="flex items-center gap-2"
          >
            <Icon name={autoRefresh ? 'pause' : 'play'} className="w-4 h-4" />
            {autoRefresh ? 'Pause Refresh' : 'Auto Refresh'}
          </Button>
          <Button
            variant="outline"
            onClick={fetchDashboardData}
            className="flex items-center gap-2"
          >
            <Icon name="refresh" className="w-4 h-4" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Primary Models Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="p-6 border-2 border-purple-200 bg-purple-50">
          <div className="flex items-center justify-between mb-4">
            <Heading level={3} className="text-lg font-semibold">
              Critical Tasks Model
            </Heading>
            <Icon name="star" className="w-5 h-5 text-purple-600" />
          </div>
          <div className="space-y-2">
            <Paragraph className="text-2xl font-bold text-purple-700">
              {dashboardData?.primary_models.critical || 'openai/gpt-5'}
            </Paragraph>
            <Paragraph className="text-sm text-gray-600">
              Primary model for most important decisions
            </Paragraph>
          </div>
        </Card>

        <Card className="p-6 border-2 border-blue-200 bg-blue-50">
          <div className="flex items-center justify-between mb-4">
            <Heading level={3} className="text-lg font-semibold">
              Counter-Reasoning Model
            </Heading>
            <Icon name="shield" className="w-5 h-5 text-blue-600" />
          </div>
          <div className="space-y-2">
            <Paragraph className="text-2xl font-bold text-blue-700">
              {dashboardData?.primary_models.counter_reasoning || 'x-ai/grok-4'}
            </Paragraph>
            <Paragraph className="text-sm text-gray-600">
              Reviews and validates critical decisions
            </Paragraph>
          </div>
        </Card>
      </div>

      {/* Task Routing Configuration */}
      <Card className="p-6">
        <Heading level={2} className="text-xl font-semibold mb-4">
          Task Routing Configuration
        </Heading>
        <div className="space-y-4">
          <div className="flex items-center gap-4">
            <Select value={selectedTask} onValueChange={setSelectedTask}>
              <SelectTrigger className="w-64">
                <SelectValue placeholder="Select task type" />
              </SelectTrigger>
              <SelectContent>
                {Object.keys(dashboardData?.task_routing || {}).map(task => (
                  <SelectItem key={task} value={task}>
                    {task.replace('_', ' ').toUpperCase()}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {selectedTask && dashboardData?.task_routing[selectedTask] && (
            <div className="bg-gray-50 rounded-lg p-4">
              <Paragraph className="font-semibold mb-2">Assigned Models:</Paragraph>
              <div className="space-y-2">
                {dashboardData.task_routing[selectedTask].map((model, index) => (
                  <div key={model} className="flex items-center justify-between p-2 bg-white rounded">
                    <span className="flex items-center gap-2">
                      <span className="text-gray-500">#{index + 1}</span>
                      <span className="font-medium">{model}</span>
                    </span>
                    <span className={`text-xs px-2 py-1 rounded ${getCostTierBadge(APPROVED_MODELS[model]?.cost_tier || 'standard')}`}>
                      {APPROVED_MODELS[model]?.cost_tier || 'standard'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </Card>

      {/* Approved Models Grid */}
      <Card className="p-6">
        <Heading level={2} className="text-xl font-semibold mb-4">
          Approved Models Status
        </Heading>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(APPROVED_MODELS).map(([model, info]) => (
            <div key={model} className="border rounded-lg p-4 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <Paragraph className="font-semibold text-sm">{model}</Paragraph>
                  <Paragraph className="text-xs text-gray-600 mt-1">{info.description}</Paragraph>
                </div>
                <div className={`w-2 h-2 rounded-full ${
                  dashboardData?.model_health[model] === 'healthy' ? 'bg-green-500' :
                  dashboardData?.model_health[model] === 'degraded' ? 'bg-yellow-500' :
                  'bg-red-500'
                }`} />
              </div>

              <div className="space-y-2 mt-3">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-500">Purpose:</span>
                  <span className="text-xs font-medium">{info.purpose}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-500">Priority:</span>
                  <span className="text-xs font-medium">{info.priority}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-500">Usage:</span>
                  <span className="text-xs font-medium">{dashboardData?.usage_stats[model] || 0} calls</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-500">Cost Tier:</span>
                  <span className={`text-xs px-2 py-0.5 rounded ${getCostTierBadge(info.cost_tier)}`}>
                    {info.cost_tier}
                  </span>
                </div>
              </div>

              {model === dashboardData?.active_model && (
                <div className="mt-3 pt-3 border-t">
                  <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                    ACTIVE
                  </span>
                </div>
              )}
            </div>
          ))}
        </div>
      </Card>

      {/* Usage Statistics */}
      <Card className="p-6">
        <Heading level={2} className="text-xl font-semibold mb-4">
          Usage Statistics
        </Heading>
        <div className="space-y-2">
          {dashboardData && Object.entries(dashboardData.usage_stats)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5)
            .map(([model, count]) => (
              <div key={model} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <span className="font-medium">{model}</span>
                <span className="text-sm text-gray-600">{count} calls</span>
              </div>
            ))}
        </div>
      </Card>
    </div>
  )
}

export default ModelControlDashboard