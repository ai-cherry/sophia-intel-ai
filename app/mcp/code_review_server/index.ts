import express from 'express';
import { createServer } from 'http';
import { createServer as createHttpsServer } from 'https';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { spawn } from 'child_process';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
const PORT = 8003;

// CORS middleware - allow all origins for development
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization');
  
  // Handle preflight requests
  if (req.method === 'OPTIONS') {
    return res.sendStatus(200);
  }
  
  next();
});

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'MCP Server' });
});

// Code review endpoint
app.post('/mcp/code-review', async (req, res) => {
  try {
    const { code } = req.body;
    if (!code) {
      return res.status(400).json({ error: 'Code is required' });
    }

    // Simulate code review processing
    const suggestions = [
      {
        type: "Performance",
        location: "Line 15",
        description: "Consider using a more efficient algorithm for this loop",
        fix: "Replace for loop with array.map()"
      },
      {
        type: "Security",
        location: "Line 22",
        description: "Potential SQL injection vulnerability",
        fix: "Use parameterized queries"
      }
    ];

    const metrics = {
      complexity: "Medium",
      readability: 75,
      bug_risk: "Low"
    };

    res.json({ suggestions, metrics });
  } catch (error) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Quality check endpoint
app.post('/mcp/quality-check', async (req, res) => {
  try {
    const { url = 'http://localhost:8501' } = req.body;
    
    // Validate URL to prevent injection
    const validUrl = new URL(url);
    if (!['http:', 'https:'].includes(validUrl.protocol)) {
      return res.status(400).json({ error: 'Invalid URL protocol' });
    }
    if (!['localhost', '127.0.0.1'].includes(validUrl.hostname)) {
      return res.status(403).json({ error: 'Only local URLs allowed' });
    }
    
    // Use spawn instead of exec for safety
    const axe = spawn('npx', ['axe-cli', validUrl.href], {
      shell: false,  // Critical: Disable shell to prevent injection
      timeout: 30000
    });
    
    let output = '';
    let errorOutput = '';
    
    axe.stdout.on('data', (data) => {
      output += data.toString();
    });
    
    axe.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });
    
    axe.on('close', (code) => {
      if (code === 0) {
        res.json({ quality_report: output });
      } else {
        res.status(500).json({ error: 'Quality check failed', details: errorOutput });
      }
    });
    
    axe.on('error', (error) => {
      res.status(500).json({ error: 'Failed to spawn quality check', details: error.message });
    });
  } catch (error) {
    res.status(500).json({ error: 'Invalid request', details: error.message });
  }
});

// Swarm status endpoint
app.get('/mcp/swarm-status', (req, res) => {
  // Mock swarm data for demonstration
  const swarmData = {
    status: 'active',
    agents: [
      { id: 'agent-1', status: 'online', last_active: new Date().toISOString() },
      { id: 'agent-2', status: 'online', last_active: new Date().toISOString() },
      { id: 'agent-3', status: 'offline', last_active: new Date(Date.now() - 300000).toISOString() }
    ],
    total_agents: 3,
    active_agents: 2
  };
  res.json(swarmData);
});

// Swarm configuration endpoint
app.post('/mcp/swarm-config', (req, res) => {
  try {
    const { num_agents, agent_type, max_concurrency } = req.body;
    
    // Input validation
    if (!num_agents || typeof num_agents !== 'number' || num_agents < 1 || num_agents > 100) {
      return res.status(400).json({ error: 'Invalid num_agents: must be between 1 and 100' });
    }
    
    const validAgentTypes = ['CPU', 'GPU', 'Hybrid'];
    if (!agent_type || !validAgentTypes.includes(agent_type)) {
      return res.status(400).json({ error: 'Invalid agent_type: must be CPU, GPU, or Hybrid' });
    }
    
    if (!max_concurrency || typeof max_concurrency !== 'number' || max_concurrency < 1 || max_concurrency > 50) {
      return res.status(400).json({ error: 'Invalid max_concurrency: must be between 1 and 50' });
    }
    
    // Process configuration (e.g., update swarm settings)
    console.log(`Swarm configuration updated: ${num_agents} agents, ${agent_type}, ${max_concurrency}`);
    res.json({ status: 'success', message: 'Configuration updated' });
  } catch (error) {
    res.status(500).json({ error: 'Invalid configuration data' });
  }
});

// Teams run endpoint for swarm coordination
app.post('/teams/run', async (req, res) => {
  try {
    const { message, team_id, stream = false, session_id } = req.body;
    
    if (!message || !team_id) {
      return res.status(400).json({ error: 'Message and team_id are required' });
    }
    
    // Set headers for streaming if requested
    if (stream) {
      res.setHeader('Content-Type', 'text/event-stream');
      res.setHeader('Cache-Control', 'no-cache');
      res.setHeader('Connection', 'keep-alive');
      res.setHeader('Access-Control-Allow-Origin', '*');
    }
    
    // Simulate swarm processing with streaming response
    const swarmResponses = {
      'strategic-swarm': [
        'Analyzing cloud deployment plan...',
        'Identified optimization opportunities:',
        '1. **Auto-scaling**: Implement horizontal pod autoscaling for microservices',
        '2. **Cost Optimization**: Use spot instances for non-critical workloads',
        '3. **Multi-region**: Deploy to multiple regions for better latency',
        '4. **Caching Strategy**: Add Redis/CDN layers for static content',
        '5. **Monitoring**: Integrate Prometheus + Grafana for observability',
        '6. **Security**: Add WAF and implement zero-trust networking',
        'Deployment plan improvements complete!'
      ],
      'coding-swarm': [
        'Reviewing code architecture...',
        'Generating implementation plan...',
        'Code improvements ready.'
      ],
      'debate-swarm': [
        'Analyzing arguments...',
        'Evaluating perspectives...',
        'Consensus reached.'
      ]
    };
    
    const responses = swarmResponses[team_id] || ['Processing request...', 'Analysis complete.'];
    
    if (stream) {
      // Stream responses with delay to simulate real processing
      for (let i = 0; i < responses.length; i++) {
        res.write(`data: ${JSON.stringify({ 
          content: responses[i], 
          done: i === responses.length - 1,
          team_id,
          session_id: session_id || `session_${Date.now()}`
        })}\n\n`);
        
        // Add delay between messages for realistic streaming
        await new Promise(resolve => setTimeout(resolve, 500));
      }
      res.end();
    } else {
      // Return all responses at once
      res.json({
        team_id,
        session_id: session_id || `session_${Date.now()}`,
        responses,
        status: 'complete'
      });
    }
  } catch (error) {
    res.status(500).json({ error: 'Team processing failed', details: error.message });
  }
});

// Teams list endpoint
app.get('/teams', (req, res) => {
  const teams = [
    {
      id: 'strategic-swarm',
      name: 'Strategic Planning Swarm',
      description: 'Analyzes and improves deployment strategies',
      status: 'active',
      agents: 3
    },
    {
      id: 'coding-swarm',
      name: 'Coding Swarm',
      description: 'Implements code improvements and refactoring',
      status: 'active',
      agents: 5
    },
    {
      id: 'debate-swarm',
      name: 'Debate Swarm',
      description: 'Evaluates multiple perspectives for decisions',
      status: 'active',
      agents: 4
    }
  ];
  res.json(teams);
});

// Start server
const server = createServer(app);
server.listen(PORT, () => {
  console.log(`MCP Server running on http://localhost:${PORT}`);
});

// Graceful shutdown
process.on('SIGINT', () => {
  server.close(() => {
    console.log('MCP Server closed');
    process.exit(0);
  });
});
