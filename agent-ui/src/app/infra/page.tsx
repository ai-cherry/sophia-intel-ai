'use client';

import React from 'react';
import { InfraQueue } from '@/components/unified/InfraQueue';
import { InfraDashboard } from '@/components/infrastructure/InfraDashboard';

export default function InfraPage() {
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
            <a href="/dashboard" className="hover:text-[#00e0ff] transition-colors">Dashboard</a>
            <a href="/memory" className="hover:text-[#00e0ff] transition-colors">Memory Explorer</a>
            <a href="/infra" className="text-[#00e0ff] hover:text-white transition-colors">InfraOps</a>
          </nav>
          <div className="w-10 h-10 rounded-full bg-gradient-to-r from-[#00e0ff] to-[#ff00c3] flex items-center justify-center font-bold">
            OP
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Infrastructure Operations</h1>
          <p className="text-white/70">Monitor and manage deployment, scaling, and infrastructure tasks</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Task Queue */}
          <div className="lg:col-span-2">
            <div className="bg-white/5 backdrop-blur-md rounded-xl border border-white/10 p-6">
              <h2 className="text-xl font-semibold mb-4 text-[#00e0ff]">Task Queue</h2>
              <InfraQueue apiEndpoint="/infra/tasks" expanded={true} />
            </div>

            {/* Infrastructure Dashboard */}
            <div className="mt-6 bg-white/5 backdrop-blur-md rounded-xl border border-white/10 p-6">
              <h2 className="text-xl font-semibold mb-4 text-[#00e0ff]">Infrastructure Overview</h2>
              <InfraDashboard />
            </div>
          </div>

          {/* Status Panels */}
          <div className="space-y-6">
            <div className="bg-white/5 backdrop-blur-md rounded-xl border border-white/10 p-6">
              <h3 className="text-lg font-semibold mb-4 text-[#00e0ff]">System Health</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-white/70">API Gateway</span>
                  <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded text-xs">Healthy</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-white/70">Swarm Orchestrator</span>
                  <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded text-xs">Running</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-white/70">Memory Store</span>
                  <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded text-xs">Connected</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-white/70">Redis Cache</span>
                  <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded text-xs">Active</span>
                </div>
              </div>
            </div>

            <div className="bg-white/5 backdrop-blur-md rounded-xl border border-white/10 p-6">
              <h3 className="text-lg font-semibold mb-4 text-[#00e0ff]">Resource Usage</h3>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-white/70">CPU</span>
                    <span className="font-mono">42%</span>
                  </div>
                  <div className="w-full bg-white/10 rounded-full h-2">
                    <div className="bg-gradient-to-r from-[#00e0ff] to-[#ff00c3] h-2 rounded-full" style={{width: '42%'}}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-white/70">Memory</span>
                    <span className="font-mono">68%</span>
                  </div>
                  <div className="w-full bg-white/10 rounded-full h-2">
                    <div className="bg-gradient-to-r from-[#00e0ff] to-[#ff00c3] h-2 rounded-full" style={{width: '68%'}}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-white/70">Storage</span>
                    <span className="font-mono">35%</span>
                  </div>
                  <div className="w-full bg-white/10 rounded-full h-2">
                    <div className="bg-gradient-to-r from-[#00e0ff] to-[#ff00c3] h-2 rounded-full" style={{width: '35%'}}></div>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white/5 backdrop-blur-md rounded-xl border border-white/10 p-6">
              <h3 className="text-lg font-semibold mb-4 text-[#00e0ff]">Recent Deployments</h3>
              <div className="space-y-2 text-sm">
                <div className="py-2 border-b border-white/10">
                  <div className="text-white/90">Swarm Alpha v2.1.0</div>
                  <div className="text-white/50 text-xs">Deployed 10 minutes ago</div>
                </div>
                <div className="py-2 border-b border-white/10">
                  <div className="text-white/90">Memory Service Update</div>
                  <div className="text-white/50 text-xs">Deployed 2 hours ago</div>
                </div>
                <div className="py-2">
                  <div className="text-white/90">API Gateway Patch</div>
                  <div className="text-white/50 text-xs">Deployed 5 hours ago</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
