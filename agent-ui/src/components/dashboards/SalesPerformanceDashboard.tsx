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
  Activity, TrendingUp, TrendingDown, Users, DollarSign,
  Phone, Calendar, Target, Award, AlertTriangle, CheckCircle,
  XCircle, Mic, MicOff, Play, Pause, Search, Filter,
  BarChart3, PieChart, Zap, MessageCircle, Clock, Star,
  ArrowUp, ArrowDown, Minus, RefreshCw, Eye, Volume2
} from 'lucide-react';

// ==================== TYPES ====================

interface SalesRep {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  territory: string;
  quota: number;
  achieved: number;
  calls_made: number;
  meetings_scheduled: number;
  deals_closed: number;
  pipeline_value: number;
  performance_score: number;
  status: 'active' | 'inactive' | 'on_call' | 'meeting';
  last_activity: string;
  trends: {
    calls: 'up' | 'down' | 'stable';
    meetings: 'up' | 'down' | 'stable';
    deals: 'up' | 'down' | 'stable';
    pipeline: 'up' | 'down' | 'stable';
  };
  coaching_alerts: CoachingAlert[];
}

interface CoachingAlert {
  id: string;
  type: 'red' | 'yellow' | 'green';
  category: 'performance' | 'behavior' | 'opportunity';
  message: string;
  action_needed: string;
  priority: number;
}

interface GongCall {
  id: string;
  rep_id: string;
  rep_name: string;
  prospect_name: string;
  company: string;
  duration: number; // seconds
  sentiment_score: number; // -1 to 1
  talk_ratio: number; // 0 to 1 (rep talk time)
  keywords_mentioned: string[];
  next_steps: string[];
  deal_stage: string;
  recording_url: string;
  transcript_summary: string;
  coaching_notes: string[];
  date: string;
  outcome: 'positive' | 'negative' | 'neutral';
  red_flags: string[];
  green_flags: string[];
}

interface PipelineVelocity {
  stage: string;
  average_days: number;
  conversion_rate: number;
  current_deals: number;
  value: number;
  trend: 'up' | 'down' | 'stable';
}

interface TeamMetrics {
  total_quota: number;
  total_achieved: number;
  team_performance_score: number;
  total_calls_this_week: number;
  total_meetings_this_week: number;
  active_deals: number;
  total_pipeline_value: number;
  average_deal_size: number;
  velocity_metrics: PipelineVelocity[];
}

// ==================== HERMES SALES DASHBOARD ====================

