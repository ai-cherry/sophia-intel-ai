#!/bin/bash
# DNS Configuration Script for sophia-intel.ai
# This script provides the exact DNS records needed in NameCheap

set -e

echo "🌐 DNS Configuration for sophia-intel.ai"
echo "========================================"
echo ""

echo "📋 REQUIRED NAMECHEAP DNS RECORDS:"
echo ""

echo "🔹 A RECORDS (Root Domain):"
echo "Type: A | Host: @ | Value: 104.21.58.123 | TTL: 300 | Proxied: Yes (CloudFlare)"
echo "Type: A | Host: @ | Value: 172.67.182.45 | TTL: 300 | Proxied: Yes (CloudFlare)"
echo ""

echo "🔹 CNAME RECORDS (Subdomains):"
echo "Type: CNAME | Host: www | Value: sophia-intel.ai | TTL: 300 | Proxied: Yes"
echo "Type: CNAME | Host: api | Value: api-lb.sophia-intel.ai | TTL: 300 | Proxied: Yes"
echo "Type: CNAME | Host: chat | Value: chat-lb.sophia-intel.ai | TTL: 300 | Proxied: Yes"
echo "Type: CNAME | Host: dashboard | Value: dash-lb.sophia-intel.ai | TTL: 300 | Proxied: Yes"
echo "Type: CNAME | Host: agents | Value: agents-lb.sophia-intel.ai | TTL: 300 | Proxied: Yes"
echo "Type: CNAME | Host: docs | Value: docs-lb.sophia-intel.ai | TTL: 300 | Proxied: Yes"
echo "Type: CNAME | Host: status | Value: status-lb.sophia-intel.ai | TTL: 300 | Proxied: Yes"
echo ""

echo "🔹 LOAD BALANCER CNAMES (Point to Lambda Labs):"
echo "Type: CNAME | Host: api-lb | Value: 192.222.58.232 | TTL: 300 | Proxied: No"
echo "Type: CNAME | Host: chat-lb | Value: 192.222.58.232 | TTL: 300 | Proxied: No"
echo "Type: CNAME | Host: dash-lb | Value: 192.222.58.232 | TTL: 300 | Proxied: No"
echo "Type: CNAME | Host: agents-lb | Value: 192.222.58.232 | TTL: 300 | Proxied: No"
echo "Type: CNAME | Host: docs-lb | Value: 192.222.58.232 | TTL: 300 | Proxied: No"
echo "Type: CNAME | Host: status-lb | Value: 192.222.58.232 | TTL: 300 | Proxied: No"
echo ""

echo "🔹 SECURITY RECORDS:"
echo "Type: TXT | Host: @ | Value: v=spf1 include:_spf.google.com ~all | TTL: 300"
echo "Type: CAA | Host: @ | Value: 0 issue \"letsencrypt.org\" | TTL: 300"
echo "Type: CAA | Host: @ | Value: 0 issue \"digicert.com\" | TTL: 300"
echo ""

echo "⚠️  IMPORTANT NOTES:"
echo "1. Remove any existing conflicting DNS records first"
echo "2. CloudFlare proxying (orange cloud) should be ENABLED for main subdomains"
echo "3. CloudFlare proxying should be DISABLED for load balancer records"
echo "4. DNS propagation may take 5-15 minutes"
echo ""

echo "🔍 VERIFICATION COMMANDS:"
echo "After updating DNS, run these commands to verify:"
echo ""
echo "# Check root domain"
echo "dig sophia-intel.ai A"
echo ""
echo "# Check subdomains"
echo "for subdomain in www api chat dashboard agents docs status; do"
echo "    echo \"Checking \$subdomain.sophia-intel.ai...\""
echo "    dig \$subdomain.sophia-intel.ai A"
echo "done"
echo ""

echo "🚀 NEXT STEPS:"
echo "1. Update NameCheap DNS with the records above"
echo "2. Wait 5-15 minutes for DNS propagation"
echo "3. Run verification commands"
echo "4. Deploy CloudFlare configuration"
echo "5. Deploy Lambda Labs services"
echo ""

# Function to test DNS resolution
sophia_dns_resolution() {
    echo "🧪 Testing DNS Resolution..."
    echo ""
    
    domains=(
        "sophia-intel.ai"
        "www.sophia-intel.ai"
        "api.sophia-intel.ai"
        "chat.sophia-intel.ai"
        "dashboard.sophia-intel.ai"
        "agents.sophia-intel.ai"
        "docs.sophia-intel.ai"
        "status.sophia-intel.ai"
    )
    
    for domain in "${domains[@]}"; do
        echo -n "Testing $domain... "
        if dig +short "$domain" A | grep -q .; then
            echo "✅ Resolved"
        else
            echo "❌ Not resolved"
        fi
    done
    echo ""
}

# Function to test SSL certificates
sophia_ssl_certificates() {
    echo "🔒 Testing SSL Certificates..."
    echo ""
    
    domains=(
        "www.sophia-intel.ai"
        "api.sophia-intel.ai"
        "chat.sophia-intel.ai"
        "dashboard.sophia-intel.ai"
    )
    
    for domain in "${domains[@]}"; do
        echo -n "Testing SSL for $domain... "
        if timeout 10 openssl s_client -connect "$domain:443" -servername "$domain" </dev/null 2>/dev/null | grep -q "Verify return code: 0"; then
            echo "✅ Valid SSL"
        else
            echo "❌ SSL issue"
        fi
    done
    echo ""
}

# Function to test service endpoints
sophia_service_endpoints() {
    echo "🔗 Testing Service Endpoints..."
    echo ""
    
    endpoints=(
        "https://www.sophia-intel.ai/health"
        "http://104.171.202.103:8080/api/health"
        "https://chat.sophia-intel.ai/health"
        "https://dashboard.sophia-intel.ai/health"
    )
    
    for endpoint in "${endpoints[@]}"; do
        echo -n "Testing $endpoint... "
        if curl -s -o /dev/null -w "%{http_code}" "$endpoint" | grep -q "200"; then
            echo "✅ Responding"
        else
            echo "❌ Not responding"
        fi
    done
    echo ""
}

# Main execution
case "${1:-help}" in
    "test-dns")
        sophia_dns_resolution
        ;;
    "test-ssl")
        sophia_ssl_certificates
        ;;
    "test-endpoints")
        sophia_service_endpoints
        ;;
    "test-all")
        sophia_dns_resolution
        sophia_ssl_certificates
        sophia_service_endpoints
        ;;
    "help"|*)
        echo "Usage: $0 [test-dns|test-ssl|test-endpoints|test-all]"
        echo ""
        echo "Commands:"
        echo "  test-dns       Test DNS resolution for all domains"
        echo "  test-ssl       Test SSL certificates for all domains"
        echo "  test-endpoints Test service endpoint availability"
        echo "  test-all       Run all tests"
        echo "  help           Show this help message"
        ;;
esac

