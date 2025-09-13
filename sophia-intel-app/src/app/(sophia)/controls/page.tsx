"use client";
import React, { useEffect, useState } from "react";
import { getJson, putJson } from "@/src/lib/apiClient";

type Controls = {
  approvals?: { mode?: string };
  dedup?: { order?: string[]; row_keys?: string[]; fuzzy_fields?: string[]; fuzzy_threshold?: number };
  dock?: { enabled?: boolean; allowlist?: string[] };
  rate_strategy?: any;
};

export default function ControlsPage() {
  const [controls, setControls] = useState<Controls | null>(null);
  const [saving, setSaving] = useState(false);
  const [email, setEmail] = useState<string>("");

  useEffect(() => {
    (async () => {
      const c = await getJson<Controls>(`/api/brain/controls`);
      setControls(c);
      const me = (typeof window !== 'undefined' ? localStorage.getItem('sophia_user_email') : null) || "";
      setEmail(me);
    })();
  }, []);

  const save = async () => {
    if (!controls) return;
    setSaving(true);
    const updated = await putJson<Controls, Controls>(`/api/brain/controls`, controls);
    setControls(updated);
    setSaving(false);
  };

  const saveEmail = () => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('sophia_user_email', email);
      alert('Saved local user email for Dock allowlist checks.');
    }
  };

  if (!controls) return <div className="p-6">Loading controls…</div>;

  const dedup = controls.dedup || {};
  const dock = controls.dock || {};
  const approvals = controls.approvals || {};

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-xl font-semibold">Sophia Brain — Central Controls</h1>

      <div className="space-y-2">
        <h2 className="font-medium">Approvals</h2>
        <select
          className="border rounded px-2 py-1"
          value={approvals.mode || "low_risk_auto"}
          onChange={(e) => setControls({ ...controls, approvals: { mode: e.target.value } })}
        >
          <option value="always">Always require</option>
          <option value="low_risk_auto">Low-risk auto, risky require approval</option>
          <option value="dev_auto_prod_approval">Dev auto, Prod approval</option>
        </select>
      </div>

      <div className="space-y-2">
        <h2 className="font-medium">Deduplication</h2>
        <div className="text-sm">Order (comma separated):</div>
        <input
          className="border rounded px-2 py-1 w-full"
          value={(dedup.order || ["content_hash","row_keys","fuzzy"]).join(",")}
          onChange={(e) => setControls({ ...controls, dedup: { ...dedup, order: e.target.value.split(',').map(s=>s.trim()) } })}
        />
        <div className="text-sm">Row keys (comma separated):</div>
        <input
          className="border rounded px-2 py-1 w-full"
          value={(dedup.row_keys || ["email","external_id"]).join(",")}
          onChange={(e) => setControls({ ...controls, dedup: { ...dedup, row_keys: e.target.value.split(',').map(s=>s.trim()) } })}
        />
        <div className="text-sm">Fuzzy fields (comma separated):</div>
        <input
          className="border rounded px-2 py-1 w-full"
          value={(dedup.fuzzy_fields || ["name","title"]).join(",")}
          onChange={(e) => setControls({ ...controls, dedup: { ...dedup, fuzzy_fields: e.target.value.split(',').map(s=>s.trim()) } })}
        />
        <div className="text-sm">Fuzzy threshold:</div>
        <input
          type="number" step="0.01"
          className="border rounded px-2 py-1 w-32"
          value={dedup.fuzzy_threshold ?? 0.88}
          onChange={(e) => setControls({ ...controls, dedup: { ...dedup, fuzzy_threshold: parseFloat(e.target.value) } })}
        />
      </div>

      <div className="space-y-2">
        <h2 className="font-medium">Dock</h2>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={!!dock.enabled}
            onChange={(e) => setControls({ ...controls, dock: { ...dock, enabled: e.target.checked } })}
          />
          Enable Dock (allowlist below)
        </label>
        <div className="text-sm">Allowlist (comma separated emails):</div>
        <input
          className="border rounded px-2 py-1 w-full"
          value={(dock.allowlist || []).join(",")}
          onChange={(e) => setControls({ ...controls, dock: { ...dock, allowlist: e.target.value.split(',').map(s=>s.trim()) } })}
        />
        <div className="text-sm">Local user email (for allowlist check):</div>
        <div className="flex gap-2">
          <input className="border rounded px-2 py-1" value={email} onChange={(e)=>setEmail(e.target.value)} />
          <button className="px-3 py-1 bg-neutral-200 rounded" onClick={saveEmail}>Save Local Email</button>
        </div>
      </div>

      <div className="flex gap-2">
        <button className="px-3 py-1 bg-blue-600 text-white rounded" onClick={save} disabled={saving}>
          {saving ? 'Saving…' : 'Save Controls'}
        </button>
      </div>
    </div>
  );
}

