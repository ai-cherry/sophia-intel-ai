'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import SalesPerformanceDashboard from '@/components/dashboards/SalesPerformanceDashboard';
import ClientHealthDashboard from '@/components/dashboards/ClientHealthDashboard';
import ProjectManagementDashboard from '@/components/dashboards/ProjectManagementDashboard';
import UnifiedChatOrchestration from '@/components/dashboards/UnifiedChatOrchestration';
import { dashboardConfig, featureFlags } from '@/config/environment';
import {
  Zap, Heart, Brain, MessageCircle, Activity, TrendingUp,
  Users, Target, AlertTriangle, CheckCircle, Eye, Settings
} from 'lucide-react';

// ==================== SOPHIA INTELLIGENCE HUB ====================

const SophiaIntelligencePage: React.FC = () => {
  const [activeModule, setActiveModule] = useState('overview');
  const [systemHealth, setSystemHealth] = useState({
    overall: 95,
    sales: 92,
    clients: 88,
    projects: 94,
    communication: 96
  });

  const [quickStats, setQuickStats] = useState({
    totalActiveProjects: 12,
    atRiskClients: 3,
    salesTeamPerformance: 87,
    openBlockers: 5,
    unreadMessages: 7
  });

  useEffect(() => {
    // Load initial system overview data
    loadSystemHealth();
  }, []);

  const loadSystemHealth = async () => {
    try {
      // This would typically fetch from your APIs
      const response = await fetch('/api/system/health');
      if (response.ok) {
        const data = await response.json();
        setSystemHealth(data.health);
        setQuickStats(data.stats);
      }
    } catch (error) {
      console.error('Failed to load system health:', error);
    }
  };

  const modules = [
    {
      id: 'hermes',
      name: 'Hermes',
      subtitle: 'Sales Performance',
      description: 'Real-time sales metrics, Gong call analysis, and coaching insights',
      icon: <Zap className="w-6 h-6" />,
      color: 'from-blue-500 to-purple-500',
      health: systemHealth.sales,
      stats: [
        { label: 'Team Quota', value: `${systemHealth.sales}%` },
        { label: 'Active Deals', value: '47' },
        { label: 'This Week', value: '23 calls' }
      ]
    },
    {
      id: 'asclepius',
      name: 'Asclepius',
      subtitle: 'Client Health',
      description: 'Health scoring, churn prevention, and expansion opportunities',
      icon: <Heart className="w-6 h-6" />,
      color: 'from-emerald-500 to-teal-500',
      health: systemHealth.clients,
      stats: [
        { label: 'Avg Health', value: `${systemHealth.clients}%` },
        { label: 'At Risk', value: quickStats.atRiskClients.toString() },
        { label: 'Renewals', value: '8 due' }
      ]
    },
    {
      id: 'athena',
      name: 'Athena',
      subtitle: 'Project Intelligence',
      description: 'Cross-platform sync, team alignment, and bottleneck detection',
      icon: <Brain className="w-6 h-6" />,
      color: 'from-purple-500 to-pink-500',
      health: systemHealth.projects,
      stats: [
        { label: 'Active Projects', value: quickStats.totalActiveProjects.toString() },
        { label: 'Team Health', value: `${systemHealth.projects}%` },
        { label: 'Blockers', value: quickStats.openBlockers.toString() }
      ]
    },
    {
      id: 'unified-chat',
      name: 'Unified Chat',
      subtitle: 'Voice & Text AI',
      description: 'Natural language interface with voice integration and smart routing',
      icon: <MessageCircle className="w-6 h-6" />,
      color: 'from-indigo-500 to-purple-500',
      health: systemHealth.communication,
      stats: [
        { label: 'Response Time', value: '0.8s' },
        { label: 'Accuracy', value: '94%' },
        { label: 'Voice Ready', value: featureFlags.voiceEnabled ? 'Yes' : 'No' }
      ]
    }
  ];

  const getHealthColor = (health: number) => {
    if (health >= 90) return 'text-green-600';
    if (health >= 75) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getHealthIcon = (health: number) => {
    if (health >= 90) return <CheckCircle className="w-4 h-4 text-green-500" />;
    if (health >= 75) return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
    return <AlertTriangle className="w-4 h-4 text-red-500" />;
  };

  const renderModuleCard = (module: any) => (
    <Card
      key={module.id}
      className={`cursor-pointer transition-all hover:shadow-xl hover:scale-105 ${
        activeModule === module.id ? 'ring-2 ring-blue-500 shadow-xl' : ''
      }`}
      onClick={() => setActiveModule(module.id)}
    >
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`w-12 h-12 rounded-lg bg-gradient-to-r ${module.color} flex items-center justify-center text-white`}>
              {module.icon}
            </div>
            <div>
              <CardTitle className="text-lg">{module.name}</CardTitle>
              <p className="text-sm text-gray-600 dark:text-gray-400">{module.subtitle}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {getHealthIcon(module.health)}
            <span className={`font-bold ${getHealthColor(module.health)}`}>
              {module.health}%
            </span>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-gray-700 dark:text-gray-300 mb-4">
          {module.description}
        </p>
        <div className="grid grid-cols-3 gap-2 text-xs">
          {module.stats.map((stat: any, idx: number) => (
            <div key={idx} className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded">
              <div className="font-bold">{stat.value}</div>
              <div className="text-gray-500">{stat.label}</div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );

  const renderDashboard = () => {
    switch (activeModule) {
      case 'hermes':
        return <SalesPerformanceDashboard />;
      case 'asclepius':
        return <ClientHealthDashboard />;
      case 'athena':
        return <ProjectManagementDashboard />;
      case 'unified-chat':
        return <UnifiedChatOrchestration />;
      default:
        return null;
    }
  };

  if (activeModule !== 'overview') {
    return (
      <div className="min-h-screen">
        {/* Quick Navigation Bar */}
        <div className="bg-white/90 dark:bg-gray-900/90 backdrop-blur-lg border-b sticky top-0 z-50">
          <div className="container mx-auto px-4 py-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setActiveModule('overview')}
                  className="text-blue-600 hover:text-blue-700"
                >
                  ← Sophia Hub
                </Button>
                <div className="w-px h-4 bg-gray-300 dark:bg-gray-600"></div>
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  {modules.find(m => m.id === activeModule)?.name} Dashboard
                </span>
              </div>

              <div className="flex items-center space-x-2">
                {modules.map((module) => (
                  <Button
                    key={module.id}
                    variant={activeModule === module.id ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setActiveModule(module.id)}
                    className="text-xs"
                  >
                    {module.icon}
                    <span className="ml-1 hidden sm:inline">{module.name}</span>
                  </Button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Dashboard Content */}
        {renderDashboard()}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 dark:from-gray-900 dark:to-blue-950">
      {/* Header */}
      <div className="border-b bg-white/80 dark:bg-gray-900/80 backdrop-blur-lg">
        <div className="container mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 via-purple-600 to-teal-600">
                Sophia Intelligence Hub
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                AI-powered business intelligence with mythology-themed specialized agents
              </p>
            </div>

            <div className="flex items-center space-x-4">
              {/* System Health Badge */}
              <div className="flex items-center space-x-2 px-3 py-2 bg-gray-100 dark:bg-gray-800 rounded-lg">
                <Activity className="w-4 h-4 text-blue-600" />
                <span className="text-sm font-medium">System Health:</span>
                <span className={`font-bold ${getHealthColor(systemHealth.overall)}`}>
                  {systemHealth.overall}%
                </span>
              </div>

              <Button variant="outline" size="sm">
                <Settings className="w-4 h-4 mr-2" />
                Settings
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Stats Bar */}
      <div className="bg-white/50 dark:bg-gray-900/50 border-b">
        <div className="container mx-auto px-6 py-4">
          <div className="grid grid-cols-5 gap-6 text-center">
            <div>
              <div className="text-2xl font-bold text-blue-600">{quickStats.totalActiveProjects}</div>
              <div className="text-xs text-gray-500">Active Projects</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-red-600">{quickStats.atRiskClients}</div>
              <div className="text-xs text-gray-500">At-Risk Clients</div>
            </div>
            <div>
              <div className={`text-2xl font-bold ${getHealthColor(quickStats.salesTeamPerformance)}`}>
                {quickStats.salesTeamPerformance}%
              </div>
              <div className="text-xs text-gray-500">Sales Performance</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-yellow-600">{quickStats.openBlockers}</div>
              <div className="text-xs text-gray-500">Open Blockers</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600">{quickStats.unreadMessages}</div>
              <div className="text-xs text-gray-500">New Messages</div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-6 py-8">
        <Tabs defaultValue="modules" className="space-y-6">
          <TabsList className="grid grid-cols-2 w-96 mx-auto">
            <TabsTrigger value="modules">
              <Eye className="w-4 h-4 mr-2" />
              Intelligence Modules
            </TabsTrigger>
            <TabsTrigger value="chat">
              <MessageCircle className="w-4 h-4 mr-2" />
              Unified Chat
            </TabsTrigger>
          </TabsList>

          <TabsContent value="modules" className="space-y-6">
            {/* Intelligence Modules Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {modules.slice(0, 3).map(renderModuleCard)}
            </div>

            {/* Feature Highlights */}
            <Card className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white">
              <CardContent className="p-6">
                <h3 className="text-xl font-bold mb-4">Powered by Advanced AI</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <div className="font-semibold">Real-time Analytics</div>
                    <div className="opacity-80">Live data streaming</div>
                  </div>
                  <div>
                    <div className="font-semibold">Voice Integration</div>
                    <div className="opacity-80">ElevenLabs powered</div>
                  </div>
                  <div>
                    <div className="font-semibold">Cross-platform Sync</div>
                    <div className="opacity-80">Linear, Asana, Airtable</div>
                  </div>
                  <div>
                    <div className="font-semibold">Smart Routing</div>
                    <div className="opacity-80">Context-aware agents</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* System Architecture Overview */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm">Data Sources</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Gong Integration</span>
                      <Badge variant="outline">Connected</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span>CRM Systems</span>
                      <Badge variant="outline">Connected</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span>Project Tools</span>
                      <Badge variant="outline">Syncing</Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm">AI Models</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>GPT-4 Turbo</span>
                      <Badge className="bg-green-100 text-green-800">Active</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span>Claude-3 Sonnet</span>
                      <Badge className="bg-green-100 text-green-800">Active</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span>ElevenLabs</span>
                      <Badge className="bg-green-100 text-green-800">Active</Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm">Performance</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Avg Response Time</span>
                      <span className="font-medium">0.8s</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Uptime</span>
                      <span className="font-medium text-green-600">99.9%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Accuracy</span>
                      <span className="font-medium">94.2%</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="chat">
            <Card className="h-[600px]">
              <CardContent className="p-0 h-full">
                <UnifiedChatOrchestration />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default SophiaIntelligencePage;
