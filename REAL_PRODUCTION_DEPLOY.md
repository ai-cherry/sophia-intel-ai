# REAL Production Deployment - www.sophia-intel.ai

## Server Information
- **Domain**: www.sophia-intel.ai
- **Server IP**: 104.171.202.107
- **DNS**: Managed via DNSimple (Account: 162809)

## Prerequisites on Production Server

SSH into your production server and install required packages:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install core packages
sudo apt install -y nginx python3 python3-pip python3-venv nodejs npm git curl

# Install Docker (optional, for containerized deployment)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

## Method 1: Direct Deployment (Recommended)

### 1. Clone Repository on Production Server

```bash
cd /opt
sudo git clone https://github.com/ai-cherry/sophia-intel.git
sudo chown -R $USER:$USER /opt/sophia-intel
cd /opt/sophia-intel
```

### 2. Setup Python Backend

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Set environment variables
sudo tee /etc/environment << EOF
LAMBDA_API_KEY=your-actual-lambda-key
OPENAI_API_KEY=your-openai-key
PORT=5000
HOST=127.0.0.1
EOF
```

### 3. Build and Setup Frontend

```bash
cd /opt/sophia-intel/apps/dashboard

# Install Node.js dependencies
npm install

# Build for production
npm run build

# Create web directory
sudo mkdir -p /var/www/sophia-intel
sudo cp -r dist/* /var/www/sophia-intel/
sudo chown -R www-data:www-data /var/www/sophia-intel
```

### 4. Configure Nginx

```bash
sudo tee /etc/nginx/sites-available/sophia-intel << 'EOF'
server {
    listen 80;
    server_name sophia-intel.ai www.sophia-intel.ai;

    # Frontend
    location / {
        root /var/www/sophia-intel;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health endpoint
    location /health {
        proxy_pass http://127.0.0.1:5000/health;
    }

    # WebSocket for chat
    location /ws {
        proxy_pass http://127.0.0.1:5000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/sophia-intel /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

### 5. Create Backend Service

```bash
sudo tee /etc/systemd/system/sophia-intel.service << 'EOF'
[Unit]
Description=SOPHIA Intel Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/sophia-intel
Environment=LAMBDA_API_KEY=your-actual-lambda-key
Environment=OPENAI_API_KEY=your-openai-key
Environment=PORT=5000
Environment=HOST=127.0.0.1
ExecStart=/opt/sophia-intel/venv/bin/python -m uvicorn backend.scalable_main:app --host 127.0.0.1 --port 5000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Start service
sudo systemctl daemon-reload
sudo systemctl enable sophia-intel
sudo systemctl start sophia-intel
```

### 6. Setup SSL Certificate

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d sophia-intel.ai -d www.sophia-intel.ai --email your-email@domain.com --agree-tos --non-interactive
```

## Method 2: Docker Deployment

### 1. Create Docker Compose

```bash
cd /opt/sophia-intel

cat > docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    environment:
      - LAMBDA_API_KEY=${LAMBDA_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - PORT=5000
    ports:
      - "127.0.0.1:5000:5000"
    restart: unless-stopped

  frontend:
    build:
      context: ./apps/dashboard
      dockerfile: Dockerfile
    ports:
      - "127.0.0.1:3000:80"
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - /etc/letsencrypt:/etc/letsencrypt
    depends_on:
      - backend
      - frontend
    restart: unless-stopped
EOF
```

### 2. Deploy with Docker

```bash
# Set environment variables
export LAMBDA_API_KEY="your-actual-lambda-key"
export OPENAI_API_KEY="your-openai-key"

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

## Verification

### 1. Check Services

```bash
# Check backend service
sudo systemctl status sophia-intel

# Check Nginx
sudo systemctl status nginx

# Check logs
sudo journalctl -u sophia-intel -f
```

### 2. Test Endpoints

```bash
# Health check
curl http://localhost:5000/health
curl https://www.sophia-intel.ai/health

# Frontend
curl -I https://www.sophia-intel.ai

# API
curl https://www.sophia-intel.ai/api/health
```

### 3. Browser Testing

Open in browser:
- https://www.sophia-intel.ai (main dashboard)
- https://www.sophia-intel.ai/health (API health)

## Monitoring and Maintenance

### 1. Log Monitoring

```bash
# Backend logs
sudo journalctl -u sophia-intel -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 2. Updates

```bash
cd /opt/sophia-intel
git pull origin main

# Rebuild frontend
cd apps/dashboard
npm run build
sudo cp -r dist/* /var/www/sophia-intel/

# Restart backend
sudo systemctl restart sophia-intel
```

### 3. SSL Renewal

```bash
# Test renewal
sudo certbot renew --dry-run

# Certbot auto-renewal is handled by systemd timer
sudo systemctl status certbot.timer
```

## Troubleshooting

### Common Issues

1. **502 Bad Gateway**: Backend service not running
   ```bash
   sudo systemctl start sophia-intel
   sudo systemctl status sophia-intel
   ```

2. **404 Not Found**: Nginx configuration issue
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

3. **SSL Issues**: Certificate problems
   ```bash
   sudo certbot certificates
   sudo certbot renew
   ```

### Performance Tuning

```bash
# Nginx worker processes
sudo sed -i 's/worker_processes auto;/worker_processes 4;/' /etc/nginx/nginx.conf

# Backend workers (in systemd service)
ExecStart=/opt/sophia-intel/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 backend.scalable_main:app
```

## Security

### 1. Firewall

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. Environment Variables

Store sensitive data in `/etc/environment` or use a secrets management system.

### 3. Regular Updates

```bash
# System updates
sudo apt update && sudo apt upgrade

# Application updates
cd /opt/sophia-intel && git pull origin main
```

---

**This deployment will make SOPHIA Intel live at https://www.sophia-intel.ai with proper SSL, monitoring, and production-grade configuration.**

