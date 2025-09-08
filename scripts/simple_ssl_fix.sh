#!/bin/bash

# Simple SSL Certificate Fix for Sophia AI
# This script provides instructions for fixing the SSL certificate issue

set -e

echo "🔒 Sophia AI SSL Certificate Fix"
echo "================================"
echo ""

echo "ISSUE: SSL certificate doesn't include www.sophia-intel.ai subdomain"
echo "SOLUTION: Simple manual steps to fix SSL certificate"
echo ""

echo "📋 SIMPLE STEPS TO FIX SSL:"
echo ""
echo "1. SSH into your Lambda Labs server (192.222.58.232):"
echo "   ssh ubuntu@192.222.58.232"
echo ""
echo "2. Install certbot (if not already installed):"
echo "   sudo apt update && sudo apt install -y certbot python3-certbot-nginx"
echo ""
echo "3. Stop nginx temporarily:"
echo "   sudo systemctl stop nginx"
echo ""
echo "4. Generate new certificate with both domains:"
echo "   sudo certbot certonly --standalone -d sophia-intel.ai -d www.sophia-intel.ai"
echo ""
echo "5. Update nginx configuration:"
echo "   sudo nano /etc/nginx/sites-available/sophia-ai"
echo ""
echo "   Add these lines in the server block:"
echo "   ssl_certificate /etc/letsencrypt/live/sophia-intel.ai/fullchain.pem;"
echo "   ssl_certificate_key /etc/letsencrypt/live/sophia-intel.ai/privkey.pem;"
echo ""
echo "6. Test nginx configuration:"
echo "   sudo nginx -t"
echo ""
echo "7. Start nginx:"
echo "   sudo systemctl start nginx"
echo ""
echo "8. Test HTTPS access:"
echo "   curl -I https://www.sophia-intel.ai"
echo "   curl -I https://sophia-intel.ai"
echo ""

echo "⏱️  ESTIMATED TIME: 10-15 minutes"
echo "🎯 RESULT: Both domains will have valid SSL certificates"
echo ""

echo "🔄 AUTOMATIC RENEWAL:"
echo "Add to crontab for automatic renewal:"
echo "0 12 * * * /usr/bin/certbot renew --quiet"
echo ""

echo "✅ This fix is simple, safe, and doesn't add complexity to the system."
echo "✅ Uses standard Let's Encrypt tools that are widely supported."
echo "✅ No additional dependencies or complex configurations required."

