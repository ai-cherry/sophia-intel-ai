"use client";
import { useEffect, useState } from "react";
import { fetchJSON } from "@/lib/api";

type TaskItem = { id: string; title: string; assignee?: string; status?: string; source: "asana" | "linear" };

export default function WorkPage() {
  const [items, setItems] = useState<TaskItem[]>([]);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    // Placeholder: call health endpoint to detect availability
    fetchJSON<any>("/health/integrations")
      .then((d) => {
        const integrations = d.integrations || d;
        const asana = integrations?.asana?.status || (integrations?.asana?.ok ? "configured" : "unconfigured");
        const linear = integrations?.linear?.status || (integrations?.linear?.ok ? "configured" : "unconfigured");
        const seed: TaskItem[] = [];
        if (asana) seed.push({ id: "asana-demo-1", title: "Follow up enterprise onboarding", assignee: "Alex", status: "stuck", source: "asana" });
        if (linear) seed.push({ id: "linear-demo-1", title: "Fix priority billing bug", assignee: "Jamie", status: "in_progress", source: "linear" });
        setItems(seed);
      })
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-semibold">Work: Asana & Linear</h1>
      {error && <div className="text-red-600">{error}</div>}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {items.map((t) => (
          <div key={t.id} className="border rounded p-4 bg-white">
            <div className="text-sm text-gray-500 mb-1 uppercase">{t.source}</div>
            <div className="font-medium">{t.title}</div>
            <div className="text-sm text-gray-600 mt-1">Assignee: {t.assignee || "Unassigned"}</div>
            <div className="text-sm mt-1">Status: <span className="px-2 py-0.5 rounded bg-gray-100">{t.status || "unknown"}</span></div>
            <div className="mt-3">
              <button className="text-xs bg-blue-600 text-white px-3 py-1 rounded mr-2">Assign</button>
              <button className="text-xs bg-gray-100 px-3 py-1 rounded mr-2">Comment</button>
              <button className="text-xs bg-green-600 text-white px-3 py-1 rounded">Mark Done</button>
            </div>
          </div>
        ))}
      </div>
      <p className="text-xs text-gray-500">Connect Asana and Linear keys to enable live data and actions.</p>
    </div>
  );
}

