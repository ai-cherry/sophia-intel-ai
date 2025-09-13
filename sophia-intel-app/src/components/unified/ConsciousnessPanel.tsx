'use client';

import React from 'react';

export function ConsciousnessPanel() {
  const consciousnessStates = [
    { agent: 'Agent-1', state: 'Active Thinking', depth: 85, context: 'Processing market analysis' },
    { agent: 'Agent-2', state: 'Deep Focus', depth: 92, context: 'Analyzing code patterns' },
    { agent: 'Agent-3', state: 'Idle', depth: 15, context: 'Waiting for new tasks' },
    { agent: 'Agent-4', state: 'Collaborative', depth: 78, context: 'Working with Agent-2' },
  ];

  return (
    <div className="bg-white/5 rounded-lg border border-white/10 p-4">
      <h3 className="text-lg font-semibold mb-3">Consciousness Monitor</h3>
      <div className="text-sm text-white/70 mb-4">
        Real-time cognitive state monitoring of active agents
      </div>
      
      <div className="space-y-3">
        {consciousnessStates.map((agent) => (
          <div key={agent.agent} className="bg-white/5 rounded p-3 border border-white/10">
            <div className="flex justify-between items-start mb-3">
              <div>
                <div className="font-medium">{agent.agent}</div>
                <div className="text-sm text-white/70">{agent.context}</div>
              </div>
              <span className={`px-2 py-1 rounded text-xs ${
                agent.state === 'Active Thinking' ? 'bg-blue-500/20 text-blue-400' :
                agent.state === 'Deep Focus' ? 'bg-purple-500/20 text-purple-400' :
                agent.state === 'Idle' ? 'bg-gray-500/20 text-gray-400' :
                'bg-green-500/20 text-green-400'
              }`}>
                {agent.state}
              </span>
            </div>
            
            <div className="mb-2">
              <div className="flex justify-between text-xs text-white/60 mb-1">
                <span>Consciousness Depth</span>
                <span>{agent.depth}%</span>
              </div>
              <div className="w-full bg-white/10 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all duration-300 ${
                    agent.depth > 80 ? 'bg-purple-500' :
                    agent.depth > 50 ? 'bg-blue-500' :
                    'bg-gray-500'
                  }`}
                  style={{ width: `${agent.depth}%` }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>
      
      <div className="mt-4 p-3 bg-white/5 rounded border border-white/10 text-xs text-white/60">
        💡 Consciousness depth indicates the complexity and focus level of agent cognitive processes
      </div>
    </div>
  );
}