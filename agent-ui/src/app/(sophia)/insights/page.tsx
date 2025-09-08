"use client";
import { useState } from "react";

type Insight = {
  id: string;
  type: "opportunity" | "risk" | "trend" | "action";
  priority: "high" | "medium" | "low";
  title: string;
  description: string;
  source: string;
  timestamp: string;
  impact?: string;
  recommendation?: string;
  metrics?: Record<string, any>;
};

const SAMPLE_INSIGHTS: Insight[] = [
  {
    id: "1",
    type: "opportunity",
    priority: "high",
    title: "Acme Corp showing 85% buying signals",
    description: "Based on recent Gong calls, Acme Corp has mentioned budget approval 3 times and asked about implementation timeline.",
    source: "Gong Analytics",
    timestamp: "2 hours ago",
    impact: "Potential $250K deal acceleration",
    recommendation: "Schedule executive meeting this week to close the deal",
    metrics: { "Buying Signals": 85, "Engagement Score": 92 }
  },
  {
    id: "2",
    type: "risk",
    priority: "high",
    title: "TechCo deal stalled - no activity for 10 days",
    description: "The $180K TechCo opportunity hasn't had any email or call activity. Last interaction mentioned budget concerns.",
    source: "Salesforce + Email Tracking",
    timestamp: "1 day ago",
    impact: "Risk of losing $180K in pipeline",
    recommendation: "Reach out with ROI calculator and case studies",
    metrics: { "Days Since Contact": 10, "Deal Value": "$180K" }
  },
  {
    id: "3",
    type: "trend",
    priority: "medium",
    title: "Security concerns becoming top objection",
    description: "40% of recent calls mentioned security as a primary concern, up from 15% last quarter.",
    source: "Gong Call Analysis",
    timestamp: "3 days ago",
    impact: "Affecting close rates",
    recommendation: "Prepare security certification deck and compliance documentation",
    metrics: { "Mentions This Quarter": "40%", "Previous Quarter": "15%" }
  },
  {
    id: "4",
    type: "action",
    priority: "high",
    title: "Follow up on FinanceApp demo request",
    description: "CFO requested a technical deep-dive after yesterday's call. They're evaluating 2 other vendors.",
    source: "Meeting Notes",
    timestamp: "5 hours ago",
    impact: "$320K opportunity",
    recommendation: "Schedule technical demo within 48 hours"
  },
  {
    id: "5",
    type: "opportunity",
    priority: "medium",
    title: "Cross-sell opportunity with DataSoft",
    description: "DataSoft is using our core product successfully. Usage data shows they could benefit from our analytics module.",
    source: "Product Usage Analytics",
    timestamp: "1 week ago",
    impact: "Additional $50K ARR",
    recommendation: "Schedule success review and present analytics capabilities"
  }
];

