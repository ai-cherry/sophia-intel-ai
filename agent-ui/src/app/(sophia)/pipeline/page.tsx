"use client";
import { useState, useEffect } from "react";
import { fetchJSON } from "@/lib/api";

type Deal = {
  id: string;
  name: string;
  account: string;
  value: number;
  stage: string;
  probability: number;
  closeDate: string;
  owner: string;
  lastActivity: string;
  riskLevel: "low" | "medium" | "high";
  nextStep?: string;
};

const STAGES = [
  { name: "Prospecting", color: "bg-gray-500" },
  { name: "Qualification", color: "bg-blue-500" },
  { name: "Discovery", color: "bg-indigo-500" },
  { name: "Proposal", color: "bg-purple-500" },
  { name: "Negotiation", color: "bg-orange-500" },
  { name: "Closed Won", color: "bg-green-500" },
  { name: "Closed Lost", color: "bg-red-500" },
];

// Mock data generator
function generateMockDeals(): Deal[] {
  const accounts = ["Acme Corp", "TechCo", "FinanceApp", "DataSoft", "CloudNet"];
  const owners = ["Sarah Chen", "Mike Roberts", "Alex Kim", "Jordan Lee"];
  
  return Array.from({ length: 15 }, (_, i) => ({
    id: `deal-${i + 1}`,
    name: `Q4 Enterprise Deal ${i + 1}`,
    account: accounts[Math.floor(Math.random() * accounts.length)],
    value: Math.floor(Math.random() * 200000) + 50000,
    stage: STAGES[Math.floor(Math.random() * 5)].name,
    probability: [20, 40, 60, 80, 90][Math.floor(Math.random() * 5)],
    closeDate: new Date(Date.now() + Math.random() * 60 * 24 * 60 * 60 * 1000).toISOString(),
    owner: owners[Math.floor(Math.random() * owners.length)],
    lastActivity: `${Math.floor(Math.random() * 7) + 1} days ago`,
    riskLevel: ["low", "medium", "high"][Math.floor(Math.random() * 3)] as "low" | "medium" | "high",
    nextStep: ["Schedule demo", "Send proposal", "Negotiate terms", "Final review"][Math.floor(Math.random() * 4)]
  }));
}

