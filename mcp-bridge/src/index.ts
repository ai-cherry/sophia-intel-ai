/**
 * Sophia MCP Bridge
 * Main entry point for multi-assistant coordination
 */

import { spawn } from 'child_process';
import winston from 'winston';
import dotenv from 'dotenv';

dotenv.config();

// Logger configuration
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.colorize(),
    winston.format.simple()
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'mcp-bridge.log' })
  ]
});

interface AdapterConfig {
  name: string;
  script: string;
  env?: Record<string, string>;
}

class MCPBridgeOrchestrator {
  private adapters: Map<string, any> = new Map();
  
  constructor() {
    logger.info('Initializing MCP Bridge Orchestrator');
  }

  async startAdapter(config: AdapterConfig): Promise<void> {
    logger.info(`Starting ${config.name} adapter...`);
    
    const adapter = spawn('tsx', [config.script], {
      env: {
        ...process.env,
        ...config.env
      },
      stdio: ['inherit', 'pipe', 'pipe']
    });

    adapter.stdout?.on('data', (data) => {
      logger.info(`[${config.name}] ${data.toString().trim()}`);
    });

    adapter.stderr?.on('data', (data) => {
      logger.error(`[${config.name}] ${data.toString().trim()}`);
    });

    adapter.on('close', (code) => {
      logger.info(`[${config.name}] Process exited with code ${code}`);
      this.adapters.delete(config.name);
      
      // Restart on unexpected exit
      if (code !== 0) {
        logger.info(`Restarting ${config.name} adapter in 5 seconds...`);
        setTimeout(() => this.startAdapter(config), 5000);
      }
    });

    this.adapters.set(config.name, adapter);
  }

  async startAll(): Promise<void> {
    const adapters: AdapterConfig[] = [
      {
        name: 'Claude Desktop',
        script: 'src/claude-adapter.ts',
        env: {
          ASSISTANT_ID: 'claude-desktop'
        }
      },
      {
        name: 'Roo/Cursor',
        script: 'src/roo-adapter.ts',
        env: {
          ASSISTANT_ID: 'roo-cursor'
        }
      },
      {
        name: 'Cline',
        script: 'src/cline-adapter.ts',
        env: {
          ASSISTANT_ID: 'cline'
        }
      }
    ];

    for (const adapter of adapters) {
      await this.startAdapter(adapter);
      // Stagger startup
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    logger.info('All MCP adapters started successfully');
  }

  async stopAll(): Promise<void> {
    logger.info('Stopping all MCP adapters...');
    
    for (const [name, adapter] of this.adapters) {
      logger.info(`Stopping ${name}...`);
      adapter.kill('SIGTERM');
    }
    
    this.adapters.clear();
    logger.info('All adapters stopped');
  }
}

// Main execution
async function main() {
  const orchestrator = new MCPBridgeOrchestrator();
  
  // Handle shutdown signals
  process.on('SIGINT', async () => {
    logger.info('Received SIGINT, shutting down gracefully...');
    await orchestrator.stopAll();
    process.exit(0);
  });

  process.on('SIGTERM', async () => {
    logger.info('Received SIGTERM, shutting down gracefully...');
    await orchestrator.stopAll();
    process.exit(0);
  });

  // Start all adapters
  try {
    await orchestrator.startAll();
  } catch (error) {
    logger.error('Failed to start MCP Bridge:', error);
    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  main().catch((error) => {
    logger.error('Fatal error:', error);
    process.exit(1);
  });
}

export { MCPBridgeOrchestrator };