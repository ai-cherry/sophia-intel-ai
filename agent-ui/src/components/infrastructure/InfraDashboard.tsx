import React, { useState } from 'react';
import { useDashboardData } from '@/hooks/useDashboardData';
import {
  Shield,
  Server,
  Database,
  GitBranch,
  Activity,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  Lock,
  Key,
  Terminal,
  Cloud
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';

// TypeScript interfaces
interface ServiceStatus {
  name: string;
  health: 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
  latency_ms: number;
  last_check: string;
  details: Record<string, any>;
  error?: string;
}

interface SecretRotation {
  service: string;
  last_rotation: string;
  next_rotation: string;
  status: 'current' | 'warning' | 'critical';
  age_hours: number;
  rotation_count: number;
  active_version: string;
}

interface PulumiStack {
  name: string;
  status: 'running' | 'succeeded' | 'failed' | 'pending';
  last_update: string;
  resources: number;
  preview_available: boolean;
}

interface SwarmAgent {
  name: string;
  role: string;
  tasks_completed: number;
  success_rate: number;
  avg_response_time_ms: number;
}

interface InfrastructureMetrics {
  services: ServiceStatus[];
  secret_rotations: SecretRotation[];
  pulumi_stacks: PulumiStack[];
  swarm_agents: SwarmAgent[];
  system_health: {
    overall: 'healthy' | 'degraded' | 'critical';
    score: number;
    issues: string[];
  };
}

// Utility functions
const getServiceIcon = (serviceName: string) => {
  const icons: Record<string, JSX.Element> = {
    'lambda-labs': <Server className="h-4 w-4" />,
    'weaviate': <Database className="h-4 w-4" />,
    'neon': <Database className="h-4 w-4" />,
    'github': <GitBranch className="h-4 w-4" />,
    'redis': <Database className="h-4 w-4" />,
    'airbyte': <Cloud className="h-4 w-4" />,
    'default': <Activity className="h-4 w-4" />
  };
  return icons[serviceName as keyof typeof icons] || icons.default;
};

const getHealthColor = (health: string) => {
  switch (health) {
    case 'healthy': return 'text-green-500';
    case 'degraded': return 'text-yellow-500';
    case 'unhealthy': return 'text-red-500';
    default: return 'text-gray-500';
  }
};

const getHealthIcon = (health: string) => {
  switch (health) {
    case 'healthy': return <CheckCircle className="h-5 w-5 text-green-500" />;
    case 'degraded': return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
    case 'unhealthy': return <XCircle className="h-5 w-5 text-red-500" />;
    default: return <Clock className="h-5 w-5 text-gray-500" />;
  }
};

const getStackStatusColor = (status: string) => {
  switch (status) {
    case 'succeeded': return 'bg-green-100 text-green-800';
    case 'running': return 'bg-blue-100 text-blue-800';
    case 'failed': return 'bg-red-100 text-red-800';
    default: return 'bg-gray-100 text-gray-800';
  }
};

export const InfraDashboard: React.FC = () => {
  const [selectedTimeRange, setSelectedTimeRange] = useState('24h');
  const [selectedService, setSelectedService] = useState<string | null>(null);
  const [showEmergencyRotation, setShowEmergencyRotation] = useState(false);

  // Fetch infrastructure metrics via shared hook (30s refresh handled by UI actions)
  const { data: metrics, loading: isLoading, error, refetch } = useDashboardData<InfrastructureMetrics>(
    `/api/infrastructure/metrics?range=${selectedTimeRange}`,
    [selectedTimeRange],
    { category: 'api.infra.metrics' }
  );

  // Mutations implemented with simple fetch helpers
  const emergencyRotate = async ({ service, reason }: { service: string; reason: string }) => {
    await fetch('/api/infrastructure/emergency-rotation', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ service, reason }),
    });
    refetch();
    setShowEmergencyRotation(false);
  };

  const stackOperation = async ({ stack, operation }: { stack: string; operation: string }) => {
    await fetch('/api/infrastructure/stack-operation', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ stack, operation }),
    });
    refetch();
  };

  const swarmTask = async ({ type, description, context }: any) => {
    await fetch('/api/infrastructure/swarm-task', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type, description, context, require_approval: true }),
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="animate-spin h-8 w-8 text-blue-500" />
        <span className="ml-2 text-gray-600">Loading infrastructure status...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <XCircle className="h-5 w-5 text-red-500 mr-2" />
          <span className="text-red-700">Failed to load infrastructure metrics</span>
        </div>
      </div>
    );
  }

  // Generate chart data
  const latencyData = metrics?.services.map(s => ({
    name: s.name,
    latency: s.latency_ms
  })) || [];

  return (
    <div className="space-y-6 p-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Infrastructure Control Center</h1>
            <p className="text-gray-500 mt-1">2025 Hardened Infrastructure Management</p>
          </div>
          <div className="flex items-center space-x-4">
            {/* System Health Score */}
            <div className="text-center">
              <div className={`text-2xl font-bold ${
                metrics?.system_health.score >= 90 ? 'text-green-500' :
                metrics?.system_health.score >= 70 ? 'text-yellow-500' : 'text-red-500'
              }`}>
                {metrics?.system_health.score}%
              </div>
              <div className="text-sm text-gray-500">Health Score</div>
            </div>

            {/* Time Range Selector */}
            <div className="flex space-x-2">
              {['1h', '24h', '7d', '30d'].map((range) => (
                <button
                  key={range}
                  className={`px-3 py-1 rounded ${
                    selectedTimeRange === range
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                  onClick={() => setSelectedTimeRange(range)}
                >
                  {range}
                </button>
              ))}
            </div>

            {/* Refresh Button */}
            <button
              onClick={() => refetch()}
              className="p-2 bg-gray-200 rounded hover:bg-gray-300"
            >
              <RefreshCw className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Service Health Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {metrics?.services.map((service) => (
          <div
            key={service.name}
            className="bg-white rounded-lg shadow-sm p-4 hover:shadow-md transition-shadow cursor-pointer"
            onClick={() => setSelectedService(service.name)}
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center">
                {getServiceIcon(service.name)}
                <span className="ml-2 font-medium text-gray-900">{service.name}</span>
              </div>
              {getHealthIcon(service.health)}
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Status</span>
                <span className={getHealthColor(service.health)}>{service.health}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Latency</span>
                <span className="text-gray-900">{service.latency_ms.toFixed(2)}ms</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Last Check</span>
                <span className="text-gray-900">
                  {new Date(service.last_check).toLocaleTimeString()}
                </span>
              </div>

              {service.health !== 'healthy' && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    emergencyRotate({ service: service.name, reason: 'Service degradation detected' });
                  }}
                  className="w-full mt-2 px-3 py-1 bg-orange-500 text-white rounded hover:bg-orange-600 text-sm"
                >
                  Emergency Rotate
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Secret Rotation Status */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center mb-4">
          <Lock className="h-5 w-5 text-gray-700 mr-2" />
          <h2 className="text-xl font-semibold">Secret Rotation Schedule</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {metrics?.secret_rotations.map((rotation) => (
            <div key={rotation.service} className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium">{rotation.service}</span>
                <span className={`px-2 py-1 rounded text-xs ${
                  rotation.status === 'current' ? 'bg-green-100 text-green-800' :
                  rotation.status === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {rotation.status}
                </span>
              </div>

              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Age</span>
                  <span>{rotation.age_hours.toFixed(1)}h</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Rotations</span>
                  <span>{rotation.rotation_count}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Version</span>
                  <span className="font-mono text-xs">{rotation.active_version}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Next</span>
                  <span>{new Date(rotation.next_rotation).toLocaleDateString()}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* AGNO InfraOps Swarm Status */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center mb-4">
          <Terminal className="h-5 w-5 text-gray-700 mr-2" />
          <h2 className="text-xl font-semibold">InfraOps Swarm Agents</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
          {metrics?.swarm_agents.map((agent) => (
            <div key={agent.name} className="border rounded-lg p-3">
              <div className="font-medium text-gray-900 mb-2">{agent.name}</div>
              <div className="text-xs text-gray-500 mb-2">{agent.role}</div>
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-gray-500">Tasks</span>
                  <span>{agent.tasks_completed}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-gray-500">Success</span>
                  <span className={agent.success_rate >= 0.95 ? 'text-green-600' : 'text-yellow-600'}>
                    {(agent.success_rate * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-gray-500">Latency</span>
                  <span>{agent.avg_response_time_ms.toFixed(2)}ms</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Swarm Task Executor */}
        <div className="mt-4 flex space-x-2">
          <button
            onClick={() => swarmTask({
              type: 'health_check',
              description: 'System-wide health check',
              context: { scope: 'all' }
            })}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Run Health Check
          </button>
          <button
            onClick={() => swarmTask({
              type: 'security_scan',
              description: 'Security vulnerability scan',
              context: { severity_threshold: 'medium' }
            })}
            className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600"
          >
            Security Scan
          </button>
          <button
            onClick={() => swarmTask({
              type: 'backup',
              description: 'Create system backup',
              context: { include: ['databases', 'configs'] }
            })}
            className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
          >
            Backup System
          </button>
        </div>
      </div>

      {/* Pulumi Stack Management */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center mb-4">
          <Server className="h-5 w-5 text-gray-700 mr-2" />
          <h2 className="text-xl font-semibold">Pulumi Stack Operations</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {metrics?.pulumi_stacks.map((stack) => (
            <div key={stack.name} className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-medium">{stack.name}</h3>
                <span className={`px-2 py-1 rounded text-xs ${getStackStatusColor(stack.status)}`}>
                  {stack.status}
                </span>
              </div>

              <div className="space-y-1 text-sm mb-3">
                <div className="flex justify-between">
                  <span className="text-gray-500">Resources</span>
                  <span>{stack.resources}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Last Update</span>
                  <span>{new Date(stack.last_update).toLocaleString()}</span>
                </div>
              </div>

              <div className="flex space-x-2">
                <button
                  onClick={() => stackOperation({ stack: stack.name, operation: 'preview' })}
                  className="flex-1 px-2 py-1 border border-gray-300 rounded hover:bg-gray-50 text-sm"
                >
                  Preview
                </button>
                <button
                  onClick={() => stackOperation({ stack: stack.name, operation: 'up' })}
                  className="flex-1 px-2 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm"
                >
                  Deploy
                </button>
                <button
                  onClick={() => stackOperation({ stack: stack.name, operation: 'refresh' })}
                  className="flex-1 px-2 py-1 border border-gray-300 rounded hover:bg-gray-50 text-sm"
                >
                  Refresh
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Performance Chart */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-semibold mb-4">Service Latency Overview</h2>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={latencyData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis label={{ value: 'Latency (ms)', angle: -90, position: 'insideLeft' }} />
            <Tooltip />
            <Area type="monotone" dataKey="latency" stroke="#3B82F6" fill="#93C5FD" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
