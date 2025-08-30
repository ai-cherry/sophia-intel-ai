'use client';

import { useState, useEffect } from 'react';
import { useUIStore } from '@/state/ui';
import { fetchJSON } from '@/lib/fetch';

export function EndpointPicker() {
  const { endpoint, isConnected, setEndpoint, setConnected } = useUIStore();
  const [inputValue, setInputValue] = useState(endpoint);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setInputValue(endpoint);
  }, [endpoint]);

  const handleConnect = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await fetchJSON<{ status: string }>(
        '/healthz',
        {},
        2,
        inputValue
      );
      
      if (result.status === 'ok') {
        setEndpoint(inputValue);
        setConnected(true);
        setError(null);
      } else {
        throw new Error('Invalid health check response');
      }
    } catch (e) {
      setConnected(false);
      setError(e instanceof Error ? e.message : 'Connection failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center gap-2 p-4 bg-white rounded-lg shadow-sm">
      <div className="flex-1">
        <input
          type="url"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleConnect()}
          placeholder="http://localhost:7777"
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={loading}
        />
      </div>
      
      <button
        onClick={handleConnect}
        disabled={loading}
        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? 'Connecting...' : 'Connect'}
      </button>
      
      <div className="flex items-center gap-2">
        <span
          className={`w-3 h-3 rounded-full ${
            isConnected ? 'bg-green-500' : 'bg-red-500'
          }`}
          title={isConnected ? 'Connected' : 'Disconnected'}
        />
        {isConnected && <span className="text-sm text-gray-600">Connected</span>}
      </div>
      
      {error && (
        <div className="absolute top-full left-0 right-0 mt-2 p-2 bg-red-50 text-red-700 rounded-md text-sm">
          {error}
        </div>
      )}
    </div>
  );
}