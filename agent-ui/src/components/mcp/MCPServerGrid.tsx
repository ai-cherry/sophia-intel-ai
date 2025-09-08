'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import MCPServerCard from './MCPServerCard';
import {
  Server, Database, Activity, AlertTriangle, CheckCircle,
  Zap, Shield, Eye, Settings, RefreshCw, Filter
} from 'lucide-react';

// ==================== MCP SERVER GRID COMPONENT ====================

interface MythologyAgentMapping {
  name: string;
  assigned_mcp_servers: string[];
  context: string;
  widget_type: string;
}

interface DomainMetrics {
  total_servers: number;
  operational_servers: number;
  total_connections: number;
  avg_response_time: number;
  error_rate: number;
}

interface MCPServerGridProps {
  domain: 'artemis' | 'sophia' | 'shared';
  servers: any[];
  mythology_agents?: MythologyAgentMapping[];
  onServerSelect?: (server: any) => void;
  refreshInterval?: number;
}

export const MCPServerGrid: React.FC<MCPServerGridProps> = ({
  domain,
  servers: initialServers,
  mythology_agents = [],
  onServerSelect,
  refreshInterval = 30000
}) => {
  const [servers, setServers] = useState(initialServers);
  const [selectedServer, setSelectedServer] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'compact' | 'list'>('grid');
  const [filterStatus, setFilterStatus] = useState<'all' | 'operational' | 'degraded' | 'offline'>('all');
  const [isLoading, setIsLoading] = useState(false);
  const [lastRefresh, setLastRefresh] = useState(new Date());

  // Auto-refresh server status
  useEffect(() => {
    const interval = setInterval(async () => {
      await refreshServerStatus();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [refreshInterval]);

  const refreshServerStatus = async () => {
    setIsLoading(true);
    try {
      // Simulate API call to refresh server status
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Update servers with simulated status changes
      setServers(prev => prev.map(server => ({
        ...server,
        performance_metrics: {
          ...server.performance_metrics,
          response_time_ms: Math.max(10, server.performance_metrics.response_time_ms + (Math.random() - 0.5) * 20),
          throughput_ops_per_sec: Math.max(0, server.performance_metrics.throughput_ops_per_sec + (Math.random() - 0.5) * 100),
        },
        connections: {
          ...server.connections,
          active: Math.min(server.connections.max, Math.max(0, server.connections.active + Math.floor((Math.random() - 0.5) * 3)))
        }
      })));

      setLastRefresh(new Date());
    } catch (error) {
      console.error('Failed to refresh server status:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getDomainTheme = (domain: string) => {
    switch (domain) {
      case 'artemis':
        return {
          title: 'ARTEMIS TECHNICAL SERVERS',
          subtitle: 'Code Excellence & Technical Operations',
          gradient: 'from-green-500 to-teal-500',
          bg: 'bg-gray-950',
          text: 'text-white',
          accent: 'text-green-400',
          headerBg: 'bg-gray-900'
        };
      case 'sophia':
        return {
          title: 'SOPHIA BUSINESS INTELLIGENCE',
          subtitle: 'Pay Ready Operations & Market Intelligence',
          gradient: 'from-blue-500 to-purple-500',
          bg: 'bg-gradient-to-br from-gray-50 to-blue-50 dark:from-gray-900 dark:to-blue-950',
          text: 'text-gray-900 dark:text-white',
          accent: 'text-blue-600 dark:text-blue-400',
          headerBg: 'bg-white/80 dark:bg-gray-900/80'
        };
      case 'shared':
        return {
          title: 'SHARED INFRASTRUCTURE',
          subtitle: 'Cross-Domain Resources & Services',
          gradient: 'from-indigo-500 to-purple-500',
          bg: 'bg-gray-100 dark:bg-gray-900',
          text: 'text-gray-900 dark:text-white',
          accent: 'text-indigo-600 dark:text-indigo-400',
          headerBg: 'bg-white dark:bg-gray-800'
        };
      default:
        return {
          title: 'MCP SERVERS',
          subtitle: 'Server Infrastructure',
          gradient: 'from-gray-500 to-gray-600',
          bg: 'bg-white dark:bg-gray-900',
          text: 'text-gray-900 dark:text-white',
          accent: 'text-gray-600 dark:text-gray-400',
          headerBg: 'bg-white dark:bg-gray-800'
        };
    }
  };

  const theme = getDomainTheme(domain);

  const filteredServers = servers.filter(server => {
    if (filterStatus === 'all') return true;
    return server.status === filterStatus;
  });

  const exclusiveServers = filteredServers.filter(s => s.access_level === 'exclusive');
  const sharedServers = filteredServers.filter(s => s.access_level === 'shared');

  const calculateDomainMetrics = (): DomainMetrics => {
    const totalServers = servers.length;
    const operationalServers = servers.filter(s => s.status === 'operational').length;
    const totalConnections = servers.reduce((sum, s) => sum + s.connections.active, 0);
    const avgResponseTime = servers.reduce((sum, s) => sum + s.performance_metrics.response_time_ms, 0) / totalServers;
    const errorRate = servers.reduce((sum, s) => sum + s.performance_metrics.error_rate, 0) / totalServers;

    return {
      total_servers: totalServers,
      operational_servers: operationalServers,
      total_connections: totalConnections,
      avg_response_time: avgResponseTime,
      error_rate: errorRate
    };
  };

  const metrics = calculateDomainMetrics();

  const handleServerClick = (server: any) => {
    setSelectedServer(server.server_name === selectedServer ? null : server.server_name);
    onServerSelect?.(server);
  };

  const getAgentForServer = (serverName: string) => {
    return mythology_agents.find(agent =>
      agent.assigned_mcp_servers.includes(serverName)
    );
  };

  const renderServerGrid = (serverList: any[], title: string) => (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className={`text-lg font-semibold ${theme.text} flex items-center space-x-2`}>
          <Server className="w-5 h-5" />
          <span>{title}</span>
          <Badge variant="outline" className="ml-2">
            {serverList.length}
          </Badge>
        </h3>
      </div>

      <div className={`grid gap-4 ${
        viewMode === 'grid'
          ? 'grid-cols-1 lg:grid-cols-2 xl:grid-cols-3'
          : viewMode === 'compact'
            ? 'grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4'
            : 'grid-cols-1'
      }`}>
        {serverList.map((server) => (
          <MCPServerCard
            key={server.server_name}
            server={{
              ...server,
              mythology_agent: getAgentForServer(server.server_name)?.name
            }}
            domain={domain}
            compact={viewMode === 'compact'}
            onClick={() => handleServerClick(server)}
          />
        ))}
      </div>
    </div>
  );

  return (
    <div className={`min-h-screen ${theme.bg}`}>
      {/* Header */}
      <div className={`border-b ${theme.headerBg} backdrop-blur-lg sticky top-0 z-50`}>
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className={`w-12 h-12 rounded-lg bg-gradient-to-r ${theme.gradient} flex items-center justify-center text-white`}>
                <Server className="w-6 h-6" />
              </div>
              <div>
                <h1 className={`text-2xl font-bold ${theme.text} ${domain === 'artemis' ? 'font-mono' : ''}`}>
                  {theme.title}
                </h1>
                <p className="text-sm text-gray-500">
                  {theme.subtitle}
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              {/* Metrics Summary */}
              <div className="hidden md:flex items-center space-x-6 text-sm">
                <div className="text-center">
                  <div className={`font-bold ${theme.accent}`}>{metrics.operational_servers}/{metrics.total_servers}</div>
                  <div className="text-xs text-gray-500">Operational</div>
                </div>
                <div className="text-center">
                  <div className={`font-bold ${theme.accent}`}>{metrics.total_connections}</div>
                  <div className="text-xs text-gray-500">Connections</div>
                </div>
                <div className="text-center">
                  <div className={`font-bold ${theme.accent}`}>{metrics.avg_response_time.toFixed(0)}ms</div>
                  <div className="text-xs text-gray-500">Avg Response</div>
                </div>
              </div>

              {/* Controls */}
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={refreshServerStatus}
                  disabled={isLoading}
                  className={domain === 'artemis' ? 'font-mono' : ''}
                >
                  <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                  {isLoading ? 'Refreshing...' : 'Refresh'}
                </Button>

                <select
                  value={viewMode}
                  onChange={(e) => setViewMode(e.target.value as any)}
                  className="text-sm bg-transparent border border-gray-300 dark:border-gray-600 rounded px-2 py-1"
                >
                  <option value="grid">Grid</option>
                  <option value="compact">Compact</option>
                  <option value="list">List</option>
                </select>

                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value as any)}
                  className="text-sm bg-transparent border border-gray-300 dark:border-gray-600 rounded px-2 py-1"
                >
                  <option value="all">All Status</option>
                  <option value="operational">Operational</option>
                  <option value="degraded">Degraded</option>
                  <option value="offline">Offline</option>
                </select>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="container mx-auto px-4 py-6">
        <div className="space-y-8">
          {/* Domain Metrics Overview */}
          <Card className={theme.headerBg}>
            <CardHeader>
              <CardTitle className={theme.text}>Domain Overview</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className={`text-2xl font-bold ${theme.accent}`}>
                    {metrics.total_servers}
                  </div>
                  <div className="text-sm text-gray-500">Total Servers</div>
                </div>
                <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className={`text-2xl font-bold ${
                    metrics.operational_servers === metrics.total_servers ? 'text-green-500' : 'text-yellow-500'
                  }`}>
                    {metrics.operational_servers}
                  </div>
                  <div className="text-sm text-gray-500">Operational</div>
                </div>
                <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className={`text-2xl font-bold ${theme.accent}`}>
                    {metrics.total_connections}
                  </div>
                  <div className="text-sm text-gray-500">Active Connections</div>
                </div>
                <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className={`text-2xl font-bold ${
                    metrics.error_rate < 0.01 ? 'text-green-500' : 'text-red-500'
                  }`}>
                    {(metrics.error_rate * 100).toFixed(2)}%
                  </div>
                  <div className="text-sm text-gray-500">Error Rate</div>
                </div>
              </div>
              <div className="mt-4 text-xs text-gray-500">
                Last refreshed: {lastRefresh.toLocaleTimeString()}
              </div>
            </CardContent>
          </Card>

          {/* Exclusive Servers */}
          {exclusiveServers.length > 0 && (
            <div>
              {renderServerGrid(
                exclusiveServers,
                domain === 'artemis' ? 'TECHNICAL OPERATIONS' :
                domain === 'sophia' ? 'BUSINESS INTELLIGENCE' : 'EXCLUSIVE SERVICES'
              )}
            </div>
          )}

          {/* Shared Resources */}
          {sharedServers.length > 0 && (
            <div>
              {renderServerGrid(sharedServers, 'SHARED RESOURCES')}
            </div>
          )}

          {/* Mythology Agents Integration */}
          {mythology_agents.length > 0 && (
            <Card className={theme.headerBg}>
              <CardHeader>
                <CardTitle className={theme.text}>Mythology Agent Orchestration</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {mythology_agents.map((agent) => (
                    <div key={agent.name} className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                      <h4 className={`font-semibold ${theme.text} mb-2`}>{agent.name}</h4>
                      <p className="text-sm text-gray-500 mb-3">{agent.context}</p>
                      <div className="space-y-1">
                        {agent.assigned_mcp_servers.map((serverName) => (
                          <Badge key={serverName} variant="outline" className="text-xs mr-1 mb-1">
                            {serverName.replace(/_/g, ' ')}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default MCPServerGrid;
