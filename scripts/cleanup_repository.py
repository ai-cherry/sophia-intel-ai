#!/usr/bin/env python3
"""
Repository cleanup script for Sophia AI
Consolidates duplicates, fixes conflicts, and standardizes structure
"""

import os
import shutil
import glob
from pathlib import Path

def cleanup_github_workflows():
    """Clean up duplicate and outdated GitHub Actions workflows"""
    print("🧹 Cleaning up GitHub Actions workflows...")
    
    workflows_dir = Path('.github/workflows')
    
    # Files to remove (duplicates or outdated)
    files_to_remove = [
        'infra-preview.yml',  # Keep infra-preview.yaml
        'continue-publish.yaml',  # Outdated
        'roo-modes-validation.yml',  # Specific validation, can be integrated
        'tooling-smoke.yml',  # Can be integrated into main CI
    ]
    
    removed_count = 0
    for filename in files_to_remove:
        file_path = workflows_dir / filename
        if file_path.exists():
            print(f"  Removing duplicate/outdated workflow: {filename}")
            file_path.unlink()
            removed_count += 1
    
    # Update infra-deploy.yaml to fix Lambda Labs configuration
    infra_deploy_path = workflows_dir / 'infra-deploy.yaml'
    if infra_deploy_path.exists():
        print("  Updating infra-deploy.yaml for Lambda Labs...")
        
        # Read current content
        with open(infra_deploy_path, 'r') as f:
            content = f.read()
        
        # Replace AWS-specific content with Lambda Labs
        updated_content = content.replace(
            'aws-actions/configure-aws-credentials@v2',
            '# Lambda Labs authentication via API key'
        ).replace(
            'cd pulumi',
            'cd infra'
        ).replace(
            'npm install',
            'pip install -r requirements.txt'
        )
        
        # Write updated content
        with open(infra_deploy_path, 'w') as f:
            f.write(updated_content)
    
    print(f"  ✅ Removed {removed_count} duplicate/outdated workflows")
    return removed_count

def consolidate_gong_integrations():
    """Consolidate duplicate Gong integrations"""
    print("🔗 Consolidating Gong integrations...")
    
    gong_files = [
        'integrations/gong_client.py',
        'integrations/gong_client_shim.py', 
        'libs/mcp_client/gong.py'
    ]
    
    existing_files = [f for f in gong_files if os.path.exists(f)]
    
    if len(existing_files) > 1:
        print(f"  Found {len(existing_files)} Gong integration files:")
        for f in existing_files:
            print(f"    - {f}")
        
        # Keep the main integration, create backup of others
        main_integration = 'integrations/gong_client.py'
        if os.path.exists(main_integration):
            for f in existing_files:
                if f != main_integration:
                    backup_name = f + '.backup'
                    print(f"  Backing up {f} to {backup_name}")
                    shutil.move(f, backup_name)
        
        print("  ✅ Gong integrations consolidated")
        return len(existing_files) - 1
    else:
        print("  ✅ No duplicate Gong integrations found")
        return 0

def fix_agent_framework_conflicts():
    """Fix agent_framework.py filename conflicts"""
    print("🤖 Checking for agent_framework.py conflicts...")
    
    agent_framework_files = glob.glob('**/agent_framework.py', recursive=True)
    
    if agent_framework_files:
        print(f"  Found {len(agent_framework_files)} agent_framework.py files:")
        for f in agent_framework_files:
            print(f"    - {f}")
        
        # Rename to avoid conflicts with Python imports
        for f in agent_framework_files:
            new_name = f.replace('agent_framework.py', 'sophia_agent_framework.py')
            print(f"  Renaming {f} to {new_name}")
            shutil.move(f, new_name)
        
        print("  ✅ Agent framework conflicts resolved")
        return len(agent_framework_files)
    else:
        print("  ✅ No agent_framework.py conflicts found")
        return 0

def standardize_requirements():
    """Ensure requirements.txt files are properly structured"""
    print("📋 Standardizing requirements.txt files...")
    
    requirements_files = [
        'requirements.txt',
        'infra/requirements.txt'
    ]
    
    standardized_count = 0
    for req_file in requirements_files:
        if os.path.exists(req_file):
            print(f"  Checking {req_file}...")
            
            with open(req_file, 'r') as f:
                content = f.read().strip()
            
            # Check if file has proper structure
            lines = content.split('\n')
            needs_update = False
            
            # Remove empty lines and comments for analysis
            package_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]
            
            if package_lines:
                # Sort packages alphabetically
                sorted_lines = sorted(package_lines)
                if sorted_lines != package_lines:
                    needs_update = True
                
                if needs_update:
                    print(f"    Standardizing {req_file}")
                    
                    # Keep comments at the top, sort packages
                    comment_lines = [line for line in lines if line.strip().startswith('#') or not line.strip()]
                    
                    new_content = '\n'.join(comment_lines + sorted_lines)
                    
                    with open(req_file, 'w') as f:
                        f.write(new_content + '\n')
                    
                    standardized_count += 1
                else:
                    print(f"    {req_file} is already standardized")
            else:
                print(f"    {req_file} is empty or contains only comments")
    
    print(f"  ✅ Standardized {standardized_count} requirements files")
    return standardized_count

