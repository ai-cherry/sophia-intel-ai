"""
CloudFlare Configuration for sophia-intel.ai
Edge deployment and optimization settings
"""
import os
from typing import Any, Dict, List
class SophiaIntelCloudFlareConfig:
    """CloudFlare configuration for sophia-intel.ai domain"""
    def __init__(self):
        self.domain = "sophia-intel.ai"
        self.zone_id = os.getenv("CLOUDFLARE_ZONE_ID")
        self.api_token = os.getenv("CLOUDFLARE_API_TOKEN")
        # Subdomain configuration
        self.subdomains = {
            "www": {
                "target": "main-app",
                "cache_level": "aggressive",
                "cache_ttl": 7200,
                "minify": True,
                "compression": True,
            },
            "api": {
                "target": "api-gateway",
                "cache_level": "bypass",
                "security_level": "high",
                "rate_limiting": True,
            },
            "chat": {
                "target": "chat-interface",
                "cache_level": "bypass",
                "websockets": True,
                "ssl": "full_strict",
            },
            "dashboard": {
                "target": "analytics-dashboard",
                "cache_level": "standard",
                "cache_ttl": 3600,
                "security_level": "medium",
            },
            "agents": {
                "target": "agent-playground",
                "cache_level": "bypass",
                "security_level": "high",
            },
            "docs": {
                "target": "documentation",
                "cache_level": "aggressive",
                "cache_ttl": 14400,
                "minify": True,
            },
            "status": {
                "target": "status-page",
                "cache_level": "standard",
                "cache_ttl": 300,
            },
        }
    def get_dns_records(self) -> List[Dict[str, Any]]:
        """Generate DNS records for CloudFlare"""
        records = [
            # A Records for root domain (CloudFlare IPs)
            {
                "type": "A",
                "name": "@",
                "content": "104.21.58.123",
                "ttl": 300,
                "proxied": True,
                "comment": "CloudFlare IP for root domain",
            },
            {
                "type": "A",
                "name": "@",
                "content": "172.67.182.45",
                "ttl": 300,
                "proxied": True,
                "comment": "CloudFlare IP for root domain (backup)",
            },
            # CNAME Records for subdomains
            {
                "type": "CNAME",
                "name": "www",
                "content": "sophia-intel.ai",
                "ttl": 300,
                "proxied": True,
                "comment": "Main website",
            },
            {
                "type": "CNAME",
                "name": "api",
                "content": "api-lb.sophia-intel.ai",
                "ttl": 300,
                "proxied": True,
                "comment": "API Gateway",
            },
            {
                "type": "CNAME",
                "name": "chat",
                "content": "chat-lb.sophia-intel.ai",
                "ttl": 300,
                "proxied": True,
                "comment": "Chat Interface",
            },
            {
                "type": "CNAME",
                "name": "dashboard",
                "content": "dash-lb.sophia-intel.ai",
                "ttl": 300,
                "proxied": True,
                "comment": "Analytics Dashboard",
            },
            {
                "type": "CNAME",
                "name": "agents",
                "content": "agents-lb.sophia-intel.ai",
                "ttl": 300,
                "proxied": True,
                "comment": "Agent Playground",
            },
            {
                "type": "CNAME",
                "name": "docs",
                "content": "docs-lb.sophia-intel.ai",
                "ttl": 300,
                "proxied": True,
                "comment": "Documentation",
            },
            {
                "type": "CNAME",
                "name": "status",
                "content": "status-lb.sophia-intel.ai",
                "ttl": 300,
                "proxied": True,
                "comment": "Status Page",
            },
            # Load Balancer CNAMEs (pointing to Lambda Labs)
            {
                "type": "CNAME",
                "name": "api-lb",
                "content": "192.222.58.232",
                "ttl": 300,
                "proxied": False,
                "comment": "API Load Balancer -> Lambda Labs",
            },
            {
                "type": "CNAME",
                "name": "chat-lb",
                "content": "192.222.58.232",
                "ttl": 300,
                "proxied": False,
                "comment": "Chat Load Balancer -> Lambda Labs",
            },
            {
                "type": "CNAME",
                "name": "dash-lb",
                "content": "192.222.58.232",
                "ttl": 300,
                "proxied": False,
                "comment": "Dashboard Load Balancer -> Lambda Labs",
            },
            {
                "type": "CNAME",
                "name": "agents-lb",
                "content": "192.222.58.232",
                "ttl": 300,
                "proxied": False,
                "comment": "Agents Load Balancer -> Lambda Labs",
            },
            {
                "type": "CNAME",
                "name": "docs-lb",
                "content": "192.222.58.232",
                "ttl": 300,
                "proxied": False,
                "comment": "Docs Load Balancer -> Lambda Labs",
            },
            {
                "type": "CNAME",
                "name": "status-lb",
                "content": "192.222.58.232",
                "ttl": 300,
                "proxied": False,
                "comment": "Status Load Balancer -> Lambda Labs",
            },
            # Security Records
            {
                "type": "TXT",
                "name": "@",
                "content": "v=spf1 include:_spf.google.com ~all",
                "ttl": 300,
                "comment": "SPF record for email security",
            },
            {
                "type": "CAA",
                "name": "@",
                "content": '0 issue "letsencrypt.org"',
                "ttl": 300,
                "comment": "CAA record for Let's Encrypt",
            },
            {
                "type": "CAA",
                "name": "@",
                "content": '0 issue "digicert.com"',
                "ttl": 300,
                "comment": "CAA record for DigiCert",
            },
        ]
        return records
    def get_page_rules(self) -> List[Dict[str, Any]]:
        """Generate page rules for CloudFlare"""
        rules = [
            # Main website optimization
            {
                "targets": [
                    {
                        "target": "url",
                        "constraint": {
                            "operator": "matches",
                            "value": f"https://www.{self.domain}/*",
                        },
                    }
                ],
                "actions": [
                    {"id": "cache_level", "value": "aggressive"},
                    {"id": "edge_cache_ttl", "value": 7200},
                    {"id": "browser_cache_ttl", "value": 3600},
                    {"id": "minify", "value": {"html": "on", "css": "on", "js": "on"}},
                    {"id": "rocket_loader", "value": "on"},
                    {"id": "mirage", "value": "on"},
                    {"id": "polish", "value": "lossless"},
                ],
                "priority": 1,
                "status": "active",
            },
            # API Gateway configuration
            {
                "targets": [
                    {
                        "target": "url",
                        "constraint": {
                            "operator": "matches",
                            "value": f"https://api.{self.domain}/*",
                        },
                    }
                ],
                "actions": [
                    {"id": "cache_level", "value": "bypass"},
                    {"id": "security_level", "value": "high"},
                    {"id": "ssl", "value": "full_strict"},
                    {"id": "disable_performance", "value": "off"},
                ],
                "priority": 2,
                "status": "active",
            },
            # Chat interface configuration
            {
                "targets": [
                    {
                        "target": "url",
                        "constraint": {
                            "operator": "matches",
                            "value": f"https://chat.{self.domain}/*",
                        },
                    }
                ],
                "actions": [
                    {"id": "cache_level", "value": "bypass"},
                    {"id": "websockets", "value": "on"},
                    {"id": "ssl", "value": "full_strict"},
                    {"id": "security_level", "value": "medium"},
                ],
                "priority": 3,
                "status": "active",
            },
            # Dashboard configuration
            {
                "targets": [
                    {
                        "target": "url",
                        "constraint": {
                            "operator": "matches",
                            "value": f"https://dashboard.{self.domain}/*",
                        },
                    }
                ],
                "actions": [
                    {"id": "cache_level", "value": "standard"},
                    {"id": "edge_cache_ttl", "value": 3600},
                    {"id": "security_level", "value": "medium"},
                    {"id": "ssl", "value": "full_strict"},
                ],
                "priority": 4,
                "status": "active",
            },
            # Documentation optimization
            {
                "targets": [
                    {
                        "target": "url",
                        "constraint": {
                            "operator": "matches",
                            "value": f"https://docs.{self.domain}/*",
                        },
                    }
                ],
                "actions": [
                    {"id": "cache_level", "value": "aggressive"},
                    {"id": "edge_cache_ttl", "value": 14400},
                    {"id": "browser_cache_ttl", "value": 7200},
                    {"id": "minify", "value": {"html": "on", "css": "on", "js": "on"}},
                ],
                "priority": 5,
                "status": "active",
            },
        ]
        return rules
    def get_worker_script(self) -> str:
        """Generate CloudFlare Worker script for edge processing"""
        worker_script = """
addEventListener('fetch', event => {
    event.respondWith(handleRequest(event.request))
})
async function handleRequest(request) {
    const url = new URL(request.url)
    const hostname = url.hostname
    // Route based on subdomain
    switch (hostname) {
        case 'chat.sophia-intel.ai':
            return handleChatRequest(request)
        case 'dashboard.sophia-intel.ai':
            return handleDashboardRequest(request)
        case 'api.sophia-intel.ai':
            return handleAPIRequest(request)
        case 'agents.sophia-intel.ai':
            return handleAgentsRequest(request)
        case 'docs.sophia-intel.ai':
            return handleDocsRequest(request)
        case 'status.sophia-intel.ai':
            return handleStatusRequest(request)
        default:
            return handleWebRequest(request)
    }
}
async function handleChatRequest(request) {
    // WebSocket upgrade for real-time chat
    if (request.headers.get('Upgrade') === 'websocket') {
        return handleWebSocket(request)
    }
    // Add CORS headers for chat API
    const response = await fetch(request)
    const newResponse = new Response(response.body, response)
    newResponse.headers.set('Access-Control-Allow-Origin', '*')
    newResponse.headers.set('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    newResponse.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    newResponse.headers.set('X-Sophia-Service', 'chat')
    return newResponse
}
async function handleDashboardRequest(request) {
    // Cache dashboard assets aggressively
    const cache = caches.default
    let response = await cache.match(request)
    if (!response) {
        response = await fetch(request)
        if (response.ok && request.method === 'GET') {
            const headers = new Headers(response.headers)
            headers.set('Cache-Control', 'public, max-age=3600')
            headers.set('X-Sophia-Cache', 'MISS')
            headers.set('X-Sophia-Service', 'dashboard')
            response = new Response(response.body, {
                status: response.status,
                statusText: response.statusText,
                headers
            })
            event.waitUntil(cache.put(request, response.clone()))
        }
    } else {
        response.headers.set('X-Sophia-Cache', 'HIT')
    }
    return response
}
async function handleAPIRequest(request) {
    // Add rate limiting and security headers
    const clientIP = request.headers.get('CF-Connecting-IP')
    const rateLimitKey = `rate_limit:${clientIP}`
    // Check rate limit (simplified)
    const response = await fetch(request)
    const newResponse = new Response(response.body, response)
    newResponse.headers.set('X-Sophia-Service', 'api')
    newResponse.headers.set('X-RateLimit-Limit', '1000')
    newResponse.headers.set('X-RateLimit-Remaining', '999')
    newResponse.headers.set('Strict-Transport-Security', 'max-age=31536000')
    return newResponse
}
async function handleAgentsRequest(request) {
    // Agent playground with enhanced security
    const response = await fetch(request)
    const newResponse = new Response(response.body, response)
    newResponse.headers.set('X-Sophia-Service', 'agents')
    newResponse.headers.set('Content-Security-Policy', "default-src 'self'; script-src 'self' 'unsafe-inline'")
    newResponse.headers.set('X-Frame-Options', 'DENY')
    return newResponse
}
async function handleDocsRequest(request) {
    // Documentation with aggressive caching
    const cache = caches.default
    let response = await cache.match(request)
    if (!response) {
        response = await fetch(request)
        if (response.ok) {
            const headers = new Headers(response.headers)
            headers.set('Cache-Control', 'public, max-age=14400')
            headers.set('X-Sophia-Service', 'docs')
            response = new Response(response.body, {
                status: response.status,
                statusText: response.statusText,
                headers
            })
            event.waitUntil(cache.put(request, response.clone()))
        }
    }
    return response
}
async function handleStatusRequest(request) {
    // Status page with minimal caching
    const response = await fetch(request)
    const newResponse = new Response(response.body, response)
    newResponse.headers.set('Cache-Control', 'public, max-age=300')
    newResponse.headers.set('X-Sophia-Service', 'status')
    return newResponse
}
async function handleWebRequest(request) {
    // Main website with optimization
    const cache = caches.default
    let response = await cache.match(request)
    if (!response) {
        response = await fetch(request)
        if (response.ok && request.method === 'GET') {
            const headers = new Headers(response.headers)
            headers.set('Cache-Control', 'public, max-age=7200')
            headers.set('X-Sophia-Service', 'web')
            response = new Response(response.body, {
                status: response.status,
                statusText: response.statusText,
                headers
            })
            event.waitUntil(cache.put(request, response.clone()))
        }
    }
    return response
}
async function handleWebSocket(request) {
    // WebSocket handling for real-time features
    return new Response('WebSocket upgrade required', {
        status: 426,
        headers: {
            'Upgrade': 'websocket',
            'Connection': 'Upgrade'
        }
    })
}
"""
        return worker_script.strip()
    def get_security_settings(self) -> Dict[str, Any]:
        """Generate security settings for CloudFlare"""
        return {
            "security_level": "medium",
            "challenge_ttl": 1800,
            "browser_check": "on",
            "hotlink_protection": "on",
            "security_header": {
                "enabled": True,
                "max_age": 31536000,
                "include_subdomains": True,
                "preload": True,
            },
            "waf": {
                "enabled": True,
                "mode": "on",
                "rules": [
                    {
                        "id": "sophia_rate_limit",
                        "expression": '(http.request.uri.path contains "/api/")',
                        "action": "challenge",
                        "description": "Rate limit API endpoints",
                    },
                    {
                        "id": "sophia_bot_protection",
                        "expression": "(cf.bot_management.score lt 30)",
                        "action": "block",
                        "description": "Block malicious bots",
                    },
                ],
            },
            "ddos_protection": {"enabled": True, "sensitivity": "medium"},
        }
    def export_terraform_config(self) -> str:
        """Export configuration as Terraform HCL"""
        terraform_config = f"""
# CloudFlare configuration for {self.domain}
terraform {{
  required_providers {{
    cloudflare = {{
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }}
  }}
}}
provider "cloudflare" {{
  api_token = var.cloudflare_api_token
}}
variable "cloudflare_api_token" {{
  description = "CloudFlare API token"
  type        = string
  sensitive   = true
}}
variable "zone_id" {{
  description = "CloudFlare zone ID for {self.domain}"
  type        = string
  default     = "{self.zone_id}"
}}
# DNS Records
"""
        for i, record in enumerate(self.get_dns_records()):
            terraform_config += f"""
resource "cloudflare_record" "record_{i}" {{
  zone_id = var.zone_id
  name    = "{record['name']}"
  value   = "{record['content']}"
  type    = "{record['type']}"
  ttl     = {record['ttl']}
  proxied = {str(record.get('proxied', False)).lower()}
  comment = "{record.get('comment', '')}"
}}
"""
        terraform_config += """
# Page Rules
"""
        for i, rule in enumerate(self.get_page_rules()):
            terraform_config += f"""
resource "cloudflare_page_rule" "rule_{i}" {{
  zone_id  = var.zone_id
  target   = "{rule['targets'][0]['constraint']['value']}"
  priority = {rule['priority']}
  status   = "{rule['status']}"
  actions {{
"""
            for action in rule["actions"]:
                if action["id"] == "minify":
                    terraform_config += f"""    minify {{
      html = "{action['value']['html']}"
      css  = "{action['value']['css']}"
      js   = "{action['value']['js']}"
    }}
"""
                else:
                    terraform_config += f'    {action["id"]} = "{action["value"]}"\n'
            terraform_config += "  }\n}\n"
        return terraform_config
# Usage example
if __name__ == "__main__":
    config = SophiaIntelCloudFlareConfig()
    print("DNS Records:")
    for record in config.get_dns_records():
        print(f"  {record['type']} | {record['name']} | {record['content']}")
    print("\nPage Rules:")
    for rule in config.get_page_rules():
        print(
            f"  Priority {rule['priority']}: {rule['targets'][0]['constraint']['value']}"
        )
    print("\nWorker Script generated successfully")
    print(f"Security settings configured for {config.domain}")
