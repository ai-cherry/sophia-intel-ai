'use client';

import { useState, useEffect } from 'react';
import { useUIStore } from '@/state/ui';
import { fetchJSON } from '@/lib/fetch';
import { streamText } from '@/lib/sse';
import { Team, Workflow } from '@/lib/types';

export function TeamWorkflowPanel() {
  const {
    endpoint,
    isConnected,
    teams,
    workflows,
    selectedTeam,
    selectedWorkflow,
    pool,
    priority,
    setTeams,
    setWorkflows,
    selectTeam,
    selectWorkflow,
    setPool,
    setPriority,
    isStreaming,
    setStreaming,
    appendContent,
    clearContent,
    setLastResponse,
  } = useUIStore();

  const [activeTab, setActiveTab] = useState<'team' | 'workflow'>('team');
  const [message, setMessage] = useState('');
  const [additionalData, setAdditionalData] = useState('{}');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isConnected) {
      loadTeamsAndWorkflows();
    }
  }, [isConnected, endpoint]);

  const loadTeamsAndWorkflows = async () => {
    try {
      const [teamsData, workflowsData] = await Promise.all([
        fetchJSON<Team[]>('/teams', {}, 2, endpoint),
        fetchJSON<Workflow[]>('/workflows', {}, 2, endpoint),
      ]);
      setTeams(teamsData || []);
      setWorkflows(workflowsData || []);
    } catch (e) {
      console.error('Failed to load teams/workflows:', e);
    }
  };

  const runTeam = async () => {
    if (!selectedTeam || !message.trim() || isStreaming) return;
    
    setError(null);
    clearContent();
    setStreaming(true);
    
    try {
      const parsedData = JSON.parse(additionalData);
      
      await streamText(`${endpoint}/teams/run`, {
        method: 'POST',
        body: JSON.stringify({
          message,
          team_id: selectedTeam.id,
          pool,
          additional_data: {
            ...parsedData,
            priority,
          },
        }),
        onToken: appendContent,
        onDone: (final) => {
          setLastResponse(final);
          setStreaming(false);
        },
        onError: (e) => {
          setError(e.message);
          setStreaming(false);
        },
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to run team');
      setStreaming(false);
    }
  };

  const runWorkflow = async () => {
    if (!selectedWorkflow || !message.trim() || isStreaming) return;
    
    setError(null);
    clearContent();
    setStreaming(true);
    
    try {
      const parsedData = JSON.parse(additionalData);
      
      await streamText(`${endpoint}/workflows/run`, {
        method: 'POST',
        body: JSON.stringify({
          workflow_id: selectedWorkflow.id,
          message,
          additional_data: {
            ...parsedData,
            pool,
            priority,
          },
        }),
        onToken: appendContent,
        onDone: (final) => {
          setLastResponse(final);
          setStreaming(false);
        },
        onError: (e) => {
          setError(e.message);
          setStreaming(false);
        },
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to run workflow');
      setStreaming(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      {/* Tabs */}
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setActiveTab('team')}
          className={`px-4 py-2 rounded-md ${
            activeTab === 'team'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          Team
        </button>
        <button
          onClick={() => setActiveTab('workflow')}
          className={`px-4 py-2 rounded-md ${
            activeTab === 'workflow'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          Workflow
        </button>
      </div>

      {/* Selection */}
      <div className="mb-4">
        {activeTab === 'team' ? (
          <select
            value={selectedTeam?.id || ''}
            onChange={(e) => {
              const team = teams.find(t => t.id === e.target.value);
              selectTeam(team || null);
            }}
            className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={!isConnected || teams.length === 0}
          >
            <option value="">Select a team...</option>
            {teams.map(team => (
              <option key={team.id} value={team.id}>
                {team.name} {team.description && `- ${team.description}`}
              </option>
            ))}
          </select>
        ) : (
          <select
            value={selectedWorkflow?.id || ''}
            onChange={(e) => {
              const workflow = workflows.find(w => w.id === e.target.value);
              selectWorkflow(workflow || null);
            }}
            className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={!isConnected || workflows.length === 0}
          >
            <option value="">Select a workflow...</option>
            {workflows.map(workflow => (
              <option key={workflow.id} value={workflow.id}>
                {workflow.name} {workflow.description && `- ${workflow.description}`}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Message */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Message
        </label>
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Enter your task or question..."
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          rows={4}
          disabled={isStreaming}
        />
      </div>

      {/* Additional Data */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Additional Data (JSON)
        </label>
        <textarea
          value={additionalData}
          onChange={(e) => setAdditionalData(e.target.value)}
          placeholder='{"repo": "ai-cherry/sophia-ai", "branch": "main"}'
          className="w-full px-3 py-2 border rounded-md font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          rows={3}
          disabled={isStreaming}
        />
      </div>

      {/* Meta Options */}
      <div className="flex gap-4 mb-4">
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Pool
          </label>
          <select
            value={pool}
            onChange={(e) => setPool(e.target.value as 'fast' | 'heavy' | 'balanced')}
            className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isStreaming}
          >
            <option value="fast">Fast</option>
            <option value="balanced">Balanced</option>
            <option value="heavy">Heavy</option>
          </select>
        </div>
        
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Priority
          </label>
          <select
            value={priority}
            onChange={(e) => setPriority(e.target.value as 'low' | 'medium' | 'high' | 'critical')}
            className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isStreaming}
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
        </div>
      </div>

      {/* Run Button */}
      <button
        onClick={activeTab === 'team' ? runTeam : runWorkflow}
        disabled={
          isStreaming ||
          !isConnected ||
          !message.trim() ||
          (activeTab === 'team' ? !selectedTeam : !selectedWorkflow)
        }
        className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isStreaming
          ? 'Running...'
          : activeTab === 'team'
          ? 'Run Team'
          : 'Run Workflow'}
      </button>

      {/* Error Display */}
      {error && (
        <div className="mt-4 p-3 bg-red-50 text-red-700 rounded-md">
          {error}
        </div>
      )}
    </div>
  );
}