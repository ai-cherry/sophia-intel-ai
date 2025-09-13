import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from './ui/progress';
import { Separator } from './ui/separator';
import {
  Activity, Brain, DollarSign, TrendingUp, TrendingDown, BarChart3,
  Clock, Zap, AlertTriangle, CheckCircle, RefreshCw, Search,
  Filter, Download, Settings, Eye, Cpu, Database, Globe
} from 'lucide-react';

// Type definitions
interface ModelMetadata {
  id: string;
  name: string;
  provider: string;
  pricing: {
    input_cost_per_1m: number;
    output_cost_per_1m: number;
    context_window: number;
    max_output_tokens: number;
  };
  capabilities: string[];
  performance_tier: 'economy' | 'balanced' | 'premium';
  updated_at: string;
  status: string;
}

interface UsageMetrics {
  total_requests: number;
  total_tokens: number;
  total_cost_usd: number;
  average_tokens_per_request: number;
  average_cost_per_request: number;
  average_latency_ms: number;
  unique_models: number;
  top_models: [string, number][];
  cost_by_model: Record<string, number>;
  cost_by_provider: Record<string, number>;
  hourly_distribution: Record<string, number>;
}

interface CostAlert {
  id: string;
  type: string;
  severity: 'info' | 'warning' | 'critical';
  message: string;
  current_value: number;
  threshold: number;
  timestamp: string;
  model_id?: string;
  provider?: string;
}

interface CurrentCosts {
  hourly_cost_usd: number;
  daily_cost_usd: number;
  weekly_cost_usd: number;
  monthly_cost_usd: number;
  timestamp: string;
}

