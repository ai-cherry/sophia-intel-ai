"use client";

import { useEffect, useState } from "react";
import ProjectManagementDashboard from '@/components/ProjectManagementDashboard';
import { getJson } from '@/lib/apiClient';

type Project = {
  name?: string;
  owner?: string;
  status?: string;
  risk?: string;
  due_date?: string;
  is_overdue?: boolean;
  source: string;
};

// Toggle between enhanced and basic dashboard
const USE_ENHANCED_DASHBOARD = true;

export default function ProjectsDashboard() {
  // If enhanced dashboard is enabled, use the new component
  if (USE_ENHANCED_DASHBOARD) {
    return <ProjectManagementDashboard />;
  }
  
  // Otherwise, use the existing basic dashboard
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [overview, setOverview] = useState<any>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getJson<any>("/api/projects/overview", { cache: 'no-store' });
        setOverview(data);
      } catch (e: any) {
        setError(e?.message || "Failed to load");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  return (
    <div className="p-6">
      <h2 className="text-2xl font-semibold mb-2">Athena – Project Management</h2>
      <p className="text-sm text-gray-500 mb-6">Unified view from Asana, Linear, Slack, and Airtable</p>

      {loading && <div className="text-sm">Loading…</div>}
      {error && (
        <div className="p-3 rounded bg-red-50 text-red-700 text-sm border border-red-200">{error}</div>
      )}

      {overview && (
        <div className="grid md:grid-cols-3 gap-6">
          <div className="md:col-span-2 space-y-4">
            <Section title="Major Projects">
              <div className="grid gap-3">
                {(overview.major_projects as Project[] | undefined)?.slice(0, 20)?.map((p, idx) => (
                  <div key={idx} className="rounded border p-3 bg-white dark:bg-gray-900 flex items-center justify-between">
                    <div>
                      <div className="font-medium">{p.name || "Untitled"}</div>
                      <div className="text-xs text-gray-500">
                        {p.owner ? `Owner: ${p.owner}` : "No owner"} • Source: {p.source}
                      </div>
                    </div>
                    <div className="text-right text-sm">
                      <span className={`px-2 py-1 rounded ${p.is_overdue || p.risk === 'high' || p.risk === 'critical' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
                        {p.is_overdue ? "Overdue" : p.risk ? p.risk : (p.status || "Active")}
                      </span>
                    </div>
                  </div>
                ))}
                {!overview.major_projects?.length && (
                  <div className="text-sm text-gray-500">No projects found or integrations not configured.</div>
                )}
              </div>
            </Section>

            <Section title="Blockages">
              <ul className="list-disc pl-5 space-y-2">
                {overview.blockages?.slice(0, 30)?.map((b: any, i: number) => (
                  <li key={i} className="text-sm">
                    <span className="font-medium">{b.title || b.issue || "Blocker"}</span>
                    {b.assignee && <span className="text-gray-500"> • {b.assignee}</span>}
                    <span className="text-gray-500"> • {b.source}</span>
                  </li>
                ))}
                {!overview.blockages?.length && (
                  <li className="text-sm text-gray-500">No blockers detected.</li>
                )}
              </ul>
            </Section>
          </div>

          <div className="space-y-4">
            <Section title="Communication Issues">
              <ul className="space-y-2 text-sm">
                {overview.communication_issues?.slice(0, 20)?.map((c: any, i: number) => (
                  <li key={i} className="rounded border p-2 bg-white dark:bg-gray-900">
                    <div className="font-medium">{c.pattern || "Issue"}</div>
                    <div className="text-gray-500">{c.impact} • {c.channel} • {c.source}</div>
                  </li>
                ))}
                {!overview.communication_issues?.length && (
                  <li className="text-gray-500">No communication issues detected.</li>
                )}
              </ul>
            </Section>

            <Section title="Notes">
              <ul className="list-disc pl-5 text-sm space-y-1">
                {overview.notes?.map((n: string, i: number) => (
                  <li key={i}>{n}</li>
                ))}
              </ul>
            </Section>

            <Section title="Sources">
              <div className="text-xs text-gray-500 space-y-1">
                {Object.entries(overview.sources || {}).map(([k, v]: any) => (
                  <div key={k}>{k}: {(v as any).configured ? "configured" : "missing"}</div>
                ))}
              </div>
            </Section>
          </div>
        </div>
      )}
    </div>
  );
}

function Section({ title, children }: { title: string; children: any }) {
  return (
    <section>
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      {children}
    </section>
  );
}
