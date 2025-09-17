# Workbench UI - Complete Startup Guide

## Repository Setup Instructions for https://github.com/ai-cherry/workbench-ui

This guide will help you initialize and set up your workbench-ui repository from scratch.

---

## 1. Initial Repository Setup

### Step 1: Clone Your Empty Repository
```bash
# Navigate to your workspace directory
cd ~/

# Clone your new repository
git clone https://github.com/ai-cherry/workbench-ui.git
cd workbench-ui
```

### Step 2: Initialize the Project
```bash
# Initialize Next.js project with TypeScript
npx create-next-app@latest . --typescript --tailwind --app --src-dir --import-alias "@/*"

# When prompted:
# ✔ Would you like to use ESLint? … Yes
# ✔ Would you like to use `src/` directory? … Yes
# ✔ Would you like to use App Router? … Yes
# ✔ Would you like to customize the default import alias? … No
```

---

## 2. Essential Files to Create

### 2.1 Package.json (Enhanced)
After initialization, update your package.json:

```json
{
  "name": "workbench-ui",
  "version": "0.1.0",
  "description": "Sophia Intel AI Workbench Frontend UI",
  "author": "AI Cherry",
  "license": "MIT",
  "scripts": {
    "dev": "next dev -p 3000",
    "build": "next build",
    "start": "next start -p 3000",
    "lint": "next lint",
    "test": "jest --watch",
    "test:ci": "jest --ci",
    "type-check": "tsc --noEmit",
    "format": "prettier --write \"**/*.{ts,tsx,js,jsx,json,md}\"",
    "mcp:connect": "node scripts/mcp-connector.js"
  },
  "dependencies": {
    "next": "14.2.3",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "@tanstack/react-query": "^5.28.0",
    "axios": "^1.6.8",
    "zustand": "^4.5.2",
    "zod": "^3.22.4",
    "@radix-ui/themes": "^3.0.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.2.2",
    "lucide-react": "^0.363.0",
    "react-hot-toast": "^2.4.1"
  },
  "devDependencies": {
    "@types/node": "^20.12.7",
    "@types/react": "^18.2.79",
    "@types/react-dom": "^18.2.25",
    "typescript": "^5.4.5",
    "eslint": "^8.57.0",
    "eslint-config-next": "14.2.3",
    "prettier": "^3.2.5",
    "@testing-library/react": "^15.0.2",
    "@testing-library/jest-dom": "^6.4.2",
    "jest": "^29.7.0",
    "jest-environment-jsdom": "^29.7.0",
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.38",
    "tailwindcss": "^3.4.3"
  }
}
```

### 2.2 Project Structure
```bash
workbench-ui/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── layout.tsx          # Root layout
│   │   ├── page.tsx            # Home page
│   │   ├── globals.css         # Global styles
│   │   └── api/               # API routes
│   │       └── mcp/           # MCP proxy endpoints
│   ├── components/             # React components
│   │   ├── ui/                # UI components
│   │   ├── chat/              # Chat interface
│   │   ├── editor/            # Code editor
│   │   └── workspace/         # Workspace components
│   ├── lib/                   # Utility functions
│   │   ├── mcp-client.ts     # MCP client
│   │   ├── api.ts            # API client
│   │   └── utils.ts          # Utilities
│   ├── hooks/                 # Custom React hooks
│   ├── stores/                # Zustand stores
│   └── types/                 # TypeScript types
├── public/                    # Static assets
├── scripts/                   # Build/dev scripts
├── tests/                     # Test files
└── docs/                      # Documentation
```

### 2.3 Environment Configuration (.env.local)
```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# MCP Server Endpoints
NEXT_PUBLIC_MCP_MEMORY_URL=http://localhost:8081
NEXT_PUBLIC_MCP_FILESYSTEM_URL=http://localhost:8082
NEXT_PUBLIC_MCP_ANALYTICS_URL=http://localhost:8083
NEXT_PUBLIC_MCP_GIT_URL=http://localhost:8084
NEXT_PUBLIC_MCP_UNIFIED_URL=http://localhost:8085

# Feature Flags
NEXT_PUBLIC_ENABLE_MCP=true
NEXT_PUBLIC_ENABLE_CHAT=true
NEXT_PUBLIC_ENABLE_EDITOR=true
NEXT_PUBLIC_ENABLE_ANALYTICS=false

# Development
NEXT_PUBLIC_DEBUG=true
```

### 2.4 MCP Client Implementation (src/lib/mcp-client.ts)
```typescript
import axios, { AxiosInstance } from 'axios';

export interface MCPServer {
  name: string;
  url: string;
  enabled: boolean;
}

export class MCPClient {
  private servers: Map<string, AxiosInstance>;
  
  constructor() {
    this.servers = new Map();
    this.initializeServers();
  }
  
  private initializeServers() {
    const serverConfigs: MCPServer[] = [
      {
        name: 'memory',
        url: process.env.NEXT_PUBLIC_MCP_MEMORY_URL || 'http://localhost:8081',
        enabled: true
      },
      {
        name: 'filesystem',
        url: process.env.NEXT_PUBLIC_MCP_FILESYSTEM_URL || 'http://localhost:8082',
        enabled: true
      },
      {
        name: 'git',
        url: process.env.NEXT_PUBLIC_MCP_GIT_URL || 'http://localhost:8084',
        enabled: true
      }
    ];
    
    serverConfigs.forEach(config => {
      if (config.enabled) {
        this.servers.set(config.name, axios.create({
          baseURL: config.url,
          timeout: 30000,
          headers: {
            'Content-Type': 'application/json'
          }
        }));
      }
    });
  }
  
  async callTool(server: string, tool: string, params: any) {
    const client = this.servers.get(server);
    if (!client) {
      throw new Error(`MCP server ${server} not found`);
    }
    
    try {
      const response = await client.post(`/tools/${tool}`, params);
      return response.data;
    } catch (error) {
      console.error(`MCP call failed: ${server}/${tool}`, error);
      throw error;
    }
  }
  
  async getHealth(server: string) {
    const client = this.servers.get(server);
    if (!client) {
      return { status: 'not_configured' };
    }
    
    try {
      const response = await client.get('/health');
      return response.data;
    } catch {
      return { status: 'down' };
    }
  }
}

export const mcpClient = new MCPClient();
```

