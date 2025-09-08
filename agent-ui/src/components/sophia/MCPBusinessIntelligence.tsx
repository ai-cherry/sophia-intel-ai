/**
 * MCP Business Intelligence Component for Sophia Dashboard
 * Provides comprehensive business-focused monitoring of MCP servers
 * Focus: Pay Ready operations, revenue analytics, client health, and business metrics
 */

'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import useMCPStatus from '@/hooks/useMCPStatus';
import {
  Building2,
  DollarSign,
  TrendingUp,
  TrendingDown,
  Activity,
  Users,
  Target,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Heart,
  Zap,
  Eye,
  Search,
  Database,
  BarChart3,
  PieChart,
  RefreshCw,
  Clock,
  Shield,
  Globe,
  Home,
  Briefcase,
  UserCheck,
  Calendar,
  Award,
  Lightbulb,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  MapPin,
  CreditCard,
  FileText,
  Bell
} from 'lucide-react';

// ==================== TYPES ====================

interface MCPServerHealth {
  server_name: string;
  server_type: string;
  domain: string;
  status: 'operational' | 'degraded' | 'down' | 'unknown';
  uptime_percentage: number;
  response_time_ms: number;
  throughput_ops_per_sec: number;
  error_rate: number;
  last_activity: string;
  connections: {
    active: number;
    max: number;
    utilization: number;
  };
  business_context?: string;
}

interface MythologyAgent {
  id: string;
  name: string;
  domain: string;
  title: string;
  assigned_mcp_servers: string[];
  status: string;
  primary_metric: {
    label: string;
    value: string;
    trend: 'up' | 'down' | 'stable';
  };
  pay_ready_context?: string;
}

interface BusinessMetric {
  label: string;
  value: string | number;
  trend: 'up' | 'down' | 'stable';
  change: string;
  context: string;
}

// ==================== SOPHIA MCP BUSINESS INTELLIGENCE ====================

