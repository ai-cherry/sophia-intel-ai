#!/usr/bin/env python3
"""
SOPHIA MVP Infrastructure Reset & Rebuild Script
Terminates all existing Lambda Labs instances and prepares for clean rebuild
"""
import os
import sys
import json
import subprocess
import time
from typing import Dict, List, Any

# Configuration
LAMBDA_LABS_API_KEY = os.getenv("LAMBDA_LABS_API_KEY")
PULUMI_ACCESS_TOKEN = os.getenv("PULUMI_ACCESS_TOKEN")

def run_command(cmd: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run shell command and return result"""
    print(f"🔧 Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"❌ Command failed: {result.stderr}")
        sys.exit(1)
    return result

def check_prerequisites():
    """Check that required tools and credentials are available"""
    print("🔍 Checking prerequisites...")
    
    # Check Lambda Labs API key
    if not LAMBDA_LABS_API_KEY:
        print("❌ LAMBDA_LABS_API_KEY environment variable not set")
        sys.exit(1)
    
    # Check Pulumi
    result = run_command("pulumi version", check=False)
    if result.returncode != 0:
        print("❌ Pulumi not installed or not in PATH")
        sys.exit(1)
    
    # Check kubectl
    result = run_command("kubectl version --client", check=False)
    if result.returncode != 0:
        print("⚠️  kubectl not found - will install if needed")
    
    print("✅ Prerequisites check complete")

def list_lambda_instances() -> List[Dict[str, Any]]:
    """List all Lambda Labs instances"""
    print("📋 Listing Lambda Labs instances...")
    
    try:
        import requests
        headers = {"Authorization": f"Bearer {LAMBDA_LABS_API_KEY}"}
        response = requests.get("https://cloud.lambdalabs.com/api/v1/instances", headers=headers)
        response.raise_for_status()
        
        instances = response.json().get("data", [])
        print(f"📊 Found {len(instances)} instances")
        
        for instance in instances:
            print(f"  - {instance.get('id')}: {instance.get('name')} ({instance.get('status')})")
        
        return instances
    except Exception as e:
        print(f"❌ Failed to list instances: {e}")
        return []

def terminate_all_instances(instances: List[Dict[str, Any]]):
    """Terminate all Lambda Labs instances"""
    if not instances:
        print("✅ No instances to terminate")
        return
    
    print(f"🔥 Terminating {len(instances)} instances...")
    
    try:
        import requests
        headers = {"Authorization": f"Bearer {LAMBDA_LABS_API_KEY}"}
        
        for instance in instances:
            instance_id = instance.get("id")
            if not instance_id:
                continue
                
            print(f"🗑️  Terminating instance {instance_id}...")
            response = requests.post(
                f"https://cloud.lambdalabs.com/api/v1/instances/{instance_id}/terminate",
                headers=headers
            )
            
            if response.status_code == 200:
                print(f"✅ Instance {instance_id} termination initiated")
            else:
                print(f"⚠️  Failed to terminate {instance_id}: {response.text}")
            
            time.sleep(1)  # Rate limiting
            
    except Exception as e:
        print(f"❌ Failed to terminate instances: {e}")

def cleanup_ssh_keys():
    """Clean up SSH keys"""
    print("🔑 Cleaning up SSH keys...")
    
    ssh_dir = os.path.expanduser("~/.ssh")
    if os.path.exists(ssh_dir):
        # Backup existing keys
        backup_dir = f"{ssh_dir}/backup_{int(time.time())}"
        run_command(f"mkdir -p {backup_dir}")
        run_command(f"cp {ssh_dir}/id_* {backup_dir}/ 2>/dev/null || true", check=False)
        
        # Remove old keys
        run_command(f"rm -f {ssh_dir}/id_rsa* {ssh_dir}/id_ed25519*", check=False)
    
    print("✅ SSH keys cleaned up")

def destroy_existing_pulumi_stacks():
    """Destroy existing Pulumi stacks"""
    print("💥 Destroying existing Pulumi stacks...")
    
    # List stacks
    result = run_command("pulumi stack ls --json", check=False)
    if result.returncode == 0:
        try:
            stacks = json.loads(result.stdout)
            for stack in stacks:
                stack_name = stack.get("name")
                if stack_name and "sophia" in stack_name.lower():
                    print(f"🗑️  Destroying stack: {stack_name}")
                    run_command(f"pulumi stack select {stack_name}", check=False)
                    run_command(f"pulumi destroy --yes", check=False)
                    run_command(f"pulumi stack rm {stack_name} --yes", check=False)
        except json.JSONDecodeError:
            print("⚠️  Could not parse Pulumi stack list")
    
    print("✅ Pulumi stacks cleaned up")

def verify_clean_slate():
    """Verify that infrastructure is clean"""
    print("🔍 Verifying clean slate...")
    
    # Check Lambda instances
    instances = list_lambda_instances()
    if instances:
        print(f"⚠️  {len(instances)} instances still exist")
        return False
    
    # Check Pulumi stacks
    result = run_command("pulumi stack ls", check=False)
    if "sophia" in result.stdout.lower():
        print("⚠️  Sophia-related Pulumi stacks still exist")
        return False
    
    print("✅ Clean slate verified")
    return True

def main():
    """Main execution function"""
    print("🚀 SOPHIA MVP Infrastructure Reset Starting...")
    print("=" * 50)
    
    # Step 1: Check prerequisites
    check_prerequisites()
    
    # Step 2: List current instances
    instances = list_lambda_instances()
    
    # Step 3: Terminate all instances
    if instances:
        confirm = input(f"⚠️  This will terminate {len(instances)} Lambda Labs instances. Continue? (y/N): ")
        if confirm.lower() != 'y':
            print("❌ Aborted by user")
            sys.exit(1)
        
        terminate_all_instances(instances)
        
        # Wait for termination
        print("⏳ Waiting for instances to terminate...")
        time.sleep(30)
    
    # Step 4: Clean up SSH keys
    cleanup_ssh_keys()
    
    # Step 5: Destroy Pulumi stacks
    destroy_existing_pulumi_stacks()
    
    # Step 6: Verify clean slate
    if verify_clean_slate():
        print("\n🎉 Infrastructure reset complete!")
        print("✅ Ready for Pulumi-managed rebuild")
    else:
        print("\n⚠️  Reset incomplete - manual cleanup may be required")
        sys.exit(1)

if __name__ == "__main__":
    main()