export default function PipelinePage() {
  const [deals, setDeals] = useState<Deal[]>([]);
  const [selectedStage, setSelectedStage] = useState<string | null>(null);
  const [selectedDeal, setSelectedDeal] = useState<Deal | null>(null);
  const [viewMode, setViewMode] = useState<"kanban" | "list">("kanban");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setDeals(generateMockDeals());
      setLoading(false);
    }, 500);
  }, []);

  const dealsByStage = STAGES.reduce((acc, stage) => {
    acc[stage.name] = deals.filter(d => d.stage === stage.name);
    return acc;
  }, {} as Record<string, Deal[]>);

  const totalPipeline = deals.reduce((sum, d) => sum + d.value, 0);
  const weightedPipeline = deals.reduce((sum, d) => sum + (d.value * d.probability / 100), 0);

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case "low": return "text-green-600 bg-green-50";
      case "medium": return "text-amber-600 bg-amber-50";
      case "high": return "text-red-600 bg-red-50";
      default: return "text-gray-600 bg-gray-50";
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Sales Pipeline</h1>
          <p className="text-gray-500 mt-1">Track and manage your active deals</p>
        </div>
        <div className="flex gap-2">
          <select className="px-4 py-2 border rounded-lg bg-white">
            <option>All Teams</option>
            <option>Enterprise</option>
            <option>Mid-Market</option>
            <option>SMB</option>
          </select>
          <div className="flex bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setViewMode("kanban")}
              className={`px-3 py-1 rounded ${viewMode === "kanban" ? "bg-white shadow-sm" : ""}`}
            >
              Kanban
            </button>
            <button
              onClick={() => setViewMode("list")}
              className={`px-3 py-1 rounded ${viewMode === "list" ? "bg-white shadow-sm" : ""}`}
            >
              List
            </button>
          </div>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border p-4">
          <p className="text-sm text-gray-600">Total Pipeline</p>
          <p className="text-2xl font-bold">${(totalPipeline / 1000000).toFixed(2)}M</p>
          <p className="text-sm text-green-600 mt-1">+15% vs last quarter</p>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <p className="text-sm text-gray-600">Weighted Pipeline</p>
          <p className="text-2xl font-bold">${(weightedPipeline / 1000000).toFixed(2)}M</p>
          <p className="text-sm text-gray-500 mt-1">Based on probability</p>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <p className="text-sm text-gray-600">Deals at Risk</p>
          <p className="text-2xl font-bold">{deals.filter(d => d.riskLevel === "high").length}</p>
          <p className="text-sm text-red-600 mt-1">Need immediate attention</p>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <p className="text-sm text-gray-600">Avg Deal Size</p>
          <p className="text-2xl font-bold">${Math.floor(totalPipeline / deals.length / 1000)}K</p>
          <p className="text-sm text-blue-600 mt-1">↑ Trending up</p>
        </div>
      </div>

      {/* Pipeline View */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="text-gray-500">Loading pipeline...</div>
        </div>
      ) : viewMode === "kanban" ? (
        <div className="flex gap-4 overflow-x-auto pb-4">
          {STAGES.slice(0, 5).map((stage) => (
            <div key={stage.name} className="flex-none w-80">
              <div className="bg-white rounded-lg border">
                <div className={`p-3 border-b ${stage.color} bg-opacity-10`}>
                  <div className="flex justify-between items-center">
                    <h3 className="font-medium">{stage.name}</h3>
                    <span className="text-sm text-gray-600">
                      {dealsByStage[stage.name]?.length || 0} deals
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">
                    ${((dealsByStage[stage.name] || []).reduce((sum, d) => sum + d.value, 0) / 1000000).toFixed(2)}M
                  </p>
                </div>
                <div className="p-2 space-y-2 max-h-96 overflow-y-auto">
                  {(dealsByStage[stage.name] || []).map((deal) => (
                    <div
                      key={deal.id}
                      onClick={() => setSelectedDeal(deal)}
                      className="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer"
                    >
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <p className="font-medium text-sm">{deal.account}</p>
                          <p className="text-xs text-gray-600 mt-0.5">{deal.name}</p>
                        </div>
                        <span className={`text-xs px-2 py-0.5 rounded ${getRiskColor(deal.riskLevel)}`}>
                          {deal.riskLevel}
                        </span>
                      </div>
                      <div className="mt-2 flex justify-between items-center">
                        <p className="text-sm font-semibold">${(deal.value / 1000).toFixed(0)}K</p>
                        <p className="text-xs text-gray-500">{deal.probability}%</p>
                      </div>
                      <div className="mt-2 text-xs text-gray-500">
                        <p>Owner: {deal.owner}</p>
                        <p>Close: {new Date(deal.closeDate).toLocaleDateString()}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-lg border">
          <table className="w-full">
            <thead className="border-b bg-gray-50">
              <tr>
                <th className="text-left px-4 py-3 text-sm font-medium">Account</th>
                <th className="text-left px-4 py-3 text-sm font-medium">Deal</th>
                <th className="text-left px-4 py-3 text-sm font-medium">Stage</th>
                <th className="text-left px-4 py-3 text-sm font-medium">Value</th>
                <th className="text-left px-4 py-3 text-sm font-medium">Probability</th>
                <th className="text-left px-4 py-3 text-sm font-medium">Close Date</th>
                <th className="text-left px-4 py-3 text-sm font-medium">Owner</th>
                <th className="text-left px-4 py-3 text-sm font-medium">Risk</th>
              </tr>
            </thead>
            <tbody>
              {deals.map((deal, idx) => (
                <tr
                  key={deal.id}
                  onClick={() => setSelectedDeal(deal)}
                  className={`border-b hover:bg-gray-50 cursor-pointer ${idx % 2 === 0 ? "bg-white" : "bg-gray-50/50"}`}
                >
                  <td className="px-4 py-3 text-sm font-medium">{deal.account}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{deal.name}</td>
                  <td className="px-4 py-3 text-sm">
                    <span className={`px-2 py-1 rounded text-xs text-white ${
                      STAGES.find(s => s.name === deal.stage)?.color || "bg-gray-500"
                    }`}>
                      {deal.stage}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm font-semibold">${(deal.value / 1000).toFixed(0)}K</td>
                  <td className="px-4 py-3 text-sm">{deal.probability}%</td>
                  <td className="px-4 py-3 text-sm">{new Date(deal.closeDate).toLocaleDateString()}</td>
                  <td className="px-4 py-3 text-sm">{deal.owner}</td>
                  <td className="px-4 py-3 text-sm">
                    <span className={`px-2 py-0.5 rounded text-xs ${getRiskColor(deal.riskLevel)}`}>
                      {deal.riskLevel}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Deal Details Modal */}
      {selectedDeal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setSelectedDeal(null)}>
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between items-start mb-4">
              <div>
                <h2 className="text-xl font-bold">{selectedDeal.account}</h2>
                <p className="text-gray-600">{selectedDeal.name}</p>
              </div>
              <button
                onClick={() => setSelectedDeal(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-6">
              <div>
                <p className="text-sm text-gray-600">Deal Value</p>
                <p className="text-2xl font-bold">${(selectedDeal.value / 1000).toFixed(0)}K</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Weighted Value</p>
                <p className="text-2xl font-bold">
                  ${(selectedDeal.value * selectedDeal.probability / 100 / 1000).toFixed(0)}K
                </p>
              </div>
            </div>

            <div className="space-y-3">
              <div>
                <p className="text-sm text-gray-600">Stage</p>
                <p className="font-medium">{selectedDeal.stage} ({selectedDeal.probability}%)</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Expected Close Date</p>
                <p className="font-medium">{new Date(selectedDeal.closeDate).toLocaleDateString()}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Owner</p>
                <p className="font-medium">{selectedDeal.owner}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Next Step</p>
                <p className="font-medium">{selectedDeal.nextStep}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Risk Level</p>
                <span className={`px-2 py-1 rounded text-sm ${getRiskColor(selectedDeal.riskLevel)}`}>
                  {selectedDeal.riskLevel}
                </span>
              </div>
            </div>

            <div className="mt-6 flex gap-2">
              <button className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                Update Deal
              </button>
              <button className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50">
                View in CRM
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}