/**
 * MCP Server Visualization for Artemis Technical Dashboard
 * Provides comprehensive technical monitoring and visualization of MCP servers
 * Focus: Code quality, technical debt, system performance, and development metrics
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
  Server,
  Activity,
  Code,
  Database,
  Search,
  FileText,
  Cpu,
  MemoryStick,
  Network,
  AlertTriangle,
  CheckCircle,
  XCircle,
  TrendingUp,
  TrendingDown,
  Zap,
  Settings,
  RefreshCw,
  Eye,
  Shield,
  GitBranch,
  TestTube,
  BarChart3,
  Clock,
  Layers,
  Hash
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
}

// ==================== ARTEMIS MCP SERVER VISUALIZATION ====================

const MCPServerVisualization: React.FC = () => {
  const [selectedServer, setSelectedServer] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'list' | 'topology'>('grid');
  const [refreshInterval, setRefreshInterval] = useState(30);

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
    restartServer,
    criticalServers,
    subscribeToChannel,
    unsubscribeFromChannel
  } = useMCPStatus({
    domain: 'artemis',
    autoConnect: true,
    subscriptions: ['mcp_domain_artemis', 'mcp_artemis_servers', 'mcp_mythology_agents']
  });

  // Filter Artemis servers
  const artemisServers = servers.filter(server => server.domain === 'artemis');
  const artemisAgents = mythologyAgentsByDomain.artemis || [];

  // ==================== SERVER TYPE MAPPING ====================

  const getServerTypeIcon = (serverType: string) => {
    const iconMap: Record<string, React.ReactNode> = {
      'filesystem': <FileText className="w-5 h-5" />,
      'code_analysis': <Code className="w-5 h-5" />,
      'design_server': <Layers className="w-5 h-5" />,
      'database': <Database className="w-5 h-5" />,
      'indexing': <Search className="w-5 h-5" />,
      'embedding': <Hash className="w-5 h-5" />,
      'meta_tagging': <GitBranch className="w-5 h-5" />,
      'chunking': <TestTube className="w-5 h-5" />
    };
    return iconMap[serverType] || <Server className="w-5 h-5" />;
  };

  const getBusinessContextDisplay = (context?: string) => {
    const contextMap: Record<string, string> = {
      'code_repository_management': 'Code Repository Management',
      'technical_debt_monitoring': 'Technical Debt Monitoring',
      'architecture_documentation': 'Architecture Documentation',
      'technical_metrics_storage': 'Technical Metrics Storage',
      'code_search_optimization': 'Code Search Optimization',
      'code_similarity_analysis': 'Code Similarity Analysis',
      'technical_operations': 'Technical Operations',
      'performance_optimization': 'Performance Optimization'
    };
    return context ? contextMap[context] || context : 'Technical Infrastructure';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'operational': return 'text-green-600 bg-green-50 dark:bg-green-900/20';
      case 'degraded': return 'text-yellow-600 bg-yellow-50 dark:bg-yellow-900/20';
      case 'down': return 'text-red-600 bg-red-50 dark:bg-red-900/20';
      default: return 'text-gray-600 bg-gray-50 dark:bg-gray-900/20';
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

  // ==================== PERFORMANCE METRICS HELPERS ====================

  const getPerformanceRating = (server: MCPServerHealth) => {
    const responseScore = server.response_time_ms < 100 ? 100 :
                         server.response_time_ms < 500 ? 80 : 60;
    const uptimeScore = server.uptime_percentage;
    const errorScore = server.error_rate < 0.01 ? 100 :
                      server.error_rate < 0.05 ? 80 : 60;

    return Math.round((responseScore + uptimeScore + errorScore) / 3);
  };

  const getThroughputTrend = (throughput: number) => {
    if (throughput > 100) return { icon: <TrendingUp className="w-4 h-4 text-green-500" />, status: 'high' };
    if (throughput > 50) return { icon: <Activity className="w-4 h-4 text-blue-500" />, status: 'normal' };
    return { icon: <TrendingDown className="w-4 h-4 text-yellow-500" />, status: 'low' };
  };

  // ==================== SERVER CARD COMPONENT ====================

  const ServerCard: React.FC<{ server: MCPServerHealth }> = ({ server }) => {
    const performanceRating = getPerformanceRating(server);
    const throughputTrend = getThroughputTrend(server.throughput_ops_per_sec);

    return (
      <Card
        className={`cursor-pointer transition-all hover:shadow-lg hover:scale-105 ${
          selectedServer === server.server_name ? 'ring-2 ring-blue-500' : ''
        }`}
        onClick={() => setSelectedServer(
          selectedServer === server.server_name ? null : server.server_name
        )}
      >
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center text-white">
                {getServerTypeIcon(server.server_type)}
              </div>
              <div>
                <CardTitle className="text-sm font-medium">
                  {server.server_name.replace(/_/g, ' ').toUpperCase()}
                </CardTitle>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {getBusinessContextDisplay(server.business_context)}
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
          {/* Performance Metrics */}
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-600">Performance</span>
                <span className="font-medium">{performanceRating}%</span>
              </div>
              <Progress value={performanceRating} className="h-1.5" />
            </div>

            <div className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-600">Utilization</span>
                <span className="font-medium">{Math.round(server.connections.utilization * 100)}%</span>
              </div>
              <Progress value={server.connections.utilization * 100} className="h-1.5" />
            </div>
          </div>

          {/* Key Metrics */}
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800 rounded">
              <div className="flex items-center space-x-2">
                <Clock className="w-3 h-3 text-blue-500" />
                <span>Response</span>
              </div>
              <span className="font-medium">{server.response_time_ms}ms</span>
            </div>

            <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800 rounded">
              <div className="flex items-center space-x-2">
                {throughputTrend.icon}
                <span>Throughput</span>
              </div>
              <span className="font-medium">{server.throughput_ops_per_sec}/sec</span>
            </div>

            <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800 rounded">
              <div className="flex items-center space-x-2">
                <Network className="w-3 h-3 text-green-500" />
                <span>Uptime</span>
              </div>
              <span className="font-medium">{server.uptime_percentage.toFixed(1)}%</span>
            </div>

            <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800 rounded">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="w-3 h-3 text-red-500" />
                <span>Errors</span>
              </div>
              <span className="font-medium">{(server.error_rate * 100).toFixed(2)}%</span>
            </div>
          </div>

          {/* Connection Info */}
          <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between text-xs text-gray-600">
              <span>Connections: {server.connections.active}/{server.connections.max}</span>
              <span>Last activity: {server.last_activity}</span>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  // ==================== MYTHOLOGY AGENTS SECTION ====================

  const MythologyAgentsSection: React.FC = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold flex items-center space-x-2">
          <Shield className="w-5 h-5 text-purple-500" />
          <span>Mythology Agents - Technical Command</span>
        </h3>
        <Badge variant="outline">{artemisAgents.length} Active</Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {artemisAgents.map((agent) => (
          <Card key={agent.id} className="border-purple-200 dark:border-purple-800">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base">{agent.name}</CardTitle>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{agent.title}</p>
                </div>
                <Badge className="bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-100">
                  {agent.status}
                </Badge>
              </div>
            </CardHeader>

            <CardContent>
              {/* Primary Metric */}
              <div className="mb-4 p-3 bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 rounded-lg">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">{agent.primary_metric.label}</span>
                  <div className="flex items-center space-x-2">
                    <span className="text-lg font-bold text-purple-600">
                      {agent.primary_metric.value}
                    </span>
                    {agent.primary_metric.trend === 'up' && <TrendingUp className="w-4 h-4 text-green-500" />}
                    {agent.primary_metric.trend === 'down' && <TrendingDown className="w-4 h-4 text-red-500" />}
                    {agent.primary_metric.trend === 'stable' && <Activity className="w-4 h-4 text-blue-500" />}
                  </div>
                </div>
              </div>

              {/* Assigned Servers */}
              <div className="space-y-2">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Assigned MCP Servers:
                </span>
                <div className="space-y-1">
                  {agent.assigned_mcp_servers.map((serverName) => {
                    const server = artemisServers.find(s => s.server_name === serverName);
                    return (
                      <div key={serverName} className="flex items-center justify-between text-xs p-2 bg-gray-50 dark:bg-gray-800 rounded">
                        <div className="flex items-center space-x-2">
                          {server && getServerTypeIcon(server.server_type)}
                          <span>{serverName.replace(/_/g, ' ')}</span>
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
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  // ==================== DETAILED SERVER VIEW ====================

  const DetailedServerView: React.FC<{ serverName: string }> = ({ serverName }) => {
    const server = artemisServers.find(s => s.server_name === serverName);
    if (!server) return null;

    return (
      <Card className="border-blue-200 dark:border-blue-800">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 rounded-lg bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center text-white">
                {getServerTypeIcon(server.server_type)}
              </div>
              <div>
                <CardTitle className="text-xl">
                  {server.server_name.replace(/_/g, ' ').toUpperCase()}
                </CardTitle>
                <p className="text-gray-600 dark:text-gray-400">
                  {getBusinessContextDisplay(server.business_context)}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => restartServer(server.server_name)}
                className="flex items-center space-x-1"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Restart</span>
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedServer(null)}
              >
                <Eye className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Performance Metrics */}
            <div className="space-y-3">
              <h4 className="font-semibold text-sm flex items-center space-x-2">
                <BarChart3 className="w-4 h-4" />
                <span>Performance</span>
              </h4>
              <div className="space-y-2">
                <div>
                  <div className="flex justify-between text-sm">
                    <span>Response Time</span>
                    <span className="font-medium">{server.response_time_ms}ms</span>
                  </div>
                  <Progress value={Math.min(100, Math.max(0, 100 - (server.response_time_ms / 10)))} className="h-2" />
                </div>
                <div>
                  <div className="flex justify-between text-sm">
                    <span>Throughput</span>
                    <span className="font-medium">{server.throughput_ops_per_sec}/sec</span>
                  </div>
                  <Progress value={Math.min(100, server.throughput_ops_per_sec)} className="h-2" />
                </div>
              </div>
            </div>

            {/* Reliability Metrics */}
            <div className="space-y-3">
              <h4 className="font-semibold text-sm flex items-center space-x-2">
                <Shield className="w-4 h-4" />
                <span>Reliability</span>
              </h4>
              <div className="space-y-2">
                <div>
                  <div className="flex justify-between text-sm">
                    <span>Uptime</span>
                    <span className="font-medium">{server.uptime_percentage.toFixed(1)}%</span>
                  </div>
                  <Progress value={server.uptime_percentage} className="h-2" />
                </div>
                <div>
                  <div className="flex justify-between text-sm">
                    <span>Error Rate</span>
                    <span className="font-medium">{(server.error_rate * 100).toFixed(2)}%</span>
                  </div>
                  <Progress value={100 - (server.error_rate * 100)} className="h-2" />
                </div>
              </div>
            </div>

            {/* Resource Utilization */}
            <div className="space-y-3">
              <h4 className="font-semibold text-sm flex items-center space-x-2">
                <Cpu className="w-4 h-4" />
                <span>Resources</span>
              </h4>
              <div className="space-y-2">
                <div>
                  <div className="flex justify-between text-sm">
                    <span>Connections</span>
                    <span className="font-medium">{server.connections.active}/{server.connections.max}</span>
                  </div>
                  <Progress value={server.connections.utilization * 100} className="h-2" />
                </div>
                <div>
                  <div className="flex justify-between text-sm">
                    <span>Utilization</span>
                    <span className="font-medium">{Math.round(server.connections.utilization * 100)}%</span>
                  </div>
                  <Progress value={server.connections.utilization * 100} className="h-2" />
                </div>
              </div>
            </div>

            {/* Status Information */}
            <div className="space-y-3">
              <h4 className="font-semibold text-sm flex items-center space-x-2">
                <Activity className="w-4 h-4" />
                <span>Status</span>
              </h4>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Current Status</span>
                  <Badge className={getStatusColor(server.status)}>
                    {getStatusIcon(server.status)}
                    <span className="ml-1">{server.status}</span>
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Last Activity</span>
                  <span className="text-sm font-medium">{server.last_activity}</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  // ==================== MAIN RENDER ====================

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-center h-64">
          <div className="flex items-center space-x-2">
            <RefreshCw className="w-5 h-5 animate-spin" />
            <span>Loading MCP server status...</span>
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
          Failed to load MCP server status: {error}
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
            <Server className="w-6 h-6 text-purple-600" />
            <span>Artemis MCP Server Command Center</span>
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Technical infrastructure monitoring for code quality, architecture, and development operations
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 text-sm">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
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

      {/* Domain Health Summary */}
      {domainHealth && (
        <Card className="bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 border-purple-200 dark:border-purple-800">
          <CardContent className="pt-6">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-purple-600">{domainHealth.total_servers}</div>
                <div className="text-sm text-gray-600">Total Servers</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-green-600">{domainHealth.operational_servers}</div>
                <div className="text-sm text-gray-600">Operational</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-yellow-600">{domainHealth.degraded_servers}</div>
                <div className="text-sm text-gray-600">Degraded</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-blue-600">{domainHealth.avg_response_time_ms.toFixed(0)}ms</div>
                <div className="text-sm text-gray-600">Avg Response</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-purple-600">{domainHealth.overall_health_score.toFixed(1)}%</div>
                <div className="text-sm text-gray-600">Health Score</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Critical Alerts */}
      {criticalServers.length > 0 && (
        <Alert>
          <AlertTriangle className="w-4 h-4" />
          <AlertDescription>
            <strong>{criticalServers.length} server(s)</strong> require attention: {' '}
            {criticalServers.map(s => s.server_name).join(', ')}
          </AlertDescription>
        </Alert>
      )}

      {/* Main Content */}
      <Tabs defaultValue="servers" className="space-y-6">
        <TabsList className="grid grid-cols-3 w-full max-w-md">
          <TabsTrigger value="servers">
            <Server className="w-4 h-4 mr-2" />
            Servers
          </TabsTrigger>
          <TabsTrigger value="agents">
            <Shield className="w-4 h-4 mr-2" />
            Agents
          </TabsTrigger>
          <TabsTrigger value="topology">
            <Network className="w-4 h-4 mr-2" />
            Topology
          </TabsTrigger>
        </TabsList>

        <TabsContent value="servers" className="space-y-6">
          {/* Server Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {artemisServers.map((server) => (
              <ServerCard key={server.server_name} server={server} />
            ))}
          </div>

          {/* Detailed Server View */}
          {selectedServer && (
            <div className="space-y-4">
              <Separator />
              <DetailedServerView serverName={selectedServer} />
            </div>
          )}
        </TabsContent>

        <TabsContent value="agents">
          <MythologyAgentsSection />
        </TabsContent>

        <TabsContent value="topology">
          <Card>
            <CardHeader>
              <CardTitle>MCP Server Topology</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">
                Interactive topology visualization will be implemented in future versions.
                This will show MCP server relationships, data flow, and dependency mapping.
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default MCPServerVisualization;
