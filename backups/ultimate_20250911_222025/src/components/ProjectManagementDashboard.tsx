"use client";

import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Activity, AlertTriangle, Users, TrendingUp, MessageSquare,
  CheckCircle, XCircle, Clock, Target, GitBranch, Briefcase,
  BarChart3, Calendar, ChevronRight, RefreshCw, AlertCircle,
  Zap, Layers, Shield, Star, ArrowUpRight, ArrowDownRight
} from 'lucide-react';
import { apiBaseUrl } from '@/config/environment';

// ==================== TYPE DEFINITIONS ====================

interface ProjectSource {
  asana: { configured: boolean; details: string };
  linear: { configured: boolean; details: string };
  slack: { configured: boolean; details: string };
  airtable: { configured: boolean; details: string };
}

interface Project {
  name: string;
  owner?: string;
  status: string;
  due_date?: string;
  is_overdue?: boolean;
  risk?: 'low' | 'medium' | 'high' | 'critical';
  source: 'asana' | 'linear' | 'slack';
  completion?: number;
  team?: string;
}

interface CommunicationIssue {
  pattern?: string;
  issue?: string;
  impact?: string;
  channel?: string;
  source: string;
}

interface TeamMetrics {
  team: string;
  velocity: number;
  velocity_trend: 'increasing' | 'stable' | 'decreasing';
  cycle_time: number;
  blocked_items: number;
  health_score: number;
}

interface PMOverview {
  generated_at: string;
  sources: ProjectSource;
  okrs?: Array<{ id?: string; name: string }>;
  okr_alignment?: Record<string, any>;
  major_projects: Project[];
  blockages: string[];
  communication_issues: CommunicationIssue[];
  notes: string[];
  departments_scorecard?: TeamMetrics[];
}

// ==================== COMPONENT ====================

