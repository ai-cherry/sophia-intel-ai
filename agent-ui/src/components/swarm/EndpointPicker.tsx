'use client';

import { useState, useEffect } from 'react';
import { usePlaygroundStore } from '@/store';
import { testEndpoint } from '@/lib/endpointUtils';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export function EndpointPicker() {
  const { 
    selectedEndpoint, 
    setSelectedEndpoint, 
    isEndpointActive, 
    setIsEndpointActive,
    isEndpointLoading,
    setIsEndpointLoading 
  } = usePlaygroundStore();
  
  const [inputValue, setInputValue] = useState(selectedEndpoint);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setInputValue(selectedEndpoint);
  }, [selectedEndpoint]);

  const handleConnect = async () => {
    setIsEndpointLoading(true);
    setError(null);
    
    try {
      const result = await testEndpoint(inputValue);
      
      if (result.success) {
        setSelectedEndpoint(inputValue);
        setIsEndpointActive(true);
        setError(null);
      } else {
        setIsEndpointActive(false);
        setError(result.error || 'Connection failed');
      }
    } catch (e) {
      setIsEndpointActive(false);
      setError(e instanceof Error ? e.message : 'Connection failed');
    } finally {
      setIsEndpointLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !isEndpointLoading) {
      handleConnect();
    }
  };

  return (
    <div className="relative">
      <div className="flex items-center gap-2 p-4 bg-white rounded-lg shadow-sm border">
        <div className="flex-1">
          <input
            type="url"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="http://localhost:8003"
            className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isEndpointLoading}
          />
        </div>
        
        <Button
          onClick={handleConnect}
          disabled={isEndpointLoading || !inputValue.trim()}
          className="px-4 py-2"
        >
          {isEndpointLoading ? 'Connecting...' : 'Connect'}
        </Button>
        
        <div className="flex items-center gap-2">
          <span
            className={cn(
              'w-3 h-3 rounded-full',
              isEndpointActive ? 'bg-green-500' : 'bg-red-500'
            )}
            title={isEndpointActive ? 'Connected' : 'Disconnected'}
          />
          {isEndpointActive && (
            <span className="text-sm text-gray-600">Connected</span>
          )}
        </div>
      </div>
      
      {error && (
        <div className="absolute top-full left-0 right-0 mt-2 p-2 bg-red-50 text-red-700 rounded-md text-sm border border-red-200">
          {error}
        </div>
      )}
    </div>
  );
}