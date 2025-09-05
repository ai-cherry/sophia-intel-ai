'use client';

import { useState } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

/**
 * Essential swarm visualizations - Core features for Phase 1
 * Simplified from the original extensive UI enhancements
 */

export function SwarmVisualization({
  swarmId,
  status
}: {
  swarmId: string;
  status: string;
}) {
  const swarmIcons: Record<string, string> = {
    'strategic-swarm': '🎯',
    'development-swarm': '💻',
    'security-swarm': '🔒',
    'research-swarm': '🔬',
    'default': '🤖'
  };

  const statusColors: Record<string, string> = {
    'running': 'text-green-500 bg-green-50',
    'completed': 'text-blue-500 bg-blue-50',
    'error': 'text-red-500 bg-red-50',
    'idle': 'text-gray-500 bg-gray-50'
  };

  return (
    <div className="flex items-center gap-3 p-3 rounded-lg bg-gray-800 border border-gray-700">
      <span className="text-2xl">{swarmIcons[swarmId] || swarmIcons.default}</span>
      <div className="flex-1">
        <div className="text-sm font-medium text-gray-300">{swarmId}</div>
        <div className={cn(
          'text-xs px-2 py-0.5 rounded-full inline-block mt-1',
          statusColors[status] || 'text-gray-400 bg-gray-50'
        )}>
          {status.toUpperCase()}
        </div>
      </div>
    </div>
  );
}

export function StreamingIndicator({ isStreaming }: { isStreaming: boolean }) {
  if (!isStreaming) return null;

  return (
    <div className="flex items-center gap-2 px-3 py-1 bg-blue-900/20 border border-blue-700/30 rounded-full">
      <div className="flex gap-1">
        <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
        <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse delay-100"></div>
        <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse delay-200"></div>
      </div>
      <span className="text-xs text-blue-300">AI Processing...</span>
    </div>
  );
}

export function BasicMetrics({
  metrics
}: {
  metrics?: {
    confidence?: number;
    latency?: number;
    tokens?: number;
  };
}) {
  if (!metrics) {
    return (
      <div className="grid grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg border">
        <div className="text-center">
          <div className="text-lg font-bold text-gray-400">--</div>
          <div className="text-xs text-gray-500">Confidence</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-bold text-gray-400">--</div>
          <div className="text-xs text-gray-500">Latency</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-bold text-gray-400">--</div>
          <div className="text-xs text-gray-500">Tokens</div>
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg border">
      <div className="text-center">
        <div className="text-lg font-bold text-green-600">
          {metrics.confidence ? (metrics.confidence * 100).toFixed(1) + '%' : '0%'}
        </div>
        <div className="text-xs text-gray-500">Confidence</div>
      </div>
      <div className="text-center">
        <div className="text-lg font-bold text-blue-600">
          {metrics.latency || '0'}ms
        </div>
        <div className="text-xs text-gray-500">Latency</div>
      </div>
      <div className="text-center">
        <div className="text-lg font-bold text-purple-600">
          {metrics.tokens || '0'}
        </div>
        <div className="text-xs text-gray-500">Tokens</div>
      </div>
    </div>
  );
}

export function AgentStatusCard({
  agent,
  role,
  status
}: {
  agent: string;
  role: string;
  status: string;
}) {
  const roleColors: Record<string, string> = {
    'generator': 'border-green-500/50 bg-green-50',
    'validator': 'border-blue-500/50 bg-blue-50',
    'analyzer': 'border-purple-500/50 bg-purple-50',
    'reviewer': 'border-yellow-500/50 bg-yellow-50'
  };

  return (
    <div className={cn(
      'p-3 rounded-lg border transition-colors cursor-pointer hover:shadow-sm',
      roleColors[role] || 'border-gray-300 bg-gray-50'
    )}>
      <div className="flex justify-between items-start mb-2">
        <h4 className="text-sm font-semibold text-gray-800">{agent}</h4>
        <span className="text-xs px-2 py-0.5 bg-white/70 rounded-full text-gray-600 border">
          {role}
        </span>
      </div>
      <div className="text-xs text-gray-600">{status}</div>
    </div>
  );
}

export function SimpleTaskProgress({
  tasks
}: {
  tasks?: Array<{ name: string; status: string }>;
}) {
  if (!tasks || tasks.length === 0) {
    return (
      <div className="p-4 bg-gray-50 rounded-lg border text-center">
        <p className="text-sm text-gray-500">No tasks to display</p>
      </div>
    );
  }

  const completed = tasks.filter(t => t.status === 'completed').length;
  const progress = (completed / tasks.length) * 100;

  return (
    <div className="space-y-3 p-4 bg-white rounded-lg border">
      <div className="flex justify-between text-sm">
        <span className="text-gray-600">Progress</span>
        <span className="text-gray-800 font-medium">{completed}/{tasks.length} tasks</span>
      </div>

      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="space-y-1 mt-3 max-h-32 overflow-y-auto">
        {tasks.map((task, i) => (
          <div key={i} className="flex items-center gap-2 text-xs">
            <span className={cn(
              'w-1.5 h-1.5 rounded-full',
              task.status === 'completed' ? 'bg-green-500' :
              task.status === 'running' ? 'bg-blue-500' : 'bg-gray-400'
            )}>
            </span>
            <span className={cn(
              task.status === 'completed' ? 'text-gray-500 line-through' : 'text-gray-700'
            )}>
              {task.name}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function QuickMessageInput({
  onSend,
  placeholder = "Quick message to swarm...",
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
    <form onSubmit={handleSubmit} className="flex gap-2 p-3 bg-white rounded-lg border">
      <input
        type="text"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder={placeholder}
        disabled={isDisabled}
        className={cn(
          'flex-1 px-3 py-2 text-sm border rounded-md',
          'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
          'disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-100'
        )}
      />
      <Button
        type="submit"
        size="sm"
        disabled={!message.trim() || isDisabled}
      >
        Send
      </Button>
    </form>
  );
}
