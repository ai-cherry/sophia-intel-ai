
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { TrendingUp, TrendingDown, AlertTriangle, CheckCircle } from 'lucide-react';

interface StuckAccount {
  account_id: string;
  customer_name: string;
  amount: number;
  days_stuck: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  assigned_team: string;
}

interface TeamMetrics {
  team_name: string;
  completion_rate: number;
  velocity: number;
  burnout_risk: number;
  efficiency_score: number;
}

interface PredictiveAlert {
  account_id: string;
  risk_score: number;
  predicted_stuck_date: string;
  prevention_actions: string[];
}

export const PayReadyDashboard: React.FC = () => {
  const [stuckAccounts, setStuckAccounts] = useState<StuckAccount[]>([]);
  const [teamMetrics, setTeamMetrics] = useState<TeamMetrics[]>([]);
  const [predictions, setPredictions] = useState<PredictiveAlert[]>([]);
  const [insights, setInsights] = useState<string[]>([]);
  const [ws, setWs] = useState<WebSocket | null>(null);

  useEffect(() => {
    // Initialize WebSocket connection
    const websocket = new WebSocket('ws://localhost:8000/ws/pay-ready');

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case 'stuck_account_update':
          setStuckAccounts(data.accounts);
          break;
        case 'team_performance_update':
          setTeamMetrics(data.teams);
          break;
        case 'predictive_alert':
          setPredictions(data.predictions);
          break;
        case 'insights_update':
          setInsights(data.insights);
          break;
      }
    };

    setWs(websocket);

    return () => {
      websocket.close();
    };
  }, []);

  const getSeverityColor = (severity: string) => {
    const colors = {
      low: 'bg-green-100 text-green-800',
      medium: 'bg-yellow-100 text-yellow-800',
      high: 'bg-orange-100 text-orange-800',
      critical: 'bg-red-100 text-red-800'
    };
    return colors[severity as keyof typeof colors] || colors.medium;
  };

  return (
    <div className="p-6 space-y-6">
      {/* Key Insights */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5" />
            Operational Intelligence Insights
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {insights.map((insight, idx) => (
              <Alert key={idx}>
                <AlertDescription>{insight}</AlertDescription>
              </Alert>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Stuck Accounts Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Stuck Accounts Monitor</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {stuckAccounts.slice(0, 5).map((account) => (
                <div key={account.account_id} className="flex justify-between items-center p-3 border rounded">
                  <div>
                    <p className="font-medium">{account.customer_name}</p>
                    <p className="text-sm text-gray-500">
                      ${account.amount.toLocaleString()} • {account.days_stuck} days
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-1 rounded text-xs ${getSeverityColor(account.severity)}`}>
                      {account.severity}
                    </span>
                    <span className="text-xs text-gray-500">{account.assigned_team}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Team Performance */}
        <Card>
          <CardHeader>
            <CardTitle>Team Performance Optimizer</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {teamMetrics.map((team) => (
                <div key={team.team_name} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="font-medium">{team.team_name}</span>
                    <span className="text-sm">
                      {team.completion_rate.toFixed(1)}% complete
                    </span>
                  </div>
                  <Progress value={team.completion_rate} />
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>Velocity: {team.velocity.toFixed(1)}</span>
                    <span className={team.burnout_risk > 0.7 ? 'text-red-500' : ''}>
                      Burnout Risk: {(team.burnout_risk * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Predictive Alerts */}
      <Card>
        <CardHeader>
          <CardTitle>Predictive Analytics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {predictions.slice(0, 6).map((prediction) => (
              <div key={prediction.account_id} className="p-4 border rounded-lg">
                <div className="flex justify-between items-start mb-2">
                  <span className="font-medium text-sm">Account {prediction.account_id}</span>
                  <span className="text-xs px-2 py-1 bg-red-100 text-red-800 rounded">
                    {(prediction.risk_score * 100).toFixed(0)}% risk
                  </span>
                </div>
                <p className="text-xs text-gray-500 mb-2">
                  Predicted stuck: {new Date(prediction.predicted_stuck_date).toLocaleDateString()}
                </p>
                <div className="space-y-1">
                  {prediction.prevention_actions.slice(0, 2).map((action, idx) => (
                    <p key={idx} className="text-xs text-blue-600">• {action}</p>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PayReadyDashboard;
