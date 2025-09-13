'use client';

import React from 'react';

export function InfraQueue() {
  const mockTasks = [
    { id: '1', name: 'Deploy new model', status: 'running', progress: 75 },
    { id: '2', name: 'Update vector database', status: 'queued', progress: 0 },
    { id: '3', name: 'Scale cluster nodes', status: 'completed', progress: 100 },
    { id: '4', name: 'Backup memories', status: 'running', progress: 30 },
  ];

  return (
    <div className="bg-white/5 rounded-lg border border-white/10 p-4">
      <h3 className="text-lg font-semibold mb-3">Infrastructure Queue</h3>
      <div className="space-y-3">
        {mockTasks.map((task) => (
          <div key={task.id} className="bg-white/5 rounded p-3 border border-white/10">
            <div className="flex justify-between items-center mb-2">
              <span className="font-medium">{task.name}</span>
              <span className={`px-2 py-1 rounded text-xs ${
                task.status === 'running' ? 'bg-yellow-500/20 text-yellow-400' :
                task.status === 'queued' ? 'bg-gray-500/20 text-gray-400' :
                'bg-green-500/20 text-green-400'
              }`}>
                {task.status}
              </span>
            </div>
            <div className="w-full bg-white/10 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-300 ${
                  task.status === 'completed' ? 'bg-green-500' :
                  task.status === 'running' ? 'bg-yellow-500' :
                  'bg-gray-500'
                }`}
                style={{ width: `${task.progress}%` }}
              />
            </div>
            <div className="text-xs text-white/60 mt-1">{task.progress}% complete</div>
          </div>
        ))}
      </div>
    </div>
  );
}