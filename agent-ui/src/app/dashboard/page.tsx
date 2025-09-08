'use client';

import React, { useState } from 'react';
import { ManagerChat } from '@/components/unified/ManagerChat';
import { SwarmList } from '@/components/unified/SwarmList';
import { AgentConfigEditor } from '@/components/unified/AgentConfigEditor';
import { MemoryExplorer } from '@/components/unified/MemoryExplorer';
import { InfraQueue } from '@/components/unified/InfraQueue';
import { MetricsPanel } from '@/components/unified/MetricsPanel';
import { ConsciousnessPanel } from '@/components/unified/ConsciousnessPanel';

export default function DashboardPage() {
  const [selectedTeamId, setSelectedTeamId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'chat' | 'metrics' | 'consciousness'>('chat');

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#050505] to-[#1b1f22] text-white">
      {/* Header */}
      <header className="border-b border-white/10 backdrop-blur-md bg-white/5">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🌀</span>
            <h1 className="text-xl font-bold bg-gradient-to-r from-[#00e0ff] to-[#ff00c3] bg-clip-text text-transparent">
              AI Orchestra
            </h1>
          </div>
          <nav className="flex gap-6">
            <a href="/dashboard" className="text-[#00e0ff] hover:text-white transition-colors">Dashboard</a>
            <a href="/memory" className="hover:text-[#00e0ff] transition-colors">Memory Explorer</a>
            <a href="/infra" className="hover:text-[#00e0ff] transition-colors">InfraOps</a>
          </nav>
          <div className="w-10 h-10 rounded-full bg-gradient-to-r from-[#00e0ff] to-[#ff00c3] flex items-center justify-center font-bold">
            OP
          </div>
        </div>
      </header>

      {/* Main Layout */}
      <div className="flex h-[calc(100vh-73px)]">
        {/* Left Sidebar */}
        <aside className="w-80 border-r border-white/10 bg-white/5 backdrop-blur-md overflow-y-auto">
          <div className="p-4">
            <h2 className="text-lg font-semibold mb-4 text-[#00e0ff]">Swarms</h2>
            <SwarmList
              apiEndpoint="/teams"
              onSelect={(teamId) => setSelectedTeamId(teamId)}
              selectedTeamId={selectedTeamId}
            />
          </div>
          <div className="p-4 border-t border-white/10">
            <h2 className="text-lg font-semibold mb-4 text-[#00e0ff]">InfraOps</h2>
            <InfraQueue apiEndpoint="/infra/tasks" />
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 flex flex-col">
          {/* Tabs */}
          <div className="border-b border-white/10 bg-white/5 backdrop-blur-md">
            <div className="flex gap-4 px-6 py-3">
              <button
                onClick={() => setActiveTab('chat')}
                className={`px-4 py-2 rounded-lg transition-all ${
                  activeTab === 'chat'
                    ? 'bg-gradient-to-r from-[#00e0ff] to-[#ff00c3] text-white'
                    : 'bg-white/10 hover:bg-white/20'
                }`}
              >
                Manager Chat
              </button>
              <button
                onClick={() => setActiveTab('metrics')}
                className={`px-4 py-2 rounded-lg transition-all ${
                  activeTab === 'metrics'
                    ? 'bg-gradient-to-r from-[#00e0ff] to-[#ff00c3] text-white'
                    : 'bg-white/10 hover:bg-white/20'
                }`}
              >
                Metrics
              </button>
              <button
                onClick={() => setActiveTab('consciousness')}
                className={`px-4 py-2 rounded-lg transition-all ${
                  activeTab === 'consciousness'
                    ? 'bg-gradient-to-r from-[#00e0ff] to-[#ff00c3] text-white'
                    : 'bg-white/10 hover:bg-white/20'
                }`}
              >
                Consciousness
              </button>
            </div>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-hidden">
            {activeTab === 'chat' && (
              <ManagerChat
                websocketUrl={`/ws/${Date.now()}/${Math.random().toString(36).substr(2, 9)}`}
                persona="AI Orchestra Manager"
              />
            )}
            {activeTab === 'metrics' && (
              <MetricsPanel apiEndpoint="/metrics" />
            )}
            {activeTab === 'consciousness' && (
              <ConsciousnessPanel apiEndpoint="/consciousness" />
            )}
          </div>
        </main>

        {/* Right Sidebar */}
        <aside className="w-96 border-l border-white/10 bg-white/5 backdrop-blur-md overflow-y-auto">
          <div className="p-4">
            <h2 className="text-lg font-semibold mb-4 text-[#00e0ff]">Agent Configuration</h2>
            {selectedTeamId ? (
              <AgentConfigEditor
                fetchEndpoint={`/teams/${selectedTeamId}`}
                updateEndpoint={`/teams/${selectedTeamId}`}
                teamId={selectedTeamId}
              />
            ) : (
              <p className="text-white/50">Select a swarm to configure</p>
            )}
          </div>
          <div className="p-4 border-t border-white/10">
            <h2 className="text-lg font-semibold mb-4 text-[#00e0ff]">Memory Explorer</h2>
            <MemoryExplorer
              searchEndpoint="/memory/search"
              writeEndpoint="/memory/write"
              deleteEndpoint="/memory/delete"
            />
          </div>
        </aside>
      </div>

      {/* Footer */}
      <footer className="border-t border-white/10 bg-white/5 backdrop-blur-md py-4">
        <div className="container mx-auto px-4 flex items-center justify-between text-sm text-white/70">
          <span>© 2024 Pay Ready</span>
          <div className="flex gap-4">
            <a href="/docs" className="hover:text-[#00e0ff] transition-colors">Docs</a>
            <a href="https://github.com/your-repo" className="hover:text-[#00e0ff] transition-colors">GitHub</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
