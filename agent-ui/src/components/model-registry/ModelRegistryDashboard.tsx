/**
 * Model Registry Dashboard - Main interface for managing AI model providers
 * Integrates with Portkey for unified model routing and cost optimization
 */

import React, { useState, useCallback } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Separator } from '../ui/separator';
import { Alert, AlertDescription } from '../ui/alert';
import { ScrollArea } from '../ui/scroll-area';
import {
  RefreshCw,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Activity,
  Settings,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Wifi,
  WifiOff,
} from 'lucide-react';

import { useModelRegistry } from '../../hooks/useModelRegistry';
import { ProviderCard } from './ProviderCard';
import { FallbackChainBuilder } from './FallbackChainBuilder';

interface ModelRegistryDashboardProps {
  className?: string;
}

export const ModelRegistryDashboard: React.FC<ModelRegistryDashboardProps> = ({
  className = '',
}) => {
  const {
    providers,
    virtualKeys,
    costAnalytics,
    fallbackChains,
    performanceMetrics,
    routingStrategies,
    isLoading,
    error,
    refreshProviders,
    isConnected,
    lastUpdate,
  } = useModelRegistry();

  const [activeTab, setActiveTab] = useState('overview');
  const [refreshing, setRefreshing] = useState(false);

  // Handle manual refresh
  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await refreshProviders();
    } finally {
      setRefreshing(false);
    }
  }, [refreshProviders]);

  // Calculate dashboard statistics
  const stats = React.useMemo(() => {
    const activeProviders = providers.filter(p => p.status === 'active').length;
    const degradedProviders = providers.filter(p => p.status === 'degraded').length;
    const offlineProviders = providers.filter(p => p.status === 'offline').length;
    const totalProviders = providers.length;

    const avgSuccessRate = providers.length > 0
      ? providers.reduce((sum, p) => sum + p.success_rate, 0) / providers.length
      : 0;

    const avgLatency = providers.length > 0
      ? providers.reduce((sum, p) => sum + p.avg_latency_ms, 0) / providers.length
      : 0;

    return {
      activeProviders,
      degradedProviders,
      offlineProviders,
      totalProviders,
      avgSuccessRate,
      avgLatency,
      healthScore: totalProviders > 0 ? (activeProviders / totalProviders) * 100 : 0,
    };
  }, [providers]);

  // Connection status indicator
  const ConnectionStatus = () => (
    <div className="flex items-center gap-2 text-sm">
      {isConnected ? (
        <div className="flex items-center gap-2 text-green-600">
          <Wifi className="h-4 w-4" />
          <span>Live</span>
        </div>
      ) : (
        <div className="flex items-center gap-2 text-orange-600">
          <WifiOff className="h-4 w-4" />
          <span>Offline</span>
        </div>
      )}
      {lastUpdate && (
        <span className="text-gray-500">
          Updated {new Date(lastUpdate).toLocaleTimeString()}
        </span>
      )}
    </div>
  );

  if (isLoading) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-gray-600">Loading Model Registry...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Model Registry</h1>
          <p className="text-gray-600 mt-1">
            Manage AI providers, monitor costs, and optimize routing strategies
          </p>
        </div>
        <div className="flex items-center gap-3">
          <ConnectionStatus />
          <Button
            onClick={handleRefresh}
            disabled={refreshing}
            variant="outline"
            size="sm"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Health Score</p>
                <p className="text-2xl font-bold text-green-600">
                  {stats.healthScore.toFixed(1)}%
                </p>
              </div>
              <Activity className="h-8 w-8 text-green-600" />
            </div>
            <div className="mt-2 flex items-center gap-2 text-sm">
              <Badge variant={stats.activeProviders > stats.offlineProviders ? 'default' : 'destructive'}>
                {stats.activeProviders} Active
              </Badge>
              <Badge variant="secondary">{stats.degradedProviders} Degraded</Badge>
              <Badge variant="destructive">{stats.offlineProviders} Offline</Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Daily Cost</p>
                <p className="text-2xl font-bold text-blue-600">
                  ${costAnalytics?.daily_cost.toFixed(2) || '0.00'}
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-blue-600" />
            </div>
            <div className="mt-2 text-sm text-gray-500">
              {costAnalytics?.request_count || 0} requests today
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Avg Success Rate</p>
                <p className="text-2xl font-bold text-green-600">
                  {stats.avgSuccessRate.toFixed(1)}%
                </p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-600" />
            </div>
            <div className="mt-2 flex items-center gap-1 text-sm">
              <TrendingUp className="h-4 w-4 text-green-500" />
              <span className="text-green-600">Stable</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Avg Latency</p>
                <p className="text-2xl font-bold text-orange-600">
                  {stats.avgLatency.toFixed(0)}ms
                </p>
              </div>
              <Activity className="h-8 w-8 text-orange-600" />
            </div>
            <div className="mt-2 flex items-center gap-1 text-sm">
              <TrendingDown className="h-4 w-4 text-green-500" />
              <span className="text-green-600">Improving</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Providers</TabsTrigger>
          <TabsTrigger value="fallbacks">Fallback Chains</TabsTrigger>
          <TabsTrigger value="analytics">Cost Analytics</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        {/* Providers Overview */}
        <TabsContent value="overview" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Provider Status</CardTitle>
                  <CardDescription>
                    Monitor health, performance, and costs for all configured providers
                  </CardDescription>
                </div>
                <Badge variant="outline">
                  {providers.length} Providers
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {providers.map((provider) => (
                  <ProviderCard
                    key={provider.provider}
                    provider={provider}
                    virtualKeyConfig={virtualKeys.find(vk => vk.provider === provider.provider)}
                    performanceMetrics={performanceMetrics.find(pm => pm.provider === provider.provider)}
                  />
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Fallback Chains */}
        <TabsContent value="fallbacks" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Fallback Chain Configuration</CardTitle>
              <CardDescription>
                Design resilient routing strategies with automatic fallbacks
              </CardDescription>
            </CardHeader>
            <CardContent>
              <FallbackChainBuilder
                providers={providers}
                fallbackChains={fallbackChains}
                routingStrategies={routingStrategies}
              />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Cost Analytics */}
        <TabsContent value="analytics" className="space-y-6">
          {costAnalytics && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg">Daily</CardTitle>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <div className="text-3xl font-bold text-blue-600">
                      ${costAnalytics.daily_cost.toFixed(2)}
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                      {costAnalytics.request_count} requests
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg">Weekly</CardTitle>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <div className="text-3xl font-bold text-blue-600">
                      ${costAnalytics.weekly_cost.toFixed(2)}
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                      Projected from daily usage
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg">Monthly</CardTitle>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <div className="text-3xl font-bold text-blue-600">
                      ${costAnalytics.monthly_cost.toFixed(2)}
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                      Projected from daily usage
                    </p>
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle>Cost Breakdown by Provider</CardTitle>
                  <CardDescription>
                    Understanding cost distribution across providers
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {Object.entries(costAnalytics.cost_by_provider)
                      .sort(([, a], [, b]) => b - a)
                      .map(([provider, cost]) => {
                        const percentage = costAnalytics.daily_cost > 0
                          ? (cost / costAnalytics.daily_cost) * 100
                          : 0;
                        const tokens = costAnalytics.token_usage[provider] || 0;

                        return (
                          <div key={provider} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                            <div className="flex items-center gap-3">
                              <Badge variant="secondary">{provider}</Badge>
                              <div>
                                <div className="font-medium">${cost.toFixed(4)}</div>
                                <div className="text-sm text-gray-600">
                                  {tokens.toLocaleString()} tokens
                                </div>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="font-medium">{percentage.toFixed(1)}%</div>
                              <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                                <div
                                  className="h-full bg-blue-500 rounded-full transition-all duration-300"
                                  style={{ width: `${percentage}%` }}
                                />
                              </div>
                            </div>
                          </div>
                        );
                      })}
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        {/* Settings */}
        <TabsContent value="settings" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Routing Strategies</CardTitle>
              <CardDescription>
                Configure global routing and optimization strategies
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {routingStrategies.map((strategy) => (
                  <div key={strategy.name} className="p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="font-medium">{strategy.display_name}</h4>
                        <p className="text-sm text-gray-600 mt-1">{strategy.description}</p>
                      </div>
                      <Button variant="outline" size="sm">
                        <Settings className="h-4 w-4 mr-2" />
                        Configure
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Pay Ready Integration</CardTitle>
              <CardDescription>
                Business context and cost optimization for production workloads
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <h4 className="font-medium text-blue-900">Business Context Integration</h4>
                <p className="text-sm text-blue-700 mt-1">
                  Automatically optimize model selection based on client tier, project budget, and business priority
                </p>
                <div className="mt-3 flex gap-2">
                  <Badge variant="secondary">Client Tier Aware</Badge>
                  <Badge variant="secondary">Budget Optimization</Badge>
                  <Badge variant="secondary">Priority Routing</Badge>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-3 border rounded-lg">
                  <h5 className="font-medium">Cost Controls</h5>
                  <p className="text-sm text-gray-600 mt-1">
                    Automatic budget limits and cost alerts
                  </p>
                </div>
                <div className="p-3 border rounded-lg">
                  <h5 className="font-medium">Quality Assurance</h5>
                  <p className="text-sm text-gray-600 mt-1">
                    Model quality monitoring and validation
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};