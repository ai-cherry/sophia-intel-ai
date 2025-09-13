'use client';

import React from 'react';

export function MetricsPanel() {
  const metrics = [
    { name: 'Active Agents', value: '12', change: '+2', trend: 'up' },
    { name: 'Tasks Completed', value: '847', change: '+15%', trend: 'up' },
    { name: 'Memory Usage', value: '2.3GB', change: '-0.2GB', trend: 'down' },
    { name: 'Response Time', value: '125ms', change: '-5ms', trend: 'down' },
  ];

  return (
    <div className="bg-white/5 rounded-lg border border-white/10 p-4">
      <h3 className="text-lg font-semibold mb-3">System Metrics</h3>
      <div className="grid grid-cols-2 gap-4">
        {metrics.map((metric) => (
          <div key={metric.name} className="bg-white/5 rounded p-3 border border-white/10">
            <div className="text-sm text-white/70 mb-1">{metric.name}</div>
            <div className="flex items-center justify-between">
              <span className="text-xl font-bold">{metric.value}</span>
              <span className={`text-sm flex items-center ${
                metric.trend === 'up' ? 'text-green-400' : 'text-blue-400'
              }`}>
                {metric.trend === 'up' ? '↗' : '↘'} {metric.change}
              </span>
            </div>
          </div>
        ))}
      </div>
      
      <div className="mt-4 p-3 bg-white/5 rounded border border-white/10">
        <div className="text-sm font-medium mb-2">System Health</div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-green-500 rounded-full"></div>
          <span className="text-sm text-white/90">All systems operational</span>
        </div>
      </div>
    </div>
  );
}