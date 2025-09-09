"use client";
import React from 'react';
import AgnoBridgeStatus from '@/components/sophia/AgnoBridgeStatus';
import CostDashboard from '@/components/analytics/CostDashboard';
import ClientHealthDashboard from '@/components/dashboards/ClientHealthDashboard';
import SalesPerformanceDashboard from '@/components/dashboards/SalesPerformanceDashboard';
import ProjectManagementDashboard from '@/components/dashboards/ProjectManagementDashboard';
import MCPBusinessIntelligence from '@/components/sophia/MCPBusinessIntelligence';
import { InfraDashboard } from '@/components/infrastructure/InfraDashboard';
import ChatArea from '@/components/playground/ChatArea/ChatArea';

export default function UnifiedCommandCenter() {
  return (
    <div className="flex h-[calc(100vh-0px)]">
      {/* Main content area */}
      <div className="flex-1 overflow-auto p-4 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Sophia Command Center</h1>
            <p className="text-sm text-gray-500">Unified view of business intelligence and operations</p>
          </div>
          <AgnoBridgeStatus />
        </div>

        {/* Quick KPIs (Costs + Infra) */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          <div className="rounded-lg border bg-white p-2">
            <CostDashboard />
          </div>
          <div className="rounded-lg border bg-white p-2">
            <InfraDashboard />
          </div>
        </div>

        {/* Deep-dive dashboards */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          <div className="rounded-lg border bg-white p-2">
            <SalesPerformanceDashboard />
          </div>
          <div className="rounded-lg border bg-white p-2">
            <ClientHealthDashboard />
          </div>
          <div className="rounded-lg border bg-white p-2">
            <ProjectManagementDashboard />
          </div>
          <div className="rounded-lg border bg-white p-2">
            <MCPBusinessIntelligence />
          </div>
        </div>
      </div>

      {/* Chat dock */}
      <div className="hidden lg:flex w-[420px] border-l bg-white">
        <div className="flex-1 flex flex-col">
          <div className="p-3 border-b">
            <h2 className="text-sm font-semibold">Chat</h2>
            <p className="text-xs text-gray-500">Ask questions, trigger agents</p>
          </div>
          <div className="flex-1 min-h-0">
            <ChatArea />
          </div>
        </div>
      </div>
    </div>
  );
}

