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
  Activity, Users, Clock, Target, AlertTriangle, CheckCircle,
  XCircle, Calendar, BarChart3, PieChart, TrendingUp, TrendingDown,
  Minus, Search, RefreshCw, Filter, MessageCircle, Phone, Mail,
  Zap, Eye, Brain, Settings, GitBranch, Code, Bug, FileText,
  ArrowUp, ArrowDown, Star, Flag, Lightbulb, Shield, Mic, MicOff,
  Play, Pause, Volume2, ExternalLink, Copy, Download, Upload
} from 'lucide-react';

// ==================== TYPES ====================

interface Project {
  id: string;
  name: string;
  description: string;
  status: 'planning' | 'active' | 'on_hold' | 'completed' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'critical';
  progress: number;
  start_date: string;
  due_date: string;
  team_lead: string;
  team_members: string[];
  platforms: Platform[];
  budget: number;
  spent: number;
  health_score: number;
  risk_factors: string[];
  blockers: Blocker[];
  milestones: Milestone[];
  sprint_info?: SprintInfo;
  communication_health: number;
  alignment_score: number;
  velocity_trend: 'up' | 'down' | 'stable';
  last_update: string;
}

interface Platform {
  type: 'linear' | 'asana' | 'airtable' | 'github' | 'jira';
  project_id: string;
  url: string;
  sync_status: 'connected' | 'disconnected' | 'syncing' | 'error';
  last_sync: string;
  tasks_count: number;
  completed_tasks: number;
}

interface Blocker {
  id: string;
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  category: 'technical' | 'resource' | 'dependency' | 'approval';
  created_date: string;
  assigned_to: string;
  estimated_resolution: string;
  status: 'open' | 'in_progress' | 'resolved' | 'escalated';
}

interface Milestone {
  id: string;
  name: string;
  description: string;
  due_date: string;
  completion_date?: string;
  status: 'upcoming' | 'in_progress' | 'completed' | 'overdue';
  dependencies: string[];
  deliverables: string[];
  progress: number;
}

interface SprintInfo {
  current_sprint: number;
  sprint_start: string;
  sprint_end: string;
  sprint_goal: string;
  planned_points: number;
  completed_points: number;
  velocity: number;
  burndown_data: { day: number; remaining: number }[];
}

interface TeamMember {
  id: string;
  name: string;
  email: string;
  role: string;
  avatar?: string;
  workload: number; // 0-100%
  current_tasks: number;
  completed_tasks_week: number;
  productivity_score: number;
  availability: 'available' | 'busy' | 'away' | 'offline';
  skills: string[];
  projects: string[];
}

interface CrossPlatformSync {
  platform: string;
  status: 'connected' | 'disconnected' | 'syncing' | 'error';
  last_sync: string;
  total_items: number;
  synced_items: number;
  error_message?: string;
}

interface CommunicationMetrics {
  daily_standup_attendance: number;
  weekly_review_completion: number;
  documentation_coverage: number;
  response_time_hours: number;
  collaboration_score: number;
  knowledge_sharing_index: number;
}

// ==================== ATHENA PROJECT MANAGEMENT DASHBOARD ====================

