'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import {
  Server, Database, Code, Search, BarChart3, Brain, Zap, Shield,
  CheckCircle, AlertTriangle, XCircle, Activity, Eye, Settings,
  Clock, TrendingUp, TrendingDown, Minus
} from 'lucide-react';

// ==================== MCP SERVER VISUALIZATION COMPONENT ====================

interface MCPServerMetrics {
  response_time_ms: number;
  throughput_ops_per_sec: number;
  error_rate: number;
  uptime_percentage: number;
}

interface ConnectionPool {
  active: number;
  max: number;
  utilization: number;
}

interface MCPServerStatus {
  server_name: string;
  server_type: 'filesystem' | 'code_analysis' | 'design_server' | 'codebase_memory' |
               'web_search' | 'business_analytics' | 'sales_intelligence' | 'business_memory' |
               'database' | 'knowledge_base' | 'indexing' | 'embedding' | 'meta_tagging' | 'chunking';
  status: 'operational' | 'degraded' | 'offline';
  domain: 'artemis' | 'sophia' | 'shared';
  access_level: 'exclusive' | 'shared';
  connections: ConnectionPool;
  capabilities: string[];
  last_activity: string;
  performance_metrics: MCPServerMetrics;
  business_context?: string;
  mythology_agent?: string;
}

interface MCPServerCardProps {
  server: MCPServerStatus;
  domain: 'artemis' | 'sophia' | 'shared';
  compact?: boolean;
  onClick?: () => void;
}

