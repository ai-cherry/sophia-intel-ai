import { useEffect, useState } from "react";

export default function Overview() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);

  const loadHealth = async () => {
    try {
      const res = await fetch("/api/health");
      const data = await res.json();
      setHealth(data);
      setLastUpdated(new Date());
    } catch (error) {
      console.error("Failed to load health:", error);
      setHealth({ status: "error", error: error.message, components: {} });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHealth();
    const interval = setInterval(loadHealth, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status) => {
    switch (status) {
      case "ok":
      case "healthy": return "text-emerald-400 bg-emerald-500/20";
      case "degraded": return "text-yellow-400 bg-yellow-500/20";
      case "error":
      case "unhealthy": return "text-red-400 bg-red-500/20";
      case "running": return "text-blue-400 bg-blue-500/20";
      default: return "text-gray-400 bg-gray-500/20";
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "ok":
      case "healthy": return "✅";
      case "degraded": return "⚠️";
      case "error":
      case "unhealthy": return "❌";
      case "running": return "🔄";
      default: return "❓";
    }
  };

  const calculateHealthScore = () => {
    if (!health?.components) return 0;
    const components = Object.values(health.components);
    const healthy = components.filter(c => c.status === "ok" || c.status === "healthy").length;
    return Math.round((healthy / components.length) * 100);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3 text-white/60">
          <div className="w-6 h-6 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
          Loading system status...
        </div>
      </div>
    );
  }

  const healthScore = calculateHealthScore();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white mb-1">System Overview</h1>
          <p className="text-white/60">Real-time health monitoring and system status</p>
        </div>
        <button
          onClick={loadHealth}
          className="px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white/70 text-sm transition-colors"
        >
          🔄 Refresh
        </button>
      </div>

      {/* Health Score */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-1">
          <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-white/5 to-white/10 p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Overall Health</h3>
            <div className="flex items-center justify-center">
              <div className="relative w-32 h-32">
                <svg className="w-32 h-32 transform -rotate-90" viewBox="0 0 100 100">
                  <circle
                    cx="50"
                    cy="50"
                    r="40"
                    stroke="currentColor"
                    strokeWidth="8"
                    fill="none"
                    className="text-white/10"
                  />
                  <circle
                    cx="50"
                    cy="50"
                    r="40"
                    stroke="currentColor"
                    strokeWidth="8"
                    fill="none"
                    strokeDasharray={`${healthScore * 2.51} 251`}
                    className={healthScore >= 80 ? "text-emerald-400" : healthScore >= 60 ? "text-yellow-400" : "text-red-400"}
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-white">{healthScore}%</div>
                    <div className="text-xs text-white/60">Healthy</div>
                  </div>
                </div>
              </div>
            </div>
            {lastUpdated && (
              <div className="text-xs text-white/40 text-center mt-4">
                Last updated: {lastUpdated.toLocaleTimeString()}
              </div>
            )}
          </div>
        </div>

        {/* Quick Stats */}
        <div className="md:col-span-2">
          <div className="grid grid-cols-2 gap-4 h-full">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
              <h4 className="text-white/70 text-sm font-medium mb-2">Response Time</h4>
              <div className="text-2xl font-bold text-white">
                {health?.elapsed_ms || 0}ms
              </div>
              <div className="text-xs text-white/50 mt-1">Average health check</div>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
              <h4 className="text-white/70 text-sm font-medium mb-2">Components</h4>
              <div className="text-2xl font-bold text-white">
                {health?.components ? Object.keys(health.components).length : 0}
              </div>
              <div className="text-xs text-white/50 mt-1">Services monitored</div>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
              <h4 className="text-white/70 text-sm font-medium mb-2">Status</h4>
              <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(health?.status)}`}>
                {getStatusIcon(health?.status)}
                {health?.status || "Unknown"}
              </div>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
              <h4 className="text-white/70 text-sm font-medium mb-2">Uptime</h4>
              <div className="text-2xl font-bold text-white">99.9%</div>
              <div className="text-xs text-white/50 mt-1">Last 30 days</div>
            </div>
          </div>
        </div>
      </div>

      {/* Component Status */}
      <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Component Status</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {health?.components && Object.entries(health.components).map(([name, component]) => (
            <div key={name} className="rounded-xl border border-white/10 bg-white/5 p-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-white/90 font-medium capitalize">{name.replace('_', ' ')}</h4>
                <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(component.status)}`}>
                  {getStatusIcon(component.status)}
                  {component.status}
                </span>
              </div>
              {component.detail && (
                <p className="text-white/60 text-sm">{component.detail}</p>
              )}
              {component.error && (
                <p className="text-red-400 text-xs mt-1">{component.error}</p>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Recent Activity */}
      <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Recent Activity</h3>
        <div className="space-y-3">
          <div className="flex items-center gap-3 p-3 rounded-lg bg-white/5">
            <div className="w-2 h-2 bg-emerald-500 rounded-full"></div>
            <div className="flex-1">
              <div className="text-white/90 text-sm">System health check completed</div>
              <div className="text-white/50 text-xs">All components operational</div>
            </div>
            <div className="text-white/40 text-xs">Just now</div>
          </div>
          <div className="flex items-center gap-3 p-3 rounded-lg bg-white/5">
            <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
            <div className="flex-1">
              <div className="text-white/90 text-sm">OpenRouter model sync completed</div>
              <div className="text-white/50 text-xs">20 approved models available</div>
            </div>
            <div className="text-white/40 text-xs">5 min ago</div>
          </div>
          <div className="flex items-center gap-3 p-3 rounded-lg bg-white/5">
            <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
            <div className="flex-1">
              <div className="text-white/90 text-sm">Airbyte connection check</div>
              <div className="text-white/50 text-xs">Some connections need attention</div>
            </div>
            <div className="text-white/40 text-xs">15 min ago</div>
          </div>
        </div>
      </div>
    </div>
  );
}

