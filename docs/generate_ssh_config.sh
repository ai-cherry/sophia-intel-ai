#!/bin/bash

# 🔧 SOPHIA AI SSH CONFIG GENERATOR
# Generates SSH configuration for Lambda Labs instances

echo "🚀 Generating Sophia AI SSH Configuration..."

# Create SSH directory if it doesn't exist
mkdir -p ~/.ssh

# Backup existing config if it exists
if [ -f ~/.ssh/config ]; then
    echo "📋 Backing up existing SSH config..."
    cp ~/.ssh/config ~/.ssh/config.backup.$(date +%Y%m%d_%H%M%S)
fi

# Generate SSH config
cat >> ~/.ssh/config << 'EOF'

# ========================================
# SOPHIA AI LAMBDA LABS INSTANCES
# ========================================

# Sophia AI Production Instance
Host sophia-production
    HostName 104.171.202.103
    User ubuntu
    IdentityFile ~/.ssh/lambda_labs_key
    ForwardAgent yes
    ServerAliveInterval 60
    ServerAliveCountMax 3
    TCPKeepAlive yes
    ExitOnForwardFailure no
    ControlMaster no
    ControlPersist no
    RequestTTY no
    Compression yes
    ConnectTimeout 30
    StrictHostKeyChecking no

# Sophia AI Development Instance
Host sophia-dev
    HostName 155.248.194.183
    User ubuntu
    IdentityFile ~/.ssh/lambda_labs_key
    ForwardAgent yes
    ServerAliveInterval 60
    ServerAliveCountMax 3
    TCPKeepAlive yes
    ExitOnForwardFailure no
    ControlMaster no
    ControlPersist no
    RequestTTY no
    Compression yes
    ConnectTimeout 30
    StrictHostKeyChecking no

# Sophia AI Core Instance
Host sophia-core
    HostName 192.222.58.232
    User ubuntu
    IdentityFile ~/.ssh/lambda_labs_key
    ForwardAgent yes
    ServerAliveInterval 60
    ServerAliveCountMax 3
    TCPKeepAlive yes
    ExitOnForwardFailure no
    ControlMaster no
    ControlPersist no
    RequestTTY no
    Compression yes
    ConnectTimeout 30
    StrictHostKeyChecking no

# Sophia AI MCP Server Instance
Host sophia-mcp
    HostName 104.171.202.117
    User ubuntu
    IdentityFile ~/.ssh/lambda_labs_key
    ForwardAgent yes
    ServerAliveInterval 60
    ServerAliveCountMax 3
    TCPKeepAlive yes
    ExitOnForwardFailure no
    ControlMaster no
    ControlPersist no
    RequestTTY no
    Compression yes
    ConnectTimeout 30
    StrictHostKeyChecking no

# Sophia AI Data Pipeline Instance
Host sophia-data
    HostName 104.171.202.134
    User ubuntu
    IdentityFile ~/.ssh/lambda_labs_key
    ForwardAgent yes
    ServerAliveInterval 60
    ServerAliveCountMax 3
    TCPKeepAlive yes
    ExitOnForwardFailure no
    ControlMaster no
    ControlPersist no
    RequestTTY no
    Compression yes
    ConnectTimeout 30
    StrictHostKeyChecking no

EOF

echo "✅ SSH configuration added to ~/.ssh/config"

# Set proper permissions
chmod 600 ~/.ssh/config
echo "🔒 Set proper permissions on SSH config"

# Test connectivity
echo "🧪 Testing SSH connectivity..."

for host in sophia-production sophia-dev sophia-core sophia-mcp sophia-data; do
    echo "Testing $host..."
    if ssh -o ConnectTimeout=10 -o BatchMode=yes $host "echo 'Connection successful'" 2>/dev/null; then
        echo "✅ $host: Connected successfully"
    else
        echo "❌ $host: Connection failed"
    fi
done

echo "🎉 SSH configuration setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Ensure lambda_labs_key is in ~/.ssh/ with proper permissions (600)"
echo "2. Test connections manually: ssh sophia-production"
echo "3. Use with Cursor IDE: Remote-SSH: Connect to Host"

