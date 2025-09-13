'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import {
  Zap, Heart, Brain, MessageCircle, Shield, Eye, Activity,
  TrendingUp, TrendingDown, DollarSign, Users, Target, AlertTriangle,
  CheckCircle, Server, Clock, BarChart3
} from 'lucide-react';

// ==================== MYTHOLOGY AGENT WIDGET COMPONENT ====================

interface AgentMetrics {
  primary_metric: {
    label: string;
    value: string;
    trend: 'up' | 'down' | 'stable';
    change_percentage?: number;
  };
  secondary_metrics: Array<{
    label: string;
    value: string;
    status?: 'good' | 'warning' | 'critical';
  }>;
  server_status: Array<{
    server_name: string;
    status: 'operational' | 'degraded' | 'offline';
    last_activity: string;
  }>;
}

interface MythologyAgent {
  id: string;
  name: string;
  title: string;
  domain: 'sophia';
  assigned_mcp_servers: string[];
  context: string;
  widget_type: string;
  icon_type: 'hermes' | 'asclepius' | 'athena' | 'odin' | 'minerva' | 'dionysus' | 'oracle';
  pay_ready_context?: string;
}

interface MythologyAgentWidgetProps {
  agent: MythologyAgent;
  metrics: AgentMetrics;
  compact?: boolean;
  onAgentClick?: (agent: MythologyAgent) => void;
}

