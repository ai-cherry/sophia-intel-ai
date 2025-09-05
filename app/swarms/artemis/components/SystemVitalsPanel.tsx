"""
Military-themed System Vitals Panel for Artemis Command Center
Integrates Prometheus metrics with tactical display aesthetics
"""

import React, { useState, useEffect } from 'react';
import { Activity, AlertTriangle, Shield, Cpu, HardDrive, Zap } from 'lucide-react';

interface SystemMetrics {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  response_time_p95: number;
  error_rate: number;
  uptime_seconds: number;
  anomaly_score: number;
  timestamp: string;
}

interface SystemVitalsPanelProps {
  metricsEndpoint?: string;
  refreshInterval?: number;
}

export const SystemVitalsPanel: React.FC<SystemVitalsPanelProps> = ({
  metricsEndpoint = '/health/metrics',
  refreshInterval = 5000
}) => {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'error'>('disconnected');

  useEffect(() => {
    let interval: NodeJS.Timeout;

    const fetchMetrics = async () => {
      try {
        const response = await fetch(metricsEndpoint);
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();

        // Transform Prometheus metrics to our format
        const transformedMetrics: SystemMetrics = {
          cpu_usage: data.metrics?.cpu?.usage_percent || 0,
          memory_usage: data.metrics?.memory?.used_percent || 0,
          disk_usage: data.metrics?.disk?.used_percent || 0,
          response_time_p95: data.metrics?.response_time_p95_ms || 0,
          error_rate: data.metrics?.error_rate_percent || 0,
          uptime_seconds: data.metrics?.uptime_seconds || 0,
          anomaly_score: data.metrics?.anomaly_score || 0,
          timestamp: new Date().toISOString()
        };

        setMetrics(transformedMetrics);
        setLastUpdate(new Date());
        setConnectionStatus('connected');
      } catch (error) {
        console.error('Failed to fetch system metrics:', error);
        setConnectionStatus('error');
      }
    };

    // Initial fetch
    fetchMetrics();

    // Set up interval
    interval = setInterval(fetchMetrics, refreshInterval);

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [metricsEndpoint, refreshInterval]);

  const getStatusColor = (value: number, thresholds: [number, number]) => {
    const [warning, critical] = thresholds;
    if (value >= critical) return 'text-red-400 bg-red-900/30';
    if (value >= warning) return 'text-yellow-400 bg-yellow-900/30';
    return 'text-green-400 bg-green-900/30';
  };

  const getThreatLevel = (anomalyScore: number) => {
    if (anomalyScore >= 80) return { level: 'CRITICAL', color: 'text-red-400', bgColor: 'bg-red-900/30' };
    if (anomalyScore >= 50) return { level: 'ELEVATED', color: 'text-yellow-400', bgColor: 'bg-yellow-900/30' };
    if (anomalyScore >= 20) return { level: 'MODERATE', color: 'text-orange-400', bgColor: 'bg-orange-900/30' };
    return { level: 'LOW', color: 'text-green-400', bgColor: 'bg-green-900/30' };
  };

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (days > 0) return `${days}d ${hours}h ${minutes}m`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  if (!metrics) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-6">
        <div className="flex items-center space-x-3 mb-4">
          <Activity className="w-5 h-5 text-gray-500 animate-pulse" />
          <h3 className="text-sm font-bold text-gray-400 font-mono">SYSTEM VITALS</h3>
        </div>
        <div className="text-center text-gray-500 py-8">
          <div className="animate-pulse">Establishing connection to tactical sensors...</div>
        </div>
      </div>
    );
  }

  const threatLevel = getThreatLevel(metrics.anomaly_score);

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <Activity className="w-5 h-5 text-green-500" />
          <h3 className="text-sm font-bold text-green-400 font-mono">SYSTEM VITALS</h3>
        </div>
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${
            connectionStatus === 'connected' ? 'bg-green-500 animate-pulse' :
            connectionStatus === 'error' ? 'bg-red-500' : 'bg-gray-500'
          }`} />
          <span className="text-xs text-gray-400 font-mono">
            {connectionStatus === 'connected' ? 'LIVE' :
             connectionStatus === 'error' ? 'ERROR' : 'DISCONNECTED'}
          </span>
        </div>
      </div>

      {/* Critical Metrics Grid */}
      <div className="grid grid-cols-2 gap-4">
        {/* CPU Usage */}
        <div className={`p-3 rounded border ${getStatusColor(metrics.cpu_usage, [70, 90])}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Cpu className="w-4 h-4" />
              <span className="text-xs font-mono">CPU</span>
            </div>
            <span className="text-sm font-bold font-mono">{metrics.cpu_usage.toFixed(1)}%</span>
          </div>
          <div className="mt-2 bg-gray-800 rounded-full h-1.5">
            <div
              className="bg-current h-1.5 rounded-full transition-all duration-500"
              style={{ width: `${Math.min(metrics.cpu_usage, 100)}%` }}
            />
          </div>
        </div>

        {/* Memory Usage */}
        <div className={`p-3 rounded border ${getStatusColor(metrics.memory_usage, [80, 90])}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Zap className="w-4 h-4" />
              <span className="text-xs font-mono">MEM</span>
            </div>
            <span className="text-sm font-bold font-mono">{metrics.memory_usage.toFixed(1)}%</span>
          </div>
          <div className="mt-2 bg-gray-800 rounded-full h-1.5">
            <div
              className="bg-current h-1.5 rounded-full transition-all duration-500"
              style={{ width: `${Math.min(metrics.memory_usage, 100)}%` }}
            />
          </div>
        </div>

        {/* Disk Usage */}
        <div className={`p-3 rounded border ${getStatusColor(metrics.disk_usage, [80, 95])}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <HardDrive className="w-4 h-4" />
              <span className="text-xs font-mono">DISK</span>
            </div>
            <span className="text-sm font-bold font-mono">{metrics.disk_usage.toFixed(1)}%</span>
          </div>
          <div className="mt-2 bg-gray-800 rounded-full h-1.5">
            <div
              className="bg-current h-1.5 rounded-full transition-all duration-500"
              style={{ width: `${Math.min(metrics.disk_usage, 100)}%` }}
            />
          </div>
        </div>

        {/* Threat Level */}
        <div className={`p-3 rounded border ${threatLevel.bgColor} ${threatLevel.color}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Shield className="w-4 h-4" />
              <span className="text-xs font-mono">THREAT</span>
            </div>
            <span className="text-xs font-bold font-mono">{threatLevel.level}</span>
          </div>
          <div className="mt-2 bg-gray-800 rounded-full h-1.5">
            <div
              className="bg-current h-1.5 rounded-full transition-all duration-500"
              style={{ width: `${Math.min(metrics.anomaly_score, 100)}%` }}
            />
          </div>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="space-y-2 pt-2 border-t border-gray-700">
        <div className="flex justify-between text-xs text-gray-400">
          <span>RESPONSE TIME (P95)</span>
          <span className={`font-mono ${
            metrics.response_time_p95 > 1000 ? 'text-red-400' :
            metrics.response_time_p95 > 500 ? 'text-yellow-400' : 'text-green-400'
          }`}>{metrics.response_time_p95.toFixed(0)}ms</span>
        </div>

        <div className="flex justify-between text-xs text-gray-400">
          <span>ERROR RATE</span>
          <span className={`font-mono ${
            metrics.error_rate > 5 ? 'text-red-400' :
            metrics.error_rate > 1 ? 'text-yellow-400' : 'text-green-400'
          }`}>{metrics.error_rate.toFixed(2)}%</span>
        </div>

        <div className="flex justify-between text-xs text-gray-400">
          <span>UPTIME</span>
          <span className="font-mono text-blue-400">{formatUptime(metrics.uptime_seconds)}</span>
        </div>
      </div>

      {/* Last Update */}
      <div className="text-xs text-gray-500 text-center pt-2 border-t border-gray-700">
        LAST INTEL: {lastUpdate ? lastUpdate.toLocaleTimeString() : 'UNKNOWN'}
      </div>
    </div>
  );
};

export default SystemVitalsPanel;
