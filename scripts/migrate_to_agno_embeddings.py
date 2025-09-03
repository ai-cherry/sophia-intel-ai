#!/usr/bin/env python3
"""
Migration script to update codebase to use Agno embedding service
Replaces old embedding implementations with new unified service
"""

import ast
import os
import re
from pathlib import Path
from typing import List, Tuple

# ============================================
# Migration Patterns
# ============================================

MIGRATION_PATTERNS = [
    # Old import patterns to replace
    (
        r'from app\.memory\.embedding_pipeline import.*',
        'from app.embeddings.agno_embedding_service import AgnoEmbeddingService, EmbeddingRequest'
    ),
    (
        r'from app\.memory\.dual_tier_embeddings import.*',
        'from app.embeddings.agno_embedding_service import AgnoEmbeddingService, EmbeddingModel'
    ),
    (
        r'from app\.memory\.advanced_embedding_router import.*',
        'from app.embeddings.portkey_integration import PortkeyGateway'
    ),
    
    # Old class instantiations
    (
        r'StandardizedEmbeddingPipeline\(\)',
        'AgnoEmbeddingService()'
    ),
    (
        r'DualTierEmbedder\(\)',
        'AgnoEmbeddingService()'
    ),
    (
        r'AdvancedEmbeddingRouter\(\)',
        'AgnoEmbeddingService()'
    ),
    
    # Method calls
    (
        r'pipeline\.generate_embeddings\((.*?)\)',
        r'await service.embed(EmbeddingRequest(texts=\1))'
    ),
    (
        r'embedder\.embed_single\((.*?)\)',
        r'await service.embed(EmbeddingRequest(texts=[\1]))'
    ),
    (
        r'embedder\.embed_batch\((.*?)\)',
        r'await service.embed(EmbeddingRequest(texts=\1))'
    ),
]

# Files to migrate
FILES_TO_MIGRATE = [
    "app/memory/unified_memory_store.py",
    "app/infrastructure/langgraph/rag_pipeline.py",
    "app/weaviate/weaviate_client.py",
    "app/agents/base_agent.py",
    "app/swarms/base_swarm.py",
]

# ============================================
# Migration Functions
# ============================================

def find_files_to_migrate(base_path: str = ".") -> List[Path]:
    """Find all Python files that need migration"""
    files = []
    
    # Add explicitly listed files
    for file_path in FILES_TO_MIGRATE:
        full_path = Path(base_path) / file_path
        if full_path.exists():
            files.append(full_path)
    
    # Find files with old imports
    for py_file in Path(base_path).rglob("*.py"):
        # Skip migration script and new files
        if "migrate_to_agno" in str(py_file):
            continue
        if "agno_embedding" in str(py_file):
            continue
        if "portkey_integration" in str(py_file):
            continue
            
        content = py_file.read_text()
        
        # Check for old imports
        if any(pattern in content for pattern in [
            "embedding_pipeline",
            "dual_tier_embeddings",
            "advanced_embedding_router",
            "StandardizedEmbeddingPipeline",
            "DualTierEmbedder",
            "AdvancedEmbeddingRouter"
        ]):
            if py_file not in files:
                files.append(py_file)
    
    return files

def migrate_file(file_path: Path, dry_run: bool = True) -> Tuple[bool, str]:
    """
    Migrate a single file to use new embedding service
    
    Args:
        file_path: Path to file
        dry_run: If True, don't write changes
        
    Returns:
        Tuple of (success, message)
    """
    try:
        original_content = file_path.read_text()
        content = original_content
        
        # Apply migration patterns
        for old_pattern, new_pattern in MIGRATION_PATTERNS:
            content = re.sub(old_pattern, new_pattern, content)
        
        # Add async/await where needed
        content = add_async_await(content)
        
        # Update method signatures
        content = update_method_signatures(content)
        
        # Add new imports if needed
        if "AgnoEmbeddingService" in content and "from app.embeddings.agno_embedding_service" not in content:
            imports = """from app.embeddings.agno_embedding_service import (
    AgnoEmbeddingService,
    EmbeddingRequest,
    EmbeddingModel
)\n"""
            # Add after other imports
            content = re.sub(r'(import.*?\n\n)', r'\1' + imports, content, count=1)
        
        # Check if changes were made
        if content != original_content:
            if not dry_run:
                # Backup original
                backup_path = file_path.with_suffix('.py.bak')
                backup_path.write_text(original_content)
                
                # Write migrated content
                file_path.write_text(content)
                
                return True, f"Migrated {file_path} (backup: {backup_path})"
            else:
                return True, f"Would migrate {file_path}"
        else:
            return False, f"No changes needed for {file_path}"
            
    except Exception as e:
        return False, f"Error migrating {file_path}: {e}"

def add_async_await(content: str) -> str:
    """Add async/await to embedding calls"""
    
    # Make embedding methods async
    patterns = [
        (r'def (.*embed.*)\(', r'async def \1('),
        (r'service\.embed\(', r'await service.embed('),
        (r'gateway\.create_embeddings\(', r'await gateway.create_embeddings('),
    ]
    
    for old, new in patterns:
        content = re.sub(old, new, content)
    
    return content

def update_method_signatures(content: str) -> str:
    """Update method signatures to match new API"""
    
    # Update embedding method calls
    content = re.sub(
        r'generate_embeddings\(\s*texts=([^,\)]+)',
        r'embed(EmbeddingRequest(texts=\1)',
        content
    )
    
    # Update embedding response handling
    content = re.sub(
        r'for result in results:',
        r'for embedding in response.embeddings:',
        content
    )
    
    return content

