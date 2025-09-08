"use client";
import { useEffect, useMemo, useRef, useState, useCallback } from 'react';
import { ApiClient, ApiError } from '@/lib/api/client';
import { API_URL } from '@/lib/config';

type Options = {
  category?: string;
  enabled?: boolean;
};

const client = new ApiClient(API_URL, (category, ms) => {
  try { require('@/lib/state/unifiedStore'); } catch {}
  // Safe, hookless update via Zustand's getState API
  try {
    const { useUnifiedStore } = require('@/lib/state/unifiedStore');
    useUnifiedStore.getState().updateLatency(category, ms);
  } catch {}
});

export function useDashboardData<T>(path: string, deps: unknown[] = [], opts: Options = {}) {
  const { category = 'api.dashboard', enabled = true } = opts;
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState<boolean>(!!enabled);
  const [error, setError] = useState<string>("");
  const ctrlRef = useRef<AbortController | null>(null);

  const refetch = useCallback(() => {
    if (!enabled) return;
    ctrlRef.current?.abort();
    const ctrl = new AbortController();
    ctrlRef.current = ctrl;
    setLoading(true);
    setError("");
    client
      .get<T>(path, { signal: ctrl.signal, category })
      .then(setData)
      .catch((e: ApiError | any) => {
        if (e && e.name === 'AbortError') return;
        setError(e?.message || 'request failed');
      })
      .finally(() => setLoading(false));
  }, [path, category, enabled]);

  // Initial + dep-triggered fetch
  useEffect(() => {
    refetch();
    return () => ctrlRef.current?.abort();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return useMemo(() => ({ data, loading, error, refetch }), [data, loading, error, refetch]);
}

