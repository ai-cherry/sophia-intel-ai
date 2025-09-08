"use client";
import { useEffect, useState } from 'react';
import { API_URL } from '@/lib/config';
import { ApiClient, ApiError } from '@/lib/api/client';

type BridgeHealth = {
  bridge: string;
  core?: { status?: string; agents?: number; teams?: number };
  origins?: string[];
};

const client = new ApiClient(API_URL);

export function useAgnoBridgeHealth(enabled: boolean = true) {
  const [data, setData] = useState<BridgeHealth | null>(null);
  const [loading, setLoading] = useState<boolean>(!!enabled);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    if (!enabled) return;
    const ctrl = new AbortController();
    setLoading(true);
    client
      .get<BridgeHealth>('/health', { signal: ctrl.signal })
      .then(setData)
      .catch((e: ApiError | any) => setError(e?.message || 'failed'))
      .finally(() => setLoading(false));
    return () => ctrl.abort();
  }, [enabled]);

  return { data, loading, error };
}
