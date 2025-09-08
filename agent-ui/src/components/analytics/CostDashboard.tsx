'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import Icon from '@/components/ui/icon'
import { usePlaygroundStore } from '@/store'
import { APIRoutes } from '@/api/routes'
import { useDashboardData } from '@/hooks/useDashboardData'
// import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts'

interface CostSummary {
  period_start: string
  period_end: string
  total_cost_usd: number
  total_tokens: number
  total_requests: number
  llm_completion_cost: number
  embedding_cost: number
  swarm_execution_cost: number
  api_call_cost: number
  model_costs: Record<string, number>
  model_tokens: Record<string, number>
  provider_costs: Record<string, number>
}

interface DailyCost {
  date: string
  total_cost: number
  total_tokens: number
  requests: number
  llm_cost: number
  embedding_cost: number
}

interface TopModel {
  model: string
  provider: string
  total_cost: number
  total_tokens: number
  requests: number
}

const CostDashboard: React.FC = () => {
  const selectedEndpoint = usePlaygroundStore((state) => state.selectedEndpoint)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [timeRange, setTimeRange] = useState('7')

  // Data state
  const [summary, setSummary] = useState<CostSummary | null>(null)
  const [dailyCosts, setDailyCosts] = useState<DailyCost[]>([])
  const [topModels, setTopModels] = useState<TopModel[]>([])

  // Shared dashboard hooks per endpoint
  const summaryUrl = `${APIRoutes.GetCostSummary(selectedEndpoint)}?days=${timeRange}`
  const dailyUrl = `${APIRoutes.GetDailyCosts(selectedEndpoint)}?days=${timeRange}`
  const modelsUrl = `${APIRoutes.GetTopModels(selectedEndpoint)}?limit=10`

  const { data: summaryResp, loading: loadingSummary, error: errSummary, refetch: refetchSummary } =
    useDashboardData<{ summary: CostSummary }>(summaryUrl, [selectedEndpoint, timeRange], { category: 'api.costs.summary' })
  const { data: dailyResp, loading: loadingDaily, error: errDaily, refetch: refetchDaily } =
    useDashboardData<{ daily_costs: DailyCost[] }>(dailyUrl, [selectedEndpoint, timeRange], { category: 'api.costs.daily' })
  const { data: modelsResp, loading: loadingModels, error: errModels, refetch: refetchModels } =
    useDashboardData<{ top_models: TopModel[] }>(modelsUrl, [selectedEndpoint, timeRange], { category: 'api.costs.topModels' })

  React.useEffect(() => {
    setLoading(loadingSummary || loadingDaily || loadingModels)
    setError(errSummary || errDaily || errModels || null)
    if (summaryResp?.summary) setSummary(summaryResp.summary)
    if (dailyResp?.daily_costs) setDailyCosts(dailyResp.daily_costs)
    if (modelsResp?.top_models) setTopModels(modelsResp.top_models)
  }, [loadingSummary, loadingDaily, loadingModels, errSummary, errDaily, errModels, summaryResp, dailyResp, modelsResp])

  const formatCurrency = (amount: number) => {
    if (amount === 0) return '$0.00'
    if (amount < 0.01) return `$${amount.toFixed(6)}`
    return `$${amount.toFixed(2)}`
  }

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
    return num.toString()
  }

  // Chart colors
  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4']

  // Prepare chart data
  const pieData = summary ? [
    { name: 'LLM Completions', value: summary.llm_completion_cost, color: COLORS[0] },
    { name: 'Embeddings', value: summary.embedding_cost, color: COLORS[1] },
    { name: 'Swarm Execution', value: summary.swarm_execution_cost, color: COLORS[2] },
    { name: 'API Calls', value: summary.api_call_cost, color: COLORS[3] }
  ].filter(item => item.value > 0) : []

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-white">Cost Analytics</h2>
          <Skeleton className="h-10 w-32" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Skeleton className="h-80" />
          <Skeleton className="h-80" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] space-y-4">
        <Icon type="alert-triangle" className="text-red-500" size="lg" />
        <div className="text-center">
          <h3 className="text-lg font-medium text-white mb-2">Failed to Load Cost Data</h3>
          <p className="text-muted-foreground mb-4">{error}</p>
          <Button onClick={() => { refetchSummary(); refetchDaily(); refetchModels(); }} variant="outline" size="sm">
            <Icon type="refresh-ccw" size="xs" className="mr-2" />
            Retry
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Cost Analytics</h2>
          <p className="text-sm text-muted-foreground">
            Track LLM costs and token usage across your AI operations
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1">1 Day</SelectItem>
              <SelectItem value="7">7 Days</SelectItem>
              <SelectItem value="30">30 Days</SelectItem>
              <SelectItem value="90">90 Days</SelectItem>
            </SelectContent>
          </Select>
          <Button
            onClick={fetchCostData}
            variant="outline"
            size="sm"
            className="shrink-0"
          >
            <Icon type="refresh-ccw" size="xs" className="mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Cost
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {formatCurrency(summary?.total_cost_usd || 0)}
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              Last {timeRange} days
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Tokens
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {formatNumber(summary?.total_tokens || 0)}
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              Across all models
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Requests
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {formatNumber(summary?.total_requests || 0)}
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              API calls made
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Avg Cost/Request
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {summary && summary.total_requests > 0
                ? formatCurrency(summary.total_cost_usd / summary.total_requests)
                : '$0.00'
              }
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              Per API call
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily Cost List */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg font-semibold text-white">
              Daily Cost Breakdown
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 max-h-80 overflow-y-auto">
              {dailyCosts.slice().reverse().map((day) => (
                <div key={day.date} className="flex items-center justify-between p-3 rounded-lg bg-accent/30 border border-primary/10">
                  <div>
                    <div className="text-sm font-medium text-white">
                      {new Date(day.date).toLocaleDateString()}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {day.requests} requests • {formatNumber(day.total_tokens)} tokens
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-bold text-white">
                      {formatCurrency(day.total_cost)}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      LLM: {formatCurrency(day.llm_cost)} • EMB: {formatCurrency(day.embedding_cost)}
                    </div>
                  </div>
                </div>
              ))}
              {dailyCosts.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  No daily cost data available
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Cost Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg font-semibold text-white">
              Cost Breakdown
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {pieData.map((item) => (
                <div key={item.name} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div
                      className="w-4 h-4 rounded-full"
                      style={{ backgroundColor: item.color }}
                    />
                    <span className="text-sm text-white">{item.name}</span>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-bold text-white">
                      {formatCurrency(item.value)}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {summary ? ((item.value / summary.total_cost_usd) * 100).toFixed(1) : 0}%
                    </div>
                  </div>
                </div>
              ))}
              {pieData.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  No cost breakdown available
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Top Models Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg font-semibold text-white">
            Top Models by Cost
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Model</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Provider</th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Cost</th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Tokens</th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Requests</th>
                </tr>
              </thead>
              <tbody>
                {topModels.slice(0, 10).map((model) => (
                  <tr key={model.model} className="border-b border-gray-800">
                    <td className="py-3 px-4">
                      <div className="text-sm font-medium text-white truncate max-w-48">
                        {model.model}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="text-sm text-muted-foreground">
                        {model.provider}
                      </div>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="text-sm font-medium text-white">
                        {formatCurrency(model.total_cost)}
                      </div>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="text-sm text-muted-foreground">
                        {formatNumber(model.total_tokens)}
                      </div>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="text-sm text-muted-foreground">
                        {formatNumber(model.requests)}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {topModels.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                No model usage data available
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default CostDashboard
