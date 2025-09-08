"use client";
import React from 'react';
import { useAgnoBridgeHealth } from '@/hooks/useAgnoBridgeHealth';

function Pill({ color, children }: { color: 'green' | 'amber' | 'red'; children: React.ReactNode }) {
  const map: Record<typeof color, string> = {
    green: 'bg-green-100 text-green-800 border-green-200',
    amber: 'bg-amber-100 text-amber-800 border-amber-200',
    red: 'bg-red-100 text-red-800 border-red-200',
  } as const;
  return <span className={`text-xs px-2 py-1 rounded-full border ${map[color]}`}>{children}</span>;
}

export default function AgnoBridgeStatus() {
  const enabled = process.env.NEXT_PUBLIC_ENABLE_AGNO_BRIDGE === 'true';
  const { data, loading, error } = useAgnoBridgeHealth(enabled);

  if (!enabled) return null;
  if (loading) return <Pill color="amber">Bridge: checking…</Pill>;
  if (error || !data) return <Pill color="red">Bridge: offline</Pill>;

  const core = data.core || {};
  const badge = core.status === 'healthy' ? (
    <Pill color="green">Bridge: ok • agents {core.agents ?? 0} • teams {core.teams ?? 0}</Pill>
  ) : (
    <Pill color="amber">Bridge: {core.status || 'degraded'}</Pill>
  );

  return badge;
}
