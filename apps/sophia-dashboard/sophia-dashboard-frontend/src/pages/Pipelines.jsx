import { useEffect, useState } from "react";

export default function Pipelines() {
  const [loading, setLoading] = useState(true);
  const [items, setItems] = useState([]);
  const [jobs, setJobs] = useState({});

  const load = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/pipelines/connections");
      const data = await res.json();
      const list = (data?.connections || data?.data || []).map((c) => ({
        connectionId: c.connectionId || c.connection?.connectionId || c?.connectionId,
        name: c.name || c?.source?.name || c?.destination?.name || "connection",
        status: c.status || c?.scheduleData?.basicSchedule?.timeUnit || "unknown",
        latestSyncJobId: c?.latestSyncJobId,
      }));
      setItems(list);
    } catch (error) {
      console.error("Failed to load connections:", error);
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  const syncNow = async (connectionId) => {
    try {
      const res = await fetch("/api/pipelines/sync", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Auth-Token": window.DASHBOARD_API_TOKEN || "",
        },
        body: JSON.stringify({ connectionId }),
      });
      const data = await res.json();
      const jid = data?.job?.id;
      if (jid) pollJob(jid);
    } catch (error) {
      console.error("Failed to trigger sync:", error);
    }
  };

  const pollJob = async (jobId) => {
    try {
      const res = await fetch(`/api/pipelines/jobs/${jobId}`);
      const data = await res.json();
      setJobs((j) => ({ ...j, [jobId]: data }));
      
      // Naive re-poll while running
      const status = data?.job?.job?.status || data?.job?.status || data?.status;
      if (["running", "in_progress", "pending"].includes(String(status || "").toLowerCase())) {
        setTimeout(() => pollJob(jobId), 2500);
      }
    } catch (error) {
      console.error("Failed to poll job:", error);
    }
  };

  useEffect(() => {
    load();
  }, []);

  if (loading) return <div className="text-white/60">Loading connections…</div>;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl text-white font-semibold">Airbyte Pipelines</h2>
        <button
          onClick={load}
          className="px-3 py-1.5 rounded-lg bg-slate-600 hover:bg-slate-700 text-white text-sm"
        >
          Refresh
        </button>
      </div>
      
      {items.length === 0 ? (
        <div className="rounded-2xl border border-white/10 bg-white/5 p-8 text-center">
          <div className="text-white/60 mb-2">No connections found</div>
          <div className="text-white/40 text-sm">
            Configure Airbyte connections to see them here
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {items.map((c) => (
            <div
              key={c.connectionId}
              className="rounded-2xl border border-white/10 bg-white/5 p-4 hover:bg-white/10 transition-colors"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="text-white/90 font-medium">{c.name}</div>
                <span className="text-xs text-white/50">
                  {c.connectionId.slice(0, 8)}…
                </span>
              </div>
              
              <div className="text-sm text-white/70 mb-3">
                Status: <span className="text-white/90">{c.status}</span>
              </div>
              
              <div className="flex gap-2">
                <button
                  onClick={() => syncNow(c.connectionId)}
                  className="px-3 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-white text-xs transition-colors"
                >
                  Sync now
                </button>
                {c.latestSyncJobId && (
                  <button
                    onClick={() => pollJob(c.latestSyncJobId)}
                    className="px-3 py-1.5 rounded-lg bg-slate-600 hover:bg-slate-700 text-white text-xs transition-colors"
                  >
                    Refresh last job
                  </button>
                )}
              </div>
              
              {/* Job status surface */}
              <JobStatus jobs={jobs} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function JobStatus({ jobs }) {
  const ids = Object.keys(jobs);
  if (!ids.length) return null;
  
  return (
    <div className="mt-3 border-t border-white/10 pt-2 text-xs text-white/80 space-y-1">
      {ids.map((k) => {
        const j = jobs[Number(k)];
        const status = j?.job?.job?.status || j?.job?.status || j?.status || "unknown";
        const statusColor = 
          status === "succeeded" ? "text-emerald-400" :
          status === "running" ? "text-blue-400" :
          status === "failed" ? "text-red-400" :
          "text-white/60";
        
        return (
          <div key={k} className="flex items-center justify-between">
            <span>Job {k}</span>
            <span className={statusColor}>{String(status)}</span>
          </div>
        );
      })}
    </div>
  );
}