export const MCPServerCard: React.FC<MCPServerCardProps> = ({
  server,
  domain,
  compact = false,
  onClick
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [liveMetrics, setLiveMetrics] = useState(server.performance_metrics);

  // Simulate live metrics updates
  useEffect(() => {
    const interval = setInterval(() => {
      setLiveMetrics(prev => ({
        ...prev,
        response_time_ms: Math.max(10, prev.response_time_ms + (Math.random() - 0.5) * 20),
        throughput_ops_per_sec: Math.max(0, prev.throughput_ops_per_sec + (Math.random() - 0.5) * 100),
        error_rate: Math.max(0, Math.min(1, prev.error_rate + (Math.random() - 0.5) * 0.01))
      }));
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  const getServerIcon = (type: string) => {
    const iconMap = {
      filesystem: <Server className="w-5 h-5" />,
      code_analysis: <Code className="w-5 h-5" />,
      design_server: <Brain className="w-5 h-5" />,
      codebase_memory: <Database className="w-5 h-5" />,
      web_search: <Search className="w-5 h-5" />,
      business_analytics: <BarChart3 className="w-5 h-5" />,
      sales_intelligence: <TrendingUp className="w-5 h-5" />,
      business_memory: <Database className="w-5 h-5" />,
      database: <Database className="w-5 h-5" />,
      knowledge_base: <Brain className="w-5 h-5" />,
      indexing: <Search className="w-5 h-5" />,
      embedding: <Zap className="w-5 h-5" />,
      meta_tagging: <Shield className="w-5 h-5" />,
      chunking: <Activity className="w-5 h-5" />
    };
    return iconMap[type as keyof typeof iconMap] || <Server className="w-5 h-5" />;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'operational':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'degraded':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      case 'offline':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <AlertTriangle className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'operational': return 'text-green-500';
      case 'degraded': return 'text-yellow-500';
      case 'offline': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  const getDomainTheme = (domain: string) => {
    switch (domain) {
      case 'artemis':
        return {
          gradient: 'from-green-500 to-teal-500',
          bg: 'bg-gray-900',
          border: 'border-gray-700',
          text: 'text-gray-100',
          accent: 'text-green-400'
        };
      case 'sophia':
        return {
          gradient: 'from-blue-500 to-purple-500',
          bg: 'bg-white dark:bg-gray-800',
          border: 'border-gray-200 dark:border-gray-600',
          text: 'text-gray-900 dark:text-gray-100',
          accent: 'text-blue-600 dark:text-blue-400'
        };
      case 'shared':
        return {
          gradient: 'from-indigo-500 to-purple-500',
          bg: 'bg-gray-50 dark:bg-gray-800',
          border: 'border-gray-200 dark:border-gray-600',
          text: 'text-gray-900 dark:text-gray-100',
          accent: 'text-indigo-600 dark:text-indigo-400'
        };
      default:
        return {
          gradient: 'from-gray-500 to-gray-600',
          bg: 'bg-white dark:bg-gray-800',
          border: 'border-gray-200 dark:border-gray-600',
          text: 'text-gray-900 dark:text-gray-100',
          accent: 'text-gray-600 dark:text-gray-400'
        };
    }
  };

  const theme = getDomainTheme(domain);
  const utilizationColor = server.connections.utilization > 0.8
    ? 'text-red-500'
    : server.connections.utilization > 0.6
      ? 'text-yellow-500'
      : 'text-green-500';

  const formatServerName = (name: string) => {
    return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const getTrendIcon = (current: number, threshold: number) => {
    if (current > threshold * 1.1) return <TrendingUp className="w-3 h-3 text-red-400" />;
    if (current < threshold * 0.9) return <TrendingDown className="w-3 h-3 text-green-400" />;
    return <Minus className="w-3 h-3 text-gray-400" />;
  };

  if (compact) {
    return (
      <Card
        className={`${theme.bg} ${theme.border} cursor-pointer transition-all hover:shadow-lg hover:scale-105`}
        onClick={() => {
          setIsExpanded(!isExpanded);
          onClick?.();
        }}
      >
        <CardContent className="p-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className={`w-8 h-8 rounded-lg bg-gradient-to-r ${theme.gradient} flex items-center justify-center text-white`}>
                {getServerIcon(server.server_type)}
              </div>
              <div>
                <div className={`text-sm font-medium ${theme.text}`}>
                  {formatServerName(server.server_name)}
                </div>
                <div className="text-xs text-gray-500">
                  {server.access_level} • {server.connections.active}/{server.connections.max}
                </div>
              </div>
            </div>
            {getStatusIcon(server.status)}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card
      className={`${theme.bg} ${theme.border} transition-all hover:shadow-xl ${
        onClick ? 'cursor-pointer hover:scale-105' : ''
      } ${isExpanded ? 'ring-2 ring-blue-500' : ''}`}
      onClick={onClick}
    >
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`w-12 h-12 rounded-lg bg-gradient-to-r ${theme.gradient} flex items-center justify-center text-white`}>
              {getServerIcon(server.server_type)}
            </div>
            <div>
              <CardTitle className={`text-lg ${theme.text}`}>
                {formatServerName(server.server_name)}
              </CardTitle>
              <div className="flex items-center space-x-2 mt-1">
                <Badge
                  variant={server.access_level === 'exclusive' ? 'default' : 'secondary'}
                  className="text-xs"
                >
                  {server.access_level}
                </Badge>
                {server.mythology_agent && (
                  <Badge variant="outline" className="text-xs">
                    {server.mythology_agent}
                  </Badge>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {getStatusIcon(server.status)}
            <span className={`font-bold text-sm ${getStatusColor(server.status)}`}>
              {server.status.toUpperCase()}
            </span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Connection Pool Status */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <span className={`text-sm font-medium ${theme.text}`}>Connection Pool</span>
            <span className={`text-sm font-mono ${utilizationColor}`}>
              {server.connections.active}/{server.connections.max}
            </span>
          </div>
          <Progress
            value={server.connections.utilization * 100}
            className="h-2"
          />
          <div className="text-xs text-gray-500 mt-1">
            {(server.connections.utilization * 100).toFixed(1)}% utilization
          </div>
        </div>

        {/* Performance Metrics */}
        <div className="grid grid-cols-3 gap-3 text-sm">
          <div className="text-center p-2 bg-gray-50 dark:bg-gray-700 rounded">
            <div className="flex items-center justify-center space-x-1">
              <Clock className="w-3 h-3" />
              {getTrendIcon(liveMetrics.response_time_ms, server.performance_metrics.response_time_ms)}
            </div>
            <div className={`font-bold ${theme.accent}`}>
              {liveMetrics.response_time_ms.toFixed(0)}ms
            </div>
            <div className="text-xs text-gray-500">Response</div>
          </div>

          <div className="text-center p-2 bg-gray-50 dark:bg-gray-700 rounded">
            <div className="flex items-center justify-center space-x-1">
              <Activity className="w-3 h-3" />
              {getTrendIcon(liveMetrics.throughput_ops_per_sec, server.performance_metrics.throughput_ops_per_sec)}
            </div>
            <div className={`font-bold ${theme.accent}`}>
              {liveMetrics.throughput_ops_per_sec.toFixed(0)}
            </div>
            <div className="text-xs text-gray-500">Ops/sec</div>
          </div>

          <div className="text-center p-2 bg-gray-50 dark:bg-gray-700 rounded">
            <div className="flex items-center justify-center space-x-1">
              <Shield className="w-3 h-3" />
              {getTrendIcon(liveMetrics.error_rate, server.performance_metrics.error_rate)}
            </div>
            <div className={`font-bold ${
              liveMetrics.error_rate > 0.01 ? 'text-red-500' : theme.accent
            }`}>
              {(liveMetrics.error_rate * 100).toFixed(2)}%
            </div>
            <div className="text-xs text-gray-500">Error Rate</div>
          </div>
        </div>

        {/* Business Context (for Sophia servers) */}
        {server.business_context && (
          <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
            <div className="text-sm font-medium text-blue-700 dark:text-blue-300">
              Pay Ready Context
            </div>
            <div className="text-xs text-blue-600 dark:text-blue-400 mt-1">
              {server.business_context.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </div>
          </div>
        )}

        {/* Capabilities */}
        <div>
          <div className={`text-sm font-medium mb-2 ${theme.text}`}>Capabilities</div>
          <div className="flex flex-wrap gap-1">
            {server.capabilities.slice(0, isExpanded ? server.capabilities.length : 4).map((capability) => (
              <Badge
                key={capability}
                variant="outline"
                className="text-xs"
              >
                {capability.replace(/_/g, ' ')}
              </Badge>
            ))}
            {!isExpanded && server.capabilities.length > 4 && (
              <Badge
                variant="outline"
                className="text-xs cursor-pointer"
                onClick={(e) => {
                  e.stopPropagation();
                  setIsExpanded(true);
                }}
              >
                +{server.capabilities.length - 4} more
              </Badge>
            )}
          </div>
        </div>

        {/* Last Activity */}
        <div className="flex justify-between items-center text-xs text-gray-500">
          <span>Last Activity: {server.last_activity}</span>
          <Button
            variant="ghost"
            size="sm"
            className="h-6 px-2"
            onClick={(e) => {
              e.stopPropagation();
              setIsExpanded(!isExpanded);
            }}
          >
            <Eye className="w-3 h-3" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default MCPServerCard;
