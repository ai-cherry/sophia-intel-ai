import React, { useState, useEffect } from 'react';
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
import { Separator } from '@/components/ui/separator';
import {
  Menu, Search, Bell, Settings, Plus, Filter,
  TrendingUp, TrendingDown, AlertTriangle, CheckCircle,
  Clock, Users, Target, Activity, BarChart3,
  ChevronRight, ChevronDown, Eye, EyeOff,
  Smartphone, Tablet, Monitor, RefreshCw,
  MessageCircle, Calendar, MapPin, Zap
} from 'lucide-react';

// ==================== MOBILE-OPTIMIZED COMPONENTS ====================

interface MobileMetric {
  id: string;
  label: string;
  value: string | number;
  change?: number;
  trend?: 'up' | 'down' | 'stable';
  color?: 'green' | 'red' | 'yellow' | 'blue' | 'gray';
  icon?: React.ReactElement;
}

interface QuickAction {
  id: string;
  label: string;
  icon: React.ReactElement;
  action: () => void;
  badge?: string;
  color?: string;
}

interface MobileAlert {
  id: string;
  type: 'urgent' | 'warning' | 'info';
  title: string;
  message: string;
  timestamp: string;
  actionable: boolean;
}

// ==================== MOBILE PROJECT DASHBOARD ====================

