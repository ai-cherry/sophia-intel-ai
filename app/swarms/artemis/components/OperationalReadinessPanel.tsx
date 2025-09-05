"""
Operational Readiness Panel for Artemis Command Center
Displays mission-critical performance and availability metrics
"""

import React, { useState, useEffect } from 'react';
import { Target, Gauge, TrendingUp, AlertCircle, CheckCircle, Clock } from 'lucide-react';

interface OperationalMetrics {
  availability_percent: number;
  throughput_rps: number;
  response_time_avg_ms: number;
  response_time_p95_ms: number;
  active_connections: number;
  max_connections: number;
  success_rate_percent: number;
  active_missions: number;
  completed_missions: number;
  timestamp: string;
}

interface OperationalReadinessPanelProps {
  metricsEndpoint?: string;
  refreshInterval?: number;
}

export const OperationalReadinessPanel: React.FC<OperationalReadinessPanelProps> = ({
  metricsEndpoint = '/health/detailed',
  refreshInterval = 5000
}) => {
  const [metrics, setMetrics] = useState<OperationalMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  useEffect(() => {
    let interval: NodeJS.Timeout;

    const fetchMetrics = async () => {
      try {
        const response = await fetch(metricsEndpoint);
        const data = await response.json();

        // Transform the health data to operational metrics
        const transformedMetrics: OperationalMetrics = {
          availability_percent: data.status === 'healthy' ? 100 : data.status === 'degraded' ? 75 : 0,
          throughput_rps: data.system_metrics?.requests_per_second || 0,
          response_time_avg_ms: data.system_metrics?.avg_response_time || 0,
          response_time_p95_ms: data.system_metrics?.p95_response_time || 0,
          active_connections: data.connection_metrics?.total_active || 0,
          max_connections: data.connection_metrics?.max_connections || 100,
          success_rate_percent: 100 - (data.system_metrics?.error_rate_percent || 0),
          active_missions: Object.keys(data.components || {}).filter(key =>
            data.components[key].status === 'active'
          ).length,
          completed_missions: Object.keys(data.components || {}).filter(key =>
            data.components[key].status === 'healthy'
          ).length,
          timestamp: new Date().toISOString()
        };

        setMetrics(transformedMetrics);
        setLastUpdate(new Date());
        setIsLoading(false);
      } catch (error) {
        console.error('Failed to fetch operational metrics:', error);
        setIsLoading(false);
      }
    };

    fetchMetrics();
    interval = setInterval(fetchMetrics, refreshInterval);

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [metricsEndpoint, refreshInterval]);

  const getReadinessLevel = (availability: number, throughput: number, responseTime: number) => {
    if (availability >= 99 && responseTime < 500 && throughput > 10) {
      return { level: 'COMBAT READY', color: 'text-green-400', bgColor: 'bg-green-900/30', icon: CheckCircle };
    }
    if (availability >= 95 && responseTime < 1000 && throughput > 5) {
      return { level: 'OPERATIONAL', color: 'text-blue-400', bgColor: 'bg-blue-900/30', icon: Target };
    }
    if (availability >= 90) {
      return { level: 'DEGRADED', color: 'text-yellow-400', bgColor: 'bg-yellow-900/30', icon: AlertCircle };
    }
    return { level: 'CRITICAL', color: 'text-red-400', bgColor: 'bg-red-900/30', icon: AlertCircle };
  };

  if (isLoading || !metrics) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-6">
        <div className="flex items-center space-x-3 mb-4">
          <Target className="w-5 h-5 text-gray-500 animate-pulse" />
          <h3 className="text-sm font-bold text-gray-400 font-mono">OPERATIONAL READINESS</h3>
        </div>
        <div className="text-center text-gray-500 py-8">
          <div className="animate-pulse">Analyzing mission readiness...</div>
        </div>
      </div>
    );
  }

  const readinessLevel = getReadinessLevel(
    metrics.availability_percent,
    metrics.throughput_rps,
    metrics.response_time_p95_ms
  );
  const ReadinessIcon = readinessLevel.icon;
  const connectionUtilization = (metrics.active_connections / metrics.max_connections) * 100;

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <Target className="w-5 h-5 text-green-500" />
          <h3 className="text-sm font-bold text-green-400 font-mono">OPERATIONAL READINESS</h3>
        </div>
        <div className={`flex items-center space-x-2 px-3 py-1 rounded ${readinessLevel.bgColor}`}>
          <ReadinessIcon className={`w-4 h-4 ${readinessLevel.color}`} />
          <span className={`text-xs font-bold font-mono ${readinessLevel.color}`}>
            {readinessLevel.level}
          </span>
        </div>
      </div>

      {/* Primary Metrics */}
      <div className="grid grid-cols-3 gap-4">
        {/* Availability */}
        <div className="text-center">
          <div className="text-2xl font-bold font-mono text-green-400">
            {metrics.availability_percent.toFixed(1)}%
          </div>
          <div className="text-xs text-gray-400 mt-1">AVAILABILITY</div>
          <div className="mt-2 bg-gray-800 rounded-full h-2">
            <div
              className="bg-green-500 h-2 rounded-full transition-all duration-500"
              style={{ width: `${metrics.availability_percent}%` }}
            />
          </div>
        </div>

        {/* Throughput */}
        <div className="text-center">
          <div className="text-2xl font-bold font-mono text-blue-400">
            {metrics.throughput_rps.toFixed(1)}
          </div>
          <div className="text-xs text-gray-400 mt-1">RPS</div>
          <div className="flex items-center justify-center mt-2">
            <TrendingUp className="w-4 h-4 text-blue-400" />
          </div>
        </div>

        {/* Response Time */}
        <div className="text-center">
          <div className={`text-2xl font-bold font-mono ${
            metrics.response_time_p95_ms > 1000 ? 'text-red-400' :
            metrics.response_time_p95_ms > 500 ? 'text-yellow-400' : 'text-green-400'
          }`}>
            {metrics.response_time_p95_ms.toFixed(0)}
          </div>
          <div className="text-xs text-gray-400 mt-1">MS P95</div>
          <div className="flex items-center justify-center mt-2">
            <Clock className="w-4 h-4" />
          </div>
        </div>
      </div>

      {/* Mission Status */}
      <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-700">
        <div className="bg-gray-800 rounded-lg p-3">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-400">ACTIVE MISSIONS</span>
            <span className="text-sm font-bold font-mono text-yellow-400">
              {metrics.active_missions}
            </span>
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-3">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-400">COMPLETED</span>
            <span className="text-sm font-bold font-mono text-green-400">
              {metrics.completed_missions}
            </span>
          </div>
        </div>
      </div>

      {/* Connection Status */}
      <div className="bg-gray-800 rounded-lg p-3">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-gray-400">CONNECTION UTILIZATION</span>
          <span className="text-sm font-bold font-mono text-blue-400">
            {metrics.active_connections}/{metrics.max_connections}
          </span>
        </div>
        <div className="bg-gray-700 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-500 ${
              connectionUtilization > 90 ? 'bg-red-500' :
              connectionUtilization > 70 ? 'bg-yellow-500' : 'bg-blue-500'
            }`}
            style={{ width: `${connectionUtilization}%` }}
          />
        </div>
        <div className="text-xs text-gray-500 mt-1 text-right">
          {connectionUtilization.toFixed(1)}% utilized
        </div>
      </div>

      {/* Success Rate Indicator */}
      <div className="flex items-center justify-between pt-2 border-t border-gray-700">
        <span className="text-xs text-gray-400">MISSION SUCCESS RATE</span>
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${
            metrics.success_rate_percent >= 99 ? 'bg-green-500' :
            metrics.success_rate_percent >= 95 ? 'bg-yellow-500' : 'bg-red-500'
          }`} />
          <span className="text-sm font-bold font-mono text-green-400">
            {metrics.success_rate_percent.toFixed(2)}%
          </span>
        </div>
      </div>

      {/* Last Update */}
      <div className="text-xs text-gray-500 text-center">
        LAST SITREP: {lastUpdate ? lastUpdate.toLocaleTimeString() : 'UNKNOWN'}
      </div>
    </div>
  );
};

export default OperationalReadinessPanel;
