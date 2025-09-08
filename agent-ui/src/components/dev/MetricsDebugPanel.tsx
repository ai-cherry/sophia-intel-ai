"use client";
import { useMemo } from 'react';
import { useUnifiedStore } from '@/lib/state/unifiedStore';

export default function MetricsDebugPanel() {
  const p95 = useUnifiedStore((s) => s.p95LatencyMs);
  const budgets = useUnifiedStore((s) => s.vkBudgetState);

  const show = useMemo(() => {
    const flag = process.env.NEXT_PUBLIC_SHOW_METRICS_DEBUG;
    return flag === '1' || flag === 'true';
  }, []);

  if (!show) return null;

  return (
    <div className="fixed bottom-2 right-2 z-50 max-w-md rounded-md border border-gray-600 bg-black/80 p-3 text-xs text-gray-100 shadow-lg">
      <div className="mb-1 font-semibold">Metrics Debug</div>
      <div className="mb-2">
        <div className="font-medium">Latency p95 (ms)</div>
        <pre className="whitespace-pre-wrap break-words">{JSON.stringify(p95, null, 2)}</pre>
      </div>
      <div>
        <div className="font-medium">VK Budgets</div>
        <pre className="whitespace-pre-wrap break-words">{JSON.stringify(budgets, null, 2)}</pre>
      </div>
    </div>
  );
}

