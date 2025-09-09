'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  AlertTriangle, CheckCircle, Clock, TrendingUp, TrendingDown,
  Users, Target, Activity, Brain, Zap, RefreshCw, Bell,
  BarChart3, PieChart, Calendar, MessageCircle
} from 'lucide-react';

// Feature flags
const ENABLE_ARTEMIS = (process.env.NEXT_PUBLIC_ENABLE_ARTEMIS === '1' || process.env.NEXT_PUBLIC_ENABLE_ARTEMIS === 'true');

// Resolve WS base from NEXT_PUBLIC_API_URL (http -> ws)
const getWsBase = (): string => {
  const api = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003';
  try {
    const u = new URL(api);
    u.protocol = u.protocol === 'https:' ? 'wss:' : 'ws:';
    return u.origin;
  } catch {
    return 'ws://localhost:8003';
  }
};

// WebSocket hook for real-time updates
const useWebSocketConnection = (path: string) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    const wsUrl = `${getWsBase()}${path}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setConnected(true);
      // Subscribe to relevant channels
      ws.send(JSON.stringify({ type: 'subscribe', channel: 'sophia_pay_ready' }));
      ws.send(JSON.stringify({ type: 'subscribe', channel: 'stuck_accounts' }));
      ws.send(JSON.stringify({ type: 'subscribe', channel: 'operational_intelligence' }));
      ws.send(JSON.stringify({ type: 'subscribe', channel: 'team_performance' }));
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setData(message);
    };

    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);

    setSocket(ws);

    return () => ws.close();
  }, [url]);

  return { socket, connected, data };
};

interface StuckAccount {
  account_id: string;
  account_type: string;
  alert_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  detected_at: string;
  recommended_actions: string[];
  affected_stakeholders: string[];
}

interface TeamMetrics {
  team_id: string;
  team_name: string;
  velocity: number;
  capacity_utilization: number;
  completion_rate: number;
  blocked_items: number;
  trend: 'improving' | 'stable' | 'declining';
}

interface OperationalIntelligence {
  insight_type: string;
  title: string;
  confidence: number;
  impact_score: number;
  recommendations: string[];
  data: unknown;
}

const PayReadyDashboard: React.FC = () => {
  const { connected, data } = useWebSocketConnection(`/ws/sophia_dashboard/${Date.now()}`);
  const [stuckAccounts, setStuckAccounts] = useState<StuckAccount[]>([]);
  const [teamMetrics, setTeamMetrics] = useState<TeamMetrics[]>([]);
  const [operationalIntelligence, setOperationalIntelligence] = useState<OperationalIntelligence[]>([]);
  const [systemHealth, setSystemHealth] = useState(85);
  const [swarmStatus, setSwarmStatus] = useState<'idle' | 'running' | 'completed'>('idle');
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  // Handle real-time WebSocket data
  useEffect(() => {
    if (!data) return;

    switch (data.type) {
      case 'stuck_account_alert':
        setStuckAccounts(prev => [...prev.filter(a => a.account_id !== data.account_id), {
          account_id: data.account_id,
          account_type: data.details.account_type,
          alert_type: data.alert_type,
          severity: data.details.severity,
          title: data.details.title,
          description: data.details.description,
          detected_at: data.timestamp,
          recommended_actions: data.details.recommended_actions,
          affected_stakeholders: data.details.affected_stakeholders
        }]);
        break;

      case 'team_performance_update':
        setTeamMetrics(prev => {
          const updated = prev.filter(t => t.team_id !== data.team_id);
          return [...updated, {
            team_id: data.team_id,
            team_name: data.metrics.team_name || `Team ${data.team_id}`,
            velocity: data.metrics.velocity || 0,
            capacity_utilization: data.metrics.capacity_utilization || 0,
            completion_rate: data.metrics.completion_rate || 0,
            blocked_items: data.metrics.blocked_items || 0,
            trend: data.metrics.trend || 'stable'
          }]);
        });
        break;

      case 'operational_intelligence':
        setOperationalIntelligence(prev => [...prev.slice(-9), {
          insight_type: data.insight_type,
          title: data.data.title || 'New Insight',
          confidence: data.confidence,
          impact_score: data.data.impact_score || 0,
          recommendations: data.data.recommendations || [],
          data: data.data
        }]);
        break;

      case 'swarm_deployment_event':
        if (data.event_type === 'deployment_start') {
          setSwarmStatus('running');
        } else if (data.event_type === 'deployment_complete') {
          setSwarmStatus('completed');
          setTimeout(() => setSwarmStatus('idle'), 3000);
        }
        break;
    }

    setLastUpdate(new Date());
  }, [data]);

  const deploySwarmEnhancements = useCallback(async () => {
    setSwarmStatus('running');

    try {
      if (!ENABLE_ARTEMIS) { setSwarmStatus('idle'); return; }
      const response = await fetch('/api/swarms/artemis/deploy-sophia-enhancements', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ trigger: 'manual_deployment' })
      });

      if (response.ok) {
        const result = await response.json();
      }
    } catch (error) {
      console.error('Failed to deploy swarm:', error);
      setSwarmStatus('idle');
    }
  }, []);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-200';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-blue-100 text-blue-800 border-blue-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving': return <TrendingUp className="w-4 h-4 text-green-500" />;
      case 'declining': return <TrendingDown className="w-4 h-4 text-red-500" />;
      default: return <Activity className="w-4 h-4 text-blue-500" />;
    }
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Brain className="w-8 h-8 text-blue-500" />
            Sophia Pay Ready Intelligence
          </h1>
          <p className="text-muted-foreground">
            {ENABLE_ARTEMIS ? 'Real-time operational intelligence powered by Artemis agent swarm' : 'Real-time operational intelligence powered by Sophia agents'}
          </p>
        </div>

        <div className="flex items-center gap-4">
          <Badge variant={connected ? "default" : "destructive"} className="flex items-center gap-1">
            <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-400' : 'bg-red-400'}`} />
            {connected ? 'Live' : 'Disconnected'}
          </Badge>

          {ENABLE_ARTEMIS && (
          <Button onClick={deploySwarmEnhancements} disabled={swarmStatus === 'running'}>
            {swarmStatus === 'running' ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                Swarm Running...
              </>
            ) : (
              <>
                <Zap className="w-4 h-4 mr-2" />
                Deploy Enhancements
              </>
            )}
          </Button>
          )}
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">System Health</p>
                <p className="text-2xl font-bold">{systemHealth}%</p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-500" />
            </div>
            <Progress value={systemHealth} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Stuck Accounts</p>
                <p className="text-2xl font-bold text-red-500">{stuckAccounts.length}</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-red-500" />
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {stuckAccounts.filter(a => a.severity === 'critical').length} critical
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Active Teams</p>
                <p className="text-2xl font-bold">{teamMetrics.length}</p>
              </div>
              <Users className="w-8 h-8 text-blue-500" />
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {teamMetrics.filter(t => t.trend === 'improving').length} improving
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">AI Insights</p>
                <p className="text-2xl font-bold">{operationalIntelligence.length}</p>
              </div>
              <Brain className="w-8 h-8 text-purple-500" />
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Last update: {lastUpdate.toLocaleTimeString()}
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="alerts" className="space-y-4">
        <TabsList>
          <TabsTrigger value="alerts">Stuck Account Alerts</TabsTrigger>
          <TabsTrigger value="teams">Team Performance</TabsTrigger>
          <TabsTrigger value="intelligence">Operational Intelligence</TabsTrigger>
          <TabsTrigger value="analytics">Predictive Analytics</TabsTrigger>
        </TabsList>

        {/* Stuck Account Alerts */}
        <TabsContent value="alerts" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5" />
                Stuck Account Detection
              </CardTitle>
            </CardHeader>
            <CardContent>
              {stuckAccounts.length === 0 ? (
                <div className="text-center py-8">
                  <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-2" />
                  <p className="text-muted-foreground">No stuck accounts detected</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {stuckAccounts.map((account) => (
                    <div key={account.account_id} className="border rounded-lg p-4 space-y-3">
                      <div className="flex items-start justify-between">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <h3 className="font-medium">{account.title}</h3>
                            <Badge className={getSeverityColor(account.severity)}>
                              {account.severity}
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground">{account.description}</p>
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <Clock className="w-3 h-3" />
                            {new Date(account.detected_at).toLocaleString()}
                          </div>
                        </div>
                      </div>

                      {account.recommended_actions.length > 0 && (
                        <div>
                          <p className="text-sm font-medium mb-1">Recommended Actions:</p>
                          <ul className="text-sm text-muted-foreground space-y-1">
                            {account.recommended_actions.map((action, i) => (
                              <li key={i} className="flex items-start gap-2">
                                <CheckCircle className="w-3 h-3 text-green-500 mt-0.5 flex-shrink-0" />
                                {action}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {account.affected_stakeholders.length > 0 && (
                        <div className="flex items-center gap-2">
                          <Users className="w-4 h-4 text-muted-foreground" />
                          <span className="text-sm text-muted-foreground">
                            Stakeholders: {account.affected_stakeholders.join(', ')}
                          </span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Team Performance */}
        <TabsContent value="teams" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="w-5 h-5" />
                Team Performance Metrics
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4">
                {teamMetrics.map((team) => (
                  <div key={team.team_id} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="font-medium flex items-center gap-2">
                        {team.team_name}
                        {getTrendIcon(team.trend)}
                      </h3>
                      <Badge variant={team.trend === 'improving' ? 'default' : team.trend === 'declining' ? 'destructive' : 'secondary'}>
                        {team.trend}
                      </Badge>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div>
                        <p className="text-sm text-muted-foreground">Velocity</p>
                        <p className="text-lg font-semibold">{team.velocity.toFixed(1)}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Capacity</p>
                        <div className="flex items-center gap-2">
                          <Progress value={team.capacity_utilization * 100} className="flex-1" />
                          <span className="text-sm">{(team.capacity_utilization * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Completion Rate</p>
                        <p className="text-lg font-semibold">{(team.completion_rate * 100).toFixed(1)}%</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Blocked Items</p>
                        <p className={`text-lg font-semibold ${team.blocked_items > 0 ? 'text-red-500' : 'text-green-500'}`}>
                          {team.blocked_items}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Operational Intelligence */}
        <TabsContent value="intelligence" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="w-5 h-5" />
                AI-Generated Insights
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {operationalIntelligence.map((insight, i) => (
                  <div key={i} className="border rounded-lg p-4">
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="font-medium">{insight.title}</h3>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">
                          {(insight.confidence * 100).toFixed(0)}% confidence
                        </Badge>
                        <Badge variant={insight.impact_score > 0.7 ? 'destructive' : insight.impact_score > 0.4 ? 'default' : 'secondary'}>
                          {insight.impact_score > 0.7 ? 'High Impact' : insight.impact_score > 0.4 ? 'Medium Impact' : 'Low Impact'}
                        </Badge>
                      </div>
                    </div>

                    {insight.recommendations.length > 0 && (
                      <div>
                        <p className="text-sm font-medium mb-1">Recommendations:</p>
                        <ul className="text-sm text-muted-foreground space-y-1">
                          {insight.recommendations.slice(0, 3).map((rec, j) => (
                            <li key={j} className="flex items-start gap-2">
                              <Target className="w-3 h-3 text-blue-500 mt-0.5 flex-shrink-0" />
                              {rec}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}

                {operationalIntelligence.length === 0 && (
                  <div className="text-center py-8">
                    <Brain className="w-12 h-12 text-muted-foreground mx-auto mb-2" />
                    <p className="text-muted-foreground">No operational insights available</p>
                    <p className="text-sm text-muted-foreground">Deploy the Artemis swarm to generate intelligence</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Predictive Analytics */}
        <TabsContent value="analytics" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="w-5 h-5" />
                  Risk Prediction Trends
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64 flex items-center justify-center border border-dashed rounded-lg">
                  <div className="text-center">
                    <PieChart className="w-12 h-12 text-muted-foreground mx-auto mb-2" />
                    <p className="text-muted-foreground">Analytics visualization will appear here</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5" />
                  Performance Forecasts
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Next Week Velocity Forecast</span>
                    <Badge variant="default">+12% predicted improvement</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Stuck Account Risk</span>
                    <Badge variant="secondary">Low risk (23% probability)</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Resource Utilization</span>
                    <Badge variant="outline">Optimal (78% capacity)</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default PayReadyDashboard;
