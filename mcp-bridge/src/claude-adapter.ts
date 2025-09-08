#!/usr/bin/env node
/**
 * Claude Desktop MCP Adapter
 * Bridges Claude Desktop with Sophia MCP Server via stdio protocol
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
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
    new winston.transports.File({ filename: 'claude-adapter.log' }),
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

// Configuration
const config = {
  mcpServerUrl: process.env.MCP_SERVER_URL || 'http://localhost:8004',
  redisUrl: process.env.REDIS_URL || 'redis://localhost:6379',
  assistantId: 'claude-desktop',
  apiKey: process.env.MCP_API_KEY || 'sophia-mcp-key',
};

// Redis client for caching
const redis = createClient({ url: config.redisUrl });
redis.on('error', (err) => logger.error('Redis error:', err));

// MCP Server client
class MCPServerClient {
  private token: string | null = null;
  private tokenExpiry: Date | null = null;

  async authenticate(): Promise<void> {
    if (this.token && this.tokenExpiry && this.tokenExpiry > new Date()) {
      return;
    }

    try {
      const response = await axios.post(`${config.mcpServerUrl}/mcp/initialize`, {
        assistant_id: config.assistantId,
        metadata: {
          type: 'claude-desktop',
          version: '1.0.0'
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
        case 'store_memory':
          return await this.storeMemory(args, headers);
        case 'search_memory':
          return await this.searchMemory(args, headers);
        case 'update_memory':
          return await this.updateMemory(args, headers);
        case 'delete_memory':
          return await this.deleteMemory(args, headers);
        case 'get_context':
          return await this.getContext(args, headers);
        default:
          throw new Error(`Unknown tool: ${toolName}`);
      }
    } catch (error) {
      logger.error(`Tool execution failed: ${toolName}`, error);
      throw error;
    }
  }

  private async storeMemory(args: any, headers: any): Promise<any> {
    const response = await axios.post(
      `${config.mcpServerUrl}/mcp/memory/store`,
      {
        content: args.content,
        metadata: args.metadata || {},
        ttl: args.ttl
      },
      { headers }
    );
    return response.data;
  }

  private async searchMemory(args: any, headers: any): Promise<any> {
    const response = await axios.post(
      `${config.mcpServerUrl}/mcp/memory/search`,
      {
        query: args.query,
        limit: args.limit || 10,
        metadata_filter: args.metadata_filter
      },
      { headers }
    );
    return response.data;
  }

  private async updateMemory(args: any, headers: any): Promise<any> {
    const response = await axios.put(
      `${config.mcpServerUrl}/mcp/memory/${args.memory_id}`,
      {
        content: args.content,
        metadata: args.metadata
      },
      { headers }
    );
    return response.data;
  }

  private async deleteMemory(args: any, headers: any): Promise<any> {
    const response = await axios.delete(
      `${config.mcpServerUrl}/mcp/memory/${args.memory_id}`,
      { headers }
    );
    return response.data;
  }

  private async getContext(args: any, headers: any): Promise<any> {
    const response = await axios.post(
      `${config.mcpServerUrl}/mcp/context`,
      {
        topic: args.topic,
        depth: args.depth || 1
      },
      { headers }
    );
    return response.data;
  }
}

// Initialize MCP server
async function main() {
  logger.info('Starting Claude Desktop MCP Adapter...');

  // Connect to Redis
  await redis.connect();
  logger.info('Connected to Redis');

  // Create MCP server client
  const mcpClient = new MCPServerClient();

  // Create MCP server
  const server = new Server(
    {
      name: 'sophia-mcp-claude',
      version: '1.0.0'
    },
    {
      capabilities: {
        tools: {}
      }
    }
  );

  // Define available tools
  const tools = [
    {
      name: 'store_memory',
      description: 'Store a memory in the Sophia knowledge base',
      inputSchema: {
        type: 'object',
        properties: {
          content: {
            type: 'string',
            description: 'The content to store'
          },
          metadata: {
            type: 'object',
            description: 'Optional metadata',
            additionalProperties: true
          },
          ttl: {
            type: 'number',
            description: 'Optional TTL in seconds'
          }
        },
        required: ['content']
      }
    },
    {
      name: 'search_memory',
      description: 'Search memories in the Sophia knowledge base',
      inputSchema: {
        type: 'object',
        properties: {
          query: {
            type: 'string',
            description: 'Search query'
          },
          limit: {
            type: 'number',
            description: 'Maximum results (default: 10)'
          },
          metadata_filter: {
            type: 'object',
            description: 'Filter by metadata',
            additionalProperties: true
          }
        },
        required: ['query']
      }
    },
    {
      name: 'update_memory',
      description: 'Update an existing memory',
      inputSchema: {
        type: 'object',
        properties: {
          memory_id: {
            type: 'string',
            description: 'Memory ID to update'
          },
          content: {
            type: 'string',
            description: 'New content'
          },
          metadata: {
            type: 'object',
            description: 'New metadata',
            additionalProperties: true
          }
        },
        required: ['memory_id']
      }
    },
    {
      name: 'delete_memory',
      description: 'Delete a memory',
      inputSchema: {
        type: 'object',
        properties: {
          memory_id: {
            type: 'string',
            description: 'Memory ID to delete'
          }
        },
        required: ['memory_id']
      }
    },
    {
      name: 'get_context',
      description: 'Get contextual information about a topic',
      inputSchema: {
        type: 'object',
        properties: {
          topic: {
            type: 'string',
            description: 'Topic to get context for'
          },
          depth: {
            type: 'number',
            description: 'Context depth (default: 1)'
          }
        },
        required: ['topic']
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
      // Check cache first
      const cacheKey = `claude:${name}:${JSON.stringify(args)}`;
      const cached = await redis.get(cacheKey);

      if (cached) {
        logger.info(`Cache hit for ${name}`);
        return {
          content: [
            {
              type: 'text',
              text: cached
            }
          ]
        };
      }

      // Call MCP server
      const result = await mcpClient.callTool(name, args);

      // Cache result
      await redis.setEx(cacheKey, 300, JSON.stringify(result));

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

  // Start server with stdio transport
  const transport = new StdioServerTransport();
  await server.connect(transport);

  logger.info('Claude Desktop MCP Adapter is running');

  // Handle graceful shutdown
  process.on('SIGINT', async () => {
    logger.info('Shutting down...');
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
