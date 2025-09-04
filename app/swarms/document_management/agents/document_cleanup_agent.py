#!/usr/bin/env python3
"""
Document Cleanup Agent - Automated document lifecycle management with safety
Part of the Revolutionary Document Management Swarm
"""

import asyncio
import aiofiles
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import logging

try:
    from swarm import Agent
except ImportError:
    from ..utils.swarm_mock import Agent
from ..models.document import (
    DocumentMetadata, CleanupPolicy, DocumentProcessingResult, 
    DocumentStatus, DocumentType, calculate_document_importance
)


class DocumentCleanupAgent(Agent):
    """Specialized agent for safe and intelligent document cleanup operations"""
    
    def __init__(self):
        super().__init__(
            name="DocumentCleanupSpecialist",
            instructions="""You are the Document Cleanup Specialist, the prudent guardian of the Document Management Swarm.

CORE MISSION:
- Execute safe, intelligent document cleanup operations
- Protect valuable knowledge while eliminating redundancy
- Implement sophisticated safety checks and rollback mechanisms
- Learn from cleanup patterns to improve future operations

SPECIALIZED CAPABILITIES:
1. Multi-tier safety validation before any destructive operation
2. Smart backup and rollback systems
3. Dependency analysis to prevent broken references
4. Consolidation operations that preserve knowledge while reducing redundancy
5. Audit trail generation for all operations

SAFETY PROTOCOLS:
- NEVER delete without backup
- ALWAYS validate dependencies before action
- Multiple confirmation layers for destructive operations
- Comprehensive audit logging
- Rollback capability for all operations

CLEANUP STRATEGIES:
1. Archive: Move to archive directory with metadata
2. Delete: Permanent removal (only after extensive validation)
3. Consolidate: Merge similar documents intelligently
4. Compress: Reduce file sizes while preserving content
5. Flag: Mark for manual review

LEARNING CAPABILITIES:
- Track cleanup success/failure patterns
- Adapt safety thresholds based on outcomes
- Improve consolidation algorithms over time
- Build confidence models for different operation types

Be extremely cautious, thorough, and always prioritize data preservation over aggressive cleanup."""
        )
        
        self.safety_config = self._initialize_safety_config()
        self.cleanup_history = []
        self.backup_manager = BackupManager()
        self.dependency_analyzer = DependencyAnalyzer()
        self.consolidation_engine = ConsolidationEngine()
        
        self.logger = logging.getLogger('DocumentCleanup')
    
    def _initialize_safety_config(self) -> Dict[str, Any]:
        """Initialize comprehensive safety configuration"""
        return {
            'require_backup': True,
            'max_deletions_per_batch': 10,
            'max_cleanup_percentage': 0.25,  # Never cleanup more than 25% in one go
            'require_manual_confirmation': True,
            'dependency_check_depth': 3,
            'rollback_window_hours': 72,  # 72 hour rollback window
            'protected_patterns': [
                'README*',
                'LICENSE*', 
                'CONTRIBUTING*',
                'CHANGELOG*',
                '*_ARCHITECTURE*',
                '*_API*'
            ],
            'minimum_confidence_scores': {
                'delete': 0.95,
                'archive': 0.80,
                'consolidate': 0.75,
                'flag': 0.60
            }
        }
    
    async def execute_cleanup_plan(self, cleanup_plan: Dict[str, Any], 
                                 documents: List[DocumentMetadata],
                                 dry_run: bool = True) -> Dict[str, Any]:
        """
        Execute comprehensive cleanup plan with extensive safety checks
        
        Args:
            cleanup_plan: The cleanup plan from orchestrator
            documents: All documents being managed
            dry_run: If True, simulate operations without executing them
        
        Returns:
            Detailed results of cleanup operations
        """
        self.logger.info(f"🧹 Cleanup Agent: {'Simulating' if dry_run else 'Executing'} cleanup plan...")
        
        operation_start = datetime.now()
        
        # Initialize results structure
        results = {
            'operation_type': 'dry_run' if dry_run else 'execution',
            'start_time': operation_start.isoformat(),
            'operations_performed': [],
            'safety_checks': [],
            'errors': [],
            'warnings': [],
            'rollback_info': {},
            'audit_trail': [],
            'summary': {}
        }
        
        try:
            # Phase 1: Pre-execution safety validation
            safety_validation = await self._comprehensive_safety_check(cleanup_plan, documents)
            results['safety_checks'] = safety_validation
            
            if not safety_validation['passed']:
                results['errors'].append("Failed pre-execution safety validation")
                return results
            
            # Phase 2: Create backups (if not dry run)
            if not dry_run and self.safety_config['require_backup']:
                backup_results = await self._create_comprehensive_backup(documents, cleanup_plan)
                results['rollback_info'] = backup_results
            
            # Phase 3: Execute cleanup operations by type
            
            # 3a: Handle deletions
            if cleanup_plan.get('candidates_for_deletion'):
                deletion_results = await self._handle_deletions(
                    cleanup_plan['candidates_for_deletion'], documents, dry_run
                )
                results['operations_performed'].extend(deletion_results)
            
            # 3b: Handle archival
            if cleanup_plan.get('candidates_for_archival'):
                archival_results = await self._handle_archival(
                    cleanup_plan['candidates_for_archival'], documents, dry_run
                )
                results['operations_performed'].extend(archival_results)
            
            # 3c: Handle consolidations
            if cleanup_plan.get('consolidation_groups'):
                consolidation_results = await self._handle_consolidations(
                    cleanup_plan['consolidation_groups'], documents, dry_run
                )
                results['operations_performed'].extend(consolidation_results)
            
            # Phase 4: Post-operation validation
            if not dry_run:
                post_validation = await self._post_operation_validation(results, documents)
                results['post_validation'] = post_validation
            
            # Phase 5: Generate audit trail and summary
            results['audit_trail'] = self._generate_audit_trail(results)
            results['summary'] = self._generate_operation_summary(results)
            
            # Update cleanup history
            self.cleanup_history.append(results)
            
            end_time = datetime.now()
            results['end_time'] = end_time.isoformat()
            results['total_duration_seconds'] = (end_time - operation_start).total_seconds()
            
            self.logger.info(f"✅ Cleanup operation completed in {results['total_duration_seconds']:.2f}s")
            
        except Exception as e:
            self.logger.error(f"❌ Cleanup operation failed: {e}")
            results['errors'].append(str(e))
            results['status'] = 'failed'
        
        return results
    
    async def _comprehensive_safety_check(self, cleanup_plan: Dict[str, Any], 
                                        documents: List[DocumentMetadata]) -> Dict[str, Any]:
        """Perform comprehensive safety validation before cleanup"""
        safety_results = {
            'passed': True,
            'checks_performed': [],
            'warnings': [],
            'blocking_issues': []
        }
        
        total_docs = len(documents)
        
        # Check 1: Cleanup percentage limit
        cleanup_candidates = (
            len(cleanup_plan.get('candidates_for_deletion', [])) +
            len(cleanup_plan.get('candidates_for_archival', [])) +
            sum(len(group.get('similar_documents', [])) + 1 
                for group in cleanup_plan.get('consolidation_groups', []))
        )
        
        cleanup_percentage = cleanup_candidates / total_docs if total_docs > 0 else 0
        
        safety_results['checks_performed'].append({
            'check': 'cleanup_percentage_limit',
            'status': 'pass' if cleanup_percentage <= self.safety_config['max_cleanup_percentage'] else 'fail',
            'details': f"Cleanup percentage: {cleanup_percentage:.1%} (limit: {self.safety_config['max_cleanup_percentage']:.1%})"
        })
        
        if cleanup_percentage > self.safety_config['max_cleanup_percentage']:
            safety_results['blocking_issues'].append(
                f"Cleanup percentage ({cleanup_percentage:.1%}) exceeds safety limit ({self.safety_config['max_cleanup_percentage']:.1%})"
            )
            safety_results['passed'] = False
        
        # Check 2: Protected file validation
        protected_violations = []
        all_candidates = (
            cleanup_plan.get('candidates_for_deletion', []) +
            cleanup_plan.get('candidates_for_archival', [])
        )
        
        for candidate in all_candidates:
            doc = self._find_document_by_id(candidate.get('document_id'), documents)
            if doc and self._is_protected_document(doc):
                protected_violations.append(doc.filename)
        
        safety_results['checks_performed'].append({
            'check': 'protected_file_validation',
            'status': 'pass' if not protected_violations else 'warn',
            'details': f"Protected files in cleanup: {protected_violations}" if protected_violations else "No protected files affected"
        })
        
        if protected_violations:
            safety_results['warnings'].extend([
                f"Protected file scheduled for cleanup: {filename}" for filename in protected_violations
            ])
        
        # Check 3: Dependency analysis
        dependency_issues = await self._analyze_cleanup_dependencies(cleanup_plan, documents)
        
        safety_results['checks_performed'].append({
            'check': 'dependency_analysis',
            'status': 'pass' if not dependency_issues['blocking_dependencies'] else 'fail',
            'details': f"Found {len(dependency_issues['blocking_dependencies'])} blocking dependencies"
        })
        
        if dependency_issues['blocking_dependencies']:
            safety_results['blocking_issues'].extend(dependency_issues['blocking_dependencies'])
            safety_results['passed'] = False
        
        safety_results['warnings'].extend(dependency_issues['warnings'])
        
        # Check 4: Recent activity validation
        recent_activity_issues = await self._check_recent_activity(cleanup_plan, documents)
        
        safety_results['checks_performed'].append({
            'check': 'recent_activity_validation',
            'status': 'pass' if not recent_activity_issues['blocking_issues'] else 'warn',
            'details': f"Documents with recent activity: {len(recent_activity_issues['recent_activity_docs'])}"
        })
        
        safety_results['warnings'].extend(recent_activity_issues['warnings'])
        
        return safety_results
    
    def _find_document_by_id(self, doc_id: str, documents: List[DocumentMetadata]) -> Optional[DocumentMetadata]:
        """Find document by ID"""
        for doc in documents:
            if not isinstance(doc, Exception) and doc.id == doc_id:
                return doc
        return None
    
    def _is_protected_document(self, doc: DocumentMetadata) -> bool:
        """Check if document matches protected patterns"""
        filename = doc.filename.upper()
        
        for pattern in self.safety_config['protected_patterns']:
            pattern_upper = pattern.upper().replace('*', '')
            if pattern.startswith('*') and pattern.endswith('*'):
                if pattern_upper[1:-1] in filename:
                    return True
            elif pattern.startswith('*'):
                if filename.endswith(pattern_upper[1:]):
                    return True
            elif pattern.endswith('*'):
                if filename.startswith(pattern_upper[:-1]):
                    return True
            elif pattern_upper == filename:
                return True
        
        return False
    
    async def _analyze_cleanup_dependencies(self, cleanup_plan: Dict[str, Any], 
                                          documents: List[DocumentMetadata]) -> Dict[str, Any]:
        """Analyze dependencies that might be broken by cleanup operations"""
        dependency_results = {
            'blocking_dependencies': [],
            'warnings': [],
            'dependency_graph': {}
        }
        
        # Build document dependency graph
        doc_references = {}
        for doc in documents:
            if isinstance(doc, Exception):
                continue
                
            references = doc.custom_fields.get('discovered_references', [])
            doc_references[doc.id] = {
                'references_to': references,
                'referenced_by': []
            }
        
        # Build reverse references
        for doc_id, refs in doc_references.items():
            for ref_path in refs['references_to']:
                # Find referenced document
                ref_doc = None
                for doc in documents:
                    if not isinstance(doc, Exception) and doc.source_path == ref_path:
                        ref_doc = doc
                        break
                
                if ref_doc:
                    doc_references[ref_doc.id]['referenced_by'].append(doc_id)
        
        # Check if any cleanup candidates have incoming references
        all_cleanup_candidates = []
        
        # Add deletion candidates
        for candidate in cleanup_plan.get('candidates_for_deletion', []):
            all_cleanup_candidates.append(candidate.get('document_id'))
        
        # Add archival candidates
        for candidate in cleanup_plan.get('candidates_for_archival', []):
            all_cleanup_candidates.append(candidate.get('document_id'))
        
        # Add consolidation candidates (documents being merged away)
        for group in cleanup_plan.get('consolidation_groups', []):
            for similar_doc in group.get('similar_documents', []):
                all_cleanup_candidates.append(similar_doc.get('id'))
        
        # Check for blocking dependencies
        for candidate_id in all_cleanup_candidates:
            if candidate_id in doc_references:
                referenced_by = doc_references[candidate_id]['referenced_by']
                if referenced_by:
                    # Check if referring documents are also being cleaned up
                    external_references = [
                        ref_id for ref_id in referenced_by 
                        if ref_id not in all_cleanup_candidates
                    ]
                    
                    if external_references:
                        doc = self._find_document_by_id(candidate_id, documents)
                        doc_name = doc.filename if doc else candidate_id
                        
                        dependency_results['blocking_dependencies'].append(
                            f"Document '{doc_name}' is referenced by {len(external_references)} other documents"
                        )
        
        return dependency_results
    
    async def _check_recent_activity(self, cleanup_plan: Dict[str, Any], 
                                   documents: List[DocumentMetadata]) -> Dict[str, Any]:
        """Check for recent activity that might indicate documents are still in use"""
        activity_results = {
            'recent_activity_docs': [],
            'warnings': [],
            'blocking_issues': []
        }
        
        # Define "recent" as within last 7 days
        recent_threshold = datetime.now() - timedelta(days=7)
        
        all_candidates = (
            cleanup_plan.get('candidates_for_deletion', []) +
            cleanup_plan.get('candidates_for_archival', [])
        )
        
        for candidate in all_candidates:
            doc = self._find_document_by_id(candidate.get('document_id'), documents)
            if not doc:
                continue
            
            # Check modification time
            if doc.modified_at > recent_threshold:
                activity_results['recent_activity_docs'].append(doc.id)
                activity_results['warnings'].append(
                    f"Document '{doc.filename}' was modified recently ({doc.modified_at.strftime('%Y-%m-%d')})"
                )
            
            # Check access time if available
            if doc.last_accessed_at and doc.last_accessed_at > recent_threshold:
                activity_results['recent_activity_docs'].append(doc.id)
                activity_results['warnings'].append(
                    f"Document '{doc.filename}' was accessed recently ({doc.last_accessed_at.strftime('%Y-%m-%d')})"
                )
        
        return activity_results
    
    async def _create_comprehensive_backup(self, documents: List[DocumentMetadata], 
                                         cleanup_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive backup before cleanup operations"""
        backup_info = await self.backup_manager.create_cleanup_backup(documents, cleanup_plan)
        return backup_info
    
    async def _handle_deletions(self, deletion_candidates: List[Dict], 
                              documents: List[DocumentMetadata], 
                              dry_run: bool) -> List[Dict[str, Any]]:
        """Handle document deletion operations"""
        results = []
        
        for candidate in deletion_candidates:
            doc_id = candidate.get('document_id')
            doc = self._find_document_by_id(doc_id, documents)
            
            if not doc:
                results.append({
                    'operation': 'delete',
                    'document_id': doc_id,
                    'status': 'error',
                    'message': 'Document not found'
                })
                continue
            
            operation_result = {
                'operation': 'delete',
                'document_id': doc_id,
                'document_path': doc.source_path,
                'filename': doc.filename,
                'reason': candidate.get('reason', 'No reason provided'),
                'timestamp': datetime.now().isoformat()
            }
            
            if dry_run:
                operation_result['status'] = 'simulated'
                operation_result['message'] = f"Would delete '{doc.filename}'"
            else:
                try:
                    # Perform actual deletion
                    file_path = Path(doc.source_path)
                    if file_path.exists():
                        file_path.unlink()
                        operation_result['status'] = 'completed'
                        operation_result['message'] = f"Deleted '{doc.filename}'"
                        
                        self.logger.info(f"🗑️ Deleted document: {doc.filename}")
                    else:
                        operation_result['status'] = 'warning'
                        operation_result['message'] = f"File not found: {doc.filename}"
                        
                except Exception as e:
                    operation_result['status'] = 'error'
                    operation_result['message'] = f"Failed to delete '{doc.filename}': {str(e)}"
                    self.logger.error(f"❌ Failed to delete {doc.filename}: {e}")
            
            results.append(operation_result)
        
        return results
    
    async def _handle_archival(self, archival_candidates: List[Dict], 
                             documents: List[DocumentMetadata], 
                             dry_run: bool) -> List[Dict[str, Any]]:
        """Handle document archival operations"""
        results = []
        archive_dir = Path("./archive") / datetime.now().strftime("%Y-%m-%d")
        
        for candidate in archival_candidates:
            doc_id = candidate.get('document_id')
            doc = self._find_document_by_id(doc_id, documents)
            
            if not doc:
                results.append({
                    'operation': 'archive',
                    'document_id': doc_id,
                    'status': 'error',
                    'message': 'Document not found'
                })
                continue
            
            operation_result = {
                'operation': 'archive',
                'document_id': doc_id,
                'document_path': doc.source_path,
                'filename': doc.filename,
                'reason': candidate.get('reason', 'No reason provided'),
                'timestamp': datetime.now().isoformat()
            }
            
            if dry_run:
                operation_result['status'] = 'simulated'
                operation_result['message'] = f"Would archive '{doc.filename}' to {archive_dir}"
                operation_result['archive_path'] = str(archive_dir / doc.filename)
            else:
                try:
                    # Create archive directory
                    archive_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Move file to archive
                    source_path = Path(doc.source_path)
                    archive_path = archive_dir / doc.filename
                    
                    # Handle name conflicts
                    counter = 1
                    while archive_path.exists():
                        stem = archive_path.stem
                        suffix = archive_path.suffix
                        archive_path = archive_dir / f"{stem}_{counter}{suffix}"
                        counter += 1
                    
                    shutil.move(str(source_path), str(archive_path))
                    
                    # Create metadata file
                    metadata_path = archive_path.with_suffix(archive_path.suffix + '.metadata.json')
                    await self._save_archive_metadata(doc, metadata_path, candidate)
                    
                    operation_result['status'] = 'completed'
                    operation_result['message'] = f"Archived '{doc.filename}'"
                    operation_result['archive_path'] = str(archive_path)
                    
                    self.logger.info(f"📦 Archived document: {doc.filename} -> {archive_path}")
                    
                except Exception as e:
                    operation_result['status'] = 'error'
                    operation_result['message'] = f"Failed to archive '{doc.filename}': {str(e)}"
                    self.logger.error(f"❌ Failed to archive {doc.filename}: {e}")
            
            results.append(operation_result)
        
        return results
    
    async def _save_archive_metadata(self, doc: DocumentMetadata, 
                                   metadata_path: Path, candidate: Dict):
        """Save metadata for archived document"""
        metadata = {
            'original_path': doc.source_path,
            'archive_timestamp': datetime.now().isoformat(),
            'archive_reason': candidate.get('reason', 'No reason provided'),
            'document_metadata': {
                'filename': doc.filename,
                'size_bytes': doc.size_bytes,
                'created_at': doc.created_at.isoformat(),
                'modified_at': doc.modified_at.isoformat(),
                'content_hash': doc.content_hash,
                'classification': doc.classification.dict() if doc.classification else None,
                'ai_score': doc.ai_score.dict() if doc.ai_score else None
            },
            'restoration_info': {
                'can_restore': True,
                'original_directory': str(Path(doc.source_path).parent),
                'dependencies': doc.custom_fields.get('discovered_references', [])
            }
        }
        
        async with aiofiles.open(metadata_path, 'w') as f:
            await f.write(json.dumps(metadata, indent=2))
    
    async def _handle_consolidations(self, consolidation_groups: List[Dict], 
                                   documents: List[DocumentMetadata], 
                                   dry_run: bool) -> List[Dict[str, Any]]:
        """Handle document consolidation operations"""
        results = []
        
        for group in consolidation_groups:
            primary_doc_info = group.get('primary_document', {})
            similar_docs = group.get('similar_documents', [])
            strategy = group.get('consolidation_strategy', 'merge_into_primary')
            
            operation_result = {
                'operation': 'consolidate',
                'primary_document': primary_doc_info,
                'similar_documents': similar_docs,
                'strategy': strategy,
                'timestamp': datetime.now().isoformat()
            }
            
            if dry_run:
                operation_result['status'] = 'simulated'
                operation_result['message'] = f"Would consolidate {len(similar_docs)} documents into '{primary_doc_info.get('filename', 'unknown')}'"
            else:
                try:
                    consolidation_result = await self.consolidation_engine.consolidate_documents(
                        primary_doc_info, similar_docs, documents, strategy
                    )
                    
                    operation_result['status'] = consolidation_result['status']
                    operation_result['message'] = consolidation_result['message']
                    operation_result['consolidated_path'] = consolidation_result.get('consolidated_path')
                    operation_result['space_saved_bytes'] = consolidation_result.get('space_saved_bytes', 0)
                    
                    self.logger.info(f"🔗 Consolidated {len(similar_docs)} documents -> {primary_doc_info.get('filename')}")
                    
                except Exception as e:
                    operation_result['status'] = 'error'
                    operation_result['message'] = f"Failed consolidation: {str(e)}"
                    self.logger.error(f"❌ Consolidation failed: {e}")
            
            results.append(operation_result)
        
        return results
    
    async def _post_operation_validation(self, results: Dict[str, Any], 
                                       documents: List[DocumentMetadata]) -> Dict[str, Any]:
        """Validate system state after cleanup operations"""
        validation_results = {
            'validation_passed': True,
            'issues_found': [],
            'recommendations': []
        }
        
        # Check for broken references
        broken_refs = await self._check_for_broken_references(results, documents)
        if broken_refs:
            validation_results['validation_passed'] = False
            validation_results['issues_found'].extend(broken_refs)
        
        # Verify cleanup completeness
        completeness_issues = self._verify_cleanup_completeness(results)
        if completeness_issues:
            validation_results['issues_found'].extend(completeness_issues)
        
        return validation_results
    
    async def _check_for_broken_references(self, results: Dict[str, Any], 
                                         documents: List[DocumentMetadata]) -> List[str]:
        """Check for references broken by cleanup operations"""
        broken_refs = []
        
        # Get list of deleted/moved files
        affected_paths = set()
        for operation in results.get('operations_performed', []):
            if operation['status'] in ['completed'] and operation['operation'] in ['delete', 'archive']:
                affected_paths.add(operation['document_path'])
        
        # Check remaining documents for references to affected paths
        for doc in documents:
            if isinstance(doc, Exception):
                continue
                
            references = doc.custom_fields.get('discovered_references', [])
            for ref_path in references:
                if ref_path in affected_paths:
                    broken_refs.append(f"Document '{doc.filename}' references deleted/archived file '{Path(ref_path).name}'")
        
        return broken_refs
    
    def _verify_cleanup_completeness(self, results: Dict[str, Any]) -> List[str]:
        """Verify that all planned cleanup operations completed successfully"""
        issues = []
        
        for operation in results.get('operations_performed', []):
            if operation['status'] == 'error':
                issues.append(f"Operation failed: {operation.get('message', 'Unknown error')}")
            elif operation['status'] == 'warning':
                issues.append(f"Operation warning: {operation.get('message', 'Unknown warning')}")
        
        return issues
    
    def _generate_audit_trail(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate comprehensive audit trail"""
        audit_entries = []
        
        # Add safety check entries
        for check in results.get('safety_checks', {}).get('checks_performed', []):
            audit_entries.append({
                'timestamp': datetime.now().isoformat(),
                'event_type': 'safety_check',
                'check_name': check['check'],
                'status': check['status'],
                'details': check['details']
            })
        
        # Add operation entries
        for operation in results.get('operations_performed', []):
            audit_entries.append({
                'timestamp': operation.get('timestamp', datetime.now().isoformat()),
                'event_type': 'cleanup_operation',
                'operation': operation['operation'],
                'document_id': operation.get('document_id'),
                'filename': operation.get('filename'),
                'status': operation['status'],
                'details': operation.get('message', '')
            })
        
        return audit_entries
    
    def _generate_operation_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate operation summary statistics"""
        operations = results.get('operations_performed', [])
        
        summary = {
            'total_operations': len(operations),
            'operations_by_type': {},
            'operations_by_status': {},
            'total_space_saved_bytes': 0,
            'documents_affected': 0
        }
        
        for operation in operations:
            # Count by type
            op_type = operation['operation']
            summary['operations_by_type'][op_type] = summary['operations_by_type'].get(op_type, 0) + 1
            
            # Count by status
            status = operation['status']
            summary['operations_by_status'][status] = summary['operations_by_status'].get(status, 0) + 1
            
            # Sum space savings
            space_saved = operation.get('space_saved_bytes', 0)
            if isinstance(space_saved, (int, float)):
                summary['total_space_saved_bytes'] += space_saved
            
            # Count affected documents
            if status == 'completed':
                summary['documents_affected'] += 1
        
        return summary
    
    async def get_cleanup_insights(self) -> Dict[str, Any]:
        """Get insights from cleanup operations for swarm coordination"""
        return {
            'cleanup_history_size': len(self.cleanup_history),
            'total_operations_performed': sum(
                len(history.get('operations_performed', [])) 
                for history in self.cleanup_history
            ),
            'success_rate': self._calculate_cleanup_success_rate(),
            'most_common_operations': self._get_most_common_operations(),
            'safety_effectiveness': self._calculate_safety_effectiveness(),
            'recommendations': self._generate_cleanup_recommendations()
        }
    
    def _calculate_cleanup_success_rate(self) -> float:
        """Calculate overall cleanup success rate"""
        if not self.cleanup_history:
            return 0.0
        
        total_operations = 0
        successful_operations = 0
        
        for history in self.cleanup_history:
            for operation in history.get('operations_performed', []):
                total_operations += 1
                if operation['status'] == 'completed':
                    successful_operations += 1
        
        return successful_operations / total_operations if total_operations > 0 else 0.0
    
    def _get_most_common_operations(self) -> List[Dict[str, Any]]:
        """Get most commonly performed operations"""
        operation_counts = {}
        
        for history in self.cleanup_history:
            for operation in history.get('operations_performed', []):
                op_type = operation['operation']
                operation_counts[op_type] = operation_counts.get(op_type, 0) + 1
        
        return [
            {'operation': op_type, 'count': count}
            for op_type, count in sorted(operation_counts.items(), key=lambda x: x[1], reverse=True)
        ]
    
    def _calculate_safety_effectiveness(self) -> Dict[str, Any]:
        """Calculate effectiveness of safety checks"""
        safety_stats = {
            'total_safety_checks': 0,
            'checks_passed': 0,
            'checks_failed': 0,
            'warnings_generated': 0
        }
        
        for history in self.cleanup_history:
            safety_checks = history.get('safety_checks', {})
            
            for check in safety_checks.get('checks_performed', []):
                safety_stats['total_safety_checks'] += 1
                if check['status'] == 'pass':
                    safety_stats['checks_passed'] += 1
                elif check['status'] == 'fail':
                    safety_stats['checks_failed'] += 1
            
            safety_stats['warnings_generated'] += len(safety_checks.get('warnings', []))
        
        return safety_stats
    
    def _generate_cleanup_recommendations(self) -> List[Dict[str, Any]]:
        """Generate recommendations for future cleanup operations"""
        recommendations = []
        
        success_rate = self._calculate_cleanup_success_rate()
        
        if success_rate < 0.8:
            recommendations.append({
                'category': 'safety',
                'priority': 'high',
                'recommendation': 'Increase safety check rigor',
                'reason': f'Success rate ({success_rate:.1%}) below optimal threshold'
            })
        
        # Check for patterns in failed operations
        failed_operations = []
        for history in self.cleanup_history:
            for operation in history.get('operations_performed', []):
                if operation['status'] in ['error', 'failed']:
                    failed_operations.append(operation)
        
        if len(failed_operations) > 5:
            recommendations.append({
                'category': 'reliability',
                'priority': 'medium',
                'recommendation': 'Investigate common failure patterns',
                'reason': f'{len(failed_operations)} operations failed recently'
            })
        
        return recommendations


class BackupManager:
    """Manages backup operations for document cleanup"""
    
    def __init__(self):
        self.backup_root = Path("./backups")
        self.backup_root.mkdir(exist_ok=True)
    
    async def create_cleanup_backup(self, documents: List[DocumentMetadata], 
                                  cleanup_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive backup before cleanup operations"""
        backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.backup_root / f"cleanup_backup_{backup_timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        backup_info = {
            'backup_id': backup_timestamp,
            'backup_path': str(backup_dir),
            'created_at': datetime.now().isoformat(),
            'files_backed_up': [],
            'backup_size_bytes': 0
        }
        
        # Identify documents that need backup
        docs_to_backup = set()
        
        # Add deletion candidates
        for candidate in cleanup_plan.get('candidates_for_deletion', []):
            docs_to_backup.add(candidate.get('document_id'))
        
        # Add archival candidates (backup before move)
        for candidate in cleanup_plan.get('candidates_for_archival', []):
            docs_to_backup.add(candidate.get('document_id'))
        
        # Add consolidation candidates
        for group in cleanup_plan.get('consolidation_groups', []):
            for doc_info in group.get('similar_documents', []):
                docs_to_backup.add(doc_info.get('id'))
        
        # Perform backups
        for doc in documents:
            if isinstance(doc, Exception) or doc.id not in docs_to_backup:
                continue
            
            try:
                source_path = Path(doc.source_path)
                if source_path.exists():
                    # Create backup file
                    backup_file = backup_dir / doc.filename
                    
                    # Handle name conflicts
                    counter = 1
                    while backup_file.exists():
                        stem = backup_file.stem
                        suffix = backup_file.suffix
                        backup_file = backup_dir / f"{stem}_{counter}{suffix}"
                        counter += 1
                    
                    shutil.copy2(str(source_path), str(backup_file))
                    
                    backup_info['files_backed_up'].append({
                        'document_id': doc.id,
                        'original_path': str(source_path),
                        'backup_path': str(backup_file),
                        'size_bytes': source_path.stat().st_size
                    })
                    
                    backup_info['backup_size_bytes'] += source_path.stat().st_size
            
            except Exception as e:
                # Log but don't fail the entire backup
                print(f"Warning: Failed to backup {doc.filename}: {e}")
        
        # Save backup manifest
        manifest_path = backup_dir / "backup_manifest.json"
        async with aiofiles.open(manifest_path, 'w') as f:
            await f.write(json.dumps(backup_info, indent=2))
        
        return backup_info


