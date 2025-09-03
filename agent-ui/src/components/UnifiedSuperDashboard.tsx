import React, { useState, useEffect, useRef, useCallback } from 'react';
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
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import {
  Activity, Brain, Terminal, Zap, Users, Server, AlertCircle,
  CheckCircle, XCircle, Loader2, Send, Bot, Network, Cpu, Eye,
  DollarSign, TrendingUp, Database, Shield, Settings, BarChart3,
  Clock, Layers, GitBranch, Package, Globe, Gauge, Search,
  Command, Star, RefreshCw, Power, Trash2, Copy, Download
} from 'lucide-react';

// ==================== UNIFIED TYPE SYSTEM ====================

interface SystemType {
  AGENT: 'agent';
  SWARM: 'swarm';
  MICRO_SWARM: 'micro_swarm';
  BACKGROUND_AGENT: 'background_agent';
  EMBEDDING_AGENT: 'embedding_agent';
  MCP_SERVER: 'mcp_server';
  TOOL: 'tool';
  SERVICE: 'service';
  MODEL: 'model';
}

interface UnifiedSystem {
  id: string;
  name: string;
  type: keyof SystemType;
  status: 'idle' | 'active' | 'processing' | 'error' | 'degraded' | 'offline';
  capabilities: string[];
  metrics: {
    cpu?: number;
    memory?: number;
    requests?: number;
    errors?: number;
    latency?: number;
    cost?: number;
  };
  config: Record<string, any>;
  connections: string[];
  last_activity: string;
  error_count: number;
  metadata: Record<string, any>;
}

interface CostMetrics {
  total_cost_usd: number;
  total_tokens: number;
  total_requests: number;
  model_costs: Record<string, number>;
  provider_costs: Record<string, number>;
  daily_costs: Array<{
    date: string;
    cost: number;
    tokens: number;
  }>;
}

interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  status: 'available' | 'unavailable' | 'rate_limited';
  performance: {
    avg_latency: number;
    success_rate: number;
    tokens_per_second: number;
  };
  cost_per_1k_tokens: number;
}

interface InfrastructureMetrics {
  servers: Array<{
    id: string;
    name: string;
    status: 'online' | 'offline' | 'maintenance';
    cpu: number;
    memory: number;
    disk: number;
    network: number;
  }>;
  containers: number;
  services: number;
  health_score: number;
}

// ==================== THE ULTIMATE UNIFIED DASHBOARD ====================