const ProjectManagementDashboard: React.FC = () => {
  // Core State
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);

  // Data State
  const [projects, setProjects] = useState<Project[]>([]);
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);
  const [syncStatuses, setSyncStatuses] = useState<CrossPlatformSync[]>([]);
  const [communicationMetrics, setCommunicationMetrics] = useState<CommunicationMetrics | null>(null);

  // Filter & Search State
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterPriority, setFilterPriority] = useState<string>('all');
  const [filterPlatform, setFilterPlatform] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('health_score');

  // UI State
  const [activeTab, setActiveTab] = useState('overview');
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [selectedMember, setSelectedMember] = useState<TeamMember | null>(null);

  const ws = useRef<WebSocket | null>(null);

  // ==================== WEBSOCKET & DATA LOADING ====================

  useEffect(() => {
    connectWebSocket();
    loadInitialData();
    return () => {
      if (ws.current) ws.current.close();
    };
  }, []);

  const connectWebSocket = () => {
    try {
      ws.current = new WebSocket('/ws/project-mgmt-athena');

      ws.current.onopen = () => {
        setConnected(true);
        sendCommand({ type: 'subscribe', channel: 'project_management' });
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
      const [projectsResponse, teamResponse, syncResponse, commResponse] = await Promise.all([
        fetch('/api/projects'),
        fetch('/api/team/members'),
        fetch('/api/projects/sync-status'),
        fetch('/api/projects/communication-metrics')
      ]);

      if (projectsResponse.ok) {
        const projectsData = await projectsResponse.json();
        setProjects(projectsData);
      }

      if (teamResponse.ok) {
        const teamData = await teamResponse.json();
        setTeamMembers(teamData);
      }

      if (syncResponse.ok) {
        const syncData = await syncResponse.json();
        setSyncStatuses(syncData);
      }

      if (commResponse.ok) {
        const commData = await commResponse.json();
        setCommunicationMetrics(commData);
      }
    } catch (error) {
      console.error('Failed to load project management data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRealtimeUpdate = (data: any) => {
    switch (data.type) {
      case 'project_update':
        setProjects(prev => prev.map(project =>
          project.id === data.project.id ? { ...project, ...data.project } : project
        ));
        break;
      case 'blocker_added':
        setProjects(prev => prev.map(project =>
          project.id === data.project_id
            ? { ...project, blockers: [...project.blockers, data.blocker] }
            : project
        ));
        break;
      case 'milestone_completed':
        setProjects(prev => prev.map(project =>
          project.id === data.project_id
            ? {
                ...project,
                milestones: project.milestones.map(m =>
                  m.id === data.milestone_id ? { ...m, status: 'completed', completion_date: data.completion_date } : m
                )
              }
            : project
        ));
        break;
      case 'sync_status_update':
        setSyncStatuses(prev => prev.map(sync =>
          sync.platform === data.platform ? { ...sync, ...data.status } : sync
        ));
        break;
      case 'team_member_update':
        setTeamMembers(prev => prev.map(member =>
          member.id === data.member.id ? { ...member, ...data.member } : member
        ));
        break;
    }
  };

  const sendCommand = (command: any) => {
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
          context: 'project_management_dashboard',
          current_project: selectedProject?.id
        })
      });

      if (response.ok) {
        const result = await response.json();
        executeVoiceCommand(result);
      }
    } catch (error) {
      console.error('Voice command processing failed:', error);
    }
  }, [voiceEnabled, selectedProject]);

  const executeVoiceCommand = (result: any) => {
    switch (result.action) {
      case 'filter_projects':
        setFilterStatus(result.status);
        break;
      case 'select_project':
        const project = projects.find(p => p.name.toLowerCase().includes(result.project_name.toLowerCase()));
        if (project) setSelectedProject(project);
        break;
      case 'show_blockers':
        setActiveTab('blockers');
        break;
      case 'show_team':
        setActiveTab('team');
        break;
      case 'sync_platforms':
        syncAllPlatforms();
        break;
    }
  };

  // ==================== ACTIONS ====================

  const syncAllPlatforms = async () => {
    try {
      const response = await fetch('/api/projects/sync-all', {
        method: 'POST'
      });

      if (response.ok) {
        setSyncStatuses(prev => prev.map(sync => ({ ...sync, status: 'syncing' })));
      }
    } catch (error) {
      console.error('Failed to sync platforms:', error);
    }
  };

  const resolveBlocker = async (projectId: string, blockerId: string) => {
    try {
      await fetch(`/api/projects/${projectId}/blockers/${blockerId}/resolve`, {
        method: 'POST'
      });

      setProjects(prev => prev.map(project =>
        project.id === projectId
          ? {
              ...project,
              blockers: project.blockers.map(b =>
                b.id === blockerId ? { ...b, status: 'resolved' } : b
              )
            }
          : project
      ));
    } catch (error) {
      console.error('Failed to resolve blocker:', error);
    }
  };

  // ==================== DATA PROCESSING ====================

  const getFilteredProjects = () => {
    return projects.filter(project => {
      const matchesSearch = project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                           project.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
                           project.team_lead.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesStatus = filterStatus === 'all' || project.status === filterStatus;
      const matchesPriority = filterPriority === 'all' || project.priority === filterPriority;

      const matchesPlatform = filterPlatform === 'all' ||
        project.platforms.some(p => p.type === filterPlatform);

      return matchesSearch && matchesStatus && matchesPriority && matchesPlatform;
    }).sort((a, b) => {
      const aVal = a[sortBy as keyof Project] as number;
      const bVal = b[sortBy as keyof Project] as number;
      return bVal - aVal;
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

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'low': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'high': return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200';
      case 'critical': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'planning': return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
      case 'active': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'on_hold': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'completed': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'cancelled': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  const getSyncStatusIcon = (status: string) => {
    switch (status) {
      case 'connected': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'syncing': return <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'error': return <XCircle className="w-4 h-4 text-red-500" />;
      default: return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return <ArrowUp className="w-3 h-3 text-green-500" />;
      case 'down': return <ArrowDown className="w-3 h-3 text-red-500" />;
      default: return <Minus className="w-3 h-3 text-gray-500" />;
    }
  };

  // ==================== RENDER METHODS ====================

  const renderProjectCard = (project: Project) => (
    <Card
      key={project.id}
      className={`cursor-pointer transition-all hover:shadow-lg ${
        selectedProject?.id === project.id ? 'ring-2 ring-blue-500' : ''
      }`}
      onClick={() => setSelectedProject(project)}
    >
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center text-white font-bold">
              {project.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
            </div>
            <div>
              <CardTitle className="text-base">{project.name}</CardTitle>
              <p className="text-xs text-gray-500">{project.team_lead} • {project.team_members.length} members</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {getHealthIcon(project.health_score)}
            <Badge className={getPriorityColor(project.priority)}>
              {project.priority}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {/* Progress */}
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span>Progress</span>
              <span className="font-medium">{project.progress}%</span>
            </div>
            <Progress value={project.progress} className="h-1" />
          </div>

          {/* Status & Budget */}
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-gray-500">Status:</span>
              <Badge className={`${getStatusColor(project.status)} text-xs`}>
                {project.status.replace('_', ' ')}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-500">Budget:</span>
              <span>{((project.spent / project.budget) * 100).toFixed(0)}%</span>
            </div>
          </div>

          {/* Health Metrics */}
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-gray-500">Health:</span>
              <div className="flex items-center space-x-1">
                <span className={getHealthColor(project.health_score)}>{project.health_score}%</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-500">Velocity:</span>
              <div className="flex items-center space-x-1">
                <span>Stable</span>
                {getTrendIcon(project.velocity_trend)}
              </div>
            </div>
          </div>

          {/* Platform Sync Status */}
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500">Platforms:</span>
            <div className="flex space-x-1">
              {project.platforms.slice(0, 3).map((platform) => (
                <div key={platform.type} className="flex items-center">
                  {getSyncStatusIcon(platform.sync_status)}
                </div>
              ))}
              {project.platforms.length > 3 && (
                <span className="text-xs text-gray-500">+{project.platforms.length - 3}</span>
              )}
            </div>
          </div>

          {/* Blockers */}
          {project.blockers.length > 0 && (
            <div className="flex items-center justify-between bg-red-50 dark:bg-red-950 p-2 rounded">
              <span className="text-xs text-red-700 dark:text-red-300">
                {project.blockers.length} active blockers
              </span>
              <Badge variant="destructive" className="text-xs">
                {project.blockers.filter(b => b.severity === 'critical').length} critical
              </Badge>
            </div>
          )}

          {/* Communication Health */}
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-gray-500">Communication:</span>
              <span className={getHealthColor(project.communication_health)}>{project.communication_health}%</span>
            </div>
            <Progress value={project.communication_health} className="h-1" />
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const renderBlockerCard = (blocker: Blocker, projectName: string) => (
    <Card key={blocker.id} className="mb-3">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-sm">{blocker.title}</CardTitle>
            <p className="text-xs text-gray-500">{projectName} • {blocker.category}</p>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant={blocker.severity === 'critical' ? 'destructive' : 'secondary'}>
              {blocker.severity}
            </Badge>
            <Badge className={getStatusColor(blocker.status)}>
              {blocker.status.replace('_', ' ')}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <p className="text-xs text-gray-700 dark:text-gray-300">{blocker.description}</p>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-gray-500">Assigned:</span>
              <span className="ml-1">{blocker.assigned_to}</span>
            </div>
            <div>
              <span className="text-gray-500">ETA:</span>
              <span className="ml-1">{blocker.estimated_resolution}</span>
            </div>
          </div>
          {blocker.status === 'open' && (
            <Button
              size="sm"
              variant="outline"
              className="w-full text-xs"
              onClick={() => resolveBlocker(
                projects.find(p => p.blockers.some(b => b.id === blocker.id))?.id || '',
                blocker.id
              )}
            >
              Mark as Resolved
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );

  const renderTeamMemberCard = (member: TeamMember) => (
    <Card key={member.id} className="cursor-pointer hover:shadow-lg" onClick={() => setSelectedMember(member)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center text-white font-bold">
              {member.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
            </div>
            <div>
              <CardTitle className="text-base">{member.name}</CardTitle>
              <p className="text-xs text-gray-500">{member.role}</p>
            </div>
          </div>
          <Badge variant={member.availability === 'available' ? 'default' : 'secondary'}>
            {member.availability}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {/* Workload */}
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span>Workload</span>
              <span className={member.workload > 90 ? 'text-red-600' : member.workload > 75 ? 'text-yellow-600' : 'text-green-600'}>
                {member.workload}%
              </span>
            </div>
            <Progress value={member.workload} className="h-1" />
          </div>

          {/* Tasks & Productivity */}
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-gray-500">Active Tasks:</span>
              <span>{member.current_tasks}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-500">This Week:</span>
              <span>{member.completed_tasks_week}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-500">Productivity:</span>
              <span className={getHealthColor(member.productivity_score)}>{member.productivity_score}%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-500">Projects:</span>
              <span>{member.projects.length}</span>
            </div>
          </div>

          {/* Skills */}
          <div className="flex flex-wrap gap-1">
            {member.skills.slice(0, 3).map((skill) => (
              <Badge key={skill} variant="outline" className="text-xs">
                {skill}
              </Badge>
            ))}
            {member.skills.length > 3 && (
              <Badge variant="outline" className="text-xs">
                +{member.skills.length - 3}
              </Badge>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-100 dark:from-gray-900 dark:to-gray-950">
      {/* Header */}
      <div className="border-b bg-white/80 dark:bg-gray-900/80 backdrop-blur-lg sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-10 h-10 rounded-full bg-gradient-to-r from-purple-600 to-pink-600 flex items-center justify-center">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                  Athena Project Intelligence
                </h1>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Cross-platform project management and team alignment
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

              {/* Sync All Platforms */}
              <Button size="sm" onClick={syncAllPlatforms}>
                <RefreshCw className="w-4 h-4" />
                Sync All
              </Button>

              {/* Connection Status */}
              <Badge variant={connected ? 'default' : 'destructive'}>
                {connected ? 'Connected' : 'Disconnected'}
              </Badge>

              {/* Team Summary */}
              <div className="flex space-x-4 text-sm">
                <div>
                  <span className="text-gray-500">Active Projects:</span>
                  <span className="ml-1 font-bold">{projects.filter(p => p.status === 'active').length}</span>
                </div>
                <div>
                  <span className="text-gray-500">Blockers:</span>
                  <span className="ml-1 font-bold text-red-600">
                    {projects.reduce((sum, p) => sum + p.blockers.length, 0)}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid grid-cols-6 w-full">
            <TabsTrigger value="overview">
              <Activity className="w-4 h-4 mr-2" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="projects">
              <Target className="w-4 h-4 mr-2" />
              Projects
            </TabsTrigger>
            <TabsTrigger value="team">
              <Users className="w-4 h-4 mr-2" />
              Team
            </TabsTrigger>
            <TabsTrigger value="blockers">
              <AlertTriangle className="w-4 h-4 mr-2" />
              Blockers
            </TabsTrigger>
            <TabsTrigger value="platforms">
              <GitBranch className="w-4 h-4 mr-2" />
              Platforms
            </TabsTrigger>
            <TabsTrigger value="communication">
              <MessageCircle className="w-4 h-4 mr-2" />
              Communication
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            {/* Key Metrics */}
            <div className="grid grid-cols-5 gap-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center">
                    <Target className="w-4 h-4 mr-2 text-purple-600" />
                    Active Projects
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {projects.filter(p => p.status === 'active').length}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {projects.filter(p => p.health_score < 60).length} need attention
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center">
                    <Users className="w-4 h-4 mr-2 text-purple-600" />
                    Team Members
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {teamMembers.length}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {teamMembers.filter(m => m.availability === 'available').length} available now
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center">
                    <AlertTriangle className="w-4 h-4 mr-2 text-red-500" />
                    Active Blockers
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-red-600">
                    {projects.reduce((sum, p) => sum + p.blockers.filter(b => b.status === 'open').length, 0)}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {projects.reduce((sum, p) => sum + p.blockers.filter(b => b.severity === 'critical').length, 0)} critical
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center">
                    <MessageCircle className="w-4 h-4 mr-2 text-purple-600" />
                    Communication
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className={`text-2xl font-bold ${getHealthColor(communicationMetrics?.collaboration_score || 0)}`}>
                    {communicationMetrics?.collaboration_score || 0}%
                  </div>
                  <p className="text-xs text-gray-500 mt-1">Team alignment score</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center">
                    <GitBranch className="w-4 h-4 mr-2 text-purple-600" />
                    Platform Sync
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {syncStatuses.filter(s => s.status === 'connected').length}/{syncStatuses.length}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">Platforms connected</p>
                </CardContent>
              </Card>
            </div>

            {/* Project Health & Team Workload */}
            <div className="grid grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Project Health Overview</CardTitle>
                  <CardDescription>Health scores across all active projects</CardDescription>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-[400px]">
                    <div className="space-y-3">
                      {projects
                        .filter(p => p.status === 'active')
                        .sort((a, b) => a.health_score - b.health_score)
                        .map((project) => (
                          <div key={project.id} className="flex items-center justify-between p-2 rounded hover:bg-gray-50">
                            <div className="flex items-center space-x-3">
                              <div className="w-8 h-8 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center text-white text-xs font-bold">
                                {project.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                              </div>
                              <div>
                                <p className="font-medium text-sm">{project.name}</p>
                                <p className="text-xs text-gray-500">{project.team_lead}</p>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className={`text-sm font-bold ${getHealthColor(project.health_score)}`}>
                                {project.health_score}%
                              </div>
                              <div className="text-xs text-gray-500">
                                {project.progress}% complete
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
                  <CardTitle>Team Workload</CardTitle>
                  <CardDescription>Current capacity and availability</CardDescription>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-[400px]">
                    <div className="space-y-3">
                      {teamMembers
                        .sort((a, b) => b.workload - a.workload)
                        .map((member) => (
                          <div key={member.id} className="flex items-center justify-between p-2 rounded hover:bg-gray-50">
                            <div className="flex items-center space-x-3">
                              <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center text-white text-xs font-bold">
                                {member.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                              </div>
                              <div>
                                <p className="font-medium text-sm">{member.name}</p>
                                <p className="text-xs text-gray-500">{member.role}</p>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className={`text-sm font-bold ${
                                member.workload > 90 ? 'text-red-600' :
                                member.workload > 75 ? 'text-yellow-600' : 'text-green-600'
                              }`}>
                                {member.workload}%
                              </div>
                              <div className="text-xs text-gray-500">
                                {member.current_tasks} active tasks
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

          {/* Projects Tab */}
          <TabsContent value="projects" className="space-y-6">
            {/* Filters */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>All Projects</CardTitle>
                  <div className="flex items-center space-x-2">
                    <Search className="w-4 h-4 text-gray-500" />
                    <Input
                      placeholder="Search projects..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-48"
                    />
                    <select
                      value={filterStatus}
                      onChange={(e) => setFilterStatus(e.target.value)}
                      className="border rounded px-2 py-1 text-sm"
                    >
                      <option value="all">All Status</option>
                      <option value="active">Active</option>
                      <option value="planning">Planning</option>
                      <option value="on_hold">On Hold</option>
                      <option value="completed">Completed</option>
                    </select>
                    <select
                      value={filterPriority}
                      onChange={(e) => setFilterPriority(e.target.value)}
                      className="border rounded px-2 py-1 text-sm"
                    >
                      <option value="all">All Priority</option>
                      <option value="critical">Critical</option>
                      <option value="high">High</option>
                      <option value="medium">Medium</option>
                      <option value="low">Low</option>
                    </select>
                    <Button size="sm" onClick={loadInitialData}>
                      <RefreshCw className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
            </Card>

            {/* Projects Grid */}
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
              {getFilteredProjects().map((project) => renderProjectCard(project))}
            </div>
          </TabsContent>

          {/* Team Tab */}
          <TabsContent value="team" className="space-y-6">
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
              {teamMembers.map((member) => renderTeamMemberCard(member))}
            </div>
          </TabsContent>

          {/* Blockers Tab */}
          <TabsContent value="blockers" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Active Blockers</CardTitle>
                <CardDescription>Issues requiring immediate attention</CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[600px]">
                  <div className="space-y-2">
                    {projects
                      .flatMap(project =>
                        project.blockers
                          .filter(blocker => blocker.status === 'open')
                          .map(blocker => renderBlockerCard(blocker, project.name))
                      )}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Platforms Tab */}
          <TabsContent value="platforms" className="space-y-6">
            <div className="grid grid-cols-2 gap-6">
              {syncStatuses.map((sync) => (
                <Card key={sync.platform}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="capitalize">{sync.platform}</CardTitle>
                      {getSyncStatusIcon(sync.status)}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Status:</span>
                        <Badge className={getStatusColor(sync.status)}>
                          {sync.status}
                        </Badge>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Last Sync:</span>
                        <span>{new Date(sync.last_sync).toLocaleDateString()}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Items Synced:</span>
                        <span>{sync.synced_items}/{sync.total_items}</span>
                      </div>
                      <Progress value={(sync.synced_items / sync.total_items) * 100} className="h-1" />
                      {sync.error_message && (
                        <Alert>
                          <AlertTriangle className="h-4 w-4" />
                          <AlertDescription className="text-xs">
                            {sync.error_message}
                          </AlertDescription>
                        </Alert>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* Communication Tab */}
          <TabsContent value="communication" className="space-y-6">
            <div className="grid grid-cols-3 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Standup Attendance</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-center">
                    {communicationMetrics?.daily_standup_attendance || 0}%
                  </div>
                  <Progress value={communicationMetrics?.daily_standup_attendance || 0} className="mt-2" />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Documentation Coverage</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-center">
                    {communicationMetrics?.documentation_coverage || 0}%
                  </div>
                  <Progress value={communicationMetrics?.documentation_coverage || 0} className="mt-2" />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Avg Response Time</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-center">
                    {communicationMetrics?.response_time_hours || 0}h
                  </div>
                  <p className="text-xs text-gray-500 text-center mt-2">
                    Average response time
                  </p>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Communication Health Breakdown</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {[
                    { label: 'Daily Standup Attendance', value: communicationMetrics?.daily_standup_attendance || 0 },
                    { label: 'Weekly Review Completion', value: communicationMetrics?.weekly_review_completion || 0 },
                    { label: 'Documentation Coverage', value: communicationMetrics?.documentation_coverage || 0 },
                    { label: 'Collaboration Score', value: communicationMetrics?.collaboration_score || 0 },
                    { label: 'Knowledge Sharing Index', value: communicationMetrics?.knowledge_sharing_index || 0 }
                  ].map((metric) => (
                    <div key={metric.label} className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm">{metric.label}</span>
                        <span className={`text-sm font-bold ${getHealthColor(metric.value)}`}>
                          {metric.value}%
                        </span>
                      </div>
                      <Progress value={metric.value} className="h-1" />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      {/* Selected Project Detail Panel */}
      {selectedProject && (
        <div className="fixed right-4 top-24 w-96 bg-white dark:bg-gray-900 rounded-lg shadow-2xl border p-4 z-40 max-h-[80vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold">Project Details</h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSelectedProject(null)}
            >
              <XCircle className="w-4 h-4" />
            </Button>
          </div>

          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center text-white font-bold">
                {selectedProject.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
              </div>
              <div>
                <h4 className="font-medium">{selectedProject.name}</h4>
                <p className="text-sm text-gray-500">{selectedProject.team_lead}</p>
                <p className="text-xs text-gray-500">{selectedProject.team_members.length} team members</p>
              </div>
            </div>

            <Separator />

            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Progress:</span>
                <span>{selectedProject.progress}%</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Health Score:</span>
                <span className={getHealthColor(selectedProject.health_score)}>
                  {selectedProject.health_score}%
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Budget Used:</span>
                <span>{((selectedProject.spent / selectedProject.budget) * 100).toFixed(0)}%</span>
              </div>
            </div>

            <Separator />

            {selectedProject.blockers.length > 0 && (
              <div>
                <h5 className="font-medium mb-2">Active Blockers</h5>
                <div className="space-y-2">
                  {selectedProject.blockers.filter(b => b.status === 'open').slice(0, 3).map((blocker) => (
                    <div key={blocker.id} className="p-2 border rounded text-xs">
                      <div className="font-medium">{blocker.title}</div>
                      <div className="text-gray-500">{blocker.category} • {blocker.severity}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <Separator />

            <div className="space-y-2">
              <Button className="w-full" size="sm">
                <ExternalLink className="w-4 h-4 mr-2" />
                View in Platform
              </Button>
              <Button className="w-full" size="sm" variant="outline">
                <MessageCircle className="w-4 h-4 mr-2" />
                Team Chat
              </Button>
              <Button className="w-full" size="sm" variant="outline">
                <Calendar className="w-4 h-4 mr-2" />
                Schedule Review
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectManagementDashboard;