const MobileProjectDashboard: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [activeSection, setActiveSection] = useState('overview');
  const [showNotifications, setShowNotifications] = useState(false);
  const [isOffline, setIsOffline] = useState(false);

  // Detect device type and orientation
  const [deviceType, setDeviceType] = useState<'mobile' | 'tablet' | 'desktop'>('mobile');
  const [isLandscape, setIsLandscape] = useState(false);

  useEffect(() => {
    const checkDeviceType = () => {
      const width = window.innerWidth;
      if (width < 768) {
        setDeviceType('mobile');
      } else if (width < 1024) {
        setDeviceType('tablet');
      } else {
        setDeviceType('desktop');
      }
      setIsLandscape(window.innerWidth > window.innerHeight);
    };

    const checkOnlineStatus = () => {
      setIsOffline(!navigator.onLine);
    };

    checkDeviceType();
    checkOnlineStatus();

    window.addEventListener('resize', checkDeviceType);
    window.addEventListener('online', checkOnlineStatus);
    window.addEventListener('offline', checkOnlineStatus);

    return () => {
      window.removeEventListener('resize', checkDeviceType);
      window.removeEventListener('online', checkOnlineStatus);
      window.removeEventListener('offline', checkOnlineStatus);
    };
  }, []);

  // Mobile-optimized metrics
  const mobileMetrics: MobileMetric[] = [
    {
      id: 'projects',
      label: 'Active Projects',
      value: 12,
      change: 2,
      trend: 'up',
      color: 'blue',
      icon: <Target className="w-4 h-4" />
    },
    {
      id: 'at-risk',
      label: 'At Risk',
      value: 3,
      change: -1,
      trend: 'down',
      color: 'red',
      icon: <AlertTriangle className="w-4 h-4" />
    },
    {
      id: 'completion',
      label: 'Completion',
      value: '73%',
      change: 5,
      trend: 'up',
      color: 'green',
      icon: <CheckCircle className="w-4 h-4" />
    },
    {
      id: 'team',
      label: 'Team Health',
      value: '85%',
      change: 0,
      trend: 'stable',
      color: 'yellow',
      icon: <Users className="w-4 h-4" />
    }
  ];

  const quickActions: QuickAction[] = [
    {
      id: 'new-task',
      label: 'Add Task',
      icon: <Plus className="w-4 h-4" />,
      action: () => {},
      color: 'blue'
    },
    {
      id: 'team-check',
      label: 'Team Status',
      icon: <Users className="w-4 h-4" />,
      action: () => {},
      badge: '3',
      color: 'green'
    },
    {
      id: 'alerts',
      label: 'Alerts',
      icon: <Bell className="w-4 h-4" />,
      action: () => setShowNotifications(true),
      badge: '5',
      color: 'red'
    },
    {
      id: 'analytics',
      label: 'Analytics',
      icon: <BarChart3 className="w-4 h-4" />,
      action: () => {},
      color: 'purple'
    }
  ];

  const mobileAlerts: MobileAlert[] = [
    {
      id: 'alert-1',
      type: 'urgent',
      title: 'Project Deadline Risk',
      message: 'Payment Processing project is 7 days behind schedule',
      timestamp: '5m ago',
      actionable: true
    },
    {
      id: 'alert-2',
      type: 'warning',
      title: 'Team Capacity',
      message: 'Sarah Chen at 95% workload - redistribution recommended',
      timestamp: '15m ago',
      actionable: true
    },
    {
      id: 'alert-3',
      type: 'info',
      title: 'Integration Update',
      message: 'Asana sync completed - 47 tasks updated',
      timestamp: '1h ago',
      actionable: false
    }
  ];

  // UI Helper Functions
  const getMetricColor = (color?: string) => {
    const colors = {
      green: 'text-green-600 bg-green-50',
      red: 'text-red-600 bg-red-50',
      yellow: 'text-yellow-600 bg-yellow-50',
      blue: 'text-blue-600 bg-blue-50',
      purple: 'text-purple-600 bg-purple-50',
      gray: 'text-gray-600 bg-gray-50'
    };
    return colors[color as keyof typeof colors] || colors.gray;
  };

  const getTrendIcon = (trend?: string) => {
    switch (trend) {
      case 'up': return <TrendingUp className="w-3 h-3 text-green-500" />;
      case 'down': return <TrendingDown className="w-3 h-3 text-red-500" />;
      default: return null;
    }
  };

  const getAlertTypeColor = (type: string) => {
    const colors = {
      urgent: 'border-l-red-500 bg-red-50',
      warning: 'border-l-yellow-500 bg-yellow-50',
      info: 'border-l-blue-500 bg-blue-50'
    };
    return colors[type as keyof typeof colors] || colors.info;
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* ==================== MOBILE HEADER ==================== */}
      <div className="sticky top-0 z-50 bg-white dark:bg-gray-800 border-b shadow-sm">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center space-x-3">
            <Button variant="ghost" size="sm" onClick={() => setCollapsed(!collapsed)}>
              <Menu className="w-5 h-5" />
            </Button>
            <div className="flex items-center space-x-2">
              <Target className="w-6 h-6 text-blue-600" />
              <div>
                <h1 className="font-semibold text-sm">Project Center</h1>
                {isOffline && (
                  <p className="text-xs text-red-600">Offline Mode</p>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {/* Device indicator */}
            <div className="text-gray-400">
              {deviceType === 'mobile' && <Smartphone className="w-4 h-4" />}
              {deviceType === 'tablet' && <Tablet className="w-4 h-4" />}
              {deviceType === 'desktop' && <Monitor className="w-4 h-4" />}
            </div>

            <Button variant="ghost" size="sm">
              <Search className="w-5 h-5" />
            </Button>

            <Button variant="ghost" size="sm" onClick={() => setShowNotifications(true)}>
              <div className="relative">
                <Bell className="w-5 h-5" />
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full flex items-center justify-center">
                  <span className="text-xs text-white font-bold">3</span>
                </div>
              </div>
            </Button>
          </div>
        </div>

        {/* Connection Status Bar */}
        {isOffline && (
          <div className="bg-red-100 dark:bg-red-900 px-4 py-1">
            <p className="text-xs text-red-800 dark:text-red-200">
              Working offline - changes will sync when connection is restored
            </p>
          </div>
        )}
      </div>

      {/* ==================== METRICS OVERVIEW (ALWAYS VISIBLE) ==================== */}
      <div className="px-4 py-4">
        <div className={`grid gap-3 ${deviceType === 'mobile' ? 'grid-cols-2' : deviceType === 'tablet' ? 'grid-cols-4' : 'grid-cols-4'}`}>
          {mobileMetrics.map((metric) => (
            <Card key={metric.id} className="p-3">
              <div className="flex items-center justify-between mb-2">
                <div className={`p-2 rounded-lg ${getMetricColor(metric.color)}`}>
                  {metric.icon}
                </div>
                {getTrendIcon(metric.trend)}
              </div>
              <div className="space-y-1">
                <p className="text-xl font-bold">{metric.value}</p>
                <p className="text-xs text-gray-600 dark:text-gray-400">{metric.label}</p>
                {metric.change !== undefined && (
                  <div className="flex items-center space-x-1">
                    <span className={`text-xs ${metric.trend === 'up' ? 'text-green-600' : metric.trend === 'down' ? 'text-red-600' : 'text-gray-600'}`}>
                      {metric.change > 0 ? '+' : ''}{metric.change}
                    </span>
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      </div>

      {/* ==================== QUICK ACTIONS (HORIZONTAL SCROLL ON MOBILE) ==================== */}
      <div className="px-4 pb-4">
        <Card className="p-4">
          <h3 className="font-medium text-sm mb-3">Quick Actions</h3>
          <div className="flex space-x-3 overflow-x-auto pb-2">
            {quickActions.map((action) => (
              <Button
                key={action.id}
                variant="outline"
                className="flex-shrink-0 relative"
                onClick={action.action}
              >
                <div className="flex items-center space-x-2">
                  {action.icon}
                  <span className="text-sm">{action.label}</span>
                </div>
                {action.badge && (
                  <div className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full flex items-center justify-center">
                    <span className="text-xs text-white font-bold">{action.badge}</span>
                  </div>
                )}
              </Button>
            ))}
          </div>
        </Card>
      </div>

      {/* ==================== EXPANDABLE CONTENT SECTIONS ==================== */}
      <div className="px-4 space-y-4">
        {/* Critical Alerts */}
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center">
                <AlertTriangle className="w-4 h-4 mr-2 text-red-500" />
                Critical Alerts
              </CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setActiveSection(activeSection === 'alerts' ? '' : 'alerts')}
              >
                {activeSection === 'alerts' ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              </Button>
            </div>
          </CardHeader>
          {activeSection === 'alerts' && (
            <CardContent className="pt-0">
              <div className="space-y-3">
                {mobileAlerts.filter(alert => alert.type === 'urgent' || alert.type === 'warning').slice(0, 3).map((alert) => (
                  <div key={alert.id} className={`border-l-4 p-3 rounded-r ${getAlertTypeColor(alert.type)}`}>
                    <div className="flex items-start justify-between mb-1">
                      <h5 className="font-medium text-sm">{alert.title}</h5>
                      <span className="text-xs text-gray-500">{alert.timestamp}</span>
                    </div>
                    <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">{alert.message}</p>
                    {alert.actionable && (
                      <Button size="sm" variant="outline" className="text-xs">
                        Take Action
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          )}
        </Card>

        {/* Team Status */}
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center">
                <Users className="w-4 h-4 mr-2 text-blue-500" />
                Team Status
              </CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setActiveSection(activeSection === 'team' ? '' : 'team')}
              >
                {activeSection === 'team' ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              </Button>
            </div>
          </CardHeader>
          {activeSection === 'team' && (
            <CardContent className="pt-0">
              <div className="space-y-3">
                {[
                  { name: 'Sarah Chen', status: 'busy', workload: 95, performance: 92 },
                  { name: 'Mike Rodriguez', status: 'available', workload: 60, performance: 78 },
                  { name: 'Alex Thompson', status: 'available', workload: 85, performance: 89 }
                ].map((member, idx) => (
                  <div key={idx} className="flex items-center justify-between p-2 border rounded">
                    <div className="flex items-center space-x-2">
                      <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
                        {member.name.charAt(0)}
                      </div>
                      <div>
                        <p className="font-medium text-sm">{member.name}</p>
                        <Badge variant={member.status === 'available' ? 'default' : 'secondary'} className="text-xs">
                          {member.status}
                        </Badge>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className={`text-sm font-medium ${member.workload > 90 ? 'text-red-600' : 'text-gray-600'}`}>
                        {member.workload}%
                      </p>
                      <p className="text-xs text-gray-500">workload</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          )}
        </Card>

        {/* Recent Activity */}
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center">
                <Activity className="w-4 h-4 mr-2 text-green-500" />
                Recent Activity
              </CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setActiveSection(activeSection === 'activity' ? '' : 'activity')}
              >
                {activeSection === 'activity' ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              </Button>
            </div>
          </CardHeader>
          {activeSection === 'activity' && (
            <CardContent className="pt-0">
              <div className="space-y-3">
                {[
                  { action: 'Task completed', project: 'Payment Processing', time: '5m ago', type: 'success' },
                  { action: 'Risk identified', project: 'API Integration', time: '15m ago', type: 'warning' },
                  { action: 'Team member assigned', project: 'Mobile App', time: '1h ago', type: 'info' }
                ].map((activity, idx) => (
                  <div key={idx} className="flex items-start space-x-3">
                    <div className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${
                      activity.type === 'success' ? 'bg-green-500' :
                      activity.type === 'warning' ? 'bg-yellow-500' :
                      'bg-blue-500'
                    }`} />
                    <div className="flex-1">
                      <p className="text-sm font-medium">{activity.action}</p>
                      <p className="text-xs text-gray-600">{activity.project}</p>
                      <p className="text-xs text-gray-500">{activity.time}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          )}
        </Card>
      </div>

      {/* ==================== FLOATING ACTION BUTTON (MOBILE ONLY) ==================== */}
      {deviceType === 'mobile' && (
        <div className="fixed bottom-6 right-6 z-40">
          <Button className="w-14 h-14 rounded-full shadow-lg">
            <Plus className="w-6 h-6" />
          </Button>
        </div>
      )}

      {/* ==================== BOTTOM SAFE AREA (MOBILE) ==================== */}
      {deviceType === 'mobile' && (
        <div className="h-6 bg-transparent" />
      )}

      {/* ==================== NOTIFICATION OVERLAY ==================== */}
      {showNotifications && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50" onClick={() => setShowNotifications(false)}>
          <div className="absolute top-0 right-0 w-full max-w-sm h-full bg-white dark:bg-gray-800 shadow-xl">
            <div className="p-4 border-b">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold">Notifications</h3>
                <Button variant="ghost" size="sm" onClick={() => setShowNotifications(false)}>
                  ×
                </Button>
              </div>
            </div>
            <div className="p-4 space-y-4 overflow-y-auto">
              {mobileAlerts.map((alert) => (
                <div key={alert.id} className={`p-3 rounded-lg border-l-4 ${getAlertTypeColor(alert.type)}`}>
                  <div className="flex items-start justify-between mb-1">
                    <h5 className="font-medium text-sm">{alert.title}</h5>
                    <span className="text-xs text-gray-500">{alert.timestamp}</span>
                  </div>
                  <p className="text-sm text-gray-700 dark:text-gray-300">{alert.message}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MobileProjectDashboard;
