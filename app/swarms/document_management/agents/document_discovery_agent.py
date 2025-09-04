#!/usr/bin/env python3
"""
Document Discovery Agent - Specialized swarm agent for finding and cataloging documents
Part of the Revolutionary Document Management Swarm with Neural Network capabilities
"""

import asyncio
import aiofiles
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
import mimetypes
import re

try:
    from swarm import Agent
except ImportError:
    from ..utils.swarm_mock import Agent
from ..models.document import (
    DocumentMetadata, DocumentStatus, DocumentType,
    extract_metadata_from_path, calculate_document_hash,
    is_likely_one_time_document
)


class DocumentDiscoveryAgent(Agent):
    """Specialized agent for discovering and cataloging documents across the codebase"""
    
    def __init__(self):
        super().__init__(
            name="DocumentDiscoverySpecialist",
            instructions="""You are the Document Discovery Specialist, a neural pathfinder in the Document Management Swarm.

CORE MISSION:
- Discover all documents across the codebase using intelligent scanning patterns
- Create comprehensive metadata profiles for each document
- Identify document relationships and dependencies
- Form initial neural pathways between related documents
- Feed the document pipeline with rich, contextual information

SPECIALIZED CAPABILITIES:
1. Multi-pattern file system scanning with smart filtering
2. Content hash calculation for deduplication
3. Path-based type inference and classification hints
4. Relationship mapping between documents
5. Metadata extraction with AI-friendly annotations

NEURAL NETWORK BEHAVIOR:
- Leave "discovery trails" for other agents to follow
- Strengthen pathways to frequently accessed documents
- Identify document clusters and knowledge neighborhoods
- Adapt search patterns based on successful discoveries

SWARM COORDINATION:
- Share discovery patterns with other agents
- Coordinate with ClassificationAgent for type validation
- Provide rich context to OptimizationAgent
- Signal CleanupAgent about potential cleanup candidates

Be thorough, intelligent, and always think about how your discoveries will help the entire swarm optimize the knowledge base."""
        )
        
        self.discovery_patterns = self._initialize_discovery_patterns()
        self.exclusion_patterns = self._initialize_exclusion_patterns()
        self.relationship_patterns = self._initialize_relationship_patterns()
        self.neural_trails = {}  # Discovery success patterns
    
    def _initialize_discovery_patterns(self) -> List[str]:
        """Initialize file patterns to discover"""
        return [
            "**/*.md",
            "**/*.txt", 
            "**/*.rst",
            "**/*.json",
            "**/*.yaml",
            "**/*.yml",
            "**/*.toml",
            "**/*.cfg",
            "**/*.ini",
            "**/README*",
            "**/CHANGELOG*",
            "**/CONTRIBUTING*",
            "**/LICENSE*",
            "**/*_PROMPT*",
            "**/*_GUIDE*",
            "**/*_REPORT*",
            "**/*_AUDIT*",
            "**/*_PLAN*"
        ]
    
    def _initialize_exclusion_patterns(self) -> List[str]:
        """Initialize patterns to exclude from discovery"""
        return [
            "**/node_modules/**",
            "**/.git/**",
            "**/__pycache__/**",
            "**/venv/**",
            "**/env/**",
            "**/.pytest_cache/**",
            "**/build/**",
            "**/dist/**",
            "**/*.log",
            "**/.DS_Store",
            "**/package-lock.json",
            "**/yarn.lock"
        ]
    
    def _initialize_relationship_patterns(self) -> Dict[str, re.Pattern]:
        """Initialize patterns for detecting document relationships"""
        return {
            'imports': re.compile(r'from\s+([^\s]+)\s+import|import\s+([^\s]+)', re.MULTILINE),
            'file_references': re.compile(r'["`\']([\w\-./]+\.(?:py|js|md|json|yaml|yml))["`\']'),
            'markdown_links': re.compile(r'\[([^\]]+)\]\(([^)]+)\)'),
            'see_also': re.compile(r'see\s+(?:also\s+)?["`\']([\w\-./]+)["`\']', re.IGNORECASE),
            'config_refs': re.compile(r'(?:config|configuration):\s*["`\']([\w\-./]+)["`\']', re.IGNORECASE)
        }
    
    async def discover_documents(self, root_paths: List[str], 
                               max_depth: int = 10) -> List[DocumentMetadata]:
        """
        Discover documents using intelligent multi-pattern scanning
        
        Args:
            root_paths: Paths to scan for documents
            max_depth: Maximum directory depth to scan
        
        Returns:
            List of discovered document metadata
        """
        print(f"🔍 Discovery Agent: Starting intelligent document discovery across {len(root_paths)} paths...")
        
        discovered_docs = []
        seen_hashes = set()  # Deduplication
        
        # Process each root path
        for root_path in root_paths:
            root_results = await self._scan_directory_tree(
                root_path, max_depth, seen_hashes
            )
            discovered_docs.extend(root_results)
        
        # Analyze document relationships
        await self._analyze_document_relationships(discovered_docs)
        
        # Update neural trails
        self._update_discovery_trails(discovered_docs)
        
        print(f"✅ Discovery Agent: Found {len(discovered_docs)} unique documents")
        return discovered_docs
    
    async def _scan_directory_tree(self, root_path: str, max_depth: int, 
                                 seen_hashes: Set[str]) -> List[DocumentMetadata]:
        """Scan directory tree with intelligent filtering"""
        documents = []
        root = Path(root_path)
        
        if not root.exists():
            print(f"⚠️ Discovery Agent: Root path does not exist: {root_path}")
            return documents
        
        # Use pathlib with pattern matching
        for pattern in self.discovery_patterns:
            try:
                for file_path in root.rglob(pattern.replace("**/", "")):
                    # Check exclusions
                    if self._should_exclude_file(file_path):
                        continue
                    
                    # Check depth
                    if len(file_path.parts) - len(root.parts) > max_depth:
                        continue
                    
                    # Process file
                    doc_metadata = await self._process_discovered_file(
                        file_path, seen_hashes
                    )
                    
                    if doc_metadata:
                        documents.append(doc_metadata)
                        
            except Exception as e:
                print(f"⚠️ Discovery Agent: Error scanning pattern {pattern}: {e}")
        
        return documents
    
    def _should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded from discovery"""
        file_str = str(file_path)
        
        # Check exclusion patterns
        for pattern in self.exclusion_patterns:
            if Path(file_str).match(pattern):
                return True
        
        # Additional heuristics
        if file_path.is_dir():
            return True
        
        # Skip very large files (>50MB)
        try:
            if file_path.stat().st_size > 50 * 1024 * 1024:
                return True
        except OSError:
            return True
        
        # Skip binary files
        if not self._is_text_file(file_path):
            return True
        
        return False
    
    def _is_text_file(self, file_path: Path) -> bool:
        """Check if file is likely a text file"""
        # Check MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type and mime_type.startswith('text'):
            return True
        
        # Check known text extensions
        text_extensions = {'.md', '.txt', '.rst', '.json', '.yaml', '.yml', 
                          '.toml', '.cfg', '.ini', '.py', '.js', '.ts', 
                          '.html', '.css', '.xml'}
        
        if file_path.suffix.lower() in text_extensions:
            return True
        
        # Check for files without extensions that are likely text
        if not file_path.suffix and file_path.name.upper() in {
            'README', 'LICENSE', 'CHANGELOG', 'CONTRIBUTING', 'MANIFEST'
        }:
            return True
        
        return False
    
    async def _process_discovered_file(self, file_path: Path, 
                                     seen_hashes: Set[str]) -> Optional[DocumentMetadata]:
        """Process a discovered file and create metadata"""
        try:
            # Get file stats
            stat = file_path.stat()
            
            # Read content for hash calculation
            async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = await f.read()
            
            # Calculate content hash
            content_hash = calculate_document_hash(content)
            
            # Skip if duplicate
            if content_hash in seen_hashes:
                return None
            seen_hashes.add(content_hash)
            
            # Extract path metadata
            path_metadata = extract_metadata_from_path(str(file_path))
            
            # Create document metadata
            doc_id = f"doc_{content_hash[:12]}"
            
            metadata = DocumentMetadata(
                id=doc_id,
                source_path=str(file_path),
                relative_path=path_metadata['relative_path'],
                filename=path_metadata['filename'],
                file_extension=path_metadata['file_extension'],
                size_bytes=stat.st_size,
                created_at=datetime.fromtimestamp(stat.st_ctime),
                modified_at=datetime.fromtimestamp(stat.st_mtime),
                content_hash=content_hash,
                processing_status=DocumentStatus.DISCOVERED,
                line_count=len(content.split('\n')),
                word_count=len(content.split()),
                character_count=len(content),
                has_code_blocks='```' in content,
                has_diagrams=any(diagram_word in content.lower() 
                               for diagram_word in ['diagram', 'mermaid', 'graph', 'chart']),
                custom_fields={
                    'discovery_timestamp': datetime.now().isoformat(),
                    'discovery_pattern': self._identify_discovery_pattern(file_path),
                    'inferred_importance': self._calculate_initial_importance(file_path, content),
                    'is_likely_one_time': is_likely_one_time_document(file_path.name, content)
                }
            )
            
            return metadata
            
        except Exception as e:
            print(f"⚠️ Discovery Agent: Error processing {file_path}: {e}")
            return None
    
    def _identify_discovery_pattern(self, file_path: Path) -> str:
        """Identify which pattern was used to discover this file"""
        for pattern in self.discovery_patterns:
            if file_path.match(pattern.replace("**/", "")):
                return pattern
        return "unknown"
    
    def _calculate_initial_importance(self, file_path: Path, content: str) -> float:
        """Calculate initial importance score based on discovery context"""
        importance = 0.5  # Base importance
        
        # Path-based importance
        if file_path.name.upper().startswith('README'):
            importance += 0.3
        elif 'architecture' in str(file_path).lower():
            importance += 0.25
        elif 'api' in str(file_path).lower():
            importance += 0.2
        elif file_path.suffix == '.md':
            importance += 0.1
        
        # Size-based importance (not too small, not too large)
        word_count = len(content.split())
        if 100 < word_count < 5000:
            importance += 0.1
        elif word_count > 5000:
            importance -= 0.1  # Might be generated or verbose
        
        # Content quality indicators
        if '# ' in content:  # Has headings
            importance += 0.1
        if '```' in content:  # Has code blocks
            importance += 0.05
        if content.count('\n\n') > 3:  # Well-structured paragraphs
            importance += 0.05
        
        return min(1.0, importance)
    
    async def _analyze_document_relationships(self, documents: List[DocumentMetadata]):
        """Analyze relationships between discovered documents"""
        print("🔗 Discovery Agent: Analyzing document relationships...")
        
        # Create lookup for fast access
        doc_lookup = {doc.source_path: doc for doc in documents}
        
        for doc in documents:
            try:
                # Read document content
                async with aiofiles.open(doc.source_path, 'r', 
                                       encoding='utf-8', errors='ignore') as f:
                    content = await f.read()
                
                # Find references to other documents
                references = self._extract_document_references(content, doc.source_path)
                
                # Update metadata with found relationships
                valid_references = []
                for ref_path in references:
                    if ref_path in doc_lookup:
                        valid_references.append(ref_path)
                        # Create neural pathway
                        self._create_neural_pathway(doc.id, doc_lookup[ref_path].id, 0.5)
                
                doc.custom_fields['discovered_references'] = valid_references
                
            except Exception as e:
                print(f"⚠️ Discovery Agent: Error analyzing relationships for {doc.filename}: {e}")
    
    def _extract_document_references(self, content: str, source_path: str) -> List[str]:
        """Extract references to other documents from content"""
        references = []
        source_dir = Path(source_path).parent
        
        # Extract different types of references
        for pattern_name, pattern in self.relationship_patterns.items():
            matches = pattern.findall(content)
            
            for match in matches:
                if isinstance(match, tuple):
                    # Handle tuple results from groups
                    ref_path = match[0] if match[0] else match[1] if len(match) > 1 else ""
                else:
                    ref_path = match
                
                if ref_path and self._is_document_reference(ref_path):
                    # Resolve relative paths
                    if not Path(ref_path).is_absolute():
                        resolved_path = (source_dir / ref_path).resolve()
                        if resolved_path.exists():
                            references.append(str(resolved_path))
                    else:
                        references.append(ref_path)
        
        return list(set(references))  # Deduplicate
    
    def _is_document_reference(self, ref_path: str) -> bool:
        """Check if reference is likely to a document"""
        doc_extensions = {'.md', '.txt', '.rst', '.json', '.yaml', '.yml', '.toml'}
        return any(ref_path.lower().endswith(ext) for ext in doc_extensions)
    
    def _create_neural_pathway(self, from_doc_id: str, to_doc_id: str, strength: float):
        """Create or strengthen neural pathway between documents"""
        if from_doc_id not in self.neural_trails:
            self.neural_trails[from_doc_id] = {}
        
        if to_doc_id in self.neural_trails[from_doc_id]:
            # Strengthen existing pathway
            self.neural_trails[from_doc_id][to_doc_id] += strength * 0.1
        else:
            # Create new pathway
            self.neural_trails[from_doc_id][to_doc_id] = strength
    
    def _update_discovery_trails(self, documents: List[DocumentMetadata]):
        """Update discovery success patterns for future optimization"""
        print("🧠 Discovery Agent: Updating neural discovery trails...")
        
        # Analyze successful discovery patterns
        pattern_success = {}
        for doc in documents:
            pattern = doc.custom_fields.get('discovery_pattern', 'unknown')
            if pattern not in pattern_success:
                pattern_success[pattern] = {'count': 0, 'avg_importance': 0}
            
            pattern_success[pattern]['count'] += 1
            importance = doc.custom_fields.get('inferred_importance', 0.5)
            pattern_success[pattern]['avg_importance'] += importance
        
        # Calculate average importance per pattern
        for pattern, stats in pattern_success.items():
            stats['avg_importance'] /= stats['count']
        
        # Store for future use
        self.neural_trails['pattern_effectiveness'] = pattern_success
        
        print(f"📊 Discovery Agent: Pattern effectiveness analysis complete")
        for pattern, stats in pattern_success.items():
            print(f"   {pattern}: {stats['count']} docs, avg importance: {stats['avg_importance']:.2f}")
    
    async def get_discovery_insights(self) -> Dict[str, Any]:
        """Get insights from discovery process for swarm coordination"""
        return {
            'neural_pathways': len(self.neural_trails),
            'pattern_effectiveness': self.neural_trails.get('pattern_effectiveness', {}),
            'last_discovery': datetime.now().isoformat(),
            'swarm_intelligence': {
                'total_connections': sum(len(connections) for connections in self.neural_trails.values() 
                                       if isinstance(connections, dict)),
                'strongest_pathways': self._get_strongest_pathways(),
                'knowledge_clusters': self._identify_knowledge_clusters()
            }
        }
    
    def _get_strongest_pathways(self) -> List[Dict[str, Any]]:
        """Get the strongest neural pathways discovered"""
        pathways = []
        
        for from_doc, connections in self.neural_trails.items():
            if not isinstance(connections, dict):
                continue
                
            for to_doc, strength in connections.items():
                if strength > 0.7:  # Strong connections only
                    pathways.append({
                        'from': from_doc,
                        'to': to_doc,
                        'strength': strength
                    })
        
        return sorted(pathways, key=lambda x: x['strength'], reverse=True)[:10]
    
    def _identify_knowledge_clusters(self) -> List[Dict[str, Any]]:
        """Identify clusters of highly connected documents"""
        # Simplified clustering based on connection density
        clusters = []
        processed_docs = set()
        
        for doc_id, connections in self.neural_trails.items():
            if not isinstance(connections, dict) or doc_id in processed_docs:
                continue
            
            if len(connections) >= 3:  # Documents with 3+ connections form clusters
                cluster = {
                    'center': doc_id,
                    'connected_docs': list(connections.keys()),
                    'cluster_strength': sum(connections.values()) / len(connections),
                    'size': len(connections)
                }
                clusters.append(cluster)
                processed_docs.add(doc_id)
        
        return sorted(clusters, key=lambda x: x['cluster_strength'], reverse=True)[:5]


# Neural Document Discovery Functions
async def discover_documents_with_neural_intelligence(
    root_paths: List[str], 
    max_depth: int = 10
) -> Tuple[List[DocumentMetadata], Dict[str, Any]]:
    """
    Main function to discover documents using neural intelligence
    
    Returns:
        Tuple of (discovered documents, neural insights)
    """
    agent = DocumentDiscoveryAgent()
    
    # Discover documents
    documents = await agent.discover_documents(root_paths, max_depth)
    
    # Get neural insights
    insights = await agent.get_discovery_insights()
    
    return documents, insights


if __name__ == "__main__":
    # Test the discovery agent
    async def test_discovery():
        agent = DocumentDiscoveryAgent()
        docs = await agent.discover_documents(["."], max_depth=3)
        
        print(f"\n📋 Discovered {len(docs)} documents:")
        for doc in docs[:5]:  # Show first 5
            print(f"  - {doc.filename} ({doc.file_extension}) - {doc.word_count} words")
        
        insights = await agent.get_discovery_insights()
        print(f"\n🧠 Neural insights: {insights['swarm_intelligence']['total_connections']} connections")
    
    asyncio.run(test_discovery())