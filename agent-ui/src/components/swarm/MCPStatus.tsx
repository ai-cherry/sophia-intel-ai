import React, { useState, useEffect, useCallback } from 'react';
import { AlertCircle, CheckCircle, XCircle, RefreshCw, Activity, Wifi, WifiOff } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Progress } from '@/components/ui/progress';

interface MCPService {
  name: string;
  url: string;
  endpoint: string;
  description: string;
  critical: boolean;
}

interface ServiceStatus {
  name: string;
  status: 'healthy' | 'degraded' | 'unhealthy' | 'checking';
  latency: number;
  lastChecked: Date;
  error?: string;
  metrics?: {
    uptime: number;
    requestCount: number;
    errorRate: number;
  };
}

const MCP_SERVICES: MCPService[] = [
  {
    name: 'MCP Server',
    url: process.env.NEXT_PUBLIC_MCP_URL || 'http://localhost:8003',
    endpoint: '/health',
    description: 'Main MCP server for tool orchestration',
    critical: true
  },
  {
    name: 'Memory Store',
    url: process.env.NEXT_PUBLIC_MCP_URL || 'http://localhost:8003',
    endpoint: '/memory/health',
    description: 'Memory storage and retrieval service',
    critical: true
  },
  {
    name: 'Code Review',
    url: process.env.NEXT_PUBLIC_MCP_URL || 'http://localhost:8003',
    endpoint: '/code-review/health',
    description: 'Code review and analysis service',
    critical: false
  },
  {
    name: 'Weaviate',
    url: process.env.NEXT_PUBLIC_WEAVIATE_URL || 'http://localhost:8080',
    endpoint: '/v1/.well-known/ready',
    description: 'Vector database for semantic search',
    critical: true
  },
  {
    name: 'Redis Cache',
    url: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8005',
    endpoint: '/cache/health',
    description: 'Caching layer for performance',
    critical: false
  }
];

