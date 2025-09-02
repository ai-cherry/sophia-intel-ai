'use client';

import React, { useState, useEffect } from 'react';
import { Save, RefreshCw } from 'lucide-react';

interface AgentConfig {
  model: string;
  instructions: string;
  persona: string;
  communicationRules: string[];
  temperature: number;
  maxTokens: number;
  policies: {
    allowGithub: boolean;
    allowDatabase: boolean;
    allowExternalAPIs: boolean;
  };
}

interface AgentConfigEditorProps {
  fetchEndpoint: string;
  updateEndpoint: string;
  teamId: string;
}

export const AgentConfigEditor: React.FC<AgentConfigEditorProps> = ({
  fetchEndpoint,
  updateEndpoint,
  teamId
}) => {
  const [config, setConfig] = useState<AgentConfig>({
    model: 'gpt-4',
    instructions: '',
    persona: '',
    communicationRules: [],
    temperature: 0.7,
    maxTokens: 2000,
    policies: {
      allowGithub: false,
      allowDatabase: false,
      allowExternalAPIs: false
    }
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (teamId) {
      fetchConfig();
    }
  }, [teamId]);

  const fetchConfig = async () => {
    setLoading(true);
    try {
      const response = await fetch(fetchEndpoint);
      if (response.ok) {
        const data = await response.json();
        setConfig(data);
      }
    } catch (error) {
      console.error('Failed to fetch configuration:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async () => {
    setSaving(true);
    try {
      const response = await fetch(updateEndpoint, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      
      if (response.ok) {
        // Show success feedback
        console.log('Configuration saved successfully');
      }
    } catch (error) {
      console.error('Failed to save configuration:', error);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-10 bg-white/10 rounded animate-pulse"></div>
        <div className="h-32 bg-white/10 rounded animate-pulse"></div>
        <div className="h-10 bg-white/10 rounded animate-pulse"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Model Selection */}
      <div>
        <label className="block text-sm font-medium mb-2">Model</label>
        <select
          value={config.model}
          onChange={(e) => setConfig({ ...config, model: e.target.value })}
          className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-[#00e0ff] transition-colors"
        >
          <option value="gpt-4">GPT-4</option>
          <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
          <option value="claude-3-opus">Claude 3 Opus</option>
          <option value="claude-3-sonnet">Claude 3 Sonnet</option>
        </select>
      </div>

      {/* Instructions */}
      <div>
        <label className="block text-sm font-medium mb-2">Instructions</label>
        <textarea
          value={config.instructions}
          onChange={(e) => setConfig({ ...config, instructions: e.target.value })}
          rows={4}
          className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white placeholder-white/50 focus:outline-none focus:border-[#00e0ff] transition-colors resize-none"
          placeholder="Define the agent's primary instructions..."
        />
      </div>

      {/* Persona */}
      <div>
        <label className="block text-sm font-medium mb-2">Persona</label>
        <input
          type="text"
          value={config.persona}
          onChange={(e) => setConfig({ ...config, persona: e.target.value })}
          className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white placeholder-white/50 focus:outline-none focus:border-[#00e0ff] transition-colors"
          placeholder="e.g., Senior Software Engineer"
        />
      </div>

      {/* Parameters */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-2">Temperature</label>
          <input
            type="number"
            min="0"
            max="2"
            step="0.1"
            value={config.temperature}
            onChange={(e) => setConfig({ ...config, temperature: parseFloat(e.target.value) })}
            className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-[#00e0ff] transition-colors"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Max Tokens</label>
          <input
            type="number"
            min="100"
            max="8000"
            step="100"
            value={config.maxTokens}
            onChange={(e) => setConfig({ ...config, maxTokens: parseInt(e.target.value) })}
            className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-[#00e0ff] transition-colors"
          />
        </div>
      </div>

      {/* Policies */}
      <div>
        <label className="block text-sm font-medium mb-2">Policies</label>
        <div className="space-y-2">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={config.policies.allowGithub}
              onChange={(e) => setConfig({
                ...config,
                policies: { ...config.policies, allowGithub: e.target.checked }
              })}
              className="w-4 h-4 bg-white/10 border-white/20 rounded text-[#00e0ff] focus:ring-[#00e0ff]"
            />
            <span className="text-sm">Allow GitHub Access</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={config.policies.allowDatabase}
              onChange={(e) => setConfig({
                ...config,
                policies: { ...config.policies, allowDatabase: e.target.checked }
              })}
              className="w-4 h-4 bg-white/10 border-white/20 rounded text-[#00e0ff] focus:ring-[#00e0ff]"
            />
            <span className="text-sm">Allow Database Access</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={config.policies.allowExternalAPIs}
              onChange={(e) => setConfig({
                ...config,
                policies: { ...config.policies, allowExternalAPIs: e.target.checked }
              })}
              className="w-4 h-4 bg-white/10 border-white/20 rounded text-[#00e0ff] focus:ring-[#00e0ff]"
            />
            <span className="text-sm">Allow External APIs</span>
          </label>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <button
          onClick={saveConfig}
          disabled={saving}
          className="flex-1 bg-gradient-to-r from-[#00e0ff] to-[#ff00c3] text-white rounded-lg px-4 py-2 hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          <Save className="w-4 h-4" />
          {saving ? 'Saving...' : 'Save Configuration'}
        </button>
        <button
          onClick={fetchConfig}
          className="p-2 bg-white/10 rounded-lg hover:bg-white/20 transition-colors"
          title="Refresh"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};