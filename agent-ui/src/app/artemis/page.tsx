'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import MCPServerGrid from '@/components/mcp/MCPServerGrid';
import MythologyAgentWidget from '@/components/mythology/MythologyAgentWidget';
import {
  Shield, Target, Activity, AlertTriangle, CheckCircle, XCircle,
  Code, GitBranch, Bug, FileText, Zap, Eye, Settings, Radio,
  Terminal, Server, Database, Cpu, HardDrive, Network, Clock
} from 'lucide-react';

// ==================== ARTEMIS TECHNICAL COMMAND CENTER ====================

interface SystemMetric {
  name: string;
  value: string;
  status: 'healthy' | 'warning' | 'critical';
  trend: 'up' | 'down' | 'stable';
}

interface CodebaseHealth {
  totalFiles: number;
  issuesFound: number;
  issuesFixed: number;
  technicalDebt: number;
  codeQualityScore: number;
  testCoverage: number;
}

interface DeploymentStatus {
  environment: string;
  status: 'deployed' | 'deploying' | 'failed' | 'pending';
  version: string;
  lastDeployment: string;
  uptime: string;
}

const ArtemisCommandCenter: React.FC = () => {
  const [systemMetrics, setSystemMetrics] = useState<SystemMetric[]>([
    { name: 'CPU Usage', value: '23%', status: 'healthy', trend: 'stable' },
    { name: 'Memory', value: '2.1GB / 8GB', status: 'healthy', trend: 'up' },
    { name: 'Disk I/O', value: '145 MB/s', status: 'healthy', trend: 'down' },
    { name: 'Network', value: '12.3 MB/s', status: 'warning', trend: 'up' },
    { name: 'Response Time', value: '124ms', status: 'healthy', trend: 'stable' },
    { name: 'Error Rate', value: '0.02%', status: 'healthy', trend: 'down' }
  ]);

  const [codebaseHealth, setCodebaseHealth] = useState<CodebaseHealth>({
    totalFiles: 1247,
    issuesFound: 23,
    issuesFixed: 18,
    technicalDebt: 15,
    codeQualityScore: 94,
    testCoverage: 87
  });

  const [deployments, setDeployments] = useState<DeploymentStatus[]>([
    {
      environment: 'Production',
      status: 'deployed',
      version: 'v2.4.1',
      lastDeployment: '2 hours ago',
      uptime: '99.98%'
    },
    {
      environment: 'Staging',
      status: 'deployed',
      version: 'v2.5.0-rc.1',
      lastDeployment: '45 minutes ago',
      uptime: '99.95%'
    },
    {
      environment: 'Development',
      status: 'deploying',
      version: 'v2.5.0-beta.3',
      lastDeployment: 'Deploying now',
      uptime: '99.92%'
    }
  ]);

  const [connected, setConnected] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  // Real-time updates simulation
  useEffect(() => {
    const interval = setInterval(() => {
      setSystemMetrics(prev => prev.map(metric => ({
        ...metric,
        value: metric.name === 'CPU Usage'
          ? `${Math.floor(Math.random() * 30 + 15)}%`
          : metric.value
      })));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-500';
      case 'warning': return 'text-yellow-500';
      case 'critical': return 'text-red-500';
      case 'deployed': return 'text-green-500';
      case 'deploying': return 'text-blue-500';
      case 'failed': return 'text-red-500';
      case 'pending': return 'text-yellow-500';
      default: return 'text-gray-500';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'deployed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'warning':
      case 'pending':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      case 'critical':
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'deploying':
        return <Activity className="w-4 h-4 text-blue-500 animate-pulse" />;
      default:
        return <AlertTriangle className="w-4 h-4 text-gray-500" />;
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return '↗';
      case 'down': return '↘';
      default: return '→';
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <div className="border-b border-gray-800 bg-gray-900/80 backdrop-blur-lg sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-r from-green-500 to-teal-500 flex items-center justify-center">
                <Target className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-green-400 to-teal-400 bg-clip-text text-transparent font-mono">
                  ARTEMIS COMMAND CENTER
                </h1>
                <p className="text-sm text-gray-400">
                  Technical Operations & Code Excellence Intelligence
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              {/* Connection Status */}
              <div className="flex items-center space-x-2 px-3 py-2 bg-gray-800 rounded-lg">
                <Radio className={`w-4 h-4 ${connected ? 'text-green-400 animate-pulse' : 'text-red-400'}`} />
                <span className="text-sm font-mono">
                  {connected ? 'CONNECTED' : 'OFFLINE'}
                </span>
              </div>

              {/* System Status */}
              <Badge variant={connected ? 'default' : 'destructive'} className="font-mono">
                OPERATIONAL
              </Badge>

              <Button variant="outline" size="sm" className="font-mono">
                <Settings className="w-4 h-4 mr-2" />
                CONFIG
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid grid-cols-6 w-full bg-gray-900 border-gray-700">
            <TabsTrigger value="overview" className="font-mono">
              <Eye className="w-4 h-4 mr-2" />
              OVERVIEW
            </TabsTrigger>
            <TabsTrigger value="mcp" className="font-mono">
              <Terminal className="w-4 h-4 mr-2" />
              MCP OPS
            </TabsTrigger>
            <TabsTrigger value="systems" className="font-mono">
              <Server className="w-4 h-4 mr-2" />
              SYSTEMS
            </TabsTrigger>
            <TabsTrigger value="codebase" className="font-mono">
              <Code className="w-4 h-4 mr-2" />
              CODEBASE
            </TabsTrigger>
            <TabsTrigger value="deployments" className="font-mono">
              <GitBranch className="w-4 h-4 mr-2" />
              DEPLOYMENTS
            </TabsTrigger>
            <TabsTrigger value="monitoring" className="font-mono">
              <Activity className="w-4 h-4 mr-2" />
              MONITORING
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            {/* System Health Grid */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {systemMetrics.slice(0, 6).map((metric) => (
                <Card key={metric.name} className="bg-gray-900 border-gray-700">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-mono text-gray-300 flex items-center justify-between">
                      {metric.name}
                      {getStatusIcon(metric.status)}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between">
                      <div className={`text-lg font-bold font-mono ${getStatusColor(metric.status)}`}>
                        {metric.value}
                      </div>
                      <div className="text-sm text-gray-400">
                        {getTrendIcon(metric.trend)}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Critical Alerts & Action Items */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card className="bg-gray-900 border-gray-700">
                <CardHeader>
                  <CardTitle className="font-mono text-green-400 flex items-center">
                    <Shield className="w-5 h-5 mr-2" />
                    SYSTEM STATUS
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-2 bg-green-950 border border-green-800 rounded">
                      <span className="text-sm font-mono">All Systems Operational</span>
                      <CheckCircle className="w-4 h-4 text-green-400" />
                    </div>
                    <div className="flex items-center justify-between p-2 bg-blue-950 border border-blue-800 rounded">
                      <span className="text-sm font-mono">Auto-scaling Active</span>
                      <Activity className="w-4 h-4 text-blue-400 animate-pulse" />
                    </div>
                    <div className="flex items-center justify-between p-2 bg-yellow-950 border border-yellow-800 rounded">
                      <span className="text-sm font-mono">Network Latency: +15ms</span>
                      <AlertTriangle className="w-4 h-4 text-yellow-400" />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-gray-900 border-gray-700">
                <CardHeader>
                  <CardTitle className="font-mono text-blue-400 flex items-center">
                    <Terminal className="w-5 h-5 mr-2" />
                    RECENT OPERATIONS
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-32">
                    <div className="space-y-2 text-xs font-mono">
                      <div className="flex items-center space-x-2">
                        <span className="text-gray-500">[14:23]</span>
                        <CheckCircle className="w-3 h-3 text-green-400" />
                        <span>Deployment v2.5.0-rc.1 completed</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-gray-500">[14:18]</span>
                        <Activity className="w-3 h-3 text-blue-400" />
                        <span>Database optimization running</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-gray-500">[14:15]</span>
                        <CheckCircle className="w-3 h-3 text-green-400" />
                        <span>Security scan passed</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-gray-500">[14:12]</span>
                        <CheckCircle className="w-3 h-3 text-green-400" />
                        <span>Backup verification complete</span>
                      </div>
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* MCP Operations Tab */}
          <TabsContent value="mcp" className="space-y-6">
            {/* Odin Technical Excellence Widget */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-1">
                <MythologyAgentWidget
                  agent={{
                    id: 'odin',
                    name: 'Odin',
                    title: 'Technical Wisdom & Code Excellence',
                    domain: 'artemis',
                    assigned_mcp_servers: ['artemis_code_analysis', 'artemis_design', 'artemis_codebase_memory'],
                    context: 'Code quality governance, architectural decisions, and technical debt management',
                    widget_type: 'technical_excellence_oracle',
                    icon_type: 'odin'
                  }}
                  metrics={{
                    primary_metric: {
                      label: 'Technical Excellence Score',
                      value: '94%',
                      trend: 'up'
                    },
                    secondary_metrics: [
                      { label: 'Code Quality', value: '94%', status: 'good' },
                      { label: 'Security Score', value: '98%', status: 'good' },
                      { label: 'Tech Debt', value: '15', status: 'warning' },
                      { label: 'Test Coverage', value: '87%', status: 'good' },
                      { label: 'Performance', value: '92%', status: 'good' },
                      { label: 'Documentation', value: '89%', status: 'good' }
                    ],
                    server_status: [
                      { server_name: 'artemis_code_analysis', status: 'operational', last_activity: '30 sec ago' },
                      { server_name: 'artemis_design', status: 'operational', last_activity: '2 min ago' },
                      { server_name: 'artemis_codebase_memory', status: 'operational', last_activity: '1 min ago' }
                    ]
                  }}
                />
              </div>

              {/* MCP Server Grid */}
              <div className="lg:col-span-2">
                <MCPServerGrid
                  domain="artemis"
                  servers={[
                    {
                      server_name: 'artemis_filesystem',
                      server_type: 'filesystem',
                      status: 'operational',
                      domain: 'artemis',
                      access_level: 'exclusive',
                      connections: { active: 6, max: 10, utilization: 0.6 },
                      capabilities: ['file_read', 'file_write', 'file_delete', 'file_watch', 'repository_management'],
                      last_activity: '1 minute ago',
                      performance_metrics: {
                        response_time_ms: 45,
                        throughput_ops_per_sec: 200,
                        error_rate: 0.001,
                        uptime_percentage: 99.9
                      }
                    },
                    {
                      server_name: 'artemis_code_analysis',
                      server_type: 'code_analysis',
                      status: 'operational',
                      domain: 'artemis',
                      access_level: 'exclusive',
                      connections: { active: 4, max: 8, utilization: 0.5 },
                      capabilities: ['syntax_analysis', 'security_scanning', 'performance_profiling', 'complexity_calculation'],
                      last_activity: '30 seconds ago',
                      performance_metrics: {
                        response_time_ms: 280,
                        throughput_ops_per_sec: 35,
                        error_rate: 0.002,
                        uptime_percentage: 99.8
                      }
                    },
                    {
                      server_name: 'artemis_design',
                      server_type: 'design_server',
                      status: 'operational',
                      domain: 'artemis',
                      access_level: 'exclusive',
                      connections: { active: 2, max: 5, utilization: 0.4 },
                      capabilities: ['uml_generation', 'architecture_diagrams', 'design_pattern_detection'],
                      last_activity: '2 minutes ago',
                      performance_metrics: {
                        response_time_ms: 450,
                        throughput_ops_per_sec: 15,
                        error_rate: 0.001,
                        uptime_percentage: 99.5
                      }
                    },
                    {
                      server_name: 'shared_database',
                      server_type: 'database',
                      status: 'operational',
                      domain: 'shared',
                      access_level: 'shared',
                      connections: { active: 15, max: 25, utilization: 0.6 },
                      capabilities: ['query', 'insert', 'update', 'delete', 'transaction'],
                      last_activity: '30 seconds ago',
                      performance_metrics: {
                        response_time_ms: 12,
                        throughput_ops_per_sec: 450,
                        error_rate: 0.001,
                        uptime_percentage: 99.95
                      }
                    }
                  ]}
                  mythology_agents={[
                    {
                      name: 'Odin - Technical Wisdom',
                      assigned_mcp_servers: ['artemis_code_analysis', 'artemis_design', 'artemis_codebase_memory'],
                      context: 'Code quality governance and architectural decisions',
                      widget_type: 'technical_excellence_oracle'
                    }
                  ]}
                />
              </div>
            </div>
          </TabsContent>

          {/* Systems Tab */}
          <TabsContent value="systems" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <Card className="bg-gray-900 border-gray-700">
                <CardHeader>
                  <CardTitle className="font-mono text-purple-400 flex items-center">
                    <Cpu className="w-5 h-5 mr-2" />
                    COMPUTE
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span>CPU Usage</span>
                    <span className="text-green-400 font-mono">23%</span>
                  </div>
                  <Progress value={23} className="h-2" />
                  <div className="text-xs text-gray-400 font-mono">
                    8 cores @ 3.2GHz | Load avg: 1.2
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-gray-900 border-gray-700">
                <CardHeader>
                  <CardTitle className="font-mono text-orange-400 flex items-center">
                    <HardDrive className="w-5 h-5 mr-2" />
                    STORAGE
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span>Disk Usage</span>
                    <span className="text-green-400 font-mono">67%</span>
                  </div>
                  <Progress value={67} className="h-2" />
                  <div className="text-xs text-gray-400 font-mono">
                    670GB / 1TB | RAID 1 | SSD
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-gray-900 border-gray-700">
                <CardHeader>
                  <CardTitle className="font-mono text-cyan-400 flex items-center">
                    <Network className="w-5 h-5 mr-2" />
                    NETWORK
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span>Bandwidth</span>
                    <span className="text-yellow-400 font-mono">78%</span>
                  </div>
                  <Progress value={78} className="h-2" />
                  <div className="text-xs text-gray-400 font-mono">
                    156 Mbps / 200 Mbps | Latency: 12ms
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-gray-900 border-gray-700">
                <CardHeader>
                  <CardTitle className="font-mono text-blue-400 flex items-center">
                    <Database className="w-5 h-5 mr-2" />
                    DATABASE
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span>Connections</span>
                    <span className="text-green-400 font-mono">34/100</span>
                  </div>
                  <Progress value={34} className="h-2" />
                  <div className="text-xs text-gray-400 font-mono">
                    PostgreSQL 15 | Query avg: 2.1ms
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Codebase Tab */}
          <TabsContent value="codebase" className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <Card className="bg-gray-900 border-gray-700">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-mono text-gray-300">TOTAL FILES</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold font-mono text-white">
                    {codebaseHealth.totalFiles.toLocaleString()}
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-gray-900 border-gray-700">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-mono text-gray-300">ISSUES FOUND</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold font-mono text-yellow-400">
                    {codebaseHealth.issuesFound}
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-gray-900 border-gray-700">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-mono text-gray-300">ISSUES FIXED</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold font-mono text-green-400">
                    {codebaseHealth.issuesFixed}
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-gray-900 border-gray-700">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-mono text-gray-300">TECHNICAL DEBT</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold font-mono text-orange-400">
                    {codebaseHealth.technicalDebt}
                  </div>
                  <div className="text-xs text-gray-400">high priority items</div>
                </CardContent>
              </Card>

              <Card className="bg-gray-900 border-gray-700">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-mono text-gray-300">CODE QUALITY</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold font-mono text-green-400">
                    {codebaseHealth.codeQualityScore}%
                  </div>
                  <Progress value={codebaseHealth.codeQualityScore} className="h-1 mt-2" />
                </CardContent>
              </Card>

              <Card className="bg-gray-900 border-gray-700">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-mono text-gray-300">TEST COVERAGE</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold font-mono text-blue-400">
                    {codebaseHealth.testCoverage}%
                  </div>
                  <Progress value={codebaseHealth.testCoverage} className="h-1 mt-2" />
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Deployments Tab */}
          <TabsContent value="deployments" className="space-y-6">
            <div className="space-y-4">
              {deployments.map((deployment) => (
                <Card key={deployment.environment} className="bg-gray-900 border-gray-700">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="font-mono text-lg">
                        {deployment.environment.toUpperCase()}
                      </CardTitle>
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(deployment.status)}
                        <Badge
                          className={`font-mono ${
                            deployment.status === 'deployed' ? 'bg-green-900 text-green-300' :
                            deployment.status === 'deploying' ? 'bg-blue-900 text-blue-300' :
                            deployment.status === 'failed' ? 'bg-red-900 text-red-300' :
                            'bg-yellow-900 text-yellow-300'
                          }`}
                        >
                          {deployment.status.toUpperCase()}
                        </Badge>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500 block">Version</span>
                        <span className="font-mono text-white">{deployment.version}</span>
                      </div>
                      <div>
                        <span className="text-gray-500 block">Last Deployment</span>
                        <span className="font-mono text-white">{deployment.lastDeployment}</span>
                      </div>
                      <div>
                        <span className="text-gray-500 block">Uptime</span>
                        <span className="font-mono text-green-400">{deployment.uptime}</span>
                      </div>
                      <div>
                        <span className="text-gray-500 block">Actions</span>
                        <Button size="sm" variant="outline" className="font-mono text-xs">
                          ROLLBACK
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* Monitoring Tab */}
          <TabsContent value="monitoring" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card className="bg-gray-900 border-gray-700">
                <CardHeader>
                  <CardTitle className="font-mono text-green-400 flex items-center">
                    <Activity className="w-5 h-5 mr-2" />
                    REAL-TIME METRICS
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-64">
                    <div className="space-y-2">
                      {systemMetrics.map((metric) => (
                        <div key={metric.name} className="flex items-center justify-between p-2 border border-gray-800 rounded">
                          <span className="text-sm font-mono">{metric.name}</span>
                          <div className="flex items-center space-x-2">
                            <span className={`font-mono ${getStatusColor(metric.status)}`}>
                              {metric.value}
                            </span>
                            {getStatusIcon(metric.status)}
                          </div>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>

              <Card className="bg-gray-900 border-gray-700">
                <CardHeader>
                  <CardTitle className="font-mono text-blue-400 flex items-center">
                    <Clock className="w-5 h-5 mr-2" />
                    SYSTEM LOGS
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-64">
                    <div className="space-y-1 text-xs font-mono">
                      <div className="text-green-400">[INFO] System health check passed</div>
                      <div className="text-blue-400">[DEBUG] Background job queue: 23 pending</div>
                      <div className="text-yellow-400">[WARN] Memory usage above 75% threshold</div>
                      <div className="text-green-400">[INFO] Database connection pool optimized</div>
                      <div className="text-blue-400">[DEBUG] Cache hit ratio: 94.2%</div>
                      <div className="text-green-400">[INFO] Security scan completed successfully</div>
                      <div className="text-gray-400">[TRACE] Request processing time: avg 124ms</div>
                      <div className="text-blue-400">[DEBUG] Active sessions: 1,247</div>
                      <div className="text-green-400">[INFO] Backup verification successful</div>
                      <div className="text-yellow-400">[WARN] Network latency spike detected: +15ms</div>
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>

      {/* Footer Status Bar */}
      <div className="border-t border-gray-800 bg-gray-900 mt-8">
        <div className="container mx-auto px-4 py-3">
          <div className="flex justify-between items-center text-xs font-mono text-gray-400">
            <div className="flex space-x-6">
              <span>SECURE CONNECTION</span>
              <span>ENCRYPTION: AES-256</span>
              <span>CLEARANCE: DEVELOPER</span>
            </div>
            <div className="flex space-x-6">
              <span>UPTIME: 99.98%</span>
              <span>LATENCY: 12ms</span>
              <span>{new Date().toLocaleString()}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ArtemisCommandCenter;
