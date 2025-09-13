'use client';

import React from 'react';

interface MemoryExplorerProps {
  teamId?: string | null;
}

export function MemoryExplorer({ teamId }: MemoryExplorerProps) {
  const mockMemories = [
    { id: '1', type: 'conversation', content: 'Discussed project requirements', timestamp: '2 hours ago' },
    { id: '2', type: 'document', content: 'API documentation review', timestamp: '4 hours ago' },
    { id: '3', type: 'decision', content: 'Architecture choice for vector storage', timestamp: '1 day ago' },
  ];

  return (
    <div className="bg-white/5 rounded-lg border border-white/10 p-4">
      <h3 className="text-lg font-semibold mb-3">Memory Explorer</h3>
      <div className="text-sm text-white/70 mb-4">
        {teamId ? `Exploring memories for team: ${teamId}` : 'Select a team to explore memories'}
      </div>
      
      {teamId && (
        <div className="space-y-3">
          {mockMemories.map((memory) => (
            <div key={memory.id} className="bg-white/5 rounded p-3 border border-white/10">
              <div className="flex justify-between items-start mb-2">
                <span className={`px-2 py-1 rounded text-xs ${
                  memory.type === 'conversation' ? 'bg-blue-500/20 text-blue-400' :
                  memory.type === 'document' ? 'bg-green-500/20 text-green-400' :
                  'bg-purple-500/20 text-purple-400'
                }`}>
                  {memory.type}
                </span>
                <span className="text-xs text-white/60">{memory.timestamp}</span>
              </div>
              <p className="text-sm text-white/90">{memory.content}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}