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
      <div className="flex-1 overflow-auto p-4 md:p-6 space-y-6">
        <div className="max-w-[1600px] mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight">Sophia Command Center</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">Unified view of business intelligence and operations</p>
          </div>
          <AgnoBridgeStatus />
        </div>

        {/* Quick KPIs (Costs + Infra) */}
        <div className="max-w-[1600px] mx-auto grid grid-cols-1 xl:grid-cols-2 gap-4">
          <div className="rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-2 md:p-3">
            <CostDashboard />
          </div>
          <div className="rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-2 md:p-3">
            <InfraDashboard />
          </div>
        </div>

        {/* Deep-dive dashboards */}
        <div className="max-w-[1600px] mx-auto grid grid-cols-1 xl:grid-cols-2 gap-4">
          <div className="rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-2 md:p-3">
            <SalesPerformanceDashboard />
          </div>
          <div className="rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-2 md:p-3">
            <ClientHealthDashboard />
          </div>
          <div className="rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-2 md:p-3">
            <ProjectManagementDashboard />
          </div>
          <div className="rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-2 md:p-3">
            <MCPBusinessIntelligence />
          </div>
        </div>
      </div>

      {/* Chat dock */}
      <div className="hidden lg:flex w-[420px] border-l border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
        <div className="flex-1 flex flex-col">
          <div className="p-3 border-b border-gray-200 dark:border-gray-800">
            <h2 className="text-sm font-semibold">Chat</h2>
            <p className="text-xs text-gray-500 dark:text-gray-400">Ask questions, trigger agents</p>
          </div>
          <div className="flex-1 min-h-0">
            <ChatArea />
          </div>
        </div>
      </div>
    </div>
  );
}