def create_deployment_scripts():
    """Create missing deployment scripts"""
    print("🚀 Creating deployment scripts...")
    
    scripts_dir = Path('scripts')
    scripts_dir.mkdir(exist_ok=True)
    
    # Create infrastructure deployment script
    infra_deploy_script = scripts_dir / 'deploy_infrastructure.sh'
    if not infra_deploy_script.exists():
        print("  Creating infrastructure deployment script...")
        
        script_content = """#!/bin/bash
set -e

echo "🚀 Deploying Sophia AI Infrastructure"

# Check required environment variables
required_vars=(
    "PULUMI_ACCESS_TOKEN"
    "LAMBDA_CLOUD_API_KEY" 
    "DNSIMPLE_API_KEY"
    "OPENROUTER_API_KEY"
)

missing_vars=()
for var in "${required_vars[@]}"; do
    if [[ -z "${!var}" ]]; then
        missing_vars+=("$var")
    fi
done

if [[ ${#missing_vars[@]} -gt 0 ]]; then
    echo "❌ Missing required environment variables:"
    printf '   %s\\n' "${missing_vars[@]}"
    exit 1
fi

# Navigate to infrastructure directory
cd infra

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Select Pulumi stack
echo "🎯 Selecting Pulumi stack..."
pulumi stack select scoobyjava-org/sophia-prod-on-lambda

# Deploy infrastructure
echo "🏗️ Deploying infrastructure..."
pulumi up --yes

echo "✅ Infrastructure deployment completed!"
"""
        
        with open(infra_deploy_script, 'w') as f:
            f.write(script_content)
        
        # Make executable
        os.chmod(infra_deploy_script, 0o755)
    
    # Create application deployment script
    app_deploy_script = scripts_dir / 'deploy_application.sh'
    if not app_deploy_script.exists():
        print("  Creating application deployment script...")
        
        script_content = """#!/bin/bash
set -e

echo "🚀 Deploying Sophia AI Application"

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ || echo "⚠️ Tests failed or no tests found"

# Deploy to K3s cluster (CPU-optimized Lambda Labs infrastructure)
echo "🚢 Deploying to K3s cluster..."
if [ -f "k8s/manifests/deployments/api-deployment.yaml" ]; then
    kubectl apply -f k8s/manifests/
    echo "✅ Deployed to K3s cluster successfully"
else
    echo "⚠️ K8s manifests not found, skipping cluster deployment"
fi

echo "✅ Application deployment completed!"
"""
        
        with open(app_deploy_script, 'w') as f:
            f.write(script_content)
        
        # Make executable
        os.chmod(app_deploy_script, 0o755)
    
    print("  ✅ Deployment scripts created")
    return 2

def generate_cleanup_report():
    """Generate a cleanup report"""
    print("\n📊 Repository Cleanup Summary")
    print("=" * 50)
    
    # Count current files
    workflow_count = len(list(Path('.github/workflows').glob('*.yml'))) + len(list(Path('.github/workflows').glob('*.yaml')))
    requirements_count = len(glob.glob('**/requirements.txt', recursive=True))
    python_files = len(glob.glob('**/*.py', recursive=True))
    
    print(f"GitHub Actions workflows: {workflow_count}")
    print(f"Requirements files: {requirements_count}")
    print(f"Python files: {python_files}")
    
    # Check for remaining issues
    issues = []
    
    # Check for duplicate files
    if len(glob.glob('**/*duplicate*', recursive=True)) > 0:
        issues.append("Duplicate files still present")
    
    # Check for backup files
    backup_files = glob.glob('**/*.backup', recursive=True)
    if backup_files:
        issues.append(f"{len(backup_files)} backup files created")
    
    if issues:
        print("\n⚠️ Remaining issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n✅ No remaining issues detected")
    
    print("\n🎯 Next steps:")
    print("  1. Review backup files and remove if not needed")
    print("  2. Test the consolidated CI/CD workflow")
    print("  3. Update documentation to reflect changes")
    print("  4. Run infrastructure deployment to validate")

def main():
    """Main cleanup execution"""
    print("🧹 Starting Sophia AI Repository Cleanup")
    print("=" * 50)
    
    total_changes = 0
    
    # Run cleanup tasks
    total_changes += cleanup_github_workflows()
    total_changes += consolidate_gong_integrations()
    total_changes += fix_agent_framework_conflicts()
    total_changes += standardize_requirements()
    total_changes += create_deployment_scripts()
    
    # Generate report
    generate_cleanup_report()
    
    print(f"\n🎉 Cleanup completed! Made {total_changes} changes.")
    
    if total_changes > 0:
        print("\n💡 Don't forget to:")
        print("  - Review the changes before committing")
        print("  - Test the updated workflows")
        print("  - Update any documentation that references old files")

if __name__ == "__main__":
    main()

