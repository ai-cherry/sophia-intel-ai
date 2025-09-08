'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  ArrowRight, ArrowDown, ArrowUp, Circle, Square,
  AlertTriangle, CheckCircle, Clock, Zap, Crown,
  Code, Briefcase, TrendingUp, Activity, Target,
  GitBranch, Workflow, Cpu, Brain
} from 'lucide-react';

interface OrchestratorStatus {
  id: string;
  name: string;
  type: 'sophia' | 'artemis';
  status: 'active' | 'idle' | 'overloaded' | 'error';
  activeTasks: number;
  maxTasks: number;
  queueSize: number;
  performance: number;
  position: { x: number; y: number };
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

interface FlowPath {
  id: string;
  from: { x: number; y: number };
  to: { x: number; y: number };
  priority: 'high' | 'medium' | 'low';
  status: string;
  taskType: string;
  animated: boolean;
}

interface TaskFlowVisualizationProps {
  orchestrators: OrchestratorStatus[];
  taskBridges: TaskBridge[];
  timeRange: string;
}

interface TaskNode {
  id: string;
  type: 'sophia' | 'artemis' | 'bridge';
  x: number;
  y: number;
  width: number;
  height: number;
  label: string;
  status: string;
  activeTasks?: number;
  maxTasks?: number;
  queueSize?: number;
}

const TaskFlowVisualization: React.FC<TaskFlowVisualizationProps> = ({
  orchestrators,
  taskBridges,
  timeRange
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [flowPaths, setFlowPaths] = useState<FlowPath[]>([]);
  const [animationEnabled, setAnimationEnabled] = useState(true);
  const [viewMode, setViewMode] = useState<'flow' | 'queue' | 'performance'>('flow');

  // SVG dimensions
  const svgWidth = 800;
  const svgHeight = 600;

  // Create task nodes from orchestrators
  const createTaskNodes = (): TaskNode[] => {
    const nodes: TaskNode[] = [];

    // Sophia orchestrator (left side)
    const sophiaOrch = orchestrators.find(o => o.type === 'sophia');
    if (sophiaOrch) {
      nodes.push({
        id: sophiaOrch.id,
        type: 'sophia',
        x: 100,
        y: 150,
        width: 180,
        height: 120,
        label: 'Sophia\nBusiness Intelligence',
        status: sophiaOrch.status,
        activeTasks: sophiaOrch.activeTasks,
        maxTasks: sophiaOrch.maxTasks,
        queueSize: sophiaOrch.queueSize
      });
    }

    // Artemis orchestrator (right side)
    const artemisOrch = orchestrators.find(o => o.type === 'artemis');
    if (artemisOrch) {
      nodes.push({
        id: artemisOrch.id,
        type: 'artemis',
        x: 520,
        y: 150,
        width: 180,
        height: 120,
        label: 'Artemis\nCode Excellence',
        status: artemisOrch.status,
        activeTasks: artemisOrch.activeTasks,
        maxTasks: artemisOrch.maxTasks,
        queueSize: artemisOrch.queueSize
      });
    }

    // Coordination bridge (center)
    nodes.push({
      id: 'coordination-bridge',
      type: 'bridge',
      x: 350,
      y: 80,
      width: 100,
      height: 60,
      label: 'Coordination\nBridge',
      status: 'active'
    });

    return nodes;
  };

  const nodes = createTaskNodes();

  // Generate flow paths based on task bridges
  useEffect(() => {
    const paths: FlowPath[] = [];

    taskBridges.forEach((bridge, index) => {
      const sourceNode = nodes.find(n => n.id === bridge.sourceOrchestrator);
      const targetNode = nodes.find(n => n.id === bridge.targetOrchestrator);
      const bridgeNode = nodes.find(n => n.type === 'bridge');

      if (sourceNode && targetNode && bridgeNode) {
        // Path from source to bridge
        paths.push({
          id: `${bridge.sourceOrchestrator}-to-bridge-${index}`,
          from: {
            x: sourceNode.x + sourceNode.width/2,
            y: sourceNode.y + sourceNode.height/2
          },
          to: {
            x: bridgeNode.x + bridgeNode.width/2,
            y: bridgeNode.y + bridgeNode.height/2
          },
          priority: bridge.priority,
          status: bridge.status,
          taskType: bridge.taskType,
          animated: bridge.status === 'in_transit'
        });

        // Path from bridge to target
        paths.push({
          id: `bridge-to-${bridge.targetOrchestrator}-${index}`,
          from: {
            x: bridgeNode.x + bridgeNode.width/2,
            y: bridgeNode.y + bridgeNode.height/2
          },
          to: {
            x: targetNode.x + targetNode.width/2,
            y: targetNode.y + targetNode.height/2
          },
          priority: bridge.priority,
          status: bridge.status,
          taskType: bridge.taskType,
          animated: bridge.status === 'in_transit'
        });
      }
    });

    setFlowPaths(paths);
  }, [taskBridges, nodes]);

  const getNodeColor = (node: TaskNode) => {
    switch (node.type) {
      case 'sophia':
        return node.status === 'active' ? '#8B5CF6' : '#6B7280';
      case 'artemis':
        return node.status === 'active' ? '#10B981' : '#6B7280';
      case 'bridge':
        return '#3B82F6';
      default:
        return '#6B7280';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return '#EF4444';
      case 'medium': return '#F59E0B';
      case 'low': return '#10B981';
      default: return '#6B7280';
    }
  };

  const getUtilizationColor = (activeTasks: number, maxTasks: number) => {
    const utilization = activeTasks / maxTasks;
    if (utilization > 0.8) return '#EF4444';
    if (utilization > 0.6) return '#F59E0B';
    return '#10B981';
  };

  const renderNode = (node: TaskNode) => {
    const isSelected = selectedNode === node.id;
    const nodeColor = getNodeColor(node);

    return (
      <g
        key={node.id}
        transform={`translate(${node.x}, ${node.y})`}
        className="cursor-pointer"
        onClick={() => setSelectedNode(isSelected ? null : node.id)}
      >
        {/* Node background */}
        <rect
          x={0}
          y={0}
          width={node.width}
          height={node.height}
          fill={nodeColor}
          fillOpacity={isSelected ? 0.8 : 0.6}
          stroke={isSelected ? '#1D4ED8' : nodeColor}
          strokeWidth={isSelected ? 3 : 1}
          rx={8}
          className="transition-all duration-300"
        />

        {/* Node icon */}
        <circle
          cx={node.width / 2}
          cy={25}
          r={12}
          fill="white"
          fillOpacity={0.9}
        />

        {node.type === 'sophia' && (
          <text
            x={node.width / 2}
            y={30}
            textAnchor="middle"
            className="fill-purple-600 text-xs font-bold"
          >
            👑
          </text>
        )}

        {node.type === 'artemis' && (
          <text
            x={node.width / 2}
            y={30}
            textAnchor="middle"
            className="fill-green-600 text-xs font-bold"
          >
            ⚡
          </text>
        )}

        {node.type === 'bridge' && (
          <text
            x={node.width / 2}
            y={30}
            textAnchor="middle"
            className="fill-blue-600 text-xs font-bold"
          >
            🌉
          </text>
        )}

        {/* Node label */}
        <text
          x={node.width / 2}
          y={50}
          textAnchor="middle"
          className="fill-white text-xs font-medium"
        >
          {node.label.split('\n').map((line, i) => (
            <tspan key={i} x={node.width / 2} dy={i === 0 ? 0 : 12}>
              {line}
            </tspan>
          ))}
        </text>

        {/* Task utilization for orchestrators */}
        {node.type !== 'bridge' && node.activeTasks !== undefined && node.maxTasks !== undefined && (
          <g transform={`translate(10, ${node.height - 30})`}>
            {/* Task slots visualization */}
            {Array.from({ length: node.maxTasks }, (_, i) => (
              <rect
                key={i}
                x={i * 18}
                y={0}
                width={14}
                height={8}
                fill={i < node.activeTasks ? getUtilizationColor(node.activeTasks, node.maxTasks) : '#374151'}
                fillOpacity={i < node.activeTasks ? 0.9 : 0.3}
                rx={2}
              />
            ))}

            {/* Task count text */}
            <text
              x={node.maxTasks * 9}
              y={6}
              className="fill-white text-xs"
              textAnchor="middle"
            >
              {node.activeTasks}/{node.maxTasks}
            </text>
          </g>
        )}

        {/* Queue indicator */}
        {node.queueSize !== undefined && node.queueSize > 0 && (
          <circle
            cx={node.width - 15}
            cy={15}
            r={8}
            fill="#F59E0B"
            className="animate-pulse"
          />
        )}
        {node.queueSize !== undefined && node.queueSize > 0 && (
          <text
            x={node.width - 15}
            y={19}
            textAnchor="middle"
            className="fill-white text-xs font-bold"
          >
            {node.queueSize}
          </text>
        )}
      </g>
    );
  };

  const renderFlowPath = (path: FlowPath) => {
    const midX = (path.from.x + path.to.x) / 2;
    const midY = Math.min(path.from.y, path.to.y) - 20;

    return (
      <g key={path.id}>
        {/* Flow path */}
        <path
          d={`M ${path.from.x} ${path.from.y} Q ${midX} ${midY} ${path.to.x} ${path.to.y}`}
          stroke={getPriorityColor(path.priority)}
          strokeWidth={3}
          fill="none"
          strokeDasharray={path.animated ? "5,5" : "none"}
          className={path.animated ? "animate-pulse" : ""}
        />

        {/* Arrow marker */}
        <polygon
          points={`${path.to.x-8},${path.to.y-4} ${path.to.x},${path.to.y} ${path.to.x-8},${path.to.y+4}`}
          fill={getPriorityColor(path.priority)}
        />

        {/* Task type label */}
        <text
          x={midX}
          y={midY - 10}
          textAnchor="middle"
          className="text-xs font-medium"
          fill="#374151"
        >
          {path.taskType}
        </text>
      </g>
    );
  };

  const renderQueueVisualization = () => {
    return (
      <div className="grid grid-cols-2 gap-6">
        {orchestrators.map((orchestrator) => (
          <Card key={orchestrator.id}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {orchestrator.type === 'sophia' ? <Crown className="h-5 w-5 text-purple-600" /> : <Code className="h-5 w-5 text-green-600" />}
                {orchestrator.name} Queue
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {/* Active tasks */}
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium">Active Tasks</span>
                    <span className="text-sm">{orchestrator.activeTasks}/{orchestrator.maxTasks}</span>
                  </div>
                  <div className="grid grid-cols-8 gap-1">
                    {Array.from({ length: orchestrator.maxTasks }, (_, i) => (
                      <div
                        key={i}
                        className={`h-8 rounded-sm flex items-center justify-center text-xs font-medium ${
                          i < orchestrator.activeTasks
                            ? orchestrator.type === 'sophia'
                              ? 'bg-purple-500 text-white'
                              : 'bg-green-500 text-white'
                            : 'bg-gray-200 text-gray-500'
                        }`}
                      >
                        {i < orchestrator.activeTasks ? i + 1 : ''}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Queued tasks */}
                {orchestrator.queueSize > 0 && (
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium">Queued Tasks</span>
                      <span className="text-sm">{orchestrator.queueSize}</span>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {Array.from({ length: orchestrator.queueSize }, (_, i) => (
                        <div
                          key={i}
                          className="w-6 h-6 rounded-full bg-yellow-400 flex items-center justify-center text-xs font-medium text-yellow-800"
                        >
                          {i + 1}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  };

  const renderPerformanceView = () => {
    return (
      <div className="space-y-6">
        {/* Performance metrics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Avg Response Time</p>
                  <p className="text-2xl font-bold">287ms</p>
                </div>
                <Clock className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Throughput</p>
                  <p className="text-2xl font-bold">23.4/min</p>
                </div>
                <TrendingUp className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Success Rate</p>
                  <p className="text-2xl font-bold">96.7%</p>
                </div>
                <CheckCircle className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Performance chart placeholder */}
        <Card>
          <CardHeader>
            <CardTitle>Task Flow Performance Over Time</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
              <p className="text-gray-500">Performance chart would be rendered here</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button
            variant={viewMode === 'flow' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setViewMode('flow')}
          >
            <Workflow className="h-4 w-4 mr-1" />
            Flow View
          </Button>
          <Button
            variant={viewMode === 'queue' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setViewMode('queue')}
          >
            <Target className="h-4 w-4 mr-1" />
            Queue View
          </Button>
          <Button
            variant={viewMode === 'performance' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setViewMode('performance')}
          >
            <Activity className="h-4 w-4 mr-1" />
            Performance
          </Button>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAnimationEnabled(!animationEnabled)}
          >
            {animationEnabled ? 'Disable' : 'Enable'} Animation
          </Button>

          {/* Legend */}
          <div className="flex items-center gap-4 ml-4">
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 bg-red-500 rounded"></div>
              <span className="text-xs">High Priority</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 bg-yellow-500 rounded"></div>
              <span className="text-xs">Medium Priority</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 bg-green-500 rounded"></div>
              <span className="text-xs">Low Priority</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main visualization */}
      {viewMode === 'flow' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <GitBranch className="h-5 w-5" />
              Task Flow Diagram
            </CardTitle>
          </CardHeader>
          <CardContent>
            <svg
              ref={svgRef}
              width={svgWidth}
              height={svgHeight}
              className="border rounded-lg bg-gray-50"
            >
              {/* Render flow paths first (behind nodes) */}
              {flowPaths.map(renderFlowPath)}

              {/* Render nodes */}
              {nodes.map(renderNode)}

              {/* Grid lines for reference */}
              <defs>
                <pattern
                  id="grid"
                  width="20"
                  height="20"
                  patternUnits="userSpaceOnUse"
                >
                  <path
                    d="M 20 0 L 0 0 0 20"
                    fill="none"
                    stroke="#E5E7EB"
                    strokeWidth="0.5"
                    opacity="0.3"
                  />
                </pattern>
              </defs>
              <rect
                width="100%"
                height="100%"
                fill="url(#grid)"
                opacity="0.5"
              />
            </svg>
          </CardContent>
        </Card>
      )}

      {viewMode === 'queue' && renderQueueVisualization()}
      {viewMode === 'performance' && renderPerformanceView()}

      {/* Node details panel */}
      {selectedNode && (
        <Card className="border-blue-200 bg-blue-50">
          <CardHeader>
            <CardTitle className="text-blue-800">
              Node Details: {nodes.find(n => n.id === selectedNode)?.label}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-sm font-medium">Status:</span>
                <Badge className="ml-2">
                  {nodes.find(n => n.id === selectedNode)?.status}
                </Badge>
              </div>
              {nodes.find(n => n.id === selectedNode)?.activeTasks !== undefined && (
                <div>
                  <span className="text-sm font-medium">Task Load:</span>
                  <span className="ml-2">
                    {nodes.find(n => n.id === selectedNode)?.activeTasks}/
                    {nodes.find(n => n.id === selectedNode)?.maxTasks}
                  </span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export { TaskFlowVisualization };