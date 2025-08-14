"""
DNS and TLS configuration for Sophia Intel platform
Implements DNSimple DNS records and cert-manager for TLS certificates
"""

import os
import pulumi
import pulumi_dnsimple as dnsimple
from pulumi import Config, Output

def setup_dns_tls(cluster):
    """
    Set up DNS records and TLS certificates for Sophia Intel domains
    
    Args:
        cluster: K3s cluster instance with control_ip and worker_ip
    """
    config = Config()
    
    # Get DNSimple API key from environment
    dnsimple_api_key = os.environ.get('DNSIMPLE_API_KEY')
    if not dnsimple_api_key:
        pulumi.log.warn("DNSIMPLE_API_KEY not found in environment. Skipping DNS setup.")
        return
    
    # Domain configuration
    domain_name = "sophia-intel.ai"
    load_balancer_ip = "192.222.58.232"  # As specified in requirements
    
    pulumi.log.info(f"Setting up DNS records for {domain_name}")
    
    try:
        # Create DNSimple provider with account
        dnsimple_provider = dnsimple.Provider(
            "dnsimple-provider",
            token=dnsimple_api_key,
            account="sophia-intel"  # DNSimple account name
        )
        
        # Create DNS records for the domain
        # Root domain A record
        root_record = dnsimple.ZoneRecord(
            "sophia-intel-root",
            zone_name=domain_name,
            name="",  # Root domain
            type="A",
            value=load_balancer_ip,
            ttl=300,
            opts=pulumi.ResourceOptions(provider=dnsimple_provider)
        )
        
        # www subdomain A record
        www_record = dnsimple.ZoneRecord(
            "sophia-intel-www",
            zone_name=domain_name,
            name="www",
            type="A",
            value=load_balancer_ip,
            ttl=300,
            opts=pulumi.ResourceOptions(provider=dnsimple_provider)
        )
        
        # app subdomain A record
        app_record = dnsimple.ZoneRecord(
            "sophia-intel-app",
            zone_name=domain_name,
            name="app",
            type="A",
            value=load_balancer_ip,
            ttl=300,
            opts=pulumi.ResourceOptions(provider=dnsimple_provider)
        )
        
        # api subdomain A record
        api_record = dnsimple.ZoneRecord(
            "sophia-intel-api",
            zone_name=domain_name,
            name="api",
            type="A",
            value=load_balancer_ip,
            ttl=300,
            opts=pulumi.ResourceOptions(provider=dnsimple_provider)
        )
        
        # Export DNS record information
        pulumi.export("dns_records", {
            "root": f"{domain_name}",
            "www": f"www.{domain_name}",
            "app": f"app.{domain_name}",
            "api": f"api.{domain_name}",
            "load_balancer_ip": load_balancer_ip
        })
        
        # Set up cert-manager for TLS certificates
        setup_cert_manager(cluster, domain_name)
        
        pulumi.log.info("DNS records created successfully")
        
    except Exception as e:
        pulumi.log.error(f"Failed to create DNS records: {str(e)}")
        # Don't raise the exception, just log it so the rest of the infrastructure can be created
        pulumi.log.warn("Continuing with infrastructure deployment without DNS records")

def setup_cert_manager(cluster, domain_name):
    """
    Set up cert-manager for automatic TLS certificate provisioning
    
    Args:
        cluster: K3s cluster instance
        domain_name: Domain name for certificates
    """
    
    # Note: This requires the cluster to be running and kubectl access
    # For now, we'll create the configuration that can be applied later
    
    cert_manager_config = f"""
# cert-manager ClusterIssuer for Let's Encrypt
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@{domain_name}
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: traefik
---
# Certificate for main domains
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: sophia-intel-tls
  namespace: default
spec:
  secretName: sophia-intel-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - {domain_name}
  - www.{domain_name}
  - app.{domain_name}
  - api.{domain_name}
"""
    
    # Write cert-manager configuration to a file for later application
    with open("/tmp/cert-manager-config.yaml", "w") as f:
        f.write(cert_manager_config)
    
    pulumi.log.info("cert-manager configuration prepared at /tmp/cert-manager-config.yaml")
    pulumi.log.info("Apply with: kubectl apply -f /tmp/cert-manager-config.yaml")
    
    # Export certificate configuration
    pulumi.export("cert_manager_config_path", "/tmp/cert-manager-config.yaml")
    pulumi.export("tls_domains", [
        domain_name,
        f"www.{domain_name}",
        f"app.{domain_name}",
        f"api.{domain_name}"
    ])

def verify_dns_setup():
    """
    Verify DNS records are properly configured
    Returns verification commands that can be run
    """
    domain_name = "sophia-intel.ai"
    
    verification_commands = [
        f"dig {domain_name} +short",
        f"dig www.{domain_name} +short", 
        f"dig app.{domain_name} +short",
        f"dig api.{domain_name} +short",
        f"curl -I https://api.{domain_name}",
        f"curl -I https://app.{domain_name}"
    ]
    
    pulumi.export("dns_verification_commands", verification_commands)
    
    return verification_commands

