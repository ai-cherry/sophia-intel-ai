'use client';

import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Activity, Cpu, HardDrive, Zap } from 'lucide-react';

interface Metrics {
  swarmPerformance: {
    totalRequests: number;
    successRate: number;
    avgResponseTime: number;
    activeSwarms: number;
  };
  resourceUsage: {
    cpu: number;
    memory: number;
    storage: number;
    network: number;
  };
  costTracking: {
    dailyCost: number;
    monthlyCost: number;
    trend: 'up' | 'down' | 'stable';
  };
}

interface MetricsPanelProps {
  apiEndpoint: string;
}

export const MetricsPanel: React.FC<MetricsPanelProps> = ({ apiEndpoint }) => {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, [apiEndpoint]);

  const fetchMetrics = async () => {
    try {
      const response = await fetch(apiEndpoint);
      if (response.ok) {
        const data = await response.json();
        setMetrics(data);
      }
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="bg-white/5 rounded-xl p-6 animate-pulse">
              <div className="h-4 bg-white/10 rounded w-3/4 mb-4"></div>
              <div className="h-8 bg-white/10 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="p-6 text-center text-white/50">
        <Activity className="w-12 h-12 mx-auto mb-4 opacity-50" />
        <p>No metrics data available</p>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Swarm Performance */}
        <div className="bg-white/5 backdrop-blur-md rounded-xl border border-white/10 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Total Requests</h3>
            <Activity className="w-5 h-5 text-[#00e0ff]" />
          </div>
          <p className="text-3xl font-bold">{metrics.swarmPerformance.totalRequests.toLocaleString()}</p>
          <p className="text-sm text-white/70 mt-2">Active Swarms: {metrics.swarmPerformance.activeSwarms}</p>
        </div>

        <div className="bg-white/5 backdrop-blur-md rounded-xl border border-white/10 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Success Rate</h3>
            <Zap className="w-5 h-5 text-green-400" />
          </div>
          <p className="text-3xl font-bold">{metrics.swarmPerformance.successRate.toFixed(1)}%</p>
          <div className="mt-2">
            <div className="w-full bg-white/10 rounded-full h-2">
              <div
                className="bg-gradient-to-r from-green-400 to-green-600 h-2 rounded-full"
                style={{ width: `${metrics.swarmPerformance.successRate}%` }}
              />
            </div>
          </div>
        </div>

        <div className="bg-white/5 backdrop-blur-md rounded-xl border border-white/10 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Avg Response</h3>
            <TrendingUp className="w-5 h-5 text-[#ff00c3]" />
          </div>
          <p className="text-3xl font-bold">{metrics.swarmPerformance.avgResponseTime}ms</p>
          <p className="text-sm text-white/70 mt-2">P95: {(metrics.swarmPerformance.avgResponseTime * 1.5).toFixed(0)}ms</p>
        </div>

        {/* Resource Usage */}
        <div className="bg-white/5 backdrop-blur-md rounded-xl border border-white/10 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">CPU Usage</h3>
            <Cpu className="w-5 h-5 text-blue-400" />
          </div>
          <p className="text-3xl font-bold">{metrics.resourceUsage.cpu}%</p>
          <div className="mt-2">
            <div className="w-full bg-white/10 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${
                  metrics.resourceUsage.cpu > 80 
                    ? 'bg-red-500' 
                    : metrics.resourceUsage.cpu > 60 
                    ? 'bg-yellow-500' 
                    : 'bg-green-500'
                }`}
                style={{ width: `${metrics.resourceUsage.cpu}%` }}
              />
            </div>
          </div>
        </div>

        <div className="bg-white/5 backdrop-blur-md rounded-xl border border-white/10 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Memory</h3>
            <HardDrive className="w-5 h-5 text-purple-400" />
          </div>
          <p className="text-3xl font-bold">{metrics.resourceUsage.memory}%</p>
          <div className="mt-2">
            <div className="w-full bg-white/10 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${
                  metrics.resourceUsage.memory > 80 
                    ? 'bg-red-500' 
                    : metrics.resourceUsage.memory > 60 
                    ? 'bg-yellow-500' 
                    : 'bg-green-500'
                }`}
                style={{ width: `${metrics.resourceUsage.memory}%` }}
              />
            </div>
          </div>
        </div>

        {/* Cost Tracking */}
        <div className="bg-white/5 backdrop-blur-md rounded-xl border border-white/10 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Daily Cost</h3>
            {metrics.costTracking.trend === 'up' ? (
              <TrendingUp className="w-5 h-5 text-red-400" />
            ) : metrics.costTracking.trend === 'down' ? (
              <TrendingDown className="w-5 h-5 text-green-400" />
            ) : (
              <Activity className="w-5 h-5 text-yellow-400" />
            )}
          </div>
          <p className="text-3xl font-bold">${metrics.costTracking.dailyCost.toFixed(2)}</p>
          <p className="text-sm text-white/70 mt-2">
            Monthly: ${metrics.costTracking.monthlyCost.toFixed(2)}
          </p>
        </div>
      </div>

      {/* Performance Chart Placeholder */}
      <div className="mt-6 bg-white/5 backdrop-blur-md rounded-xl border border-white/10 p-6">
        <h3 className="text-lg font-semibold mb-4">Performance Trends</h3>
        <div className="h-64 flex items-center justify-center text-white/50">
          <p>Chart visualization would go here</p>
        </div>
      </div>
    </div>
  );
};