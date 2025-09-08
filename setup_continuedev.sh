#!/bin/bash

echo "🚀 Setting up Continue.dev with MCP Memory integration..."

# Create .continue directory if it doesn't exist
mkdir -p ~/.continue

# Create config.json with custom MCP integration
cat > ~/.continue/config.json << 'EOF'
{
  "$schema": "https://continue.dev/config.schema.json",
  "models": {
    "claude-3-5-sonnet": {
      "title": "Claude 3.5 Sonnet",
      "provider": "anthropic",
      "model": "claude-3-5-sonnet-20240620"
    },
    "claude-3-opus": {
      "title": "Claude 3 Opus",
      "provider": "anthropic",
      "model": "claude-3-opus-20240229"
    },
    "gpt-4o": {
      "title": "GPT-4o",
      "provider": "openai",
      "model": "gpt-4o"
    },
    "sophia-memory": {
      "title": "Sophia MCP Memory",
      "provider": "openai",
      "model": "gpt-4o",
      "apiKey": "${OPENAI_API_KEY}",
      "contextConfig": {
        "contextProvider": "custom",
        "customContextProviderPath": "/workspace/continue_plugins/sophia_mcp.js"
      }
    }
  },
  "defaultModel": "claude-3-5-sonnet",
  "newConversationMode": "automatic",
  "completionOptions": {
    "maxTokens": 8000
  },
  "defaultContextProviders": {
    "web": "none",
    "retrieval": "default"
  }
}
EOF

echo "✅ Created Continue.dev configuration with MCP Memory integration"

# Create plugins directory
mkdir -p /workspace/continue_plugins

# Create MCP memory integration plugin
cat > /workspace/continue_plugins/sophia_mcp.js << 'EOF'
/**
 * Sophia MCP Memory Integration for Continue.dev
 */

const http = require('http');

class SophiaMCPContextProvider {
  constructor() {
    this.mcpBaseUrl = "http://localhost:8001";
  }

  /**
   * Get context from MCP Memory Server
   */
  async getContext(options) {
    // Get agent ID and conversation ID
    const agentId = "continue-dev";
    const conversationId = options.input.conversationId || "default";
    
    try {
      // Fetch previous context
      const contextResponse = await this.fetchFromMCP(`/context/${agentId}/${conversationId}`);
      
      // Create new context if this is a new conversation
      if (!contextResponse || contextResponse.status === "not_found") {
        return { 
          contextItems: [], 
          responseText: "No previous context found. Starting a new conversation."
        };
      }
      
      // Extract context information
      const contextData = contextResponse.content || {};
      const contextItems = contextData.contextItems || [];
      
      return {
        contextItems,
        responseText: `Retrieved ${contextItems.length} context items from MCP memory.`
      };
    } catch (error) {
      console.error("Error retrieving context from MCP:", error);
      return { 
        contextItems: [], 
        responseText: "Error retrieving context from MCP server."
      };
    }
  }

  /**
   * Store context in MCP Memory Server
   */
  async storeContext(options, contextItems) {
    // Get agent ID and conversation ID
    const agentId = "continue-dev";
    const conversationId = options.input.conversationId || "default";
    
    try {
      // Create context payload
      const contextData = {
        contextItems,
        timestamp: new Date().toISOString(),
        metadata: {
          userQuery: options.input.query,
          modelId: options.input.modelId
        }
      };
      
      // Store in MCP
      await this.postToMCP("/context/store", {
        agent_id: agentId,
        context_type: conversationId,
        content: contextData
      });
      
      return true;
    } catch (error) {
      console.error("Error storing context in MCP:", error);
      return false;
    }
  }

  /**
   * Fetch data from MCP Memory Server
   */
  async fetchFromMCP(endpoint) {
    return new Promise((resolve, reject) => {
      http.get(`${this.mcpBaseUrl}${endpoint}`, (res) => {
        let data = '';
        res.on('data', (chunk) => {
          data += chunk;
        });
        res.on('end', () => {
          try {
            resolve(JSON.parse(data));
          } catch (e) {
            reject(e);
          }
        });
      }).on('error', reject);
    });
  }

  /**
   * Post data to MCP Memory Server
   */
  async postToMCP(endpoint, payload) {
    return new Promise((resolve, reject) => {
      const data = JSON.stringify(payload);
      const options = {
        hostname: 'localhost',
        port: 8001,
        path: endpoint,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': data.length
        }
      };

      const req = http.request(options, (res) => {
        let responseData = '';
        res.on('data', (chunk) => {
          responseData += chunk;
        });
        res.on('end', () => {
          try {
            resolve(JSON.parse(responseData));
          } catch (e) {
            reject(e);
          }
        });
      });

      req.on('error', reject);
      req.write(data);
      req.end();
    });
  }
}

// Export the provider
module.exports = {
  SophiaMCPContextProvider
};
EOF

echo "✅ Created Sophia MCP integration plugin for Continue.dev"

# Install Continue.dev extension if VS Code CLI is available
if command -v code &> /dev/null; then
    echo "🔍 Installing Continue.dev extension..."
    code --install-extension continue.continue || echo "⚠️ Could not install Continue.dev extension automatically"
else
    echo "⚠️ VS Code CLI not available. Please install Continue.dev extension manually."
    echo "   Install from: https://marketplace.visualstudio.com/items?itemName=continue.continue"
fi

echo "🎉 Continue.dev setup complete!"
echo ""
echo "To use Continue.dev with MCP Memory:"
echo "1. Start the MCP Memory Server with ./start_essential_services.sh"
echo "2. Open VS Code and use the Continue.dev extension"
echo "3. Select 'Sophia MCP Memory' as your model in Continue.dev"
