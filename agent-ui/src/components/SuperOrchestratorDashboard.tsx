import React, { useState, useEffect, useRef } from 'react';
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
import {
  Activity,
  Brain,
  Terminal,
  Zap,
  Users,
  Server,
  AlertCircle,
  CheckCircle,
  XCircle,
  Loader2,
  Send,
  Bot,
  Network,
  Cpu,
  Eye
} from 'lucide-react';

interface SystemMetrics {
  total_systems: number;
  by_type: Record<string, number>;
  by_status: Record<string, number>;
  health_score: number;
}

interface RegisteredSystem {
  id: string;
  name: string;
  type: string;
  status: string;
  capabilities: string[];
  last_activity: string;
  error_count?: number;
}

interface MicroSwarmConfig {
  agents: string[];
  capabilities: string[];
  max_parallel: number;
}

const SuperOrchestratorDashboard: React.FC = () => {
  // State management
  const [connected, setConnected] = useState(false);
  const [systems, setSystems] = useState<RegisteredSystem[]>([]);
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [commandInput, setCommandInput] = useState('');
  const [commandHistory, setCommandHistory] = useState<any[]>([]);
  const [selectedSystem, setSelectedSystem] = useState<RegisteredSystem | null>(null);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [microSwarms, setMicroSwarms] = useState<Record<string, MicroSwarmConfig>>({});
  
  const ws = useRef<WebSocket | null>(null);
  const commandHistoryRef = useRef<HTMLDivElement>(null);

  // WebSocket connection
  useEffect(() => {
    connectWebSocket();
    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, []);

  const connectWebSocket = () => {
    ws.current = new WebSocket('ws://localhost:8006/ws/orchestrator');
    
    ws.current.onopen = () => {
      setConnected(true);
      // Subscribe to monitoring
      sendCommand({ type: 'subscribe_monitoring' });
      // Get initial overview
      sendCommand({ type: 'get_overview' });
    };

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    };

    ws.current.onclose = () => {
      setConnected(false);
      // Reconnect after 3 seconds
      setTimeout(connectWebSocket, 3000);
    };
  };

  const handleWebSocketMessage = (data: any) => {
    switch (data.type) {
      case 'system_state':
        updateSystemState(data);
        break;
      case 'metrics_update':
        setMetrics(data.metrics.aggregate);
        break;
      case 'command_executed':
        addToCommandHistory(data);
        break;
      case 'alert':
        setAlerts(prev => [data, ...prev].slice(0, 10));
        break;
    }
  };

  const updateSystemState = (data: any) => {
    if (data.overview) {
      // Update systems list
      const systemsList: RegisteredSystem[] = [];
      if (data.overview.registry?.systems) {
        Object.values(data.overview.registry.systems).forEach((sys: any) => {
          systemsList.push(sys);
        });
      }
      setSystems(systemsList);
      
      // Update micro swarms
      if (data.overview.micro_swarms?.types) {
        // Request configs for each type
        data.overview.micro_swarms.types.forEach((type: string) => {
          // Would fetch config here
        });
      }
    }
  };

  const sendCommand = (command: any) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(command));
    }
  };

  const handleNaturalLanguageCommand = () => {
    if (!commandInput.trim()) return;
    
    const command = {
      type: 'natural_language',
      text: commandInput,
      context: {
        selected_system: selectedSystem?.id
      }
    };
    
    sendCommand(command);
    addToCommandHistory({
      command: commandInput,
      timestamp: new Date().toISOString(),
      status: 'sent'
    });
    
    setCommandInput('');
  };

  const addToCommandHistory = (entry: any) => {
    setCommandHistory(prev => [entry, ...prev].slice(0, 50));
    if (commandHistoryRef.current) {
      commandHistoryRef.current.scrollTop = 0;
    }
  };

  const spawnMicroSwarm = (swarmType: string) => {
    sendCommand({
      type: 'spawn_swarm',
      swarm_type: swarmType
    });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
      case 'processing':
        return <Activity className="w-4 h-4 text-green-500" />;
      case 'idle':
        return <CheckCircle className="w-4 h-4 text-blue-500" />;
      case 'error':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'offline':
        return <AlertCircle className="w-4 h-4 text-gray-500" />;
      default:
        return <Loader2 className="w-4 h-4 animate-spin" />;
    }
  };

  const getSystemTypeIcon = (type: string) => {
    switch (type) {
      case 'agent':
        return <Bot className="w-4 h-4" />;
      case 'swarm':
      case 'micro_swarm':
        return <Users className="w-4 h-4" />;
      case 'mcp_server':
        return <Server className="w-4 h-4" />;
      case 'embedding_agent':
        return <Brain className="w-4 h-4" />;
      default:
        return <Cpu className="w-4 h-4" />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-4">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Brain className="w-8 h-8 text-blue-600" />
            <div>
              <h1 className="text-3xl font-bold">SuperOrchestrator Control Center</h1>
              <p className="text-gray-600 dark:text-gray-400">
                Complete visibility and control over all AI systems
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant={connected ? 'success' : 'destructive'}>
              {connected ? 'Connected' : 'Disconnected'}
            </Badge>
            {metrics && (
              <Badge variant="outline">
                Health: {metrics.health_score?.toFixed(0)}%
              </Badge>
            )}
          </div>
        </div>
      </div>

      {/* Natural Language Command Bar */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex space-x-2">
            <Terminal className="w-5 h-5 mt-2.5 text-gray-500" />
            <Input
              placeholder="Enter natural language command... (e.g., 'spawn a code generation swarm', 'show all active agents', 'analyze system health')"
              value={commandInput}
              onChange={(e) => setCommandInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleNaturalLanguageCommand()}
              className="flex-1"
            />
            <Button onClick={handleNaturalLanguageCommand}>
              <Send className="w-4 h-4 mr-2" />
              Execute
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Main Dashboard Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="grid grid-cols-5 w-full">
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
            Micro-Swarms
          </TabsTrigger>
          <TabsTrigger value="monitoring">
            <Activity className="w-4 h-4 mr-2" />
            Monitoring
          </TabsTrigger>
          <TabsTrigger value="history">
            <Terminal className="w-4 h-4 mr-2" />
            Command History
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-4 gap-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Total Systems</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metrics?.total_systems || 0}</div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Active Systems</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">
                  {metrics?.by_status?.active || 0}
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Health Score</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-600">
                  {metrics?.health_score?.toFixed(0) || 0}%
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Errors</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-600">
                  {metrics?.by_status?.error || 0}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* System Type Distribution */}
          <Card>
            <CardHeader>
              <CardTitle>System Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-6 gap-4">
                {Object.entries(metrics?.by_type || {}).map(([type, count]) => (
                  <div key={type} className="text-center">
                    <div className="text-2xl font-bold">{count}</div>
                    <div className="text-sm text-gray-600 capitalize">{type}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Systems Tab */}
        <TabsContent value="systems" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Registered Systems</CardTitle>
              <CardDescription>All AI systems under orchestrator control</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[500px]">
                <div className="space-y-2">
                  {systems.map((system) => (
                    <div
                      key={system.id}
                      className={`p-3 border rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 ${
                        selectedSystem?.id === system.id ? 'border-blue-500' : ''
                      }`}
                      onClick={() => setSelectedSystem(system)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          {getSystemTypeIcon(system.type)}
                          <div>
                            <div className="font-medium">{system.name}</div>
                            <div className="text-sm text-gray-500">{system.id}</div>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          {getStatusIcon(system.status)}
                          <Badge variant="outline">{system.type}</Badge>
                        </div>
                      </div>
                      {system.capabilities.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {system.capabilities.map((cap) => (
                            <Badge key={cap} variant="secondary" className="text-xs">
                              {cap}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Micro-Swarms Tab */}
        <TabsContent value="swarms" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Micro-Swarm Control</CardTitle>
              <CardDescription>Spawn and manage specialized micro-swarms</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                {['code_embedding', 'meta_tagging', 'planning', 'code_generation', 'debugging'].map((swarmType) => (
                  <Card key={swarmType}>
                    <CardHeader>
                      <CardTitle className="text-lg capitalize">
                        {swarmType.replace('_', ' ')} Swarm
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <Button 
                        onClick={() => spawnMicroSwarm(swarmType)}
                        className="w-full"
                      >
                        <Zap className="w-4 h-4 mr-2" />
                        Spawn Swarm
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Monitoring Tab */}
        <TabsContent value="monitoring" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Real-Time Monitoring</CardTitle>
            </CardHeader>
            <CardContent>
              {alerts.length > 0 ? (
                <div className="space-y-2">
                  {alerts.map((alert, idx) => (
                    <Alert key={idx} variant={alert.level === 'critical' ? 'destructive' : 'default'}>
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>
                        {alert.message}
                      </AlertDescription>
                    </Alert>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500">No alerts</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Command History Tab */}
        <TabsContent value="history" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Command History</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[500px]" ref={commandHistoryRef}>
                <div className="space-y-2">
                  {commandHistory.map((entry, idx) => (
                    <div key={idx} className="p-2 border rounded text-sm font-mono">
                      <div className="text-gray-600">{entry.timestamp}</div>
                      <div>{entry.command || entry.text}</div>
                      {entry.result && (
                        <div className="text-green-600">Result: {JSON.stringify(entry.result)}</div>
                      )}
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default SuperOrchestratorDashboard;