### 2.5 Main App Layout (src/app/layout.tsx)
```typescript
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Providers } from '@/components/providers';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Sophia Workbench UI',
  description: 'AI-powered development workbench',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
```

### 2.6 Home Page (src/app/page.tsx)
```typescript
'use client';

import { useState, useEffect } from 'react';
import { mcpClient } from '@/lib/mcp-client';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

export default function HomePage() {
  const [mcpStatus, setMcpStatus] = useState<Record<string, any>>({});
  
  useEffect(() => {
    checkMCPServers();
  }, []);
  
  const checkMCPServers = async () => {
    const servers = ['memory', 'filesystem', 'git'];
    const status: Record<string, any> = {};
    
    for (const server of servers) {
      status[server] = await mcpClient.getHealth(server);
    }
    
    setMcpStatus(status);
  };
  
  return (
    <div className="container mx-auto p-8">
      <h1 className="text-4xl font-bold mb-8">Sophia Workbench UI</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">MCP Server Status</h2>
          {Object.entries(mcpStatus).map(([server, status]) => (
            <div key={server} className="flex justify-between mb-2">
              <span>{server}:</span>
              <span className={status.status === 'healthy' ? 'text-green-500' : 'text-red-500'}>
                {status.status || 'checking...'}
              </span>
            </div>
          ))}
        </Card>
        
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
          <div className="space-y-2">
            <Button className="w-full">Open Chat</Button>
            <Button className="w-full">Code Editor</Button>
            <Button className="w-full">View Analytics</Button>
          </div>
        </Card>
        
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
          <p className="text-gray-600">No recent activity</p>
        </Card>
      </div>
    </div>
  );
}
```

### 2.7 Git Configuration (.gitignore)
```
# Dependencies
node_modules/
.pnp/
.pnp.js

# Testing
coverage/
.nyc_output

# Next.js
.next/
out/
build/
dist/

# Production
*.production

# Misc
.DS_Store
*.pem
.vscode/
.idea/

# Debug
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-debug.log*

# Local env files
.env*.local
.env

# Vercel
.vercel

# TypeScript
*.tsbuildinfo
next-env.d.ts
```

---

## 3. Setup Commands

Run these commands in order in your workbench-ui directory:

```bash
# 1. Install dependencies
npm install

# 2. Create the directory structure
mkdir -p src/components/ui src/components/chat src/components/editor src/components/workspace
mkdir -p src/lib src/hooks src/stores src/types
mkdir -p scripts tests docs
mkdir -p src/app/api/mcp

# 3. Create environment file
cp .env.template .env.local
# Edit .env.local with your configuration

# 4. Initialize git (if not already done)
git add .
git commit -m "Initial workbench-ui setup with MCP integration"
git push origin main

# 5. Start development server
npm run dev
```

---

## 4. Integration with Sophia Intel AI

### 4.1 Connect to Backend Services
Ensure sophia-intel-ai services are running:
```bash
cd ~/sophia-intel-ai
./sophia start
```

### 4.2 Verify Connections
Open http://localhost:3000 and check:
- ✅ MCP server status indicators
- ✅ API connection to localhost:8000
- ✅ WebSocket connection established

### 4.3 Configure Cursor/VSCode
In your workbench-ui directory, create `.vscode/settings.json`:
```json
{
  "typescript.tsdk": "node_modules/typescript/lib",
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "tailwindCSS.experimental.classRegex": [
    ["clsx\\(([^)]*)\\)", "(?:'|\"|`)([^']*)(?:'|\"|`)"]
  ]
}
```

---

## 5. Next Steps

1. **Set up authentication**: Implement JWT-based auth
2. **Create chat interface**: Build AI chat component
3. **Add code editor**: Integrate Monaco or CodeMirror
4. **Implement MCP tools**: Create UI for MCP server interactions
5. **Add real-time updates**: WebSocket integration

---

## 6. Troubleshooting

### Common Issues:

**Port 3000 already in use:**
```bash
# Find and kill process
lsof -i :3000
kill -9 <PID>
# Or use different port
npm run dev -- -p 3001
```

**MCP servers not responding:**
```bash
# Check if sophia-intel-ai is running
cd ~/sophia-intel-ai
./sophia status
./sophia start  # if not running
```

**TypeScript errors:**
```bash
npm run type-check
npm install --save-dev @types/node @types/react
```

---

## 7. Development Workflow

### Daily Startup:
```bash
# Terminal 1: Start backend
cd ~/sophia-intel-ai
./sophia start

# Terminal 2: Start frontend
cd ~/workbench-ui
npm run dev

# Terminal 3: Run tests
cd ~/workbench-ui
npm test
```

### Before Committing:
```bash
npm run lint
npm run type-check
npm run format
npm test
```

---

*Ready to start building! Your workbench-ui is now configured to work with Sophia Intel AI.*