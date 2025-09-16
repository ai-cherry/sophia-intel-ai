/**
 * PM2 Ecosystem Configuration for Sophia Intel AI
 * Production-ready process management for NPM-based MCP servers
 * 
 * Usage:
 *   pm2 start config/pm2.ecosystem.config.js
 *   pm2 stop all
 *   pm2 restart all
 *   pm2 logs
 *   pm2 monit
 */

module.exports = {
  apps: [
    // ==========================================
    // MCP Python Servers (using PM2 interpreter)
    // ==========================================
    {
      name: 'mcp-memory',
      script: '-m',
      args: 'uvicorn mcp.memory_server:app --host 0.0.0.0 --port 8081',
      interpreter: 'python3',
      cwd: '/Users/lynnmusil/sophia-intel-ai',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_restarts: 3,
      min_uptime: '10s',
      max_memory_restart: '500M',
      error_file: './logs/pm2/mcp-memory-error.log',
      out_file: './logs/pm2/mcp-memory-out.log',
      log_file: './logs/pm2/mcp-memory-combined.log',
      time: true,
      merge_logs: true,
      kill_timeout: 5000,
      listen_timeout: 10000,
      env: {
        NODE_ENV: 'production',
        PYTHONUNBUFFERED: '1'
      },
      // Health check configuration
      health_check: {
        interval: 30000,  // 30 seconds
        timeout: 5000,    // 5 seconds
        max_consecutive_failures: 3,
        http_options: {
          url: 'http://localhost:8081/health',
          method: 'GET'
        }
      }
    },
    
    {
      name: 'mcp-filesystem',
      script: '-m',
      args: 'uvicorn mcp.filesystem.server:app --host 0.0.0.0 --port 8082',
      interpreter: 'python3',
      cwd: '/Users/lynnmusil/sophia-intel-ai',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_restarts: 3,
      min_uptime: '10s',
      max_memory_restart: '500M',
      error_file: './logs/pm2/mcp-filesystem-error.log',
      out_file: './logs/pm2/mcp-filesystem-out.log',
      log_file: './logs/pm2/mcp-filesystem-combined.log',
      time: true,
      merge_logs: true,
      kill_timeout: 5000,
      listen_timeout: 10000,
      env: {
        NODE_ENV: 'production',
        PYTHONUNBUFFERED: '1'
      },
      health_check: {
        interval: 30000,
        timeout: 5000,
        max_consecutive_failures: 3,
        http_options: {
          url: 'http://localhost:8082/health',
          method: 'GET'
        }
      }
    },
    
    {
      name: 'mcp-git',
      script: '-m',
      args: 'uvicorn mcp.git.server:app --host 0.0.0.0 --port 8084',
      interpreter: 'python3',
      cwd: '/Users/lynnmusil/sophia-intel-ai',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_restarts: 3,
      min_uptime: '10s',
      max_memory_restart: '500M',
      error_file: './logs/pm2/mcp-git-error.log',
      out_file: './logs/pm2/mcp-git-out.log',
      log_file: './logs/pm2/mcp-git-combined.log',
      time: true,
      merge_logs: true,
      kill_timeout: 5000,
      listen_timeout: 10000,
      env: {
        NODE_ENV: 'production',
        PYTHONUNBUFFERED: '1'
      },
      health_check: {
        interval: 30000,
        timeout: 5000,
        max_consecutive_failures: 3,
        http_options: {
          url: 'http://localhost:8084/health',
          method: 'GET'
        }
      }
    },
    
    // ==========================================
    // NPM-based MCP Servers
    // ==========================================
    {
      name: 'mcp-memory-npm',
      script: 'npx',
      args: '-y @modelcontextprotocol/server-memory',
      cwd: '/Users/lynnmusil/sophia-intel-ai',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_restarts: 3,
      min_uptime: '10s',
      max_memory_restart: '300M',
      error_file: './logs/pm2/mcp-memory-npm-error.log',
      out_file: './logs/pm2/mcp-memory-npm-out.log',
      log_file: './logs/pm2/mcp-memory-npm-combined.log',
      time: true,
      merge_logs: true,
      kill_timeout: 3000,
      env: {
        NODE_ENV: 'production'
      }
    },
    
    {
      name: 'mcp-sequentialthinking',
      script: 'npx',
      args: '-y @modelcontextprotocol/server-sequential-thinking',
      cwd: '/Users/lynnmusil/sophia-intel-ai',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_restarts: 3,
      min_uptime: '10s',
      max_memory_restart: '300M',
      error_file: './logs/pm2/mcp-sequentialthinking-error.log',
      out_file: './logs/pm2/mcp-sequentialthinking-out.log',
      log_file: './logs/pm2/mcp-sequentialthinking-combined.log',
      time: true,
      merge_logs: true,
      kill_timeout: 3000,
      env: {
        NODE_ENV: 'production'
      }
    },
    
    {
      name: 'mcp-apify',
      script: 'npx',
      args: '-y @apify/actors-mcp-server',
      cwd: '/Users/lynnmusil/sophia-intel-ai',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_restarts: 3,
      min_uptime: '10s',
      max_memory_restart: '300M',
      error_file: './logs/pm2/mcp-apify-error.log',
      out_file: './logs/pm2/mcp-apify-out.log',
      log_file: './logs/pm2/mcp-apify-combined.log',
      time: true,
      merge_logs: true,
      kill_timeout: 3000,
      env: {
        NODE_ENV: 'production',
        APIFY_API_TOKEN: process.env.APIFY_API_TOKEN
      }
    },
    
    {
      name: 'mcp-brave-search',
      script: 'npx',
      args: '-y @modelcontextprotocol/server-brave-search',
      cwd: '/Users/lynnmusil/sophia-intel-ai',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_restarts: 3,
      min_uptime: '10s',
      max_memory_restart: '300M',
      error_file: './logs/pm2/mcp-brave-search-error.log',
      out_file: './logs/pm2/mcp-brave-search-out.log',
      log_file: './logs/pm2/mcp-brave-search-combined.log',
      time: true,
      merge_logs: true,
      kill_timeout: 3000,
      env: {
        NODE_ENV: 'production',
        BRAVE_SEARCH_API_KEY: process.env.BRAVE_SEARCH_API_KEY
      }
    },
    
    {
      name: 'mcp-exa',
      script: 'npx',
      args: 'exa-mcp-server',
      cwd: '/Users/lynnmusil/sophia-intel-ai',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_restarts: 3,
      min_uptime: '10s',
      max_memory_restart: '300M',
      error_file: './logs/pm2/mcp-exa-error.log',
      out_file: './logs/pm2/mcp-exa-out.log',
      log_file: './logs/pm2/mcp-exa-combined.log',
      time: true,
      merge_logs: true,
      kill_timeout: 3000,
      env: {
        NODE_ENV: 'production',
        EXA_API_KEY: process.env.EXA_API_KEY
      }
    },
    
    {
      name: 'mcp-github',
      script: 'docker',
      args: 'run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN -e GITHUB_TOOLSETS -e GITHUB_READ_ONLY ghcr.io/github/github-mcp-server',
      cwd: '/Users/lynnmusil/sophia-intel-ai',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_restarts: 3,
      min_uptime: '10s',
      max_memory_restart: '500M',
      error_file: './logs/pm2/mcp-github-error.log',
      out_file: './logs/pm2/mcp-github-out.log',
      log_file: './logs/pm2/mcp-github-combined.log',
      time: true,
      merge_logs: true,
      kill_timeout: 5000,
      env: {
        NODE_ENV: 'production',
        GITHUB_PERSONAL_ACCESS_TOKEN: process.env.GITHUB_PERSONAL_ACCESS_TOKEN,
        GITHUB_TOOLSETS: process.env.GITHUB_TOOLSETS || 'all',
        GITHUB_READ_ONLY: process.env.GITHUB_READ_ONLY || 'false'
      }
    },
    
    // ==========================================
    // Health Monitor Process
    // ==========================================
    {
      name: 'health-monitor',
      script: './scripts/mcp_health_monitor.py',
      interpreter: 'python3',
      cwd: '/Users/lynnmusil/sophia-intel-ai',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_restarts: 10,
      min_uptime: '30s',
      max_memory_restart: '200M',
      error_file: './logs/pm2/health-monitor-error.log',
      out_file: './logs/pm2/health-monitor-out.log',
      log_file: './logs/pm2/health-monitor-combined.log',
      time: true,
      merge_logs: true,
      args: '--interval 30',
      env: {
        NODE_ENV: 'production',
        PYTHONUNBUFFERED: '1'
      }
    }
  ],
  
  // Deploy configuration (for reference)
  deploy: {
    production: {
      user: 'sophia',
      host: 'localhost',
      ref: 'origin/main',
      repo: 'https://github.com/sophia-intel/sophia-intel-ai.git',
      path: '/Users/lynnmusil/sophia-intel-ai',
      'post-deploy': 'npm install && pm2 reload config/pm2.ecosystem.config.js --env production',
      'pre-deploy-local': 'echo "Deploying to production"'
    }
  }
};

// Log rotation configuration (automatic with PM2)
// PM2 will automatically rotate logs when they reach 10MB
// Keeps 30 days of logs by default
// Can be configured with: pm2 install pm2-logrotate
// pm2 set pm2-logrotate:max_size 10M
// pm2 set pm2-logrotate:retain 30
// pm2 set pm2-logrotate:compress true