'use client';

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
  Activity, TrendingUp, TrendingDown, Users, DollarSign, Heart,
  AlertTriangle, CheckCircle, XCircle, Clock, Star, Search,
  RefreshCw, MessageCircle, Phone, Mail, Calendar, BarChart3,
  ArrowUp, ArrowDown, Minus, Target, Zap, Shield, Eye,
  PieChart, Filter, SortAsc, Mic, MicOff, Bell, BellRing,
  ThumbsUp, ThumbsDown, HelpCircle, Lightbulb, TrendingUp as Expand
} from 'lucide-react';

// ==================== TYPES ====================

interface Client {
  id: string;
  name: string;
  company: string;
  industry: string;
  tier: 'enterprise' | 'mid_market' | 'smb';
  mrr: number;
  contract_value: number;
  contract_start: string;
  contract_end: string;
  health_score: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  engagement_score: number;
  satisfaction_score: number;
  usage_score: number;
  financial_health: number;
  support_tickets: number;
  last_interaction: string;
  csm: string; // Customer Success Manager
  renewal_probability: number;
  expansion_potential: number;
  churn_risk_factors: string[];
  positive_indicators: string[];
  upcoming_renewal: boolean;
  days_to_renewal: number;
  expansion_opportunities: ExpansionOpportunity[];
  health_trends: {
    engagement: 'up' | 'down' | 'stable';
    satisfaction: 'up' | 'down' | 'stable';
    usage: 'up' | 'down' | 'stable';
    financial: 'up' | 'down' | 'stable';
  };
}

interface ExpansionOpportunity {
  id: string;
  type: 'upsell' | 'cross_sell' | 'add_on';
  product: string;
  potential_value: number;
  probability: number;
  timeline: string;
  trigger_event: string;
  recommended_action: string;
}

interface RecoveryPlan {
  client_id: string;
  risk_factors: string[];
  recommended_actions: RecoveryAction[];
  timeline: string;
  success_probability: number;
  estimated_cost: number;
  roi_projection: number;
}

interface RecoveryAction {
  id: string;
  type: 'call' | 'email' | 'meeting' | 'discount' | 'feature_request' | 'training';
  description: string;
  priority: number;
  estimated_effort: string;
  expected_impact: number;
  deadline: string;
  assigned_to: string;
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
}

interface HealthMetrics {
  total_clients: number;
  healthy_clients: number;
  at_risk_clients: number;
  critical_clients: number;
  total_mrr: number;
  expansion_pipeline: number;
  avg_health_score: number;
  churn_rate: number;
  nps_score: number;
  renewals_this_quarter: number;
  expansion_closed: number;
}

// ==================== ASCLEPIUS CLIENT HEALTH DASHBOARD ====================

