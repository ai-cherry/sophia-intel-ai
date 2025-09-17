'use client'

import { useState, useEffect, useMemo } from 'react'

type Metric = {
  id: string
  label: string
  value: number
  unit?: string | null
  trend?: string | null
  target?: number | null
  change?: number | null
  tags?: Record<string, string>
}

const FALLBACK_LABELS: Record<string, string> = {
  revenue: 'Revenue',
  customers: 'Customers',
  conversion_rate: 'Conversion Rate',
  avg_deal_size: 'Average Deal Size'
}

export default function BusinessIntelligenceTab() {
  const [metrics, setMetrics] = useState<Metric[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchMetrics()
  }, [])

  const fetchMetrics = async () => {
    try {
      const response = await fetch('/api/bi/metrics')
      const payload = await response.json()
      setMetrics(normaliseMetrics(payload))
    } catch (error) {
      console.error('Failed to fetch BI metrics:', error)
      setMetrics([])
    } finally {
      setLoading(false)
    }
  }

  const normaliseMetrics = (payload: any): Metric[] => {
    const source = Array.isArray(payload)
      ? payload
      : Array.isArray(payload?.metrics)
        ? payload.metrics
        : payload?.metrics && typeof payload.metrics === 'object'
          ? Object.entries(payload.metrics).map(([id, value]: [string, any]) => ({
              id,
              label: FALLBACK_LABELS[id] || id.replace(/_/g, ' '),
              value: Number(value?.value ?? 0),
              unit: value?.unit ?? null,
              trend: value?.trend ?? null,
              target: value?.target ?? null,
              change: typeof value?.change === 'number' ? value.change : null
            }))
          : []

    return source
      .map((metric: any) => ({
        id: metric.id ?? 'metric',
        label: metric.label ?? FALLBACK_LABELS[metric.id] ?? metric.id ?? 'Metric',
        value: Number(metric.value ?? 0),
        unit: metric.unit ?? null,
        trend: metric.trend ?? null,
        target: metric.target ?? null,
        change: typeof metric.change === 'number' ? metric.change : null,
        tags: metric.tags ?? undefined
      }))
      .sort((a: any, b: any) => a.label.localeCompare(b.label))
  }

  const primaryMetrics = useMemo(() => metrics.slice(0, 4), [metrics])
  const secondaryMetrics = useMemo(() => metrics.slice(4), [metrics])

  const formatMetricValue = (metric: Metric) => {
    if (metric.unit) {
      const trimmed = metric.unit.trim()
      if (trimmed === '%' || trimmed.endsWith('%')) {
        return `${metric.value.toFixed(1)}%`
      }
      if (trimmed.toLowerCase().includes('day')) {
        return `${metric.value.toFixed(1)} ${trimmed}`
      }
      if (trimmed.toLowerCase().includes('mo') || trimmed.toLowerCase().includes('month')) {
        return `${metric.value.toFixed(1)} ${trimmed}`
      }
    }

    if (metric.value >= 1_000_000) {
      return `$${(metric.value / 1_000_000).toFixed(1)}M`
    }
    if (metric.value >= 1_000) {
      return `$${(metric.value / 1_000).toFixed(0)}K`
    }

    return metric.unit ? `${metric.value} ${metric.unit}`.trim() : metric.value.toString()
  }

  const getTrendIcon = (trend?: string | null) => {
    if (trend === 'up') return '↑'
    if (trend === 'down') return '↓'
    if (trend === 'flat') return '→'
    return null
  }

  const getTrendColor = (trend?: string | null) => {
    if (trend === 'up') return 'text-green-500'
    if (trend === 'down') return 'text-red-500'
    return 'text-tertiary'
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-primary mb-2">Business Intelligence</h2>
        <p className="text-secondary">Real-time analytics, reports, and business insights</p>
      </div>

      {/* Metric Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-card p-6 rounded-lg shadow border border-custom">
          <h3 className="text-lg font-medium text-primary mb-4">Core Metrics</h3>
          <div className="space-y-3">
            {loading ? (
              <MetricSkeleton rows={4} />
            ) : primaryMetrics.length ? (
              primaryMetrics.map(metric => (
                <MetricRow
                  key={metric.id}
                  metric={metric}
                  formatMetricValue={formatMetricValue}
                  getTrendIcon={getTrendIcon}
                  getTrendColor={getTrendColor}
                />
              ))
            ) : (
              <EmptyState onRetry={fetchMetrics} />
            )}
          </div>
        </div>

        <div className="bg-card p-6 rounded-lg shadow border border-custom">
          <h3 className="text-lg font-medium text-primary mb-4">Financial Signals</h3>
          <div className="space-y-3">
            {loading ? (
              <MetricSkeleton rows={4} />
            ) : secondaryMetrics.length ? (
              secondaryMetrics.map(metric => (
                <MetricRow
                  key={metric.id}
                  metric={metric}
                  formatMetricValue={formatMetricValue}
                  getTrendIcon={getTrendIcon}
                  getTrendColor={getTrendColor}
                />
              ))
            ) : primaryMetrics.length ? (
              primaryMetrics.slice(0, 2).map(metric => (
                <MetricRow
                  key={`secondary-${metric.id}`}
                  metric={metric}
                  formatMetricValue={formatMetricValue}
                  getTrendIcon={getTrendIcon}
                  getTrendColor={getTrendColor}
                />
              ))
            ) : (
              <EmptyState onRetry={fetchMetrics} />
            )}
          </div>
        </div>
      </div>

      {/* Knowledge Cards */}
      <div className="bg-card rounded-lg shadow border border-custom">
        <div className="px-6 py-4 border-b border-custom">
          <h3 className="text-lg font-medium text-primary">Insights & Reports</h3>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {['Process Automation', 'Response Time', 'System Uptime'].map(label => (
              <div key={label} className="text-center bg-card-hover rounded-lg py-6 border border-custom">
                <div className="text-3xl font-bold text-primary mb-2">Coming Soon</div>
                <div className="text-sm text-secondary">{label}</div>
                <div className="text-xs text-tertiary mt-1">Detailed trend view will appear here</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

type MetricRowProps = {
  metric: Metric
  formatMetricValue: (metric: Metric) => string
  getTrendIcon: (trend?: string | null) => string | null
  getTrendColor: (trend?: string | null) => string
}

function MetricRow({ metric, formatMetricValue, getTrendIcon, getTrendColor }: MetricRowProps) {
  const trendIcon = getTrendIcon(metric.trend)

  return (
    <div className="flex items-start justify-between">
      <div>
        <span className="text-sm text-secondary block">{metric.label}</span>
        {metric.target && (
          <span className="text-xs text-tertiary">Target: {metric.target}{metric.unit ?? ''}</span>
        )}
      </div>
      <div className="flex items-center space-x-2 text-right">
        <span className="text-lg font-semibold text-primary">
          {formatMetricValue(metric)}
        </span>
        {trendIcon && (
          <span className={`text-sm ${getTrendColor(metric.trend)}`}>
            {trendIcon}
            {metric.change != null ? ` ${metric.change}%` : ''}
          </span>
        )}
      </div>
    </div>
  )
}

type MetricSkeletonProps = {
  rows: number
}

function MetricSkeleton({ rows }: MetricSkeletonProps) {
  return (
    <div className="space-y-3 animate-pulse">
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="flex justify-between">
          <div className="h-4 bg-tertiary rounded w-24"></div>
          <div className="h-4 bg-tertiary rounded w-16"></div>
        </div>
      ))}
    </div>
  )
}

type EmptyStateProps = {
  onRetry: () => void
}

function EmptyState({ onRetry }: EmptyStateProps) {
  return (
    <div className="text-center py-4 text-secondary">
      <p>Unable to load metrics</p>
      <button
        onClick={onRetry}
        className="mt-2 text-sm text-accent hover:text-accent-hover"
      >
        Retry
      </button>
    </div>
  )
}
