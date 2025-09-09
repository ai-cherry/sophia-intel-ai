'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useOrchestratorCoordination } from '@/hooks/useOrchestratorCoordination';
import { TaskFlowVisualization } from './TaskFlowVisualization';
import {
  Brain, Zap, Cpu, Activity, GitBranch, ArrowRight,
  AlertTriangle, CheckCircle, Clock, Users, Target,
  Briefcase, Code, TrendingUp, Workflow, Crown, Shield
} from 'lucide-react';

interface OrchestratorStatus {
  id: string;
  name: string;
  type: 'sophia';
  status: 'active' | 'idle' | 'overloaded' | 'error';
  activeTasks: number;
  maxTasks: number;
  queueSize: number;
  performance: number;
  uptime: number;
  domain: string;
  icon: React.ComponentType<any>;
  color: string;
}

interface TaskBridge {
  sourceOrchestrator: string;
  targetOrchestrator: string;
  taskType: string;
  priority: 'high' | 'medium' | 'low';
  status: 'pending' | 'in_transit' | 'delivered' | 'failed';
  contextPreserved: boolean;
  payReadyContext?: boolean;
}

interface CoordinationMetrics {
  totalTasks: number;
  taskFlowRate: number;
  resourceUtilization: number;
  bridgeHealth: number;
  synchronizationLag: number;
  bottleneckCount: number;
}

