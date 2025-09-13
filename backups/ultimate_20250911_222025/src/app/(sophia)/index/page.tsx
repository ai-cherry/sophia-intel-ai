"use client";

import React from "react";

export default function IndexStatusPage() {
  const [status, setStatus] = React.useState<any>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [refreshing, setRefreshing] = React.useState(false);

  const load = React.useCallback(async () => {
    try {
      const r = await fetch("/api/index/status", { cache: "no-store" });
      const j = await r.json();
      setStatus(j);
    } catch (e: any) {
      setError(e?.message || "Failed to load index status");
    }
  }, []);

  React.useEffect(() => {
    load();
  }, [load]);

  const doRefresh = async () => {
    setRefreshing(true);
    try {
      const r = await fetch("/api/index/refresh", { method: "POST" });
      const j = await r.json();
      setStatus(j);
    } catch (e: any) {
      setError(e?.message || "Failed to refresh index");
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-semibold">Repository Index Status</h1>
      {error && <div className="text-red-600">{error}</div>}
      {status && status.enabled === false && (
        <div className="text-yellow-700">Indexing is disabled (INDEX_ENABLED=false).</div>
      )}
      {status && status.enabled !== false && (
        <div className="space-y-2">
          <div>Repo: {status.repo}</div>
          <div>Files: {status.files}</div>
          <div>Symbols: {status.symbols}</div>
          <div>Deps: {status.deps}</div>
          <button
            className="px-3 py-1 border rounded"
            onClick={doRefresh}
            disabled={refreshing}
          >
            {refreshing ? "Refreshing..." : "Refresh Index"}
          </button>
        </div>
      )}
    </div>
  );
}

