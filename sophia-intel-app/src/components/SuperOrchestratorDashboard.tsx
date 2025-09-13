'use client';

import React, { useState } from 'react';

interface OrchestratorState {
  id: string;
  name: string;
  status: 'active' | 'idle' | 'processing';
  currentTask: string;
  efficiency: number;
}

export default function SuperOrchestratorDashboard() {
  const [orchestrators] = useState<OrchestratorState[]>([
    {
      id: 'orch-1',
      name: 'Master Orchestrator',
      status: 'active',
      currentTask: 'Managing 5 active swarms',
      efficiency: 94
    },
    {
      id: 'orch-2', 
      name: 'Research Orchestrator',
      status: 'processing',
      currentTask: 'Analyzing market data',
      efficiency: 87
    },
    {
      id: 'orch-3',
      name: 'Development Orchestrator', 
      status: 'idle',
      currentTask: 'Waiting for tasks',
      efficiency: 72
    }
  ]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#050505] to-[#1b1f22] text-white p-6">
      <div className="max-w-7xl mx-auto">
        <header className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Super Orchestrator Dashboard</h1>
          <p className="text-white/70">Central command for multi-agent orchestration</p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {orchestrators.map((orch) => (
            <div key={orch.id} className="bg-white/5 rounded-lg border border-white/10 p-6">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-semibold">{orch.name}</h3>
                <span className={`px-3 py-1 rounded text-sm ${
                  orch.status === 'active' ? 'bg-green-500/20 text-green-400' :
                  orch.status === 'processing' ? 'bg-yellow-500/20 text-yellow-400' :
                  'bg-gray-500/20 text-gray-400'
                }`}>
                  {orch.status}
                </span>
              </div>
              
              <p className="text-white/70 mb-4">{orch.currentTask}</p>
              
              <div className="mb-2">
                <div className="flex justify-between text-sm mb-1">
                  <span>Efficiency</span>
                  <span>{orch.efficiency}%</span>
                </div>
                <div className="w-full bg-white/10 rounded-full h-2">
                  <div
                    className="h-2 rounded-full bg-gradient-to-r from-blue-500 to-purple-500"
                    style={{ width: `${orch.efficiency}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white/5 rounded-lg border border-white/10 p-6">
            <h3 className="text-lg font-semibold mb-4">System Overview</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-white/70">Total Orchestrators</span>
                <span className="font-mono">{orchestrators.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-white/70">Active Tasks</span>
                <span className="font-mono">12</span>
              </div>
              <div className="flex justify-between">
                <span className="text-white/70">Completed Today</span>
                <span className="font-mono">87</span>
              </div>
              <div className="flex justify-between">
                <span className="text-white/70">Average Efficiency</span>
                <span className="font-mono">
                  {Math.round(orchestrators.reduce((acc, o) => acc + o.efficiency, 0) / orchestrators.length)}%
                </span>
              </div>
            </div>
          </div>

          <div className="bg-white/5 rounded-lg border border-white/10 p-6">
            <h3 className="text-lg font-semibold mb-4">Recent Activities</h3>
            <div className="space-y-3">
              <div className="text-sm">
                <div className="text-white/90">Swarm deployment completed</div>
                <div className="text-white/60 text-xs">2 minutes ago</div>
              </div>
              <div className="text-sm">
                <div className="text-white/90">Agent configuration updated</div>
                <div className="text-white/60 text-xs">5 minutes ago</div>
              </div>
              <div className="text-sm">
                <div className="text-white/90">New orchestrator initialized</div>
                <div className="text-white/60 text-xs">12 minutes ago</div>
              </div>
              <div className="text-sm">
                <div className="text-white/90">Memory optimization completed</div>
                <div className="text-white/60 text-xs">18 minutes ago</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}