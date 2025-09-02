'use client';

import React, { useState, useEffect } from 'react';
import { Activity, Settings, Play, Pause, StopCircle } from 'lucide-react';

interface Swarm {
  id: string;
  name: string;
  status: 'active' | 'paused' | 'stopped';
  model: string;
  capabilities: string[];
  lastActive: Date;
}

interface SwarmListProps {
  apiEndpoint: string;
  onSelect: (teamId: string) => void;
  selectedTeamId?: string | null;
}

export const SwarmList: React.FC<SwarmListProps> = ({ apiEndpoint, onSelect, selectedTeamId }) => {
  const [swarms, setSwarms] = useState<Swarm[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSwarms();
    const interval = setInterval(fetchSwarms, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, [apiEndpoint]);

  const fetchSwarms = async () => {
    try {
      const response = await fetch(apiEndpoint);
      if (response.ok) {
        const data = await response.json();
        setSwarms(data.teams || []);
      }
    } catch (error) {
      console.error('Failed to fetch swarms:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAction = async (swarmId: string, action: string) => {
    try {
      const response = await fetch(`${apiEndpoint}/${swarmId}/actions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action })
      });
      
      if (response.ok) {
        fetchSwarms(); // Refresh the list
      }
    } catch (error) {
      console.error(`Failed to ${action} swarm:`, error);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <Activity className="w-4 h-4 text-green-400" />;
      case 'paused':
        return <Pause className="w-4 h-4 text-yellow-400" />;
      case 'stopped':
        return <StopCircle className="w-4 h-4 text-red-400" />;
      default:
        return null;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'paused':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'stopped':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      default:
        return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white/5 rounded-lg p-3 animate-pulse">
            <div className="h-4 bg-white/10 rounded w-3/4 mb-2"></div>
            <div className="h-3 bg-white/10 rounded w-1/2"></div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {swarms.map((swarm) => (
        <div
          key={swarm.id}
          onClick={() => onSelect(swarm.id)}
          className={`bg-white/5 rounded-lg p-3 cursor-pointer transition-all hover:bg-white/10 ${
            selectedTeamId === swarm.id ? 'ring-2 ring-[#00e0ff]' : ''
          }`}
        >
          <div className="flex items-start justify-between mb-2">
            <div className="flex items-center gap-2">
              {getStatusIcon(swarm.status)}
              <h4 className="font-semibold">{swarm.name}</h4>
            </div>
            <Settings className="w-4 h-4 text-white/50 hover:text-white transition-colors" />
          </div>
          
          <div className="text-sm text-white/70 mb-2">
            Model: <span className="text-white/90 font-mono">{swarm.model}</span>
          </div>
          
          <div className="flex flex-wrap gap-1 mb-2">
            {swarm.capabilities.slice(0, 3).map((cap, idx) => (
              <span
                key={idx}
                className="px-2 py-0.5 bg-white/10 rounded text-xs"
              >
                {cap}
              </span>
            ))}
            {swarm.capabilities.length > 3 && (
              <span className="px-2 py-0.5 bg-white/10 rounded text-xs">
                +{swarm.capabilities.length - 3}
              </span>
            )}
          </div>
          
          <div className="flex items-center justify-between">
            <span className={`px-2 py-1 rounded text-xs border ${getStatusColor(swarm.status)}`}>
              {swarm.status}
            </span>
            
            <div className="flex gap-1">
              {swarm.status === 'stopped' && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleAction(swarm.id, 'deploy');
                  }}
                  className="p-1 hover:bg-white/10 rounded transition-colors"
                  title="Deploy"
                >
                  <Play className="w-3 h-3" />
                </button>
              )}
              {swarm.status === 'active' && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleAction(swarm.id, 'pause');
                  }}
                  className="p-1 hover:bg-white/10 rounded transition-colors"
                  title="Pause"
                >
                  <Pause className="w-3 h-3" />
                </button>
              )}
              {swarm.status === 'paused' && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleAction(swarm.id, 'resume');
                  }}
                  className="p-1 hover:bg-white/10 rounded transition-colors"
                  title="Resume"
                >
                  <Play className="w-3 h-3" />
                </button>
              )}
              {swarm.status !== 'stopped' && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleAction(swarm.id, 'terminate');
                  }}
                  className="p-1 hover:bg-white/10 rounded transition-colors"
                  title="Stop"
                >
                  <StopCircle className="w-3 h-3" />
                </button>
              )}
            </div>
          </div>
        </div>
      ))}
      
      {swarms.length === 0 && (
        <div className="text-center text-white/50 py-4">
          <p>No swarms configured</p>
        </div>
      )}
    </div>
  );
};