"use client";
import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

type Item = {
  status: 'green' | 'yellow' | 'red';
  env: Record<string, boolean>;
  endpoints: string[];
};

type Report = {
  summary: { timestamp: string; counts: { green: number; yellow: number; red: number } };
  items: Record<string, Item>;
};

export default function IntegrationStatusPanel() {
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/integrations/report')
      .then((r) => r.json())
      .then(setReport)
      .catch((e) => setError(String(e)));
  }, []);

  const statusBadge = (s: string) => (
    <Badge className={`capitalize ${s === 'green' ? 'bg-emerald-600' : s === 'yellow' ? 'bg-amber-600' : 'bg-rose-600'}`}>{s}</Badge>
  );

  if (error) {
    return <div className="text-sm text-red-600">Error loading integrations: {error}</div>;
  }
  if (!report) {
    return <div className="text-sm text-gray-500">Loading integrations…</div>;
  }

  const entries = Object.entries(report.items);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      {entries.map(([name, item]) => (
        <Card key={name} className="border border-gray-200 dark:border-gray-800">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-sm font-semibold capitalize">{name}</CardTitle>
            {statusBadge(item.status)}
          </CardHeader>
          <CardContent>
            <div className="text-xs text-gray-500 dark:text-gray-400 space-y-2">
              <div>
                <span className="font-medium">Env:</span>{' '}
                {Object.entries(item.env).map(([k, v]) => (
                  <span key={k} className={`inline-block mr-2 ${v ? 'text-emerald-600' : 'text-rose-600'}`}>{k}:{v ? '✔' : '✗'}</span>
                ))}
              </div>
              {item.endpoints && item.endpoints.length > 0 && (
                <div>
                  <span className="font-medium">Endpoints:</span>{' '}
                  <span className="text-[11px] opacity-80">{item.endpoints.join(', ')}</span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

