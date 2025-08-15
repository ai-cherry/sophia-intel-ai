import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Textarea } from '@/components/ui/textarea.jsx'
import { Label } from '@/components/ui/label.jsx'
import { Activity, Brain, Database, GitBranch, Server, Zap, CheckCircle, XCircle, AlertCircle, Clock } from 'lucide-react'
import './App.css'

// API base URL - adjust for your backend
const API_BASE = '/api'

function Navigation() {
  const location = useLocation()
  
  const navItems = [
    { path: '/', label: 'Overview', icon: Activity },
    { path: '/swarm', label: 'Swarm', icon: Brain },
    { path: '/pipelines', label: 'Pipelines', icon: Database },
    { path: '/models', label: 'Models', icon: Zap }
  ]

  return (
    <nav className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center space-x-4">
            <Link to="/" className="flex items-center space-x-2">
              <Brain className="h-6 w-6" />
              <span className="font-bold text-xl">Sophia Intel</span>
            </Link>
          </div>
          <div className="flex items-center space-x-6">
            {navItems.map((item) => {
              const Icon = item.icon
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    location.pathname === item.path
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.label}</span>
                </Link>
              )
            })}
          </div>
        </div>
      </div>
    </nav>
  )
}

function StatusBadge({ status, children }) {
  const variants = {
    healthy: { variant: 'default', icon: CheckCircle, className: 'bg-green-500 hover:bg-green-600' },
    degraded: { variant: 'secondary', icon: AlertCircle, className: 'bg-yellow-500 hover:bg-yellow-600' },
    unhealthy: { variant: 'destructive', icon: XCircle, className: 'bg-red-500 hover:bg-red-600' },
    blocked: { variant: 'outline', icon: XCircle, className: 'border-red-500 text-red-500' },
    unknown: { variant: 'outline', icon: AlertCircle, className: 'border-gray-500 text-gray-500' }
  }
  
  const config = variants[status] || variants.unknown
  const Icon = config.icon
  
  return (
    <Badge variant={config.variant} className={config.className}>
      <Icon className="h-3 w-3 mr-1" />
      {children}
    </Badge>
  )
}