const MCPBusinessIntelligence: React.FC = () => {
  const [selectedView, setSelectedView] = useState<'overview' | 'agents' | 'operations' | 'intelligence'>('overview');
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [alertsExpanded, setAlertsExpanded] = useState(false);

  const {
    overview,
    servers,
    domainHealth,
    mythologyAgentsByDomain,
    isConnected,
    isLoading,
    error,
    lastUpdate,
    refreshData,
    criticalServers,
    subscribeToChannel,
    unsubscribeFromChannel
  } = useMCPStatus({
    domain: 'sophia',
    autoConnect: true,
    subscriptions: ['mcp_domain_sophia', 'mcp_business_intelligence', 'sophia_pay_ready', 'operational_intelligence']
  });

  // Filter Sophia servers and agents;
  const sophiaServers = servers.filter(server => server.domain === 'sophia');
  const sophiaAgents = mythologyAgentsByDomain.sophia || [];

  // ==================== BUSINESS CONTEXT MAPPING ====================

  const getServerBusinessIcon = (serverName: string, serverType: string) => {
    const iconMap: Record<string, React.ReactNode> = {
      'sophia_web_search': <Search className="w-5 h-5" />,
      'sophia_analytics': <BarChart3 className="w-5 h-5" />,
      'sophia_sales_intelligence': <Target className="w-5 h-5" />,
      'sophia_business_memory': <Database className="w-5 h-5" />,
      'shared_database': <Database className="w-5 h-5" />,
      'shared_indexing': <Search className="w-5 h-5" />,
      'shared_embedding': <Lightbulb className="w-5 h-5" />
    };

    if (iconMap[serverName]) return iconMap[serverName];

    const typeIconMap: Record<string, React.ReactNode> = {
      'web_search': <Globe className="w-5 h-5" />,
      'business_analytics': <PieChart className="w-5 h-5" />,
      'sales_intelligence': <TrendingUp className="w-5 h-5" />,
      'database': <Database className="w-5 h-5" />
    };

    return typeIconMap[serverType] || <Building2 className="w-5 h-5" />;
  };

  const getBusinessContextDisplay = (context?: string) => {
    const contextMap: Record<string, { title: string; description: string; icon: React.ReactNode }> = {
      'market_intelligence_gathering': {
        title: 'Market Intelligence',
        description: 'Real-time market data and competitive analysis for property management',
        icon: <Globe className="w-4 h-4" />
      },
      'pay_ready_operations': {
        title: 'Pay Ready Operations',
        description: 'Core rent processing and property management operations',
        icon: <CreditCard className="w-4 h-4" />
      },
      'property_sales_optimization': {
        title: 'Property Sales Intelligence',
        description: 'Sales performance and property acquisition optimization',
        icon: <Home className="w-4 h-4" />
      },
      'tenant_landlord_satisfaction': {
        title: 'Client Satisfaction',
        description: 'Tenant and landlord satisfaction monitoring',
        icon: <Heart className="w-4 h-4" />
      },
      'business_metrics_storage': {
        title: 'Business Data Management',
        description: 'Critical business metrics and analytics storage',
        icon: <Database className="w-4 h-4" />
      },
      'business_search_optimization': {
        title: 'Business Intelligence Search',
        description: 'Optimized search for business insights and analytics',
        icon: <Search className="w-4 h-4" />
      },
      'business_similarity_analysis': {
        title: 'Pattern Recognition',
        description: 'Business pattern analysis and predictive insights',
        icon: <Lightbulb className="w-4 h-4" />
      }
    };

    return context ? contextMap[context] || {
      title: 'Business Operations',
      description: 'General business intelligence operations',
      icon: <Building2 className="w-4 h-4" />
    } : {
      title: 'Business Intelligence',
      description: 'Strategic business operations and analytics',
      icon: <Building2 className="w-4 h-4" />
    };
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'operational': return 'text-green-600 bg-green-50 dark:bg-green-900/20 border-green-200';
      case 'degraded': return 'text-yellow-600 bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200';
      case 'down': return 'text-red-600 bg-red-50 dark:bg-red-900/20 border-red-200';
      default: return 'text-gray-600 bg-gray-50 dark:bg-gray-900/20 border-gray-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'operational': return <CheckCircle className="w-4 h-4" />;
      case 'degraded': return <AlertTriangle className="w-4 h-4" />;
      case 'down': return <XCircle className="w-4 h-4" />;
      default: return <AlertTriangle className="w-4 h-4" />;
    }
  };

  const getTrendIcon = (trend: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up': return <ArrowUpRight className="w-4 h-4 text-green-500" />;
      case 'down': return <ArrowDownRight className="w-4 h-4 text-red-500" />;
      default: return <Minus className="w-4 h-4 text-blue-500" />;
    }
  };

  // ==================== BUSINESS METRICS SIMULATION ====================

  const businessMetrics: BusinessMetric[] = useMemo(() => [
    {
      label: 'Processing Volume',
      value: '$2.1B',
      trend: 'up',
      change: '+12.3%',
      context: 'Total rent processing volume today'
    },
    {
      label: 'Market Share',
      value: '47.3%',
      trend: 'up',
      change: '+2.1%',
      context: 'Property management market penetration'
    },
    {
      label: 'Active Properties',
      value: '15,247',
      trend: 'up',
      change: '+127',
      context: 'Properties under active management'
    },
    {
      label: 'Client Satisfaction',
      value: '4.2/5',
      trend: 'stable',
      change: '0.0',
      context: 'Average tenant satisfaction rating'
    },
    {
      label: 'Compliance Score',
      value: '97.2%',
      trend: 'up',
      change: '+0.8%',
      context: 'Regulatory compliance rating'
    },
    {
      label: 'Revenue Growth',
      value: '23.4%',
      trend: 'up',
      change: '+1.2%',
      context: 'Year-over-year revenue growth'
    }
  ], []);

  // ==================== SERVER CARD COMPONENT ====================

  const BusinessServerCard: React.FC<{ server: MCPServerHealth }> = ({ server }) => {
    const businessContext = getBusinessContextDisplay(server.business_context);
    const businessImpact = getBusinessImpact(server);

    return (
      <Card className="cursor-pointer transition-all hover:shadow-lg hover:scale-105 border-blue-200 dark:border-blue-800">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-r from-blue-500 to-teal-500 flex items-center justify-center text-white">
                {getServerBusinessIcon(server.server_name, server.server_type)}
              </div>
              <div>
                <CardTitle className="text-sm font-medium">
                  {businessContext.title}
                </CardTitle>
                <p className="text-xs text-gray-500 dark:text-gray-400 line-clamp-1">
                  {businessContext.description}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Badge variant="outline" className={getStatusColor(server.status)}>
                {getStatusIcon(server.status)}
                <span className="ml-1 text-xs">{server.status.toUpperCase()}</span>
              </Badge>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          {/* Business Impact Metrics */}
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-600">Business Impact</span>
                <span className="font-medium text-green-600">{businessImpact.score}%</span>
              </div>
              <Progress value={businessImpact.score} className="h-1.5" />
            </div>

            <div className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-600">Availability</span>
                <span className="font-medium">{server.uptime_percentage.toFixed(1)}%</span>
              </div>
              <Progress value={server.uptime_percentage} className="h-1.5" />
            </div>
          </div>

          {/* Performance Indicators */}
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="flex items-center justify-between p-2 bg-blue-50 dark:bg-blue-900/20 rounded">
              <div className="flex items-center space-x-2">
                <Clock className="w-3 h-3 text-blue-500" />
                <span>Response</span>
              </div>
              <span className="font-medium">{server.response_time_ms}ms</span>
            </div>

            <div className="flex items-center justify-between p-2 bg-green-50 dark:bg-green-900/20 rounded">
              <div className="flex items-center space-x-2">
                <Activity className="w-3 h-3 text-green-500" />
                <span>Throughput</span>
              </div>
              <span className="font-medium">{server.throughput_ops_per_sec}/sec</span>
            </div>
          </div>

          {/* Business Context & Activity */}
          <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center space-x-1 text-gray-600">
                {businessContext.icon}
                <span>{businessImpact.operations} ops/hour</span>
              </div>
              <span className="text-gray-500">{server.last_activity}</span>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  // Helper function to calculate business impact;
  const getBusinessImpact = (server: MCPServerHealth) => {
    const baseScore = (server.uptime_percentage +
                     (100 - Math.min(100, server.response_time_ms / 10)) +
                     (100 - Math.min(100, server.error_rate * 1000))) / 3;

    const operations = Math.round(server.throughput_ops_per_sec * 3600);

    return {
      score: Math.round(baseScore),
      operations
    };
  };

  // ==================== MYTHOLOGY AGENTS BUSINESS VIEW ====================

  const BusinessAgentsSection: React.FC = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold flex items-center space-x-2">
          <Users className="w-5 h-5 text-blue-500" />
          <span>Business Intelligence Agents</span>
        </h3>
        <Badge variant="outline" className="bg-blue-50 text-blue-700">
          {sophiaAgents.length} Active Agents
        </Badge>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {sophiaAgents.map((agent) => (
          <Card
            key={agent.id}
            className={`border-blue-200 dark:border-blue-800 cursor-pointer transition-all hover:shadow-lg ${
              selectedAgent === agent.id ? 'ring-2 ring-blue-500' : ''
            }`}
            onClick={() => setSelectedAgent(selectedAgent === agent.id ? null : agent.id)}
          >
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-r from-blue-500 to-teal-500 flex items-center justify-center text-white text-lg font-bold">
                    {agent.name.substring(0, 2)}
                  </div>
                  <div>
                    <CardTitle className="text-base">{agent.name}</CardTitle>
                    <p className="text-sm text-gray-600 dark:text-gray-400">{agent.title}</p>
                  </div>
                </div>
                <Badge className="bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100">
                  {agent.status}
                </Badge>
              </div>
            </CardHeader>

            <CardContent>
              {/* Primary Metric with Pay Ready Context */}
              <div className="mb-4 p-4 bg-gradient-to-r from-blue-50 to-teal-50 dark:from-blue-900/20 dark:to-teal-900/20 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {agent.primary_metric.label}
                  </span>
                  {getTrendIcon(agent.primary_metric.trend)}
                </div>
                <div className="flex items-end justify-between">
                  <span className="text-2xl font-bold text-blue-600">
                    {agent.primary_metric.value}
                  </span>
                  {agent.pay_ready_context && (
                    <Badge variant="outline" className="text-xs bg-white/50">
                      Pay Ready
                    </Badge>
                  )}
                </div>
              </div>

              {/* Assigned Servers with Business Context */}
              <div className="space-y-3">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Business Operations:
                </span>
                <div className="space-y-2">
                  {agent.assigned_mcp_servers.map((serverName) => {
                    const server = sophiaServers.find(s => s.server_name === serverName);
                    const context = getBusinessContextDisplay(server?.business_context);

                    return (
                      <div key={serverName} className="flex items-center justify-between text-xs p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                        <div className="flex items-center space-x-2">
                          {context.icon}
                          <div>
                            <div className="font-medium">{context.title}</div>
                            <div className="text-gray-500">{context.description}</div>
                          </div>
                        </div>
                        {server && (
                          <Badge variant="outline" className={getStatusColor(server.status)}>
                            {server.status}
                          </Badge>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Business Impact Metrics */}
              {selectedAgent === agent.id && (
                <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div className="space-y-1">
                      <span className="text-gray-600">Daily Operations</span>
                      <span className="text-lg font-semibold text-green-600">2,847</span>
                    </div>
                    <div className="space-y-1">
                      <span className="text-gray-600">Success Rate</span>
                      <span className="text-lg font-semibold text-blue-600">98.2%</span>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  // ==================== PAY READY OPERATIONS OVERVIEW ====================

  const PayReadyOperationsOverview: React.FC = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold flex items-center space-x-2">
          <CreditCard className="w-5 h-5 text-green-500" />
          <span>Pay Ready Operations Intelligence</span>
        </h3>
        <Badge className="bg-green-100 text-green-800">Live</Badge>
      </div>

      {/* Key Business Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {businessMetrics.map((metric, index) => (
          <Card key={index} className="border-green-200 dark:border-green-800">
            <CardContent className="pt-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-600">{metric.label}</span>
                  {getTrendIcon(metric.trend)}
                </div>
                <div className="space-y-1">
                  <span className="text-lg font-bold text-green-600">{metric.value}</span>
                  <div className="text-xs text-gray-500">
                    <span className={`font-medium ${
                      metric.trend === 'up' ? 'text-green-600' :
                      metric.trend === 'down' ? 'text-red-600' : 'text-blue-600'
                    }`}>
                      {metric.change}
                    </span>
                  </div>
                </div>
                <p className="text-xs text-gray-500 line-clamp-2">{metric.context}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Operational Status */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="border-blue-200 dark:border-blue-800">
          <CardHeader>
            <CardTitle className="text-base flex items-center space-x-2">
              <Home className="w-4 h-4" />
              <span>Property Portfolio Health</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm">Total Properties</span>
                <span className="font-semibold">15,247</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Occupied Units</span>
                <span className="font-semibold text-green-600">94.2%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">At-Risk Properties</span>
                <span className="font-semibold text-yellow-600">3</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Maintenance Requests</span>
                <span className="font-semibold text-blue-600">127 pending</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-purple-200 dark:border-purple-800">
          <CardHeader>
            <CardTitle className="text-base flex items-center space-x-2">
              <Users className="w-4 h-4" />
              <span>Client Satisfaction Metrics</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm">Tenant Satisfaction</span>
                <div className="flex items-center space-x-2">
                  <span className="font-semibold">4.2/5</span>
                  <TrendingUp className="w-4 h-4 text-green-500" />
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Landlord Retention</span>
                <div className="flex items-center space-x-2">
                  <span className="font-semibold text-green-600">96.8%</span>
                  <TrendingUp className="w-4 h-4 text-green-500" />
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Support Response</span>
                <span className="font-semibold text-blue-600">&lt; 2 hours</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Issue Resolution</span>
                <span className="font-semibold text-purple-600">98.1%</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );

  // ==================== MAIN RENDER ====================

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-center h-64">
          <div className="flex items-center space-x-2">
            <RefreshCw className="w-5 h-5 animate-spin text-blue-500" />
            <span>Loading business intelligence data...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert>
        <AlertTriangle className="w-4 h-4" />
        <AlertDescription>
          Failed to load business intelligence: {error}
          <Button
            variant="outline"
            size="sm"
            onClick={refreshData}
            className="ml-2"
          >
            <RefreshCw className="w-4 h-4 mr-1" />
            Retry
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center space-x-3">
            <Building2 className="w-6 h-6 text-blue-600" />
            <span>Sophia Business Intelligence Center</span>
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Pay Ready business operations monitoring - Managing $20B+ in rent processing with AI-powered insights
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 text-sm">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span>{isConnected ? 'Live Data' : 'Offline'}</span>
          </div>

          {lastUpdate && (
            <span className="text-xs text-gray-500">
              Updated: {lastUpdate.toLocaleTimeString()}
            </span>
          )}

          <Button variant="outline" size="sm" onClick={refreshData}>
            <RefreshCw className="w-4 h-4 mr-1" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Domain Health Summary with Pay Ready Context */}
      {domainHealth && (
        <Card className="bg-gradient-to-r from-blue-50 to-teal-50 dark:from-blue-900/20 dark:to-teal-900/20 border-blue-200 dark:border-blue-800">
          <CardContent className="pt-6">
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-blue-600">{domainHealth.total_servers}</div>
                <div className="text-sm text-gray-600">MCP Services</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-green-600">{domainHealth.operational_servers}</div>
                <div className="text-sm text-gray-600">Operational</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-blue-600">{domainHealth.avg_response_time_ms.toFixed(0)}ms</div>
                <div className="text-sm text-gray-600">Avg Response</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-purple-600">{domainHealth.overall_health_score.toFixed(1)}%</div>
                <div className="text-sm text-gray-600">Health Score</div>
              </div>
              {domainHealth.pay_ready_context && (
                <>
                  <div>
                    <div className="text-2xl font-bold text-green-600">
                      ${(domainHealth.pay_ready_context.processing_volume_today! / 1000000000).toFixed(1)}B
                    </div>
                    <div className="text-sm text-gray-600">Processing Volume</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-teal-600">
                      {domainHealth.pay_ready_context.market_share}%
                    </div>
                    <div className="text-sm text-gray-600">Market Share</div>
                  </div>
                </>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Critical Business Alerts */}
      {criticalServers.length > 0 && (
        <Alert>
          <Bell className="w-4 h-4" />
          <AlertDescription>
            <strong>Business Critical:</strong> {criticalServers.length} service(s) affecting operations: {' '}
            {criticalServers.map(s => getBusinessContextDisplay(s.business_context).title).join(', ')}
          </AlertDescription>
        </Alert>
      )}

      {/* Main Content Tabs */}
      <Tabs value={selectedView} onValueChange={(value: unknown) => setSelectedView(value)} className="space-y-6">
        <TabsList className="grid grid-cols-4 w-full max-w-2xl">
          <TabsTrigger value="overview">
            <Eye className="w-4 h-4 mr-2" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="operations">
            <CreditCard className="w-4 h-4 mr-2" />
            Pay Ready
          </TabsTrigger>
          <TabsTrigger value="agents">
            <Users className="w-4 h-4 mr-2" />
            AI Agents
          </TabsTrigger>
          <TabsTrigger value="intelligence">
            <Lightbulb className="w-4 h-4 mr-2" />
            Intelligence
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Business Server Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {sophiaServers.map((server) => (
              <BusinessServerCard key={server.server_name} server={server} />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="operations">
          <PayReadyOperationsOverview />
        </TabsContent>

        <TabsContent value="agents">
          <BusinessAgentsSection />
        </TabsContent>

        <TabsContent value="intelligence">
          <Card>
            <CardHeader>
              <CardTitle>Operational Intelligence Hub</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">
                Advanced business intelligence features including predictive analytics,
                market trend analysis, and automated insights will be available in future versions.
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default MCPBusinessIntelligence;