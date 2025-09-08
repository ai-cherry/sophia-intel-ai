"use client";
import { useState, useEffect } from "react";
import { fetchJSON } from "@/lib/api";

type Integration = {
  id: string;
  name: string;
  icon: string;
  status: "healthy" | "configured" | "unconfigured" | "error";
  description: string;
  lastSync?: string;
  dataPoints?: number;
  config?: Record<string, any>;
};

const INTEGRATIONS: Integration[] = [
  {
    id: "gong",
    name: "Gong",
    icon: "📞",
    status: "unconfigured",
    description: "Conversation intelligence and call analytics",
    config: { required: ["GONG_ACCESS_KEY", "GONG_CLIENT_SECRET"] }
  },
  {
    id: "salesforce",
    name: "Salesforce",
    icon: "☁️",
    status: "unconfigured",
    description: "CRM and sales pipeline management",
    config: { required: ["SALESFORCE_CLIENT_ID", "SALESFORCE_CLIENT_SECRET"] }
  },
  {
    id: "hubspot",
    name: "HubSpot",
    icon: "🎯",
    status: "unconfigured",
    description: "Marketing automation and lead tracking",
    config: { required: ["HUBSPOT_API_KEY"] }
  },
  {
    id: "looker",
    name: "Looker",
    icon: "📊",
    status: "unconfigured",
    description: "Business intelligence and analytics",
    config: { required: ["LOOKERSDK_BASE_URL", "LOOKERSDK_CLIENT_ID"] }
  },
  {
    id: "slack",
    name: "Slack",
    icon: "💬",
    status: "unconfigured",
    description: "Team communication and notifications",
    config: { required: ["SLACK_BOT_TOKEN"] }
  },
  {
    id: "asana",
    name: "Asana",
    icon: "✅",
    status: "healthy",
    description: "Project management and task tracking",
    lastSync: "2 minutes ago",
    dataPoints: 127,
    config: { required: ["ASANA_ACCESS_TOKEN"] }
  },
  {
    id: "linear",
    name: "Linear",
    icon: "🔄",
    status: "unconfigured",
    description: "Issue tracking and development workflow",
    config: { required: ["LINEAR_API_KEY"] }
  },
  {
    id: "airtable",
    name: "Airtable",
    icon: "📋",
    status: "unconfigured",
    description: "Database and spreadsheet hybrid",
    config: { required: ["AIRTABLE_API_KEY", "AIRTABLE_BASE_ID"] }
  }
];

export default function IntegrationsPage() {
  const [integrations, setIntegrations] = useState(INTEGRATIONS);
  const [selectedIntegration, setSelectedIntegration] = useState<Integration | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Fetch actual integration status
    fetchJSON<any>("/health/integrations")
      .then((data) => {
        if (data?.integrations) {
          setIntegrations(prev => prev.map(int => ({
            ...int,
            status: data.integrations[int.id]?.status || int.status,
            lastSync: data.integrations[int.id]?.last_check ? 
              new Date(data.integrations[int.id].last_check).toLocaleString() : 
              int.lastSync
          })));
        }
      })
      .catch(console.error);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "healthy": return "bg-green-100 text-green-700 border-green-200";
      case "configured": return "bg-amber-100 text-amber-700 border-amber-200";
      case "error": return "bg-red-100 text-red-700 border-red-200";
      default: return "bg-gray-100 text-gray-600 border-gray-200";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "healthy": return "✅";
      case "configured": return "⚙️";
      case "error": return "❌";
      default: return "⚪";
    }
  };

  const handleConnect = async (integration: Integration) => {
    setLoading(true);
    // Simulate connection process
    setTimeout(() => {
      setLoading(false);
      setSelectedIntegration(integration);
    }, 1000);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Integrations</h1>
          <p className="text-gray-500 mt-1">Connect and manage your business tools</p>
        </div>
        <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          🔄 Sync All
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border p-4">
          <p className="text-sm text-gray-600">Connected</p>
          <p className="text-2xl font-bold">
            {integrations.filter(i => i.status === "healthy").length}/{integrations.length}
          </p>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <p className="text-sm text-gray-600">Data Points</p>
          <p className="text-2xl font-bold">12.4K</p>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <p className="text-sm text-gray-600">Last Sync</p>
          <p className="text-2xl font-bold">2m ago</p>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <p className="text-sm text-gray-600">API Calls Today</p>
          <p className="text-2xl font-bold">1,847</p>
        </div>
      </div>

      {/* Integrations Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {integrations.map((integration) => (
          <div
            key={integration.id}
            className="bg-white rounded-lg border hover:shadow-lg transition-shadow"
          >
            <div className="p-4">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <span className="text-3xl">{integration.icon}</span>
                  <div>
                    <h3 className="font-semibold">{integration.name}</h3>
                    <span className={`text-xs px-2 py-0.5 rounded border ${getStatusColor(integration.status)}`}>
                      {getStatusIcon(integration.status)} {integration.status}
                    </span>
                  </div>
                </div>
              </div>

              <p className="text-sm text-gray-600 mb-4">{integration.description}</p>

              {integration.status === "healthy" && (
                <div className="space-y-1 mb-4">
                  {integration.lastSync && (
                    <p className="text-xs text-gray-500">Last sync: {integration.lastSync}</p>
                  )}
                  {integration.dataPoints && (
                    <p className="text-xs text-gray-500">Data points: {integration.dataPoints.toLocaleString()}</p>
                  )}
                </div>
              )}

              <div className="flex gap-2">
                {integration.status === "healthy" ? (
                  <>
                    <button className="flex-1 px-3 py-1.5 bg-gray-100 text-sm rounded hover:bg-gray-200">
                      Configure
                    </button>
                    <button className="flex-1 px-3 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700">
                      Sync Now
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => handleConnect(integration)}
                    disabled={loading}
                    className="w-full px-3 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50"
                  >
                    {loading ? "Connecting..." : "Connect"}
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Connection Modal */}
      {selectedIntegration && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setSelectedIntegration(null)}>
          <div className="bg-white rounded-lg p-6 max-w-md w-full" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center gap-3 mb-4">
              <span className="text-3xl">{selectedIntegration.icon}</span>
              <h2 className="text-xl font-bold">Connect {selectedIntegration.name}</h2>
            </div>

            <p className="text-gray-600 mb-4">{selectedIntegration.description}</p>

            <div className="space-y-3 mb-6">
              <p className="text-sm font-medium">Required Configuration:</p>
              {selectedIntegration.config?.required.map((field: string) => (
                <div key={field}>
                  <label className="text-sm text-gray-600">{field}</label>
                  <input
                    type="password"
                    placeholder="Enter value..."
                    className="w-full mt-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              ))}
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => setSelectedIntegration(null)}
                className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                Connect
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}