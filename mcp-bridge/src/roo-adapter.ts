#!/usr/bin/env node
/**
 * Roo/Cursor MCP Adapter
 * Bridges Roo/Cursor with Sophia MCP Server via stdio protocol
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import axios from 'axios';
import { createClient } from 'redis';
import winston from 'winston';
import dotenv from 'dotenv';

dotenv.config();

// Logger configuration
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.File({ filename: 'roo-adapter.log' }),
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

// Configuration
const config = {
  mcpServerUrl: process.env.MCP_SERVER_URL || 'http://localhost:8004',
  redisUrl: process.env.REDIS_URL || 'redis://localhost:6379',
  assistantId: 'roo-cursor',
  apiKey: process.env.MCP_API_KEY || 'sophia-mcp-key',
};

// Redis client for real-time sync
const redis = createClient({ url: config.redisUrl });
const subscriber = createClient({ url: config.redisUrl });

redis.on('error', (err) => logger.error('Redis error:', err));
subscriber.on('error', (err) => logger.error('Redis subscriber error:', err));

// MCP Server client with enhanced features for Roo/Cursor
class RooMCPClient {
  private token: string | null = null;
  private tokenExpiry: Date | null = null;
  private syncChannel = 'sophia:sync:roo';

  async authenticate(): Promise<void> {
    if (this.token && this.tokenExpiry && this.tokenExpiry > new Date()) {
      return;
    }

    try {
      const response = await axios.post(`${config.mcpServerUrl}/mcp/initialize`, {
        assistant_id: config.assistantId,
        metadata: {
          type: 'roo-cursor',
          version: '1.0.0',
          capabilities: ['code-generation', 'refactoring', 'testing']
        }
      }, {
        headers: { 'X-API-Key': config.apiKey }
      });

      this.token = response.data.access_token;
      this.tokenExpiry = new Date(Date.now() + response.data.expires_in * 1000);
      logger.info('Authentication successful');
    } catch (error) {
      logger.error('Authentication failed:', error);
      throw error;
    }
  }

  async callTool(toolName: string, args: any): Promise<any> {
    await this.authenticate();

    const headers = {
      'Authorization': `Bearer ${this.token}`,
      'Content-Type': 'application/json'
    };

    try {
      switch (toolName) {
        // Memory operations
        case 'store_code_memory':
          return await this.storeCodeMemory(args, headers);
        case 'search_code_patterns':
          return await this.searchCodePatterns(args, headers);
        case 'get_code_context':
          return await this.getCodeContext(args, headers);

        // Code intelligence
        case 'analyze_codebase':
          return await this.analyzeCodebase(args, headers);
        case 'suggest_refactoring':
          return await this.suggestRefactoring(args, headers);
        case 'generate_tests':
          return await this.generateTests(args, headers);

        // Collaboration
        case 'share_insight':
          return await this.shareInsight(args, headers);
        case 'get_team_context':
          return await this.getTeamContext(args, headers);

        default:
          throw new Error(`Unknown tool: ${toolName}`);
      }
    } catch (error) {
      logger.error(`Tool execution failed: ${toolName}`, error);
      throw error;
    }
  }

  private async storeCodeMemory(args: any, headers: any): Promise<any> {
    const response = await axios.post(
      `${config.mcpServerUrl}/mcp/memory/store`,
      {
        content: args.code,
        metadata: {
          type: 'code',
          language: args.language,
          file_path: args.file_path,
          project: args.project,
          tags: args.tags || []
        },
        ttl: args.ttl || 86400 * 30 // 30 days for code
      },
      { headers }
    );

    // Publish to sync channel
    await redis.publish(this.syncChannel, JSON.stringify({
      event: 'code_stored',
      data: response.data
    }));

    return response.data;
  }

  private async searchCodePatterns(args: any, headers: any): Promise<any> {
    const response = await axios.post(
      `${config.mcpServerUrl}/mcp/memory/search`,
      {
        query: args.pattern,
        limit: args.limit || 20,
        metadata_filter: {
          type: 'code',
          language: args.language,
          project: args.project
        }
      },
      { headers }
    );
    return response.data;
  }

  private async getCodeContext(args: any, headers: any): Promise<any> {
    const response = await axios.post(
      `${config.mcpServerUrl}/mcp/context`,
      {
        topic: args.file_path,
        depth: args.depth || 2,
        include_types: ['code', 'documentation', 'tests']
      },
      { headers }
    );
    return response.data;
  }

  private async analyzeCodebase(args: any, headers: any): Promise<any> {
    // Analyze codebase structure and patterns
    const analysis: any = {
      project: args.project,
      patterns: [],
      suggestions: [],
      metrics: {}
    };

    // Search for common patterns
    const patterns = await this.searchCodePatterns({
      pattern: args.pattern || '*',
      project: args.project,
      limit: 100
    }, headers);

    // Analyze patterns
    analysis.patterns = this.extractPatterns(patterns.results);
    analysis.metrics = this.calculateMetrics(patterns.results);
    analysis.suggestions = this.generateSuggestions(analysis);

    return analysis;
  }

  private async suggestRefactoring(args: any, headers: any): Promise<any> {
    // Get context for the code
    const context = await this.getCodeContext({
      file_path: args.file_path,
      depth: 3
    }, headers);

    // Generate refactoring suggestions
    return {
      file_path: args.file_path,
      suggestions: [
        {
          type: 'extract_method',
          description: 'Extract complex logic into separate methods',
          priority: 'high'
        },
        {
          type: 'simplify_conditionals',
          description: 'Simplify nested conditionals',
          priority: 'medium'
        }
      ],
      context: context
    };
  }

  private async generateTests(args: any, headers: any): Promise<any> {
    // Get code context
    await this.getCodeContext({
      file_path: args.file_path,
      depth: 2
    }, headers);

    // Generate test suggestions
    return {
      file_path: args.file_path,
      test_framework: args.framework || 'pytest',
      tests: [
        {
          name: 'test_basic_functionality',
          type: 'unit',
          description: 'Test basic function behavior'
        },
        {
          name: 'test_edge_cases',
          type: 'unit',
          description: 'Test edge cases and error handling'
        }
      ],
      coverage_estimate: 80
    };
  }

  private async shareInsight(args: any, headers: any): Promise<any> {
    // Share insight with team
    const insight = {
      from: config.assistantId,
      type: args.type,
      content: args.content,
      context: args.context,
      timestamp: new Date().toISOString()
    };

    // Store in memory
    await axios.post(
      `${config.mcpServerUrl}/mcp/memory/store`,
      {
        content: JSON.stringify(insight),
        metadata: {
          type: 'insight',
          from: config.assistantId,
          shared: true
        }
      },
      { headers }
    );

    // Broadcast to team
    await redis.publish('sophia:insights', JSON.stringify(insight));

    return { status: 'shared', insight };
  }

  private async getTeamContext(args: any, headers: any): Promise<any> {
    // Get shared team context
    const response = await axios.post(
      `${config.mcpServerUrl}/mcp/memory/search`,
      {
        query: args.topic || '*',
        limit: 50,
        metadata_filter: {
          shared: true
        }
      },
      { headers }
    );

    return {
      topic: args.topic,
      team_insights: response.data.results,
      active_assistants: await this.getActiveAssistants()
    };
  }

  private extractPatterns(results: any[]): any[] {
    // Extract common code patterns
    const patterns = new Map<string, number>();

    for (const result of results) {
      // Simple pattern extraction (would be more sophisticated in production)
      const content = result.content;
      if (content.includes('async')) patterns.set('async', (patterns.get('async') || 0) + 1);
      if (content.includes('class')) patterns.set('class', (patterns.get('class') || 0) + 1);
      if (content.includes('function')) patterns.set('function', (patterns.get('function') || 0) + 1);
    }

    return Array.from(patterns.entries()).map(([pattern, count]) => ({
      pattern,
      count,
      percentage: (count / results.length) * 100
    }));
  }

  private calculateMetrics(results: any[]): any {
    return {
      total_files: results.length,
      average_length: results.reduce((acc, r) => acc + r.content.length, 0) / results.length,
      languages: [...new Set(results.map(r => r.metadata?.language).filter(Boolean))]
    };
  }

  private generateSuggestions(analysis: any): any[] {
    const suggestions: any[] = [];

    // Generate suggestions based on patterns
    for (const pattern of analysis.patterns) {
      if (pattern.pattern === 'async' && pattern.percentage > 50) {
        suggestions.push({
          type: 'architecture',
          suggestion: 'Consider implementing async/await patterns consistently',
          priority: 'medium'
        });
      }
    }

    return suggestions;
  }

  private async getActiveAssistants(): Promise<string[]> {
    // Get list of active assistants from Redis
    const keys = await redis.keys('session:*');
    const assistants = new Set<string>();

    for (const key of keys) {
      const session = await redis.get(key);
      if (session) {
        const data = JSON.parse(session);
        if (data.active) {
          assistants.add(data.assistant_id);
        }
      }
    }

    return Array.from(assistants);
  }
}

// Initialize MCP server
async function main() {
  logger.info('Starting Roo/Cursor MCP Adapter...');

  // Connect to Redis
  await redis.connect();
  await subscriber.connect();
  logger.info('Connected to Redis');

  // Subscribe to sync channels
  await subscriber.subscribe('sophia:sync:*', (message, channel) => {
    logger.info(`Sync event on ${channel}:`, message);
  });

  // Create MCP client
  const mcpClient = new RooMCPClient();

  // Create MCP server
  const server = new Server(
    {
      name: 'sophia-mcp-roo',
      version: '1.0.0'
    },
    {
      capabilities: {
        tools: {},
        resources: {}
      }
    }
  );

  // Define available tools
  const tools = [
    {
      name: 'store_code_memory',
      description: 'Store code snippet or pattern in knowledge base',
      inputSchema: {
        type: 'object',
        properties: {
          code: { type: 'string', description: 'Code content' },
          language: { type: 'string', description: 'Programming language' },
          file_path: { type: 'string', description: 'File path' },
          project: { type: 'string', description: 'Project name' },
          tags: { type: 'array', items: { type: 'string' } }
        },
        required: ['code', 'language']
      }
    },
    {
      name: 'search_code_patterns',
      description: 'Search for code patterns in knowledge base',
      inputSchema: {
        type: 'object',
        properties: {
          pattern: { type: 'string', description: 'Search pattern' },
          language: { type: 'string', description: 'Filter by language' },
          project: { type: 'string', description: 'Filter by project' },
          limit: { type: 'number', description: 'Max results' }
        },
        required: ['pattern']
      }
    },
    {
      name: 'analyze_codebase',
      description: 'Analyze codebase structure and patterns',
      inputSchema: {
        type: 'object',
        properties: {
          project: { type: 'string', description: 'Project to analyze' },
          pattern: { type: 'string', description: 'Pattern to look for' }
        },
        required: ['project']
      }
    },
    {
      name: 'suggest_refactoring',
      description: 'Get refactoring suggestions for code',
      inputSchema: {
        type: 'object',
        properties: {
          file_path: { type: 'string', description: 'File to analyze' }
        },
        required: ['file_path']
      }
    },
    {
      name: 'generate_tests',
      description: 'Generate test suggestions for code',
      inputSchema: {
        type: 'object',
        properties: {
          file_path: { type: 'string', description: 'File to test' },
          framework: { type: 'string', description: 'Test framework' }
        },
        required: ['file_path']
      }
    },
    {
      name: 'share_insight',
      description: 'Share coding insight with team',
      inputSchema: {
        type: 'object',
        properties: {
          type: { type: 'string', description: 'Insight type' },
          content: { type: 'string', description: 'Insight content' },
          context: { type: 'object', additionalProperties: true }
        },
        required: ['type', 'content']
      }
    },
    {
      name: 'get_team_context',
      description: 'Get shared team context and insights',
      inputSchema: {
        type: 'object',
        properties: {
          topic: { type: 'string', description: 'Topic to get context for' }
        }
      }
    }
  ];

  // Handle list tools request
  server.setRequestHandler(ListToolsRequestSchema, async () => {
    return { tools };
  });

  // Handle tool calls
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    try {
      const result = await mcpClient.callTool(name, args);

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(result, null, 2)
          }
        ]
      };
    } catch (error: any) {
      logger.error(`Tool execution failed: ${name}`, error);
      return {
        content: [
          {
            type: 'text',
            text: `Error: ${error.message}`
          }
        ],
        isError: true
      };
    }
  });

  // Handle resource listing
  server.setRequestHandler(ListResourcesRequestSchema, async () => {
    return {
      resources: [
        {
          uri: 'sophia://codebase',
          name: 'Codebase Analysis',
          description: 'Access codebase analysis and metrics',
          mimeType: 'application/json'
        },
        {
          uri: 'sophia://insights',
          name: 'Team Insights',
          description: 'Shared team insights and knowledge',
          mimeType: 'application/json'
        }
      ]
    };
  });

  // Handle resource reading
  server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
    const { uri } = request.params;

    if (uri === 'sophia://codebase') {
      return {
        contents: [
          {
            uri,
            mimeType: 'application/json',
            text: JSON.stringify({
              status: 'active',
              projects: ['sophia-intel-ai'],
              metrics: {
                total_files: 150,
                languages: ['python', 'typescript', 'javascript']
              }
            }, null, 2)
          }
        ]
      };
    }

    return { contents: [] };
  });

  // Start server with stdio transport
  const transport = new StdioServerTransport();
  await server.connect(transport);

  logger.info('Roo/Cursor MCP Adapter is running');

  // Handle graceful shutdown
  process.on('SIGINT', async () => {
    logger.info('Shutting down...');
    await subscriber.unsubscribe();
    await subscriber.quit();
    await redis.quit();
    await server.close();
    process.exit(0);
  });
}

// Run
main().catch((error) => {
  logger.error('Fatal error:', error);
  process.exit(1);
});
