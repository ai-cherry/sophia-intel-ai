import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api/working_client';

export function useRealData<T = any>(endpoint: string, pollInterval = 5000) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    const fetchData = async () => {
      try {
        setLoading(true);
        const result = await apiClient.fetch(endpoint);
        if (!active) return;
        setData(result);
        setError(null);
      } catch (err: unknown) {
        if (!active) return;
        setError(err?.message || 'Request failed');
      } finally {
        if (active) setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, pollInterval);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [endpoint, pollInterval]);

  return { data, loading, error } as const;
}
