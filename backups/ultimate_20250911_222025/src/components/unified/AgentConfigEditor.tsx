'use client';

import React from 'react';

interface AgentConfigEditorProps {
  teamId?: string | null;
}

export function AgentConfigEditor({ teamId }: AgentConfigEditorProps) {
  return (
    <div className="bg-white/5 rounded-lg border border-white/10 p-4">
      <h3 className="text-lg font-semibold mb-3">Agent Configuration</h3>
      <div className="text-sm text-white/70 mb-4">
        {teamId ? `Configuring agents for team: ${teamId}` : 'Select a team to configure agents'}
      </div>
      
      {teamId && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Agent Type</label>
              <select className="w-full bg-white/10 border border-white/20 rounded px-3 py-2 text-white">
                <option value="researcher">Researcher</option>
                <option value="developer">Developer</option>
                <option value="analyst">Analyst</option>
                <option value="manager">Manager</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Max Tokens</label>
              <input
                type="number"
                className="w-full bg-white/10 border border-white/20 rounded px-3 py-2 text-white"
                defaultValue={4000}
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">System Prompt</label>
            <textarea
              className="w-full bg-white/10 border border-white/20 rounded px-3 py-2 text-white h-24 resize-none"
              placeholder="Enter system prompt for agents..."
            />
          </div>
          
          <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded transition-colors">
            Update Configuration
          </button>
        </div>
      )}
    </div>
  );
}