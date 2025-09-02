'use client';

import React from 'react';
import { MemoryExplorer } from '@/components/unified/MemoryExplorer';

export default function MemoryPage() {
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
            <a href="/memory" className="text-[#00e0ff] hover:text-white transition-colors">Memory Explorer</a>
            <a href="/infra" className="hover:text-[#00e0ff] transition-colors">InfraOps</a>
          </nav>
          <div className="w-10 h-10 rounded-full bg-gradient-to-r from-[#00e0ff] to-[#ff00c3] flex items-center justify-center font-bold">
            OP
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Memory Explorer</h1>
          <p className="text-white/70">Search, analyze, and manage the collective memory of your AI swarms</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Search Panel */}
          <div className="lg:col-span-2">
            <div className="bg-white/5 backdrop-blur-md rounded-xl border border-white/10 p-6">
              <h2 className="text-xl font-semibold mb-4 text-[#00e0ff]">Memory Search</h2>
              <MemoryExplorer
                searchEndpoint="/memory/search"
                writeEndpoint="/memory/write"
                deleteEndpoint="/memory/delete"
                expanded={true}
              />
            </div>
          </div>

          {/* Stats Panel */}
          <div className="space-y-6">
            <div className="bg-white/5 backdrop-blur-md rounded-xl border border-white/10 p-6">
              <h3 className="text-lg font-semibold mb-4 text-[#00e0ff]">Memory Statistics</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-white/70">Total Memories</span>
                  <span className="font-mono">12,847</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-white/70">Vector Dimensions</span>
                  <span className="font-mono">1,536</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-white/70">Collections</span>
                  <span className="font-mono">8</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-white/70">Storage Used</span>
                  <span className="font-mono">2.4 GB</span>
                </div>
              </div>
            </div>

            <div className="bg-white/5 backdrop-blur-md rounded-xl border border-white/10 p-6">
              <h3 className="text-lg font-semibold mb-4 text-[#00e0ff]">Recent Activity</h3>
              <div className="space-y-2 text-sm">
                <div className="py-2 border-b border-white/10">
                  <div className="text-white/90">New memory indexed</div>
                  <div className="text-white/50 text-xs">2 minutes ago</div>
                </div>
                <div className="py-2 border-b border-white/10">
                  <div className="text-white/90">Vector search performed</div>
                  <div className="text-white/50 text-xs">5 minutes ago</div>
                </div>
                <div className="py-2">
                  <div className="text-white/90">Memory pruning completed</div>
                  <div className="text-white/50 text-xs">1 hour ago</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}