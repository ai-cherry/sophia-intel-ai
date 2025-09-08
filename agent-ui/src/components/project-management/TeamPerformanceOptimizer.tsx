import React, { useState, useMemo } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Avatar } from '@/components/ui/avatar';
import { Separator } from '@/components/ui/separator';
import {
  Users, TrendingUp, TrendingDown, AlertTriangle, Target,
  User, UserCheck, UserX, Clock, Zap, BarChart3,
  ArrowUp, ArrowDown, Minus, RefreshCw, Settings,
  Award, Star, CheckCircle, XCircle, Loader2,
  Brain, Lightbulb, Scale, Activity, Eye
} from 'lucide-react';

// ==================== TEAM PERFORMANCE TYPES ====================

interface TeamMember {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  role: string;
  department: string;
  hire_date: string;

  // Performance Metrics
  workload_percentage: number;
  performance_score: number;
  completion_rate: number;
  quality_score: number;
  collaboration_score: number;

  // Current Status
  current_tasks: number;
  overdue_tasks: number;
  availability_status: 'available' | 'busy' | 'offline' | 'vacation' | 'sick';
  weekly_hours: number;

  // Skills and Growth
  skills: Skill[];
  skill_gaps: string[];
  learning_progress: LearningProgress[];

  // Performance History
  performance_trend: 'improving' | 'declining' | 'stable';
  recent_achievements: Achievement[];
  areas_for_improvement: string[];
}

interface Skill {
  name: string;
  level: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  confidence: number;
  last_used: string;
  certifications?: string[];
}

interface LearningProgress {
  skill: string;
  progress_percentage: number;
  target_date: string;
  learning_method: string;
}

interface Achievement {
  title: string;
  date: string;
  description: string;
  impact: string;
}

interface TeamOptimizationSuggestion {
  type: 'skill_gap' | 'workload_balance' | 'cross_training' | 'mentorship' | 'role_adjustment';
  priority: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  affected_members: string[];
  expected_impact: string;
  implementation_effort: 'low' | 'medium' | 'high';
  estimated_roi: number;
}

interface TeamMetrics {
  total_members: number;
  avg_performance_score: number;
  avg_workload: number;
  skill_coverage: number;
  collaboration_index: number;
  burnout_risk_members: number;
  high_performers: number;
  capacity_utilization: number;
}

// ==================== TEAM PERFORMANCE OPTIMIZER ====================

