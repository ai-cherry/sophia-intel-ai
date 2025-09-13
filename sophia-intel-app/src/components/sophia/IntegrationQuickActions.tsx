"use client";
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

type Provider = 'slack' | 'salesforce' | 'microsoft' | 'asana';

const healthPaths: Record<Provider, string> = {
  slack: '/api/slack/health',
  salesforce: '/api/salesforce/health',
  microsoft: '/api/microsoft/health',
  asana: '/api/asana/health',
};

const connectPaths: Record<Provider, string> = {
  slack: '/api/slack/oauth/start', // optional; webhook-only setups may skip
  salesforce: '/api/salesforce/oauth/start',
  microsoft: '/api/microsoft/oauth/start',
  asana: '/api/asana/oauth/start',
};

export default function IntegrationQuickActions() {
  const [status, setStatus] = useState<Record<string, 'ok' | 'error' | 'idle'>>({});
  const [details, setDetails] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState<Record<string, boolean>>({});

  const providers: Provider[] = ['slack', 'salesforce', 'microsoft', 'asana'];

  const testHealth = async (name: Provider) => {
    setLoading((s) => ({ ...s, [name]: true }));
    try {
      const r = await fetch(healthPaths[name]);
      const j = await r.json();
      setDetails((d) => ({ ...d, [name]: j }));
      setStatus((s) => ({ ...s, [name]: j.ok ? 'ok' : 'error' }));
    } catch (e) {
      setDetails((d) => ({ ...d, [name]: { error: String(e) } }));
      setStatus((s) => ({ ...s, [name]: 'error' }));
    } finally {
      setLoading((s) => ({ ...s, [name]: false }));
    }
  };

  const connect = (name: Provider) => {
    const url = connectPaths[name];
    if (url) window.location.href = url;
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
      {providers.map((p) => (
        <Card key={p} className="border border-gray-200 dark:border-gray-800">
          <CardHeader className="flex items-center justify-between">
            <CardTitle className="text-sm font-semibold capitalize">{p}</CardTitle>
            <Badge variant="outline" className={`text-[11px] ${status[p]==='ok' ? 'border-emerald-600 text-emerald-600' : status[p]==='error' ? 'border-rose-600 text-rose-600' : 'opacity-60'}`}>
              {status[p] ?? 'idle'}
            </Badge>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex gap-2">
              <Button size="sm" onClick={() => testHealth(p)} disabled={loading[p]}>Test</Button>
              <Button size="sm" variant="secondary" onClick={() => connect(p)}>Connect</Button>
            </div>
            {details[p] && (
              <pre className="text-[11px] opacity-70 whitespace-pre-wrap break-words mt-2 max-h-40 overflow-auto">
                {JSON.stringify(details[p], null, 2)}
              </pre>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