export const MCPStatus: React.FC = () => {
  const [services, setServices] = useState<Map<string, ServiceStatus>>(new Map());
  const [isChecking, setIsChecking] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30000); // 30 seconds default

  const checkService = async (service: MCPService): Promise<ServiceStatus> => {
    const startTime = Date.now();

    try {
      const response = await fetch(`${service.url}${service.endpoint}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: AbortSignal.timeout(5000) // 5 second timeout
      });

      const latency = Date.now() - startTime;

      if (response.ok) {
        const data = await response.json().catch(() => ({}));

        return {
          name: service.name,
          status: 'healthy',
          latency,
          lastChecked: new Date(),
          metrics: data.metrics
        };
      } else if (response.status >= 500) {
        return {
          name: service.name,
          status: 'unhealthy',
          latency,
          lastChecked: new Date(),
          error: `Server error: ${response.status}`
        };
      } else {
        return {
          name: service.name,
          status: 'degraded',
          latency,
          lastChecked: new Date(),
          error: `Response: ${response.status}`
        };
      }
    } catch (error) {
      return {
        name: service.name,
        status: 'unhealthy',
        latency: Date.now() - startTime,
        lastChecked: new Date(),
        error: error instanceof Error ? error.message : 'Connection failed'
      };
    }
  };

  const checkAllServices = useCallback(async () => {
    setIsChecking(true);

    const checks = MCP_SERVICES.map(async (service) => {
      const status = await checkService(service);
      return [service.name, status] as [string, ServiceStatus];
    });

    const results = await Promise.all(checks);
    const newStatuses = new Map(results);
    setServices(newStatuses);
    setIsChecking(false);
  }, []);

  useEffect(() => {
    // Initial check
    checkAllServices();

    // Set up auto-refresh
    if (autoRefresh) {
      const interval = setInterval(checkAllServices, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [checkAllServices, autoRefresh, refreshInterval]);

  const getStatusIcon = (status: ServiceStatus['status']) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'degraded':
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
      case 'unhealthy':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'checking':
        return <RefreshCw className="w-5 h-5 text-gray-500 animate-spin" />;
    }
  };

  const getStatusBadge = (status: ServiceStatus['status']) => {
    const variants: Record<ServiceStatus['status'], 'default' | 'secondary' | 'destructive' | 'outline'> = {
      healthy: 'default',
      degraded: 'secondary',
      unhealthy: 'destructive',
      checking: 'outline'
    };

    return (
      <Badge variant={variants[status]}>
        {status}
      </Badge>
    );
  };

  const getOverallHealth = () => {
    const statuses = Array.from(services.values());
    const criticalServices = MCP_SERVICES.filter(s => s.critical);

    const criticalStatuses = statuses.filter(s =>
      criticalServices.some(cs => cs.name === s.name)
    );

    if (criticalStatuses.some(s => s.status === 'unhealthy')) {
      return 'critical';
    }
    if (statuses.some(s => s.status === 'unhealthy')) {
      return 'degraded';
    }
    if (statuses.some(s => s.status === 'degraded')) {
      return 'warning';
    }
    return 'healthy';
  };

  const overallHealth = getOverallHealth();

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CardTitle>MCP Services Health</CardTitle>
            {overallHealth === 'healthy' && <Wifi className="w-5 h-5 text-green-500" />}
            {overallHealth === 'warning' && <Activity className="w-5 h-5 text-yellow-500" />}
            {overallHealth === 'degraded' && <AlertCircle className="w-5 h-5 text-orange-500" />}
            {overallHealth === 'critical' && <WifiOff className="w-5 h-5 text-red-500" />}
          </div>

          <div className="flex items-center gap-2">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setAutoRefresh(!autoRefresh)}
                  >
                    {autoRefresh ? 'Auto' : 'Manual'}
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  {autoRefresh
                    ? `Auto-refreshing every ${refreshInterval / 1000}s`
                    : 'Click to enable auto-refresh'
                  }
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>

            <Button
              variant="outline"
              size="sm"
              onClick={checkAllServices}
              disabled={isChecking}
            >
              <RefreshCw className={`w-4 h-4 ${isChecking ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <div className="space-y-4">
          {MCP_SERVICES.map((service) => {
            const status = services.get(service.name) || {
              name: service.name,
              status: 'checking' as const,
              latency: 0,
              lastChecked: new Date()
            };

            return (
              <div
                key={service.name}
                className="flex items-center justify-between p-3 rounded-lg border bg-card"
              >
                <div className="flex items-center gap-3">
                  {getStatusIcon(status.status)}

                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{service.name}</span>
                      {service.critical && (
                        <Badge variant="outline" className="text-xs">
                          Critical
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {service.description}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <div className="flex items-center gap-2">
                      {getStatusBadge(status.status)}
                      <span className="text-sm text-muted-foreground">
                        {status.latency}ms
                      </span>
                    </div>

                    {status.error && (
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger>
                            <p className="text-xs text-red-500 mt-1">
                              Error occurred
                            </p>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p className="max-w-xs">{status.error}</p>
                            <a
                              href={`/docs/troubleshooting#${service.name.toLowerCase().replace(' ', '-')}`}
                              className="text-xs text-blue-400 underline mt-2 block"
                            >
                              Troubleshooting Guide →
                            </a>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Latency Chart */}
        <div className="mt-6 pt-6 border-t">
          <h4 className="text-sm font-medium mb-3">Average Latency</h4>
          <div className="space-y-2">
            {Array.from(services.values())
              .filter(s => s.status !== 'unhealthy')
              .map(service => (
                <div key={service.name} className="flex items-center gap-2">
                  <span className="text-xs w-24 truncate">{service.name}</span>
                  <Progress
                    value={Math.min((service.latency / 1000) * 100, 100)}
                    className="flex-1"
                  />
                  <span className="text-xs w-12 text-right">{service.latency}ms</span>
                </div>
              ))}
          </div>
        </div>

        {/* Refresh Interval Control */}
        <div className="mt-4 pt-4 border-t">
          <label className="text-sm font-medium">
            Refresh Interval
          </label>
          <select
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            value={refreshInterval}
            onChange={(e) => setRefreshInterval(Number(e.target.value))}
            disabled={!autoRefresh}
          >
            <option value={10000}>10 seconds</option>
            <option value={30000}>30 seconds</option>
            <option value={60000}>1 minute</option>
            <option value={300000}>5 minutes</option>
          </select>
        </div>
      </CardContent>
    </Card>
  );
};

export default MCPStatus;