"use client";
import { useEffect, useState } from "react";
import { fetchJSON } from "@/lib/api";

type CallItem = { id: string; title: string; when: string; risk?: string; rep?: string };

export default function CallsPage() {
  const [calls, setCalls] = useState<CallItem[]>([]);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    fetchJSON<any>("/api/integrations/gong/calls")
      .then((d) => setCalls(d.items || []))
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-semibold">Calls (Gong)</h1>
      {error && <div className="text-red-600">{error}</div>}
      {calls.length === 0 ? (
        <div className="text-sm text-gray-600">Connect Gong credentials to enable call listings and transcript search.</div>
      ) : (
        <div className="space-y-3">
          {calls.map((c) => (
            <div key={c.id} className="border rounded p-4 bg-white">
              <div className="font-medium">{c.title}</div>
              <div className="text-sm text-gray-600">{c.when} &middot; Rep: {c.rep}</div>
              <div className="text-sm mt-1">Risk: <span className="px-2 py-0.5 rounded bg-yellow-100">{c.risk || "unknown"}</span></div>
              <div className="mt-2">
                <button className="text-xs bg-gray-100 px-3 py-1 rounded mr-2">Preview Transcript</button>
                <button className="text-xs bg-blue-600 text-white px-3 py-1 rounded">Open in Gong</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}