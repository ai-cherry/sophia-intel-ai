"""
Quality Assurance Agent for SOPHIA Intel
Validates knowledge quality, accuracy, and consistency across all data sources
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from celery import Task
from .celery_app import celery_app
from ..database.unified_knowledge_repository import UnifiedKnowledgeRepository

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QualityAssuranceAgent:
    """Agent for ensuring knowledge quality and accuracy"""
    
    def __init__(self):
        self.knowledge_repo = UnifiedKnowledgeRepository()
        
        # Quality metrics and thresholds
        self.quality_thresholds = {
            'confidence_score': 0.7,
            'data_freshness_hours': 168,  # 1 week
            'correlation_strength': 0.6,
            'entity_completeness': 0.8,
            'relationship_validity': 0.75
        }
        
        # Quality check categories
        self.quality_checks = {
            'data_consistency': {
                'weight': 0.25,
                'checks': ['duplicate_detection', 'format_validation', 'field_completeness']
            },
            'temporal_validity': {
                'weight': 0.20,
                'checks': ['data_freshness', 'temporal_consistency', 'update_frequency']
            },
            'business_relevance': {
                'weight': 0.25,
                'checks': ['pay_ready_context', 'business_entity_validity', 'domain_alignment']
            },
            'relationship_integrity': {
                'weight': 0.20,
                'checks': ['relationship_validity', 'circular_dependencies', 'orphaned_entities']
            },
            'source_reliability': {
                'weight': 0.10,
                'checks': ['source_availability', 'api_response_quality', 'data_volume_consistency']
            }
        }
        
        # Business context validators
        self.business_validators = {
            'pay_ready_entities': [
                'revenue', 'customer', 'product', 'sales', 'marketing',
                'operations', 'finance', 'growth', 'retention', 'acquisition'
            ],
            'financial_metrics': [
                'ARR', 'MRR', 'LTV', 'CAC', 'churn', 'margin', 'profit',
                'revenue', 'cost', 'expense', 'budget', 'forecast'
            ],
            'operational_terms': [
                'process', 'workflow', 'automation', 'efficiency',
                'productivity', 'performance', 'optimization'
            ]
        }
    
    def validate_entity_quality(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the quality of a single entity"""
        quality_score = 0.0
        issues = []
        checks_passed = 0
        total_checks = 0
        
        try:
            # Data consistency checks
            consistency_score, consistency_issues = self.check_data_consistency(entity)
            quality_score += consistency_score * self.quality_checks['data_consistency']['weight']
            issues.extend(consistency_issues)
            total_checks += len(self.quality_checks['data_consistency']['checks'])
            checks_passed += len(self.quality_checks['data_consistency']['checks']) - len(consistency_issues)
            
            # Temporal validity checks
            temporal_score, temporal_issues = self.check_temporal_validity(entity)
            quality_score += temporal_score * self.quality_checks['temporal_validity']['weight']
            issues.extend(temporal_issues)
            total_checks += len(self.quality_checks['temporal_validity']['checks'])
            checks_passed += len(self.quality_checks['temporal_validity']['checks']) - len(temporal_issues)
            
            # Business relevance checks
            relevance_score, relevance_issues = self.check_business_relevance(entity)
            quality_score += relevance_score * self.quality_checks['business_relevance']['weight']
            issues.extend(relevance_issues)
            total_checks += len(self.quality_checks['business_relevance']['checks'])
            checks_passed += len(self.quality_checks['business_relevance']['checks']) - len(relevance_issues)
            
            return {
                'entity_id': entity.get('id'),
                'overall_quality_score': quality_score,
                'checks_passed': checks_passed,
                'total_checks': total_checks,
                'pass_rate': checks_passed / total_checks if total_checks > 0 else 0.0,
                'issues': issues,
                'validated_at': datetime.utcnow(),
                'meets_threshold': quality_score >= self.quality_thresholds['confidence_score']
            }
            
        except Exception as e:
            logger.error(f"Error validating entity quality: {e}")
            return {
                'entity_id': entity.get('id'),
                'overall_quality_score': 0.0,
                'error': str(e),
                'validated_at': datetime.utcnow()
            }
    
    def check_data_consistency(self, entity: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Check data consistency for an entity"""
        score = 1.0
        issues = []
        
        try:
            # Check for required fields
            required_fields = ['text', 'category', 'confidence']
            for field in required_fields:
                if not entity.get(field):
                    issues.append(f'missing_{field}')
                    score -= 0.3
            
            # Check text quality
            entity_text = entity.get('text', '').strip()
            if len(entity_text) < 2:
                issues.append('text_too_short')
                score -= 0.2
            elif not entity_text.replace(' ', '').replace('-', '').replace('_', '').isalnum():
                issues.append('text_contains_invalid_characters')
                score -= 0.1
            
            # Check confidence score validity
            confidence = entity.get('confidence', 0)
            if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
                issues.append('invalid_confidence_score')
                score -= 0.2
            
            # Check category validity
            category = entity.get('category', '')
            if not category or category == 'unknown':
                issues.append('invalid_category')
                score -= 0.2
            
        except Exception as e:
            logger.error(f"Error checking data consistency: {e}")
            issues.append('consistency_check_error')
            score = 0.0
        
        return max(score, 0.0), issues
    
    def check_temporal_validity(self, entity: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Check temporal validity for an entity"""
        score = 1.0
        issues = []
        
        try:
            # Check data freshness
            extracted_at = entity.get('extracted_at')
            if extracted_at:
                if isinstance(extracted_at, str):
                    extracted_at = datetime.fromisoformat(extracted_at.replace('Z', '+00:00'))
                
                age_hours = (datetime.utcnow() - extracted_at).total_seconds() / 3600
                if age_hours > self.quality_thresholds['data_freshness_hours']:
                    issues.append('data_too_old')
                    score -= 0.3
                elif age_hours > self.quality_thresholds['data_freshness_hours'] / 2:
                    issues.append('data_aging')
                    score -= 0.1
            else:
                issues.append('missing_timestamp')
                score -= 0.4
            
            # Check for temporal consistency
            created_at = entity.get('created_at')
            updated_at = entity.get('updated_at')
            
            if created_at and updated_at:
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                if isinstance(updated_at, str):
                    updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                
                if updated_at < created_at:
                    issues.append('temporal_inconsistency')
                    score -= 0.2
            
        except Exception as e:
            logger.error(f"Error checking temporal validity: {e}")
            issues.append('temporal_check_error')
            score = 0.0
        
        return max(score, 0.0), issues
    
    def check_business_relevance(self, entity: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Check business relevance for Pay Ready context"""
        score = 1.0
        issues = []
        
        try:
            entity_text = entity.get('text', '').lower()
            category = entity.get('category', '').lower()
            context = entity.get('context', {})
            
            # Check for Pay Ready business context
            has_business_context = False
            
            # Check entity text against business validators
            for validator_category, terms in self.business_validators.items():
                for term in terms:
                    if term.lower() in entity_text:
                        has_business_context = True
                        break
                if has_business_context:
                    break
            
            # Check category alignment
            valid_categories = [
                'revenue_metrics', 'customer_entities', 'product_entities',
                'operational_entities', 'market_entities', 'financial_entities'
            ]
            
            if category not in valid_categories:
                issues.append('category_not_business_aligned')
                score -= 0.3
            
            # Check for Pay Ready specific context
            if isinstance(context, dict):
                context_str = json.dumps(context).lower()
                if 'pay_ready' in context_str or 'payready' in context_str:
                    has_business_context = True
            
            if not has_business_context:
                issues.append('lacks_business_context')
                score -= 0.4
            
            # Check source reliability
            source_type = entity.get('source_type', '')
            reliable_sources = [
                'salesforce', 'hubspot', 'gong', 'netsuite', 'looker',
                'chat_conversation', 'api_integration'
            ]
            
            if source_type not in reliable_sources:
                issues.append('unreliable_source')
                score -= 0.2
            
        except Exception as e:
            logger.error(f"Error checking business relevance: {e}")
            issues.append('relevance_check_error')
            score = 0.0
        
        return max(score, 0.0), issues
    
    def validate_relationship_quality(self, relationship: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the quality of a relationship"""
        quality_score = 0.0
        issues = []
        
        try:
            # Check relationship integrity
            source_entity_id = relationship.get('source_entity_id')
            target_entity_id = relationship.get('target_entity_id')
            
            if not source_entity_id or not target_entity_id:
                issues.append('missing_entity_references')
                quality_score -= 0.4
            elif source_entity_id == target_entity_id:
                issues.append('self_referential_relationship')
                quality_score -= 0.3
            else:
                quality_score += 0.4
            
            # Check relationship type validity
            relationship_type = relationship.get('relationship_type', '')
            valid_types = ['causal', 'correlation', 'dependency', 'composition', 'temporal', 'hierarchical']
            
            if relationship_type in valid_types:
                quality_score += 0.3
            else:
                issues.append('invalid_relationship_type')
                quality_score -= 0.2
            
            # Check confidence score
            confidence = relationship.get('confidence_score', 0)
            if confidence >= self.quality_thresholds['correlation_strength']:
                quality_score += 0.3
            else:
                issues.append('low_confidence_relationship')
                quality_score -= 0.1
            
            return {
                'relationship_id': relationship.get('id'),
                'quality_score': max(quality_score, 0.0),
                'issues': issues,
                'validated_at': datetime.utcnow(),
                'meets_threshold': quality_score >= self.quality_thresholds['relationship_validity']
            }
            
        except Exception as e:
            logger.error(f"Error validating relationship quality: {e}")
            return {
                'relationship_id': relationship.get('id'),
                'quality_score': 0.0,
                'error': str(e),
                'validated_at': datetime.utcnow()
            }
    
    def validate_correlation_quality(self, correlation: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the quality of a cross-platform correlation"""
        quality_score = 0.0
        issues = []
        
        try:
            # Check correlation strength
            confidence = correlation.get('confidence_score', 0)
            if confidence >= 0.8:
                quality_score += 0.4
            elif confidence >= 0.6:
                quality_score += 0.2
            else:
                issues.append('weak_correlation')
            
            # Check business impact assessment
            business_impact = correlation.get('business_impact', '')
            high_value_impacts = [
                'customer_lifecycle_tracking', 'revenue_tracking',
                'sales_optimization', 'customer_satisfaction'
            ]
            
            if business_impact in high_value_impacts:
                quality_score += 0.3
            elif business_impact:
                quality_score += 0.1
            else:
                issues.append('missing_business_impact')
            
            # Check source reliability
            source1 = correlation.get('source1', '')
            source2 = correlation.get('source2', '')
            
            high_priority_sources = ['salesforce', 'hubspot', 'gong', 'netsuite', 'looker']
            
            if source1 in high_priority_sources and source2 in high_priority_sources:
                quality_score += 0.3
            elif source1 in high_priority_sources or source2 in high_priority_sources:
                quality_score += 0.2
            else:
                quality_score += 0.1
            
            return {
                'correlation_id': correlation.get('id'),
                'quality_score': max(quality_score, 0.0),
                'issues': issues,
                'validated_at': datetime.utcnow(),
                'meets_threshold': quality_score >= 0.6
            }
            
        except Exception as e:
            logger.error(f"Error validating correlation quality: {e}")
            return {
                'correlation_id': correlation.get('id'),
                'quality_score': 0.0,
                'error': str(e),
                'validated_at': datetime.utcnow()
            }
    
    def generate_quality_report(self) -> Dict[str, Any]:
        """Generate comprehensive quality report"""
        try:
            # Get recent data for analysis
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=24)
            
            entities = self.knowledge_repo.get_entities_by_time_range(start_time, end_time)
            relationships = self.knowledge_repo.get_relationships_by_time_range(start_time, end_time)
            correlations = self.knowledge_repo.get_correlations_by_time_range(start_time, end_time)
            
            # Validate entities
            entity_validations = []
            for entity in entities[:100]:  # Limit for performance
                validation = self.validate_entity_quality(entity)
                entity_validations.append(validation)
            
            # Validate relationships
            relationship_validations = []
            for relationship in relationships[:50]:  # Limit for performance
                validation = self.validate_relationship_quality(relationship)
                relationship_validations.append(validation)
            
            # Validate correlations
            correlation_validations = []
            for correlation in correlations[:50]:  # Limit for performance
                validation = self.validate_correlation_quality(correlation)
                correlation_validations.append(validation)
            
            # Calculate summary statistics
            entity_quality_scores = [v['overall_quality_score'] for v in entity_validations if 'overall_quality_score' in v]
            relationship_quality_scores = [v['quality_score'] for v in relationship_validations if 'quality_score' in v]
            correlation_quality_scores = [v['quality_score'] for v in correlation_validations if 'quality_score' in v]
            
            avg_entity_quality = sum(entity_quality_scores) / len(entity_quality_scores) if entity_quality_scores else 0.0
            avg_relationship_quality = sum(relationship_quality_scores) / len(relationship_quality_scores) if relationship_quality_scores else 0.0
            avg_correlation_quality = sum(correlation_quality_scores) / len(correlation_quality_scores) if correlation_quality_scores else 0.0
            
            # Count issues
            all_issues = []
            for validation in entity_validations + relationship_validations + correlation_validations:
                all_issues.extend(validation.get('issues', []))
            
            issue_counts = {}
            for issue in all_issues:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
            
            return {
                'report_generated_at': datetime.utcnow(),
                'time_period': {
                    'start': start_time,
                    'end': end_time
                },
                'summary': {
                    'entities_analyzed': len(entity_validations),
                    'relationships_analyzed': len(relationship_validations),
                    'correlations_analyzed': len(correlation_validations),
                    'average_entity_quality': avg_entity_quality,
                    'average_relationship_quality': avg_relationship_quality,
                    'average_correlation_quality': avg_correlation_quality,
                    'overall_system_quality': (avg_entity_quality + avg_relationship_quality + avg_correlation_quality) / 3
                },
                'quality_thresholds': self.quality_thresholds,
                'top_issues': dict(sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
                'entities_meeting_threshold': len([v for v in entity_validations if v.get('meets_threshold', False)]),
                'relationships_meeting_threshold': len([v for v in relationship_validations if v.get('meets_threshold', False)]),
                'correlations_meeting_threshold': len([v for v in correlation_validations if v.get('meets_threshold', False)])
            }
            
        except Exception as e:
            logger.error(f"Error generating quality report: {e}")
            return {
                'error': str(e),
                'report_generated_at': datetime.utcnow()
            }

# Celery Tasks
@celery_app.task(bind=True, name='sophia_agents.quality_assurance.validate_knowledge_quality')
def validate_knowledge_quality(self: Task) -> Dict[str, Any]:
    """Validate overall knowledge quality"""
    agent = QualityAssuranceAgent()
    
    try:
        quality_report = agent.generate_quality_report()
        
        result = {
            'task': 'validate_knowledge_quality',
            'quality_report': quality_report,
            'completed_at': datetime.utcnow().isoformat(),
            'status': 'success'
        }
        
        logger.info(f"Knowledge quality validation completed: Overall quality = {quality_report.get('summary', {}).get('overall_system_quality', 0):.2f}")
        return result
        
    except Exception as e:
        logger.error(f"Knowledge quality validation failed: {e}")
        return {
            'task': 'validate_knowledge_quality',
            'error': str(e),
            'completed_at': datetime.utcnow().isoformat(),
            'status': 'failed'
        }

@celery_app.task(bind=True, name='sophia_agents.quality_assurance.validate_entity_batch')
def validate_entity_batch(self: Task, entity_ids: List[str]) -> Dict[str, Any]:
    """Validate a specific batch of entities"""
    agent = QualityAssuranceAgent()
    
    try:
        validations = []
        
        for entity_id in entity_ids:
            entity = agent.knowledge_repo.get_entity_by_id(entity_id)
            if entity:
                validation = agent.validate_entity_quality(entity)
                validations.append(validation)
                
                # Update entity with validation results
                agent.knowledge_repo.update_entity_quality_score(
                    entity_id,
                    validation['overall_quality_score'],
                    validation.get('issues', [])
                )
        
        avg_quality = sum(v['overall_quality_score'] for v in validations) / len(validations) if validations else 0.0
        
        return {
            'task': 'validate_entity_batch',
            'entities_validated': len(validations),
            'average_quality_score': avg_quality,
            'entities_meeting_threshold': len([v for v in validations if v.get('meets_threshold', False)]),
            'completed_at': datetime.utcnow().isoformat(),
            'status': 'success'
        }
        
    except Exception as e:
        logger.error(f"Entity batch validation failed: {e}")
        return {
            'task': 'validate_entity_batch',
            'error': str(e),
            'completed_at': datetime.utcnow().isoformat(),
            'status': 'failed'
        }

@celery_app.task(bind=True, name='sophia_agents.quality_assurance.cleanup_low_quality_data')
def cleanup_low_quality_data(self: Task, quality_threshold: float = 0.3) -> Dict[str, Any]:
    """Clean up low-quality data that doesn't meet standards"""
    agent = QualityAssuranceAgent()
    
    try:
        # Get entities with low quality scores
        low_quality_entities = agent.knowledge_repo.get_entities_below_quality_threshold(quality_threshold)
        
        # Get relationships with low confidence
        low_quality_relationships = agent.knowledge_repo.get_relationships_below_threshold(quality_threshold)
        
        # Mark for cleanup (don't delete immediately, mark as inactive)
        entities_cleaned = 0
        relationships_cleaned = 0
        
        for entity in low_quality_entities:
            agent.knowledge_repo.mark_entity_inactive(entity['id'], 'low_quality_score')
            entities_cleaned += 1
        
        for relationship in low_quality_relationships:
            agent.knowledge_repo.mark_relationship_inactive(relationship['id'], 'low_confidence')
            relationships_cleaned += 1
        
        return {
            'task': 'cleanup_low_quality_data',
            'quality_threshold': quality_threshold,
            'entities_cleaned': entities_cleaned,
            'relationships_cleaned': relationships_cleaned,
            'completed_at': datetime.utcnow().isoformat(),
            'status': 'success'
        }
        
    except Exception as e:
        logger.error(f"Low quality data cleanup failed: {e}")
        return {
            'task': 'cleanup_low_quality_data',
            'error': str(e),
            'completed_at': datetime.utcnow().isoformat(),
            'status': 'failed'
        }