const TeamPerformanceOptimizer: React.FC = () => {
  const [selectedMember, setSelectedMember] = useState<TeamMember | null>(null);
  const [viewMode, setViewMode] = useState<'overview' | 'individual' | 'optimization'>('overview');
  const [sortBy, setSortBy] = useState<'performance' | 'workload' | 'name'>('performance');
  const [loading, setLoading] = useState(false);

  // Mock team data - would come from API
  const mockTeamMembers: TeamMember[] = [
    {
      id: 'tm-001',
      name: 'Sarah Chen',
      email: 'sarah.chen@company.com',
      role: 'Senior Developer',
      department: 'Engineering',
      hire_date: '2022-03-15',
      workload_percentage: 95,
      performance_score: 92,
      completion_rate: 87,
      quality_score: 95,
      collaboration_score: 88,
      current_tasks: 8,
      overdue_tasks: 1,
      availability_status: 'busy',
      weekly_hours: 42,
      skills: [
        { name: 'Python', level: 'expert', confidence: 95, last_used: '2024-02-20' },
        { name: 'React', level: 'advanced', confidence: 88, last_used: '2024-02-19' },
        { name: 'DevOps', level: 'intermediate', confidence: 75, last_used: '2024-02-15' }
      ],
      skill_gaps: ['Machine Learning', 'Mobile Development'],
      learning_progress: [
        { skill: 'Machine Learning', progress_percentage: 60, target_date: '2024-04-01', learning_method: 'Online Course' }
      ],
      performance_trend: 'stable',
      recent_achievements: [
        { title: 'API Performance Optimization', date: '2024-02-10', description: 'Reduced API response time by 40%', impact: 'High' }
      ],
      areas_for_improvement: ['Time Management', 'Documentation']
    },
    {
      id: 'tm-002',
      name: 'Mike Rodriguez',
      email: 'mike.rodriguez@company.com',
      role: 'Frontend Developer',
      department: 'Engineering',
      hire_date: '2023-01-20',
      workload_percentage: 60,
      performance_score: 78,
      completion_rate: 62,
      quality_score: 82,
      collaboration_score: 91,
      current_tasks: 5,
      overdue_tasks: 2,
      availability_status: 'available',
      weekly_hours: 38,
      skills: [
        { name: 'React', level: 'advanced', confidence: 85, last_used: '2024-02-20' },
        { name: 'TypeScript', level: 'intermediate', confidence: 70, last_used: '2024-02-18' },
        { name: 'CSS', level: 'expert', confidence: 92, last_used: '2024-02-20' }
      ],
      skill_gaps: ['Backend Development', 'Testing'],
      learning_progress: [
        { skill: 'Node.js', progress_percentage: 30, target_date: '2024-05-01', learning_method: 'Mentorship' }
      ],
      performance_trend: 'improving',
      recent_achievements: [
        { title: 'UI Component Library', date: '2024-01-25', description: 'Built reusable component system', impact: 'Medium' }
      ],
      areas_for_improvement: ['Backend Integration', 'Performance Optimization']
    },
    {
      id: 'tm-003',
      name: 'Alex Thompson',
      email: 'alex.thompson@company.com',
      role: 'Product Manager',
      department: 'Product',
      hire_date: '2021-08-10',
      workload_percentage: 85,
      performance_score: 89,
      completion_rate: 91,
      quality_score: 87,
      collaboration_score: 95,
      current_tasks: 12,
      overdue_tasks: 0,
      availability_status: 'available',
      weekly_hours: 45,
      skills: [
        { name: 'Product Strategy', level: 'expert', confidence: 93, last_used: '2024-02-20' },
        { name: 'Data Analysis', level: 'advanced', confidence: 82, last_used: '2024-02-19' },
        { name: 'User Research', level: 'advanced', confidence: 88, last_used: '2024-02-17' }
      ],
      skill_gaps: ['Technical Architecture', 'AI/ML Fundamentals'],
      learning_progress: [
        { skill: 'Technical Architecture', progress_percentage: 45, target_date: '2024-06-01', learning_method: 'Workshop' }
      ],
      performance_trend: 'stable',
      recent_achievements: [
        { title: 'User Engagement Increase', date: '2024-02-05', description: 'Led initiative that increased user engagement by 25%', impact: 'High' }
      ],
      areas_for_improvement: ['Technical Knowledge', 'Cross-team Communication']
    }
  ];

  const mockOptimizationSuggestions: TeamOptimizationSuggestion[] = [
    {
      type: 'workload_balance',
      priority: 'high',
      title: 'Redistribute Sarah\'s Workload',
      description: 'Sarah Chen is at 95% capacity with declining completion rates. Redistribute 2-3 tasks to Mike Rodriguez who is at 60% capacity.',
      affected_members: ['tm-001', 'tm-002'],
      expected_impact: 'Improve team velocity by 15% and reduce burnout risk',
      implementation_effort: 'low',
      estimated_roi: 85
    },
    {
      type: 'cross_training',
      priority: 'medium',
      title: 'Cross-train Mike on Backend Development',
      description: 'Mike shows interest in backend development and has 40% available capacity. Cross-training would improve team flexibility.',
      affected_members: ['tm-002'],
      expected_impact: 'Increase team versatility and reduce single points of failure',
      implementation_effort: 'medium',
      estimated_roi: 120
    },
    {
      type: 'skill_gap',
      priority: 'critical',
      title: 'Address Testing Skills Gap',
      description: 'Team lacks automated testing expertise. Quality scores dropping across projects.',
      affected_members: ['tm-001', 'tm-002'],
      expected_impact: 'Improve code quality scores by 20% and reduce bug reports',
      implementation_effort: 'high',
      estimated_roi: 200
    }
  ];

  // Computed metrics
  const teamMetrics: TeamMetrics = useMemo(() => {
    const totalMembers = mockTeamMembers.length;
    const avgPerformance = mockTeamMembers.reduce((acc, member) => acc + member.performance_score, 0) / totalMembers;
    const avgWorkload = mockTeamMembers.reduce((acc, member) => acc + member.workload_percentage, 0) / totalMembers;
    const burnoutRisk = mockTeamMembers.filter(member => member.workload_percentage > 90).length;
    const highPerformers = mockTeamMembers.filter(member => member.performance_score > 85).length;

    return {
      total_members: totalMembers,
      avg_performance_score: Math.round(avgPerformance),
      avg_workload: Math.round(avgWorkload),
      skill_coverage: 78, // Would be calculated based on skill analysis
      collaboration_index: 91, // Would be calculated from collaboration scores
      burnout_risk_members: burnoutRisk,
      high_performers: highPerformers,
      capacity_utilization: Math.round(avgWorkload)
    };
  }, [mockTeamMembers]);

  const sortedMembers = useMemo(() => {
    return [...mockTeamMembers].sort((a, b) => {
      switch (sortBy) {
        case 'performance':
          return b.performance_score - a.performance_score;
        case 'workload':
          return b.workload_percentage - a.workload_percentage;
        case 'name':
          return a.name.localeCompare(b.name);
        default:
          return 0;
      }
    });
  }, [mockTeamMembers, sortBy]);

  // UI Helper Functions
  const getPerformanceTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving': return <TrendingUp className="w-4 h-4 text-green-500" />;
      case 'declining': return <TrendingDown className="w-4 h-4 text-red-500" />;
      default: return <Minus className="w-4 h-4 text-gray-500" />;
    }
  };

  const getWorkloadColor = (workload: number) => {
    if (workload > 90) return 'text-red-600';
    if (workload > 75) return 'text-yellow-600';
    return 'text-green-600';
  };

  const getSkillLevelBadge = (level: string) => {
    const variants = {
      'beginner': 'secondary',
      'intermediate': 'outline',
      'advanced': 'default',
      'expert': 'default'
    };
    return variants[level as keyof typeof variants] || 'secondary';
  };

  const getPriorityColor = (priority: string) => {
    const colors = {
      'low': 'border-green-200 bg-green-50 text-green-800',
      'medium': 'border-yellow-200 bg-yellow-50 text-yellow-800',
      'high': 'border-orange-200 bg-orange-50 text-orange-800',
      'critical': 'border-red-200 bg-red-50 text-red-800'
    };
    return colors[priority as keyof typeof colors] || '';
  };

  return (
    <div className="space-y-6">
      {/* ==================== TEAM OVERVIEW METRICS ==================== */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center">
              <Users className="w-4 h-4 mr-2" />
              Team Size
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{teamMetrics.total_members}</div>
            <div className="text-xs text-gray-500">Active members</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center">
              <Target className="w-4 h-4 mr-2" />
              Avg Performance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${teamMetrics.avg_performance_score > 80 ? 'text-green-600' : 'text-yellow-600'}`}>
              {teamMetrics.avg_performance_score}%
            </div>
            <Progress value={teamMetrics.avg_performance_score} className="mt-2 h-1" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center">
              <Activity className="w-4 h-4 mr-2" />
              Capacity Utilization
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getWorkloadColor(teamMetrics.capacity_utilization)}`}>
              {teamMetrics.capacity_utilization}%
            </div>
            <div className="text-xs text-gray-500">{teamMetrics.burnout_risk_members} at risk of burnout</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center">
              <Award className="w-4 h-4 mr-2" />
              High Performers
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{teamMetrics.high_performers}</div>
            <div className="text-xs text-gray-500">Score > 85%</div>
          </CardContent>
        </Card>
      </div>

      {/* ==================== VIEW MODE CONTROLS ==================== */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Button
            variant={viewMode === 'overview' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setViewMode('overview')}
          >
            <Eye className="w-4 h-4 mr-2" />
            Overview
          </Button>
          <Button
            variant={viewMode === 'individual' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setViewMode('individual')}
          >
            <User className="w-4 h-4 mr-2" />
            Individual
          </Button>
          <Button
            variant={viewMode === 'optimization' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setViewMode('optimization')}
          >
            <Lightbulb className="w-4 h-4 mr-2" />
            Optimization
          </Button>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-500">Sort by:</span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="text-sm border rounded px-2 py-1"
          >
            <option value="performance">Performance</option>
            <option value="workload">Workload</option>
            <option value="name">Name</option>
          </select>
        </div>
      </div>

      {/* ==================== TEAM MEMBER GRID ==================== */}
      {viewMode === 'individual' && (
        <div className="grid grid-cols-2 gap-4">
          {sortedMembers.map((member) => (
            <Card
              key={member.id}
              className={`cursor-pointer transition-all hover:shadow-lg ${
                selectedMember?.id === member.id ? 'ring-2 ring-blue-500' : ''
              }`}
              onClick={() => setSelectedMember(member)}
            >
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-medium">
                      {member.name.charAt(0)}
                    </div>
                    <div>
                      <CardTitle className="text-base">{member.name}</CardTitle>
                      <CardDescription>{member.role}</CardDescription>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {getPerformanceTrendIcon(member.performance_trend)}
                    <Badge variant={member.availability_status === 'available' ? 'default' : 'secondary'}>
                      {member.availability_status}
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {/* Performance Score */}
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Performance Score</span>
                      <span className="font-medium">{member.performance_score}%</span>
                    </div>
                    <Progress value={member.performance_score} className="h-2" />
                  </div>

                  {/* Workload */}
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Workload</span>
                      <span className={`font-medium ${getWorkloadColor(member.workload_percentage)}`}>
                        {member.workload_percentage}%
                      </span>
                    </div>
                    <Progress
                      value={member.workload_percentage}
                      className="h-2"
                      // Add color variant based on workload
                    />
                  </div>

                  {/* Current Tasks */}
                  <div className="grid grid-cols-3 gap-2 text-sm">
                    <div className="text-center">
                      <div className="font-medium">{member.current_tasks}</div>
                      <div className="text-gray-500 text-xs">Tasks</div>
                    </div>
                    <div className="text-center">
                      <div className={`font-medium ${member.overdue_tasks > 0 ? 'text-red-600' : 'text-gray-600'}`}>
                        {member.overdue_tasks}
                      </div>
                      <div className="text-gray-500 text-xs">Overdue</div>
                    </div>
                    <div className="text-center">
                      <div className="font-medium">{member.completion_rate}%</div>
                      <div className="text-gray-500 text-xs">Complete</div>
                    </div>
                  </div>

                  {/* Top Skills */}
                  <div>
                    <div className="text-sm font-medium mb-2">Top Skills</div>
                    <div className="flex flex-wrap gap-1">
                      {member.skills.slice(0, 3).map((skill) => (
                        <Badge key={skill.name} variant={getSkillLevelBadge(skill.level)} className="text-xs">
                          {skill.name}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  {/* Alerts */}
                  {member.workload_percentage > 90 && (
                    <Alert className="border-red-200 bg-red-50">
                      <AlertTriangle className="h-4 w-4 text-red-600" />
                      <AlertDescription className="text-red-800 text-xs">
                        High workload - consider redistribution
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* ==================== OPTIMIZATION SUGGESTIONS ==================== */}
      {viewMode === 'optimization' && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Brain className="w-5 h-5 text-purple-600" />
                <span>AI-Powered Team Optimization Suggestions</span>
              </CardTitle>
              <CardDescription>
                Based on performance patterns, workload analysis, and skill mapping
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {mockOptimizationSuggestions.map((suggestion, idx) => (
                  <div key={idx} className={`border rounded-lg p-4 ${getPriorityColor(suggestion.priority)}`}>
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <div className="flex items-center space-x-2">
                          <Badge variant="outline" className={`${getPriorityColor(suggestion.priority)} border-current`}>
                            {suggestion.priority.toUpperCase()} PRIORITY
                          </Badge>
                          <span className="font-medium capitalize">{suggestion.type.replace('_', ' ')}</span>
                        </div>
                        <h4 className="font-semibold mt-1">{suggestion.title}</h4>
                      </div>
                      <div className="text-right text-sm">
                        <div className="font-medium text-green-600">+{suggestion.estimated_roi}% ROI</div>
                        <div className="text-gray-500">{suggestion.implementation_effort} effort</div>
                      </div>
                    </div>

                    <p className="text-sm mb-3">{suggestion.description}</p>

                    <div className="flex items-center justify-between">
                      <div className="text-sm">
                        <span className="text-gray-600">Impact: </span>
                        <span>{suggestion.expected_impact}</span>
                      </div>
                      <div className="flex space-x-2">
                        <Button size="sm" variant="outline">
                          View Details
                        </Button>
                        <Button size="sm">
                          Implement
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* ==================== OVERVIEW CHARTS AND INSIGHTS ==================== */}
      {viewMode === 'overview' && (
        <div className="grid grid-cols-2 gap-6">
          {/* Performance Distribution */}
          <Card>
            <CardHeader>
              <CardTitle>Performance Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {['Expert (90-100%)', 'Advanced (80-89%)', 'Intermediate (70-79%)', 'Needs Support (<70%)'].map((category, idx) => {
                  const ranges = [[90, 100], [80, 89], [70, 79], [0, 69]];
                  const [min, max] = ranges[idx];
                  const count = mockTeamMembers.filter(m => m.performance_score >= min && m.performance_score <= max).length;
                  const percentage = (count / mockTeamMembers.length) * 100;

                  return (
                    <div key={category} className="flex items-center justify-between">
                      <span className="text-sm">{category}</span>
                      <div className="flex items-center space-x-2">
                        <Progress value={percentage} className="w-24 h-2" />
                        <span className="text-sm font-medium">{count}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Workload Balance */}
          <Card>
            <CardHeader>
              <CardTitle>Workload Balance</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {mockTeamMembers.map((member) => (
                  <div key={member.id} className="flex items-center justify-between">
                    <span className="text-sm">{member.name}</span>
                    <div className="flex items-center space-x-2">
                      <Progress value={member.workload_percentage} className="w-24 h-2" />
                      <span className={`text-sm font-medium ${getWorkloadColor(member.workload_percentage)}`}>
                        {member.workload_percentage}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default TeamPerformanceOptimizer;