export default function ProjectManagementDashboard() {
  const [overview, setOverview] = useState<PMOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [selectedSource, setSelectedSource] = useState<'all' | 'asana' | 'linear' | 'slack'>('all');

  // Fetch project overview
  const fetchOverview = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${apiBaseUrl}/api/projects/overview`, { cache: 'no-store' });
      if (!response.ok) throw new Error('Failed to fetch project overview');
      const data = await response.json();
      setOverview(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  // Auto-refresh every 60 seconds if enabled
  useEffect(() => {
    fetchOverview();
    
    if (autoRefresh) {
      const interval = setInterval(fetchOverview, 60000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  // Filter projects by source
  const filteredProjects = overview?.major_projects.filter(
    p => selectedSource === 'all' || p.source === selectedSource
  ) || [];

  // Calculate risk distribution
  const riskDistribution = {
    critical: filteredProjects.filter(p => p.risk === 'critical' || p.is_overdue).length,
    high: filteredProjects.filter(p => p.risk === 'high').length,
    medium: filteredProjects.filter(p => p.risk === 'medium').length,
    low: filteredProjects.filter(p => p.risk === 'low' || (!p.risk && !p.is_overdue)).length
  };

  // Source health indicators
  const getSourceStatus = (source: keyof ProjectSource) => {
    if (!overview) return 'offline';
    return overview.sources[source].configured ? 'online' : 'offline';
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Project Management Intelligence</h1>
          <p className="text-muted-foreground mt-1">
            Unified insights from Asana, Linear, and Slack
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant={autoRefresh ? "default" : "outline"}
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
            Auto-refresh
          </Button>
          <Button onClick={fetchOverview} disabled={loading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh Now
          </Button>
        </div>
      </div>

      {/* Source Status Cards */}
      <div className="grid grid-cols-4 gap-4">
        {(['asana', 'linear', 'slack', 'airtable'] as const).map(source => (
          <Card key={source}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {source === 'asana' && <Briefcase className="w-5 h-5 text-orange-500" />}
                  {source === 'linear' && <GitBranch className="w-5 h-5 text-blue-500" />}
                  {source === 'slack' && <MessageSquare className="w-5 h-5 text-purple-500" />}
                  {source === 'airtable' && <Layers className="w-5 h-5 text-green-500" />}
                  <span className="font-medium capitalize">{source}</span>
                </div>
                <Badge 
                  variant={getSourceStatus(source) === 'online' ? 'default' : 'secondary'}
                  className={getSourceStatus(source) === 'online' ? 'bg-green-500' : ''}
                >
                  {getSourceStatus(source)}
                </Badge>
              </div>
              {overview && (
                <p className="text-xs text-muted-foreground mt-2">
                  {overview.sources[source].details}
                </p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Risk Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5" />
            Risk Overview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-red-500">{riskDistribution.critical}</div>
              <div className="text-sm text-muted-foreground">Critical</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-500">{riskDistribution.high}</div>
              <div className="text-sm text-muted-foreground">High</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-500">{riskDistribution.medium}</div>
              <div className="text-sm text-muted-foreground">Medium</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-500">{riskDistribution.low}</div>
              <div className="text-sm text-muted-foreground">Low</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* OKR Alignment */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="w-5 h-5" />
            OKR Alignment
          </CardTitle>
          <CardDescription>
            Company OKRs from Airtable and alignment signals across projects
          </CardDescription>
        </CardHeader>
        <CardContent>
          {overview?.okrs && overview.okrs.length > 0 ? (
            <div className="space-y-2">
              {overview.okrs.map((okr, idx) => (
                <div key={okr.id || idx} className="flex items-center justify-between border rounded p-2">
                  <div className="text-sm font-medium">{okr.name}</div>
                  <Badge variant="outline">Coming Soon</Badge>
                </div>
              ))}
              <div className="text-xs text-muted-foreground mt-2">
                Alignment scoring and drilldowns will appear here as data accrues.
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <AlertCircle className="w-12 h-12 mx-auto mb-3" />
              <p>Coming Soon</p>
              <p className="text-xs mt-1">Connect Airtable and tag OKR records to enable alignment analysis.</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Main Tabs */}
      <Tabs defaultValue="projects" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="projects">Projects</TabsTrigger>
          <TabsTrigger value="communication">Communication</TabsTrigger>
          <TabsTrigger value="teams">Teams</TabsTrigger>
          <TabsTrigger value="insights">AI Insights</TabsTrigger>
        </TabsList>

        {/* Projects Tab */}
        <TabsContent value="projects" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle>Active Projects</CardTitle>
                <div className="flex gap-2">
                  {(['all', 'asana', 'linear', 'slack'] as const).map(source => (
                    <Button
                      key={source}
                      variant={selectedSource === source ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setSelectedSource(source)}
                    >
                      {source === 'all' ? 'All Sources' : source}
                    </Button>
                  ))}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[400px]">
                <div className="space-y-3">
                  {filteredProjects.map((project, idx) => (
                    <div key={idx} className="border rounded-lg p-4 hover:bg-accent/50 transition-colors">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <h3 className="font-medium">{project.name}</h3>
                            <Badge variant="outline" className="text-xs">
                              {project.source}
                            </Badge>
                            {project.is_overdue && (
                              <Badge variant="destructive" className="text-xs">
                                <AlertCircle className="w-3 h-3 mr-1" />
                                Overdue
                              </Badge>
                            )}
                            {project.risk === 'high' && (
                              <Badge variant="destructive" className="text-xs">
                                High Risk
                              </Badge>
                            )}
                          </div>
                          <div className="flex gap-4 mt-2 text-sm text-muted-foreground">
                            {project.owner && (
                              <span className="flex items-center gap-1">
                                <Users className="w-3 h-3" />
                                {project.owner}
                              </span>
                            )}
                            {project.due_date && (
                              <span className="flex items-center gap-1">
                                <Calendar className="w-3 h-3" />
                                {new Date(project.due_date).toLocaleDateString()}
                              </span>
                            )}
                            <span className="flex items-center gap-1">
                              <Activity className="w-3 h-3" />
                              {project.status}
                            </span>
                          </div>
                        </div>
                        {project.completion && (
                          <div className="w-24">
                            <div className="text-right text-sm font-medium mb-1">
                              {project.completion}%
                            </div>
                            <Progress value={project.completion} className="h-2" />
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Communication Tab */}
        <TabsContent value="communication" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Communication Health</CardTitle>
              <CardDescription>
                Slack channel insights and potential issues
              </CardDescription>
            </CardHeader>
            <CardContent>
              {overview?.communication_issues.length ? (
                <div className="space-y-3">
                  {overview.communication_issues.map((issue, idx) => (
                    <Alert key={idx} className="border-yellow-200 bg-yellow-50">
                      <AlertTriangle className="h-4 w-4 text-yellow-600" />
                      <AlertDescription>
                        <div className="font-medium">
                          {issue.pattern || issue.issue}
                        </div>
                        {issue.channel && (
                          <div className="text-sm mt-1">Channel: {issue.channel}</div>
                        )}
                        {issue.impact && (
                          <div className="text-sm text-muted-foreground mt-1">
                            Impact: {issue.impact}
                          </div>
                        )}
                      </AlertDescription>
                    </Alert>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <CheckCircle className="w-12 h-12 mx-auto mb-3 text-green-500" />
                  <p>No communication issues detected</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Teams Tab */}
        <TabsContent value="teams" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Team Performance Metrics</CardTitle>
              <CardDescription>
                Velocity, cycle time, and health scores across teams
              </CardDescription>
            </CardHeader>
            <CardContent>
              {overview?.departments_scorecard?.length ? (
                <div className="grid grid-cols-2 gap-4">
                  {overview.departments_scorecard.map((team, idx) => (
                    <Card key={idx} className="p-4">
                      <div className="flex justify-between items-start mb-3">
                        <h3 className="font-medium">{team.team}</h3>
                        <Badge variant={team.health_score > 70 ? 'default' : 'destructive'}>
                          Health: {team.health_score}%
                        </Badge>
                      </div>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Velocity</span>
                          <span className="flex items-center gap-1">
                            {team.velocity}
                            {team.velocity_trend === 'increasing' && 
                              <ArrowUpRight className="w-3 h-3 text-green-500" />}
                            {team.velocity_trend === 'decreasing' && 
                              <ArrowDownRight className="w-3 h-3 text-red-500" />}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Cycle Time</span>
                          <span>{team.cycle_time} days</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Blocked Items</span>
                          <span className={team.blocked_items > 0 ? 'text-orange-500' : ''}>
                            {team.blocked_items}
                          </span>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <BarChart3 className="w-12 h-12 mx-auto mb-3" />
                  <p>Team metrics will appear here once Linear is configured</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* AI Insights Tab */}
        <TabsContent value="insights" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="w-5 h-5 text-yellow-500" />
                Sophia's AI Insights
              </CardTitle>
              <CardDescription>
                AI-powered analysis and recommendations
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* System Notes */}
                {overview?.notes.length ? (
                  <div>
                    <h3 className="font-medium mb-2">System Observations</h3>
                    <div className="space-y-2">
                      {overview.notes.map((note, idx) => (
                        <div key={idx} className="flex items-start gap-2">
                          <Star className="w-4 h-4 text-yellow-500 mt-0.5" />
                          <p className="text-sm">{note}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : null}

                {/* Blockages */}
                {overview?.blockages.length ? (
                  <div>
                    <h3 className="font-medium mb-2">Detected Blockages</h3>
                    <div className="space-y-2">
                      {overview.blockages.map((blockage, idx) => (
                        <Alert key={idx} variant="destructive">
                          <AlertCircle className="h-4 w-4" />
                          <AlertDescription>{blockage}</AlertDescription>
                        </Alert>
                      ))}
                    </div>
                  </div>
                ) : null}

                {/* AI Recommendations */}
                <div>
                  <h3 className="font-medium mb-2">Recommended Actions</h3>
                  <div className="space-y-2">
                    {riskDistribution.critical > 0 && (
                      <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                        <p className="text-sm">
                          <strong>Critical:</strong> {riskDistribution.critical} projects need immediate attention
                        </p>
                      </div>
                    )}
                    {overview?.communication_issues.length > 2 && (
                      <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                        <p className="text-sm">
                          <strong>Communication:</strong> Multiple Slack channels showing signs of neglect
                        </p>
                      </div>
                    )}
                    {!overview?.sources.linear.configured && (
                      <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                        <p className="text-sm">
                          <strong>Integration:</strong> Connect Linear to enable development velocity tracking
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Error State */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
    </div>
  );
}
