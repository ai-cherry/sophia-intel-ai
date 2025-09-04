#!/usr/bin/env python3
"""
Document Management Swarm Orchestrator - Revolutionary AI-powered document management
Implements Neural Documentation Networks, Quantum Document States, and Swarm Intelligence
"""

import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict

from ..agents.document_discovery_agent import DocumentDiscoveryAgent, discover_documents_with_neural_intelligence
from ..agents.document_classifier_agent import DocumentClassifierAgent, classify_documents_with_intelligence
from ..models.document import (
    DocumentMetadata, DocumentStatus, DocumentSwarmState, DocumentBatch,
    DocumentType, CleanupPolicy, DocumentProcessingResult
)


@dataclass
class SwarmConfiguration:
    """Configuration for the Document Management Swarm"""
    max_concurrent_workers: int = 10
    batch_size: int = 20
    discovery_max_depth: int = 15
    classification_confidence_threshold: float = 0.7
    cleanup_dry_run: bool = True
    enable_neural_networks: bool = True
    enable_quantum_states: bool = True
    auto_cleanup_threshold_days: int = 30
    min_ai_score_for_keep: float = 40.0


class DocumentSwarmOrchestrator:
    """Revolutionary orchestrator for AI-powered document management swarm"""
    
    def __init__(self, config: Optional[SwarmConfiguration] = None):
        self.config = config or SwarmConfiguration()
        self.state = DocumentSwarmState()
        self.logger = self._setup_logging()
        
        # Initialize swarm agents
        self.discovery_agent = DocumentDiscoveryAgent()
        self.classifier_agent = DocumentClassifierAgent()
        
        # Swarm intelligence
        self.swarm_memory = {}
        self.neural_networks = {}
        self.quantum_document_states = {}
        
        # Performance tracking
        self.performance_metrics = {
            'documents_processed': 0,
            'total_processing_time': 0.0,
            'classification_accuracy': 0.0,
            'cleanup_candidates_identified': 0,
            'neural_pathways_created': 0
        }
        
        self.logger.info("🚀 Document Management Swarm Orchestrator initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging for swarm operations"""
        logger = logging.getLogger('DocumentSwarm')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    async def unleash_swarm(self, root_paths: List[str]) -> Dict[str, Any]:
        """
        UNLEASH THE DOCUMENT MANAGEMENT SWARM!
        Complete end-to-end document analysis, cleanup, and optimization
        
        Args:
            root_paths: Paths to analyze for documents
            
        Returns:
            Comprehensive swarm operation results
        """
        start_time = datetime.now()
        self.logger.info(f"🔥 UNLEASHING DOCUMENT MANAGEMENT SWARM on {len(root_paths)} paths!")
        
        try:
            # Phase 1: Neural Document Discovery
            self.logger.info("📡 Phase 1: Neural Document Discovery")
            discovered_docs, discovery_insights = await self._phase_1_discovery(root_paths)
            
            # Phase 2: AI Classification & Scoring
            self.logger.info("🎯 Phase 2: AI Classification & Scoring")
            classified_docs, classification_insights = await self._phase_2_classification(discovered_docs)
            
            # Phase 3: Neural Network Formation
            self.logger.info("🧠 Phase 3: Neural Network Formation")
            networked_docs = await self._phase_3_neural_networks(classified_docs)
            
            # Phase 4: Quantum Document States
            self.logger.info("⚛️ Phase 4: Quantum Document States")
            quantum_docs = await self._phase_4_quantum_states(networked_docs)
            
            # Phase 5: Intelligent Cleanup Analysis
            self.logger.info("🧹 Phase 5: Intelligent Cleanup Analysis")
            cleanup_plan = await self._phase_5_cleanup_analysis(quantum_docs)
            
            # Phase 6: Swarm Intelligence Synthesis
            self.logger.info("🌟 Phase 6: Swarm Intelligence Synthesis")
            final_results = await self._phase_6_synthesis(
                quantum_docs, cleanup_plan, discovery_insights, classification_insights
            )
            
            # Calculate total time
            total_time = (datetime.now() - start_time).total_seconds()
            final_results['total_execution_time'] = total_time
            
            self.logger.info(f"✅ SWARM UNLEASHED! Processed {len(quantum_docs)} documents in {total_time:.2f}s")
            
            return final_results
            
        except Exception as e:
            self.logger.error(f"❌ Swarm operation failed: {e}")
            raise
    
    async def _phase_1_discovery(self, root_paths: List[str]) -> Tuple[List[DocumentMetadata], Dict[str, Any]]:
        """Phase 1: Discover all documents with neural intelligence"""
        self.state.discovery_queue = root_paths.copy()
        
        # Discover documents with neural pathfinding
        discovered_docs, insights = await discover_documents_with_neural_intelligence(
            root_paths, self.config.discovery_max_depth
        )
        
        # Update swarm state
        self.state.active_agents.append("DocumentDiscoverySpecialist")
        self.performance_metrics['documents_processed'] = len(discovered_docs)
        self.performance_metrics['neural_pathways_created'] = insights['swarm_intelligence']['total_connections']
        
        self.logger.info(f"📊 Discovery Results: {len(discovered_docs)} documents, {insights['neural_pathways']} pathways")
        
        return discovered_docs, insights
    
    async def _phase_2_classification(self, documents: List[DocumentMetadata]) -> Tuple[List[DocumentMetadata], Dict[str, Any]]:
        """Phase 2: Classify and score documents with AI intelligence"""
        self.state.classification_queue = [doc.id for doc in documents]
        
        # Classify with AI intelligence
        classified_docs, insights = await classify_documents_with_intelligence(documents)
        
        # Update swarm state
        self.state.active_agents.append("DocumentClassificationSpecialist")
        self.performance_metrics['classification_accuracy'] = insights['swarm_intelligence']['classification_accuracy']
        
        # Analyze classification results
        type_distribution = {}
        score_distribution = {'high': 0, 'medium': 0, 'low': 0}
        
        for doc in classified_docs:
            if isinstance(doc, Exception):
                continue
                
            if doc.classification:
                doc_type = doc.classification.primary_type.value
                type_distribution[doc_type] = type_distribution.get(doc_type, 0) + 1
            
            if doc.ai_score:
                if doc.ai_score.overall_score >= 75:
                    score_distribution['high'] += 1
                elif doc.ai_score.overall_score >= 50:
                    score_distribution['medium'] += 1
                else:
                    score_distribution['low'] += 1
        
        insights['type_distribution'] = type_distribution
        insights['score_distribution'] = score_distribution
        
        self.logger.info(f"📈 Classification Results: {len(type_distribution)} types, avg accuracy: {insights['swarm_intelligence']['classification_accuracy']:.1f}%")
        
        return classified_docs, insights
    
    async def _phase_3_neural_networks(self, documents: List[DocumentMetadata]) -> List[DocumentMetadata]:
        """Phase 3: Form neural networks between related documents"""
        if not self.config.enable_neural_networks:
            return documents
        
        self.logger.info("🧠 Forming neural document networks...")
        
        # Create neural networks based on document relationships
        for doc in documents:
            if isinstance(doc, Exception):
                continue
                
            doc_id = doc.id
            
            # Initialize neural node
            if doc_id not in self.neural_networks:
                self.neural_networks[doc_id] = {
                    'connections': {},
                    'activation_history': [],
                    'learning_rate': 0.1,
                    'specialization': doc.classification.primary_type.value if doc.classification else 'unknown'
                }
            
            # Form connections based on:
            # 1. Document type similarity
            # 2. Content references
            # 3. Directory proximity
            # 4. Naming patterns
            
            await self._form_neural_connections(doc, documents)
        
        # Strengthen pathways based on successful connections
        await self._strengthen_neural_pathways()
        
        self.logger.info(f"🔗 Neural networks formed: {len(self.neural_networks)} nodes, {self._count_neural_connections()} connections")
        
        return documents
    
    async def _form_neural_connections(self, doc: DocumentMetadata, all_docs: List[DocumentMetadata]):
        """Form neural connections for a specific document"""
        doc_network = self.neural_networks[doc.id]
        
        for other_doc in all_docs:
            if isinstance(other_doc, Exception) or other_doc.id == doc.id:
                continue
            
            connection_strength = 0.0
            
            # Type similarity connection
            if (doc.classification and other_doc.classification and 
                doc.classification.primary_type == other_doc.classification.primary_type):
                connection_strength += 0.3
            
            # Directory proximity connection
            doc_path = Path(doc.source_path)
            other_path = Path(other_doc.source_path)
            
            if doc_path.parent == other_path.parent:
                connection_strength += 0.4
            elif len(set(doc_path.parts) & set(other_path.parts)) >= 2:
                connection_strength += 0.2
            
            # Content reference connection
            if doc.custom_fields.get('discovered_references'):
                if other_doc.source_path in doc.custom_fields['discovered_references']:
                    connection_strength += 0.5
            
            # Naming pattern connection
            if self._has_similar_naming_pattern(doc.filename, other_doc.filename):
                connection_strength += 0.2
            
            # Create connection if strength is significant
            if connection_strength > 0.3:
                doc_network['connections'][other_doc.id] = connection_strength
    
    def _has_similar_naming_pattern(self, name1: str, name2: str) -> bool:
        """Check if two filenames have similar patterns"""
        # Remove extensions for comparison
        base1 = Path(name1).stem.lower()
        base2 = Path(name2).stem.lower()
        
        # Check for common patterns
        patterns = ['_report', '_guide', '_audit', '_plan', '_status', '_summary']
        
        for pattern in patterns:
            if pattern in base1 and pattern in base2:
                return True
        
        # Check for shared prefixes/suffixes
        if len(base1) > 4 and len(base2) > 4:
            if (base1[:4] == base2[:4] or  # Same prefix
                base1[-4:] == base2[-4:]):  # Same suffix
                return True
        
        return False
    
    async def _strengthen_neural_pathways(self):
        """Strengthen neural pathways based on successful connections"""
        for doc_id, network in self.neural_networks.items():
            # Strengthen connections that appear frequently across the network
            for connected_id, strength in network['connections'].items():
                if connected_id in self.neural_networks:
                    # Mutual reinforcement
                    reverse_strength = self.neural_networks[connected_id]['connections'].get(doc_id, 0.0)
                    if reverse_strength > 0:
                        # Strengthen both connections
                        network['connections'][connected_id] = min(1.0, strength + 0.1)
                        self.neural_networks[connected_id]['connections'][doc_id] = min(1.0, reverse_strength + 0.1)
    
    def _count_neural_connections(self) -> int:
        """Count total neural connections across the network"""
        return sum(len(network['connections']) for network in self.neural_networks.values())
    
    async def _phase_4_quantum_states(self, documents: List[DocumentMetadata]) -> List[DocumentMetadata]:
        """Phase 4: Create quantum document states for adaptive presentation"""
        if not self.config.enable_quantum_states:
            return documents
        
        self.logger.info("⚛️ Creating quantum document states...")
        
        for doc in documents:
            if isinstance(doc, Exception):
                continue
            
            # Create quantum superposition states for each document
            quantum_states = await self._create_quantum_states(doc)
            self.quantum_document_states[doc.id] = quantum_states
            
            # Add quantum metadata to document
            doc.custom_fields['quantum_states'] = quantum_states['available_states']
            doc.custom_fields['default_quantum_state'] = quantum_states['default_state']
        
        self.logger.info(f"⚛️ Quantum states created: {len(self.quantum_document_states)} document quantum systems")
        
        return documents
    
    async def _create_quantum_states(self, doc: DocumentMetadata) -> Dict[str, Any]:
        """Create quantum superposition states for a document"""
        states = {
            'available_states': [],
            'default_state': 'standard',
            'collapse_triggers': {},
            'entangled_documents': []
        }
        
        # Standard state (default)
        states['available_states'].append({
            'name': 'standard',
            'description': 'Standard document presentation',
            'verbosity': 'medium',
            'technical_level': 'intermediate'
        })
        
        # Beginner state (high verbosity, examples)
        if doc.ai_score and doc.ai_score.examples_included:
            states['available_states'].append({
                'name': 'beginner',
                'description': 'Beginner-friendly with extensive examples',
                'verbosity': 'high',
                'technical_level': 'basic',
                'emphasis': ['examples', 'explanations', 'context']
            })
        
        # Expert state (concise, technical)
        if doc.classification and doc.classification.primary_type in [
            DocumentType.API_DOCUMENTATION, DocumentType.ARCHITECTURE, DocumentType.CONFIGURATION
        ]:
            states['available_states'].append({
                'name': 'expert',
                'description': 'Concise technical reference',
                'verbosity': 'low',
                'technical_level': 'advanced',
                'emphasis': ['technical_details', 'parameters', 'specifications']
            })
        
        # Troubleshooting state (problem-focused)
        if (doc.classification and 
            DocumentType.TROUBLESHOOTING in [doc.classification.primary_type] + doc.classification.secondary_types):
            states['available_states'].append({
                'name': 'troubleshooting',
                'description': 'Problem-solving focused presentation',
                'verbosity': 'medium',
                'technical_level': 'practical',
                'emphasis': ['symptoms', 'solutions', 'diagnostics']
            })
        
        # Set up collapse triggers (when quantum state collapses to specific state)
        states['collapse_triggers'] = {
            'agent_type': {
                'beginner_agent': 'beginner',
                'expert_agent': 'expert', 
                'debugging_agent': 'troubleshooting',
                'default': 'standard'
            },
            'query_context': {
                'learning': 'beginner',
                'reference': 'expert',
                'debugging': 'troubleshooting',
                'default': 'standard'
            }
        }
        
        # Find entangled documents (documents that should update together)
        if doc.id in self.neural_networks:
            strong_connections = [
                connected_id for connected_id, strength in self.neural_networks[doc.id]['connections'].items()
                if strength > 0.7
            ]
            states['entangled_documents'] = strong_connections[:5]  # Limit entanglement
        
        return states
    
    async def _phase_5_cleanup_analysis(self, documents: List[DocumentMetadata]) -> Dict[str, Any]:
        """Phase 5: Analyze documents for intelligent cleanup opportunities"""
        cleanup_plan = {
            'candidates_for_deletion': [],
            'candidates_for_archival': [],
            'candidates_for_consolidation': [],
            'consolidation_groups': [],
            'cleanup_policies_applied': [],
            'safety_warnings': []
        }
        
        self.logger.info("🧹 Analyzing cleanup opportunities...")
        
        # Apply intelligent cleanup policies
        policies = self._create_default_cleanup_policies()
        
        for policy in policies:
            policy_results = await self._apply_cleanup_policy(policy, documents)
            cleanup_plan[f"policy_{policy.id}_results"] = policy_results
            cleanup_plan['cleanup_policies_applied'].append(policy.name)
        
        # Identify consolidation opportunities
        consolidation_groups = await self._identify_consolidation_opportunities(documents)
        cleanup_plan['consolidation_groups'] = consolidation_groups
        
        # Generate safety warnings
        safety_warnings = self._generate_safety_warnings(cleanup_plan, documents)
        cleanup_plan['safety_warnings'] = safety_warnings
        
        self.performance_metrics['cleanup_candidates_identified'] = (
            len(cleanup_plan['candidates_for_deletion']) +
            len(cleanup_plan['candidates_for_archival']) +
            len(cleanup_plan['consolidation_groups'])
        )
        
        self.logger.info(f"🎯 Cleanup analysis: {self.performance_metrics['cleanup_candidates_identified']} candidates identified")
        
        return cleanup_plan
    
    def _create_default_cleanup_policies(self) -> List[CleanupPolicy]:
        """Create intelligent default cleanup policies"""
        policies = []
        
        # Policy 1: One-time reports older than 30 days
        policies.append(CleanupPolicy(
            id="one_time_reports",
            name="Archive One-Time Reports",
            description="Archive one-time reports and status documents older than 30 days",
            conditions={
                "age_days": {"$gt": self.config.auto_cleanup_threshold_days},
                "is_likely_one_time": True,
                "ai_score": {"$lt": 60}
            },
            action="archive",
            safety_checks=["recent_access", "dependency_check"]
        ))
        
        # Policy 2: Low quality documents
        policies.append(CleanupPolicy(
            id="low_quality_docs",
            name="Flag Low Quality Documents",
            description="Flag documents with very low AI-friendliness scores for review",
            conditions={
                "ai_score": {"$lt": self.config.min_ai_score_for_keep}
            },
            action="flag_for_review",
            safety_checks=["manual_review_required"]
        ))
        
        # Policy 3: Duplicate content
        policies.append(CleanupPolicy(
            id="duplicate_content",
            name="Consolidate Duplicate Content",
            description="Identify and consolidate documents with duplicate or highly similar content",
            conditions={
                "content_similarity": {"$gt": 0.9}
            },
            action="consolidate",
            safety_checks=["content_merge_validation"]
        ))
        
        return policies
    
    async def _apply_cleanup_policy(self, policy: CleanupPolicy, 
                                  documents: List[DocumentMetadata]) -> Dict[str, Any]:
        """Apply a specific cleanup policy to documents"""
        results = {
            'policy_name': policy.name,
            'matched_documents': [],
            'action_recommendations': [],
            'safety_checks_passed': [],
            'safety_checks_failed': []
        }
        
        for doc in documents:
            if isinstance(doc, Exception):
                continue
            
            if await self._document_matches_policy(doc, policy):
                results['matched_documents'].append({
                    'document_id': doc.id,
                    'filename': doc.filename,
                    'reason': self._get_policy_match_reason(doc, policy)
                })
                
                # Check safety conditions
                safety_passed = await self._check_safety_conditions(doc, policy)
                if safety_passed:
                    results['action_recommendations'].append({
                        'document_id': doc.id,
                        'action': policy.action,
                        'confidence': 'high'
                    })
                    results['safety_checks_passed'].append(doc.id)
                else:
                    results['safety_checks_failed'].append(doc.id)
        
        return results
    
    async def _document_matches_policy(self, doc: DocumentMetadata, policy: CleanupPolicy) -> bool:
        """Check if document matches cleanup policy conditions"""
        conditions = policy.conditions
        
        # Age condition
        if "age_days" in conditions:
            age_condition = conditions["age_days"]
            doc_age_days = (datetime.now() - doc.modified_at).days
            
            if "$gt" in age_condition and doc_age_days <= age_condition["$gt"]:
                return False
            if "$lt" in age_condition and doc_age_days >= age_condition["$lt"]:
                return False
        
        # AI score condition
        if "ai_score" in conditions and doc.ai_score:
            score_condition = conditions["ai_score"]
            ai_score = doc.ai_score.overall_score
            
            if "$gt" in score_condition and ai_score <= score_condition["$gt"]:
                return False
            if "$lt" in score_condition and ai_score >= score_condition["$lt"]:
                return False
        
        # One-time document condition
        if "is_likely_one_time" in conditions:
            is_one_time = doc.custom_fields.get('is_likely_one_time', False)
            if conditions["is_likely_one_time"] != is_one_time:
                return False
        
        return True
    
    def _get_policy_match_reason(self, doc: DocumentMetadata, policy: CleanupPolicy) -> str:
        """Get human-readable reason why document matches policy"""
        reasons = []
        
        if "age_days" in policy.conditions:
            doc_age = (datetime.now() - doc.modified_at).days
            reasons.append(f"Age: {doc_age} days")
        
        if "ai_score" in policy.conditions and doc.ai_score:
            reasons.append(f"AI Score: {doc.ai_score.overall_score:.1f}")
        
        if "is_likely_one_time" in policy.conditions:
            reasons.append("Identified as one-time document")
        
        return "; ".join(reasons)
    
    async def _check_safety_conditions(self, doc: DocumentMetadata, policy: CleanupPolicy) -> bool:
        """Check if document passes safety conditions for cleanup action"""
        for safety_check in policy.safety_checks:
            if safety_check == "recent_access":
                # Check if document was accessed recently
                last_access = doc.last_accessed_at
                if last_access and (datetime.now() - last_access).days < 7:
                    return False
            
            elif safety_check == "dependency_check":
                # Check if other documents depend on this one
                if doc.id in self.neural_networks:
                    # Has strong neural connections (other docs reference it)
                    strong_connections = sum(
                        1 for strength in self.neural_networks[doc.id]['connections'].values()
                        if strength > 0.5
                    )
                    if strong_connections > 2:
                        return False
        
        return True
    
    async def _identify_consolidation_opportunities(self, documents: List[DocumentMetadata]) -> List[Dict[str, Any]]:
        """Identify opportunities to consolidate similar documents"""
        consolidation_groups = []
        processed_docs = set()
        
        for doc in documents:
            if isinstance(doc, Exception) or doc.id in processed_docs:
                continue
            
            # Find similar documents
            similar_docs = []
            for other_doc in documents:
                if (isinstance(other_doc, Exception) or 
                    other_doc.id == doc.id or 
                    other_doc.id in processed_docs):
                    continue
                
                similarity = await self._calculate_document_similarity(doc, other_doc)
                if similarity > 0.7:  # High similarity threshold
                    similar_docs.append({
                        'document': other_doc,
                        'similarity': similarity
                    })
            
            if similar_docs:
                # Create consolidation group
                group = {
                    'primary_document': {
                        'id': doc.id,
                        'filename': doc.filename,
                        'ai_score': doc.ai_score.overall_score if doc.ai_score else 0
                    },
                    'similar_documents': [
                        {
                            'id': item['document'].id,
                            'filename': item['document'].filename,
                            'similarity': item['similarity'],
                            'ai_score': item['document'].ai_score.overall_score if item['document'].ai_score else 0
                        }
                        for item in similar_docs
                    ],
                    'consolidation_strategy': self._suggest_consolidation_strategy(doc, similar_docs),
                    'estimated_space_savings': self._estimate_consolidation_savings(doc, similar_docs)
                }
                
                consolidation_groups.append(group)
                processed_docs.add(doc.id)
                for item in similar_docs:
                    processed_docs.add(item['document'].id)
        
        return consolidation_groups
    
    async def _calculate_document_similarity(self, doc1: DocumentMetadata, 
                                          doc2: DocumentMetadata) -> float:
        """Calculate similarity between two documents"""
        similarity = 0.0
        
        # Filename similarity
        if self._has_similar_naming_pattern(doc1.filename, doc2.filename):
            similarity += 0.3
        
        # Type similarity
        if (doc1.classification and doc2.classification and
            doc1.classification.primary_type == doc2.classification.primary_type):
            similarity += 0.2
        
        # Size similarity (within 50% of each other)
        size_ratio = min(doc1.size_bytes, doc2.size_bytes) / max(doc1.size_bytes, doc2.size_bytes)
        if size_ratio > 0.5:
            similarity += 0.2
        
        # Directory proximity
        if Path(doc1.source_path).parent == Path(doc2.source_path).parent:
            similarity += 0.3
        
        # Neural network connection
        if (doc1.id in self.neural_networks and 
            doc2.id in self.neural_networks[doc1.id]['connections']):
            connection_strength = self.neural_networks[doc1.id]['connections'][doc2.id]
            similarity += connection_strength * 0.3
        
        return min(1.0, similarity)
    
    def _suggest_consolidation_strategy(self, primary_doc: DocumentMetadata, 
                                      similar_docs: List[Dict]) -> str:
        """Suggest the best consolidation strategy for similar documents"""
        if len(similar_docs) == 1:
            return "merge_into_primary"
        elif len(similar_docs) <= 3:
            return "create_comprehensive_guide"
        else:
            return "create_topic_hub"
    
    def _estimate_consolidation_savings(self, primary_doc: DocumentMetadata,
                                      similar_docs: List[Dict]) -> Dict[str, Any]:
        """Estimate space and maintenance savings from consolidation"""
        total_size = primary_doc.size_bytes + sum(
            item['document'].size_bytes for item in similar_docs
        )
        
        # Assume 60-80% space savings from consolidation
        estimated_final_size = int(total_size * 0.3)  # 70% reduction
        space_saved = total_size - estimated_final_size
        
        return {
            'total_original_size_bytes': total_size,
            'estimated_consolidated_size_bytes': estimated_final_size,
            'space_saved_bytes': space_saved,
            'maintenance_overhead_reduction': f"{len(similar_docs)} -> 1 document",
            'readability_improvement_expected': True
        }
    
    def _generate_safety_warnings(self, cleanup_plan: Dict, 
                                documents: List[DocumentMetadata]) -> List[Dict[str, Any]]:
        """Generate safety warnings for cleanup operations"""
        warnings = []
        
        # Check for aggressive cleanup
        total_docs = len([d for d in documents if not isinstance(d, Exception)])
        cleanup_percentage = (cleanup_plan.get('cleanup_candidates_identified', 0) / total_docs) * 100
        
        if cleanup_percentage > 30:
            warnings.append({
                'level': 'high',
                'type': 'aggressive_cleanup',
                'message': f"High cleanup percentage ({cleanup_percentage:.1f}%) detected",
                'recommendation': "Consider manual review before executing cleanup"
            })
        
        # Check for potential important document deletion
        for doc in documents:
            if isinstance(doc, Exception):
                continue
                
            if (doc.filename.upper().startswith('README') or 
                'architecture' in doc.filename.lower()):
                warnings.append({
                    'level': 'medium',
                    'type': 'important_document',
                    'message': f"Important document in cleanup scope: {doc.filename}",
                    'recommendation': "Verify this document should be cleaned up"
                })
        
        return warnings
    
    async def _phase_6_synthesis(self, documents: List[DocumentMetadata], 
                               cleanup_plan: Dict[str, Any],
                               discovery_insights: Dict[str, Any],
                               classification_insights: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 6: Synthesize all swarm intelligence into final results"""
        
        # Calculate final metrics
        total_docs = len([d for d in documents if not isinstance(d, Exception)])
        
        # Document type distribution
        type_counts = {}
        score_stats = {'total': 0, 'sum': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        for doc in documents:
            if isinstance(doc, Exception):
                continue
                
            if doc.classification:
                doc_type = doc.classification.primary_type.value
                type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
            
            if doc.ai_score:
                score_stats['total'] += 1
                score_stats['sum'] += doc.ai_score.overall_score
                
                if doc.ai_score.overall_score >= 75:
                    score_stats['high'] += 1
                elif doc.ai_score.overall_score >= 50:
                    score_stats['medium'] += 1
                else:
                    score_stats['low'] += 1
        
        avg_ai_score = score_stats['sum'] / score_stats['total'] if score_stats['total'] > 0 else 0
        
        # Swarm intelligence summary
        swarm_intelligence = {
            'neural_networks': {
                'total_nodes': len(self.neural_networks),
                'total_connections': self._count_neural_connections(),
                'network_density': self._count_neural_connections() / max(len(self.neural_networks), 1),
                'strongest_pathways': self._get_top_neural_pathways()
            },
            'quantum_states': {
                'documents_with_quantum_states': len(self.quantum_document_states),
                'average_states_per_document': sum(
                    len(states['available_states']) for states in self.quantum_document_states.values()
                ) / max(len(self.quantum_document_states), 1),
                'entanglement_pairs': self._count_quantum_entanglements()
            },
            'emergent_patterns': self._identify_emergent_patterns(documents)
        }
        
        # Create comprehensive results
        results = {
            'swarm_operation_summary': {
                'total_documents_processed': total_docs,
                'documents_by_type': type_counts,
                'ai_friendliness_stats': {
                    'average_score': avg_ai_score,
                    'distribution': {
                        'high_quality': score_stats['high'],
                        'medium_quality': score_stats['medium'],
                        'low_quality': score_stats['low']
                    }
                }
            },
            'cleanup_analysis': cleanup_plan,
            'swarm_intelligence': swarm_intelligence,
            'performance_metrics': self.performance_metrics,
            'recommendations': self._generate_final_recommendations(
                documents, cleanup_plan, swarm_intelligence
            ),
            'next_steps': self._generate_next_steps(cleanup_plan, swarm_intelligence)
        }
        
        return results
    
    def _get_top_neural_pathways(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """Get the strongest neural pathways in the network"""
        pathways = []
        
        for doc_id, network in self.neural_networks.items():
            for connected_id, strength in network['connections'].items():
                pathways.append({
                    'from_document': doc_id,
                    'to_document': connected_id,
                    'connection_strength': strength,
                    'pathway_type': 'neural'
                })
        
        return sorted(pathways, key=lambda x: x['connection_strength'], reverse=True)[:top_n]
    
    def _count_quantum_entanglements(self) -> int:
        """Count quantum entanglement pairs"""
        entanglements = 0
        for states in self.quantum_document_states.values():
            entanglements += len(states.get('entangled_documents', []))
        return entanglements // 2  # Avoid double counting pairs
    
    def _identify_emergent_patterns(self, documents: List[DocumentMetadata]) -> List[Dict[str, Any]]:
        """Identify emergent patterns from swarm behavior"""
        patterns = []
        
        # Pattern 1: Document clusters by directory
        directory_clusters = {}
        for doc in documents:
            if isinstance(doc, Exception):
                continue
            
            directory = str(Path(doc.source_path).parent)
            if directory not in directory_clusters:
                directory_clusters[directory] = []
            directory_clusters[directory].append(doc)
        
        large_clusters = {d: docs for d, docs in directory_clusters.items() if len(docs) > 5}
        if large_clusters:
            patterns.append({
                'type': 'directory_clustering',
                'description': f"Found {len(large_clusters)} directories with 5+ documents",
                'data': {d: len(docs) for d, docs in large_clusters.items()}
            })
        
        # Pattern 2: Document type specialization
        type_specialization = {}
        for doc in documents:
            if isinstance(doc, Exception) or not doc.classification:
                continue
            
            doc_type = doc.classification.primary_type.value
            directory = str(Path(doc.source_path).parent)
            
            if directory not in type_specialization:
                type_specialization[directory] = {}
            
            if doc_type not in type_specialization[directory]:
                type_specialization[directory][doc_type] = 0
            
            type_specialization[directory][doc_type] += 1
        
        specialized_dirs = {
            d: types for d, types in type_specialization.items()
            if len(types) == 1 and list(types.values())[0] > 2
        }
        
        if specialized_dirs:
            patterns.append({
                'type': 'type_specialization',
                'description': f"Found {len(specialized_dirs)} directories specialized in single document types",
                'data': specialized_dirs
            })
        
        return patterns
    
    def _generate_final_recommendations(self, documents: List[DocumentMetadata],
                                      cleanup_plan: Dict[str, Any],
                                      swarm_intelligence: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate final recommendations based on swarm analysis"""
        recommendations = []
        
        # Cleanup recommendations
        cleanup_candidates = cleanup_plan.get('cleanup_candidates_identified', 0)
        if cleanup_candidates > 0:
            recommendations.append({
                'category': 'cleanup',
                'priority': 'high',
                'action': 'Execute Cleanup Plan',
                'description': f"Implement cleanup for {cleanup_candidates} identified candidates",
                'benefits': ['Reduced maintenance overhead', 'Improved knowledge navigation', 'Better AI processing efficiency']
            })
        
        # Consolidation recommendations
        consolidation_groups = cleanup_plan.get('consolidation_groups', [])
        if consolidation_groups:
            recommendations.append({
                'category': 'consolidation',
                'priority': 'medium',
                'action': 'Consolidate Similar Documents',
                'description': f"Merge {len(consolidation_groups)} groups of similar documents",
                'benefits': ['Eliminated redundancy', 'Improved content quality', 'Easier maintenance']
            })
        
        # Neural network recommendations
        network_density = swarm_intelligence['neural_networks']['network_density']
        if network_density < 0.3:  # Sparse network
            recommendations.append({
                'category': 'connectivity',
                'priority': 'medium',
                'action': 'Improve Document Connectivity',
                'description': 'Add cross-references and links between related documents',
                'benefits': ['Better knowledge discovery', 'Improved AI navigation', 'Enhanced user experience']
            })
        
        # Quality improvement recommendations
        total_docs = len([d for d in documents if not isinstance(d, Exception)])
        low_quality_count = sum(
            1 for doc in documents
            if (not isinstance(doc, Exception) and doc.ai_score and doc.ai_score.overall_score < 50)
        )
        
        if low_quality_count / total_docs > 0.3:  # More than 30% low quality
            recommendations.append({
                'category': 'quality',
                'priority': 'high',
                'action': 'Launch Quality Improvement Initiative',
                'description': f'Improve {low_quality_count} low-quality documents',
                'benefits': ['Better AI processing', 'Improved user experience', 'Higher information value']
            })
        
        return recommendations
    
    def _generate_next_steps(self, cleanup_plan: Dict[str, Any], 
                           swarm_intelligence: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate specific next steps for implementation"""
        next_steps = []
        
        # Step 1: Review cleanup plan
        if cleanup_plan.get('safety_warnings'):
            next_steps.append({
                'step': 1,
                'action': 'Review Safety Warnings',
                'description': 'Manually review all safety warnings before proceeding',
                'estimated_time': '30-60 minutes',
                'prerequisites': []
            })
        
        # Step 2: Execute cleanup (if safe)
        if cleanup_plan.get('cleanup_candidates_identified', 0) > 0:
            next_steps.append({
                'step': 2,
                'action': 'Execute Cleanup Plan',
                'description': 'Run cleanup operations in dry-run mode first, then execute',
                'estimated_time': '1-2 hours',
                'prerequisites': ['Review Safety Warnings']
            })
        
        # Step 3: Implement neural improvements
        network_connections = swarm_intelligence['neural_networks']['total_connections']
        if network_connections > 50:
            next_steps.append({
                'step': 3,
                'action': 'Implement Neural Pathways',
                'description': 'Add cross-references based on discovered neural connections',
                'estimated_time': '2-4 hours',
                'prerequisites': []
            })
        
        # Step 4: Deploy quantum states
        quantum_docs = swarm_intelligence['quantum_states']['documents_with_quantum_states']
        if quantum_docs > 10:
            next_steps.append({
                'step': 4,
                'action': 'Deploy Quantum Document States',
                'description': 'Implement adaptive document presentation system',
                'estimated_time': '4-8 hours',
                'prerequisites': ['Implement Neural Pathways']
            })
        
        return next_steps
    
    async def save_swarm_state(self, results: Dict[str, Any], output_path: str = "swarm_results.json"):
        """Save complete swarm operation results"""
        output_file = Path(output_path)
        
        # Ensure results are JSON serializable
        serializable_results = self._make_json_serializable(results)
        
        async with aiofiles.open(output_file, 'w') as f:
            await f.write(json.dumps(serializable_results, indent=2))
        
        self.logger.info(f"💾 Swarm results saved to: {output_file}")
        
        # Also save a summary report
        await self._save_summary_report(serializable_results, f"{output_file.stem}_summary.md")
    
    def _make_json_serializable(self, obj: Any) -> Any:
        """Make object JSON serializable"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif hasattr(obj, '__dict__'):
            return self._make_json_serializable(obj.__dict__)
        else:
            return obj
    
    async def _save_summary_report(self, results: Dict[str, Any], output_path: str):
        """Save human-readable summary report"""
        summary = f"""# Document Management Swarm - Operation Summary

## 📊 Overview
- **Total Documents Processed**: {results['swarm_operation_summary']['total_documents_processed']}
- **Average AI-Friendliness Score**: {results['swarm_operation_summary']['ai_friendliness_stats']['average_score']:.1f}/100
- **Execution Time**: {results.get('total_execution_time', 0):.2f} seconds

## 📈 Document Distribution
"""
        
        for doc_type, count in results['swarm_operation_summary']['documents_by_type'].items():
            summary += f"- **{doc_type}**: {count} documents\n"
        
        summary += f"""
## 🧠 Swarm Intelligence Results
- **Neural Network Nodes**: {results['swarm_intelligence']['neural_networks']['total_nodes']}
- **Neural Connections**: {results['swarm_intelligence']['neural_networks']['total_connections']}
- **Quantum Document States**: {results['swarm_intelligence']['quantum_states']['documents_with_quantum_states']}

## 🧹 Cleanup Analysis
- **Cleanup Candidates**: {results['cleanup_analysis'].get('cleanup_candidates_identified', 0)}
- **Safety Warnings**: {len(results['cleanup_analysis'].get('safety_warnings', []))}
- **Consolidation Groups**: {len(results['cleanup_analysis'].get('consolidation_groups', []))}

## 🎯 Recommendations
"""
        
        for i, rec in enumerate(results.get('recommendations', []), 1):
            summary += f"{i}. **{rec['action']}** ({rec['priority']} priority)\n   - {rec['description']}\n"
        
        summary += f"""
## 🚀 Next Steps
"""
        
        for step in results.get('next_steps', []):
            summary += f"{step['step']}. **{step['action']}** (Est. {step['estimated_time']})\n   - {step['description']}\n"
        
        summary += f"""
---
*Generated by Document Management Swarm on {datetime.now().isoformat()}*
"""
        
        async with aiofiles.open(output_path, 'w') as f:
            await f.write(summary)
        
        self.logger.info(f"📝 Summary report saved to: {output_path}")


# Main orchestration function
async def unleash_document_management_swarm(
    root_paths: List[str],
    config: Optional[SwarmConfiguration] = None,
    save_results: bool = True
) -> Dict[str, Any]:
    """
    UNLEASH THE REVOLUTIONARY DOCUMENT MANAGEMENT SWARM!
    
    This is the main entry point for the complete document management system.
    
    Args:
        root_paths: Paths to analyze for documents
        config: Optional swarm configuration
        save_results: Whether to save results to files
    
    Returns:
        Comprehensive swarm operation results
    """
    orchestrator = DocumentSwarmOrchestrator(config)
    
    # UNLEASH THE SWARM!
    results = await orchestrator.unleash_swarm(root_paths)
    
    # Save results if requested
    if save_results:
        await orchestrator.save_swarm_state(results)
    
    return results


if __name__ == "__main__":
    # Example usage
    async def main():
        config = SwarmConfiguration(
            max_concurrent_workers=15,
            batch_size=25,
            discovery_max_depth=20,
            cleanup_dry_run=True,  # Safety first!
            enable_neural_networks=True,
            enable_quantum_states=True
        )
        
        # Unleash the swarm on current directory
        results = await unleash_document_management_swarm(["."], config)
        
        print(f"\n🎉 SWARM OPERATION COMPLETE!")
        print(f"📊 Processed: {results['swarm_operation_summary']['total_documents_processed']} documents")
        print(f"🧠 Neural connections: {results['swarm_intelligence']['neural_networks']['total_connections']}")
        print(f"⚛️ Quantum states: {results['swarm_intelligence']['quantum_states']['documents_with_quantum_states']}")
        print(f"🧹 Cleanup candidates: {results['cleanup_analysis'].get('cleanup_candidates_identified', 0)}")
    
    # Uncomment to test
    # asyncio.run(main())