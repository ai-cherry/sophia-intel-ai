'use client';

import React from 'react';

interface SwarmListProps {
  onTeamSelect?: (teamId: string) => void;
  selectedTeamId?: string | null;
}

export function SwarmList({ onTeamSelect, selectedTeamId }: SwarmListProps) {
  const mockSwarms = [
    { id: 'swarm-1', name: 'Research Team', status: 'active', agents: 3 },
    { id: 'swarm-2', name: 'Development Team', status: 'idle', agents: 5 },
    { id: 'swarm-3', name: 'Analysis Team', status: 'active', agents: 2 },
  ];

  return (
    <div className="bg-white/5 rounded-lg border border-white/10 p-4">
      <h3 className="text-lg font-semibold mb-3">Active Swarms</h3>
      <div className="space-y-2">
        {mockSwarms.map((swarm) => (
          <div
            key={swarm.id}
            className={`p-3 rounded bg-white/5 border border-white/10 cursor-pointer transition-colors ${
              selectedTeamId === swarm.id ? 'bg-blue-500/20 border-blue-500/50' : 'hover:bg-white/10'
            }`}
            onClick={() => onTeamSelect?.(swarm.id)}
          >
            <div className="flex justify-between items-center">
              <span className="font-medium">{swarm.name}</span>
              <div className="flex items-center gap-2 text-sm">
                <span className={`px-2 py-1 rounded text-xs ${
                  swarm.status === 'active' ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'
                }`}>
                  {swarm.status}
                </span>
                <span className="text-white/60">{swarm.agents} agents</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}