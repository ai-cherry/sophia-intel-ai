'use client';

import { useEffect, useState } from 'react';

/**
 * UI Enhancements for Better User Experience
 * Q3 2025 Upgrade - Modern, responsive, accessible
 */

export function SwarmVisualization({ swarmId, status }: { swarmId: string; status: string }) {
  const swarmIcons = {
    'strategic-swarm': '🎯',
    'development-swarm': '💻',
    'security-swarm': '🔒',
    'research-swarm': '🔬'
  };

  const statusColors = {
    'running': 'text-green-500',
    'completed': 'text-blue-500',
    'error': 'text-red-500',
    'idle': 'text-gray-500'
  };

  return (
    <div className="flex items-center gap-2 p-2 rounded-lg bg-gray-800 border border-gray-700">
      <span className="text-2xl">{swarmIcons[swarmId] || '🤖'}</span>
      <div className="flex-1">
        <div className="text-sm font-medium text-gray-300">{swarmId}</div>
        <div className={`text-xs ${statusColors[status] || 'text-gray-400'}`}>
          {status.toUpperCase()}
        </div>
      </div>
    </div>
  );
}

export function RealTimeMetrics({ metrics }: { metrics: any }) {
  return (
    <div className="grid grid-cols-3 gap-4 p-4 bg-gray-900 rounded-lg">
      <div className="text-center">
        <div className="text-2xl font-bold text-green-400">
          {metrics?.confidence || '0.0'}
        </div>
        <div className="text-xs text-gray-500">Confidence</div>
      </div>
      <div className="text-center">
        <div className="text-2xl font-bold text-blue-400">
          {metrics?.latency || '0'}ms
        </div>
        <div className="text-xs text-gray-500">Latency</div>
      </div>
      <div className="text-center">
        <div className="text-2xl font-bold text-purple-400">
          {metrics?.tokens || '0'}
        </div>
        <div className="text-xs text-gray-500">Tokens</div>
      </div>
    </div>
  );
}

export function StreamingIndicator({ isStreaming }: { isStreaming: boolean }) {
  if (!isStreaming) return null;
  
  return (
    <div className="flex items-center gap-2 px-3 py-1 bg-blue-900/30 border border-blue-700 rounded-full">
      <div className="flex gap-1">
        <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
        <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse delay-100"></div>
        <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse delay-200"></div>
      </div>
      <span className="text-xs text-blue-300">Real AI Processing...</span>
    </div>
  );
}

export function AgentCard({ agent, role, status }: { agent: string; role: string; status: string }) {
  const roleColors = {
    'generator': 'border-green-600',
    'validator': 'border-blue-600',
    'analyzer': 'border-purple-600',
    'reviewer': 'border-yellow-600'
  };

  return (
    <div className={`p-3 rounded-lg bg-gray-800/50 border ${roleColors[role] || 'border-gray-600'} 
                     hover:bg-gray-800 transition-colors cursor-pointer`}>
      <div className="flex justify-between items-start mb-2">
        <h4 className="text-sm font-semibold text-gray-200">{agent}</h4>
        <span className="text-xs px-2 py-0.5 bg-gray-700 rounded-full text-gray-400">
          {role}
        </span>
      </div>
      <div className="text-xs text-gray-500">{status}</div>
    </div>
  );
}

export function CodePreview({ code, language = 'javascript' }: { code: string; language?: string }) {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative group">
      <pre className="p-4 bg-gray-950 rounded-lg overflow-x-auto">
        <code className={`language-${language} text-sm`}>{code}</code>
      </pre>
      <button
        onClick={copyToClipboard}
        className="absolute top-2 right-2 px-2 py-1 text-xs bg-gray-800 hover:bg-gray-700 
                   rounded opacity-0 group-hover:opacity-100 transition-opacity"
      >
        {copied ? '✓ Copied' : 'Copy'}
      </button>
    </div>
  );
}

export function TaskProgress({ tasks }: { tasks: Array<{ name: string; status: string }> }) {
  const completed = tasks.filter(t => t.status === 'completed').length;
  const progress = (completed / tasks.length) * 100;

  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span className="text-gray-400">Progress</span>
        <span className="text-gray-300">{completed}/{tasks.length} tasks</span>
      </div>
      <div className="w-full bg-gray-800 rounded-full h-2">
        <div 
          className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all"
          style={{ width: `${progress}%` }}
        />
      </div>
      <div className="space-y-1 mt-3">
        {tasks.map((task, i) => (
          <div key={i} className="flex items-center gap-2 text-xs">
            <span className={task.status === 'completed' ? 'text-green-500' : 'text-gray-500'}>
              {task.status === 'completed' ? '✓' : '○'}
            </span>
            <span className={task.status === 'completed' ? 'text-gray-400 line-through' : 'text-gray-300'}>
              {task.name}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function MessageInput({ 
  onSend, 
  placeholder = "Ask your AI swarm anything...",
  isDisabled = false 
}: { 
  onSend: (message: string) => void;
  placeholder?: string;
  isDisabled?: boolean;
}) {
  const [message, setMessage] = useState('');
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isDisabled) {
      onSend(message);
      setMessage('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative">
      <input
        type="text"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder={placeholder}
        disabled={isDisabled}
        className="w-full px-4 py-3 pr-12 bg-gray-800 border border-gray-700 rounded-lg 
                   text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500
                   disabled:opacity-50 disabled:cursor-not-allowed"
      />
      <button
        type="submit"
        disabled={!message.trim() || isDisabled}
        className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-blue-400 
                   hover:text-blue-300 disabled:text-gray-600 disabled:cursor-not-allowed"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
        </svg>
      </button>
    </form>
  );
}