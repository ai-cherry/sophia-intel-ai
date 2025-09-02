import express from 'express';
import { createServer } from 'http';
import { createServer as createHttpsServer } from 'https';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { exec } from 'child_process';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
const PORT = 8000;

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
    // Trigger Claude's quality check
    const result = await new Promise((resolve, reject) => {
      exec('npx axe-cli http://localhost:8501', (error, stdout, stderr) => {
        if (error) {
          reject(error);
        } else {
          resolve(stdout);
        }
      });
    });

    res.json({ quality_report: result });
  } catch (error) {
    res.status(500).json({ error: 'Quality check failed' });
  }
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