export default function InsightsPage() {
  const [selectedType, setSelectedType] = useState<string>("all");
  const [selectedInsight, setSelectedInsight] = useState<Insight | null>(null);

  const filteredInsights = selectedType === "all" 
    ? SAMPLE_INSIGHTS 
    : SAMPLE_INSIGHTS.filter(i => i.type === selectedType);

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "opportunity": return "💡";
      case "risk": return "⚠️";
      case "trend": return "📈";
      case "action": return "🎯";
      default: return "📊";
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case "opportunity": return "border-green-200 bg-green-50";
      case "risk": return "border-red-200 bg-red-50";
      case "trend": return "border-blue-200 bg-blue-50";
      case "action": return "border-purple-200 bg-purple-50";
      default: return "border-gray-200 bg-gray-50";
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "high": return "bg-red-100 text-red-700";
      case "medium": return "bg-amber-100 text-amber-700";
      case "low": return "bg-gray-100 text-gray-700";
      default: return "bg-gray-100 text-gray-700";
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">AI-Powered Insights</h1>
          <p className="text-gray-500 mt-1">Actionable intelligence from your business data</p>
        </div>
        <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          🔄 Refresh Insights
        </button>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-green-500 to-green-600 text-white rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm opacity-90">Opportunities</p>
              <p className="text-2xl font-bold">
                {SAMPLE_INSIGHTS.filter(i => i.type === "opportunity").length}
              </p>
            </div>
            <span className="text-3xl">💡</span>
          </div>
        </div>
        <div className="bg-gradient-to-br from-red-500 to-red-600 text-white rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm opacity-90">Risks</p>
              <p className="text-2xl font-bold">
                {SAMPLE_INSIGHTS.filter(i => i.type === "risk").length}
              </p>
            </div>
            <span className="text-3xl">⚠️</span>
          </div>
        </div>
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm opacity-90">Trends</p>
              <p className="text-2xl font-bold">
                {SAMPLE_INSIGHTS.filter(i => i.type === "trend").length}
              </p>
            </div>
            <span className="text-3xl">📈</span>
          </div>
        </div>
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 text-white rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm opacity-90">Actions</p>
              <p className="text-2xl font-bold">
                {SAMPLE_INSIGHTS.filter(i => i.type === "action").length}
              </p>
            </div>
            <span className="text-3xl">🎯</span>
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2 border-b">
        {["all", "opportunity", "risk", "trend", "action"].map((type) => (
          <button
            key={type}
            onClick={() => setSelectedType(type)}
            className={`px-4 py-2 capitalize font-medium transition-colors ${
              selectedType === type
                ? "border-b-2 border-blue-600 text-blue-600"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            {type === "all" ? "All Insights" : type}
          </button>
        ))}
      </div>

      {/* Insights Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredInsights.map((insight) => (
          <div
            key={insight.id}
            onClick={() => setSelectedInsight(insight)}
            className={`border rounded-lg p-4 cursor-pointer hover:shadow-lg transition-shadow ${getTypeColor(insight.type)}`}
          >
            <div className="flex justify-between items-start mb-3">
              <div className="flex items-center gap-2">
                <span className="text-2xl">{getTypeIcon(insight.type)}</span>
                <div>
                  <span className={`text-xs px-2 py-0.5 rounded ${getPriorityColor(insight.priority)}`}>
                    {insight.priority} priority
                  </span>
                </div>
              </div>
              <span className="text-xs text-gray-500">{insight.timestamp}</span>
            </div>

            <h3 className="font-semibold mb-2">{insight.title}</h3>
            <p className="text-sm text-gray-700 mb-3">{insight.description}</p>

            {insight.impact && (
              <div className="mb-2">
                <span className="text-xs text-gray-600">Impact:</span>
                <p className="text-sm font-medium">{insight.impact}</p>
              </div>
            )}

            {insight.metrics && (
              <div className="flex gap-3 mt-3 pt-3 border-t">
                {Object.entries(insight.metrics).map(([key, value]) => (
                  <div key={key}>
                    <p className="text-xs text-gray-600">{key}</p>
                    <p className="text-sm font-semibold">{value}</p>
                  </div>
                ))}
              </div>
            )}

            <div className="mt-3 flex items-center justify-between">
              <span className="text-xs text-gray-500">Source: {insight.source}</span>
              <button className="text-sm text-blue-600 hover:text-blue-700 font-medium">
                View Details →
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Insight Detail Modal */}
      {selectedInsight && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setSelectedInsight(null)}>
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between items-start mb-4">
              <div className="flex items-center gap-3">
                <span className="text-3xl">{getTypeIcon(selectedInsight.type)}</span>
                <div>
                  <h2 className="text-xl font-bold">{selectedInsight.title}</h2>
                  <div className="flex items-center gap-2 mt-1">
                    <span className={`text-xs px-2 py-0.5 rounded ${getPriorityColor(selectedInsight.priority)}`}>
                      {selectedInsight.priority} priority
                    </span>
                    <span className="text-xs text-gray-500">• {selectedInsight.timestamp}</span>
                  </div>
                </div>
              </div>
              <button
                onClick={() => setSelectedInsight(null)}
                className="text-gray-400 hover:text-gray-600 text-xl"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-semibold text-gray-600 mb-1">Description</h3>
                <p className="text-gray-800">{selectedInsight.description}</p>
              </div>

              {selectedInsight.impact && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-600 mb-1">Business Impact</h3>
                  <p className="text-gray-800">{selectedInsight.impact}</p>
                </div>
              )}

              {selectedInsight.recommendation && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h3 className="text-sm font-semibold text-blue-900 mb-1">💡 Recommended Action</h3>
                  <p className="text-blue-800">{selectedInsight.recommendation}</p>
                </div>
              )}

              {selectedInsight.metrics && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-600 mb-2">Key Metrics</h3>
                  <div className="grid grid-cols-2 gap-3">
                    {Object.entries(selectedInsight.metrics).map(([key, value]) => (
                      <div key={key} className="bg-gray-50 rounded-lg p-3">
                        <p className="text-xs text-gray-600">{key}</p>
                        <p className="text-lg font-semibold">{value}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="pt-4 border-t">
                <p className="text-xs text-gray-500">Data Source: {selectedInsight.source}</p>
              </div>
            </div>

            <div className="mt-6 flex gap-2">
              <button className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                Take Action
              </button>
              <button className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50">
                Share Insight
              </button>
              <button className="px-4 py-2 border rounded-lg hover:bg-gray-50">
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}