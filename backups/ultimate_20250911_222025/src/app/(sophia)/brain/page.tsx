"use client";
import React, { useState } from "react";
import { API_URL } from "@/lib/config";

export default function BrainTrainingPage() {
  const [file, setFile] = useState<File | null>(null);
  const [context, setContext] = useState("payready_business");
  const [status, setStatus] = useState<string>("");
  const [count, setCount] = useState<number>(0);
  const [loading, setLoading] = useState(false);

  const onUpload = async () => {
    if (!file) return;
    setLoading(true);
    setStatus("");
    setCount(0);
    try {
      const form = new FormData();
      form.append("file", file);
      form.append("context", context);
      const resp = await fetch(`${API_URL}/api/brain/ingest`, {
        method: "POST",
        body: form,
      });
      if (!resp.ok) {
        const txt = await resp.text();
        setStatus(`Error: ${txt}`);
      } else {
        const data = await resp.json();
        setCount(data?.chunks || 0);
        setStatus("Ingestion complete");
      }
    } catch (e: any) {
      setStatus(`Upload failed: ${e?.message || e}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Brain Training</h1>
        <p className="text-sm text-gray-500">Ingest documents to Sophia memory for PayReady context.</p>
      </div>

      <div className="space-y-3 bg-white border rounded-lg p-4">
        <div className="flex items-center gap-3">
          <input
            type="file"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="block text-sm"
            aria-label="Select a file to ingest"
          />
          <select
            value={context}
            onChange={(e) => setContext(e.target.value)}
            className="text-sm border rounded px-2 py-1"
            aria-label="Select ingestion context"
          >
            <option value="payready_business">PayReady Business</option>
            <option value="sales_intelligence">Sales Intelligence</option>
            <option value="operational_docs">Operational Docs</option>
          </select>
          <button
            disabled={!file || loading}
            onClick={onUpload}
            className="px-4 py-2 bg-blue-600 text-white text-sm rounded disabled:opacity-50"
          >
            {loading ? "Uploading..." : "Ingest"}
          </button>
        </div>
        {status && (
          <p className="text-sm">
            {status} {count ? `(${count} chunks)` : ""}
          </p>
        )}
      </div>

      <div className="text-sm text-gray-500">
        After ingestion, ask Chat about the document. Sophia will include relevant context from memory automatically when enabled.
      </div>
    </div>
  );
}