# ============================================
# Migration Report
# ============================================

def generate_migration_report(results: List[Tuple[Path, bool, str]]) -> str:
    """Generate migration report"""
    
    report = ["=" * 60]
    report.append("EMBEDDING MIGRATION REPORT")
    report.append("=" * 60)
    report.append("")
    
    successful = [r for r in results if r[1]]
    failed = [r for r in results if not r[1]]
    
    report.append(f"Total files processed: {len(results)}")
    report.append(f"Successfully migrated: {len(successful)}")
    report.append(f"Failed/Skipped: {len(failed)}")
    report.append("")
    
    if successful:
        report.append("Successfully Migrated Files:")
        report.append("-" * 30)
        for path, _, msg in successful:
            report.append(f"  ✓ {path}")
    
    if failed:
        report.append("")
        report.append("Failed/Skipped Files:")
        report.append("-" * 30)
        for path, _, msg in failed:
            report.append(f"  ✗ {path}: {msg}")
    
    report.append("")
    report.append("Next Steps:")
    report.append("-" * 30)
    report.append("1. Review migrated files for correctness")
    report.append("2. Run tests to ensure functionality")
    report.append("3. Update environment variables:")
    report.append("   - PORTKEY_API_KEY")
    report.append("   - TOGETHER_VIRTUAL_KEY")
    report.append("4. Remove old embedding files after verification")
    
    return "\n".join(report)

# ============================================
# Example Updates
# ============================================

def create_example_updates():
    """Create example files showing how to use new service"""
    
    examples = []
    
    # Example 1: Agent with embeddings
    agent_example = '''"""
Example: Agent using Agno embedding service
"""

from app.embeddings.agno_embedding_service import (
    AgnoEmbeddingService,
    AgnoEmbeddingAgent,
    EmbeddingRequest
)

class SmartAgent:
    def __init__(self):
        self.embedding_service = AgnoEmbeddingService()
        self.embedding_agent = AgnoEmbeddingAgent(self.embedding_service)
    
    async def process_document(self, document: str):
        """Process document with embeddings"""
        
        # Generate embeddings for RAG
        response = await self.embedding_service.create_agent_embeddings(
            agent_id=self.id,
            context=document,
            memory_type="semantic"
        )
        
        # Store in vector DB
        await self.store_embedding(
            embedding=response.embeddings[0],
            metadata=response.metadata
        )
        
        return response

# Usage with Agno Agent
from agno.agent import Agent

agent = Agent(
    name="smart_agent",
    tools=[embedding_agent.as_tool()]
)
'''
    
    examples.append(("examples/agent_with_embeddings.py", agent_example))
    
    # Example 2: Swarm with embeddings
    swarm_example = '''"""
Example: Swarm using embeddings for coordination
"""

from app.embeddings.agno_embedding_service import AgnoEmbeddingService

class DocumentSwarm:
    def __init__(self):
        self.embedding_service = AgnoEmbeddingService()
    
    async def process_documents(self, documents: list[str]):
        """Process documents in swarm"""
        
        # Generate embeddings for all documents
        response = await self.embedding_service.create_swarm_embeddings(
            swarm_id=self.id,
            documents=documents,
            task_type="retrieval"
        )
        
        # Distribute to agents based on similarity
        clusters = self.cluster_by_similarity(response.embeddings)
        
        for cluster in clusters:
            await self.assign_to_agent(cluster)
        
        return response
'''
    
    examples.append(("examples/swarm_with_embeddings.py", swarm_example))
    
    # Example 3: Direct API usage
    api_example = '''"""
Example: Direct API usage for embeddings
"""

import httpx

async def generate_embeddings(texts: list[str]):
    """Generate embeddings via API"""
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/embeddings/create",
            json={
                "text": texts,
                "use_case": "rag",
                "language": "en"
            }
        )
        
        result = response.json()
        return result["data"]["embeddings"]

# Using curl
# curl -X POST http://localhost:8000/embeddings/create \\
#   -H "Content-Type: application/json" \\
#   -d '{"text": "Hello world", "use_case": "search"}'
'''
    
    examples.append(("examples/api_embedding_usage.py", api_example))
    
    return examples

# ============================================
# Main Migration Script
# ============================================

def main():
    """Run migration script"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate to Agno embedding service")
    parser.add_argument("--dry-run", action="store_true", help="Don't write changes")
    parser.add_argument("--create-examples", action="store_true", help="Create example files")
    parser.add_argument("--path", default=".", help="Base path to search")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("AGNO EMBEDDING SERVICE MIGRATION")
    print("=" * 60)
    print()
    
    # Create examples if requested
    if args.create_examples:
        print("Creating example files...")
        examples = create_example_updates()
        
        for path, content in examples:
            example_path = Path(path)
            example_path.parent.mkdir(parents=True, exist_ok=True)
            example_path.write_text(content)
            print(f"  Created: {path}")
        
        print()
    
    # Find files to migrate
    print("Searching for files to migrate...")
    files = find_files_to_migrate(args.path)
    print(f"Found {len(files)} files to check")
    print()
    
    # Migrate files
    results = []
    for file_path in files:
        success, message = migrate_file(file_path, dry_run=args.dry_run)
        results.append((file_path, success, message))
        print(f"  {message}")
    
    print()
    
    # Generate report
    report = generate_migration_report(results)
    print(report)
    
    # Save report
    report_path = Path("migration_report.txt")
    report_path.write_text(report)
    print(f"\nReport saved to: {report_path}")
    
    if args.dry_run:
        print("\nThis was a dry run. Use without --dry-run to apply changes.")

if __name__ == "__main__":
    main()