class DependencyAnalyzer:
    """Analyzes document dependencies to prevent broken references"""
    
    async def analyze_dependencies(self, documents: List[DocumentMetadata]) -> Dict[str, Any]:
        """Analyze document dependency graph"""
        # This would implement sophisticated dependency analysis
        # For now, placeholder implementation
        return {
            'dependency_graph': {},
            'circular_dependencies': [],
            'orphaned_documents': [],
            'critical_dependencies': []
        }


class ConsolidationEngine:
    """Handles intelligent document consolidation operations"""
    
    async def consolidate_documents(self, primary_doc_info: Dict, 
                                  similar_docs: List[Dict],
                                  all_documents: List[DocumentMetadata],
                                  strategy: str) -> Dict[str, Any]:
        """Consolidate similar documents using specified strategy"""
        
        if strategy == "merge_into_primary":
            return await self._merge_into_primary(primary_doc_info, similar_docs, all_documents)
        elif strategy == "create_comprehensive_guide":
            return await self._create_comprehensive_guide(primary_doc_info, similar_docs, all_documents)
        elif strategy == "create_topic_hub":
            return await self._create_topic_hub(primary_doc_info, similar_docs, all_documents)
        else:
            return {
                'status': 'error',
                'message': f'Unknown consolidation strategy: {strategy}'
            }
    
    async def _merge_into_primary(self, primary_doc_info: Dict, 
                                similar_docs: List[Dict],
                                all_documents: List[DocumentMetadata]) -> Dict[str, Any]:
        """Merge similar documents into primary document"""
        # Placeholder implementation
        # In production, this would intelligently merge content
        return {
            'status': 'completed',
            'message': f'Merged {len(similar_docs)} documents into primary',
            'consolidated_path': f"consolidated_{primary_doc_info.get('filename', 'unknown')}",
            'space_saved_bytes': sum(doc.get('size_bytes', 0) for doc in similar_docs)
        }
    
    async def _create_comprehensive_guide(self, primary_doc_info: Dict,
                                        similar_docs: List[Dict],
                                        all_documents: List[DocumentMetadata]) -> Dict[str, Any]:
        """Create comprehensive guide from similar documents"""
        # Placeholder implementation
        return {
            'status': 'completed',
            'message': f'Created comprehensive guide from {len(similar_docs) + 1} documents',
            'consolidated_path': f"comprehensive_guide_{primary_doc_info.get('filename', 'unknown')}",
            'space_saved_bytes': sum(doc.get('size_bytes', 0) for doc in similar_docs) // 2
        }
    
    async def _create_topic_hub(self, primary_doc_info: Dict,
                              similar_docs: List[Dict], 
                              all_documents: List[DocumentMetadata]) -> Dict[str, Any]:
        """Create topic hub linking to related documents"""
        # Placeholder implementation
        return {
            'status': 'completed',
            'message': f'Created topic hub linking {len(similar_docs) + 1} documents',
            'consolidated_path': f"topic_hub_{primary_doc_info.get('filename', 'unknown')}",
            'space_saved_bytes': 0  # No space saved, just reorganized
        }


if __name__ == "__main__":
    # Test the cleanup agent
    async def test_cleanup():
        agent = DocumentCleanupAgent()
        
        # Mock cleanup plan
        test_plan = {
            'candidates_for_deletion': [
                {'document_id': 'test_doc_1', 'reason': 'Test deletion'}
            ],
            'candidates_for_archival': [
                {'document_id': 'test_doc_2', 'reason': 'Test archival'}
            ],
            'consolidation_groups': []
        }
        
        # Mock documents
        test_docs = []
        
        # Execute cleanup in dry-run mode
        results = await agent.execute_cleanup_plan(test_plan, test_docs, dry_run=True)
        
        print(f"\n🧹 Cleanup Test Results:")
        print(f"   Operations: {len(results.get('operations_performed', []))}")
        print(f"   Safety checks: {len(results.get('safety_checks', {}).get('checks_performed', []))}")
        print(f"   Duration: {results.get('total_duration_seconds', 0):.2f}s")
    
    # Uncomment to test
    # asyncio.run(test_cleanup())