const OrchestratorCoordinationView: React.FC = () => {
  const {
    orchestrators,
    taskBridges,
    coordinationMetrics,
    isConnected,
    error
  } = useOrchestratorCoordination();

  const [selectedView, setSelectedView] = useState<'overview' | 'flow' | 'metrics' | 'resources'>('overview');
  const [timeRange, setTimeRange] = useState<'1h' | '6h' | '24h' | '7d'>('1h');

  // Mock data for demonstration
  const mockOrchestrators: OrchestratorStatus[] = [
    {
      id: 'sophia-001',
      name: 'Sophia Business Intelligence',
      type: 'sophia',
      status: 'active',
      activeTasks: 6,
      maxTasks: 8,
      queueSize: 3,
      performance: 94,
      uptime: 99.8,
      domain: 'Business Intelligence & Analytics',
      icon: Crown,
      color: 'text-purple-600'
    },
    // Additional orchestrators can be added here
  ];

  const mockTaskBridges: TaskBridge[] = [
    {
      sourceOrchestrator: 'sophia-001',
      targetOrchestrator: 'sophia-002',
      taskType: 'Pay Ready Implementation',
      priority: 'high',
      status: 'in_transit',
      contextPreserved: true,
      payReadyContext: true
    },
    {
      sourceOrchestrator: 'sophia-002',
      targetOrchestrator: 'sophia-001',
      taskType: 'Performance Analytics',
      priority: 'medium',
      status: 'delivered',
      contextPreserved: true
    }
  ];

  const mockMetrics: CoordinationMetrics = {
    totalTasks: 156,
    taskFlowRate: 23.4,
    resourceUtilization: 87,
    bridgeHealth: 96,
    synchronizationLag: 120,
    bottleneckCount: 2
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-500';
      case 'idle': return 'text-gray-500';
      case 'overloaded': return 'text-orange-500';
      case 'error': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'active': return 'default';
      case 'idle': return 'secondary';
      case 'overloaded': return 'destructive';
      case 'error': return 'destructive';
      default: return 'secondary';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'text-red-500';
      case 'medium': return 'text-yellow-500';
      case 'low': return 'text-green-500';
      default: return 'text-gray-500';
    }
  };

  const renderOrchestratorCard = (orchestrator: OrchestratorStatus) => {
    const Icon = orchestrator.icon;
    const utilizationPercentage = (orchestrator.activeTasks / orchestrator.maxTasks) * 100;

    return (
      <Card key={orchestrator.id} className="relative overflow-hidden">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg bg-gray-100 ${orchestrator.color}`}>
                <Icon className="h-6 w-6" />
              </div>
              <div>
                <CardTitle className="text-lg font-semibold">
                  {orchestrator.name}
                </CardTitle>
                <p className="text-sm text-gray-500 mt-1">
                  {orchestrator.domain}
                </p>
              </div>
            </div>
            <Badge variant={getStatusBadgeVariant(orchestrator.status)}>
              {orchestrator.status.toUpperCase()}
            </Badge>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Resource Utilization */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium">Active Tasks</span>
              <span className="text-sm text-gray-500">
                {orchestrator.activeTasks}/{orchestrator.maxTasks}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-300 ${
                  utilizationPercentage > 80 ? 'bg-red-500' :
                  utilizationPercentage > 60 ? 'bg-yellow-500' : 'bg-green-500'
                }`}
                style={{ width: `${utilizationPercentage}%` }}
              />
            </div>
          </div>

          {/* Queue Status */}
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-gray-400" />
              <span className="text-sm">Queue Size</span>
            </div>
            <Badge variant={orchestrator.queueSize > 5 ? "destructive" : "outline"}>
              {orchestrator.queueSize}
            </Badge>
          </div>

          {/* Performance Metrics */}
          <div className="grid grid-cols-2 gap-4 pt-2 border-t">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {orchestrator.performance}%
              </div>
              <div className="text-xs text-gray-500">Performance</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {orchestrator.uptime}%
              </div>
              <div className="text-xs text-gray-500">Uptime</div>
            </div>
          </div>
        </CardContent>

        {/* Orchestrator Type Indicator */}
        <div className={`absolute top-0 right-0 w-1 h-full ${
          orchestrator.type === 'sophia' ? 'bg-purple-500' : 'bg-green-500'
        }`} />
      </Card>
    );
  };

  const renderBridgeStatus = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <GitBranch className="h-5 w-5" />
          Coordination Bridge Status
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {mockTaskBridges.map((bridge, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1">
                  <span className="text-sm font-medium capitalize">
                    {bridge.sourceOrchestrator.split('-')[0]}
                  </span>
                  <ArrowRight className="h-4 w-4 text-gray-400" />
                  <span className="text-sm font-medium capitalize">
                    {bridge.targetOrchestrator.split('-')[0]}
                  </span>
                </div>
                <Badge variant="outline" className={getPriorityColor(bridge.priority)}>
                  {bridge.priority}
                </Badge>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">{bridge.taskType}</span>
                {bridge.payReadyContext && (
                  <Badge className="bg-blue-100 text-blue-800">Pay Ready</Badge>
                )}
                {bridge.status === 'delivered' ? (
                  <CheckCircle className="h-4 w-4 text-green-500" />
                ) : bridge.status === 'failed' ? (
                  <AlertTriangle className="h-4 w-4 text-red-500" />
                ) : (
                  <Activity className="h-4 w-4 text-blue-500 animate-pulse" />
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );

  const renderCoordinationMetrics = () => (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Tasks</p>
              <p className="text-2xl font-bold">{mockMetrics.totalTasks}</p>
            </div>
            <Target className="h-8 w-8 text-blue-500" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Flow Rate</p>
              <p className="text-2xl font-bold">{mockMetrics.taskFlowRate}/min</p>
            </div>
            <TrendingUp className="h-8 w-8 text-green-500" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Bridge Health</p>
              <p className="text-2xl font-bold">{mockMetrics.bridgeHealth}%</p>
            </div>
            <Shield className="h-8 w-8 text-purple-500" />
          </div>
        </CardContent>
      </Card>
    </div>
  );

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Workflow className="h-8 w-8 text-blue-600" />
            Orchestrator Coordination
          </h1>
          <p className="text-gray-600 mt-2">
            Real-time visualization of Sophia-Artemis orchestrator interactions and resource allocation
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Connection Status */}
          <Badge variant={isConnected ? "default" : "destructive"} className="mr-4">
            {isConnected ? "Connected" : "Disconnected"}
          </Badge>

          {/* Time Range Selector */}
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value as any)}
            className="px-3 py-1 border rounded-md text-sm"
          >
            <option value="1h">Last Hour</option>
            <option value="6h">Last 6 Hours</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
          </select>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-red-800">
              <AlertTriangle className="h-4 w-4" />
              <span className="font-medium">Connection Error: {error}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Navigation Tabs */}
      <Tabs value={selectedView} onValueChange={(value: unknown) => setSelectedView(value)}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="flow">Task Flow</TabsTrigger>
          <TabsTrigger value="metrics">Metrics</TabsTrigger>
          <TabsTrigger value="resources">Resources</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Coordination Metrics */}
          {renderCoordinationMetrics()}

          {/* Orchestrator Status Cards */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {mockOrchestrators.map(renderOrchestratorCard)}
          </div>

          {/* Bridge Status */}
          {renderBridgeStatus()}
        </TabsContent>

        <TabsContent value="flow" className="space-y-6">
          <TaskFlowVisualization
            orchestrators={mockOrchestrators}
            taskBridges={mockTaskBridges}
            timeRange={timeRange}
          />
        </TabsContent>

        <TabsContent value="metrics" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Resource Utilization</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between mb-2">
                      <span>Overall Utilization</span>
                      <span>{mockMetrics.resourceUtilization}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="h-2 bg-blue-500 rounded-full"
                        style={{ width: `${mockMetrics.resourceUtilization}%` }}
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between mb-2">
                      <span>Sync Lag</span>
                      <span>{mockMetrics.synchronizationLag}ms</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          mockMetrics.synchronizationLag > 200 ? 'bg-red-500' :
                          mockMetrics.synchronizationLag > 100 ? 'bg-yellow-500' : 'bg-green-500'
                        }`}
                        style={{ width: `${Math.min((mockMetrics.synchronizationLag / 500) * 100, 100)}%` }}
                      />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Bottleneck Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span>Active Bottlenecks</span>
                    <Badge variant={mockMetrics.bottleneckCount > 0 ? "destructive" : "default"}>
                      {mockMetrics.bottleneckCount}
                    </Badge>
                  </div>

                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4 text-orange-500" />
                      <span>Artemis Queue Saturation (7/8 tasks)</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4 text-yellow-500" />
                      <span>Cross-domain Context Transfer Delay</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="resources" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {mockOrchestrators.map((orchestrator) => (
              <Card key={`resource-${orchestrator.id}`}>
                <CardHeader>
                  <CardTitle className="text-lg">{orchestrator.name} Resources</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-medium">Task Allocation</label>
                      <div className="mt-2 space-y-1">
                        {Array.from({ length: orchestrator.maxTasks }, (_, i) => (
                          <div
                            key={i}
                            className={`h-3 rounded ${
                              i < orchestrator.activeTasks
                                ? orchestrator.type === 'sophia' ? 'bg-purple-500' : 'bg-green-500'
                                : 'bg-gray-200'
                            }`}
                          />
                        ))}
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4 pt-4 border-t">
                      <div className="text-center">
                        <div className="text-lg font-bold">{orchestrator.activeTasks}</div>
                        <div className="text-xs text-gray-500">Active</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-bold">{orchestrator.maxTasks - orchestrator.activeTasks}</div>
                        <div className="text-xs text-gray-500">Available</div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default OrchestratorCoordinationView;