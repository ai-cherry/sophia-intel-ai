"use client";
import { useState } from "react";

export default function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState("30d");
  const [selectedMetric, setSelectedMetric] = useState("revenue");

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Analytics Dashboard</h1>
          <p className="text-gray-500 mt-1">Deep insights into your sales performance</p>
        </div>
        <div className="flex gap-2">
          <select 
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-4 py-2 border rounded-lg bg-white"
          >
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
            <option value="1y">Last year</option>
          </select>
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            📊 Export Report
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border p-4">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm text-gray-600">Total Revenue</p>
              <p className="text-3xl font-bold mt-1">$3.2M</p>
              <p className="text-sm text-green-600 mt-2">↑ 18% vs prev period</p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center text-2xl">
              💰
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm text-gray-600">Conversion Rate</p>
              <p className="text-3xl font-bold mt-1">24.5%</p>
              <p className="text-sm text-amber-600 mt-2">↓ 2% vs prev period</p>
            </div>
            <div className="w-12 h-12 bg-amber-100 rounded-lg flex items-center justify-center text-2xl">
              🎯
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm text-gray-600">Avg Deal Size</p>
              <p className="text-3xl font-bold mt-1">$85K</p>
              <p className="text-sm text-green-600 mt-2">↑ 12% vs prev period</p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center text-2xl">
              📈
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm text-gray-600">Sales Velocity</p>
              <p className="text-3xl font-bold mt-1">32d</p>
              <p className="text-sm text-green-600 mt-2">↓ 5d improvement</p>
            </div>
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center text-2xl">
              ⚡
            </div>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-2 gap-6">
        {/* Revenue Chart */}
        <div className="bg-white rounded-lg border p-6">
          <h2 className="text-lg font-semibold mb-4">Revenue Trend</h2>
          <div className="h-64 flex items-end justify-between gap-2">
            {Array.from({ length: 12 }, (_, i) => (
              <div key={i} className="flex-1 flex flex-col items-center gap-2">
                <div
                  className="w-full bg-blue-500 rounded-t hover:bg-blue-600 transition-colors"
                  style={{ height: `${Math.random() * 100 + 50}%` }}
                ></div>
                <span className="text-xs text-gray-500">
                  {["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][i]}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Pipeline by Stage */}
        <div className="bg-white rounded-lg border p-6">
          <h2 className="text-lg font-semibold mb-4">Pipeline Distribution</h2>
          <div className="space-y-3">
            {[
              { stage: "Prospecting", value: 450000, color: "bg-gray-500" },
              { stage: "Qualification", value: 820000, color: "bg-blue-500" },
              { stage: "Discovery", value: 1200000, color: "bg-indigo-500" },
              { stage: "Proposal", value: 650000, color: "bg-purple-500" },
              { stage: "Negotiation", value: 380000, color: "bg-orange-500" }
            ].map((item) => (
              <div key={item.stage}>
                <div className="flex justify-between text-sm mb-1">
                  <span>{item.stage}</span>
                  <span className="font-semibold">${(item.value / 1000000).toFixed(2)}M</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`${item.color} h-2 rounded-full`}
                    style={{ width: `${(item.value / 1200000) * 100}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="bg-white rounded-lg border p-6">
        <h2 className="text-lg font-semibold mb-4">Team Performance Matrix</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="border-b">
              <tr>
                <th className="text-left py-2 px-3 text-sm font-medium">Team Member</th>
                <th className="text-right py-2 px-3 text-sm font-medium">Calls Made</th>
                <th className="text-right py-2 px-3 text-sm font-medium">Meetings Booked</th>
                <th className="text-right py-2 px-3 text-sm font-medium">Proposals Sent</th>
                <th className="text-right py-2 px-3 text-sm font-medium">Deals Closed</th>
                <th className="text-right py-2 px-3 text-sm font-medium">Revenue</th>
                <th className="text-right py-2 px-3 text-sm font-medium">Quota %</th>
              </tr>
            </thead>
            <tbody>
              {[
                { name: "Sarah Chen", calls: 145, meetings: 28, proposals: 12, deals: 8, revenue: "$680K", quota: 113 },
                { name: "Mike Roberts", calls: 132, meetings: 24, proposals: 10, deals: 6, revenue: "$520K", quota: 87 },
                { name: "Alex Kim", calls: 168, meetings: 35, proposals: 15, deals: 10, revenue: "$450K", quota: 75 },
                { name: "Jordan Lee", calls: 98, meetings: 18, proposals: 8, deals: 5, revenue: "$380K", quota: 95 }
              ].map((member, idx) => (
                <tr key={idx} className="border-b hover:bg-gray-50">
                  <td className="py-3 px-3 font-medium">{member.name}</td>
                  <td className="py-3 px-3 text-right">{member.calls}</td>
                  <td className="py-3 px-3 text-right">{member.meetings}</td>
                  <td className="py-3 px-3 text-right">{member.proposals}</td>
                  <td className="py-3 px-3 text-right">{member.deals}</td>
                  <td className="py-3 px-3 text-right font-semibold">{member.revenue}</td>
                  <td className="py-3 px-3 text-right">
                    <span className={`px-2 py-1 rounded text-xs ${
                      member.quota >= 100 ? "bg-green-100 text-green-700" : 
                      member.quota >= 80 ? "bg-amber-100 text-amber-700" : 
                      "bg-red-100 text-red-700"
                    }`}>
                      {member.quota}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Insights Summary */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-lg p-4">
          <h3 className="font-semibold mb-2">🎯 Top Performer</h3>
          <p className="text-2xl font-bold">Sarah Chen</p>
          <p className="text-sm opacity-90 mt-1">113% of quota achieved</p>
        </div>
        <div className="bg-gradient-to-br from-green-500 to-green-600 text-white rounded-lg p-4">
          <h3 className="font-semibold mb-2">📈 Best Conversion</h3>
          <p className="text-2xl font-bold">28.5%</p>
          <p className="text-sm opacity-90 mt-1">Lead to opportunity rate</p>
        </div>
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 text-white rounded-lg p-4">
          <h3 className="font-semibold mb-2">⚡ Fastest Deal</h3>
          <p className="text-2xl font-bold">18 days</p>
          <p className="text-sm opacity-90 mt-1">Acme Corp closed in record time</p>
        </div>
      </div>
    </div>
  );
}