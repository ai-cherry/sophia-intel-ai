#!/bin/bash
set -euo pipefail

# Complete Workbench UI Separation Script
# This script finishes the extraction and creates the new repository

echo "🚀 Completing Workbench UI Separation..."
echo "======================================"

# Variables
NEW_REPO="ai-cherry/sophia-workbench-ui"
WORKTREE_DIR="../worktrees/workbench-ui"
CURRENT_DIR=$(pwd)

# Step 1: Verify we're in the right place
if [ ! -d ".git" ]; then
  echo "❌ Error: Must run from sophia-intel-ai repository root"
  exit 1
fi

# Step 2: Check if worktree exists
if [ ! -d "$WORKTREE_DIR" ]; then
  echo "❌ Error: Worktree not found at $WORKTREE_DIR"
  echo "Run: bash scripts/extract_workbench_repo.sh first"
  exit 1
fi

echo "✅ Worktree found at $WORKTREE_DIR"

# Step 3: Navigate to worktree and check its contents
cd "$WORKTREE_DIR"
echo "📁 Contents of workbench-ui worktree:"
ls -la

# Step 4: Fix path references in server.ts if it exists
if [ -f "src/server.ts" ]; then
  echo "🔧 Fixing config paths in src/server.ts..."
  # Fix the config paths to be repo-root relative
  sed -i.bak "s|'workbench-ui', 'config'|'config'|g" src/server.ts || true
  rm -f src/server.ts.bak
  echo "✅ Paths fixed"
fi

# Step 5: Initialize git if needed and set up proper structure
if [ ! -f "package.json" ]; then
  echo "📦 Creating package.json..."
  cat > package.json << 'EOF'
{
  "name": "@sophia-intel/workbench-ui",
  "version": "1.0.0",
  "description": "Workbench UI for Sophia Intel AI System",
  "main": "dist/server.js",
  "scripts": {
    "dev": "tsx watch src/server.ts",
    "build": "tsc",
    "start": "node dist/server.js",
    "test": "jest",
    "lint": "eslint src/"
  },
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "dotenv": "^16.3.1",
    "axios": "^1.6.2",
    "yaml": "^2.3.4"
  },
  "devDependencies": {
    "@types/express": "^4.17.21",
    "@types/node": "^20.10.5",
    "typescript": "^5.3.3",
    "tsx": "^4.6.2",
    "@typescript-eslint/eslint-plugin": "^6.15.0",
    "@typescript-eslint/parser": "^6.15.0",
    "eslint": "^8.56.0",
    "jest": "^29.7.0",
    "@types/jest": "^29.5.11"
  }
}
EOF
fi

# Step 6: Create README if it doesn't exist
if [ ! -f "README.md" ]; then
  echo "📝 Creating README.md..."
  cat > README.md << 'EOF'
# Sophia Workbench UI

Separated backend service for the Sophia Intel AI Workbench interface.

## Quick Start

```bash
# Install dependencies
npm install

# Set environment variables
export REPO_ENV_MASTER_PATH=../sophia-intel-ai/.env.master
export PORTKEY_API_KEY=your-key-here

# Start development server
npm run dev
```

## Environment Variables

- `REPO_ENV_MASTER_PATH`: Path to main repo's .env.master
- `MCP_MEMORY_URL`: Memory server URL (default: http://localhost:8081)
- `MCP_FILESYSTEM_URL`: Filesystem server URL (default: http://localhost:8082)
- `MCP_GIT_URL`: Git server URL (default: http://localhost:8084)
- `MCP_VECTOR_URL`: Vector server URL (default: http://localhost:8085)

## Architecture

This service provides backend APIs for:
- Policy enforcement
- Git operations
- Model configuration
- AI provider routing

## Development

The service runs on port 3200 by default.

```bash
# Build for production
npm run build

# Run production build
npm start
```
EOF
fi

# Step 7: Create .gitignore
if [ ! -f ".gitignore" ]; then
  echo "📝 Creating .gitignore..."
  cat > .gitignore << 'EOF'
node_modules/
dist/
*.log
.env
.env.local
.env.master
.DS_Store
coverage/
*.bak
EOF
fi

# Step 8: Commit changes locally
echo "💾 Committing local changes..."
git add -A
git commit -m "chore: prepare for standalone repository" || echo "No changes to commit"

# Step 9: Print instructions for manual steps
echo ""
echo "======================================"
echo "✅ PREPARATION COMPLETE!"
echo "======================================"
echo ""
echo "Now run these commands to create and push to GitHub:"
echo ""
echo "1️⃣  Create the GitHub repository (using GitHub CLI):"
echo "    gh repo create $NEW_REPO --private --confirm"
echo ""
echo "2️⃣  Set up the remote and push:"
echo "    cd $WORKTREE_DIR"
echo "    git remote remove origin 2>/dev/null || true"
echo "    git remote add origin git@github.com:$NEW_REPO.git"
echo "    git push -u origin HEAD:main"
echo ""
echo "3️⃣  Back in the main repo, push the removal commit:"
echo "    cd $CURRENT_DIR"
echo "    git push origin HEAD"
echo ""
echo "4️⃣  Test the separated workbench:"
echo "    cd $WORKTREE_DIR"
echo "    npm install"
echo "    REPO_ENV_MASTER_PATH=$CURRENT_DIR/.env.master npm run dev"
echo ""
echo "======================================"
echo "🔐 SECURITY REMINDER:"
echo "Please IMMEDIATELY revoke the GitHub token you shared!"
echo "Never paste tokens in chat - use 'gh auth login' instead"
echo "======================================"

# Return to original directory
cd "$CURRENT_DIR"