const UnifiedSuperDashboard: React.FC = () => {
  // Core State
  const [connected, setConnected] = useState(false);
  const [systems, setSystems] = useState<UnifiedSystem[]>([]);
  const [selectedSystem, setSelectedSystem] = useState<UnifiedSystem | null>(null);
  
  // Natural Language
  const [commandInput, setCommandInput] = useState('');
  const [commandHistory, setCommandHistory] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Metrics & Analytics
  const [costMetrics, setCostMetrics] = useState<CostMetrics | null>(null);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [infrastructure, setInfrastructure] = useState<InfrastructureMetrics | null>(null);
  const [healthScore, setHealthScore] = useState(100);
  
  // UI State
  const [activeTab, setActiveTab] = useState('overview');
  const [alerts, setAlerts] = useState<any[]>([]);
  const [activities, setActivities] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<NodeJS.Timeout>();

  // ==================== WEBSOCKET CONNECTION ====================
  
  useEffect(() => {
    connectWebSocket();
    return () => {
      if (ws.current) ws.current.close();
      if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current);
    };
  }, []);

  const connectWebSocket = () => {
    ws.current = new WebSocket('ws://localhost:8000/ws/orchestrator');
    
    ws.current.onopen = () => {
      setConnected(true);
      sendCommand({ type: 'subscribe_all' }); // Subscribe to everything
      refreshAllData();
    };

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleMessage(data);
    };

    ws.current.onclose = () => {
      setConnected(false);
      reconnectTimeout.current = setTimeout(connectWebSocket, 3000);
    };

    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnected(false);
    };
  };

  const handleMessage = (data: any) => {
    switch (data.type) {
      case 'system_update':
        updateSystems(data.systems);
        break;
      case 'metrics_update':
        updateMetrics(data);
        break;
      case 'alert':
        addAlert(data);
        break;
      case 'activity':
        addActivity(data);
        break;
      case 'command_result':
        handleCommandResult(data);
        break;
    }
  };

  // ==================== NATURAL LANGUAGE CONTROL ====================

  const executeNaturalLanguage = async () => {
    if (!commandInput.trim()) return;
    
    setLoading(true);
    const command = {
      type: 'natural_language',
      text: commandInput,
      context: {
        active_tab: activeTab,
        selected_system: selectedSystem?.id,
        search_query: searchQuery
      }
    };
    
    sendCommand(command);
    addToHistory({
      type: 'command',
      text: commandInput,
      timestamp: new Date().toISOString()
    });
    
    setCommandInput('');
  };

  // ==================== QUICK ACTIONS ====================

  const quickActions = [
    {
      label: 'Code Gen Swarm',
      icon: <Zap className="w-4 h-4" />,
      action: () => spawnSwarm('code_generation')
    },
    {
      label: 'Debug Mode',
      icon: <Shield className="w-4 h-4" />,
      action: () => spawnSwarm('debugging')
    },
    {
      label: 'Health Check',
      icon: <Activity className="w-4 h-4" />,
      action: () => sendCommand({ type: 'health_check' })
    },
    {
      label: 'Optimize',
      icon: <TrendingUp className="w-4 h-4" />,
      action: () => sendCommand({ type: 'optimize_all' })
    },
    {
      label: 'Emergency Stop',
      icon: <Power className="w-4 h-4" />,
      action: () => sendCommand({ type: 'emergency_stop' }),
      variant: 'destructive'
    }
  ];

  // ==================== HELPER FUNCTIONS ====================

  const sendCommand = (command: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(command));
    }
  };

  const spawnSwarm = (swarmType: string) => {
    sendCommand({
      type: 'spawn_swarm',
      swarm_type: swarmType,
      auto_start: true
    });
  };

  const updateSystems = (newSystems: UnifiedSystem[]) => {
    setSystems(newSystems);
    updateHealthScore(newSystems);
  };

  const updateMetrics = (data: any) => {
    if (data.cost) setCostMetrics(data.cost);
    if (data.models) setModels(data.models);
    if (data.infrastructure) setInfrastructure(data.infrastructure);
  };

  const updateHealthScore = (systems: UnifiedSystem[]) => {
    const total = systems.length;
    if (total === 0) {
      setHealthScore(100);
      return;
    }
    
    const healthy = systems.filter(s => 
      s.status === 'active' || s.status === 'idle'
    ).length;
    
    const score = (healthy / total) * 100;
    setHealthScore(Math.round(score));
  };

  const addAlert = (alert: any) => {
    setAlerts(prev => [alert, ...prev].slice(0, 50));
  };

  const addActivity = (activity: any) => {
    setActivities(prev => [activity, ...prev].slice(0, 100));
  };

  const addToHistory = (entry: any) => {
    setCommandHistory(prev => [entry, ...prev].slice(0, 100));
  };

  const handleCommandResult = (result: any) => {
    setLoading(false);
    addToHistory({
      type: 'result',
      ...result,
      timestamp: new Date().toISOString()
    });
  };

  const refreshAllData = () => {
    sendCommand({ type: 'get_all_data' });
  };

  // ==================== SEARCH & FILTER ====================

  const filteredSystems = systems.filter(system => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      system.name.toLowerCase().includes(query) ||
      system.type.toLowerCase().includes(query) ||
      system.capabilities.some(c => c.toLowerCase().includes(query)) ||
      system.id.toLowerCase().includes(query)
    );
  });

  // ==================== UI COMPONENTS ====================

  const getStatusIcon = (status: string) => {
    const icons: Record<string, JSX.Element> = {
      active: <Activity className="w-4 h-4 text-green-500" />,
      processing: <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />,
      idle: <CheckCircle className="w-4 h-4 text-gray-500" />,
      error: <XCircle className="w-4 h-4 text-red-500" />,
      degraded: <AlertCircle className="w-4 h-4 text-yellow-500" />,
      offline: <Power className="w-4 h-4 text-gray-400" />
    };
    return icons[status] || <Circle className="w-4 h-4" />;
  };

  const getSystemIcon = (type: string) => {
    const icons: Record<string, JSX.Element> = {
      agent: <Bot className="w-4 h-4" />,
      swarm: <Users className="w-4 h-4" />,
      micro_swarm: <Users className="w-4 h-4 text-purple-500" />,
      mcp_server: <Server className="w-4 h-4" />,
      embedding_agent: <Brain className="w-4 h-4" />,
      model: <Package className="w-4 h-4" />,
      service: <Globe className="w-4 h-4" />,
      tool: <Settings className="w-4 h-4" />
    };
    return icons[type] || <Cpu className="w-4 h-4" />;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-950">
      {/* ==================== HEADER ==================== */}
      <div className="border-b bg-white/80 dark:bg-gray-900/80 backdrop-blur-lg sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Brain className="w-8 h-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  SuperOrchestrator Command Center
                </h1>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Complete control over all AI systems
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Connection Status */}
              <Badge variant={connected ? 'success' : 'destructive'}>
                {connected ? 'Connected' : 'Disconnected'}
              </Badge>
              
              {/* Health Score */}
              <div className="flex items-center space-x-2">
                <Gauge className="w-5 h-5 text-gray-500" />
                <div className="text-sm">
                  <span className="font-medium">Health:</span>
                  <span className={`ml-1 font-bold ${
                    healthScore > 80 ? 'text-green-600' :
                    healthScore > 60 ? 'text-yellow-600' :
                    'text-red-600'
                  }`}>
                    {healthScore}%
                  </span>
                </div>
              </div>
              
              {/* Quick Stats */}
              <div className="flex space-x-4 text-sm">
                <div>
                  <span className="text-gray-500">Systems:</span>
                  <span className="ml-1 font-bold">{systems.length}</span>
                </div>
                <div>
                  <span className="text-gray-500">Active:</span>
                  <span className="ml-1 font-bold text-green-600">
                    {systems.filter(s => s.status === 'active').length}
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">Errors:</span>
                  <span className="ml-1 font-bold text-red-600">
                    {systems.filter(s => s.status === 'error').length}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ==================== COMMAND BAR ==================== */}
      <div className="container mx-auto px-4 py-4">
        <Card className="shadow-xl">
          <CardContent className="p-4">
            <div className="space-y-4">
              {/* Natural Language Input */}
              <div className="flex space-x-2">
                <Command className="w-5 h-5 mt-2.5 text-gray-500" />
                <Input
                  placeholder="Enter any command in natural language... (e.g., 'spawn a debugging swarm for agent-123', 'show me cost breakdown for today', 'optimize all running systems')"
                  value={commandInput}
                  onChange={(e) => setCommandInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && executeNaturalLanguage()}
                  className="flex-1 text-lg"
                  disabled={loading}
                />
                <Button 
                  onClick={executeNaturalLanguage}
                  disabled={loading || !connected}
                  size="lg"
                >
                  {loading ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Send className="w-4 h-4 mr-2" />
                  )}
                  Execute
                </Button>
              </div>
              
              {/* Quick Actions */}
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-500">Quick Actions:</span>
                {quickActions.map((action, idx) => (
                  <Button
                    key={idx}
                    variant={action.variant || 'outline'}
                    size="sm"
                    onClick={action.action}
                    disabled={!connected}
                  >
                    {action.icon}
                    <span className="ml-2">{action.label}</span>
                  </Button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ==================== MAIN CONTENT ==================== */}
      <div className="container mx-auto px-4 pb-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
          <TabsList className="grid grid-cols-8 w-full">
            <TabsTrigger value="overview">
              <Eye className="w-4 h-4 mr-2" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="systems">
              <Network className="w-4 h-4 mr-2" />
              Systems
            </TabsTrigger>
            <TabsTrigger value="swarms">
              <Users className="w-4 h-4 mr-2" />
              Swarms
            </TabsTrigger>
            <TabsTrigger value="analytics">
              <DollarSign className="w-4 h-4 mr-2" />
              Analytics
            </TabsTrigger>
            <TabsTrigger value="models">
              <Brain className="w-4 h-4 mr-2" />
              Models
            </TabsTrigger>
            <TabsTrigger value="infrastructure">
              <Server className="w-4 h-4 mr-2" />
              Infrastructure
            </TabsTrigger>
            <TabsTrigger value="monitoring">
              <Activity className="w-4 h-4 mr-2" />
              Monitoring
            </TabsTrigger>
            <TabsTrigger value="history">
              <Clock className="w-4 h-4 mr-2" />
              History
            </TabsTrigger>
          </TabsList>

          {/* ==================== OVERVIEW TAB ==================== */}
          <TabsContent value="overview" className="space-y-4">
            {/* Metrics Grid */}
            <div className="grid grid-cols-4 gap-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Total Systems</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">{systems.length}</div>
                  <Progress value={100} className="mt-2" />
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Active Now</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-green-600">
                    {systems.filter(s => s.status === 'active').length}
                  </div>
                  <Progress 
                    value={(systems.filter(s => s.status === 'active').length / Math.max(systems.length, 1)) * 100} 
                    className="mt-2"
                  />
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Today's Cost</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-blue-600">
                    ${costMetrics?.total_cost_usd.toFixed(2) || '0.00'}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {costMetrics?.total_tokens.toLocaleString() || 0} tokens
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Health Score</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className={`text-3xl font-bold ${
                    healthScore > 80 ? 'text-green-600' :
                    healthScore > 60 ? 'text-yellow-600' :
                    'text-red-600'
                  }`}>
                    {healthScore}%
                  </div>
                  <Progress value={healthScore} className="mt-2" />
                </CardContent>
              </Card>
            </div>

            {/* Activity Feed & Alerts */}
            <div className="grid grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle>Live Activity</CardTitle>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-[400px]">
                    <div className="space-y-2">
                      {activities.map((activity, idx) => (
                        <div key={idx} className="flex items-start space-x-2 p-2 rounded hover:bg-gray-50 dark:hover:bg-gray-800">
                          <Activity className="w-4 h-4 mt-0.5 text-blue-500" />
                          <div className="flex-1">
                            <p className="text-sm">{activity.message}</p>
                            <p className="text-xs text-gray-500">{activity.timestamp}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader>
                  <CardTitle>Alerts</CardTitle>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-[400px]">
                    <div className="space-y-2">
                      {alerts.map((alert, idx) => (
                        <Alert key={idx} variant={alert.level === 'error' ? 'destructive' : 'default'}>
                          <AlertCircle className="h-4 w-4" />
                          <AlertDescription>{alert.message}</AlertDescription>
                        </Alert>
                      ))}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* ==================== SYSTEMS TAB ==================== */}
          <TabsContent value="systems" className="space-y-4">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>All AI Systems</CardTitle>
                  <div className="flex items-center space-x-2">
                    <Search className="w-4 h-4 text-gray-500" />
                    <Input
                      placeholder="Search systems..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-64"
                    />
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[600px]">
                  <div className="grid grid-cols-2 gap-4">
                    {filteredSystems.map((system) => (
                      <Card 
                        key={system.id}
                        className={`cursor-pointer transition-all hover:shadow-lg ${
                          selectedSystem?.id === system.id ? 'ring-2 ring-blue-500' : ''
                        }`}
                        onClick={() => setSelectedSystem(system)}
                      >
                        <CardHeader className="pb-3">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-2">
                              {getSystemIcon(system.type)}
                              <CardTitle className="text-base">{system.name}</CardTitle>
                            </div>
                            {getStatusIcon(system.status)}
                          </div>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-2">
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-gray-500">Type:</span>
                              <Badge variant="outline">{system.type}</Badge>
                            </div>
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-gray-500">ID:</span>
                              <code className="text-xs">{system.id.slice(0, 8)}...</code>
                            </div>
                            {system.metrics.cpu && (
                              <div className="space-y-1">
                                <div className="flex justify-between text-xs">
                                  <span>CPU</span>
                                  <span>{system.metrics.cpu}%</span>
                                </div>
                                <Progress value={system.metrics.cpu} className="h-1" />
                              </div>
                            )}
                            {system.capabilities.length > 0 && (
                              <div className="flex flex-wrap gap-1 mt-2">
                                {system.capabilities.slice(0, 3).map((cap) => (
                                  <Badge key={cap} variant="secondary" className="text-xs">
                                    {cap}
                                  </Badge>
                                ))}
                                {system.capabilities.length > 3 && (
                                  <Badge variant="secondary" className="text-xs">
                                    +{system.capabilities.length - 3}
                                  </Badge>
                                )}
                              </div>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>

          {/* ==================== SWARMS TAB ==================== */}
          <TabsContent value="swarms" className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              {['code_embedding', 'meta_tagging', 'planning', 'code_generation', 'debugging', 'consensus'].map((swarmType) => (
                <Card key={swarmType}>
                  <CardHeader>
                    <CardTitle className="capitalize">
                      {swarmType.replace('_', ' ')} Swarm
                    </CardTitle>
                    <CardDescription>
                      Specialized micro-swarm for {swarmType.replace('_', ' ')}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex justify-between text-sm">
                      <span>Status:</span>
                      <Badge>
                        {systems.find(s => s.type === 'micro_swarm' && s.metadata?.swarm_type === swarmType)?.status || 'Not Spawned'}
                      </Badge>
                    </div>
                    <Button 
                      className="w-full"
                      onClick={() => spawnSwarm(swarmType)}
                    >
                      <Zap className="w-4 h-4 mr-2" />
                      Spawn Swarm
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* ==================== ANALYTICS TAB ==================== */}
          <TabsContent value="analytics" className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle>Total Cost Today</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-4xl font-bold">
                    ${costMetrics?.total_cost_usd.toFixed(2) || '0.00'}
                  </div>
                  <div className="mt-4 space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Tokens:</span>
                      <span>{costMetrics?.total_tokens.toLocaleString() || 0}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Requests:</span>
                      <span>{costMetrics?.total_requests.toLocaleString() || 0}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader>
                  <CardTitle>Cost by Model</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {Object.entries(costMetrics?.model_costs || {}).slice(0, 5).map(([model, cost]) => (
                      <div key={model} className="flex justify-between text-sm">
                        <span className="truncate">{model}</span>
                        <span className="font-medium">${cost.toFixed(2)}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader>
                  <CardTitle>Cost by Provider</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {Object.entries(costMetrics?.provider_costs || {}).map(([provider, cost]) => (
                      <div key={provider} className="flex justify-between text-sm">
                        <span>{provider}</span>
                        <span className="font-medium">${cost.toFixed(2)}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
            
            {/* Cost Trend Chart would go here */}
            <Card>
              <CardHeader>
                <CardTitle>7-Day Cost Trend</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64 flex items-center justify-center text-gray-500">
                  {/* Chart component would go here */}
                  <BarChart3 className="w-8 h-8" />
                  <span className="ml-2">Cost trend visualization</span>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* ==================== MODELS TAB ==================== */}
          <TabsContent value="models" className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              {models.map((model) => (
                <Card key={model.id}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-base">{model.name}</CardTitle>
                      <Badge variant={model.status === 'available' ? 'success' : 'destructive'}>
                        {model.status}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Provider:</span>
                        <span>{model.provider}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Latency:</span>
                        <span>{model.performance.avg_latency}ms</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Success Rate:</span>
                        <span>{model.performance.success_rate}%</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Cost/1K:</span>
                        <span>${model.cost_per_1k_tokens}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* ==================== INFRASTRUCTURE TAB ==================== */}
          <TabsContent value="infrastructure" className="space-y-4">
            <div className="grid grid-cols-4 gap-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Servers</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {infrastructure?.servers.length || 0}
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Containers</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {infrastructure?.containers || 0}
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Services</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {infrastructure?.services || 0}
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Infra Health</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {infrastructure?.health_score || 100}%
                  </div>
                </CardContent>
              </Card>
            </div>
            
            {/* Server List */}
            <Card>
              <CardHeader>
                <CardTitle>Server Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {infrastructure?.servers.map((server) => (
                    <div key={server.id} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <Server className="w-4 h-4" />
                          <span className="font-medium">{server.name}</span>
                        </div>
                        <Badge variant={server.status === 'online' ? 'success' : 'destructive'}>
                          {server.status}
                        </Badge>
                      </div>
                      <div className="grid grid-cols-4 gap-4">
                        <div>
                          <div className="text-xs text-gray-500">CPU</div>
                          <Progress value={server.cpu} className="h-1 mt-1" />
                          <div className="text-xs mt-1">{server.cpu}%</div>
                        </div>
                        <div>
                          <div className="text-xs text-gray-500">Memory</div>
                          <Progress value={server.memory} className="h-1 mt-1" />
                          <div className="text-xs mt-1">{server.memory}%</div>
                        </div>
                        <div>
                          <div className="text-xs text-gray-500">Disk</div>
                          <Progress value={server.disk} className="h-1 mt-1" />
                          <div className="text-xs mt-1">{server.disk}%</div>
                        </div>
                        <div>
                          <div className="text-xs text-gray-500">Network</div>
                          <Progress value={server.network} className="h-1 mt-1" />
                          <div className="text-xs mt-1">{server.network}%</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* ==================== MONITORING TAB ==================== */}
          <TabsContent value="monitoring" className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle>System Metrics</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Real-time metrics would update here */}
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Request Rate</span>
                        <span>1,234 req/s</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Error Rate</span>
                        <span className="text-red-600">0.02%</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Avg Latency</span>
                        <span>124ms</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Active Connections</span>
                        <span>847</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader>
                  <CardTitle>Recent Alerts</CardTitle>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-[300px]">
                    <div className="space-y-2">
                      {alerts.slice(0, 10).map((alert, idx) => (
                        <div key={idx} className="p-2 border rounded">
                          <div className="flex items-start space-x-2">
                            <AlertCircle className={`w-4 h-4 mt-0.5 ${
                              alert.level === 'error' ? 'text-red-500' :
                              alert.level === 'warning' ? 'text-yellow-500' :
                              'text-blue-500'
                            }`} />
                            <div className="flex-1">
                              <p className="text-sm">{alert.message}</p>
                              <p className="text-xs text-gray-500">{alert.timestamp}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* ==================== HISTORY TAB ==================== */}
          <TabsContent value="history" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Command History</CardTitle>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[600px]">
                  <div className="space-y-2">
                    {commandHistory.map((entry, idx) => (
                      <div key={idx} className="border rounded-lg p-3">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-2">
                              {entry.type === 'command' ? (
                                <Terminal className="w-4 h-4 text-blue-500" />
                              ) : (
                                <CheckCircle className="w-4 h-4 text-green-500" />
                              )}
                              <span className="font-mono text-sm">{entry.text || entry.command}</span>
                            </div>
                            {entry.result && (
                              <div className="mt-2 p-2 bg-gray-50 dark:bg-gray-800 rounded text-sm">
                                <pre>{JSON.stringify(entry.result, null, 2)}</pre>
                              </div>
                            )}
                          </div>
                          <span className="text-xs text-gray-500">{entry.timestamp}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      {/* ==================== SELECTED SYSTEM DETAILS (Floating Panel) ==================== */}
      {selectedSystem && (
        <div className="fixed right-4 top-24 w-96 bg-white dark:bg-gray-900 rounded-lg shadow-2xl border p-4 z-40">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold">System Details</h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSelectedSystem(null)}
            >
              <XCircle className="w-4 h-4" />
            </Button>
          </div>
          
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              {getSystemIcon(selectedSystem.type)}
              <span className="font-medium">{selectedSystem.name}</span>
              {getStatusIcon(selectedSystem.status)}
            </div>
            
            <Separator />
            
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">ID:</span>
                <code className="text-xs">{selectedSystem.id}</code>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Type:</span>
                <Badge>{selectedSystem.type}</Badge>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Status:</span>
                <Badge variant={selectedSystem.status === 'active' ? 'success' : 'default'}>
                  {selectedSystem.status}
                </Badge>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Errors:</span>
                <span>{selectedSystem.error_count}</span>
              </div>
            </div>
            
            <Separator />
            
            <div>
              <h4 className="font-medium mb-2">Capabilities</h4>
              <div className="flex flex-wrap gap-1">
                {selectedSystem.capabilities.map((cap) => (
                  <Badge key={cap} variant="secondary" className="text-xs">
                    {cap}
                  </Badge>
                ))}
              </div>
            </div>
            
            <Separator />
            
            <div className="space-y-2">
              <Button className="w-full" size="sm">
                <RefreshCw className="w-4 h-4 mr-2" />
                Restart
              </Button>
              <Button className="w-full" size="sm" variant="outline">
                <Settings className="w-4 h-4 mr-2" />
                Configure
              </Button>
              <Button className="w-full" size="sm" variant="destructive">
                <Trash2 className="w-4 h-4 mr-2" />
                Terminate
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UnifiedSuperDashboard;