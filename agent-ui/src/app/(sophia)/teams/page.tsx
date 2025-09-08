"use client";
import { useState } from "react";

type TeamMember = {
  id: string;
  name: string;
  role: string;
  avatar: string;
  status: "online" | "busy" | "offline";
  performance: {
    dealsWon: number;
    revenue: string;
    winRate: number;
    avgDealSize: string;
  };
  recentActivity?: string;
};

const TEAM_MEMBERS: TeamMember[] = [
  {
    id: "1",
    name: "Sarah Chen",
    role: "Enterprise Sales Lead",
    avatar: "SC",
    status: "online",
    performance: {
      dealsWon: 12,
      revenue: "$1.8M",
      winRate: 68,
      avgDealSize: "$150K"
    },
    recentActivity: "Closed Acme Corp deal - $250K"
  },
  {
    id: "2",
    name: "Mike Roberts",
    role: "Account Executive",
    avatar: "MR",
    status: "busy",
    performance: {
      dealsWon: 8,
      revenue: "$920K",
      winRate: 52,
      avgDealSize: "$115K"
    },
    recentActivity: "In call with TechCo team"
  },
  {
    id: "3",
    name: "Alex Kim",
    role: "Sales Development Rep",
    avatar: "AK",
    status: "online",
    performance: {
      dealsWon: 15,
      revenue: "$450K",
      winRate: 45,
      avgDealSize: "$30K"
    },
    recentActivity: "Qualified 3 new leads today"
  },
  {
    id: "4",
    name: "Jordan Lee",
    role: "Customer Success Manager",
    avatar: "JL",
    status: "offline",
    performance: {
      dealsWon: 5,
      revenue: "$380K",
      winRate: 71,
      avgDealSize: "$76K"
    },
    recentActivity: "Upsold DataSoft to Premium plan"
  }
];

