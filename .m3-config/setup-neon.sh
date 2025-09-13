#!/bin/bash
# Neon Setup for M3 Mac (ARM64 Native)
# No x86 emulation bullshit - pure ARM64 performance

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🚀 Neon + PostgreSQL Setup for M3 Mac"
echo "======================================"

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo -e "${RED}❌ Homebrew not found!${NC}"
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH for M1/M2/M3
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
fi

echo -e "${GREEN}✅ Homebrew ready${NC}"

# Install Neon CLI if not present
if ! command -v neonctl &> /dev/null; then
    echo "Installing Neon CLI..."
    brew install neonctl
else
    echo -e "${GREEN}✅ Neon CLI already installed${NC}"
fi

# Install PostgreSQL 17 (ARM64 native)
if ! command -v psql &> /dev/null; then
    echo "Installing PostgreSQL 17 (ARM64 native)..."
    brew install postgresql@17
    
    # Add to PATH
    echo 'export PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH"' >> ~/.zshrc
    export PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH"
else
    echo -e "${GREEN}✅ PostgreSQL already installed${NC}"
    psql --version
fi

# Check if PostgreSQL service should be started
echo ""
read -p "Start PostgreSQL as a service? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    brew services start postgresql@17
    echo -e "${GREEN}✅ PostgreSQL service started${NC}"
fi

# Check Neon authentication
echo ""
echo "Checking Neon authentication..."
if ! neonctl auth status &> /dev/null; then
    echo -e "${YELLOW}Need to authenticate with Neon${NC}"
    echo "Opening browser for authentication..."
    neonctl auth
else
    echo -e "${GREEN}✅ Already authenticated with Neon${NC}"
fi

# Create or list Neon projects
echo ""
echo "Neon Projects:"
neonctl projects list 2>/dev/null || echo "No projects yet"

echo ""
read -p "Create a new Neon project for SOPHIA? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Creating SOPHIA project..."
    PROJECT_OUTPUT=$(neonctl projects create --name sophia-intel-ai --region-id us-east-1)
    PROJECT_ID=$(echo "$PROJECT_OUTPUT" | grep -o 'id: [^ ]*' | cut -d' ' -f2)
    
    echo -e "${GREEN}✅ Project created: $PROJECT_ID${NC}"
    
    # Get connection string
    CONNECTION_STRING=$(neonctl connection-string --project-id "$PROJECT_ID")
    
    # Save to .env
    echo ""
    echo "Updating .env with Neon connection..."
    if [ -f .env ]; then
        # Remove old NEON_URL if exists
        grep -v "^NEON_URL=" .env > .env.tmp && mv .env.tmp .env
        echo "NEON_URL=$CONNECTION_STRING" >> .env
    else
        echo "NEON_URL=$CONNECTION_STRING" > .env
    fi
    
    echo -e "${GREEN}✅ Connection string saved to .env${NC}"
    echo ""
    echo "Connection details:"
    echo "  URL: $CONNECTION_STRING"
    echo ""
    echo "Test connection with:"
    echo "  psql \$NEON_URL"
fi

# Create helper functions
cat > ~/.neon-helpers <<'EOF'
# Neon Helper Functions for M3 Mac

# Quick connect to Neon
neon-connect() {
    if [ -f .env ]; then
        source .env
        psql "$NEON_URL"
    else
        echo "No .env file found"
    fi
}

# List all Neon projects
neon-list() {
    neonctl projects list
}

# Get connection string for a project
neon-url() {
    if [ -z "$1" ]; then
        echo "Usage: neon-url <project-id>"
    else
        neonctl connection-string --project-id "$1"
    fi
}

# Create a new database
neon-create-db() {
    if [ -z "$1" ] || [ -z "$2" ]; then
        echo "Usage: neon-create-db <project-id> <database-name>"
    else
        neonctl databases create --project-id "$1" --name "$2"
    fi
}
EOF

# Add helpers to shell config
if ! grep -q "source ~/.neon-helpers" ~/.zshrc 2>/dev/null; then
    echo "source ~/.neon-helpers" >> ~/.zshrc
    echo -e "${GREEN}✅ Neon helpers added to ~/.zshrc${NC}"
fi

echo ""
echo "======================================"
echo -e "${GREEN}✅ Neon Setup Complete!${NC}"
echo ""
echo "Available commands:"
echo "  neonctl projects list     - List all projects"
echo "  neonctl auth status       - Check authentication"
echo "  psql \$NEON_URL           - Connect to database"
echo "  neon-connect              - Quick connect (uses .env)"
echo ""
echo "PostgreSQL tools (ARM64 native):"
echo "  psql    - PostgreSQL client"
echo "  pg_dump - Database backup"
echo "  createdb - Create database"
echo ""
echo -e "${YELLOW}Restart your terminal or run: source ~/.zshrc${NC}"