"use client";

import React from "react";

type Report = {
  status: string;
  report: { [k: string]: number };
  timestamp: string;
};

type VerboseItem = {
  id: string;
  provider?: string;
  share?: number;
  banned: boolean;
  missing_caps: boolean;
  short_context: boolean;
  stale: boolean;
  last_updated?: string | null;
};

export default function RouterStatusPage() {
  const [report, setReport] = React.useState<Report | null>(null);
  const [verbose, setVerbose] = React.useState<VerboseItem[]>([]);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const r = await fetch("/api/router/report", { cache: "no-store" });
        const v = await fetch("/api/router/report/verbose", { cache: "no-store" });
        if (!cancelled) {
          const rj = await r.json();
          const vj = await v.json();
          setReport(rj);
          setVerbose(vj.models || []);
        }
      } catch (e: any) {
        if (!cancelled) setError(e?.message || "Failed to load router status");
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-semibold">Router Status</h1>
      {error && <div className="text-red-600">{error}</div>}
      {report && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {Object.entries(report.report).map(([k, v]) => (
            <div key={k} className="rounded border p-3">
              <div className="text-sm text-gray-500">{k.replaceAll("_", " ")}</div>
              <div className="text-xl">{v}</div>
            </div>
          ))}
        </div>
      )}
      <div>
        <h2 className="text-xl font-medium mb-2">Models</h2>
        <div className="overflow-auto border rounded">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left p-2">Model</th>
                <th className="text-left p-2">Provider</th>
                <th className="text-left p-2">Share</th>
                <th className="text-left p-2">Banned</th>
                <th className="text-left p-2">Missing Caps</th>
                <th className="text-left p-2">Short Ctx</th>
                <th className="text-left p-2">Stale</th>
              </tr>
            </thead>
            <tbody>
              {verbose.map((m) => (
                <tr key={m.id} className="border-t">
                  <td className="p-2">{m.id}</td>
                  <td className="p-2">{m.provider || "-"}</td>
                  <td className="p-2">{m.share?.toFixed?.(3) ?? "-"}</td>
                  <td className="p-2">{m.banned ? "yes" : "no"}</td>
                  <td className="p-2">{m.missing_caps ? "yes" : "no"}</td>
                  <td className="p-2">{m.short_context ? "yes" : "no"}</td>
                  <td className="p-2">{m.stale ? "yes" : "no"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