export default function TeamsPage() {
  const [selectedMember, setSelectedMember] = useState<TeamMember | null>(null);
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");

  const getStatusColor = (status: string) => {
    switch (status) {
      case "online": return "bg-green-500";
      case "busy": return "bg-amber-500";
      case "offline": return "bg-gray-400";
      default: return "bg-gray-400";
    }
  };

  const getPerformanceColor = (winRate: number) => {
    if (winRate >= 60) return "text-green-600";
    if (winRate >= 40) return "text-amber-600";
    return "text-red-600";
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Team Performance</h1>
          <p className="text-gray-500 mt-1">Monitor and collaborate with your sales team</p>
        </div>
        <div className="flex gap-2">
          <button className="px-4 py-2 bg-white border rounded-lg hover:bg-gray-50">
            📊 Team Report
          </button>
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            + Add Member
          </button>
        </div>
      </div>

      {/* Team Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border p-4">
          <p className="text-sm text-gray-600">Total Team Revenue</p>
          <p className="text-2xl font-bold">$3.55M</p>
          <p className="text-sm text-green-600 mt-1">+22% vs last quarter</p>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <p className="text-sm text-gray-600">Average Win Rate</p>
          <p className="text-2xl font-bold">59%</p>
          <p className="text-sm text-amber-600 mt-1">↑ 5% improvement</p>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <p className="text-sm text-gray-600">Deals Won (Q4)</p>
          <p className="text-2xl font-bold">40</p>
          <p className="text-sm text-gray-600 mt-1">8 in progress</p>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <p className="text-sm text-gray-600">Team Activity</p>
          <div className="flex items-center gap-2 mt-2">
            <span className="w-2 h-2 bg-green-500 rounded-full"></span>
            <span className="text-sm">3 online</span>
            <span className="w-2 h-2 bg-amber-500 rounded-full ml-2"></span>
            <span className="text-sm">1 busy</span>
          </div>
        </div>
      </div>

      {/* View Toggle */}
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">Team Members</h2>
        <div className="flex bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setViewMode("grid")}
            className={`px-3 py-1 rounded ${viewMode === "grid" ? "bg-white shadow-sm" : ""}`}
          >
            Grid
          </button>
          <button
            onClick={() => setViewMode("list")}
            className={`px-3 py-1 rounded ${viewMode === "list" ? "bg-white shadow-sm" : ""}`}
          >
            List
          </button>
        </div>
      </div>

      {/* Team Members */}
      {viewMode === "grid" ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {TEAM_MEMBERS.map((member) => (
            <div
              key={member.id}
              onClick={() => setSelectedMember(member)}
              className="bg-white rounded-lg border p-4 hover:shadow-lg transition-shadow cursor-pointer"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="relative">
                    <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center text-white font-semibold">
                      {member.avatar}
                    </div>
                    <span className={`absolute bottom-0 right-0 w-3 h-3 ${getStatusColor(member.status)} rounded-full border-2 border-white`}></span>
                  </div>
                  <div>
                    <p className="font-semibold">{member.name}</p>
                    <p className="text-sm text-gray-600">{member.role}</p>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 mb-4">
                <div>
                  <p className="text-xs text-gray-600">Revenue</p>
                  <p className="font-semibold">{member.performance.revenue}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-600">Deals Won</p>
                  <p className="font-semibold">{member.performance.dealsWon}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-600">Win Rate</p>
                  <p className={`font-semibold ${getPerformanceColor(member.performance.winRate)}`}>
                    {member.performance.winRate}%
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-600">Avg Deal</p>
                  <p className="font-semibold">{member.performance.avgDealSize}</p>
                </div>
              </div>

              {member.recentActivity && (
                <div className="pt-3 border-t">
                  <p className="text-xs text-gray-600">Recent Activity</p>
                  <p className="text-sm mt-1">{member.recentActivity}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-lg border">
          <table className="w-full">
            <thead className="border-b bg-gray-50">
              <tr>
                <th className="text-left px-4 py-3 text-sm font-medium">Member</th>
                <th className="text-left px-4 py-3 text-sm font-medium">Status</th>
                <th className="text-left px-4 py-3 text-sm font-medium">Revenue</th>
                <th className="text-left px-4 py-3 text-sm font-medium">Deals Won</th>
                <th className="text-left px-4 py-3 text-sm font-medium">Win Rate</th>
                <th className="text-left px-4 py-3 text-sm font-medium">Avg Deal Size</th>
                <th className="text-left px-4 py-3 text-sm font-medium">Recent Activity</th>
              </tr>
            </thead>
            <tbody>
              {TEAM_MEMBERS.map((member) => (
                <tr
                  key={member.id}
                  onClick={() => setSelectedMember(member)}
                  className="border-b hover:bg-gray-50 cursor-pointer"
                >
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center text-white text-sm font-semibold">
                        {member.avatar}
                      </div>
                      <div>
                        <p className="font-medium">{member.name}</p>
                        <p className="text-sm text-gray-600">{member.role}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 ${getStatusColor(member.status)} rounded-full`}></span>
                      <span className="text-sm capitalize">{member.status}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 font-semibold">{member.performance.revenue}</td>
                  <td className="px-4 py-3">{member.performance.dealsWon}</td>
                  <td className={`px-4 py-3 font-semibold ${getPerformanceColor(member.performance.winRate)}`}>
                    {member.performance.winRate}%
                  </td>
                  <td className="px-4 py-3">{member.performance.avgDealSize}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{member.recentActivity}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Leaderboard */}
      <div className="bg-gradient-to-br from-blue-600 to-purple-600 text-white rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">🏆 Q4 Leaderboard</h2>
        <div className="grid grid-cols-3 gap-6">
          <div>
            <p className="text-sm opacity-90 mb-1">Top Revenue</p>
            <p className="text-lg font-bold">Sarah Chen - $1.8M</p>
          </div>
          <div>
            <p className="text-sm opacity-90 mb-1">Most Deals Won</p>
            <p className="text-lg font-bold">Alex Kim - 15 deals</p>
          </div>
          <div>
            <p className="text-sm opacity-90 mb-1">Best Win Rate</p>
            <p className="text-lg font-bold">Jordan Lee - 71%</p>
          </div>
        </div>
      </div>
    </div>
  );
}