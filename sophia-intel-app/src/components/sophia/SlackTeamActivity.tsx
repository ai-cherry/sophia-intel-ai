"use client";
import React, { useEffect, useState } from 'react';
import { fetchJSON } from '@/lib/api';

type SlackActivity = {
  status?: string;
  active_users?: number;
  channels?: number;
  error?: string;
  timestamp?: string;
};

export default function SlackTeamActivity() {
  const [data, setData] = useState<SlackActivity | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchJSON<SlackActivity>('/api/team/activity')
      .then(setData)
      .catch((e) => setError(e?.message || 'failed'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-sm text-gray-500">Loading Slack…</div>;
  if (error) return <div className="text-sm text-red-600">{error}</div>;
  if (!data) return <div className="text-sm text-gray-500">No Slack data</div>;

  if (data.status === 'unconfigured') {
    return <div className="text-sm text-gray-600">Slack not configured.</div>;
  }
  if (data.status === 'error') {
    return <div className="text-sm text-red-600">Slack error: {data.error}</div>;
  }

  return (
    <div className="text-sm">
      <div className="grid grid-cols-2 gap-3">
        <div className="border rounded-lg p-3 bg-white">
          <div className="text-xs text-gray-500">Active users</div>
          <div className="text-xl font-semibold">{data.active_users ?? 0}</div>
        </div>
        <div className="border rounded-lg p-3 bg-white">
          <div className="text-xs text-gray-500">Public channels</div>
          <div className="text-xl font-semibold">{data.channels ?? 0}</div>
        </div>
      </div>
      {data.timestamp && (
        <div className="mt-2 text-xs text-gray-500">{new Date(data.timestamp).toLocaleString()}</div>
      )}
    </div>
  );
}

