"use client";
import { useEffect, useState } from "react";
import { fetchJSON } from "@/lib/api";
import AgnoBridgeStatus from "@/components/sophia/AgnoBridgeStatus";

type IntegrationData = {
  integrations?: Record<string, any>;
  overall?: string;
  healthy_count?: number;
  total_integrations?: number;
};

type MetricCard = {
  label: string;
  value: string | number;
  change?: string;
  trend?: "up" | "down" | "neutral";
};

export default function Dashboard() {
  const [integrations, setIntegrations] = useState<IntegrationData | null>(null);
  const [metrics, setMetrics] = useState<MetricCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    Promise.all([
      fetchJSON<IntegrationData>("/health/integrations"),
      // Fetch mock metrics for now
      Promise.resolve([
        { label: "Active Deals", value: "42", change: "+12%", trend: "up" as const },
        { label: "Revenue Pipeline", value: "$2.4M", change: "+8%", trend: "up" as const },
        { label: "Conversion Rate", value: "24%", change: "-2%", trend: "down" as const },
        { label: "Avg Deal Size", value: "$57K", change: "+15%", trend: "up" as const },
        { label: "Team Calls Today", value: "18", change: "+3", trend: "up" as const },
        { label: "Tasks Completed", value: "127", change: "+22%", trend: "up" as const },
      ])
    ])
      .then(([intData, metricsData]) => {
        setIntegrations(intData);
        setMetrics(metricsData);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "healthy": return "bg-green-100 text-green-800 border-green-200";
      case "configured": return "bg-amber-100 text-amber-800 border-amber-200";
      case "unconfigured": return "bg-gray-100 text-gray-600 border-gray-200";
      default: return "bg-red-100 text-red-800 border-red-200";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "healthy": return "✅";
      case "configured": return "⚙️";
      case "unconfigured": return "⚪";
      default: return "❌";
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Business Intelligence Dashboard</h1>
          <p className="text-gray-500 mt-1">Real-time insights across your revenue operations</p>
        </div>
        <div className="flex gap-2 items-center">
          {/* Optional Agno bridge health indicator */}
          <AgnoBridgeStatus />
          <button className="px-4 py-2 bg-white border rounded-lg hover:bg-gray-50">
            📊 Export Report
          </button>
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            🔄 Refresh All
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          ⚠️ {error}
        </div>
      )}

      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {metrics.map((metric, idx) => (
          <div key={idx} className="bg-white rounded-lg border p-4">
            <p className="text-sm text-gray-600">{metric.label}</p>
            <p className="text-2xl font-bold mt-1">{metric.value}</p>
            {metric.change && (
              <p className={`text-sm mt-2 flex items-center gap-1 ${
                metric.trend === "up" ? "text-green-600" : metric.trend === "down" ? "text-red-600" : "text-gray-600"
              }`}>
                <span>{metric.trend === "up" ? "↑" : metric.trend === "down" ? "↓" : "→"}</span>
                {metric.change}
              </p>
            )}
          </div>
        ))}
      </div>

      {/* Integration Status */}
      <div className="bg-white rounded-lg border">
        <div className="p-4 border-b">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            🔗 Integration Status
            {integrations?.overall && (
              <span className={`text-sm px-2 py-1 rounded-full ${
                integrations.overall === "healthy" ? "bg-green-100 text-green-700" :
                integrations.overall === "degraded" ? "bg-amber-100 text-amber-700" :
                "bg-red-100 text-red-700"
              }`}>
                {integrations.healthy_count}/{integrations.total_integrations} Active
              </span>
            )}
          </h2>
        </div>
        <div className="p-4">
          {loading ? (
            <div className="text-center py-8 text-gray-500">Loading integrations...</div>
          ) : integrations?.integrations ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {Object.entries(integrations.integrations).map(([name, data]: [string, any]) => (
                <div
                  key={name}
                  className={`border rounded-lg p-3 ${getStatusColor(data.status || "unknown")}`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium capitalize text-sm">{name}</span>
                    <span className="text-lg">{getStatusIcon(data.status || "unknown")}</span>
                  </div>
                  {data.error && (
                    <p className="text-xs mt-1 opacity-75">{data.error.slice(0, 50)}</p>
                  )}
                  {data.details && Object.keys(data.details).length > 0 && (
                    <p className="text-xs mt-1 font-medium">
                      {data.details.user || data.details.team || "Connected"}
                    </p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">No integration data available</div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-lg p-4">
          <h3 className="font-semibold mb-2">📞 Recent Gong Calls</h3>
          <p className="text-sm opacity-90 mb-3">3 new recordings to review</p>
          <button className="bg-white/20 backdrop-blur px-3 py-1 rounded text-sm hover:bg-white/30">
            View Calls →
          </button>
        </div>
        <div className="bg-gradient-to-br from-green-500 to-green-600 text-white rounded-lg p-4">
          <h3 className="font-semibold mb-2">🎯 Salesforce Opps</h3>
          <p className="text-sm opacity-90 mb-3">5 deals closing this week</p>
          <button className="bg-white/20 backdrop-blur px-3 py-1 rounded text-sm hover:bg-white/30">
            Review Pipeline →
          </button>
        </div>
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 text-white rounded-lg p-4">
          <h3 className="font-semibold mb-2">📊 Looker Reports</h3>
          <p className="text-sm opacity-90 mb-3">Weekly metrics ready</p>
          <button className="bg-white/20 backdrop-blur px-3 py-1 rounded text-sm hover:bg-white/30">
            View Analytics →
          </button>
        </div>
      </div>
    </div>
  );
}
