#!/usr/bin/env python3
"""
Sophia Intel AI - Secret Centralization System
Migrates all secrets from .env files to centralized configuration management
"""

import os
import json
import yaml
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

class SecretCentralizer:
    def __init__(self, project_root: str = "/Users/lynnmusil/sophia-intel-ai"):
        self.project_root = Path(project_root)
        self.secrets_collected = {}
        self.env_files_found = []
        
        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
        self.logger = logging.getLogger(__name__)
        
    def find_env_files(self) -> List[Path]:
        """Find all .env files in the project"""
        env_files = []
        patterns = [".env*", "*.env", ".envrc"]
        
        for pattern in patterns:
            env_files.extend(self.project_root.glob(f"**/{pattern}"))
            
        # Filter out some non-env files
        filtered_files = []
        for file_path in env_files:
            if file_path.name.endswith(('.example', '.sample', '.template')):
                continue
            if file_path.is_file():
                filtered_files.append(file_path)
                
        self.env_files_found = filtered_files
        self.logger.info(f"Found {len(filtered_files)} environment files")
        return filtered_files
    
    def extract_secrets_from_file(self, file_path: Path) -> Dict[str, str]:
        """Extract secrets from a single .env file"""
        secrets = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Skip export statements
                    if line.startswith('export '):
                        line = line[7:]  # Remove 'export '
                    
                    # Split on first = only
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        # Skip empty values and placeholder values
                        if value and not value.startswith('YOUR_') and not value.startswith('CHANGEME'):
                            secrets[key] = value
                            
        except Exception as e:
            self.logger.warning(f"Error reading {file_path}: {e}")
            
        return secrets
    
    def categorize_secrets(self, secrets: Dict[str, str]) -> Dict[str, Dict[str, str]]:
        """Categorize secrets into logical groups"""
        categories = {
            "ai_providers": {},
            "business_integrations": {},
            "databases": {},
            "infrastructure": {},
            "development": {},
            "security": {},
            "misc": {}
        }
        
        # AI Provider mappings
        ai_keys = [
            'openai', 'anthropic', 'gemini', 'groq', 'deepseek', 'mistral', 'grok', 'xai',
            'together', 'perplexity', 'openrouter', 'aimlapi', 'cohere', 'huggingface',
            'stability', 'replicate', 'llama', 'qwen', 'agno', 'eleven_labs', 'elevenlabs',
            'assembly', 'deepgram', 'eden_ai', 'eden', 'venice_ai', 'mem0', 'portkey'
        ]
        
        # Business Integration mappings
        business_keys = [
            'slack', 'gong', 'salesforce', 'hubspot', 'linear', 'asana', 'airtable',
            'netsuite', 'lattice', 'intercom', 'looker', 'apollo_io'
        ]
        
        # Database mappings
        database_keys = [
            'postgres', 'redis', 'weaviate', 'qdrant', 'milvus', 'neo4j', 'neon'
        ]
        
        # Infrastructure mappings
        infra_keys = [
            'github', 'fly_org', 'lambda', 'pulumi', 'docker'
        ]
        
        # Development mappings
        dev_keys = [
            'continue', 'langchain', 'sentry', 'arize', 'jwt_secret',
            'api_secret', 'encryption_key', 'mcp_secret', 'mcp_api_key', 'telegram',
            'n8n'
        ]
        
        # Categorize each secret
        for key, value in secrets.items():
            key_lower = key.lower()
            categorized = False
            
            # Check AI providers
            for ai_key in ai_keys:
                if ai_key in key_lower:
                    categories["ai_providers"][key] = value
                    categorized = True
                    break
            
            if categorized:
                continue
                
            # Check business integrations
            for business_key in business_keys:
                if business_key in key_lower:
                    categories["business_integrations"][key] = value
                    categorized = True
                    break
                    
            if categorized:
                continue
                
            # Check databases
            for db_key in database_keys:
                if db_key in key_lower:
                    categories["databases"][key] = value
                    categorized = True
                    break
                    
            if categorized:
                continue
                
            # Check infrastructure
            for infra_key in infra_keys:
                if infra_key in key_lower:
                    categories["infrastructure"][key] = value
                    categorized = True
                    break
                    
            if categorized:
                continue
                
            # Check development
            for dev_key in dev_keys:
                if dev_key in key_lower:
                    categories["development"][key] = value
                    categorized = True
                    break
                    
            if categorized:
                continue
                
            # Security keys
            if any(sec_key in key_lower for sec_key in ['secret', 'key', 'token', 'password']):
                categories["security"][key] = value
            else:
                categories["misc"][key] = value
                
        return categories
    
    def create_unified_env(self, categorized_secrets: Dict[str, Dict[str, str]]) -> str:
        """Create a unified .env file content"""
        content = []
        content.append("############################################################")
        content.append("# SOPHIA UNIFIED ENVIRONMENT - CENTRALIZED SECRETS")
        content.append(f"# Generated: {os.popen('date +%Y-%m-%d').read().strip()}")
        content.append("# This is the SINGLE SOURCE OF TRUTH for all environment variables")
        content.append("# SECURITY: Contains sensitive API keys - DO NOT COMMIT TO GIT")
        content.append("############################################################")
        content.append("")
        
        for category, secrets in categorized_secrets.items():
            if not secrets:
                continue
                
            category_name = category.replace('_', ' ').title()
            content.append(f"# ====================================")
            content.append(f"# {category_name}")
            content.append(f"# ====================================")
            content.append("")
            
            for key, value in sorted(secrets.items()):
                content.append(f"{key}={value}")
                
            content.append("")
            
        content.append("############################################################")
        content.append("# END OF UNIFIED ENVIRONMENT FILE")
        content.append("############################################################")
        
        return "\n".join(content)
    
    def backup_existing_env_files(self) -> None:
        """Backup existing .env files before deletion"""
        backup_dir = self.project_root / ".env_backup"
        backup_dir.mkdir(exist_ok=True)
        
        self.logger.info(f"Creating backup of {len(self.env_files_found)} env files")
        
        for env_file in self.env_files_found:
            relative_path = env_file.relative_to(self.project_root)
            backup_path = backup_dir / str(relative_path).replace('/', '_')
            shutil.copy2(env_file, backup_path)
            self.logger.info(f"Backed up {env_file} -> {backup_path}")
    
    def generate_centralized_config(self) -> Dict[str, Any]:
        """Generate centralized configuration"""
        config = {
            "system_config": {
                "sophia_ui_port": 3000,
                "sophia_api_port": 8003,
                "builder_agno_port": 8005,
                "mcp_gateway_port": 8080,
                "mcp_memory_port": 8081,
                "mcp_git_port": 8082,
                "mcp_context_port": 8083,
                "mcp_index_port": 8084,
                
                "environment": "development",
                "node_env": "development",
                "app_env": "development",
                "debug": False,
                "log_level": "INFO",
                
                "use_portkey_routing": True,
                "enable_fallback": True,
                "enable_load_balancing": True,
                "local_dev_mode": True,
                
                "application_name": "Sophia Intelligence Platform",
                "workspace_path": "/Users/lynnmusil/sophia-intel-ai",
                "workspace_name": "sophia",
                "read_only": False
            }
        }
        
        return config
    
    def run_migration(self, backup: bool = True, create_unified: bool = True):
        """Run the complete migration process"""
        self.logger.info("🚀 Starting secret centralization migration")
        
        # Step 1: Find all env files
        env_files = self.find_env_files()
        if not env_files:
            self.logger.warning("No environment files found!")
            return
        
        # Step 2: Extract all secrets
        all_secrets = {}
        for env_file in env_files:
            self.logger.info(f"Processing {env_file}")
            file_secrets = self.extract_secrets_from_file(env_file)
            all_secrets.update(file_secrets)
            self.logger.info(f"  -> Extracted {len(file_secrets)} secrets")
        
        self.logger.info(f"Total unique secrets found: {len(all_secrets)}")
        
        # Step 3: Categorize secrets
        categorized = self.categorize_secrets(all_secrets)
        
        # Step 4: Create unified environment file
        if create_unified:
            unified_content = self.create_unified_env(categorized)
            unified_path = self.project_root / ".env.centralized"
            
            with open(unified_path, 'w') as f:
                f.write(unified_content)
            
            self.logger.info(f"✅ Created unified environment file: {unified_path}")
        
        # Step 5: Generate centralized config
        config = self.generate_centralized_config()
        config.update(categorized)
        
        config_path = self.project_root / "centralized_config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        self.logger.info(f"✅ Created centralized config: {config_path}")
        
        # Step 6: Backup existing files
        if backup:
            self.backup_existing_env_files()
        
        # Step 7: Generate summary report
        summary = {
            "migration_timestamp": os.popen('date -Iseconds').read().strip(),
            "env_files_processed": len(env_files),
            "total_secrets_extracted": len(all_secrets),
            "secrets_by_category": {k: len(v) for k, v in categorized.items()},
            "env_files_found": [str(f) for f in env_files],
            "next_steps": [
                "1. Review centralized_config.yaml for accuracy",
                "2. Test applications with new .env.centralized file",
                "3. Update deployment scripts to use centralized config",
                "4. Delete old .env files after verification",
                "5. Implement model enforcement system"
            ]
        }
        
        summary_path = self.project_root / "migration_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.logger.info(f"✅ Migration complete! Summary: {summary_path}")
        
        # Print summary
        print("\n🎯 MIGRATION SUMMARY")
        print("="*60)
        print(f"Environment files processed: {len(env_files)}")
        print(f"Total secrets extracted: {len(all_secrets)}")
        print("\nSecrets by category:")
        for category, secrets in categorized.items():
            if secrets:
                print(f"  {category}: {len(secrets)} secrets")
        
        print(f"\n✅ Files created:")
        print(f"  - {unified_path}")
        print(f"  - {config_path}")
        print(f"  - {summary_path}")
        
        if backup:
            print(f"  - Backups in: {self.project_root}/.env_backup/")


if __name__ == "__main__":
    centralizer = SecretCentralizer()
    centralizer.run_migration()
