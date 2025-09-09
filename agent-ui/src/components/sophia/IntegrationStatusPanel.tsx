"use client";
import React, { useEffect, useState } from 'react';
import { fetchJSON } from '@/lib/api';

type IntegrationData = {
  integrations?: Record<string, { status?: string; error?: string; details?: Record<string, any> }>;
  overall?: string;
  healthy_count?: number;
  total_integrations?: number;
};

const badge = (status?: string) => {
  switch (status) {
    case 'healthy': return 'bg-green-100 text-green-800 border-green-200';
    case 'configured': return 'bg-amber-100 text-amber-800 border-amber-200';
    case 'unconfigured': return 'bg-gray-100 text-gray-600 border-gray-200';
    default: return 'bg-red-100 text-red-800 border-red-200';
  }
};

export default function IntegrationStatusPanel() {
  const [data, setData] = useState<IntegrationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchJSON<IntegrationData>('/health/integrations')
      .then(setData)
      .catch((e) => setError(e?.message || 'failed'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-sm text-gray-500">Loading integrations…</div>;
  if (error) return <div className="text-sm text-red-600">{error}</div>;
  if (!data?.integrations) return <div className="text-sm text-gray-500">No integration data</div>;

  return (
    <div className="space-y-3">
      {data.overall && (
        <div className="text-xs">
          <span className="font-medium">Overall:</span>{' '}
          <span className={`${badge(data.overall)} border px-2 py-0.5 rounded-full`}>{data.overall}</span>
          {typeof data.healthy_count === 'number' && typeof data.total_integrations === 'number' && (
            <span className="ml-2 text-gray-500">{data.healthy_count}/{data.total_integrations} Active</span>
          )}
        </div>
      )}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
        {Object.entries(data.integrations).map(([name, info]) => (
          <div key={name} className={`border rounded-lg p-2 ${badge(info.status)}`}>
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium capitalize">{name}</span>
              <span className="text-[10px] opacity-70">{info.status || 'unknown'}</span>
            </div>
            {info.error && (
              <div className="mt-1 text-[10px] opacity-70 truncate" title={info.error}>{info.error}</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

