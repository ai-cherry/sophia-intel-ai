'use client';

import { useState, useEffect } from 'react';
import { usePlaygroundStore } from '@/store';
import { fetchJSON } from '@/lib/fetchUtils';
import { streamText } from '@/lib/streamUtils';
import { buildEndpointUrl } from '@/lib/endpointUtils';
import { Team, Workflow, StreamResponse } from '@/types/swarm';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { cn } from '@/lib/utils';

export function TeamWorkflowPanel() {
  const {
    selectedEndpoint,
    isEndpointActive,
    teams,
    setTeams,
    selectedTeamId,
    setSelectedTeamId,
    isStreaming,
    setIsStreaming,
  } = usePlaygroundStore();

  // Local state for workflows and form data
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null);
  const [activeTab, setActiveTab] = useState<'team' | 'workflow'>('team');
  const [message, setMessage] = useState('');
  const [additionalData, setAdditionalData] = useState('{}');
  const [pool, setPool] = useState<'fast' | 'heavy' | 'balanced'>('balanced');
  const [priority, setPriority] = useState<'low' | 'medium' | 'high' | 'critical'>('medium');
  const [error, setError] = useState<string | null>(null);
  const [streamContent, setStreamContent] = useState('');
  const [lastResponse, setLastResponse] = useState<StreamResponse | null>(null);

  const selectedTeam = teams.find(team => team.value === selectedTeamId);

  useEffect(() => {
    if (isEndpointActive) {
      loadTeamsAndWorkflows();
    }
  }, [isEndpointActive, selectedEndpoint]);

  const loadTeamsAndWorkflows = async () => {
    try {
      const [teamsData, workflowsData] = await Promise.all([
        fetchJSON<any[]>(buildEndpointUrl(selectedEndpoint, '/teams')),
        fetchJSON<Workflow[]>(buildEndpointUrl(selectedEndpoint, '/workflows')),
      ]);

      // Transform teams data to match agent-ui format
      const formattedTeams = teamsData?.map(team => ({
        value: team.id || team.name,
        label: team.name || team.id,
        model: { provider: 'swarm' },
      })) || [];

      setTeams(formattedTeams);
      setWorkflows(workflowsData || []);
    } catch (e) {
      console.error('Failed to load teams/workflows:', e);
      setError('Failed to load teams and workflows');
    }
  };

  const runTeam = async () => {
    if (!selectedTeam || !message.trim() || isStreaming) return;

    setError(null);
    setStreamContent('');
    setLastResponse(null);
    setIsStreaming(true);

    try {
      const parsedData = JSON.parse(additionalData);

      await streamText(buildEndpointUrl(selectedEndpoint, '/teams/run'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          team_id: selectedTeam.value,
          pool,
          additional_data: {
            ...parsedData,
            priority,
          },
        }),
        onToken: (token) => {
          setStreamContent(prev => prev + token);
        },
        onDone: (final) => {
          setLastResponse(final);
          setIsStreaming(false);
        },
        onError: (e) => {
          setError(e.message);
          setIsStreaming(false);
        },
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to run team');
      setIsStreaming(false);
    }
  };

  const runWorkflow = async () => {
    if (!selectedWorkflow || !message.trim() || isStreaming) return;

    setError(null);
    setStreamContent('');
    setLastResponse(null);
    setIsStreaming(true);

    try {
      const parsedData = JSON.parse(additionalData);

      await streamText(buildEndpointUrl(selectedEndpoint, '/workflows/run'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          workflow_id: selectedWorkflow.id,
          message,
          additional_data: {
            ...parsedData,
            pool,
            priority,
          },
        }),
        onToken: (token) => {
          setStreamContent(prev => prev + token);
        },
        onDone: (final) => {
          setLastResponse(final);
          setIsStreaming(false);
        },
        onError: (e) => {
          setError(e.message);
          setIsStreaming(false);
        },
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to run workflow');
      setIsStreaming(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 border">
      {/* Tabs */}
      <div className="flex gap-2 mb-4">
        <Button
          variant={activeTab === 'team' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setActiveTab('team')}
        >
          Team
        </Button>
        <Button
          variant={activeTab === 'workflow' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setActiveTab('workflow')}
        >
          Workflow
        </Button>
      </div>

      {/* Selection */}
      <div className="mb-4">
        {activeTab === 'team' ? (
          <Select
            value={selectedTeamId || ''}
            onValueChange={setSelectedTeamId}
            disabled={!isEndpointActive || teams.length === 0}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select a team..." />
            </SelectTrigger>
            <SelectContent>
              {teams.map(team => (
                <SelectItem key={team.value} value={team.value}>
                  {team.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        ) : (
          <Select
            value={selectedWorkflow?.id || ''}
            onValueChange={(value) => {
              const workflow = workflows.find(w => w.id === value);
              setSelectedWorkflow(workflow || null);
            }}
            disabled={!isEndpointActive || workflows.length === 0}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select a workflow..." />
            </SelectTrigger>
            <SelectContent>
              {workflows.map(workflow => (
                <SelectItem key={workflow.id} value={workflow.id}>
                  {workflow.name} {workflow.description && `- ${workflow.description}`}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
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
          <Select
            value={pool}
            onValueChange={(value) => setPool(value as 'fast' | 'heavy' | 'balanced')}
            disabled={isStreaming}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="fast">Fast</SelectItem>
              <SelectItem value="balanced">Balanced</SelectItem>
              <SelectItem value="heavy">Heavy</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Priority
          </label>
          <Select
            value={priority}
            onValueChange={(value) => setPriority(value as 'low' | 'medium' | 'high' | 'critical')}
            disabled={isStreaming}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="low">Low</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="high">High</SelectItem>
              <SelectItem value="critical">Critical</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Run Button */}
      <Button
        onClick={activeTab === 'team' ? runTeam : runWorkflow}
        disabled={
          isStreaming ||
          !isEndpointActive ||
          !message.trim() ||
          (activeTab === 'team' ? !selectedTeam : !selectedWorkflow)
        }
        className="w-full"
      >
        {isStreaming
          ? 'Running...'
          : activeTab === 'team'
          ? 'Run Team'
          : 'Run Workflow'}
      </Button>

      {/* Error Display */}
      {error && (
        <div className="mt-4 p-3 bg-red-50 text-red-700 rounded-md border border-red-200">
          {error}
        </div>
      )}

      {/* Stream Output */}
      {(streamContent || lastResponse) && (
        <div className="mt-4 p-3 bg-gray-50 rounded-md">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Output</h4>
          <pre className="text-xs whitespace-pre-wrap font-mono">
            {streamContent}
            {isStreaming && <span className="inline-block w-2 h-3 bg-blue-600 animate-pulse ml-1" />}
          </pre>
          {lastResponse && (
            <div className="mt-2 pt-2 border-t text-xs text-gray-500">
              Final response received with {Object.keys(lastResponse).length} properties
            </div>
          )}
        </div>
      )}
    </div>
  );
}