const ClientHealthDashboard: React.FC = () => {
  // Core State
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);

  // Data State
  const [clients, setClients] = useState<Client[]>([]);
  const [recoveryPlans, setRecoveryPlans] = useState<RecoveryPlan[]>([]);
  const [healthMetrics, setHealthMetrics] = useState<HealthMetrics | null>(null);

  // Filter & Search State
  const [searchQuery, setSearchQuery] = useState('');
  const [filterRisk, setFilterRisk] = useState<string>('all');
  const [filterTier, setFilterTier] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('health_score');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // UI State
  const [activeTab, setActiveTab] = useState('overview');
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const ws = useRef<WebSocket | null>(null);
  const refreshInterval = useRef<NodeJS.Timeout | null>(null);

  // ==================== WEBSOCKET & DATA LOADING ====================

  useEffect(() => {
    connectWebSocket();
    loadInitialData();
    if (autoRefresh) {
      refreshInterval.current = setInterval(loadInitialData, 30000); // Refresh every 30s
    }

    return () => {
      if (ws.current) ws.current.close();
      if (refreshInterval.current) clearInterval(refreshInterval.current);
    };
  }, [autoRefresh]);

  const connectWebSocket = () => {
    try {
      ws.current = new WebSocket('/ws/client-health-asclepius');

      ws.current.onopen = () => {
        setConnected(true);
        sendCommand({ type: 'subscribe', channel: 'client_health' });
      };

      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleRealtimeUpdate(data);
      };

      ws.current.onclose = () => {
        setConnected(false);
        setTimeout(connectWebSocket, 3000);
      };
    } catch (error) {
      console.error('WebSocket connection failed:', error);
      setConnected(false);
    }
  };

  const loadInitialData = async () => {
    setLoading(true);
    try {
      const [clientsResponse, plansResponse, metricsResponse] = await Promise.all([
        fetch('/api/clients/health'),
        fetch('/api/clients/recovery-plans'),
        fetch('/api/clients/metrics')
      ]);

      if (clientsResponse.ok) {
        const clientData = await clientsResponse.json();
        setClients(clientData);
      }

      if (plansResponse.ok) {
        const plansData = await plansResponse.json();
        setRecoveryPlans(plansData);
      }

      if (metricsResponse.ok) {
        const metricsData = await metricsResponse.json();
        setHealthMetrics(metricsData);
      }
    } catch (error) {
      console.error('Failed to load client health data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRealtimeUpdate = (data: unknown) => {
    switch (data.type) {
      case 'client_update':
        setClients(prev => prev.map(client =>
          client.id === data.client.id ? { ...client, ...data.client } : client
        ));
        break;
      case 'health_alert':
        if (data.client_id) {
          setClients(prev => prev.map(client =>
            client.id === data.client_id
              ? { ...client, risk_level: data.new_risk_level, health_score: data.new_score }
              : client
          ));
        }
        break;
      case 'metrics_update':
        setHealthMetrics(prev => ({ ...prev, ...data.metrics }));
        break;
      case 'expansion_opportunity':
        setClients(prev => prev.map(client =>
          client.id === data.client_id
            ? { ...client, expansion_opportunities: [...client.expansion_opportunities, data.opportunity] }
            : client
        ));
        break;
    }
  };

  const sendCommand = (command: unknown) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(command));
    }
  };

  // ==================== VOICE INTEGRATION ====================

  const handleVoiceCommand = useCallback(async (command: string) => {
    if (!voiceEnabled) return;

    try {
      const response = await fetch('/api/voice/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          command,
          context: 'client_health_dashboard',
          current_client: selectedClient?.id
        })
      });

      if (response.ok) {
        const result = await response.json();
        executeVoiceCommand(result);
      }
    } catch (error) {
      console.error('Voice command processing failed:', error);
    }
  }, [voiceEnabled, selectedClient]);

  const executeVoiceCommand = (result: unknown) => {
    switch (result.action) {
      case 'filter_clients':
        setFilterRisk(result.risk_level);
        break;
      case 'select_client':
        const client = clients.find(c => c.name.toLowerCase().includes(result.client_name.toLowerCase()));
        if (client) setSelectedClient(client);
        break;
      case 'show_at_risk':
        setFilterRisk('high');
        setActiveTab('at_risk');
        break;
      case 'show_expansion':
        setActiveTab('expansion');
        break;
    }
  };

  // ==================== DATA PROCESSING ====================

  const getFilteredClients = () => {
    return clients.filter(client => {
      const matchesSearch = client.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                           client.company.toLowerCase().includes(searchQuery.toLowerCase()) ||
                           client.industry.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesRisk = filterRisk === 'all' || client.risk_level === filterRisk;
      const matchesTier = filterTier === 'all' || client.tier === filterTier;

      return matchesSearch && matchesRisk && matchesTier;
    }).sort((a, b) => {
      const aVal = a[sortBy as keyof Client] as number;
      const bVal = b[sortBy as keyof Client] as number;

      if (sortOrder === 'asc') {
        return aVal > bVal ? 1 : -1;
      } else {
        return aVal < bVal ? 1 : -1;
      }
    });
  };

  const getHealthColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    if (score >= 40) return 'text-orange-600';
    return 'text-red-600';
  };

  const getHealthIcon = (score: number) => {
    if (score >= 80) return <CheckCircle className="w-4 h-4 text-green-500" />;
    if (score >= 60) return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
    if (score >= 40) return <AlertTriangle className="w-4 h-4 text-orange-500" />;
    return <XCircle className="w-4 h-4 text-red-500" />;
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'high': return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200';
      case 'critical': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return <ArrowUp className="w-3 h-3 text-green-500" />;
      case 'down': return <ArrowDown className="w-3 h-3 text-red-500" />;
      default: return <Minus className="w-3 h-3 text-gray-500" />;
    }
  };

  const calculateExpansionValue = (client: Client) => {
    return client.expansion_opportunities.reduce((sum, opp) =>
      sum + (opp.potential_value * opp.probability / 100), 0
    );
  };

  // ==================== ACTIONS ====================

  const generateRecoveryPlan = async (clientId: string) => {
    try {
      const response = await fetch(`/api/clients/${clientId}/recovery-plan`, {
        method: 'POST'
      });

      if (response.ok) {
        const plan = await response.json();
        setRecoveryPlans(prev => [...prev, plan]);
      }
    } catch (error) {
      console.error('Failed to generate recovery plan:', error);
    }
  };

  const scheduleHealthCheck = async (clientId: string) => {
    try {
      await fetch(`/api/clients/${clientId}/health-check`, {
        method: 'POST'
      });
      // Show success notification
    } catch (error) {
      console.error('Failed to schedule health check:', error);
    }
  };

  // ==================== RENDER METHODS ====================

  const renderClientCard = (client: Client) => (
    <Card
      key={client.id}
      className={`cursor-pointer transition-all hover:shadow-lg ${
        selectedClient?.id === client.id ? 'ring-2 ring-blue-500' : ''
      }`}
      onClick={() => setSelectedClient(client)}
    >
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-r from-emerald-500 to-teal-500 flex items-center justify-center text-white font-bold">
              {client.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
            </div>
            <div>
              <CardTitle className="text-base">{client.name}</CardTitle>
              <p className="text-xs text-gray-500">{client.company} • {client.industry}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {getHealthIcon(client.health_score)}
            <Badge className={getRiskColor(client.risk_level)}>
              {client.risk_level}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {/* Health Score */}
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span>Health Score</span>
              <span className={getHealthColor(client.health_score)}>
                {client.health_score}%
              </span>
            </div>
            <Progress value={client.health_score} className="h-1" />
          </div>

          {/* Key Metrics */}
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-gray-500">MRR:</span>
              <span>${(client.mrr / 1000).toFixed(1)}k</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-500">Tier:</span>
              <Badge variant="outline" className="text-xs">
                {client.tier.replace('_', ' ')}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-500">Engagement:</span>
              <div className="flex items-center space-x-1">
                <span>{client.engagement_score}%</span>
                {getTrendIcon(client.health_trends.engagement)}
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-500">Satisfaction:</span>
              <div className="flex items-center space-x-1">
                <span>{client.satisfaction_score}%</span>
                {getTrendIcon(client.health_trends.satisfaction)}
              </div>
            </div>
          </div>

          {/* Renewal Status */}
          {client.upcoming_renewal && (
            <div className="flex items-center justify-between bg-blue-50 dark:bg-blue-950 p-2 rounded">
              <span className="text-xs text-blue-700 dark:text-blue-300">Renewal in {client.days_to_renewal} days</span>
              <span className="text-xs font-medium">{client.renewal_probability}% likely</span>
            </div>
          )}

          {/* Risk Factors */}
          {client.churn_risk_factors.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {client.churn_risk_factors.slice(0, 2).map((factor) => (
                <Badge key={factor} variant="destructive" className="text-xs">
                  {factor}
                </Badge>
              ))}
              {client.churn_risk_factors.length > 2 && (
                <Badge variant="outline" className="text-xs">
                  +{client.churn_risk_factors.length - 2}
                </Badge>
              )}
            </div>
          )}

          {/* Expansion Opportunities */}
          {client.expansion_opportunities.length > 0 && (
            <div className="flex items-center justify-between bg-green-50 dark:bg-green-950 p-2 rounded">
              <span className="text-xs text-green-700 dark:text-green-300">
                {client.expansion_opportunities.length} expansion opps
              </span>
              <span className="text-xs font-medium">
                ${(calculateExpansionValue(client) / 1000).toFixed(0)}k potential
              </span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );

  const renderExpansionOpportunity = (opportunity: ExpansionOpportunity, client: Client) => (
    <Card key={opportunity.id} className="mb-3">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-sm">{opportunity.product}</CardTitle>
            <p className="text-xs text-gray-500">{client.name} • {opportunity.type.replace('_', ' ')}</p>
          </div>
          <Badge variant={opportunity.probability > 70 ? 'default' : 'secondary'}>
            {opportunity.probability}%
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex justify-between text-xs">
            <span className="text-gray-500">Potential Value:</span>
            <span className="font-medium">${opportunity.potential_value.toLocaleString()}</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-gray-500">Timeline:</span>
            <span>{opportunity.timeline}</span>
          </div>
          <div className="text-xs">
            <p className="text-gray-500">Trigger:</p>
            <p>{opportunity.trigger_event}</p>
          </div>
          <div className="text-xs">
            <p className="text-gray-500">Recommended Action:</p>
            <p className="text-blue-600">{opportunity.recommended_action}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 to-teal-100 dark:from-gray-900 dark:to-gray-950">
      {/* Header */}
      <div className="border-b bg-white/80 dark:bg-gray-900/80 backdrop-blur-lg sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-10 h-10 rounded-full bg-gradient-to-r from-emerald-600 to-teal-600 flex items-center justify-center">
                <Heart className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent">
                  Asclepius Client Health
                </h1>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  AI-powered client health monitoring and recovery
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              {/* Voice Control */}
              <Button
                variant={voiceEnabled ? 'default' : 'outline'}
                size="sm"
                onClick={() => setVoiceEnabled(!voiceEnabled)}
              >
                {voiceEnabled ? <Mic className="w-4 h-4" /> : <MicOff className="w-4 h-4" />}
                Voice Control
              </Button>

              {/* Auto Refresh */}
              <Button
                variant={autoRefresh ? 'default' : 'outline'}
                size="sm"
                onClick={() => setAutoRefresh(!autoRefresh)}
              >
                {autoRefresh ? <BellRing className="w-4 h-4" /> : <Bell className="w-4 h-4" />}
                Auto Refresh
              </Button>

              {/* Connection Status */}
              <Badge variant={connected ? 'default' : 'destructive'}>
                {connected ? 'Connected' : 'Disconnected'}
              </Badge>

              {/* Health Summary */}
              <div className="flex space-x-4 text-sm">
                <div>
                  <span className="text-gray-500">Avg Health:</span>
                  <span className={`ml-1 font-bold ${getHealthColor(healthMetrics?.avg_health_score || 0)}`}>
                    {healthMetrics?.avg_health_score || 0}%
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">At Risk:</span>
                  <span className="ml-1 font-bold text-red-600">{healthMetrics?.at_risk_clients || 0}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid grid-cols-5 w-full">
            <TabsTrigger value="overview">
              <Activity className="w-4 h-4 mr-2" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="clients">
              <Users className="w-4 h-4 mr-2" />
              All Clients
            </TabsTrigger>
            <TabsTrigger value="at_risk">
              <AlertTriangle className="w-4 h-4 mr-2" />
              At Risk
            </TabsTrigger>
            <TabsTrigger value="expansion">
              <Expand className="w-4 h-4 mr-2" />
              Expansion
            </TabsTrigger>
            <TabsTrigger value="recovery">
              <Shield className="w-4 h-4 mr-2" />
              Recovery Plans
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            {/* Key Metrics */}
            <div className="grid grid-cols-5 gap-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center">
                    <Heart className="w-4 h-4 mr-2 text-emerald-600" />
                    Health Score
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className={`text-2xl font-bold ${getHealthColor(healthMetrics?.avg_health_score || 0)}`}>
                    {healthMetrics?.avg_health_score || 0}%
                  </div>
                  <p className="text-xs text-gray-500 mt-1">Average across all clients</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center">
                    <DollarSign className="w-4 h-4 mr-2 text-emerald-600" />
                    Total MRR
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    ${(healthMetrics?.total_mrr / 1000 || 0).toFixed(0)}k
                  </div>
                  <p className="text-xs text-gray-500 mt-1">Monthly recurring revenue</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center">
                    <AlertTriangle className="w-4 h-4 mr-2 text-red-500" />
                    At Risk
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-red-600">
                    {healthMetrics?.at_risk_clients || 0}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">Clients needing attention</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center">
                    <TrendingUp className="w-4 h-4 mr-2 text-emerald-600" />
                    Expansion
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-emerald-600">
                    ${(healthMetrics?.expansion_pipeline / 1000 || 0).toFixed(0)}k
                  </div>
                  <p className="text-xs text-gray-500 mt-1">Pipeline potential</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center">
                    <Star className="w-4 h-4 mr-2 text-emerald-600" />
                    NPS Score
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {healthMetrics?.nps_score || 0}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">Net Promoter Score</p>
                </CardContent>
              </Card>
            </div>

            {/* Health Distribution & Risk Analysis */}
            <div className="grid grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Health Score Distribution</CardTitle>
                  <CardDescription>Client health across all accounts</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {[
                      { label: 'Excellent (80-100%)', count: clients.filter(c => c.health_score >= 80).length, color: 'bg-green-500' },
                      { label: 'Good (60-79%)', count: clients.filter(c => c.health_score >= 60 && c.health_score < 80).length, color: 'bg-yellow-500' },
                      { label: 'At Risk (40-59%)', count: clients.filter(c => c.health_score >= 40 && c.health_score < 60).length, color: 'bg-orange-500' },
                      { label: 'Critical (<40%)', count: clients.filter(c => c.health_score < 40).length, color: 'bg-red-500' }
                    ].map((segment) => (
                      <div key={segment.label} className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <div className={`w-3 h-3 rounded-full ${segment.color}`}></div>
                          <span className="text-sm">{segment.label}</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className="text-sm font-medium">{segment.count}</span>
                          <div className="w-20 bg-gray-200 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full ${segment.color}`}
                              style={{ width: `${(segment.count / Math.max(clients.length, 1)) * 100}%` }}
                            ></div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Critical Alerts</CardTitle>
                  <CardDescription>Immediate attention required</CardDescription>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-[300px]">
                    <div className="space-y-3">
                      {clients
                        .filter(c => c.risk_level === 'critical' || c.health_score < 40)
                        .map((client) => (
                          <div key={client.id} className="flex items-start space-x-3 p-3 border-l-4 border-red-500 bg-red-50 dark:bg-red-950 rounded">
                            <XCircle className="w-4 h-4 text-red-500 mt-0.5" />
                            <div className="flex-1">
                              <div className="flex items-center justify-between">
                                <span className="font-medium text-sm">{client.name}</span>
                                <Badge className="text-xs bg-red-100 text-red-800">
                                  {client.health_score}%
                                </Badge>
                              </div>
                              <p className="text-xs text-gray-600 mt-1">
                                {client.churn_risk_factors.slice(0, 2).join(', ')}
                              </p>
                              <div className="flex space-x-2 mt-2">
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="text-xs h-6"
                                  onClick={() => generateRecoveryPlan(client.id)}
                                >
                                  Recovery Plan
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="text-xs h-6"
                                  onClick={() => setSelectedClient(client)}
                                >
                                  View Details
                                </Button>
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

          {/* All Clients Tab */}
          <TabsContent value="clients" className="space-y-6">
            {/* Filters */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>All Clients</CardTitle>
                  <div className="flex items-center space-x-2">
                    <Search className="w-4 h-4 text-gray-500" />
                    <Input
                      placeholder="Search clients..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-48"
                    />
                    <select
                      value={filterRisk}
                      onChange={(e) => setFilterRisk(e.target.value)}
                      className="border rounded px-2 py-1 text-sm"
                    >
                      <option value="all">All Risk Levels</option>
                      <option value="low">Low Risk</option>
                      <option value="medium">Medium Risk</option>
                      <option value="high">High Risk</option>
                      <option value="critical">Critical</option>
                    </select>
                    <select
                      value={filterTier}
                      onChange={(e) => setFilterTier(e.target.value)}
                      className="border rounded px-2 py-1 text-sm"
                    >
                      <option value="all">All Tiers</option>
                      <option value="enterprise">Enterprise</option>
                      <option value="mid_market">Mid Market</option>
                      <option value="smb">SMB</option>
                    </select>
                    <Button size="sm" onClick={loadInitialData}>
                      <RefreshCw className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
            </Card>

            {/* Clients Grid */}
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
              {getFilteredClients().map((client) => renderClientCard(client))}
            </div>
          </TabsContent>

          {/* At Risk Tab */}
          <TabsContent value="at_risk" className="space-y-6">
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
              {clients
                .filter(c => c.risk_level === 'high' || c.risk_level === 'critical')
                .map((client) => renderClientCard(client))}
            </div>
          </TabsContent>

          {/* Expansion Tab */}
          <TabsContent value="expansion" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Expansion Opportunities</CardTitle>
                <CardDescription>Upsell and cross-sell potential</CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[600px]">
                  <div className="space-y-2">
                    {clients
                      .filter(c => c.expansion_opportunities.length > 0)
                      .flatMap(client =>
                        client.expansion_opportunities.map(opp =>
                          renderExpansionOpportunity(opp, client)
                        )
                      )}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Recovery Plans Tab */}
          <TabsContent value="recovery" className="space-y-6">
            <div className="space-y-4">
              {recoveryPlans.map((plan) => {
                const client = clients.find(c => c.id === plan.client_id);
                return (
                  <Card key={plan.client_id}>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle className="text-base">{client?.name} Recovery Plan</CardTitle>
                          <CardDescription>
                            Success probability: {plan.success_probability}% •
                            ROI projection: ${plan.roi_projection.toLocaleString()}
                          </CardDescription>
                        </div>
                        <Badge variant="outline">{plan.timeline}</Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div>
                          <h5 className="font-medium mb-2">Risk Factors:</h5>
                          <div className="flex flex-wrap gap-1">
                            {plan.risk_factors.map((factor) => (
                              <Badge key={factor} variant="destructive" className="text-xs">
                                {factor}
                              </Badge>
                            ))}
                          </div>
                        </div>

                        <div>
                          <h5 className="font-medium mb-2">Recommended Actions:</h5>
                          <div className="space-y-2">
                            {plan.recommended_actions.map((action) => (
                              <div key={action.id} className="flex items-start justify-between p-2 border rounded">
                                <div className="flex-1">
                                  <div className="flex items-center space-x-2">
                                    <Badge variant="outline" className="text-xs">
                                      {action.type}
                                    </Badge>
                                    <span className="text-sm font-medium">{action.description}</span>
                                  </div>
                                  <div className="text-xs text-gray-500 mt-1">
                                    Effort: {action.estimated_effort} • Impact: {action.expected_impact}% •
                                    Assigned: {action.assigned_to}
                                  </div>
                                </div>
                                <Badge
                                  variant={action.status === 'completed' ? 'default' : 'secondary'}
                                  className="text-xs"
                                >
                                  {action.status}
                                </Badge>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </TabsContent>
        </Tabs>
      </div>

      {/* Selected Client Detail Panel */}
      {selectedClient && (
        <div className="fixed right-4 top-24 w-96 bg-white dark:bg-gray-900 rounded-lg shadow-2xl border p-4 z-40 max-h-[80vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold">Client Details</h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSelectedClient(null)}
            >
              <XCircle className="w-4 h-4" />
            </Button>
          </div>

          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 rounded-full bg-gradient-to-r from-emerald-500 to-teal-500 flex items-center justify-center text-white font-bold">
                {selectedClient.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
              </div>
              <div>
                <h4 className="font-medium">{selectedClient.name}</h4>
                <p className="text-sm text-gray-500">{selectedClient.company}</p>
                <p className="text-xs text-gray-500">{selectedClient.industry} • {selectedClient.tier.replace('_', ' ')}</p>
              </div>
            </div>

            <Separator />

            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Health Score:</span>
                <span className={getHealthColor(selectedClient.health_score)}>
                  {selectedClient.health_score}%
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span>MRR:</span>
                <span>${selectedClient.mrr.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Contract Value:</span>
                <span>${selectedClient.contract_value.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Renewal Probability:</span>
                <span>{selectedClient.renewal_probability}%</span>
              </div>
            </div>

            <Separator />

            <div>
              <h5 className="font-medium mb-2">Risk Factors</h5>
              <div className="flex flex-wrap gap-1">
                {selectedClient.churn_risk_factors.map((factor) => (
                  <Badge key={factor} variant="destructive" className="text-xs">
                    {factor}
                  </Badge>
                ))}
              </div>
            </div>

            <div>
              <h5 className="font-medium mb-2">Positive Indicators</h5>
              <div className="flex flex-wrap gap-1">
                {selectedClient.positive_indicators.map((indicator) => (
                  <Badge key={indicator} className="text-xs bg-green-100 text-green-800">
                    {indicator}
                  </Badge>
                ))}
              </div>
            </div>

            <Separator />

            <div className="space-y-2">
              <Button className="w-full" size="sm" onClick={() => scheduleHealthCheck(selectedClient.id)}>
                <Calendar className="w-4 h-4 mr-2" />
                Schedule Health Check
              </Button>
              <Button className="w-full" size="sm" variant="outline" onClick={() => generateRecoveryPlan(selectedClient.id)}>
                <Shield className="w-4 h-4 mr-2" />
                Generate Recovery Plan
              </Button>
              <Button className="w-full" size="sm" variant="outline">
                <MessageCircle className="w-4 h-4 mr-2" />
                Contact CSM
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ClientHealthDashboard;