const ModelCostDashboard: React.FC = () => {
  // State management
  const [models, setModels] = useState<ModelMetadata[]>([]);
  const [filteredModels, setFilteredModels] = useState<ModelMetadata[]>([]);
  const [usageMetrics, setUsageMetrics] = useState<UsageMetrics | null>(null);
  const [currentCosts, setCurrentCosts] = useState<CurrentCosts | null>(null);
  const [alerts, setAlerts] = useState<CostAlert[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  
  // Filter states
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedProvider, setSelectedProvider] = useState('');
  const [selectedTier, setSelectedTier] = useState('');
  const [maxCost, setMaxCost] = useState('');
  
  // Chat state
  const [chatModel, setChatModel] = useState('');
  const [chatMessage, setChatMessage] = useState('');
  const [chatResponse, setChatResponse] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  // API base URL
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8004';

  // Fetch initial data
  useEffect(() => {
    loadInitialData();
    const interval = setInterval(loadCurrentCosts, 30000); // Update costs every 30s
    return () => clearInterval(interval);
  }, []);

  const loadInitialData = async () => {
    setIsLoading(true);
    try {
      await Promise.all([
        loadModelCatalog(),
        loadUsageMetrics(),
        loadCurrentCosts(),
        loadAlerts()
      ]);
    } catch (error) {
      console.error('Failed to load initial data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadModelCatalog = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/models/catalog`);
      const data = await response.json();
      setModels(data.models || []);
      setFilteredModels(data.models || []);
    } catch (error) {
      console.error('Failed to load model catalog:', error);
    }
  };

  const loadUsageMetrics = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/usage/metrics?window=day`);
      const data = await response.json();
      setUsageMetrics(data.metrics);
    } catch (error) {
      console.error('Failed to load usage metrics:', error);
    }
  };

  const loadCurrentCosts = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/usage/cost/current`);
      const data = await response.json();
      setCurrentCosts(data);
    } catch (error) {
      console.error('Failed to load current costs:', error);
    }
  };

  const loadAlerts = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/usage/alerts?limit=10`);
      const data = await response.json();
      setAlerts(data);
    } catch (error) {
      console.error('Failed to load alerts:', error);
    }
  };

  // Filter models based on search criteria
  useEffect(() => {
    let filtered = models;

    if (searchQuery) {
      filtered = filtered.filter(model =>
        model.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        model.name.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    if (selectedProvider) {
      filtered = filtered.filter(model => model.provider === selectedProvider);
    }

    if (selectedTier) {
      filtered = filtered.filter(model => model.performance_tier === selectedTier);
    }

    if (maxCost) {
      const maxCostNum = parseFloat(maxCost);
      filtered = filtered.filter(model => model.pricing.input_cost_per_1m <= maxCostNum);
    }

    setFilteredModels(filtered);
  }, [models, searchQuery, selectedProvider, selectedTier, maxCost]);

  const handleRefresh = async () => {
    await loadInitialData();
  };

  const handleChatSubmit = async () => {
    if (!chatModel || !chatMessage) return;

    setChatLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/v1/models/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: chatModel,
          messages: [{ role: 'user', content: chatMessage }],
          max_tokens: 500,
          track_usage: true
        })
      });

      const data = await response.json();
      setChatResponse(data.content);
      
      // Refresh costs after chat
      setTimeout(loadCurrentCosts, 1000);
    } catch (error) {
      console.error('Chat failed:', error);
      setChatResponse('Error: Failed to get response');
    } finally {
      setChatLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 4
    }).format(amount);
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('en-US').format(num);
  };

  const getProviders = () => {
    return [...new Set(models.map(m => m.provider))].sort();
  };

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'economy': return 'bg-green-100 text-green-800';
      case 'balanced': return 'bg-blue-100 text-blue-800';
      case 'premium': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getAlertColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'border-red-500 bg-red-50';
      case 'warning': return 'border-yellow-500 bg-yellow-50';
      case 'info': return 'border-blue-500 bg-blue-50';
      default: return 'border-gray-500 bg-gray-50';
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading model catalog and usage data...</span>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Model & Cost Dashboard</h1>
          <p className="text-gray-600">
            Monitor OpenRouter models, costs, and usage in real-time
          </p>
        </div>
        <Button onClick={handleRefresh} variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Current Costs Overview */}
      {currentCosts && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Hourly Cost</p>
                  <p className="text-2xl font-bold">{formatCurrency(currentCosts.hourly_cost_usd)}</p>
                </div>
                <Clock className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Daily Cost</p>
                  <p className="text-2xl font-bold">{formatCurrency(currentCosts.daily_cost_usd)}</p>
                </div>
                <DollarSign className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Weekly Cost</p>
                  <p className="text-2xl font-bold">{formatCurrency(currentCosts.weekly_cost_usd)}</p>
                </div>
                <TrendingUp className="h-8 w-8 text-orange-500" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Monthly Cost</p>
                  <p className="text-2xl font-bold">{formatCurrency(currentCosts.monthly_cost_usd)}</p>
                </div>
                <BarChart3 className="h-8 w-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Alerts */}
      {alerts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <AlertTriangle className="h-5 w-5 mr-2" />
              Cost Alerts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {alerts.slice(0, 3).map((alert) => (
                <Alert key={alert.id} className={getAlertColor(alert.severity)}>
                  <AlertDescription>
                    <div className="flex items-center justify-between">
                      <span>{alert.message}</span>
                      <Badge variant="outline" className="text-xs">
                        {alert.severity}
                      </Badge>
                    </div>
                  </AlertDescription>
                </Alert>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="models">Model Catalog</TabsTrigger>
          <TabsTrigger value="usage">Usage Analytics</TabsTrigger>
          <TabsTrigger value="chat">Test Chat</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Usage Metrics */}
            {usageMetrics && (
              <Card>
                <CardHeader>
                  <CardTitle>Today's Usage Summary</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-600">Total Requests</p>
                      <p className="text-xl font-semibold">{formatNumber(usageMetrics.total_requests)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Total Tokens</p>
                      <p className="text-xl font-semibold">{formatNumber(usageMetrics.total_tokens)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Avg Latency</p>
                      <p className="text-xl font-semibold">{usageMetrics.average_latency_ms.toFixed(0)}ms</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Models Used</p>
                      <p className="text-xl font-semibold">{usageMetrics.unique_models}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Top Models */}
            {usageMetrics && usageMetrics.top_models.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Top Models Today</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {usageMetrics.top_models.slice(0, 5).map(([modelId, requests]) => (
                      <div key={modelId} className="flex items-center justify-between">
                        <span className="text-sm font-medium truncate">{modelId}</span>
                        <Badge variant="secondary">{requests} requests</Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        {/* Model Catalog Tab */}
        <TabsContent value="models" className="space-y-6">
          {/* Filters */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Filter className="h-5 w-5 mr-2" />
                Filter Models
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <label className="text-sm font-medium">Search</label>
                  <Input
                    placeholder="Search models..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Provider</label>
                  <select
                    className="w-full p-2 border rounded"
                    value={selectedProvider}
                    onChange={(e) => setSelectedProvider(e.target.value)}
                  >
                    <option value="">All Providers</option>
                    {getProviders().map(provider => (
                      <option key={provider} value={provider}>{provider}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium">Tier</label>
                  <select
                    className="w-full p-2 border rounded"
                    value={selectedTier}
                    onChange={(e) => setSelectedTier(e.target.value)}
                  >
                    <option value="">All Tiers</option>
                    <option value="economy">Economy</option>
                    <option value="balanced">Balanced</option>
                    <option value="premium">Premium</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium">Max Cost ($/1M tokens)</label>
                  <Input
                    type="number"
                    placeholder="Max cost..."
                    value={maxCost}
                    onChange={(e) => setMaxCost(e.target.value)}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Model List */}
          <Card>
            <CardHeader>
              <CardTitle>
                Models ({filteredModels.length} of {models.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-96">
                <div className="space-y-2">
                  {filteredModels.slice(0, 50).map((model) => (
                    <div key={model.id} className="border rounded p-3 hover:bg-gray-50">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <h4 className="font-medium">{model.name}</h4>
                          <p className="text-sm text-gray-600">{model.id}</p>
                          <div className="flex items-center gap-2 mt-1">
                            <Badge variant="outline">{model.provider}</Badge>
                            <Badge className={getTierColor(model.performance_tier)}>
                              {model.performance_tier}
                            </Badge>
                            {model.capabilities.slice(0, 2).map(cap => (
                              <Badge key={cap} variant="secondary" className="text-xs">
                                {cap}
                              </Badge>
                            ))}
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-medium">
                            {formatCurrency(model.pricing.input_cost_per_1m / 1000000)} / 1K tokens
                          </p>
                          <p className="text-xs text-gray-600">
                            {formatNumber(model.pricing.context_window)} context
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Usage Analytics Tab */}
        <TabsContent value="usage" className="space-y-6">
          {usageMetrics && (
            <>
              {/* Cost by Provider */}
              <Card>
                <CardHeader>
                  <CardTitle>Cost by Provider</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {Object.entries(usageMetrics.cost_by_provider)
                      .sort(([,a], [,b]) => b - a)
                      .map(([provider, cost]) => (
                        <div key={provider} className="flex items-center justify-between">
                          <span className="font-medium">{provider}</span>
                          <span>{formatCurrency(cost)}</span>
                        </div>
                      ))}
                  </div>
                </CardContent>
              </Card>

              {/* Hourly Distribution */}
              <Card>
                <CardHeader>
                  <CardTitle>Hourly Cost Distribution</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-6 gap-2">
                    {Object.entries(usageMetrics.hourly_distribution)
                      .slice(-24)
                      .map(([hour, cost]) => (
                        <div key={hour} className="text-center">
                          <div className="text-xs text-gray-600">{hour}</div>
                          <div 
                            className="bg-blue-500 mt-1"
                            style={{ 
                              height: `${Math.max(4, (cost / Math.max(...Object.values(usageMetrics.hourly_distribution))) * 40)}px`
                            }}
                          />
                          <div className="text-xs mt-1">{formatCurrency(cost)}</div>
                        </div>
                      ))}
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        {/* Test Chat Tab */}
        <TabsContent value="chat" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Test Model Chat</CardTitle>
              <CardDescription>
                Test any model and automatically track usage costs
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium">Select Model</label>
                <select
                  className="w-full p-2 border rounded mt-1"
                  value={chatModel}
                  onChange={(e) => setChatModel(e.target.value)}
                >
                  <option value="">Choose a model...</option>
                  {models.slice(0, 20).map(model => (
                    <option key={model.id} value={model.id}>
                      {model.name} - {formatCurrency(model.pricing.input_cost_per_1m / 1000000)}/1K
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="text-sm font-medium">Message</label>
                <textarea
                  className="w-full p-2 border rounded mt-1"
                  rows={3}
                  placeholder="Enter your message..."
                  value={chatMessage}
                  onChange={(e) => setChatMessage(e.target.value)}
                />
              </div>
              
              <Button 
                onClick={handleChatSubmit}
                disabled={!chatModel || !chatMessage || chatLoading}
                className="w-full"
              >
                {chatLoading ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Sending...
                  </>
                ) : (
                  'Send Message'
                )}
              </Button>
              
              {chatResponse && (
                <div className="mt-4">
                  <label className="text-sm font-medium">Response</label>
                  <div className="mt-1 p-3 border rounded bg-gray-50">
                    <pre className="whitespace-pre-wrap text-sm">{chatResponse}</pre>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ModelCostDashboard;