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
import MCPServerGrid from '@/components/mcp/MCPServerGrid';
import MythologyAgentWidget from '@/components/mythology/MythologyAgentWidget';
import { dashboardConfig, featureFlags } from '@/config/environment';
import {
  Zap, Heart, Brain, MessageCircle, Activity, TrendingUp,
  Users, Target, AlertTriangle, CheckCircle, Eye, Settings,
  Crown, Briefcase, UserCheck, ExternalLink, Server
} from 'lucide-react';

// ==================== SOPHIA INTELLIGENCE HUB ====================

const SophiaIntelligencePage: React.FC = () => {
  const [activeModule, setActiveModule] = useState('overview');
  const [currentRole, setCurrentRole] = useState<'executive' | 'project_manager' | 'team_lead'>('executive');
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
    processingVolumeToday: 2100000000, // $2.1B
    complianceScore: 97.2,
    unreadMessages: 7
  });

  // Role definitions
  const roles = [
    {
      id: 'executive',
      name: 'Executive',
      icon: <Crown className="w-4 h-4" />,
      description: 'Strategic oversight and high-level KPIs',
      color: 'from-amber-500 to-orange-500'
    },
    {
      id: 'project_manager',
      name: 'Project Manager',
      icon: <Briefcase className="w-4 h-4" />,
      description: 'Operational metrics and team coordination',
      color: 'from-blue-500 to-indigo-500'
    },
    {
      id: 'team_lead',
      name: 'Team Lead',
      icon: <UserCheck className="w-4 h-4" />,
      description: 'Individual performance and development',
      color: 'from-green-500 to-teal-500'
    }
  ];

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

  // Enhanced modules with Pay Ready business context
  const modules = [
    {
      id: 'hermes',
      name: 'Hermes',
      subtitle: 'Sales Performance & Market Intelligence',
      description: 'Real-time sales metrics, market penetration, and Pay Ready competitive positioning',
      icon: <Zap className="w-6 h-6" />,
      color: 'from-blue-500 to-purple-500',
      health: systemHealth.sales,
      payReadyContext: 'property_management_sales',
      stats: [
        { label: 'Processing Volume', value: '$2.1B' },
        { label: 'Market Share', value: '47.3%' },
        { label: 'New Properties', value: '127' }
      ]
    },
    {
      id: 'asclepius',
      name: 'Asclepius',
      subtitle: 'Client Health & Portfolio Management',
      description: 'Tenant satisfaction, landlord retention, and portfolio health metrics',
      icon: <Heart className="w-6 h-6" />,
      color: 'from-emerald-500 to-teal-500',
      health: systemHealth.clients,
      payReadyContext: 'tenant_landlord_satisfaction',
      stats: [
        { label: 'Portfolio Health', value: `${systemHealth.clients}%` },
        { label: 'At Risk Properties', value: quickStats.atRiskClients.toString() },
        { label: 'Compliance Score', value: '97.2%' }
      ]
    },
    {
      id: 'artemis',
      name: 'Artemis',
      subtitle: 'Technical Command Center',
      description: 'Dedicated technical operations dashboard for development teams and system monitoring',
      icon: <Brain className="w-6 h-6" />,
      color: 'from-purple-500 to-pink-500',
      health: systemHealth.projects,
      payReadyContext: 'technical_operations',
      stats: [
        { label: 'System Health', value: '99.8%' },
        { label: 'Code Quality', value: '94%' },
        { label: 'Deployments', value: '3 Active' }
      ]
    },
    {
      id: 'oracle',
      name: 'Oracle',
      subtitle: 'AI Assistant & Voice Intelligence',
      description: 'Natural language interface with Pay Ready business context and voice integration',
      icon: <MessageCircle className="w-6 h-6" />,
      color: 'from-indigo-500 to-purple-500',
      health: systemHealth.communication,
      payReadyContext: 'natural_language_interface',
      stats: [
        { label: 'Query Response', value: '0.6s' },
        { label: 'Context Accuracy', value: '96.4%' },
        { label: 'Voice Integration', value: featureFlags.voiceEnabled ? 'Active' : 'Ready' }
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
      onClick={() => {
        if (module.id === 'artemis') {
          window.location.href = '/artemis';
        } else {
          setActiveModule(module.id);
        }
      }}
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
            {module.id === 'artemis' && (
              <ExternalLink className="w-4 h-4 text-gray-500" />
            )}
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
      case 'artemis':
        // This should redirect to the dedicated Artemis Command Center
        return null;
      case 'oracle':
        return <UnifiedChatOrchestration />;
      // Legacy support
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
      {/* Deprecated notice */}
      <div className="bg-amber-50 dark:bg-amber-900/30 border-b border-amber-200 dark:border-amber-800">
        <div className="container mx-auto px-6 py-3 text-amber-900 dark:text-amber-200 text-sm flex items-center justify-between">
          <span>
            Heads up: This Sophia Hub view is deprecated. Use the unified dashboard instead.
          </span>
          <a href="/dashboard" className="underline font-medium">Go to /dashboard →</a>
        </div>
      </div>
      {/* Header */}
      <div className="border-b bg-white/80 dark:bg-gray-900/80 backdrop-blur-lg">
        <div className="container mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 via-purple-600 to-teal-600">
                Sophia Intelligence Hub
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                Pay Ready Business Intelligence - Managing $20B+ in rent processing with AI-powered insights
              </p>
            </div>

            <div className="flex items-center space-x-4">
              {/* Role Selector */}
              <div className="flex items-center space-x-2 px-3 py-2 bg-gray-100 dark:bg-gray-800 rounded-lg">
                <span className="text-sm font-medium">View as:</span>
                <select
                  value={currentRole}
                  onChange={(e) => setCurrentRole(e.target.value as 'executive' | 'project_manager' | 'team_lead')}
                  className="text-sm font-medium bg-transparent border-none focus:outline-none"
                >
                  {roles.map((role) => (
                    <option key={role.id} value={role.id}>
                      {role.name}
                    </option>
                  ))}
                </select>
              </div>

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
              <div className="text-xs text-gray-500">At-Risk Properties</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600">
                ${(quickStats.processingVolumeToday / 1000000000).toFixed(1)}B
              </div>
              <div className="text-xs text-gray-500">Processing Volume Today</div>
            </div>
            <div>
              <div className={`text-2xl font-bold ${getHealthColor(quickStats.complianceScore)}`}>
                {quickStats.complianceScore}%
              </div>
              <div className="text-xs text-gray-500">Compliance Score</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-purple-600">{quickStats.unreadMessages}</div>
              <div className="text-xs text-gray-500">Priority Alerts</div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-6 py-8">
        <Tabs defaultValue="modules" className="space-y-6">
          <TabsList className="grid grid-cols-3 w-full mx-auto">
            <TabsTrigger value="modules">
              <Eye className="w-4 h-4 mr-2" />
              Intelligence Modules
            </TabsTrigger>
            <TabsTrigger value="mcp">
              <Server className="w-4 h-4 mr-2" />
              MCP Intelligence
            </TabsTrigger>
            <TabsTrigger value="chat">
              <MessageCircle className="w-4 h-4 mr-2" />
              Oracle Assistant
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
                <h3 className="text-xl font-bold mb-4">Pay Ready Enterprise Intelligence</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <div className="font-semibold">$20B+ Processing</div>
                    <div className="opacity-80">Real-time rent analytics</div>
                  </div>
                  <div>
                    <div className="font-semibold">AI Voice Assistant</div>
                    <div className="opacity-80">Pay Ready context aware</div>
                  </div>
                  <div>
                    <div className="font-semibold">Cross-Platform Ops</div>
                    <div className="opacity-80">Unified Asana, Linear, Slack</div>
                  </div>
                  <div>
                    <div className="font-semibold">Predictive Insights</div>
                    <div className="opacity-80">Risk & opportunity detection</div>
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

          <TabsContent value="mcp" className="space-y-6">
            {/* Mythology Agent Widgets */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-3 gap-6">
              <MythologyAgentWidget
                agent={{
                  id: 'hermes',
                  name: 'Hermes',
                  title: 'Sales Performance & Market Intelligence',
                  domain: 'sophia',
                  assigned_mcp_servers: ['sophia_web_search', 'sophia_sales_intelligence'],
                  context: 'Real-time sales metrics, market penetration, and Pay Ready competitive positioning',
                  widget_type: 'sales_performance_intelligence',
                  icon_type: 'hermes',
                  pay_ready_context: 'property_management_sales'
                }}
                metrics={{
                  primary_metric: {
                    label: 'Processing Volume',
                    value: '$2.1B',
                    trend: 'up',
                    change_percentage: 12.3
                  },
                  secondary_metrics: [
                    { label: 'Market Share', value: '47.3%', status: 'good' },
                    { label: 'New Properties', value: '127', status: 'good' },
                    { label: 'Market Signals', value: '23 new', status: 'warning' },
                    { label: 'Response Time', value: '0.6s', status: 'good' }
                  ],
                  server_status: [
                    { server_name: 'sophia_web_search', status: 'operational', last_activity: '2 min ago' },
                    { server_name: 'sophia_sales_intelligence', status: 'operational', last_activity: '5 min ago' }
                  ]
                }}
              />

              <MythologyAgentWidget
                agent={{
                  id: 'asclepius',
                  name: 'Asclepius',
                  title: 'Client Health & Portfolio Management',
                  domain: 'sophia',
                  assigned_mcp_servers: ['sophia_business_analytics', 'sophia_business_memory'],
                  context: 'Tenant satisfaction, landlord retention, and portfolio health metrics',
                  widget_type: 'client_health_monitor',
                  icon_type: 'asclepius',
                  pay_ready_context: 'tenant_landlord_satisfaction'
                }}
                metrics={{
                  primary_metric: {
                    label: 'Portfolio Health',
                    value: '88%',
                    trend: 'stable'
                  },
                  secondary_metrics: [
                    { label: 'At Risk Properties', value: '3', status: 'warning' },
                    { label: 'Compliance Score', value: '97.2%', status: 'good' },
                    { label: 'Tenant Satisfaction', value: '4.2/5', status: 'good' },
                    { label: 'Retention Rate', value: '94%', status: 'good' }
                  ],
                  server_status: [
                    { server_name: 'sophia_business_analytics', status: 'operational', last_activity: '1 min ago' },
                    { server_name: 'sophia_business_memory', status: 'operational', last_activity: '3 min ago' }
                  ]
                }}
              />

              <MythologyAgentWidget
                agent={{
                  id: 'athena',
                  name: 'Athena',
                  title: 'Strategic Operations',
                  domain: 'sophia',
                  assigned_mcp_servers: ['sophia_business_analytics', 'shared_knowledge_base'],
                  context: 'Strategic initiatives and executive decision support',
                  widget_type: 'strategic_operations_command',
                  icon_type: 'athena'
                }}
                metrics={{
                  primary_metric: {
                    label: 'Strategic KPIs',
                    value: '94%',
                    trend: 'up'
                  },
                  secondary_metrics: [
                    { label: 'Active Projects', value: '12', status: 'good' },
                    { label: 'On Track', value: '10', status: 'good' },
                    { label: 'At Risk', value: '2', status: 'warning' },
                    { label: 'Executive Alerts', value: '3', status: 'warning' }
                  ],
                  server_status: [
                    { server_name: 'sophia_business_analytics', status: 'operational', last_activity: '1 min ago' },
                    { server_name: 'shared_knowledge_base', status: 'operational', last_activity: '4 min ago' }
                  ]
                }}
              />

              <MythologyAgentWidget
                agent={{
                  id: 'minerva',
                  name: 'Minerva',
                  title: 'Cross-Domain Analytics',
                  domain: 'sophia',
                  assigned_mcp_servers: ['sophia_business_analytics', 'shared_database'],
                  context: 'Advanced analytics bridging Sophia business intelligence with Artemis technical metrics',
                  widget_type: 'cross_domain_analytics',
                  icon_type: 'minerva'
                }}
                metrics={{
                  primary_metric: {
                    label: 'Insight Score',
                    value: '92%',
                    trend: 'up'
                  },
                  secondary_metrics: [
                    { label: 'Data Correlations', value: '847', status: 'good' },
                    { label: 'Predictive Models', value: '6 Active', status: 'good' },
                    { label: 'Anomaly Detection', value: '2 New', status: 'warning' },
                    { label: 'Cross-Domain Sync', value: '98%', status: 'good' }
                  ],
                  server_status: [
                    { server_name: 'sophia_business_analytics', status: 'operational', last_activity: '2 min ago' },
                    { server_name: 'shared_database', status: 'operational', last_activity: '1 min ago' }
                  ]
                }}
              />

              <MythologyAgentWidget
                agent={{
                  id: 'dionysus',
                  name: 'Dionysus',
                  title: 'Creative Market Intelligence',
                  domain: 'sophia',
                  assigned_mcp_servers: ['sophia_web_search', 'sophia_business_memory'],
                  context: 'Creative insights for market trends, competitor analysis, and innovative business opportunities',
                  widget_type: 'creative_market_intelligence',
                  icon_type: 'dionysus'
                }}
                metrics={{
                  primary_metric: {
                    label: 'Market Innovation Score',
                    value: '87%',
                    trend: 'up'
                  },
                  secondary_metrics: [
                    { label: 'Trend Signals', value: '23 New', status: 'good' },
                    { label: 'Competitor Moves', value: '5 Tracked', status: 'warning' },
                    { label: 'Innovation Opps', value: '12 Identified', status: 'good' },
                    { label: 'Creative Insights', value: '8 Generated', status: 'good' }
                  ],
                  server_status: [
                    { server_name: 'sophia_web_search', status: 'operational', last_activity: '3 min ago' },
                    { server_name: 'sophia_business_memory', status: 'operational', last_activity: '2 min ago' }
                  ]
                }}
              />

              <MythologyAgentWidget
                agent={{
                  id: 'oracle',
                  name: 'Oracle',
                  title: 'Natural Language Intelligence',
                  domain: 'sophia',
                  assigned_mcp_servers: ['shared_knowledge_base', 'sophia_business_memory'],
                  context: 'Voice-enabled natural language interface for business queries and conversational intelligence',
                  widget_type: 'natural_language_interface',
                  icon_type: 'oracle'
                }}
                metrics={{
                  primary_metric: {
                    label: 'Query Accuracy',
                    value: '96.4%',
                    trend: 'stable'
                  },
                  secondary_metrics: [
                    { label: 'Response Time', value: '0.6s', status: 'good' },
                    { label: 'Voice Queries', value: '127 Today', status: 'good' },
                    { label: 'Context Retention', value: '94%', status: 'good' },
                    { label: 'Language Models', value: '4 Active', status: 'good' }
                  ],
                  server_status: [
                    { server_name: 'shared_knowledge_base', status: 'operational', last_activity: '1 min ago' },
                    { server_name: 'sophia_business_memory', status: 'operational', last_activity: '2 min ago' }
                  ]
                }}
              />
            </div>

            {/* MCP Server Grid */}
            <MCPServerGrid
              domain="sophia"
              servers={[
                {
                  server_name: 'sophia_web_search',
                  server_type: 'web_search',
                  status: 'operational',
                  domain: 'sophia',
                  access_level: 'exclusive',
                  connections: { active: 4, max: 10, utilization: 0.4 },
                  capabilities: ['web_search', 'web_scraping', 'trend_analysis', 'market_research'],
                  last_activity: '2 minutes ago',
                  performance_metrics: {
                    response_time_ms: 650,
                    throughput_ops_per_sec: 45,
                    error_rate: 0.008,
                    uptime_percentage: 99.2
                  },
                  business_context: 'market_intelligence_gathering'
                },
                {
                  server_name: 'sophia_business_analytics',
                  server_type: 'business_analytics',
                  status: 'operational',
                  domain: 'sophia',
                  access_level: 'exclusive',
                  connections: { active: 7, max: 10, utilization: 0.7 },
                  capabilities: ['revenue_analytics', 'customer_analytics', 'sales_forecasting', 'churn_analysis'],
                  last_activity: '1 minute ago',
                  performance_metrics: {
                    response_time_ms: 180,
                    throughput_ops_per_sec: 125,
                    error_rate: 0.002,
                    uptime_percentage: 99.8
                  },
                  business_context: 'pay_ready_operations'
                },
                {
                  server_name: 'sophia_sales_intelligence',
                  server_type: 'sales_intelligence',
                  status: 'operational',
                  domain: 'sophia',
                  access_level: 'exclusive',
                  connections: { active: 3, max: 8, utilization: 0.375 },
                  capabilities: ['deal_scoring', 'opportunity_analysis', 'account_intelligence', 'sales_signals_detection'],
                  last_activity: '5 minutes ago',
                  performance_metrics: {
                    response_time_ms: 220,
                    throughput_ops_per_sec: 85,
                    error_rate: 0.005,
                    uptime_percentage: 99.5
                  },
                  business_context: 'property_sales_optimization'
                },
                {
                  server_name: 'sophia_business_memory',
                  server_type: 'business_memory',
                  status: 'operational',
                  domain: 'sophia',
                  access_level: 'exclusive',
                  connections: { active: 6, max: 12, utilization: 0.5 },
                  capabilities: ['context_memory', 'business_knowledge', 'historical_data', 'pattern_recognition'],
                  last_activity: '3 minutes ago',
                  performance_metrics: {
                    response_time_ms: 95,
                    throughput_ops_per_sec: 200,
                    error_rate: 0.003,
                    uptime_percentage: 99.6
                  },
                  business_context: 'pay_ready_business_memory'
                },
                {
                  server_name: 'shared_database',
                  server_type: 'database',
                  status: 'operational',
                  domain: 'shared',
                  access_level: 'shared',
                  connections: { active: 15, max: 25, utilization: 0.6 },
                  capabilities: ['query', 'insert', 'update', 'delete', 'transaction'],
                  last_activity: '30 seconds ago',
                  performance_metrics: {
                    response_time_ms: 12,
                    throughput_ops_per_sec: 450,
                    error_rate: 0.001,
                    uptime_percentage: 99.95
                  }
                }
              ]}
              mythology_agents={[
                {
                  name: 'Hermes - Sales Intelligence',
                  assigned_mcp_servers: ['sophia_web_search', 'sophia_sales_intelligence'],
                  context: 'Market intelligence and sales performance',
                  widget_type: 'sales_performance_intelligence'
                },
                {
                  name: 'Asclepius - Client Health',
                  assigned_mcp_servers: ['sophia_business_analytics', 'sophia_business_memory'],
                  context: 'Customer health and portfolio management',
                  widget_type: 'client_health_monitor'
                },
                {
                  name: 'Athena - Strategic Operations',
                  assigned_mcp_servers: ['sophia_business_analytics', 'shared_knowledge_base'],
                  context: 'Strategic initiatives and executive decision support',
                  widget_type: 'strategic_operations_command'
                },
                {
                  name: 'Minerva - Cross-Domain Analytics',
                  assigned_mcp_servers: ['sophia_business_analytics', 'shared_database'],
                  context: 'Advanced analytics bridging business and technical domains',
                  widget_type: 'cross_domain_analytics'
                },
                {
                  name: 'Dionysus - Creative Intelligence',
                  assigned_mcp_servers: ['sophia_web_search', 'sophia_business_memory'],
                  context: 'Creative market insights and innovation opportunities',
                  widget_type: 'creative_market_intelligence'
                },
                {
                  name: 'Oracle - Natural Language Interface',
                  assigned_mcp_servers: ['shared_knowledge_base', 'sophia_business_memory'],
                  context: 'Voice-enabled conversational business intelligence',
                  widget_type: 'natural_language_interface'
                }
              ]}
            />
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
