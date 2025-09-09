"use client";
import React from 'react';
import dynamic from 'next/dynamic';
import AgnoBridgeStatus from '@/components/sophia/AgnoBridgeStatus';
import ChatArea from '@/components/playground/ChatArea/ChatArea';
import Section from '@/components/widgets/Section';
import IntegrationStatusPanel from '@/components/sophia/IntegrationStatusPanel';

const CostDashboard = dynamic(() => import('@/components/analytics/CostDashboard'), { ssr: false, loading: () => <div className="h-32" /> });
const ClientHealthDashboard = dynamic(() => import('@/components/dashboards/ClientHealthDashboard'), { ssr: false, loading: () => <div className="h-32" /> });
const SalesPerformanceDashboard = dynamic(() => import('@/components/dashboards/SalesPerformanceDashboard'), { ssr: false, loading: () => <div className="h-32" /> });
const ProjectManagementDashboard = dynamic(() => import('@/components/dashboards/ProjectManagementDashboard'), { ssr: false, loading: () => <div className="h-32" /> });
const MCPBusinessIntelligence = dynamic(() => import('@/components/sophia/MCPBusinessIntelligence'), { ssr: false, loading: () => <div className="h-32" /> });
const InfraDashboard = dynamic(() => import('@/components/infrastructure/InfraDashboard').then(m => m.InfraDashboard), { ssr: false, loading: () => <div className="h-32" /> });

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

        {/* Integration Status */}
        <div className="max-w-[1600px] mx-auto">
          <Section title="Integrations" subtitle="Connected systems and health">
            <IntegrationStatusPanel />
          </Section>
        </div>

        {/* Quick KPIs (Costs + Infra) */}
        <div className="max-w-[1600px] mx-auto grid grid-cols-1 xl:grid-cols-2 gap-4">
          <Section title="Costs & Usage" subtitle="LLM spend, tokens, and trends">
            <CostDashboard />
          </Section>
          <Section title="Infrastructure" subtitle="Service health and operations">
            <InfraDashboard />
          </Section>
        </div>

        {/* Deep-dive dashboards */}
        <div className="max-w-[1600px] mx-auto grid grid-cols-1 xl:grid-cols-2 gap-4">
          <Section title="Sales Performance" subtitle="Pipeline and rep performance">
            <SalesPerformanceDashboard />
          </Section>
          <Section title="Client Health" subtitle="Retention and risk">
            <ClientHealthDashboard />
          </Section>
          <Section title="Project Management" subtitle="Workstreams and throughput">
            <ProjectManagementDashboard />
          </Section>
          <Section title="MCP Intelligence" subtitle="Server status and insight">
            <MCPBusinessIntelligence />
          </Section>
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