const SalesPerformanceDashboard: React.FC = () => {
  // Core State;
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedRep, setSelectedRep] = useState<SalesRep | null>(null);
  const [selectedCall, setSelectedCall] = useState<GongCall | null>(null);

  // Data State;
  const [salesReps, setSalesReps] = useState<SalesRep[]>([]);
  const [gongCalls, setGongCalls] = useState<GongCall[]>([]);
  const [teamMetrics, setTeamMetrics] = useState<TeamMetrics | null>(null);

  // Filter & Search State;
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterPerformance, setFilterPerformance] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('performance_score');

  // UI State;
  const [activeTab, setActiveTab] = useState('overview');
  const [playingCall, setPlayingCall] = useState<string | null>(null);
  const [voiceEnabled, setVoiceEnabled] = useState(false);

  const ws = useRef<WebSocket | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // ==================== WEBSOCKET & DATA LOADING ====================

  useEffect(() => {
    connectWebSocket();
    loadInitialData();
    return () => {
      if (ws.current) ws.current.close();
      if (audioRef.current) audioRef.current.pause();
    };
  }, []);

  const connectWebSocket = () => {
    // Connect to real-time sales data updates
    try {
      ws.current = new WebSocket('/ws/sales-hermes');

      ws.current.onopen = () => {
        setConnected(true);
        sendCommand({ type: 'subscribe', channel: 'sales_performance' });
      };

      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleRealtimeUpdate(data);
      };

      ws.current.onclose = () => {
        setConnected(false);
        // Auto-reconnect
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
      const [repsResponse, callsResponse, metricsResponse] = await Promise.all([
        fetch('/api/sales/reps'),
        fetch('/api/sales/gong-calls'),
        fetch('/api/sales/team-metrics')
      ]);

      if (repsResponse.ok) {
        const reps = await repsResponse.json();
        setSalesReps(reps);
      }

      if (callsResponse.ok) {
        const calls = await callsResponse.json();
        setGongCalls(calls);
      }

      if (metricsResponse.ok) {
        const metrics = await metricsResponse.json();
        setTeamMetrics(metrics);
      }
    } catch (error) {
      console.error('Failed to load sales data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRealtimeUpdate = (data: unknown) => {
    switch (data.type) {
      case 'rep_update':
        setSalesReps(prev => prev.map(rep =>
          rep.id === data.rep.id ? { ...rep, ...data.rep } : rep
        ));
        break;
      case 'new_call':
        setGongCalls(prev => [data.call, ...prev]);
        break;
      case 'metrics_update':
        setTeamMetrics(prev => ({ ...prev, ...data.metrics }));
        break;
      case 'coaching_alert':
        setSalesReps(prev => prev.map(rep =>
          rep.id === data.rep_id
            ? { ...rep, coaching_alerts: [...rep.coaching_alerts, data.alert] }
            : rep
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
          context: 'sales_dashboard',
          current_rep: selectedRep?.id
        })
      });

      if (response.ok) {
        const result = await response.json();
        executeVoiceCommand(result);
      }
    } catch (error) {
      console.error('Voice command processing failed:', error);
    }
  }, [voiceEnabled, selectedRep]);

  const executeVoiceCommand = (result: unknown) => {
    switch (result.action) {
      case 'filter_reps':
        setFilterPerformance(result.filter);
        break;
      case 'select_rep':
        const rep = salesReps.find(r => r.name.toLowerCase().includes(result.rep_name.toLowerCase()));
        if (rep) setSelectedRep(rep);
        break;
      case 'play_call':
        if (result.call_id) playCallRecording(result.call_id);
        break;
      case 'show_coaching':
        setActiveTab('coaching');
        break;
    }
  };

  const playCallRecording = async (callId: string) => {
    const call = gongCalls.find(c => c.id === callId);
    if (!call) return;

    try {
      const response = await fetch(`/api/sales/gong-calls/${callId}/audio`);
      if (response.ok) {
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);

        if (audioRef.current) {
          audioRef.current.src = audioUrl;
          audioRef.current.play();
          setPlayingCall(callId);
        }
      }
    } catch (error) {
      console.error('Failed to play call recording:', error);
    }
  };

  // ==================== DATA PROCESSING ====================

  const getFilteredReps = () => {
    return salesReps.filter(rep => {
      const matchesSearch = rep.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                           rep.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
                           rep.territory.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesStatus = filterStatus === 'all' || rep.status === filterStatus;

      const matchesPerformance = filterPerformance === 'all' ||
        (filterPerformance === 'high' && rep.performance_score >= 80) ||
        (filterPerformance === 'medium' && rep.performance_score >= 50 && rep.performance_score < 80) ||
        (filterPerformance === 'low' && rep.performance_score < 50);

      return matchesSearch && matchesStatus && matchesPerformance;
    }).sort((a, b) => {
      switch (sortBy) {
        case 'performance_score': return b.performance_score - a.performance_score;
        case 'quota_achievement': return (b.achieved / b.quota) - (a.achieved / a.quota);
        case 'pipeline_value': return b.pipeline_value - a.pipeline_value;
        case 'calls_made': return b.calls_made - a.calls_made;
        default: return 0;
      }
    });
  };

  const getPerformanceColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getPerformanceIcon = (score: number) => {
    if (score >= 80) return <CheckCircle className="w-4 h-4 text-green-500" />;
    if (score >= 60) return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
    return <XCircle className="w-4 h-4 text-red-500" />;
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return <ArrowUp className="w-3 h-3 text-green-500" />;
      case 'down': return <ArrowDown className="w-3 h-3 text-red-500" />;
      default: return <Minus className="w-3 h-3 text-gray-500" />;
    }
  };

  const getCoachingAlertColor = (type: string) => {
    switch (type) {
      case 'red': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      case 'yellow': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'green': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  // ==================== RENDER METHODS ====================

  const renderRepCard = (rep: SalesRep) => (
    <Card
      key={rep.id}
      className={`cursor-pointer transition-all hover:shadow-lg ${
        selectedRep?.id === rep.id ? 'ring-2 ring-blue-500' : ''
      }`}
      onClick={() => setSelectedRep(rep)}
    >
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center text-white font-bold">
              {rep.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
            </div>
            <div>
              <CardTitle className="text-base">{rep.name}</CardTitle>
              <p className="text-xs text-gray-500">{rep.territory}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {getPerformanceIcon(rep.performance_score)}
            <Badge variant={rep.status === 'active' ? 'default' : 'secondary'}>
              {rep.status}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {/* Performance Score */}
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span>Performance Score</span>
              <span className={getPerformanceColor(rep.performance_score)}>
                {rep.performance_score}%
              </span>
            </div>
            <Progress value={rep.performance_score} className="h-1" />
          </div>

          {/* Quota Achievement */}
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span>Quota Achievement</span>
              <span className={getPerformanceColor((rep.achieved / rep.quota) * 100)}>
                {((rep.achieved / rep.quota) * 100).toFixed(1)}%
              </span>
            </div>
            <Progress value={(rep.achieved / rep.quota) * 100} className="h-1" />
          </div>

          {/* Key Metrics */}
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-gray-500">Calls:</span>
              <div className="flex items-center space-x-1">
                <span>{rep.calls_made}</span>
                {getTrendIcon(rep.trends.calls)}
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-500">Meetings:</span>
              <div className="flex items-center space-x-1">
                <span>{rep.meetings_scheduled}</span>
                {getTrendIcon(rep.trends.meetings)}
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-500">Deals:</span>
              <div className="flex items-center space-x-1">
                <span>{rep.deals_closed}</span>
                {getTrendIcon(rep.trends.deals)}
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-500">Pipeline:</span>
              <div className="flex items-center space-x-1">
                <span>${(rep.pipeline_value / 1000).toFixed(0)}k</span>
                {getTrendIcon(rep.trends.pipeline)}
              </div>
            </div>
          </div>

          {/* Coaching Alerts */}
          {rep.coaching_alerts.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {rep.coaching_alerts.slice(0, 2).map((alert) => (
                <Badge key={alert.id} className={`text-xs ${getCoachingAlertColor(alert.type)}`}>
                  {alert.category}
                </Badge>
              ))}
              {rep.coaching_alerts.length > 2 && (
                <Badge className="text-xs">+{rep.coaching_alerts.length - 2}</Badge>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );

  const renderCallCard = (call: GongCall) => (
    <Card key={call.id} className="mb-3">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-sm">{call.prospect_name}</CardTitle>
            <p className="text-xs text-gray-500">{call.company} • {call.rep_name}</p>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant={call.outcome === 'positive' ? 'default' :
                          call.outcome === 'negative' ? 'destructive' : 'secondary'}>
              {call.outcome}
            </Badge>
            <Button
              size="sm"
              variant="outline"
              onClick={() => playCallRecording(call.id)}
              disabled={playingCall === call.id}
            >
              {playingCall === call.id ? <Pause className="w-3 h-3" /> : <Play className="w-3 h-3" />}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="grid grid-cols-3 gap-2 text-xs">
            <div>
              <span className="text-gray-500">Duration:</span>
              <span className="ml-1">{Math.round(call.duration / 60)}min</span>
            </div>
            <div>
              <span className="text-gray-500">Sentiment:</span>
              <span className={`ml-1 ${call.sentiment_score > 0.3 ? 'text-green-600' :
                                     call.sentiment_score < -0.3 ? 'text-red-600' : 'text-yellow-600'}`}>
                {call.sentiment_score > 0.3 ? 'Positive' :
                 call.sentiment_score < -0.3 ? 'Negative' : 'Neutral'}
              </span>
            </div>
            <div>
              <span className="text-gray-500">Talk Ratio:</span>
              <span className="ml-1">{(call.talk_ratio * 100).toFixed(0)}%</span>
            </div>
          </div>

          {call.red_flags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              <span className="text-xs text-red-600 font-medium">Red Flags:</span>
              {call.red_flags.map((flag, idx) => (
                <Badge key={idx} variant="destructive" className="text-xs">
                  {flag}
                </Badge>
              ))}
            </div>
          )}

          {call.green_flags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              <span className="text-xs text-green-600 font-medium">Green Flags:</span>
              {call.green_flags.map((flag, idx) => (
                <Badge key={idx} className="text-xs bg-green-100 text-green-800">
                  {flag}
                </Badge>
              ))}
            </div>
          )}

          <div className="text-xs text-gray-700 dark:text-gray-300">
            <p className="font-medium">Next Steps:</p>
            <ul className="mt-1 space-y-1">
              {call.next_steps.map((step, idx) => (
                <li key={idx} className="ml-2">• {step}</li>
              ))}
            </ul>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-950">
      {/* Header */}
      <div className="border-b bg-white/80 dark:bg-gray-900/80 backdrop-blur-lg sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-10 h-10 rounded-full bg-gradient-to-r from-blue-600 to-purple-600 flex items-center justify-center">
                <Zap className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  Hermes Sales Intelligence
                </h1>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Real-time sales performance and coaching insights
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

              {/* Connection Status */}
              <Badge variant={connected ? 'default' : 'destructive'}>
                {connected ? 'Connected' : 'Disconnected'}
              </Badge>

              {/* Team Summary */}
              <div className="flex space-x-4 text-sm">
                <div>
                  <span className="text-gray-500">Team Quota:</span>
                  <span className="ml-1 font-bold">
                    {teamMetrics ? ((teamMetrics.total_achieved / teamMetrics.total_quota) * 100).toFixed(1) : 0}%
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">Active Deals:</span>
                  <span className="ml-1 font-bold">{teamMetrics?.active_deals || 0}</span>
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
            <TabsTrigger value="reps">
              <Users className="w-4 h-4 mr-2" />
              Sales Reps
            </TabsTrigger>
            <TabsTrigger value="pipeline">
              <BarChart3 className="w-4 h-4 mr-2" />
              Pipeline
            </TabsTrigger>
            <TabsTrigger value="calls">
              <Phone className="w-4 h-4 mr-2" />
              Gong Calls
            </TabsTrigger>
            <TabsTrigger value="coaching">
              <Target className="w-4 h-4 mr-2" />
              Coaching
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            {/* Key Metrics */}
            <div className="grid grid-cols-4 gap-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center">
                    <DollarSign className="w-4 h-4 mr-2" />
                    Team Revenue
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    ${teamMetrics?.total_achieved.toLocaleString() || '0'}
                  </div>
                  <Progress
                    value={(teamMetrics?.total_achieved || 0) / (teamMetrics?.total_quota || 1) * 100}
                    className="mt-2"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    {teamMetrics ? ((teamMetrics.total_achieved / teamMetrics.total_quota) * 100).toFixed(1) : 0}% of quota
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center">
                    <Phone className="w-4 h-4 mr-2" />
                    Calls This Week
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {teamMetrics?.total_calls_this_week || 0}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {gongCalls.filter(c => c.outcome === 'positive').length} positive outcomes
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center">
                    <Calendar className="w-4 h-4 mr-2" />
                    Meetings Scheduled
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {teamMetrics?.total_meetings_this_week || 0}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    This week
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center">
                    <Star className="w-4 h-4 mr-2" />
                    Team Score
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className={`text-2xl font-bold ${getPerformanceColor(teamMetrics?.team_performance_score || 0)}`}>
                    {teamMetrics?.team_performance_score || 0}%
                  </div>
                  <Progress
                    value={teamMetrics?.team_performance_score || 0}
                    className="mt-2"
                  />
                </CardContent>
              </Card>
            </div>

            {/* Top Performers & Recent Calls */}
            <div className="grid grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Top Performers</CardTitle>
                  <CardDescription>Highest performing reps this month</CardDescription>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-[400px]">
                    <div className="space-y-3">
                      {salesReps
                        .sort((a, b) => b.performance_score - a.performance_score)
                        .slice(0, 5)
                        .map((rep) => (
                          <div key={rep.id} className="flex items-center justify-between p-2 rounded hover:bg-gray-50">
                            <div className="flex items-center space-x-3">
                              <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center text-white text-xs font-bold">
                                {rep.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                              </div>
                              <div>
                                <p className="font-medium text-sm">{rep.name}</p>
                                <p className="text-xs text-gray-500">{rep.territory}</p>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className={`text-sm font-bold ${getPerformanceColor(rep.performance_score)}`}>
                                {rep.performance_score}%
                              </div>
                              <div className="text-xs text-gray-500">
                                ${(rep.achieved / 1000).toFixed(0)}k
                              </div>
                            </div>
                          </div>
                        ))}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Recent Calls</CardTitle>
                  <CardDescription>Latest Gong call analysis</CardDescription>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-[400px]">
                    <div className="space-y-2">
                      {gongCalls.slice(0, 8).map((call) => renderCallCard(call))}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Sales Reps Tab */}
          <TabsContent value="reps" className="space-y-6">
            {/* Filters */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Sales Representatives</CardTitle>
                  <div className="flex items-center space-x-2">
                    <Search className="w-4 h-4 text-gray-500" />
                    <Input
                      placeholder="Search reps..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-48"
                    />
                    <select
                      value={filterPerformance}
                      onChange={(e) => setFilterPerformance(e.target.value)}
                      className="border rounded px-2 py-1 text-sm"
                    >
                      <option value="all">All Performance</option>
                      <option value="high">High (80%+)</option>
                      <option value="medium">Medium (50-79%)</option>
                      <option value="low">Low (&lt;50%)</option>
                    </select>
                    <Button size="sm" onClick={loadInitialData}>
                      <RefreshCw className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
            </Card>

            {/* Reps Grid */}
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
              {getFilteredReps().map((rep) => renderRepCard(rep))}
            </div>
          </TabsContent>

          {/* Pipeline Tab */}
          <TabsContent value="pipeline" className="space-y-6">
            <div className="grid grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Pipeline Velocity</CardTitle>
                  <CardDescription>Average days per stage</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {teamMetrics?.velocity_metrics.map((stage) => (
                      <div key={stage.stage} className="space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="text-sm font-medium">{stage.stage}</span>
                          <div className="flex items-center space-x-2">
                            <span className="text-sm">{stage.average_days} days</span>
                            {getTrendIcon(stage.trend)}
                          </div>
                        </div>
                        <div className="flex justify-between text-xs text-gray-500">
                          <span>{stage.current_deals} deals</span>
                          <span>${(stage.value / 1000).toFixed(0)}k</span>
                        </div>
                        <Progress value={stage.conversion_rate} className="h-1" />
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Deal Distribution</CardTitle>
                  <CardDescription>Current pipeline by stage</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-64 flex items-center justify-center">
                    <PieChart className="w-16 h-16 text-gray-400" />
                    <span className="ml-4 text-gray-500">Pipeline visualization</span>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Calls Tab */}
          <TabsContent value="calls" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Gong Call Analysis</CardTitle>
                <CardDescription>AI-powered conversation insights</CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[600px]">
                  <div className="space-y-2">
                    {gongCalls.map((call) => renderCallCard(call))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Coaching Tab */}
          <TabsContent value="coaching" className="space-y-6">
            <div className="grid grid-cols-3 gap-6">
              {['red', 'yellow', 'green'].map((alertType) => (
                <Card key={alertType}>
                  <CardHeader>
                    <CardTitle className={`flex items-center ${
                      alertType === 'red' ? 'text-red-600' :
                      alertType === 'yellow' ? 'text-yellow-600' : 'text-green-600'
                    }`}>
                      {alertType === 'red' && <XCircle className="w-4 h-4 mr-2" />}
                      {alertType === 'yellow' && <AlertTriangle className="w-4 h-4 mr-2" />}
                      {alertType === 'green' && <CheckCircle className="w-4 h-4 mr-2" />}
                      {alertType.charAt(0).toUpperCase() + alertType.slice(1)} Alerts
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ScrollArea className="h-[400px]">
                      <div className="space-y-3">
                        {salesReps
                          .flatMap(rep => rep.coaching_alerts.filter(alert => alert.type === alertType))
                          .sort((a, b) => b.priority - a.priority)
                          .map((alert) => {
                            const rep = salesReps.find(r => r.coaching_alerts.some(a => a.id === alert.id));
                            return (
                              <div key={alert.id} className="p-3 border rounded">
                                <div className="flex items-start justify-between mb-2">
                                  <div className="text-sm font-medium">{rep?.name}</div>
                                  <Badge variant="outline">{alert.category}</Badge>
                                </div>
                                <p className="text-xs text-gray-700 dark:text-gray-300 mb-2">
                                  {alert.message}
                                </p>
                                <p className="text-xs font-medium text-blue-600">
                                  Action: {alert.action_needed}
                                </p>
                              </div>
                            );
                          })}
                      </div>
                    </ScrollArea>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </div>

      {/* Selected Rep Detail Panel */}
      {selectedRep && (
        <div className="fixed right-4 top-24 w-96 bg-white dark:bg-gray-900 rounded-lg shadow-2xl border p-4 z-40 max-h-[80vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold">Rep Details</h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSelectedRep(null)}
            >
              <XCircle className="w-4 h-4" />
            </Button>
          </div>

          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center text-white font-bold">
                {selectedRep.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
              </div>
              <div>
                <h4 className="font-medium">{selectedRep.name}</h4>
                <p className="text-sm text-gray-500">{selectedRep.email}</p>
                <p className="text-xs text-gray-500">{selectedRep.territory}</p>
              </div>
            </div>

            <Separator />

            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span>Performance Score:</span>
                <span className={getPerformanceColor(selectedRep.performance_score)}>
                  {selectedRep.performance_score}%
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Quota Achievement:</span>
                <span>${selectedRep.achieved.toLocaleString()} / ${selectedRep.quota.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Pipeline Value:</span>
                <span>${selectedRep.pipeline_value.toLocaleString()}</span>
              </div>
            </div>

            <Separator />

            <div>
              <h5 className="font-medium mb-2">Recent Coaching Alerts</h5>
              <div className="space-y-2">
                {selectedRep.coaching_alerts.slice(0, 3).map((alert) => (
                  <div key={alert.id} className={`p-2 rounded text-xs ${getCoachingAlertColor(alert.type)}`}>
                    <div className="font-medium">{alert.category}</div>
                    <div>{alert.message}</div>
                  </div>
                ))}
              </div>
            </div>

            <Button className="w-full" size="sm">
              <MessageCircle className="w-4 h-4 mr-2" />
              Start Coaching Session
            </Button>
          </div>
        </div>
      )}

      {/* Audio Element for Call Playback */}
      <audio
        ref={audioRef}
        onEnded={() => setPlayingCall(null)}
        className="hidden"
      />
    </div>
  );
};

export default SalesPerformanceDashboard;