export const MythologyAgentWidget: React.FC<MythologyAgentWidgetProps> = ({
  agent,
  metrics,
  compact = false,
  onAgentClick
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [liveMetrics, setLiveMetrics] = useState(metrics);

  // Simulate live updates
  useEffect(() => {
    const interval = setInterval(() => {
      // Simulate metric updates based on agent type
      if (agent.widget_type === 'sales_performance_intelligence') {
        setLiveMetrics(prev => ({
          ...prev,
          primary_metric: {
            ...prev.primary_metric,
            value: `$${(parseFloat(prev.primary_metric.value.replace(/[$B]/g, '')) + (Math.random() - 0.5) * 0.1).toFixed(1)}B`
          }
        }));
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [agent.widget_type]);

  const getAgentIcon = (iconType: string) => {
    const iconMap = {
      hermes: <Zap className="w-6 h-6" />,
      asclepius: <Heart className="w-6 h-6" />,
      athena: <Target className="w-6 h-6" />,
      odin: <Shield className="w-6 h-6" />,
      minerva: <Brain className="w-6 h-6" />,
      dionysus: <Eye className="w-6 h-6" />,
      oracle: <MessageCircle className="w-6 h-6" />
    };
    return iconMap[iconType as keyof typeof iconMap] || <Activity className="w-6 h-6" />;
  };

  const getAgentTheme = (domain: string, iconType: string) => {
    const gradientMap = {
      hermes: 'from-blue-500 to-purple-500',
      asclepius: 'from-emerald-500 to-teal-500',
      athena: 'from-indigo-500 to-purple-500',
      minerva: 'from-cyan-500 to-blue-500',
      dionysus: 'from-orange-500 to-red-500',
      oracle: 'from-violet-500 to-purple-500'
    };
    return {
      gradient: gradientMap[iconType as keyof typeof gradientMap] || 'from-blue-500 to-purple-500',
      bg: 'bg-white dark:bg-gray-800',
      border: 'border-gray-200 dark:border-gray-600',
      text: 'text-gray-900 dark:text-white',
      accent: 'text-blue-600 dark:text-blue-400',
      cardBg: 'bg-gray-50 dark:bg-gray-700'
    };
  };

  const theme = getAgentTheme(agent.domain, agent.icon_type);

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return <TrendingUp className="w-4 h-4 text-green-500" />;
      case 'down': return <TrendingDown className="w-4 h-4 text-red-500" />;
      default: return <Activity className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'operational': return <CheckCircle className="w-3 h-3 text-green-500" />;
      case 'degraded': return <AlertTriangle className="w-3 h-3 text-yellow-500" />;
      case 'offline': return <AlertTriangle className="w-3 h-3 text-red-500" />;
      default: return <Activity className="w-3 h-3 text-gray-500" />;
    }
  };

  const renderHermesWidget = () => (
    <div className="space-y-4">
      {/* Primary Sales Metric */}
      <div className="flex items-center justify-between">
        <div>
          <div className="text-2xl font-bold text-blue-600 dark:text-blue-400 flex items-center space-x-2">
            <DollarSign className="w-6 h-6" />
            <span>{liveMetrics.primary_metric.value}</span>
            {getTrendIcon(liveMetrics.primary_metric.trend)}
          </div>
          <div className="text-sm text-gray-500">{liveMetrics.primary_metric.label}</div>
        </div>
      </div>

      {/* Pay Ready Context */}
      {agent.pay_ready_context && (
        <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <div className="text-sm font-medium text-blue-700 dark:text-blue-300">
            Property Management Intelligence
          </div>
          <div className="text-xs text-blue-600 dark:text-blue-400 mt-1">
            Market penetration analysis for $20B+ rent processing volume
          </div>
        </div>
      )}

      {/* Secondary Metrics */}
      <div className="grid grid-cols-2 gap-3">
        {liveMetrics.secondary_metrics.map((metric, idx) => (
          <div key={idx} className={`text-center p-2 ${theme.cardBg} rounded`}>
            <div className="font-bold text-sm">{metric.value}</div>
            <div className="text-xs text-gray-500">{metric.label}</div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderAsclepiusWidget = () => (
    <div className="space-y-4">
      {/* Health Score */}
      <div className="flex items-center justify-between">
        <div>
          <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 flex items-center space-x-2">
            <Heart className="w-6 h-6" />
            <span>{liveMetrics.primary_metric.value}</span>
          </div>
          <div className="text-sm text-gray-500">Portfolio Health Score</div>
        </div>
      </div>

      {/* Health Progress */}
      <div>
        <Progress
          value={parseInt(liveMetrics.primary_metric.value.replace('%', ''))}
          className="h-2"
        />
      </div>

      {/* Tenant/Landlord Metrics */}
      <div className="grid grid-cols-2 gap-3">
        {liveMetrics.secondary_metrics.map((metric, idx) => (
          <div key={idx} className={`text-center p-2 ${theme.cardBg} rounded`}>
            <div className={`font-bold text-sm ${
              metric.status === 'critical' ? 'text-red-500' :
              metric.status === 'warning' ? 'text-yellow-500' :
              'text-emerald-500'
            }`}>
              {metric.value}
            </div>
            <div className="text-xs text-gray-500">{metric.label}</div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderOdinWidget = () => (
    <div className="space-y-4">
      {/* Code Quality Score */}
      <div className="flex items-center justify-between">
        <div>
          <div className="text-2xl font-bold text-green-400 flex items-center space-x-2 font-mono">
            <Shield className="w-6 h-6" />
            <span>{liveMetrics.primary_metric.value}</span>
            {getTrendIcon(liveMetrics.primary_metric.trend)}
          </div>
          <div className="text-sm text-gray-400 font-mono">
            TECHNICAL EXCELLENCE SCORE
          </div>
        </div>
      </div>

      {/* Technical Metrics Grid */}
      <div className="grid grid-cols-3 gap-2">
        {liveMetrics.secondary_metrics.map((metric, idx) => (
          <div key={idx} className="text-center p-2 bg-gray-800 border border-gray-700 rounded">
            <div className="font-bold text-xs text-green-400 font-mono">
              {metric.value}
            </div>
            <div className="text-xs text-gray-500 font-mono">
              {metric.label}
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderMinervaWidget = () => (
    <div className="space-y-4">
      {/* Analytics Overview */}
      <div className="flex items-center justify-between">
        <div>
          <div className="text-2xl font-bold text-cyan-600 dark:text-cyan-400 flex items-center space-x-2">
            <BarChart3 className="w-6 h-6" />
            <span>{liveMetrics.primary_metric.value}</span>
          </div>
          <div className="text-sm text-gray-500">Cross-Domain Insights</div>
        </div>
      </div>

      {/* Insight Metrics */}
      <div className="grid grid-cols-2 gap-3">
        {liveMetrics.secondary_metrics.map((metric, idx) => (
          <div key={idx} className={`text-center p-2 ${theme.cardBg} rounded`}>
            <div className="font-bold text-sm text-cyan-600 dark:text-cyan-400">
              {metric.value}
            </div>
            <div className="text-xs text-gray-500">{metric.label}</div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderWidgetContent = () => {
    switch (agent.icon_type) {
      case 'hermes': return renderHermesWidget();
      case 'asclepius': return renderAsclepiusWidget();
      case 'odin': return renderOdinWidget();
      case 'minerva': return renderMinervaWidget();
      case 'dionysus': return renderHermesWidget(); // Use Hermes style for creative intelligence
      case 'oracle': return renderMinervaWidget(); // Use Minerva style for conversational AI
      case 'athena': return renderMinervaWidget(); // Use Minerva style for strategic operations
      default: return renderHermesWidget();
    }
  };

  if (compact) {
    return (
      <Card
        className={`${theme.bg} ${theme.border} cursor-pointer transition-all hover:shadow-lg hover:scale-105`}
        onClick={() => {
          setIsExpanded(!isExpanded);
          onAgentClick?.(agent);
        }}
      >
        <CardContent className="p-3">
          <div className="flex items-center space-x-3">
            <div className={`w-10 h-10 rounded-lg bg-gradient-to-r ${theme.gradient} flex items-center justify-center text-white`}>
              {getAgentIcon(agent.icon_type)}
            </div>
            <div className="flex-1">
              <div className={`font-medium ${theme.text} text-sm`}>{agent.name}</div>
              <div className="text-xs text-gray-500">{agent.context.substring(0, 30)}...</div>
            </div>
            <div className={`text-lg font-bold ${theme.accent}`}>
              {liveMetrics.primary_metric.value}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card
      className={`${theme.bg} ${theme.border} transition-all hover:shadow-xl ${
        onAgentClick ? 'cursor-pointer hover:scale-105' : ''
      }`}
      onClick={() => onAgentClick?.(agent)}
    >
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`w-12 h-12 rounded-lg bg-gradient-to-r ${theme.gradient} flex items-center justify-center text-white`}>
              {getAgentIcon(agent.icon_type)}
            </div>
            <div>
              <CardTitle className={`text-lg ${theme.text} ${agent.domain === 'sophia' ? 'font-mono' : ''}`}>
                {agent.name}
              </CardTitle>
              <p className="text-sm text-gray-500">{agent.title}</p>
            </div>
          </div>

          <Badge variant="outline" className="text-xs">
            {agent.assigned_mcp_servers.length} servers
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Widget-specific content */}
        {renderWidgetContent()}

        {/* MCP Server Status */}
        <div className="pt-3 border-t border-gray-200 dark:border-gray-700">
          <div className={`text-sm font-medium mb-2 ${theme.text}`}>
            MCP Server Status
          </div>
          <div className="space-y-1">
            {liveMetrics.server_status.map((server) => (
              <div key={server.server_name} className="flex items-center justify-between text-xs">
                <div className="flex items-center space-x-2">
                  {getStatusIcon(server.status)}
                  <span className={theme.text}>
                    {server.server_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </span>
                </div>
                <span className="text-gray-500">{server.last_activity}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Agent Description */}
        <div className="text-xs text-gray-500">
          {agent.context}
        </div>
      </CardContent>
    </Card>
  );
};

export default MythologyAgentWidget;
