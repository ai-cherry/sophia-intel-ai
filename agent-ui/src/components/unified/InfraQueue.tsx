'use client';

import React, { useState, useEffect } from 'react';
import { Server, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react';

interface InfraTask {
  id: string;
  name: string;
  type: 'deployment' | 'security' | 'provisioning' | 'backup';
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  startedAt?: Date;
  completedAt?: Date;
  error?: string;
}

interface InfraQueueProps {
  apiEndpoint: string;
  expanded?: boolean;
}

export const InfraQueue: React.FC<InfraQueueProps> = ({ apiEndpoint, expanded = false }) => {
  const [tasks, setTasks] = useState<InfraTask[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, 3000); // Refresh every 3 seconds
    return () => clearInterval(interval);
  }, [apiEndpoint]);

  const fetchTasks = async () => {
    try {
      const response = await fetch(apiEndpoint);
      if (response.ok) {
        const data = await response.json();
        setTasks(data.tasks || []);
      }
    } catch (error) {
      console.error('Failed to fetch infrastructure tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-400" />;
      case 'running':
        return <Server className="w-4 h-4 text-blue-400 animate-pulse" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-400" />;
      default:
        return <AlertCircle className="w-4 h-4 text-gray-400" />;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'deployment':
        return 'bg-blue-500/20 text-blue-400';
      case 'security':
        return 'bg-yellow-500/20 text-yellow-400';
      case 'provisioning':
        return 'bg-green-500/20 text-green-400';
      case 'backup':
        return 'bg-purple-500/20 text-purple-400';
      default:
        return 'bg-gray-500/20 text-gray-400';
    }
  };

  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white/5 rounded-lg p-3 animate-pulse">
            <div className="h-4 bg-white/10 rounded w-3/4 mb-2"></div>
            <div className="h-2 bg-white/10 rounded w-full"></div>
          </div>
        ))}
      </div>
    );
  }

  const activeTasks = tasks.filter(t => t.status === 'running' || t.status === 'pending');
  const completedTasks = tasks.filter(t => t.status === 'completed' || t.status === 'failed');

  return (
    <div className={`space-y-4 ${expanded ? 'h-full flex flex-col' : ''}`}>
      {/* Active Tasks */}
      <div className={expanded ? 'flex-1 overflow-y-auto' : ''}>
        <h4 className="text-sm font-semibold text-white/70 mb-2">Active Tasks</h4>
        <div className="space-y-2">
          {activeTasks.length === 0 ? (
            <p className="text-white/50 text-sm text-center py-4">No active tasks</p>
          ) : (
            activeTasks.map((task) => (
              <div key={task.id} className="bg-white/5 rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(task.status)}
                    <span className="font-medium text-sm">{task.name}</span>
                  </div>
                  <span className={`px-2 py-0.5 rounded text-xs ${getTypeColor(task.type)}`}>
                    {task.type}
                  </span>
                </div>
                
                {task.status === 'running' && (
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs text-white/50">
                      <span>Progress</span>
                      <span>{task.progress}%</span>
                    </div>
                    <div className="w-full bg-white/10 rounded-full h-1.5">
                      <div
                        className="bg-gradient-to-r from-[#00e0ff] to-[#ff00c3] h-1.5 rounded-full transition-all"
                        style={{ width: `${task.progress}%` }}
                      />
                    </div>
                  </div>
                )}
                
                {task.error && (
                  <p className="text-xs text-red-400 mt-2">{task.error}</p>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Completed Tasks */}
      {!expanded && completedTasks.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-white/70 mb-2">Recent</h4>
          <div className="space-y-2">
            {completedTasks.slice(0, 3).map((task) => (
              <div key={task.id} className="bg-white/5 rounded-lg p-2 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {getStatusIcon(task.status)}
                  <span className="text-sm text-white/70">{task.name}</span>
                </div>
                <span className="text-xs text-white/50">
                  {task.completedAt && new Date(task.completedAt).toLocaleTimeString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};