function OverviewPage() {
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchHealth()
  }, [])

  const fetchHealth = async () => {
    try {
      const response = await fetch(`${API_BASE}/health`)
      const data = await response.json()
      setHealth(data)
    } catch (error) {
      console.error('Failed to fetch health:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </div>
    )
  }

  const components = health?.components || {}
  const healthScore = health?.overall_health_score || 0

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">System Overview</h1>
        <p className="text-muted-foreground">Real-time health monitoring for Sophia Intel platform</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Overall Health</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{healthScore.toFixed(1)}%</div>
            <div className="w-full bg-muted rounded-full h-2 mt-2">
              <div 
                className="bg-primary h-2 rounded-full transition-all duration-300" 
                style={{ width: `${healthScore}%` }}
              ></div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Response Time</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{health?.total_response_time_ms || 0}ms</div>
            <p className="text-xs text-muted-foreground">Total check duration</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Last Updated</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {health?.timestamp ? new Date(health.timestamp).toLocaleTimeString() : 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground">System check time</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {Object.entries(components).map(([name, status]) => (
          <Card key={name}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="capitalize">{name.replace('_', ' ')}</CardTitle>
                <StatusBadge status={status.status}>
                  {status.status}
                </StatusBadge>
              </div>
            </CardHeader>
            <CardContent>
              {status.error && (
                <p className="text-sm text-destructive mb-2">{status.error}</p>
              )}
              {status.response_time_ms !== undefined && (
                <p className="text-sm text-muted-foreground">
                  Response: {status.response_time_ms}ms
                </p>
              )}
              {status.collections !== undefined && (
                <p className="text-sm text-muted-foreground">
                  Collections: {status.collections}
                </p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="mt-8 flex justify-center">
        <Button onClick={fetchHealth} variant="outline">
          <Activity className="h-4 w-4 mr-2" />
          Refresh Health Check
        </Button>
      </div>
    </div>
  )
}

function SwarmPage() {
  const [jobs, setJobs] = useState([])
  const [currentJob, setCurrentJob] = useState(null)
  const [formData, setFormData] = useState({ repo: '', goal: '', constraints: '' })
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)

    try {
      const response = await fetch(`${API_BASE}/swarm/plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })
      
      const result = await response.json()
      if (response.ok) {
        setCurrentJob(result.job_id)
        setJobs(prev => [...prev, result])
        // Start polling for status
        pollJobStatus(result.job_id)
      } else {
        alert(`Error: ${result.error}`)
      }
    } catch (error) {
      alert(`Error: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  const pollJobStatus = async (jobId) => {
    const poll = async () => {
      try {
        const response = await fetch(`${API_BASE}/swarm/status/${jobId}`)
        const status = await response.json()
        
        setJobs(prev => prev.map(job => 
          job.job_id === jobId ? { ...job, ...status } : job
        ))

        if (status.status === 'planned') {
          // Auto-implement after planning
          setTimeout(() => implementJob(jobId), 1000)
        } else if (!['completed', 'failed'].includes(status.status)) {
          setTimeout(poll, 2000)
        }
      } catch (error) {
        console.error('Polling error:', error)
      }
    }
    poll()
  }

  const implementJob = async (jobId) => {
    try {
      const response = await fetch(`${API_BASE}/swarm/implement`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_id: jobId })
      })
      
      if (response.ok) {
        pollJobStatus(jobId)
      }
    } catch (error) {
      console.error('Implementation error:', error)
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Coding Swarm</h1>
        <p className="text-muted-foreground">AI-powered code generation with Planner → Coder → Reviewer → Integrator</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Card>
          <CardHeader>
            <CardTitle>Start New Job</CardTitle>
            <CardDescription>Define a coding task for the swarm to execute</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label htmlFor="repo">Repository</Label>
                <Input
                  id="repo"
                  placeholder="owner/repo-name"
                  value={formData.repo}
                  onChange={(e) => setFormData(prev => ({ ...prev, repo: e.target.value }))}
                  required
                />
              </div>
              <div>
                <Label htmlFor="goal">Goal</Label>
                <Textarea
                  id="goal"
                  placeholder="Describe what you want the swarm to implement..."
                  value={formData.goal}
                  onChange={(e) => setFormData(prev => ({ ...prev, goal: e.target.value }))}
                  required
                />
              </div>
              <div>
                <Label htmlFor="constraints">Constraints (optional)</Label>
                <Textarea
                  id="constraints"
                  placeholder="Any specific requirements or limitations..."
                  value={formData.constraints}
                  onChange={(e) => setFormData(prev => ({ ...prev, constraints: e.target.value }))}
                />
              </div>
              <Button type="submit" disabled={loading} className="w-full">
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Starting Swarm...
                  </>
                ) : (
                  <>
                    <Brain className="h-4 w-4 mr-2" />
                    Start Swarm Job
                  </>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Active Jobs</CardTitle>
            <CardDescription>Real-time swarm execution status</CardDescription>
          </CardHeader>
          <CardContent>
            {jobs.length === 0 ? (
              <p className="text-muted-foreground text-center py-8">No active jobs</p>
            ) : (
              <div className="space-y-4">
                {jobs.map((job) => (
                  <div key={job.job_id} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">{job.repo}</span>
                      <StatusBadge status={job.status === 'completed' ? 'healthy' : job.status === 'failed' ? 'unhealthy' : 'degraded'}>
                        {job.status}
                      </StatusBadge>
                    </div>
                    <p className="text-sm text-muted-foreground mb-3">{job.goal}</p>
                    
                    {job.agents && (
                      <div className="grid grid-cols-4 gap-2">
                        {Object.entries(job.agents).map(([agent, status]) => (
                          <div key={agent} className="text-center">
                            <div className={`w-8 h-8 rounded-full mx-auto mb-1 flex items-center justify-center ${
                              status.status === 'completed' ? 'bg-green-500' :
                              status.status === 'running' ? 'bg-blue-500 animate-pulse' :
                              status.status === 'failed' ? 'bg-red-500' : 'bg-gray-300'
                            }`}>
                              {status.status === 'completed' ? <CheckCircle className="h-4 w-4 text-white" /> :
                               status.status === 'running' ? <Clock className="h-4 w-4 text-white" /> :
                               status.status === 'failed' ? <XCircle className="h-4 w-4 text-white" /> :
                               <div className="w-2 h-2 bg-gray-500 rounded-full"></div>}
                            </div>
                            <span className="text-xs capitalize">{agent}</span>
                          </div>
                        ))}
                      </div>
                    )}

                    {job.events && job.events.length > 0 && (
                      <div className="mt-3 max-h-32 overflow-y-auto">
                        {job.events.slice(-3).map((event, i) => (
                          <div key={i} className="text-xs text-muted-foreground">
                            {new Date(event.timestamp).toLocaleTimeString()}: {event.message}
                          </div>
                        ))}
                      </div>
                    )}

                    {job.branch_url && (
                      <div className="mt-3 flex space-x-2">
                        <Button size="sm" variant="outline" asChild>
                          <a href={job.branch_url} target="_blank" rel="noopener noreferrer">
                            <GitBranch className="h-3 w-3 mr-1" />
                            Branch
                          </a>
                        </Button>
                        {job.pr_url && (
                          <Button size="sm" variant="outline" asChild>
                            <a href={job.pr_url} target="_blank" rel="noopener noreferrer">
                              PR
                            </a>
                          </Button>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function PipelinesPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Data Pipelines</h1>
        <p className="text-muted-foreground">Airbyte connections and pipeline status (read-only for MVP)</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Pipeline Status</CardTitle>
          <CardDescription>Overview of data pipeline health</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <Database className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>Pipeline management interface coming soon</p>
            <p className="text-sm">Check the Overview page for Airbyte health status</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function ModelsPage() {
  const [models, setModels] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchModels()
  }, [])

  const fetchModels = async () => {
    try {
      const response = await fetch(`${API_BASE}/models/allowlist`)
      const data = await response.json()
      setModels(data)
    } catch (error) {
      console.error('Failed to fetch models:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Model Allow-list</h1>
        <p className="text-muted-foreground">OpenRouter approved models with availability status</p>
      </div>

      {models?.error ? (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center text-destructive">
              <XCircle className="h-12 w-12 mx-auto mb-4" />
              <p className="font-medium">Error loading models</p>
              <p className="text-sm">{models.error}</p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Total Approved</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{models?.total_approved || 0}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Available</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">{models?.available_count || 0}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Last Checked</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-sm">
                  {models?.last_checked ? new Date(models.last_checked).toLocaleString() : 'N/A'}
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Model Status</CardTitle>
              <CardDescription>Availability status for each approved model</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {models?.approved_models?.map((model, index) => (
                  <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                    <span className="text-sm font-medium">{model.name}</span>
                    <div className="flex items-center space-x-2">
                      {model.allowed && (
                        <Badge variant="outline" className="text-xs">
                          🔒 Allowed
                        </Badge>
                      )}
                      <StatusBadge status={model.status === 'available' ? 'healthy' : 'unhealthy'}>
                        {model.status === 'available' ? '✅' : '❌'}
                      </StatusBadge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <div className="flex justify-center">
            <Button onClick={fetchModels} variant="outline">
              <Zap className="h-4 w-4 mr-2" />
              Refresh Model Status
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-background">
        <Navigation />
        <main>
          <Routes>
            <Route path="/" element={<OverviewPage />} />
            <Route path="/swarm" element={<SwarmPage />} />
            <Route path="/pipelines" element={<PipelinesPage />} />
            <Route path="/models" element={<ModelsPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App

