'use client';

import { useEffect } from 'react';

import { useState } from 'react';
// NOTE: Local components may not exist yet; keep page functional.
// Replace missing imports with lightweight placeholders as needed.
import dynamic from 'next/dynamic';
import BuilderChatDock from '../components/BuilderChatDock';
import VoiceControl from '../components/VoiceControl';

const Placeholder = ({ title }: { title: string }) => (
  <div className="border border-gray-700 rounded p-4 bg-gray-800/50 text-sm text-gray-300">{title}</div>
);

const BuilderAgnoHeader: any = () => <div className="h-16 px-4 flex items-center border-b border-gray-700 bg-gray-900"><div className="text-lg font-semibold">Builder Agno System</div></div>;
const BuilderAgnoCodeEditor: any = () => <Placeholder title="Code Generation (coming soon)" />;
const BuilderAgnoSwarmPanel: any = () => <Placeholder title="Agent Swarms (wired to /api/builder)" />;
const BuilderAgnoRepositoryManager: any = () => <Placeholder title="Repositories (MCP-backed)" />;
const BuilderAgnoAgentStatus: any = () => <Placeholder title="Agent Status" />;

export default function BuilderAgnoSystem() {
  const [activeTab, setActiveTab] = useState<'code' | 'swarms' | 'repos'>('code');
  
  useEffect(() => {
    // Register service worker for PWA
    if ('serviceWorker' in navigator && process.env.NODE_ENV === 'production') {
      navigator.serviceWorker.register('/sw.js');
    }
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <BuilderAgnoHeader />
      
      <div className="flex h-[calc(100vh-64px)]">
        {/* Sidebar */}
        <div className="w-64 bg-gray-800 border-r border-gray-700 p-4">
          <h2 className="text-xl font-bold mb-4 text-purple-400">Builder Agno</h2>
          <nav className="space-y-2">
            <button
              onClick={() => setActiveTab('code')}
              className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                activeTab === 'code' 
                  ? 'bg-purple-600 text-white' 
                  : 'hover:bg-gray-700 text-gray-300'
              }`}
            >
              Code Generation
            </button>
            <button
              onClick={() => setActiveTab('swarms')}
              className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                activeTab === 'swarms' 
                  ? 'bg-purple-600 text-white' 
                  : 'hover:bg-gray-700 text-gray-300'
              }`}
            >
              Agent Swarms
            </button>
            <button
              onClick={() => setActiveTab('repos')}
              className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                activeTab === 'repos' 
                  ? 'bg-purple-600 text-white' 
                  : 'hover:bg-gray-700 text-gray-300'
              }`}
            >
              Repositories
            </button>
          </nav>
          
          <div className="mt-8">
            <BuilderAgnoAgentStatus />
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 p-6">
          {activeTab === 'code' && <BuilderAgnoCodeEditor />}
          {activeTab === 'swarms' && <BuilderAgnoSwarmPanel />}
          {activeTab === 'repos' && <BuilderAgnoRepositoryManager />}
        </div>
      </div>
    </div>
    <BuilderChatDock />
    <VoiceControl />
  );
}
